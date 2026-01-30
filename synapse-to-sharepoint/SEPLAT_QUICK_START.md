# SEPLAT Energy - Quick Start Guide

## What You Have

A complete Python solution to sync 6 tables from your Azure Synapse database to SharePoint:

**From:** Azure Synapse (SEP_EDW database, oml40 schema)
- daily_field_parameters
- daily_production
- daily_well_parameters
- headerid
- pressure
- welltest

**To:** SharePoint (https://seplatenergy.sharepoint.com/sites/SIMS/Others/ABERDEEN)

## Package Contents

You have TWO zip files:

1. **synapse-to-sharepoint.zip** (33 KB)
   - Core framework with all modules
   - Testing suite
   - Full documentation
   - Azure Functions support

2. **synapse-to-sharepoint-complete.zip** (51 KB) ⭐ **USE THIS ONE**
   - Everything from #1 PLUS
   - Custom SEPLAT configuration
   - Multi-table sync scripts
   - Your 6 tables pre-configured
   - SEPLAT-specific documentation

## 5-Minute Quick Start

### 1. Extract Files
```bash
unzip synapse-to-sharepoint-complete.zip
cd synapse-to-sharepoint
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

### 3. Get Your Azure AD Credentials

**You need 3 things:**
1. **Tenant ID** - Your Azure AD tenant
2. **Client ID** - From Azure AD app registration
3. **Client Secret** - From Azure AD app registration

**To create them:**
1. Go to https://portal.azure.com
2. Azure Active Directory → App registrations → New registration
3. Name: "SEPLAT-Synapse-SharePoint"
4. Grant permission: Sites.ReadWrite.All (Microsoft Graph)
5. Create client secret
6. Copy all 3 values

### 4. Configure
```bash
cd synapse-sharepoint-seplat
cp .env.seplat .env.seplat.backup  # Keep a backup
nano .env.seplat  # or use any text editor
```

**Update these lines:**
```env
SYNAPSE_SERVER=<your-synapse-workspace>.sql.azuresynapse.net
SYNAPSE_USERNAME=<your_username>
SYNAPSE_PASSWORD=<your_password>

TENANT_ID=<your_tenant_id>
CLIENT_ID=<your_client_id>
CLIENT_SECRET=<your_client_secret>
```

### 5. Test Connection
```bash
python test_connection.py
```

Should show:
```
✅ Synapse connection test PASSED
✅ SharePoint connection test PASSED
```

### 6. Check Your Tables
```bash
python inspect_schema.py
```

This shows all 6 tables, their columns, and sample data.

### 7. Create SharePoint Lists

Go to: https://seplatenergy.sharepoint.com/sites/SIMS/Others/ABERDEEN

Create these 6 lists (New → List → Blank):
1. DailyFieldParameters
2. DailyProduction
3. DailyWellParameters
4. HeaderID
5. Pressure
6. WellTest

For each list, add columns matching your Synapse table structure (from step 6 output).

### 8. Run Sync
```bash
# Sync all tables
python sync_all_tables.py

# OR sync just one table first (recommended)
python sync_all_tables.py --tables daily_production
```

### 9. Verify
1. Check SharePoint lists
2. Verify data loaded correctly
3. Check counts match

### 10. Schedule
Set up daily automatic sync (see SETUP_GUIDE.md for details)

## Project Structure

```
synapse-to-sharepoint/
├── src/                              # Core modules (don't modify)
│   ├── synapse_client.py            # Synapse connection
│   ├── sharepoint_client.py         # SharePoint API
│   └── ...                          # Other core modules
│
├── synapse-sharepoint-seplat/       # YOUR CUSTOM CONFIGURATION ⭐
│   ├── .env.seplat                  # Your settings (UPDATE THIS)
│   ├── table_config.py              # 6 table definitions
│   ├── sync_all_tables.py           # Main sync script
│   ├── test_connection.py           # Connection test
│   ├── inspect_schema.py            # View table schemas
│   ├── SETUP_GUIDE.md              # Detailed setup guide
│   └── README.md                    # SEPLAT documentation
│
├── tests/                           # Test suite
├── README.md                        # General documentation
└── requirements.txt                 # Dependencies
```

## Key Files for SEPLAT

**Work in the `synapse-sharepoint-seplat/` folder:**

1. **.env.seplat** - Your configuration (UPDATE THIS FIRST)
2. **table_config.py** - Defines your 6 tables
3. **sync_all_tables.py** - Runs the sync
4. **test_connection.py** - Tests connections
5. **inspect_schema.py** - Shows table structure

## Common Commands

```bash
# All commands run from: synapse-sharepoint-seplat/

# Test connections
python test_connection.py

# View your tables
python inspect_schema.py

# Sync all 6 tables
python sync_all_tables.py

# Sync specific tables
python sync_all_tables.py --tables daily_production pressure

# See available options
python sync_all_tables.py --help
```

## Customization

### Change Date Range
Edit `table_config.py`:
```python
"daily_production": {
    "query": """
        SELECT *
        FROM oml40.daily_production
        WHERE production_date >= DATEADD(day, -30, GETDATE())  -- Last 30 days
    """
}
```

### Change Batch Size
Edit `.env.seplat`:
```env
BATCH_SIZE=50  # Process 50 items at a time
```

### Map Field Names
If SharePoint field names differ, edit `table_config.py`:
```python
"daily_production": {
    "field_mapping": {
        "prod_date": "ProductionDate",
        "well_id": "WellID"
    }
}
```

## Troubleshooting

### "Cannot connect to Synapse"
- Check firewall rules in Azure Portal
- Verify username/password
- Install ODBC Driver 18

### "List not found"
- Verify list exists in SharePoint
- Check spelling (case-sensitive)
- Run test_connection.py to see available lists

### "Some items failed"
- Check required fields in SharePoint
- Verify data types match
- Review error messages in output

## Documentation

| File | What's Inside |
|------|---------------|
| synapse-sharepoint-seplat/SETUP_GUIDE.md | Step-by-step setup (START HERE) |
| synapse-sharepoint-seplat/README.md | SEPLAT-specific docs |
| README.md (parent folder) | General framework docs |
| DEPLOYMENT.md | Azure Functions deployment |

## Support

1. Read synapse-sharepoint-seplat/SETUP_GUIDE.md for detailed instructions
2. Run test_connection.py to diagnose issues
3. Check error messages in script output
4. Review logs for detailed debugging

## What's Next?

1. ✅ Extract synapse-to-sharepoint-complete.zip
2. ✅ Follow steps 1-10 above
3. ✅ Read synapse-sharepoint-seplat/SETUP_GUIDE.md for details
4. ✅ Schedule automatic daily syncs
5. ✅ Monitor and maintain

---

**Ready to start? Extract `synapse-to-sharepoint-complete.zip` and go to the `synapse-sharepoint-seplat` folder!**

For detailed instructions, open: `synapse-sharepoint-seplat/SETUP_GUIDE.md`

Good luck! 🚀
