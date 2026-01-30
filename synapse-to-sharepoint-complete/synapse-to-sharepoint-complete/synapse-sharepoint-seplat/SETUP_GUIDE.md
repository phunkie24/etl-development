# SEPLAT Energy - Complete Setup Guide

## Overview
This guide will walk you through setting up the Synapse to SharePoint integration for your 6 tables:
1. daily_field_parameters
2. daily_production  
3. daily_well_parameters
4. headerid
5. pressure
6. welltest

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] Access to Azure Synapse workspace (SEP_EDW database)
- [ ] Permissions to create Azure AD app registrations
- [ ] Admin access to SharePoint site: https://seplatenergy.sharepoint.com/sites/SIMS/Others/ABERDEEN
- [ ] Python 3.9+ installed
- [ ] ODBC Driver 18 for SQL Server installed

## Step-by-Step Setup

### 1. Install ODBC Driver (One-time)

**Windows:**
```
Download and install from:
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo apt-get install -y msodbcsql18
```

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18
```

### 2. Extract and Setup Project

```bash
# Extract the zip files
unzip synapse-to-sharepoint.zip
cd synapse-to-sharepoint

# There's a folder synapse-sharepoint-seplat with your custom configuration
cd synapse-sharepoint-seplat

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies (from parent directory)
pip install -r ../requirements.txt
```

### 3. Create Azure AD App Registration

#### 3.1 Register Application
1. Go to https://portal.azure.com
2. Navigate to: **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Fill in:
   - Name: `SEPLAT-Synapse-SharePoint-Integration`
   - Supported account types: `Accounts in this organizational directory only`
   - Redirect URI: Leave blank
5. Click **Register**

#### 3.2 Note Your IDs
After registration, note these values:
- **Application (client) ID**: Found on Overview page
- **Directory (tenant) ID**: Found on Overview page

#### 3.3 Create Client Secret
1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Description: `Integration Secret`
4. Expires: Choose `24 months` or as per policy
5. Click **Add**
6. **IMMEDIATELY COPY THE VALUE** (shown only once!)

#### 3.4 Grant Permissions
1. Go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions**
5. Search and add: `Sites.ReadWrite.All`
6. Click **Add permissions**
7. Click **Grant admin consent for [Your Organization]**
8. Confirm by clicking **Yes**

### 4. Configure Environment File

Edit `.env.seplat` with your values:

```bash
# Use a text editor (notepad, nano, vim, etc.)
nano .env.seplat  # or: notepad .env.seplat
```

Update these values:

```env
# Azure Synapse - Update these
SYNAPSE_SERVER=<your-workspace-name>.sql.azuresynapse.net
SYNAPSE_DATABASE=SEP_EDW
SYNAPSE_USERNAME=<your_sql_username>
SYNAPSE_PASSWORD=<your_sql_password>
USE_MANAGED_IDENTITY=false

# SharePoint - Already configured
SHAREPOINT_SITE_URL=https://seplatenergy.sharepoint.com/sites/SIMS/Others/ABERDEEN

# Azure AD - Update with values from Step 3
TENANT_ID=<paste_tenant_id_here>
CLIENT_ID=<paste_client_id_here>
CLIENT_SECRET=<paste_client_secret_here>

# Keep these defaults
BATCH_SIZE=100
LOG_LEVEL=INFO
FIELD_MAPPING={}
```

**Save and close the file**

### 5. Test Connections

```bash
python test_connection.py
```

Expected output:
```
==================================================
SEPLAT ENERGY - CONNECTION TEST
==================================================

Testing Synapse Connection
==================================================
✓ Connected to Synapse successfully
✓ Found 6 tables in oml40 schema:
  - daily_field_parameters
  - daily_production
  - daily_well_parameters
  - headerid
  - pressure
  - welltest
✅ Synapse connection test PASSED

