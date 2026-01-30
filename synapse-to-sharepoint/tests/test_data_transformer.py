"""
Tests for data transformation module.
"""
import pytest
from datetime import datetime, date
from src.data_transformer import (
    DataTransformer,
    create_transformer_from_settings,
    chunk_data
)


class TestDataTransformer:
    """Test DataTransformer class."""
    
    def test_init_without_mapping(self):
        """Test initialization without field mapping."""
        transformer = DataTransformer()
        assert transformer.field_mapping == {}
    
    def test_init_with_mapping(self):
        """Test initialization with field mapping."""
        mapping = {"old_field": "NewField"}
        transformer = DataTransformer(mapping)
        assert transformer.field_mapping == mapping
    
    def test_serialize_none(self):
        """Test serialization of None value."""
        result = DataTransformer.serialize_value(None)
        assert result is None
    
    def test_serialize_datetime(self):
        """Test serialization of datetime."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = DataTransformer.serialize_value(dt)
        assert result == "2024-01-15T10:30:00"
    
    def test_serialize_date(self):
        """Test serialization of date."""
        d = date(2024, 1, 15)
        result = DataTransformer.serialize_value(d)
        assert result == "2024-01-15"
    
    def test_serialize_boolean(self):
        """Test serialization of boolean."""
        assert DataTransformer.serialize_value(True) is True
        assert DataTransformer.serialize_value(False) is False
    
    def test_serialize_numeric(self):
        """Test serialization of numeric values."""
        assert DataTransformer.serialize_value(42) == 42
        assert DataTransformer.serialize_value(3.14) == 3.14
    
    def test_serialize_string(self):
        """Test serialization of string."""
        assert DataTransformer.serialize_value("test") == "test"
    
    def test_transform_row_without_mapping(self):
        """Test row transformation without field mapping."""
        transformer = DataTransformer()
        row = {"field1": "value1", "field2": 42}
        result = transformer.transform_row(row)
        
        assert result == {"field1": "value1", "field2": 42}
    
    def test_transform_row_with_mapping(self):
        """Test row transformation with field mapping."""
        mapping = {"field1": "Field1", "field2": "Field2"}
        transformer = DataTransformer(mapping)
        row = {"field1": "value1", "field2": 42}
        result = transformer.transform_row(row)
        
        assert result == {"Field1": "value1", "Field2": 42}
    
    def test_transform_row_partial_mapping(self):
        """Test row transformation with partial field mapping."""
        mapping = {"field1": "Field1"}
        transformer = DataTransformer(mapping)
        row = {"field1": "value1", "field2": 42}
        result = transformer.transform_row(row)
        
        assert result == {"Field1": "value1", "field2": 42}
    
    def test_transform_batch(self, sample_synapse_data):
        """Test batch transformation."""
        mapping = {"id": "ID", "name": "Title"}
        transformer = DataTransformer(mapping)
        result = transformer.transform_batch(sample_synapse_data)
        
        assert len(result) == 3
        assert result[0]["ID"] == 1
        assert result[0]["Title"] == "Test Item 1"
    
    def test_validate_sharepoint_field_name_valid(self):
        """Test validation of valid SharePoint field names."""
        assert DataTransformer.validate_sharepoint_field_name("ValidField") is True
        assert DataTransformer.validate_sharepoint_field_name("Field_Name") is True
        assert DataTransformer.validate_sharepoint_field_name("Field123") is True
    
    def test_validate_sharepoint_field_name_invalid_chars(self):
        """Test validation of invalid SharePoint field names."""
        invalid_names = ["Field<Name", "Field>Name", "Field#Name", "Field%Name"]
        for name in invalid_names:
            assert DataTransformer.validate_sharepoint_field_name(name) is False
    
    def test_validate_sharepoint_field_name_too_long(self):
        """Test validation of field name that's too long."""
        long_name = "a" * 33
        assert DataTransformer.validate_sharepoint_field_name(long_name) is False
    
    def test_validate_mapping_valid(self):
        """Test validation of valid field mapping."""
        mapping = {"field1": "Field1", "field2": "Field2"}
        transformer = DataTransformer(mapping)
        errors = transformer.validate_mapping()
        assert len(errors) == 0
    
    def test_validate_mapping_invalid(self):
        """Test validation of invalid field mapping."""
        mapping = {"field1": "Field<Invalid>"}
        transformer = DataTransformer(mapping)
        errors = transformer.validate_mapping()
        assert len(errors) > 0


class TestCreateTransformerFromSettings:
    """Test transformer creation from settings."""
    
    def test_create_with_valid_mapping(self, mock_settings):
        """Test creating transformer with valid JSON mapping."""
        transformer = create_transformer_from_settings(mock_settings)
        assert isinstance(transformer, DataTransformer)
        assert transformer.field_mapping == {"id": "ID", "name": "Title"}
    
    def test_create_with_empty_mapping(self, mock_settings):
        """Test creating transformer with empty mapping."""
        mock_settings.field_mapping = "{}"
        transformer = create_transformer_from_settings(mock_settings)
        assert transformer.field_mapping == {}
    
    def test_create_with_invalid_json(self, mock_settings):
        """Test creating transformer with invalid JSON."""
        mock_settings.field_mapping = "invalid json"
        with pytest.raises(ValueError):
            create_transformer_from_settings(mock_settings)


class TestChunkData:
    """Test data chunking function."""
    
    def test_chunk_exact_division(self):
        """Test chunking with exact division."""
        data = list(range(10))
        chunks = chunk_data(data, 5)
        
        assert len(chunks) == 2
        assert chunks[0] == [0, 1, 2, 3, 4]
        assert chunks[1] == [5, 6, 7, 8, 9]
    
    def test_chunk_with_remainder(self):
        """Test chunking with remainder."""
        data = list(range(11))
        chunks = chunk_data(data, 5)
        
        assert len(chunks) == 3
        assert chunks[0] == [0, 1, 2, 3, 4]
        assert chunks[1] == [5, 6, 7, 8, 9]
        assert chunks[2] == [10]
    
    def test_chunk_single_chunk(self):
        """Test chunking when data fits in single chunk."""
        data = list(range(5))
        chunks = chunk_data(data, 10)
        
        assert len(chunks) == 1
        assert chunks[0] == [0, 1, 2, 3, 4]
    
    def test_chunk_empty_data(self):
        """Test chunking empty data."""
        data = []
        chunks = chunk_data(data, 5)
        
        assert len(chunks) == 0
