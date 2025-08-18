"""
Configuration settings for the ITSM AI Agent
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_title: str = "ITSM AI Agent API"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered ITSM agent with Teams integration"
    debug: bool = False
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_key: str = os.getenv("AZURE_OPENAI_KEY", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    azure_openai_deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    
    # Azure Cosmos DB Configuration
    cosmos_endpoint: str = os.getenv("COSMOS_ENDPOINT", "")
    cosmos_key: str = os.getenv("COSMOS_KEY", "")
    cosmos_database_name: str = os.getenv("COSMOS_DATABASE_NAME", "itsm_agent")
    cosmos_conversations_container: str = os.getenv("COSMOS_CONVERSATIONS_CONTAINER", "conversations")
    cosmos_users_container: str = os.getenv("COSMOS_USERS_CONTAINER", "users")
    cosmos_agents_container: str = os.getenv("COSMOS_AGENTS_CONTAINER", "agents")
    cosmos_tickets_container: str = os.getenv("COSMOS_TICKETS_CONTAINER", "tickets")
    
    # Azure Computer Vision Configuration
    computer_vision_endpoint: str = os.getenv("COMPUTER_VISION_ENDPOINT", "")
    computer_vision_key: str = os.getenv("COMPUTER_VISION_KEY", "")
    
    # Azure Text Analytics Configuration
    text_analytics_endpoint: str = os.getenv("TEXT_ANALYTICS_ENDPOINT", "")
    text_analytics_key: str = os.getenv("TEXT_ANALYTICS_KEY", "")
    
    # Azure Storage Configuration
    storage_connection_string: str = os.getenv("STORAGE_CONNECTION_STRING", "")
    storage_container_name: str = os.getenv("STORAGE_CONTAINER_NAME", "agent-files")
    
    # Bot Framework Configuration
    microsoft_app_id: str = os.getenv("MICROSOFT_APP_ID", "")
    microsoft_app_password: str = os.getenv("MICROSOFT_APP_PASSWORD", "")
    
    # Teams Configuration
    teams_app_id: str = os.getenv("TEAMS_APP_ID", "")
    teams_tenant_id: str = os.getenv("TEAMS_TENANT_ID", "")
    
    # Agent Configuration
    max_conversation_history: int = 20
    context_memory_ttl_hours: int = 24 * 7  # 7 days
    proactive_suggestions_enabled: bool = True
    human_handoff_enabled: bool = True
    visual_analysis_enabled: bool = True
    
    # API Rate Limiting
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst: int = 200
    
    # Security
    allowed_origins: list = ["*"]  # Configure for production
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def validate_azure_config() -> bool:
    """Validate that required Azure configurations are present"""
    required_configs = [
        settings.azure_openai_endpoint,
        settings.azure_openai_key,
        settings.cosmos_endpoint,
        settings.cosmos_key,
    ]
    
    return all(config for config in required_configs)


def get_database_config() -> dict:
    """Get database configuration"""
    return {
        "endpoint": settings.cosmos_endpoint,
        "key": settings.cosmos_key,
        "database_name": settings.cosmos_database_name,
        "containers": {
            "conversations": settings.cosmos_conversations_container,
            "users": settings.cosmos_users_container,
            "agents": settings.cosmos_agents_container,
            "tickets": settings.cosmos_tickets_container,
        }
    }


def get_openai_config() -> dict:
    """Get OpenAI configuration"""
    return {
        "endpoint": settings.azure_openai_endpoint,
        "key": settings.azure_openai_key,
        "api_version": settings.azure_openai_api_version,
        "deployment_name": settings.azure_openai_deployment_name,
    }


def get_vision_config() -> dict:
    """Get Computer Vision configuration"""
    return {
        "endpoint": settings.computer_vision_endpoint,
        "key": settings.computer_vision_key,
    }


def get_analytics_config() -> dict:
    """Get Text Analytics configuration"""
    return {
        "endpoint": settings.text_analytics_endpoint,
        "key": settings.text_analytics_key,
    }
