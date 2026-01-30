# Quick Start Guide

Get up and running with Synapse to SharePoint integration in 10 minutes.

## Step 1: Install Dependencies (2 min)

```bash
# Clone repository
cd synapse-to-sharepoint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Azure AD App Setup (3 min)

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: **Azure Active Directory** → **App registrations** → **New registration**
3. Name: `Synapse-SharePoint-Integration`
4. Click **Register**

### Add Permissions:
1. Go to **API permissions** → **Add a permission**
2. Select **Microsoft Graph** → **Application permissions**
3. Add: `Sites.ReadWrite.All`
4. Click **Grant admin consent for [Your Tenant]**

### Create Secret:
1. Go to **Certificates & secrets** → **New client secret**
2. Description: `Integration Secret`
3. Expiry: Choose duration
4. **Copy the secret value** (shown only once!)

### Get IDs:
- **Tenant ID**: Azure AD → Overview → Tenant ID
- **Client ID**: App registration → Overview → Application (client) ID

## Step 3: Configure Environment (2 min)

Create `.env` file in project root:

```bash
# Copy template
cp config/.env.example .env

# Edit with your values
nano .env  # or use your favorite editor
```

**Minimum required settings:**

```env
# Synapse
SYNAPSE_SERVER=mysynapse.sql.azuresynapse.net
SYNAPSE_DATABASE=mydb
SYNAPSE_USERNAME=myuser
SYNAPSE_PASSWORD=mypassword

# SharePoint
SHAREPOINT_SITE_URL=https://mytenant.sharepoint.com/sites/mysite
SHAREPOINT_LIST_NAME=MyList

# Azure AD (from Step 2)
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret-value

# Query
SYNAPSE_QUERY=SELECT TOP 10 * FROM MyTable
```

## Step 4: Test Connection (1 min)

```python
# test_connection.py
from src.config import get_settings
from src.synapse_client import SynapseClient
from src.sharepoint_client import SharePointClient

settings = get_settings()

# Test Synapse
print("Testing Synapse connection...")
with SynapseClient(settings) as client:
    data = client.execute_query("SELECT TOP 1 * FROM sys.tables")
    print(f"✓ Synapse connected! Found {len(data)} table(s)")

# Test SharePoint
print("\nTesting SharePoint connection...")
with SharePointClient(settings) as client:
    site_id = client.get_site_id()
    print(f"✓ SharePoint connected! Site ID: {site_id[:20]}...")

print("\n✓ All connections successful!")
```

Run test:
```bash
python test_connection.py
```

## Step 5: Run Your First Pipeline (2 min)

```bash
# Run the pipeline
python -m src.main
```

Expected output:
```
==================================================
Pipeline Execution Results
==================================================
Status: success
Extracted Rows: 10
Transformed Rows: 10
Successfully Loaded: 10
Failed: 0
==================================================
```

## Next Steps

### Configure Field Mapping

Edit `.env` to map Synapse columns to SharePoint fields:

```env
FIELD_MAPPING={"employee_id": "EmployeeID", "first_name": "FirstName", "last_name": "LastName"}
```

### Schedule Automatic Runs

**Option 1: Cron (Linux/Mac)**
```bash
# Edit crontab
crontab -e

# Add line (runs daily at 2 AM)
0 2 * * * cd /path/to/project && /path/to/venv/bin/python -m src.main
```

**Option 2: Task Scheduler (Windows)**
1. Open Task Scheduler
2. Create Basic Task
3. Action: Start a program
4. Program: `C:\path\to\venv\Scripts\python.exe`
5. Arguments: `-m src.main`
6. Start in: `C:\path\to\project`

**Option 3: Deploy to Azure Functions** (See DEPLOYMENT.md)

### Monitor Execution

View logs:
```bash
# Logs are written to console in JSON format
python -m src.main 2>&1 | tee pipeline.log
```

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html
```

## Common Issues

### Issue: "ODBC Driver not found"
**Solution**: Install ODBC Driver 18
- Linux: `sudo apt-get install msodbcsql18`
- Mac: `brew tap microsoft/mssql-release && brew install msodbcsql18`
- Windows: Download from [Microsoft](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### Issue: "Cannot connect to Synapse"
**Solution**: Check firewall rules
1. Go to Synapse workspace in Azure Portal
2. Navigate to: Networking → Firewall rules
3. Add your IP address or enable "Allow Azure services"

### Issue: "Insufficient permissions on SharePoint"
**Solution**: 
1. Verify app has `Sites.ReadWrite.All` permission
2. Ensure admin consent was granted
3. Wait 5-10 minutes for permissions to propagate

### Issue: "Field name is invalid"
**Solution**: SharePoint field restrictions
- Use internal field names (not display names)
- Max 32 characters
- No special chars: `< > # % & * { } \ : / | "`

## Example Queries

### Get all active employees:
```sql
SELECT 
    employee_id,
    first_name,
    last_name,
    department,
    hire_date,
    salary
FROM HR.Employees
WHERE status = 'Active'
ORDER BY hire_date DESC
```

### Get sales data for last month:
```sql
SELECT 
    order_id,
    customer_name,
    order_date,
    total_amount,
    status
FROM Sales.Orders
WHERE order_date >= DATEADD(month, -1, GETDATE())
```

## Tips for Success

1. **Start Small**: Test with `SELECT TOP 100` first
2. **Check SharePoint First**: Verify list exists and you have permissions
3. **Use Field Mapping**: Always map to SharePoint internal field names
4. **Monitor Batch Size**: Adjust based on performance (default: 100)
5. **Enable Logging**: Use `LOG_LEVEL=DEBUG` for troubleshooting

## Getting Help

- **Documentation**: See README.md for full details
- **Issues**: Check existing test cases in `tests/` folder
- **Deployment**: See DEPLOYMENT.md for Azure Functions setup

## Congratulations! 🎉

You've successfully set up Synapse to SharePoint integration!
