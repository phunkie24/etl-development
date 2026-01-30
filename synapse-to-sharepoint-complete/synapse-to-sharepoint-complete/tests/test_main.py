"""
Tests for main pipeline orchestration.
"""
import pytest
from unittest.mock import Mock, patch
from src.main import SynapseToSharePointPipeline


class TestSynapseToSharePointPipeline:
    """Test main pipeline orchestrator."""
    
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_init(self, mock_transformer, mock_logging, mock_settings):
        """Test pipeline initialization."""
        mock_transformer.return_value = Mock()
        
        pipeline = SynapseToSharePointPipeline(mock_settings)
        
        assert pipeline.settings == mock_settings
        mock_logging.assert_called_once_with(mock_settings.log_level)
        mock_transformer.assert_called_once_with(mock_settings)
    
    @patch('src.main.get_synapse_data')
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_extract_success(self, mock_transformer, mock_logging, 
                            mock_get_data, mock_settings, sample_synapse_data):
        """Test successful data extraction."""
        mock_transformer.return_value = Mock()
        mock_get_data.return_value = sample_synapse_data
        
        pipeline = SynapseToSharePointPipeline(mock_settings)
        result = pipeline.extract()
        
        assert result == sample_synapse_data
        mock_get_data.assert_called_once_with(mock_settings)
    
    @patch('src.main.get_synapse_data')
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_extract_failure(self, mock_transformer, mock_logging, 
                            mock_get_data, mock_settings):
        """Test extraction failure."""
        mock_transformer.return_value = Mock()
        mock_get_data.side_effect = Exception("Connection failed")
        
        pipeline = SynapseToSharePointPipeline(mock_settings)
        
        with pytest.raises(Exception):
            pipeline.extract()
    
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_transform_success(self, mock_transformer_factory, mock_logging,
                               mock_settings, sample_synapse_data, 
                               sample_transformed_data):
        """Test successful data transformation."""
        mock_transformer = Mock()
        mock_transformer.transform_batch.return_value = sample_transformed_data
        mock_transformer_factory.return_value = mock_transformer
        
        pipeline = SynapseToSharePointPipeline(mock_settings)
        result = pipeline.transform(sample_synapse_data)
        
        assert result == sample_transformed_data
        mock_transformer.transform_batch.assert_called_once_with(sample_synapse_data)
    
    @patch('src.main.upload_to_sharepoint')
    @patch('src.main.chunk_data')
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_load_success(self, mock_transformer, mock_logging, mock_chunk,
                         mock_upload, mock_settings, sample_transformed_data):
        """Test successful data loading."""
        mock_transformer.return_value = Mock()
        mock_chunk.return_value = [sample_transformed_data]
        mock_upload.return_value = {
            "success": 3,
            "failed": 0,
            "errors": []
        }
        
        pipeline = SynapseToSharePointPipeline(mock_settings)
        result = pipeline.load(sample_transformed_data)
        
        assert result["success"] == 3
        assert result["failed"] == 0
        assert result["total_chunks"] == 1
        mock_chunk.assert_called_once()
        mock_upload.assert_called_once()
    
    @patch('src.main.upload_to_sharepoint')
    @patch('src.main.chunk_data')
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_load_with_failures(self, mock_transformer, mock_logging, mock_chunk,
                               mock_upload, mock_settings, sample_transformed_data):
        """Test data loading with some failures."""
        mock_transformer.return_value = Mock()
        mock_chunk.return_value = [sample_transformed_data]
        mock_upload.return_value = {
            "success": 2,
            "failed": 1,
            "errors": [{"item_index": 3, "error": "Failed"}]
        }
        
        pipeline = SynapseToSharePointPipeline(mock_settings)
        result = pipeline.load(sample_transformed_data)
        
        assert result["success"] == 2
        assert result["failed"] == 1
        assert len(result["errors"]) == 1
    
    @patch('src.main.upload_to_sharepoint')
    @patch('src.main.get_synapse_data')
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_run_success(self, mock_transformer_factory, mock_logging,
                        mock_get_data, mock_upload, mock_settings,
                        sample_synapse_data, sample_transformed_data):
        """Test successful full pipeline run."""
        mock_transformer = Mock()
        mock_transformer.transform_batch.return_value = sample_transformed_data
        mock_transformer_factory.return_value = mock_transformer
        
        mock_get_data.return_value = sample_synapse_data
        mock_upload.return_value = {
            "success": 3,
            "failed": 0,
            "errors": []
        }
        
        with patch('src.main.chunk_data') as mock_chunk:
            mock_chunk.return_value = [sample_transformed_data]
            
            pipeline = SynapseToSharePointPipeline(mock_settings)
            result = pipeline.run()
        
        assert result["status"] == "success"
        assert result["extracted_rows"] == 3
        assert result["transformed_rows"] == 3
        assert result["loaded_rows"] == 3
        assert result["failed_rows"] == 0
    
    @patch('src.main.upload_to_sharepoint')
    @patch('src.main.get_synapse_data')
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_run_partial_success(self, mock_transformer_factory, mock_logging,
                                 mock_get_data, mock_upload, mock_settings,
                                 sample_synapse_data, sample_transformed_data):
        """Test pipeline run with partial success."""
        mock_transformer = Mock()
        mock_transformer.transform_batch.return_value = sample_transformed_data
        mock_transformer_factory.return_value = mock_transformer
        
        mock_get_data.return_value = sample_synapse_data
        mock_upload.return_value = {
            "success": 2,
            "failed": 1,
            "errors": [{"item_index": 3, "error": "Failed"}]
        }
        
        with patch('src.main.chunk_data') as mock_chunk:
            mock_chunk.return_value = [sample_transformed_data]
            
            pipeline = SynapseToSharePointPipeline(mock_settings)
            result = pipeline.run()
        
        assert result["status"] == "partial_success"
        assert result["loaded_rows"] == 2
        assert result["failed_rows"] == 1
    
    @patch('src.main.get_synapse_data')
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_run_no_data(self, mock_transformer_factory, mock_logging,
                        mock_get_data, mock_settings):
        """Test pipeline run with no data extracted."""
        mock_transformer = Mock()
        mock_transformer_factory.return_value = mock_transformer
        mock_get_data.return_value = []
        
        pipeline = SynapseToSharePointPipeline(mock_settings)
        result = pipeline.run()
        
        assert result["status"] == "success"
        assert result["extracted_rows"] == 0
    
    @patch('src.main.get_synapse_data')
    @patch('src.main.configure_logging')
    @patch('src.main.create_transformer_from_settings')
    def test_run_extraction_failure(self, mock_transformer_factory, mock_logging,
                                   mock_get_data, mock_settings):
        """Test pipeline run with extraction failure."""
        mock_transformer = Mock()
        mock_transformer_factory.return_value = mock_transformer
        mock_get_data.side_effect = Exception("Database error")
        
        pipeline = SynapseToSharePointPipeline(mock_settings)
        
        with pytest.raises(Exception):
            pipeline.run()
