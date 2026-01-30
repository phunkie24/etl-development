"""
Main orchestration module for Synapse to SharePoint integration.
Coordinates the data pipeline from extraction to loading.
"""
from typing import Dict, Any, List
from src.config import get_settings
from src.logging_config import configure_logging, get_logger, LogContext
from src.synapse_client import get_synapse_data
from src.sharepoint_client import upload_to_sharepoint
from src.data_transformer import create_transformer_from_settings, chunk_data


logger = get_logger(__name__)


class SynapseToSharePointPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, settings=None):
        """
        Initialize pipeline.
        
        Args:
            settings: Optional settings object (will load from env if not provided)
        """
        self.settings = settings or get_settings()
        configure_logging(self.settings.log_level)
        self.transformer = create_transformer_from_settings(self.settings)
        logger.info("Pipeline initialized")
    
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract data from Synapse.
        
        Returns:
            List of row dictionaries
        """
        with LogContext(logger, stage="extract"):
            logger.info("Starting data extraction from Synapse")
            
            try:
                data = get_synapse_data(self.settings)
                logger.info("Data extraction completed", row_count=len(data))
                return data
            except Exception as e:
                logger.error("Data extraction failed", error=str(e))
                raise
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform data from Synapse format to SharePoint format.
        
        Args:
            data: Raw data from Synapse
            
        Returns:
            Transformed data ready for SharePoint
        """
        with LogContext(logger, stage="transform"):
            logger.info("Starting data transformation", row_count=len(data))
            
            try:
                transformed_data = self.transformer.transform_batch(data)
                logger.info("Data transformation completed", row_count=len(transformed_data))
                return transformed_data
            except Exception as e:
                logger.error("Data transformation failed", error=str(e))
                raise
    
    def load(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Load data into SharePoint.
        
        Args:
            data: Transformed data ready for SharePoint
            
        Returns:
            Results dictionary with success/failure counts
        """
        with LogContext(logger, stage="load"):
            logger.info("Starting data load to SharePoint", row_count=len(data))
            
            try:
                # Split into chunks for better error handling
                chunks = chunk_data(data, self.settings.batch_size)
                
                overall_results = {
                    "success": 0,
                    "failed": 0,
                    "errors": [],
                    "total_chunks": len(chunks)
                }
                
                for chunk_idx, chunk in enumerate(chunks, 1):
                    logger.info(
                        "Processing chunk",
                        chunk_number=chunk_idx,
                        total_chunks=len(chunks),
                        chunk_size=len(chunk)
                    )
                    
                    results = upload_to_sharepoint(self.settings, chunk)
                    
                    overall_results["success"] += results["success"]
                    overall_results["failed"] += results["failed"]
                    overall_results["errors"].extend(results["errors"])
                
                logger.info(
                    "Data load completed",
                    success=overall_results["success"],
                    failed=overall_results["failed"]
                )
                
                return overall_results
                
            except Exception as e:
                logger.error("Data load failed", error=str(e))
                raise
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the complete ETL pipeline.
        
        Returns:
            Results dictionary with pipeline execution details
        """
        logger.info("Starting Synapse to SharePoint pipeline")
        
        pipeline_results = {
            "status": "failed",
            "extracted_rows": 0,
            "transformed_rows": 0,
            "loaded_rows": 0,
            "failed_rows": 0,
            "errors": []
        }
        
        try:
            # Extract
            raw_data = self.extract()
            pipeline_results["extracted_rows"] = len(raw_data)
            
            if not raw_data:
                logger.warning("No data extracted from Synapse")
                pipeline_results["status"] = "success"
                return pipeline_results
            
            # Transform
            transformed_data = self.transform(raw_data)
            pipeline_results["transformed_rows"] = len(transformed_data)
            
            # Load
            load_results = self.load(transformed_data)
            pipeline_results["loaded_rows"] = load_results["success"]
            pipeline_results["failed_rows"] = load_results["failed"]
            pipeline_results["errors"] = load_results["errors"]
            
            # Determine overall status
            if load_results["failed"] == 0:
                pipeline_results["status"] = "success"
            elif load_results["success"] > 0:
                pipeline_results["status"] = "partial_success"
            else:
                pipeline_results["status"] = "failed"
            
            logger.info(
                "Pipeline execution completed",
                status=pipeline_results["status"],
                extracted=pipeline_results["extracted_rows"],
                loaded=pipeline_results["loaded_rows"],
                failed=pipeline_results["failed_rows"]
            )
            
            return pipeline_results
            
        except Exception as e:
            logger.error("Pipeline execution failed", error=str(e))
            pipeline_results["errors"].append({"stage": "pipeline", "error": str(e)})
            raise


def main():
    """Main entry point for command-line execution."""
    try:
        pipeline = SynapseToSharePointPipeline()
        results = pipeline.run()
        
        print("\n" + "="*50)
        print("Pipeline Execution Results")
        print("="*50)
        print(f"Status: {results['status']}")
        print(f"Extracted Rows: {results['extracted_rows']}")
        print(f"Transformed Rows: {results['transformed_rows']}")
        print(f"Successfully Loaded: {results['loaded_rows']}")
        print(f"Failed: {results['failed_rows']}")
        
        if results['errors']:
            print(f"\nErrors: {len(results['errors'])}")
            for idx, error in enumerate(results['errors'][:5], 1):
                print(f"  {idx}. {error}")
            if len(results['errors']) > 5:
                print(f"  ... and {len(results['errors']) - 5} more errors")
        
        print("="*50 + "\n")
        
        return 0 if results['status'] in ['success', 'partial_success'] else 1
        
    except Exception as e:
        print(f"Pipeline failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