Testing SharePoint Connection
==================================================
✓ Authenticated to SharePoint successfully
✓ Site ID retrieved
✓ Found X lists in SharePoint site
✅ SharePoint connection test PASSED

TEST SUMMARY
==================================================
Synapse:    ✅ PASS
SharePoint: ✅ PASS

✅ All tests passed! You're ready to sync data.
```

**If tests fail**, check the troubleshooting section in the output.

### 6. Inspect Table Schemas

```bash
python inspect_schema.py
```

This will show you:
- All 6 tables and their columns
- Data types
- Sample data
- Suggested SharePoint field types
- Row counts

**Save this output** - you'll use it to create SharePoint lists.

### 7. Create SharePoint Lists

For each of the 6 tables, create a SharePoint list:

#### 7.1 Create Lists
1. Go to: https://seplatenergy.sharepoint.com/sites/SIMS/Others/ABERDEEN
2. Click **New** → **List**
3. Choose **Blank list**
4. Create these 6 lists:

| List Name | For Table |
|-----------|-----------|
| DailyFieldParameters | daily_field_parameters |
| DailyProduction | daily_production |
| DailyWellParameters | daily_well_parameters |
| HeaderID | headerid |
| Pressure | pressure |
| WellTest | welltest |

#### 7.2 Add Columns
For each list, add columns based on the output from `inspect_schema.py`:

**Example for DailyProduction:**
- List settings → Add column
- Add each column from your Synapse table
- Use the suggested SharePoint types from inspect_schema.py output

**Important:**
- Use internal names (no spaces): `ProductionDate` not "Production Date"
- Choose correct field types (Number, Date, Text, etc.)
- Make required fields match your data
- The Title column already exists - you can rename or hide it

### 8. Run Your First Sync

#### Option A: Sync All Tables
```bash
python sync_all_tables.py
```

#### Option B: Sync One Table (for testing)
```bash
python sync_all_tables.py --tables daily_production
```

#### Option C: Sync Specific Tables
```bash
python sync_all_tables.py --tables daily_production pressure welltest
```

Expected output:
```
==================================================
SEPLAT ENERGY - MULTI-TABLE SYNC RESULTS
==================================================
Start Time: 2024-01-30T10:30:00
End Time: 2024-01-30T10:32:15
Overall Status: SUCCESS
Total Records Loaded: 15,423
Total Records Failed: 0

Individual Table Results:
--------------------------------------------------
📊 DailyFieldParameters
   Source: oml40.daily_field_parameters
   Status: SUCCESS
   Extracted: 3,421
   Loaded: 3,421
   Failed: 0
...
```

### 9. Verify Data in SharePoint

1. Go to your SharePoint site
2. Check each list
3. Verify data appears correctly
4. Check a few records to ensure field mapping is correct

### 10. Schedule Automatic Syncs

#### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
   - Name: `SEPLAT Synapse to SharePoint Sync`
   - Trigger: Daily at 2:00 AM
   - Action: Start a program
     - Program: `C:\path\to\synapse-sharepoint-seplat\venv\Scripts\python.exe`
     - Arguments: `sync_all_tables.py`
     - Start in: `C:\path\to\synapse-sharepoint-seplat`

#### Linux/Mac Cron

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/synapse-sharepoint-seplat && ./venv/bin/python sync_all_tables.py >> /path/to/logs/sync.log 2>&1
```

## Customization

### Filtering Data

Edit `table_config.py` to add WHERE clauses:

```python
"daily_production": {
    "query": """
        SELECT *
        FROM oml40.daily_production
        WHERE production_date >= DATEADD(day, -90, GETDATE())  -- Last 90 days only
        ORDER BY production_date DESC
    """
}
```

### Field Mapping

If SharePoint field names differ from Synapse columns:

```python
"daily_production": {
    "field_mapping": {
        "prod_date": "ProductionDate",
        "well_id": "WellID",
        "oil_bopd": "OilRate",
        "gas_mcfd": "GasRate"
    }
}
```

### Batch Size

