"""
Tests for Synapse client module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.synapse_client import SynapseClient, get_synapse_data


class TestSynapseClient:
    """Test SynapseClient class."""
    
    def test_init(self, mock_settings):
        """Test client initialization."""
        client = SynapseClient(mock_settings)
        assert client.settings == mock_settings
        assert client.connection is None
    
    def test_get_connection_string_sql_auth(self, mock_settings):
        """Test connection string generation with SQL auth."""
        mock_settings.use_managed_identity = False
        client = SynapseClient(mock_settings)
        conn_str = client._get_connection_string()
        
        assert "Driver={ODBC Driver 18 for SQL Server}" in conn_str
        assert mock_settings.synapse_server in conn_str
        assert mock_settings.synapse_database in conn_str
        assert mock_settings.synapse_username in conn_str
    
    def test_get_connection_string_managed_identity(self, mock_settings):
        """Test connection string generation with managed identity."""
        mock_settings.use_managed_identity = True
        client = SynapseClient(mock_settings)
        conn_str = client._get_connection_string()
        
        assert "Driver={ODBC Driver 18 for SQL Server}" in conn_str
        assert "Authentication=ActiveDirectoryMsi" in conn_str
        assert mock_settings.synapse_server in conn_str
    
    @patch('src.synapse_client.pyodbc.connect')
    def test_connect_success(self, mock_connect, mock_settings):
        """Test successful connection."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        client = SynapseClient(mock_settings)
        client.connect()
        
        assert client.connection == mock_connection
        mock_connect.assert_called_once()
    
    @patch('src.synapse_client.pyodbc.connect')
    def test_connect_failure(self, mock_connect, mock_settings):
        """Test connection failure."""
        mock_connect.side_effect = Exception("Connection failed")
        
        client = SynapseClient(mock_settings)
        with pytest.raises(Exception):
            client.connect()
    
    def test_disconnect(self, mock_settings):
        """Test disconnection."""
        client = SynapseClient(mock_settings)
        mock_connection = Mock()
        client.connection = mock_connection
        
        client.disconnect()
        
        mock_connection.close.assert_called_once()
        assert client.connection is None
    
    @patch('src.synapse_client.pyodbc.connect')
    def test_execute_query_success(self, mock_connect, mock_settings):
        """Test successful query execution."""
        # Setup mock connection and cursor
        mock_cursor = Mock()
        mock_cursor.description = [("id",), ("name",), ("value",)]
        mock_cursor.fetchall.return_value = [
            (1, "Item 1", 100),
            (2, "Item 2", 200)
        ]
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Execute query
        client = SynapseClient(mock_settings)
        client.connect()
        results = client.execute_query("SELECT * FROM test_table")
        
        # Verify results
        assert len(results) == 2
        assert results[0] == {"id": 1, "name": "Item 1", "value": 100}
        assert results[1] == {"id": 2, "name": "Item 2", "value": 200}
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    def test_execute_query_not_connected(self, mock_settings):
        """Test query execution without connection."""
        client = SynapseClient(mock_settings)
        
        with pytest.raises(Exception, match="Not connected"):
            client.execute_query("SELECT * FROM test_table")
    
    @patch('src.synapse_client.pyodbc.connect')
    def test_context_manager(self, mock_connect, mock_settings):
        """Test context manager usage."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        with SynapseClient(mock_settings) as client:
            assert client.connection == mock_connection
        
        mock_connection.close.assert_called_once()


class TestGetSynapseData:
    """Test get_synapse_data convenience function."""
    
    @patch('src.synapse_client.SynapseClient')
    def test_get_synapse_data(self, mock_client_class, mock_settings, sample_synapse_data):
        """Test getting data from Synapse."""
        mock_client = Mock()
        mock_client.execute_query.return_value = sample_synapse_data
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client
        
        result = get_synapse_data(mock_settings)
        
        assert result == sample_synapse_data
        mock_client.execute_query.assert_called_once_with(mock_settings.synapse_query)
