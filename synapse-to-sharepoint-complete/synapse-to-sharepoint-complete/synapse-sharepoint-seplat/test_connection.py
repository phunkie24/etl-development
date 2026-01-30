"""
Test connection to both Synapse and SharePoint for SEPLAT Energy.
Run this first to verify your configuration before syncing data.
"""
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'synapse-to-sharepoint'))

from src.config import Settings
from src.synapse_client import SynapseClient
from src.sharepoint_client import SharePointClient


def test_synapse_connection(settings: Settings) -> bool:
    """Test connection to Synapse."""
    print("\n" + "="*70)
    print("Testing Synapse Connection")
    print("="*70)
    
    try:
        print(f"Server: {settings.synapse_server}")
        print(f"Database: {settings.synapse_database}")
        print(f"Authentication: {'Managed Identity' if settings.use_managed_identity else 'SQL'}")
        
        with SynapseClient(settings) as client:
            # Test basic connectivity
            print("\n✓ Connected to Synapse successfully")
            
            # Test access to oml40 schema
            query = """
            SELECT 
                TABLE_NAME, 
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'oml40'
            ORDER BY TABLE_NAME
            """
            
            tables = client.execute_query(query)
            
            print(f"\n✓ Found {len(tables)} tables in oml40 schema:")
            for table in tables:
                print(f"  - {table['TABLE_NAME']} ({table['TABLE_TYPE']})")
            
            # Test sample query
            sample_query = "SELECT TOP 1 * FROM oml40.daily_production"
            print(f"\n✓ Testing sample query: {sample_query}")
            result = client.execute_query(sample_query)
            print(f"✓ Sample query successful - returned {len(result)} row(s)")
            
            print("\n✅ Synapse connection test PASSED")
            return True
            
    except Exception as e:
        print(f"\n❌ Synapse connection test FAILED")
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check SYNAPSE_SERVER, SYNAPSE_DATABASE in .env.seplat")
        print("2. Verify username/password are correct")
        print("3. Ensure your IP is allowed in Synapse firewall")
        print("4. Check ODBC Driver 18 is installed")
        return False


def test_sharepoint_connection(settings: Settings) -> bool:
    """Test connection to SharePoint."""
    print("\n" + "="*70)
    print("Testing SharePoint Connection")
    print("="*70)
    
    try:
        print(f"Site URL: {settings.sharepoint_site_url}")
        print(f"Tenant ID: {settings.tenant_id}")
        print(f"Client ID: {settings.client_id}")
        
        with SharePointClient(settings) as client:
            print("\n✓ Authenticated to SharePoint successfully")
            
            # Get site ID
            site_id = client.get_site_id()
            print(f"✓ Site ID retrieved: {site_id[:50]}...")
            
            # List available lists
            url = f"{client.GRAPH_API_ENDPOINT}/sites/{site_id}/lists"
            response = client._get_headers()
            import requests
            lists_response = requests.get(url, headers=client._get_headers())
            lists_response.raise_for_status()
            
            lists_data = lists_response.json()
            available_lists = lists_data.get('value', [])
            
            print(f"\n✓ Found {len(available_lists)} lists in SharePoint site:")
            for lst in available_lists:
                print(f"  - {lst['displayName']} (ID: {lst['id'][:30]}...)")
            
            # Check if expected lists exist
            print("\n📋 Checking for expected lists:")
            expected_lists = [
                'DailyFieldParameters',
                'DailyProduction',
                'DailyWellParameters',
                'HeaderID',
                'Pressure',
                'WellTest'
            ]
            
            list_names = [lst['displayName'] for lst in available_lists]
            
            for expected in expected_lists:
                if expected in list_names:
                    print(f"  ✓ {expected}")
                else:
                    print(f"  ⚠️  {expected} - NOT FOUND (needs to be created)")
            
            print("\n✅ SharePoint connection test PASSED")
            return True
            
    except Exception as e:
        print(f"\n❌ SharePoint connection test FAILED")
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check TENANT_ID, CLIENT_ID, CLIENT_SECRET in .env.seplat")
        print("2. Verify Azure AD app has Sites.ReadWrite.All permission")
        print("3. Ensure admin consent was granted")
        print("4. Check SHAREPOINT_SITE_URL is correct")
        return False


def main():
    """Run all connection tests."""
    print("\n" + "="*70)
    print("SEPLAT ENERGY - CONNECTION TEST")
    print("="*70)
    
    # Load environment
    load_dotenv('.env.seplat')
    
    try:
        settings = Settings()
    except Exception as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env.seplat file")
        return 1
    
    # Run tests
    synapse_ok = test_synapse_connection(settings)
    sharepoint_ok = test_sharepoint_connection(settings)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Synapse:    {'✅ PASS' if synapse_ok else '❌ FAIL'}")
    print(f"SharePoint: {'✅ PASS' if sharepoint_ok else '❌ FAIL'}")
    
    if synapse_ok and sharepoint_ok:
        print("\n✅ All tests passed! You're ready to sync data.")
        print("\nNext steps:")
        print("1. Run: python inspect_schema.py")
        print("2. Create any missing SharePoint lists")
        print("3. Run: python sync_all_tables.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix issues before syncing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
