"""
Configuration module for the Multi-Agent Code Generation System.
Handles environment variables and application settings for Hugging Face Spaces.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support for Hugging Face."""
    
    # Application settings
    app_name: str = "Multi-Agent Code Generation System"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings (Hugging Face uses port 7860)
    host: str = "0.0.0.0"
    port: int = 7860
    workers: int = 1
    server_host: str = "0.0.0.0"
    server_port: int = 7860
    server_workers: int = 1
    server_reload: bool = False  # Disabled for production
    server_log_level: str = "info"
    
    # Database settings (SQLite for Hugging Face)
    database_url: str = "sqlite+aiosqlite:///./multiagent.db"
    database_echo: bool = False
    
    # Cache settings (Memory-based, no Redis)
    cache_ttl: int = 3600  # 1 hour default TTL
    max_cache_size: int = 1000  # Maximum cache entries
    
    # Security settings
    jwt_secret_key: str = "huggingface-multiagent-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    api_key: Optional[str] = None
    
    # OpenAI settings (Required for agents)
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
    temp_dir: str = "./temp"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", 
        ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".env",
        ".vue", ".go", ".java", ".cpp", ".c", ".cs", ".php", ".rb"
    ]
    
    # Rate limiting settings (more conservative for shared hosting)
    rate_limit_requests: int = 50
    rate_limit_window: int = 3600  # 1 hour
    
    # WebSocket settings
    websocket_timeout: int = 60
    websocket_ping_interval: int = 30
    
    # Monitoring settings (simplified for Hugging Face)
    enable_prometheus: bool = False  # Disabled for simplicity
    metrics_endpoint: str = "/metrics"
    
    # CORS settings (open for Hugging Face Spaces)
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Hugging Face specific settings
    hf_space_id: Optional[str] = None
    hf_token: Optional[str] = None
    
    # Backend URL (for frontend)
    backend_url: str = "http://localhost:7860"
    
    # Agent settings
    max_concurrent_generations: int = 3
    timeout_seconds: int = 300
    
    @validator("upload_dir", "temp_dir")
    def create_directories(cls, v):
        """Ensure directories exist."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("openai_api_key", pre=True)
    def validate_openai_key(cls, v):
        """Validate OpenAI API key is provided."""
        if not v:
            # Try to get from environment if not provided
            v = os.getenv("OPENAI_API_KEY")
        if not v:
            print("⚠️  Warning: OPENAI_API_KEY not set. AI agents will not work!")
        return v
    
    @validator("database_url", pre=True)
    def ensure_sqlite_for_hf(cls, v):
        """Ensure SQLite is used for Hugging Face deployment."""
        if v and ("postgresql" in v or "postgres" in v):
            print("🔄 Converting PostgreSQL URL to SQLite for Hugging Face compatibility")
            return "sqlite+aiosqlite:///./multiagent.db"
        elif not v or v == "":
            return "sqlite+aiosqlite:///./multiagent.db"
        return v
    
    @validator("port", pre=True)
    def ensure_hf_port(cls, v):
        """Ensure correct port for Hugging Face Spaces."""
        env_port = os.getenv("PORT")
        if env_port:
            return int(env_port)
        return v or 7860
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings