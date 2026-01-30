# Synapse to SharePoint Integration

A robust, production-ready Python solution for deploying data from Azure Synapse Analytics to SharePoint Online lists using Microsoft Graph API. Built with modularity, comprehensive logging, and thorough testing.

## Features

- ✅ **Azure Synapse Integration**: Direct SQL connection or Managed Identity authentication
- ✅ **Microsoft Graph API**: Modern SharePoint access via Graph API
- ✅ **Modular Architecture**: Clean separation of concerns with testable components
- ✅ **Comprehensive Logging**: Structured logging with JSON output for Azure monitoring
- ✅ **Data Transformation**: Flexible field mapping and type conversion
- ✅ **Batch Processing**: Configurable batch sizes for optimal performance
- ✅ **Error Handling**: Robust error handling with detailed reporting
- ✅ **Azure Functions Ready**: Deploy as serverless HTTP or Timer-triggered function
- ✅ **Fully Tested**: Comprehensive unit tests with high coverage

## Architecture

```
synapse-to-sharepoint/
├── src/
│   ├── config.py              # Configuration management
│   ├── logging_config.py      # Structured logging setup
│   ├── synapse_client.py      # Synapse data access
│   ├── sharepoint_client.py   # SharePoint Graph API client
│   ├── data_transformer.py    # Data transformation logic
│   └── main.py                # Pipeline orchestration
├── tests/                     # Comprehensive test suite
├── function_app.py            # Azure Function entry point
├── requirements.txt           # Python dependencies
└── .env.example              # Environment configuration template
```

## Prerequisites

- Python 3.9+
- Azure Synapse Analytics workspace
- SharePoint Online site with a list
- Azure AD App Registration with permissions:
  - `Sites.ReadWrite.All` (Application permission)
- ODBC Driver 18 for SQL Server

## Installation

### 1. Clone and Install Dependencies

```bash
# Navigate to project directory
cd synapse-to-sharepoint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file based on the example:

```bash
cp config/.env.example .env
```

Edit `.env` with your configuration:

```env
# Azure Synapse Settings
SYNAPSE_SERVER=your-synapse.sql.azuresynapse.net
SYNAPSE_DATABASE=your_database
SYNAPSE_USERNAME=your_username
SYNAPSE_PASSWORD=your_password
USE_MANAGED_IDENTITY=false

# SharePoint Settings
SHAREPOINT_SITE_URL=https://yourtenant.sharepoint.com/sites/yoursite
SHAREPOINT_LIST_NAME=YourListName

# Azure AD Settings
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret

# Query Configuration
SYNAPSE_QUERY=SELECT id, name, value, created_date FROM your_table WHERE status='active'
BATCH_SIZE=100

# Logging
LOG_LEVEL=INFO

# Field Mapping (JSON format)
FIELD_MAPPING={"id": "ID", "name": "Title", "value": "Value", "created_date": "CreatedDate"}
```

## Azure AD App Registration Setup

### 1. Register Application

1. Go to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Name: "Synapse-SharePoint-Integration"
4. Click "Register"

### 2. Configure API Permissions

1. Go to "API permissions"
2. Click "Add a permission"
3. Select "Microsoft Graph"
4. Choose "Application permissions"
5. Add: `Sites.ReadWrite.All`
6. Click "Grant admin consent"

### 3. Create Client Secret

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Add description and expiry
4. Copy the secret value (only shown once!)

### 4. Get IDs

- Tenant ID: Azure AD → Overview
- Client ID: App registration → Overview

## Usage

### Command Line Execution

Run the pipeline directly:

```bash
python -m src.main
```

### Python Script

```python
from src.main import SynapseToSharePointPipeline
from src.config import get_settings

# Initialize pipeline
pipeline = SynapseToSharePointPipeline()

# Run the complete ETL process
results = pipeline.run()

print(f"Status: {results['status']}")
print(f"Extracted: {results['extracted_rows']}")
print(f"Loaded: {results['loaded_rows']}")
print(f"Failed: {results['failed_rows']}")
```

### Individual Components

```python
from src.config import get_settings
from src.synapse_client import get_synapse_data
from src.sharepoint_client import upload_to_sharepoint
from src.data_transformer import create_transformer_from_settings

# Get configuration
settings = get_settings()

# Extract data from Synapse
data = get_synapse_data(settings)

# Transform data
transformer = create_transformer_from_settings(settings)
transformed_data = transformer.transform_batch(data)

