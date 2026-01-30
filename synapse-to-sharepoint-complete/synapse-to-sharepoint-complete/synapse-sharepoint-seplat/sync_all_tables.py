"""
Multi-table sync script for SEPLAT Energy.
Syncs all 6 tables from Synapse oml40 schema to SharePoint lists.
"""
import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'synapse-to-sharepoint'))

from src.config import Settings
from src.logging_config import configure_logging, get_logger
from src.synapse_client import SynapseClient
from src.sharepoint_client import SharePointClient
from src.data_transformer import DataTransformer, chunk_data
from table_config import TABLES_CONFIG, get_all_table_keys


logger = get_logger(__name__)


class MultiTableSyncManager:
    """Manages synchronization of multiple tables from Synapse to SharePoint."""
    
    def __init__(self, settings: Settings):
        """Initialize the multi-table sync manager."""
        self.settings = settings
        configure_logging(settings.log_level)
        self.results = {
            "start_time": datetime.now().isoformat(),
            "tables": {},
            "overall_success": 0,
            "overall_failed": 0,
            "overall_status": "not_started"
        }
        logger.info("Multi-table sync manager initialized")
    
    def sync_single_table(
        self, 
        table_key: str, 
        synapse_client: SynapseClient,
        sharepoint_client: SharePointClient
    ) -> Dict[str, Any]:
        """
        Sync a single table from Synapse to SharePoint.
        
        Args:
            table_key: Key identifying the table configuration
            synapse_client: Connected Synapse client
            sharepoint_client: Authenticated SharePoint client
            
        Returns:
            Dictionary with sync results for this table
        """
        table_config = TABLES_CONFIG[table_key]
        table_results = {
            "status": "failed",
            "extracted": 0,
            "loaded": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            logger.info(
                "Starting sync for table",
                table=table_key,
                sharepoint_list=table_config['sharepoint_list']
            )
            
            # Extract data from Synapse
            logger.info("Extracting data from Synapse", table=table_key)
            data = synapse_client.execute_query(table_config['query'])
            table_results["extracted"] = len(data)
            
            if not data:
                logger.warning("No data found for table", table=table_key)
                table_results["status"] = "success"
                return table_results
            
            # Transform data
            transformer = DataTransformer(table_config.get('field_mapping', {}))
            transformed_data = transformer.transform_batch(data)
            
            # Update SharePoint client to target this table's list
            original_list_name = sharepoint_client.settings.sharepoint_list_name
            sharepoint_client.settings.sharepoint_list_name = table_config['sharepoint_list']
            sharepoint_client.list_id = None  # Reset cached list ID
            
            # Load to SharePoint in batches
            chunks = chunk_data(transformed_data, self.settings.batch_size)
            
            for chunk_idx, chunk in enumerate(chunks, 1):
                logger.info(
                    "Processing chunk",
                    table=table_key,
                    chunk=f"{chunk_idx}/{len(chunks)}",
                    size=len(chunk)
                )
                
                results = sharepoint_client.batch_create_items(chunk)
                table_results["loaded"] += results["success"]
                table_results["failed"] += results["failed"]
                table_results["errors"].extend(results["errors"])
            
            # Restore original list name
            sharepoint_client.settings.sharepoint_list_name = original_list_name
            
            # Determine status
            if table_results["failed"] == 0:
                table_results["status"] = "success"
            elif table_results["loaded"] > 0:
                table_results["status"] = "partial_success"
            else:
                table_results["status"] = "failed"
            
            logger.info(
                "Table sync completed",
                table=table_key,
                status=table_results["status"],
                loaded=table_results["loaded"],
                failed=table_results["failed"]
            )
            
            return table_results
            
        except Exception as e:
            logger.error("Table sync failed", table=table_key, error=str(e))
            table_results["errors"].append({
                "stage": "sync",
                "error": str(e)
            })
            return table_results
    
    def sync_all_tables(self, tables_to_sync: List[str] = None) -> Dict[str, Any]:
        """
        Sync all configured tables or a subset.
        
        Args:
            tables_to_sync: Optional list of table keys to sync. If None, syncs all.
            
        Returns:
            Dictionary with overall results
        """
        if tables_to_sync is None:
            tables_to_sync = get_all_table_keys()
        
        logger.info(
            "Starting multi-table sync",
            total_tables=len(tables_to_sync),
            tables=tables_to_sync
        )
        
        try:
            # Connect to Synapse
            with SynapseClient(self.settings) as synapse_client:
                # Connect to SharePoint
                with SharePointClient(self.settings) as sharepoint_client:
                    
                    # Sync each table
                    for table_key in tables_to_sync:
                        if table_key not in TABLES_CONFIG:
                            logger.warning(f"Table key '{table_key}' not found in configuration")
                            continue
                        
                        table_results = self.sync_single_table(
                            table_key,
                            synapse_client,
                            sharepoint_client
                        )
                        
                        self.results["tables"][table_key] = table_results
                        self.results["overall_success"] += table_results["loaded"]
                        self.results["overall_failed"] += table_results["failed"]
            
            # Determine overall status
            success_count = sum(
                1 for r in self.results["tables"].values() 
                if r["status"] == "success"
            )
            
            if success_count == len(tables_to_sync):
                self.results["overall_status"] = "success"
            elif success_count > 0:
                self.results["overall_status"] = "partial_success"
            else:
                self.results["overall_status"] = "failed"
            
            self.results["end_time"] = datetime.now().isoformat()
            
            logger.info(
                "Multi-table sync completed",
                status=self.results["overall_status"],
                tables_synced=len(tables_to_sync),
                total_loaded=self.results["overall_success"],
                total_failed=self.results["overall_failed"]
            )
            
            return self.results
            
        except Exception as e:
            logger.error("Multi-table sync failed", error=str(e))
            self.results["overall_status"] = "error"
            self.results["error"] = str(e)
            self.results["end_time"] = datetime.now().isoformat()
            raise


def print_results(results: Dict[str, Any]):
    """Print formatted results."""
    print("\n" + "="*70)
    print("SEPLAT ENERGY - MULTI-TABLE SYNC RESULTS")
    print("="*70)
    print(f"Start Time: {results['start_time']}")
    print(f"End Time: {results.get('end_time', 'N/A')}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Total Records Loaded: {results['overall_success']}")
    print(f"Total Records Failed: {results['overall_failed']}")
    print("\n" + "-"*70)
    print("Individual Table Results:")
    print("-"*70)
    
    for table_key, table_result in results['tables'].items():
        config = TABLES_CONFIG[table_key]
        print(f"\n📊 {config['sharepoint_list']}")
        print(f"   Source: {config['schema']}.{config['table_name']}")
        print(f"   Status: {table_result['status'].upper()}")
        print(f"   Extracted: {table_result['extracted']}")
        print(f"   Loaded: {table_result['loaded']}")
        print(f"   Failed: {table_result['failed']}")
        
        if table_result['errors']:
            print(f"   Errors: {len(table_result['errors'])}")
            for idx, error in enumerate(table_result['errors'][:3], 1):
                print(f"     {idx}. {error.get('error', error)}")
            if len(table_result['errors']) > 3:
                print(f"     ... and {len(table_result['errors']) - 3} more errors")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main entry point."""
    import argparse
    from dotenv import load_dotenv
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Sync SEPLAT Energy Synapse tables to SharePoint"
    )
    parser.add_argument(
        '--tables',
        nargs='+',
        help='Specific tables to sync (default: all)',
        choices=get_all_table_keys(),
        default=None
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - extract data but do not load to SharePoint'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv('.env.seplat')
    
    # Create settings
    settings = Settings()
    
    # Run sync
    try:
        manager = MultiTableSyncManager(settings)
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No data will be loaded to SharePoint")
            # Implement dry run logic here
            print("Dry run mode not yet implemented")
            return 1
        
        results = manager.sync_all_tables(args.tables)
        print_results(results)
        
        # Return exit code based on status
        if results['overall_status'] == 'success':
            return 0
        elif results['overall_status'] == 'partial_success':
            return 1
        else:
            return 2
            
    except Exception as e:
        logger.error("Script execution failed", error=str(e))
        print(f"\n❌ ERROR: {e}\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
