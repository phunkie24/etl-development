"""
Test configuration and fixtures.
"""
import pytest
from unittest.mock import Mock
from src.config import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return Settings(
        synapse_server="test-synapse.sql.azuresynapse.net",
        synapse_database="testdb",
        synapse_username="testuser",
        synapse_password="testpass",
        use_managed_identity=False,
        sharepoint_site_url="https://contoso.sharepoint.com/sites/testsite",
        sharepoint_list_name="TestList",
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-client-secret",
        synapse_query="SELECT * FROM test_table",
        batch_size=100,
        log_level="INFO",
        field_mapping='{"id": "ID", "name": "Title"}'
    )


@pytest.fixture
def sample_synapse_data():
    """Sample data from Synapse."""
    return [
        {"id": 1, "name": "Test Item 1", "value": 100.0, "created": "2024-01-01"},
        {"id": 2, "name": "Test Item 2", "value": 200.0, "created": "2024-01-02"},
        {"id": 3, "name": "Test Item 3", "value": 300.0, "created": "2024-01-03"},
    ]


@pytest.fixture
def sample_transformed_data():
    """Sample transformed data for SharePoint."""
    return [
        {"ID": 1, "Title": "Test Item 1", "value": 100.0, "created": "2024-01-01"},
        {"ID": 2, "Title": "Test Item 2", "value": 200.0, "created": "2024-01-02"},
        {"ID": 3, "Title": "Test Item 3", "value": 300.0, "created": "2024-01-03"},
    ]
