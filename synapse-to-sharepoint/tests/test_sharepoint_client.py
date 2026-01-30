"""
Tests for SharePoint client module.
"""
import pytest
import responses
from unittest.mock import Mock, patch
from src.sharepoint_client import SharePointClient, upload_to_sharepoint


class TestSharePointClient:
    """Test SharePointClient class."""
    
    def test_init(self, mock_settings):
        """Test client initialization."""
        client = SharePointClient(mock_settings)
        assert client.settings == mock_settings
        assert client.access_token is None
        assert client.site_id is None
        assert client.list_id is None
    
    @patch('src.sharepoint_client.msal.ConfidentialClientApplication')
    def test_get_access_token_success(self, mock_msal, mock_settings):
        """Test successful token acquisition."""
        mock_app = Mock()
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "test_token_123"
        }
        mock_msal.return_value = mock_app
        
        client = SharePointClient(mock_settings)
        token = client._get_access_token()
        
        assert token == "test_token_123"
    
    @patch('src.sharepoint_client.msal.ConfidentialClientApplication')
    def test_get_access_token_failure(self, mock_msal, mock_settings):
        """Test token acquisition failure."""
        mock_app = Mock()
        mock_app.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "Invalid client"
        }
        mock_msal.return_value = mock_app
        
        client = SharePointClient(mock_settings)
        
        with pytest.raises(Exception):
            client._get_access_token()
    
    def test_parse_site_url(self, mock_settings):
        """Test parsing SharePoint site URL."""
        client = SharePointClient(mock_settings)
        hostname, site_path = client._parse_site_url()
        
        assert hostname == "contoso.sharepoint.com"
        assert site_path == "sites/testsite"
    
    def test_get_headers(self, mock_settings):
        """Test getting HTTP headers."""
        client = SharePointClient(mock_settings)
        client.access_token = "test_token"
        
        headers = client._get_headers()
        
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"
    
    @responses.activate
    def test_get_site_id_success(self, mock_settings):
        """Test getting site ID successfully."""
        # Mock token acquisition
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/testsite",
            json={"id": "site-123"},
            status=200
        )
        
        client = SharePointClient(mock_settings)
        client.access_token = "test_token"
        
        site_id = client.get_site_id()
        
        assert site_id == "site-123"
        assert client.site_id == "site-123"
    
    @responses.activate
    def test_get_list_id_success(self, mock_settings):
        """Test getting list ID successfully."""
        # Mock site ID
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/testsite",
            json={"id": "site-123"},
            status=200
        )
        
        # Mock list retrieval
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/site-123/lists",
            json={
                "value": [
                    {"id": "list-123", "displayName": "TestList"},
                    {"id": "list-456", "displayName": "OtherList"}
                ]
            },
            status=200
        )
        
        client = SharePointClient(mock_settings)
        client.access_token = "test_token"
        
        list_id = client.get_list_id()
        
        assert list_id == "list-123"
        assert client.list_id == "list-123"
    
    @responses.activate
    def test_get_list_id_not_found(self, mock_settings):
        """Test getting list ID when list doesn't exist."""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/testsite",
            json={"id": "site-123"},
            status=200
        )
        
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/site-123/lists",
            json={
                "value": [
                    {"id": "list-456", "displayName": "OtherList"}
                ]
            },
            status=200
        )
        
        client = SharePointClient(mock_settings)
        client.access_token = "test_token"
        
        with pytest.raises(Exception, match="List .* not found"):
            client.get_list_id()
    
    @responses.activate
    def test_create_list_item_success(self, mock_settings):
        """Test creating list item successfully."""
        # Mock getting site and list IDs
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/testsite",
            json={"id": "site-123"},
            status=200
        )
        
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/site-123/lists",
            json={"value": [{"id": "list-123", "displayName": "TestList"}]},
            status=200
        )
        
        # Mock item creation
        responses.add(
            responses.POST,
            "https://graph.microsoft.com/v1.0/sites/site-123/lists/list-123/items",
            json={"id": "item-1", "fields": {"Title": "Test Item"}},
            status=201
        )
        
        client = SharePointClient(mock_settings)
        client.access_token = "test_token"
        
        item_data = {"Title": "Test Item"}
        result = client.create_list_item(item_data)
        
        assert result["id"] == "item-1"
    
    @responses.activate
    def test_update_list_item_success(self, mock_settings):
        """Test updating list item successfully."""
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/testsite",
            json={"id": "site-123"},
            status=200
        )
        
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/site-123/lists",
            json={"value": [{"id": "list-123", "displayName": "TestList"}]},
            status=200
        )
        
        responses.add(
            responses.PATCH,
            "https://graph.microsoft.com/v1.0/sites/site-123/lists/list-123/items/item-1/fields",
            json={"Title": "Updated Item"},
            status=200
        )
        
        client = SharePointClient(mock_settings)
        client.access_token = "test_token"
        
        item_data = {"Title": "Updated Item"}
        result = client.update_list_item("item-1", item_data)
        
        assert result["Title"] == "Updated Item"
    
    @responses.activate
    def test_batch_create_items(self, mock_settings, sample_transformed_data):
        """Test batch creation of items."""
        # Mock site and list
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/testsite",
            json={"id": "site-123"},
            status=200
        )
        
        responses.add(
            responses.GET,
            "https://graph.microsoft.com/v1.0/sites/site-123/lists",
            json={"value": [{"id": "list-123", "displayName": "TestList"}]},
            status=200
        )
        
        # Mock item creation for each item
        for i in range(len(sample_transformed_data)):
            responses.add(
                responses.POST,
                "https://graph.microsoft.com/v1.0/sites/site-123/lists/list-123/items",
                json={"id": f"item-{i+1}"},
                status=201
            )
        
        client = SharePointClient(mock_settings)
        client.access_token = "test_token"
        
        results = client.batch_create_items(sample_transformed_data)
        
        assert results["success"] == 3
        assert results["failed"] == 0
        assert len(results["errors"]) == 0
    
    def test_context_manager(self, mock_settings):
        """Test context manager usage."""
        with patch.object(SharePointClient, 'authenticate'):
            with SharePointClient(mock_settings) as client:
                assert isinstance(client, SharePointClient)


class TestUploadToSharePoint:
    """Test upload_to_sharepoint convenience function."""
    
    @patch('src.sharepoint_client.SharePointClient')
    def test_upload_to_sharepoint(self, mock_client_class, mock_settings, sample_transformed_data):
        """Test uploading data to SharePoint."""
        mock_client = Mock()
        mock_client.batch_create_items.return_value = {
            "success": 3,
            "failed": 0,
            "errors": []
        }
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client
        
        result = upload_to_sharepoint(mock_settings, sample_transformed_data)
        
        assert result["success"] == 3
        assert result["failed"] == 0
        mock_client.batch_create_items.assert_called_once_with(sample_transformed_data)
