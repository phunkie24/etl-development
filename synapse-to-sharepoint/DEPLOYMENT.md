# Deployment Guide

This guide covers deploying the Synapse to SharePoint integration to Azure Functions.

## Prerequisites

- Azure subscription
- Azure CLI installed
- Azure Functions Core Tools
- Python 3.9+

## Deployment Steps

### 1. Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="rg-synapse-sharepoint"
LOCATION="eastus"
STORAGE_ACCOUNT="stsynapsesharepoint"
FUNCTION_APP="func-synapse-sharepoint"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --name $FUNCTION_APP \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux
```

### 2. Configure Application Settings

```bash
# Set environment variables
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    SYNAPSE_SERVER="your-synapse.sql.azuresynapse.net" \
    SYNAPSE_DATABASE="your_database" \
    SYNAPSE_USERNAME="your_username" \
    SYNAPSE_PASSWORD="your_password" \
    USE_MANAGED_IDENTITY="false" \
    SHAREPOINT_SITE_URL="https://yourtenant.sharepoint.com/sites/yoursite" \
    SHAREPOINT_LIST_NAME="YourListName" \
    TENANT_ID="your-tenant-id" \
    CLIENT_ID="your-client-id" \
    CLIENT_SECRET="your-client-secret" \
    SYNAPSE_QUERY="SELECT * FROM your_table" \
    BATCH_SIZE="100" \
    LOG_LEVEL="INFO" \
    FIELD_MAPPING="{\"id\": \"ID\", \"name\": \"Title\"}"
```

### 3. Deploy Function Code

```bash
# From project directory
func azure functionapp publish $FUNCTION_APP
```

### 4. Configure Managed Identity (Optional but Recommended)

```bash
# Enable system-assigned managed identity
az functionapp identity assign \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP

# Get the identity
IDENTITY_ID=$(az functionapp identity show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Grant permissions to Synapse (run in Synapse SQL pool)
# CREATE USER [func-synapse-sharepoint] FROM EXTERNAL PROVIDER;
# GRANT SELECT ON SCHEMA::dbo TO [func-synapse-sharepoint];
```

### 5. Set Up Timer Trigger (Optional)

Create a new function with timer trigger:

```json
{
  "scriptFile": "function_app.py",
  "bindings": [
    {
      "name": "mytimer",
      "type": "timerTrigger",
      "direction": "in",
      "schedule": "0 0 2 * * *",
      "runOnStartup": false
    }
  ]
}
```

Schedule examples:
- `0 0 2 * * *` - Daily at 2 AM
- `0 0 */6 * * *` - Every 6 hours
- `0 30 8 * * 1-5` - Weekdays at 8:30 AM

### 6. Configure Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app $FUNCTION_APP-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app $FUNCTION_APP-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv)

# Link to function app
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

### 7. Test Deployment

```bash
# Get function URL
FUNCTION_URL=$(az functionapp function show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --function-name main \
  --query invokeUrlTemplate -o tsv)

# Get function key
FUNCTION_KEY=$(az functionapp keys list \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query functionKeys.default -o tsv)

# Test the function
curl -X POST "$FUNCTION_URL?code=$FUNCTION_KEY"
```

## Using Azure Key Vault (Recommended for Production)

### 1. Create Key Vault

```bash
KEY_VAULT="kv-synapse-sharepoint"

az keyvault create \
  --name $KEY_VAULT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

### 2. Store Secrets

```bash
# Store secrets
az keyvault secret set --vault-name $KEY_VAULT --name "SynapsePassword" --value "your-password"
az keyvault secret set --vault-name $KEY_VAULT --name "ClientSecret" --value "your-client-secret"
```

### 3. Grant Function App Access

```bash
# Get function app identity
FUNCTION_IDENTITY=$(az functionapp identity show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Grant access to Key Vault
az keyvault set-policy \
  --name $KEY_VAULT \
  --object-id $FUNCTION_IDENTITY \
  --secret-permissions get list
```

### 4. Reference Secrets in App Settings

```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    SYNAPSE_PASSWORD="@Microsoft.KeyVault(SecretUri=https://$KEY_VAULT.vault.azure.net/secrets/SynapsePassword/)" \
    CLIENT_SECRET="@Microsoft.KeyVault(SecretUri=https://$KEY_VAULT.vault.azure.net/secrets/ClientSecret/)"
```

## Monitoring and Troubleshooting

### View Logs

```bash
# Stream logs
az webapp log tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP

# Download logs
az webapp log download --name $FUNCTION_APP --resource-group $RESOURCE_GROUP
```

### Application Insights Queries

```kusto
// Failed executions
traces
| where message contains "Pipeline execution failed"
| order by timestamp desc

// Performance metrics
requests
| where name == "main"
| summarize avg(duration), percentile(duration, 95) by bin(timestamp, 1h)

// Error analysis
exceptions
| where outerMessage contains "SharePoint" or outerMessage contains "Synapse"
| summarize count() by outerMessage, bin(timestamp, 1h)
```

## Scaling Considerations

### Consumption Plan Limits
- **Timeout**: 5 minutes default, 10 minutes max
- **Memory**: 1.5 GB
- **Concurrent executions**: 200

### Premium Plan (for longer executions)

```bash
# Create App Service Plan
az appservice plan create \
  --name plan-synapse-sharepoint \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku EP1 \
  --is-linux

# Update function app to use premium plan
az functionapp update \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --plan plan-synapse-sharepoint
```

## Security Hardening

### 1. Network Isolation

```bash
# Create VNet
az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name vnet-functions \
  --address-prefix 10.0.0.0/16 \
  --subnet-name subnet-functions \
  --subnet-prefix 10.0.1.0/24

# Enable VNet integration
az functionapp vnet-integration add \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --vnet vnet-functions \
  --subnet subnet-functions
```

### 2. Restrict Function Access

```bash
# Allow only specific IP addresses
az functionapp config access-restriction add \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --rule-name "AllowCorporateNetwork" \
  --action Allow \
  --ip-address 203.0.113.0/24 \
  --priority 100
```

### 3. Enable Authentication

```bash
# Enable Azure AD authentication
az webapp auth update \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --enabled true \
  --action LoginWithAzureActiveDirectory \
  --aad-client-id $CLIENT_ID \
  --aad-token-issuer-url "https://sts.windows.net/$TENANT_ID/"
```

## Maintenance

### Update Function Code

```bash
# Pull latest changes
git pull

# Deploy update
func azure functionapp publish $FUNCTION_APP
```

### Rotate Secrets

```bash
# Update in Key Vault
az keyvault secret set --vault-name $KEY_VAULT --name "ClientSecret" --value "new-secret"

# Function app will automatically use new secret
```

### Monitor Costs

```bash
# View resource costs
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --query "[?contains(instanceName, '$FUNCTION_APP')]"
```

## Rollback

```bash
# List deployments
az functionapp deployment list \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP

# Rollback to previous deployment
az functionapp deployment source config-zip \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --src previous-deployment.zip
```

## Cleanup

```bash
# Delete all resources
az group delete --name $RESOURCE_GROUP --yes
```
