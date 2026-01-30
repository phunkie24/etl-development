# SEPLAT Energy - Synapse to SharePoint Integration

Custom configuration for deploying 6 tables from Azure Synapse (SEP_EDW database, oml40 schema) to SharePoint lists.

## Your Configuration

### Synapse Database
- **Database**: SEP_EDW
- **Schema**: oml40
- **Tables**: 6 tables (daily_field_parameters, daily_production, daily_well_parameters, headerid, pressure, welltest)

### SharePoint Site
- **Site URL**: https://seplatenergy.sharepoint.com/sites/SIMS/Others/ABERDEEN
- **Lists**: Will be created/mapped to match table names

## Quick Setup (10 Minutes)

### Step 1: Install Dependencies

```bash
# Navigate to the parent directory (synapse-to-sharepoint)
cd ../synapse-to-sharepoint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure Azure AD App

1. Go to [Azure Portal](https://portal.azure.com)
2. Azure Active Directory → App registrations → New registration
3. Name: `SEPLAT-Synapse-SharePoint`
4. Register

**Add Permissions:**
- API permissions → Add permission
- Microsoft Graph → Application permissions
- Add: `Sites.ReadWrite.All`
- Grant admin consent

**Create Secret:**
- Certificates & secrets → New client secret
- Copy the value (only shown once!)

**Get IDs:**
- Tenant ID: Azure AD → Overview
- Client ID: App registration → Overview

### Step 3: Update Configuration

Edit `.env.seplat`:

```bash
# Update these values
SYNAPSE_SERVER=<your-synapse>.sql.azuresynapse.net
SYNAPSE_USERNAME=<your_username>
SYNAPSE_PASSWORD=<your_password>

TENANT_ID=<your-tenant-id>
CLIENT_ID=<your-client-id>
CLIENT_SECRET=<your-client-secret>
```

### Step 4: Inspect Your Tables

This script will show you the structure of all 6 tables:

```bash
cd synapse-sharepoint-seplat
python inspect_schema.py
```

This will display:
- Column names and types
- Row counts
- Sample data
- Suggested SharePoint field types

### Step 5: Create SharePoint Lists

Create these 6 lists in your SharePoint site:
https://seplatenergy.sharepoint.com/sites/SIMS/Others/ABERDEEN

**Lists to create:**
1. `DailyFieldParameters` - for oml40.daily_field_parameters
2. `DailyProduction` - for oml40.daily_production
3. `DailyWellParameters` - for oml40.daily_well_parameters
4. `HeaderID` - for oml40.headerid
5. `Pressure` - for oml40.pressure
6. `WellTest` - for oml40.welltest

**For each list:**
1. Go to Site Contents → New → List
2. Create from blank
3. Add columns matching your Synapse table structure (use output from Step 4)

### Step 6: Run the Sync

#### Sync All Tables
```bash
python sync_all_tables.py
```

#### Sync Specific Tables
```bash
# Sync only daily_production and pressure
python sync_all_tables.py --tables daily_production pressure
```

## Configuration Files

### table_config.py
Defines the 6 tables and their mappings:
- Source table (schema.table)
- Target SharePoint list
- SQL query to extract data
- Field mapping (if needed)

### .env.seplat
Environment configuration:
- Synapse connection details
- SharePoint site URL
- Azure AD credentials

### sync_all_tables.py
Main sync script with multi-table support

## Customizing Queries

Edit `table_config.py` to customize queries for each table:

```python
"daily_production": {
    "query": """
        SELECT 
            production_date,
            well_id,
            oil_rate,
            gas_rate,
            water_rate
        FROM oml40.daily_production
        WHERE production_date >= DATEADD(day, -30, GETDATE())  -- Last 30 days
        ORDER BY production_date DESC
    """
}
```

## Field Mapping

If your SharePoint field names differ from Synapse columns, update the field_mapping:

```python
"daily_production": {
    "field_mapping": {
        "production_date": "ProductionDate",
        "well_id": "WellID",
        "oil_rate": "OilRate",
        "gas_rate": "GasRate"
    }
}
```

## Scheduling

### Option 1: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → Daily
3. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `sync_all_tables.py`
   - Start in: `C:\path\to\synapse-sharepoint-seplat`

### Option 2: Linux Cron

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/synapse-sharepoint-seplat && /path/to/venv/bin/python sync_all_tables.py
```

### Option 3: Azure Functions

Deploy to Azure Functions for serverless execution (see main README.md)

## Monitoring

### View Logs
The script outputs structured JSON logs:

```bash
python sync_all_tables.py 2>&1 | tee sync_$(date +%Y%m%d).log
```

### Check Results
After running, you'll see:
```
==================================================
SEPLAT ENERGY - MULTI-TABLE SYNC RESULTS
==================================================
Overall Status: SUCCESS
Total Records Loaded: 15,423
Total Records Failed: 0

Individual Table Results:
--------------------------------------------------
📊 DailyFieldParameters
   Status: SUCCESS
   Extracted: 3,421
   Loaded: 3,421
   Failed: 0
...
```

## Troubleshooting

### "Cannot connect to Synapse"
- Check if your IP is allowed in Synapse firewall
- Verify username/password
- Ensure ODBC Driver 18 is installed

### "List not found in SharePoint"
- Verify list names match exactly (case-sensitive)
- Check you have permissions to the site
- Lists must exist before running sync

### "Field name is invalid"
- Use internal field names (no spaces)
- Check SharePoint field name restrictions
- Update field_mapping in table_config.py

### "Token acquisition failed"
- Verify Azure AD app has Sites.ReadWrite.All permission
- Check admin consent was granted
- Verify client secret hasn't expired

## Performance Tips

1. **Batch Size**: Adjust in .env.seplat (default: 100)
   - Smaller batches: Better error recovery
   - Larger batches: Faster overall sync

2. **Filtering**: Add WHERE clauses to queries
   ```sql
   WHERE production_date >= DATEADD(day, -90, GETDATE())
   ```

3. **Indexing**: Create indexes on SharePoint lookup columns

4. **Scheduling**: Run during off-peak hours

## Security Best Practices

1. **Never commit .env.seplat** to version control
2. Use Azure Key Vault for production
3. Rotate secrets regularly
4. Use Managed Identity when possible
5. Grant minimum required permissions

## Support

For issues specific to SEPLAT configuration:
1. Check the main README.md for general issues
2. Run `inspect_schema.py` to verify table access
3. Test connection to both Synapse and SharePoint separately
4. Check Azure AD app permissions

## File Structure

```
synapse-sharepoint-seplat/
├── .env.seplat              # Your environment config (DO NOT COMMIT)
├── table_config.py          # 6 table definitions
├── sync_all_tables.py       # Main sync script
├── inspect_schema.py        # Schema inspection tool
└── README.md               # This file
```

## Next Steps

1. ✅ Configure .env.seplat with your credentials
2. ✅ Run inspect_schema.py to see table structures
3. ✅ Create 6 SharePoint lists
4. ✅ Run sync_all_tables.py
5. ✅ Schedule automatic syncs
6. ✅ Monitor and maintain

Good luck! 🚀
