"""
Azure Synapse data access layer.
Handles connection and querying of Synapse SQL pools.
"""
from typing import List, Dict, Any, Optional
import pyodbc
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from src.logging_config import get_logger
from src.config import Settings


logger = get_logger(__name__)


class SynapseClient:
    """Client for interacting with Azure Synapse SQL pools."""
    
    def __init__(self, settings: Settings):
        """
        Initialize Synapse client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.connection: Optional[pyodbc.Connection] = None
        logger.info("Synapse client initialized", server=settings.synapse_server)
    
    def _get_connection_string(self) -> str:
        """
        Build connection string based on authentication method.
        
        Returns:
            ODBC connection string
        """
        driver = "{ODBC Driver 18 for SQL Server}"
        server = self.settings.synapse_server
        database = self.settings.synapse_database
        
        if self.settings.use_managed_identity:
            # Use Azure AD authentication
            conn_str = (
                f"Driver={driver};"
                f"Server={server};"
                f"Database={database};"
                f"Authentication=ActiveDirectoryMsi;"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
            )
            logger.info("Using Managed Identity authentication")
        else:
            # Use SQL authentication
            conn_str = (
                f"Driver={driver};"
                f"Server={server};"
                f"Database={database};"
                f"UID={self.settings.synapse_username};"
                f"PWD={self.settings.synapse_password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
            )
            logger.info("Using SQL authentication")
        
        return conn_str
    
    def connect(self) -> None:
        """Establish connection to Synapse."""
        try:
            conn_str = self._get_connection_string()
            self.connection = pyodbc.connect(conn_str, timeout=30)
            logger.info("Connected to Synapse successfully")
        except Exception as e:
            logger.error("Failed to connect to Synapse", error=str(e))
            raise
    
    def disconnect(self) -> None:
        """Close connection to Synapse."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from Synapse")
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as list of dictionaries.
        
        Args:
            query: SQL query to execute
            
        Returns:
            List of row dictionaries
            
        Raises:
            Exception: If query execution fails
        """
        if not self.connection:
            raise Exception("Not connected to Synapse. Call connect() first.")
        
        try:
            logger.info("Executing query", query_preview=query[:100])
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch all rows and convert to dictionaries
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                rows.append(row_dict)
            
            logger.info("Query executed successfully", row_count=len(rows))
            return rows
            
        except Exception as e:
            logger.error("Query execution failed", error=str(e), query=query)
            raise
        finally:
            cursor.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False


def get_synapse_data(settings: Settings) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch data from Synapse.
    
    Args:
        settings: Application settings
        
    Returns:
        List of row dictionaries
    """
    with SynapseClient(settings) as client:
        return client.execute_query(settings.synapse_query)
