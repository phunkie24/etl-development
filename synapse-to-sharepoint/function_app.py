"""
Azure Function entry point for Synapse to SharePoint integration.
Supports both HTTP trigger and Timer trigger.
"""
import json
import logging
import azure.functions as func
from src.main import SynapseToSharePointPipeline
from src.config import get_settings


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger Azure Function.
    
    Args:
        req: HTTP request object
        
    Returns:
        HTTP response with pipeline results
    """
    logging.info('Synapse to SharePoint HTTP trigger function processing request.')
    
    try:
        # Initialize and run pipeline
        pipeline = SynapseToSharePointPipeline()
        results = pipeline.run()
        
        # Prepare response
        response_data = {
            "status": results["status"],
            "message": "Pipeline execution completed",
            "details": {
                "extracted_rows": results["extracted_rows"],
                "transformed_rows": results["transformed_rows"],
                "loaded_rows": results["loaded_rows"],
                "failed_rows": results["failed_rows"],
                "error_count": len(results["errors"])
            }
        }
        
        # Include error details if any
        if results["errors"]:
            response_data["errors"] = results["errors"][:10]  # Limit to first 10 errors
        
        status_code = 200 if results["status"] in ["success", "partial_success"] else 500
        
        return func.HttpResponse(
            body=json.dumps(response_data, indent=2),
            status_code=status_code,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Function execution failed: {str(e)}")
        
        error_response = {
            "status": "error",
            "message": "Pipeline execution failed",
            "error": str(e)
        }
        
        return func.HttpResponse(
            body=json.dumps(error_response, indent=2),
            status_code=500,
            mimetype="application/json"
        )


def timer_trigger(mytimer: func.TimerRequest) -> None:
    """
    Timer trigger Azure Function.
    
    Args:
        mytimer: Timer request object
    """
    logging.info('Synapse to SharePoint timer trigger function started.')
    
    if mytimer.past_due:
        logging.info('The timer is past due!')
    
    try:
        # Initialize and run pipeline
        pipeline = SynapseToSharePointPipeline()
        results = pipeline.run()
        
        logging.info(
            f"Pipeline completed with status: {results['status']}. "
            f"Loaded: {results['loaded_rows']}, Failed: {results['failed_rows']}"
        )
        
    except Exception as e:
        logging.error(f"Timer function execution failed: {str(e)}")
        raise
