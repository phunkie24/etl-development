"""
Configuration settings for Synapse to SharePoint integration.
Uses Pydantic for validation and environment variable management.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Azure Synapse Settings
    synapse_server: str = Field(..., description="Synapse SQL endpoint")
    synapse_database: str = Field(..., description="Synapse database name")
    synapse_username: Optional[str] = Field(None, description="SQL authentication username")
    synapse_password: Optional[str] = Field(None, description="SQL authentication password")
    
    # Azure AD Authentication (preferred over SQL auth)
    use_managed_identity: bool = Field(default=False, description="Use Managed Identity for Synapse")
    
    # SharePoint Settings
    sharepoint_site_url: str = Field(..., description="SharePoint site URL")
    sharepoint_list_name: str = Field(..., description="SharePoint list name")
    
    # Azure AD App Registration
    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    client_id: str = Field(..., description="Azure AD Application (client) ID")
    client_secret: str = Field(..., description="Azure AD Application secret")
    
    # Query Configuration
    synapse_query: str = Field(..., description="SQL query to execute")
    batch_size: int = Field(default=100, description="Number of items to process in each batch")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # SharePoint List Field Mapping (JSON string or dict)
    field_mapping: str = Field(
        default='{}',
        description="JSON mapping of SQL columns to SharePoint fields"
    )
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Batch size must be between 1 and 1000')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