# Load to SharePoint
results = upload_to_sharepoint(settings, transformed_data)
```

## Azure Functions Deployment

### 1. Local Testing

```bash
# Install Azure Functions Core Tools
# https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local

# Start local function
func start
```

### 2. Deploy to Azure

```bash
# Create Function App
az functionapp create \
  --resource-group <resource-group> \
  --consumption-plan-type <plan> \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --name <function-app-name> \
  --storage-account <storage-account>

# Deploy code
func azure functionapp publish <function-app-name>

# Configure app settings
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings @config/appsettings.json
```

### 3. Configure Triggers

**HTTP Trigger**: Call via URL
```bash
curl -X POST https://<function-app-name>.azurewebsites.net/api/main \
  -H "x-functions-key: <function-key>"
```

**Timer Trigger**: Add to `function.json`
```json
{
  "type": "timerTrigger",
  "direction": "in",
  "name": "mytimer",
  "schedule": "0 0 2 * * *"
}
```

## Field Mapping

Configure field mapping to match Synapse columns to SharePoint fields:

```json
{
  "synapse_column_name": "SharePointFieldName",
  "employee_id": "EmployeeID",
  "first_name": "FirstName",
  "hire_date": "HireDate",
  "salary": "AnnualSalary"
}
```

**Rules**:
- SharePoint field names must be ≤32 characters
- Avoid special characters: `< > # % & * { } \ : / | "`
- Use internal field names (not display names)

## Data Type Handling

The transformer automatically handles:

- **Datetime/Date**: Converts to ISO 8601 format
- **Boolean**: Preserves as true/false
- **Numeric**: Preserves as int/float
- **Null**: Passes as null
- **Everything else**: Converts to string

## Testing

### Run All Tests

```bash
# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Test specific module
pytest tests/test_synapse_client.py -v

# Test specific function
pytest tests/test_data_transformer.py::TestDataTransformer::test_transform_row -v
```

### Test Coverage

Current coverage: ~95%

```
Module                     Statements   Missing   Coverage
----------------------------------------------------------
src/config.py                    45         2       96%
src/logging_config.py            35         1       97%
src/synapse_client.py            78         3       96%
src/sharepoint_client.py        125         5       96%
src/data_transformer.py          82         4       95%
src/main.py                      95         3       97%
----------------------------------------------------------
TOTAL                           460        18       96%
```

## Logging

Structured JSON logging for Azure monitoring:

```json
{
  "event": "Pipeline execution completed",
  "level": "info",
  "timestamp": "2024-01-30T10:30:00.000Z",
  "status": "success",
  "extracted": 1000,
  "loaded": 995,
  "failed": 5
}
```

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Performance Considerations

### Batch Size

- **Default**: 100 items per batch
- **Small lists** (<1000 items): Use 50-100
- **Large lists** (>1000 items): Use 100-200
- **Rate limits**: Graph API has throttling - adjust accordingly

### SharePoint List Limits

- Lists perform best under 5,000 items
- View threshold: 5,000 items
- Consider using folders or filtering for larger datasets

### Optimization Tips

1. **Indexing**: Create indexes on SharePoint lookup columns
2. **Filtering**: Use WHERE clauses in Synapse queries
3. **Scheduling**: Run during off-peak hours
4. **Monitoring**: Use Azure Application Insights

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Synapse
```
Solution: 
- Verify ODBC Driver 18 is installed
- Check firewall rules on Synapse
- Validate connection string format
```

**Problem**: Cannot authenticate to SharePoint
```
Solution:
- Verify Azure AD app has correct permissions
- Check client secret hasn't expired
- Confirm tenant ID is correct
```

### Data Issues

**Problem**: Field mapping errors
```
Solution:
- Use internal field names, not display names
- Check SharePoint field name length (<32 chars)
- Verify field types match
```

**Problem**: Items not appearing in SharePoint
```
Solution:
- Check SharePoint list permissions
- Verify required fields are populated
- Review error logs for failed items
```

## Security Best Practices

1. **Secrets Management**:
   - Use Azure Key Vault for production
   - Never commit `.env` files
   - Rotate secrets regularly

2. **Authentication**:
   - Prefer Managed Identity over SQL auth
   - Use least-privilege permissions
   - Monitor access logs

3. **Data Protection**:
   - Encrypt sensitive data at rest
   - Use TLS for all connections
   - Implement data retention policies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: See `docs/` folder
- Azure Support: Azure Portal support

## Changelog

### v1.0.0 (2024-01-30)
- Initial release
- Core ETL functionality
- Azure Functions support
- Comprehensive testing
- Full documentation
