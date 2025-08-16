"""
Configuration module for the Multi-Agent Code Generation System.
Handles environment variables and application settings.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Multi-Agent Code Generation System"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_workers: int = 1
    server_reload: bool = True
    server_log_level: str = "info"
    
    # Database settings
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/multiagent"
    database_echo: bool = False
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300  # 5 minutes default TTL
    
    # Security settings
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    api_key: Optional[str] = None
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    
    # CrewAI settings
    crewai_verbose: bool = True
    crewai_memory: bool = True
    max_iter: int = 10
    max_execution_time: int = 300  # 5 minutes
    
    # File storage settings
    upload_dir: str = "./uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", 
        ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".env"
    ]
    
    # Rate limiting settings
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # WebSocket settings
    websocket_timeout: int = 60
    websocket_ping_interval: int = 30
    
    # Monitoring settings
    enable_prometheus: bool = True
    metrics_endpoint: str = "/metrics"
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Backend URL (for frontend)
    backend_url: str = "http://localhost:8000"
    
    # Feature flags for phased rollout
    FEATURE_FLAGS = {
        "cost_based_scheduling": False,  # Phase 2
        "critical_path_analysis": True,  # Phase 1
    }
    
    @validator("upload_dir")
    def create_upload_dir(cls, v):
        """Ensure upload directory exists."""
        try:
            # Use /tmp for Vercel compatibility
            if os.getenv("VERCEL") == "1":
                v = "/tmp/uploads"
            
            Path(v).mkdir(parents=True, exist_ok=True)
            return v
        except (OSError, PermissionError) as e:
            # If we can't create the directory, use /tmp as fallback
            if os.getenv("VERCEL") == "1":
                fallback_path = "/tmp/uploads"
                try:
                    Path(fallback_path).mkdir(parents=True, exist_ok=True)
                    return fallback_path
                except:
                    return None
            else:
                raise e
    
    @validator("openai_api_key", pre=True)
    def validate_openai_key(cls, v):
        """Validate OpenAI API key is provided."""
        if not v:
            # Try to get from environment if not provided
            v = os.getenv("OPENAI_API_KEY")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings