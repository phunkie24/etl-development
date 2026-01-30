"""
SharePoint client using Microsoft Graph API.
Handles authentication and CRUD operations on SharePoint lists.
"""
from typing import List, Dict, Any, Optional
import json
import requests
import msal
from src.logging_config import get_logger
from src.config import Settings


logger = get_logger(__name__)


class SharePointClient:
    """Client for interacting with SharePoint via Microsoft Graph API."""
    
    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
    SCOPES = ["https://graph.microsoft.com/.default"]
    
    def __init__(self, settings: Settings):
        """
        Initialize SharePoint client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.access_token: Optional[str] = None
        self.site_id: Optional[str] = None
        self.list_id: Optional[str] = None
        logger.info("SharePoint client initialized")
    
    def _get_access_token(self) -> str:
        """
        Acquire access token using MSAL.
        
        Returns:
            Access token string
            
        Raises:
            Exception: If token acquisition fails
        """
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.settings.client_id,
                client_credential=self.settings.client_secret,
                authority=f"https://login.microsoftonline.com/{self.settings.tenant_id}"
            )
            
            result = app.acquire_token_for_client(scopes=self.SCOPES)
            
            if "access_token" in result:
                logger.info("Access token acquired successfully")
                return result["access_token"]
            else:
                error_msg = result.get("error_description", "Unknown error")
                logger.error("Failed to acquire token", error=error_msg)
                raise Exception(f"Token acquisition failed: {error_msg}")
                
        except Exception as e:
            logger.error("Token acquisition error", error=str(e))
            raise
    
    def authenticate(self) -> None:
        """Authenticate and get access token."""
        self.access_token = self._get_access_token()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with authorization.
        
        Returns:
            Headers dictionary
        """
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _parse_site_url(self) -> tuple:
        """
        Parse SharePoint site URL to extract hostname and site path.
        
        Returns:
            Tuple of (hostname, site_path)
        """
        url = self.settings.sharepoint_site_url.rstrip('/')
        # Remove protocol
        url = url.replace('https://', '').replace('http://', '')
        parts = url.split('/', 1)
        hostname = parts[0]
        site_path = parts[1] if len(parts) > 1 else ''
        return hostname, site_path
    
    def get_site_id(self) -> str:
        """
        Get SharePoint site ID from site URL.
        
        Returns:
            Site ID string
            
        Raises:
            Exception: If site retrieval fails
        """
        if self.site_id:
            return self.site_id
        
        try:
            hostname, site_path = self._parse_site_url()
            
            # Get site using hostname and path
            url = f"{self.GRAPH_API_ENDPOINT}/sites/{hostname}:/{site_path}"
            
            logger.info("Getting site ID", url=url)
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            site_data = response.json()
            self.site_id = site_data['id']
            
            logger.info("Site ID retrieved", site_id=self.site_id)
            return self.site_id
            
        except Exception as e:
            logger.error("Failed to get site ID", error=str(e))
            raise
    
    def get_list_id(self) -> str:
        """
        Get SharePoint list ID from list name.
        
        Returns:
            List ID string
            
        Raises:
            Exception: If list retrieval fails
        """
        if self.list_id:
            return self.list_id
        
        try:
            site_id = self.get_site_id()
            url = f"{self.GRAPH_API_ENDPOINT}/sites/{site_id}/lists"
            
            logger.info("Getting list ID", list_name=self.settings.sharepoint_list_name)
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            lists_data = response.json()
            
            # Find list by display name
            for list_item in lists_data.get('value', []):
                if list_item['displayName'] == self.settings.sharepoint_list_name:
                    self.list_id = list_item['id']
                    logger.info("List ID retrieved", list_id=self.list_id)
                    return self.list_id
            
            raise Exception(f"List '{self.settings.sharepoint_list_name}' not found")
            
        except Exception as e:
            logger.error("Failed to get list ID", error=str(e))
            raise
    
    def create_list_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new item in the SharePoint list.
        
        Args:
            item_data: Dictionary of field values
            
        Returns:
            Created item data
            
        Raises:
            Exception: If item creation fails
        """
        try:
            site_id = self.get_site_id()
            list_id = self.get_list_id()
            
            url = f"{self.GRAPH_API_ENDPOINT}/sites/{site_id}/lists/{list_id}/items"
            
            # Prepare payload with fields
            payload = {
                "fields": item_data
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            created_item = response.json()
            logger.debug("List item created", item_id=created_item.get('id'))
            return created_item
            
        except requests.exceptions.HTTPError as e:
            logger.error(
                "Failed to create list item",
                error=str(e),
                response=e.response.text if e.response else None
            )
            raise
    
    def update_list_item(self, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing item in the SharePoint list.
        
        Args:
            item_id: Item ID to update
            item_data: Dictionary of field values to update
            
        Returns:
            Updated item data
            
        Raises:
            Exception: If item update fails
        """
        try:
            site_id = self.get_site_id()
            list_id = self.get_list_id()
            
            url = f"{self.GRAPH_API_ENDPOINT}/sites/{site_id}/lists/{list_id}/items/{item_id}/fields"
            
            response = requests.patch(
                url,
                headers=self._get_headers(),
                json=item_data
            )
            response.raise_for_status()
            
            updated_item = response.json()
            logger.debug("List item updated", item_id=item_id)
            return updated_item
            
        except requests.exceptions.HTTPError as e:
            logger.error(
                "Failed to update list item",
                error=str(e),
                item_id=item_id,
                response=e.response.text if e.response else None
            )
            raise
    
    def batch_create_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple items in batch.
        
        Args:
            items: List of item data dictionaries
            
        Returns:
            Dictionary with success/failure counts and details
        """
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        logger.info("Starting batch creation", total_items=len(items))
        
        for idx, item in enumerate(items, 1):
            try:
                self.create_list_item(item)
                results["success"] += 1
                
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{len(items)} items processed")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "item_index": idx,
                    "error": str(e),
                    "item_data": item
                })
                logger.warning("Item creation failed", item_index=idx, error=str(e))
        
        logger.info(
            "Batch creation completed",
            success=results["success"],
            failed=results["failed"]
        )
        
        return results
    
    def __enter__(self):
        """Context manager entry."""
        self.authenticate()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.access_token = None
        return False


def upload_to_sharepoint(
    settings: Settings,
    data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Convenience function to upload data to SharePoint.
    
    Args:
        settings: Application settings
        data: List of row dictionaries to upload
        
    Returns:
        Results dictionary with success/failure counts
    """
    with SharePointClient(settings) as client:
        return client.batch_create_items(data)