Adjust in `.env.seplat`:
```env
BATCH_SIZE=50  # Smaller for better error recovery
# or
BATCH_SIZE=200  # Larger for faster sync
```

## Troubleshooting

### Issue: "Cannot connect to Synapse"
**Solutions:**
1. Check Synapse firewall: Azure Portal → Synapse workspace → Networking → Firewall rules
2. Add your IP address or enable "Allow Azure services"
3. Verify credentials in `.env.seplat`
4. Test: `ping <your-workspace>.sql.azuresynapse.net`

### Issue: "ODBC Driver not found"
**Solutions:**
- Reinstall ODBC Driver 18 (see Step 1)
- Windows: Check "ODBC Data Sources (64-bit)" in Control Panel
- Linux: Run `odbcinst -j` to verify installation

### Issue: "Token acquisition failed"
**Solutions:**
1. Verify Azure AD app has `Sites.ReadWrite.All` permission
2. Check admin consent was granted (green checkmark in Azure Portal)
3. Verify client secret hasn't expired
4. Wait 5-10 minutes after granting permissions

### Issue: "List not found"
**Solutions:**
1. List names are case-sensitive - check exact match
2. Ensure lists exist in SharePoint
3. Verify you have permissions to the site
4. Run `test_connection.py` to see available lists

### Issue: "Field name is invalid"
**Solutions:**
1. SharePoint field names: max 32 characters
2. Avoid special characters: `< > # % & * { } \ : / | "`
3. Use internal field names (no spaces)
4. Update field_mapping in `table_config.py`

### Issue: "Some items failed to load"
**Solutions:**
1. Check logs for specific error messages
2. Verify required SharePoint fields are populated
3. Check data type mismatches
4. Review field length limits

## Monitoring

### View Logs
```bash
# Run with logging to file
python sync_all_tables.py 2>&1 | tee logs/sync_$(date +%Y%m%d_%H%M%S).log
```

### Check Last Run
Look at the output summary after each run

### Set Up Alerts
Use Task Scheduler or cron to email results:
```bash
python sync_all_tables.py 2>&1 | mail -s "Synapse Sync Results" admin@seplatenergy.com
```

## Security Best Practices

1. ✅ Never commit `.env.seplat` to git
2. ✅ Use strong passwords
3. ✅ Rotate client secrets every 6-12 months
4. ✅ Grant minimum required permissions
5. ✅ Enable MFA on admin accounts
6. ✅ Review access logs regularly

## Support Contacts

**For technical issues:**
- Azure Synapse: Your Azure administrator
- SharePoint: Your SharePoint administrator  
- Azure AD: Your identity team

**For this script:**
- Check README.md in parent directory
- Review error messages in logs
- Run test scripts to isolate issues

## Next Steps After Setup

1. ✅ Set up monitoring/alerting
2. ✅ Document field mappings
3. ✅ Train users on new SharePoint lists
4. ✅ Set up data retention policies
5. ✅ Plan for scaling if data grows
6. ✅ Schedule regular maintenance

## Quick Reference Commands

```bash
# Test connections
python test_connection.py

# View table schemas
python inspect_schema.py

# Sync all tables
python sync_all_tables.py

# Sync specific tables
python sync_all_tables.py --tables daily_production pressure

# View available tables
python sync_all_tables.py --help
```

## Appendix: File Descriptions

| File | Purpose |
|------|---------|
| `.env.seplat` | Your configuration (DO NOT COMMIT) |
| `table_config.py` | 6 table definitions and queries |
| `sync_all_tables.py` | Main sync script |
| `inspect_schema.py` | View Synapse table structures |
| `test_connection.py` | Test Synapse and SharePoint connectivity |
| `README.md` | General documentation |
| `SETUP_GUIDE.md` | This file |

---

**Good luck with your deployment! 🚀**

If you encounter any issues not covered in this guide, refer to the main documentation in the parent `synapse-to-sharepoint` folder.
