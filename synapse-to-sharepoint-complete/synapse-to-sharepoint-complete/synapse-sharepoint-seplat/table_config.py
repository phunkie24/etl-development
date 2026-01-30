"""
Table configuration for SEPLAT Energy Synapse to SharePoint deployment.
Defines the 6 tables to sync and their SharePoint list mappings.
"""

TABLES_CONFIG = {
    "daily_field_parameters": {
        "schema": "oml40",
        "table_name": "daily_field_parameters",
        "sharepoint_list": "DailyFieldParameters",
        "description": "Daily field parameters data",
        "query": """
            SELECT 
                *
            FROM oml40.daily_field_parameters
            WHERE 1=1
            ORDER BY created_date DESC
        """,
        # Optional: Custom field mapping if SharePoint field names differ
        "field_mapping": {}
    },
    
    "daily_production": {
        "schema": "oml40",
        "table_name": "daily_production",
        "sharepoint_list": "DailyProduction",
        "description": "Daily production data",
        "query": """
            SELECT 
                *
            FROM oml40.daily_production
            WHERE 1=1
            ORDER BY production_date DESC
        """,
        "field_mapping": {}
    },
    
    "daily_well_parameters": {
        "schema": "oml40",
        "table_name": "daily_well_parameters",
        "sharepoint_list": "DailyWellParameters",
        "description": "Daily well parameters data",
        "query": """
            SELECT 
                *
            FROM oml40.daily_well_parameters
            WHERE 1=1
            ORDER BY parameter_date DESC
        """,
        "field_mapping": {}
    },
    
    "headerid": {
        "schema": "oml40",
        "table_name": "headerid",
        "sharepoint_list": "HeaderID",
        "description": "Header ID data",
        "query": """
            SELECT 
                *
            FROM oml40.headerid
            WHERE 1=1
        """,
        "field_mapping": {}
    },
    
    "pressure": {
        "schema": "oml40",
        "table_name": "pressure",
        "sharepoint_list": "Pressure",
        "description": "Pressure measurement data",
        "query": """
            SELECT 
                *
            FROM oml40.pressure
            WHERE 1=1
            ORDER BY measurement_date DESC
        """,
        "field_mapping": {}
    },
    
    "welltest": {
        "schema": "oml40",
        "table_name": "welltest",
        "sharepoint_list": "WellTest",
        "description": "Well test data",
        "query": """
            SELECT 
                *
            FROM oml40.welltest
            WHERE 1=1
            ORDER BY test_date DESC
        """,
        "field_mapping": {}
    }
}


def get_table_config(table_key):
    """Get configuration for a specific table."""
    return TABLES_CONFIG.get(table_key)


def get_all_table_keys():
    """Get list of all table keys."""
    return list(TABLES_CONFIG.keys())


def get_sharepoint_list_name(table_key):
    """Get SharePoint list name for a table."""
    config = TABLES_CONFIG.get(table_key)
    return config['sharepoint_list'] if config else None


def get_query(table_key):
    """Get SQL query for a table."""
    config = TABLES_CONFIG.get(table_key)
    return config['query'] if config else None
