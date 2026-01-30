"""
Data transformation utilities.
Handles mapping and transformation of data between Synapse and SharePoint.
"""
from typing import List, Dict, Any
import json
from datetime import datetime, date
from src.logging_config import get_logger


logger = get_logger(__name__)


class DataTransformer:
    """Transforms data from Synapse format to SharePoint format."""
    
    def __init__(self, field_mapping: Dict[str, str] = None):
        """
        Initialize data transformer.
        
        Args:
            field_mapping: Dictionary mapping Synapse column names to SharePoint field names
                          Format: {"synapse_column": "SharePointField"}
        """
        self.field_mapping = field_mapping or {}
        logger.info("Data transformer initialized", mapping_count=len(self.field_mapping))
    
    @staticmethod
    def serialize_value(value: Any) -> Any:
        """
        Serialize a value to SharePoint-compatible format.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized value
        """
        if value is None:
            return None
        
        # Handle datetime objects
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        
        # Handle boolean
        if isinstance(value, bool):
            return value
        
        # Handle numeric types
        if isinstance(value, (int, float)):
            return value
        
        # Convert everything else to string
        return str(value)
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single row from Synapse to SharePoint format.
        
        Args:
            row: Dictionary representing a Synapse row
            
        Returns:
            Transformed dictionary for SharePoint
        """
        transformed = {}
        
        for synapse_field, value in row.items():
            # Get SharePoint field name (use mapping or original name)
            sharepoint_field = self.field_mapping.get(synapse_field, synapse_field)
            
            # Serialize the value
            transformed[sharepoint_field] = self.serialize_value(value)
        
        return transformed
    
    def transform_batch(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform a batch of rows.
        
        Args:
            rows: List of Synapse row dictionaries
            
        Returns:
            List of transformed SharePoint-compatible dictionaries
        """
        logger.info("Transforming batch", row_count=len(rows))
        
        transformed_rows = []
        for idx, row in enumerate(rows):
            try:
                transformed = self.transform_row(row)
                transformed_rows.append(transformed)
            except Exception as e:
                logger.error(
                    "Failed to transform row",
                    row_index=idx,
                    error=str(e),
                    row_data=row
                )
                raise
        
        logger.info("Batch transformation completed", transformed_count=len(transformed_rows))
        return transformed_rows
    
    @staticmethod
    def validate_sharepoint_field_name(field_name: str) -> bool:
        """
        Validate SharePoint field name.
        
        Args:
            field_name: Field name to validate
            
        Returns:
            True if valid, False otherwise
        """
        # SharePoint field names cannot contain certain characters
        invalid_chars = ['<', '>', '#', '%', '&', '*', '{', '}', '\\', ':', '/', '|', '"']
        
        if any(char in field_name for char in invalid_chars):
            return False
        
        if len(field_name) > 32:
            return False
        
        return True
    
    def validate_mapping(self) -> List[str]:
        """
        Validate field mapping.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        for synapse_field, sharepoint_field in self.field_mapping.items():
            if not self.validate_sharepoint_field_name(sharepoint_field):
                errors.append(
                    f"Invalid SharePoint field name: '{sharepoint_field}' "
                    f"(mapped from '{synapse_field}')"
                )
        
        return errors


def create_transformer_from_settings(settings) -> DataTransformer:
    """
    Create a DataTransformer from settings.
    
    Args:
        settings: Application settings
        
    Returns:
        Configured DataTransformer instance
    """
    try:
        # Parse field mapping from JSON string
        field_mapping = json.loads(settings.field_mapping) if settings.field_mapping else {}
        
        transformer = DataTransformer(field_mapping)
        
        # Validate mapping
        validation_errors = transformer.validate_mapping()
        if validation_errors:
            logger.warning("Field mapping validation warnings", errors=validation_errors)
        
        return transformer
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse field mapping JSON", error=str(e))
        raise ValueError(f"Invalid field_mapping JSON: {e}")


def chunk_data(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split data into chunks of specified size.
    
    Args:
        data: List of data items
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    chunks = []
    for i in range(0, len(data), chunk_size):
        chunks.append(data[i:i + chunk_size])
    
    logger.debug("Data chunked", total_items=len(data), chunk_count=len(chunks))
    return chunks
