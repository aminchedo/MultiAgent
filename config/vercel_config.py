"""
Vercel-specific configuration for serverless deployment.
Disables database and Redis dependencies that are not available in serverless environment.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator
from pathlib import Path


class VercelSettings(BaseSettings):
    """Vercel-specific application settings for serverless deployment."""
    
    # Application settings
    app_name: str = "Multi-Agent Code Generation System"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings (not used in serverless)
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_workers: int = 1
    server_reload: bool = False  # Disabled for serverless
    server_log_level: str = "info"
    
    # Database settings (disabled for serverless)
    database_url: str = ""  # Empty for serverless
    database_echo: bool = False
    
    # Redis settings (disabled for serverless)
    redis_url: str = ""  # Empty for serverless
    cache_ttl: int = 300
    
    # Security settings
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    api_key: Optional[str] = None
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    
    # CrewAI settings
    crewai_verbose: bool = True
    crewai_memory: bool = False  # Disabled for serverless
    max_iter: int = 5  # Reduced for serverless
    max_execution_time: int = 60  # Reduced for serverless
    
    # File storage settings (disabled for serverless)
    upload_dir: str = "/tmp"  # Use temp directory
    max_file_size: int = 5 * 1024 * 1024  # Reduced to 5MB
    allowed_extensions: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", 
        ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".env"
    ]
    
    # Rate limiting settings (reduced for serverless)
    rate_limit_requests: int = 50
    rate_limit_window: int = 3600
    
    # WebSocket settings (disabled for serverless)
    websocket_timeout: int = 30
    websocket_ping_interval: int = 15
    
    # Monitoring settings (disabled for serverless)
    enable_prometheus: bool = False
    metrics_endpoint: str = "/metrics"
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Backend URL (for frontend)
    backend_url: str = "https://your-vercel-domain.vercel.app"
    
    @validator("upload_dir")
    def create_upload_dir(cls, v):
        """Ensure upload directory exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("openai_api_key", pre=True)
    def validate_openai_key(cls, v):
        """Validate OpenAI API key is provided."""
        if not v:
            v = os.getenv("OPENAI_API_KEY")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global Vercel settings instance
vercel_settings = VercelSettings()


def get_vercel_settings() -> VercelSettings:
    """Get Vercel-specific application settings."""
    return vercel_settings