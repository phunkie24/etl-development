"""
Schema inspection script for SEPLAT Energy tables.
Inspects the structure of Synapse tables and suggests SharePoint list configurations.
"""
import sys
import os
from typing import Dict, List
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'synapse-to-sharepoint'))

from src.config import Settings
from src.synapse_client import SynapseClient
from table_config import TABLES_CONFIG


def get_table_schema(client: SynapseClient, schema: str, table: str) -> List[Dict]:
    """Get column information for a table."""
    query = f"""
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        IS_NULLABLE,
        CHARACTER_MAXIMUM_LENGTH,
        NUMERIC_PRECISION,
        NUMERIC_SCALE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = '{table}'
    ORDER BY ORDINAL_POSITION
    """
    
    return client.execute_query(query)


def get_row_count(client: SynapseClient, schema: str, table: str) -> int:
    """Get approximate row count for a table."""
    query = f"SELECT COUNT(*) as row_count FROM {schema}.{table}"
    result = client.execute_query(query)
    return result[0]['row_count'] if result else 0


def map_sql_to_sharepoint_type(sql_type: str) -> str:
    """Map SQL data type to suggested SharePoint field type."""
    sql_type = sql_type.lower()
    
    type_mapping = {
        'int': 'Number',
        'bigint': 'Number',
        'smallint': 'Number',
        'tinyint': 'Number',
        'decimal': 'Number',
        'numeric': 'Number',
        'float': 'Number',
        'real': 'Number',
        'money': 'Currency',
        'smallmoney': 'Currency',
        'bit': 'Yes/No',
        'date': 'Date',
        'datetime': 'Date and Time',
        'datetime2': 'Date and Time',
        'smalldatetime': 'Date and Time',
        'time': 'Single line of text',
        'varchar': 'Single line of text',
        'nvarchar': 'Single line of text',
        'char': 'Single line of text',
        'nchar': 'Single line of text',
        'text': 'Multiple lines of text',
        'ntext': 'Multiple lines of text',
        'uniqueidentifier': 'Single line of text'
    }
    
    return type_mapping.get(sql_type, 'Single line of text')


def inspect_all_tables():
    """Inspect all configured tables and display their schemas."""
    load_dotenv('.env.seplat')
    settings = Settings()
    
    print("\n" + "="*80)
    print("SEPLAT ENERGY - SYNAPSE TABLE SCHEMA INSPECTION")
    print("="*80)
    
    with SynapseClient(settings) as client:
        for table_key, config in TABLES_CONFIG.items():
            schema = config['schema']
            table = config['table_name']
            sharepoint_list = config['sharepoint_list']
            
            print(f"\n{'='*80}")
            print(f"📊 Table: {schema}.{table}")
            print(f"📋 SharePoint List: {sharepoint_list}")
            print(f"{'='*80}")
            
            try:
                # Get row count
                row_count = get_row_count(client, schema, table)
                print(f"\n📈 Approximate Row Count: {row_count:,}")
                
                # Get schema
                columns = get_table_schema(client, schema, table)
                
                if not columns:
                    print("⚠️  No columns found or table doesn't exist")
                    continue
                
                print(f"\n📋 Columns ({len(columns)}):")
                print("-" * 80)
                print(f"{'Column Name':<30} {'SQL Type':<20} {'SharePoint Type':<20} {'Nullable'}")
                print("-" * 80)
                
                for col in columns:
                    col_name = col['COLUMN_NAME']
                    sql_type = col['DATA_TYPE']
                    is_nullable = col['IS_NULLABLE']
                    sp_type = map_sql_to_sharepoint_type(sql_type)
                    
                    # Add size info for character types
                    if col['CHARACTER_MAXIMUM_LENGTH']:
                        sql_type = f"{sql_type}({col['CHARACTER_MAXIMUM_LENGTH']})"
                    elif col['NUMERIC_PRECISION']:
                        if col['NUMERIC_SCALE']:
                            sql_type = f"{sql_type}({col['NUMERIC_PRECISION']},{col['NUMERIC_SCALE']})"
                        else:
                            sql_type = f"{sql_type}({col['NUMERIC_PRECISION']})"
                    
                    print(f"{col_name:<30} {sql_type:<20} {sp_type:<20} {is_nullable}")
                
                # Sample data
                print(f"\n📄 Sample Data (first 3 rows):")
                print("-" * 80)
                sample_query = f"SELECT TOP 3 * FROM {schema}.{table}"
                sample_data = client.execute_query(sample_query)
                
                if sample_data:
                    # Print column headers
                    headers = list(sample_data[0].keys())
                    header_line = " | ".join(f"{h[:15]:<15}" for h in headers[:5])
                    print(header_line)
                    print("-" * len(header_line))
                    
                    # Print data
                    for row in sample_data:
                        values = [str(row.get(h, ''))[:15] for h in headers[:5]]
                        print(" | ".join(f"{v:<15}" for v in values))
                else:
                    print("No sample data available")
                
                print("\n" + "="*80)
                
            except Exception as e:
                print(f"❌ Error inspecting table: {e}")
    
    print("\n" + "="*80)
    print("✅ Schema inspection complete")
    print("="*80 + "\n")
    
    print("\n📝 NEXT STEPS:")
    print("-" * 80)
    print("1. Create SharePoint lists with names matching the configuration:")
    for config in TABLES_CONFIG.values():
        print(f"   - {config['sharepoint_list']}")
    print("\n2. Add columns to each list based on the SQL schema shown above")
    print("3. Use internal field names (no spaces) when creating SharePoint columns")
    print("4. Update field_mapping in table_config.py if SharePoint names differ")
    print("5. Run: python sync_all_tables.py")
    print("-" * 80 + "\n")


if __name__ == "__main__":
    try:
        inspect_all_tables()
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        sys.exit(1)
