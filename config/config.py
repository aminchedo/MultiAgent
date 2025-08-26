"""
Configuration module for the Multi-Agent Code Generation System.
Handles environment variables and application settings.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator, Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Enhanced 6-Agent Code Generation System"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = Field(default="development", description="Environment: development, staging, production")
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_workers: int = 1
    server_reload: bool = True
    server_log_level: str = "info"
    
    # OpenAI Configuration
    openai_api_key: str = Field(description="OpenAI API key for code generation")
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7
    openai_timeout: int = 120
    openai_max_retries: int = 3
    
    # Enhanced 6-Agent Configuration
    total_agents: int = 6
    qa_validation_enabled: bool = True
    minimum_quality_score: int = 85
    max_concurrent_agents: int = 6
    agent_timeout: int = 300
    agent_retry_attempts: int = 3
    agent_heartbeat_interval: int = 30
    
    # QA Validation Configuration
    qa_timeout_seconds: int = 600
    run_security_scans: bool = True
    run_performance_tests: bool = True
    required_test_coverage: int = 80
    
    # QA Testing Tools Configuration
    jest_timeout: int = 30000
    cypress_timeout: int = 60000
    lighthouse_timeout: int = 45000
    npm_audit_enabled: bool = True
    python_safety_check: bool = True
    
    # Enhanced WebSocket Configuration for 6-Agent System
    ws_message_size_limit: int = 1048576  # 1MB
    ws_ping_interval: int = 30
    ws_ping_timeout: int = 10
    ws_close_timeout: int = 10
    ws_agent_update_interval: int = 2  # seconds
    ws_qa_progress_detail: bool = True
    ws_max_connections: int = 100
    
    # File System Configuration
    output_dir: str = "./generated_projects"
    temp_dir: str = "./temp"
    max_file_size: int = 10485760  # 10MB
    max_project_files: int = 1000
    cleanup_temp_files: bool = True
    
    # Security Configuration
    jwt_secret_key: str = Field(description="JWT secret key for authentication")
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    api_key: Optional[str] = None
    cors_origins: List[str] = ["*"]
    rate_limit_per_minute: int = 60
    
    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",  # SQLite for dev
        description="Database connection URL"
    )
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300  # 5 minutes default TTL
    redis_max_connections: int = 10
    
    # gRPC Configuration
    grpc_server_port: int = 50051
    grpc_max_workers: int = 10
    grpc_max_message_length: int = 4194304  # 4MB
    grpc_keepalive_time: int = 30
    grpc_keepalive_timeout: int = 5
    
    # Monitoring and Logging
    log_level: str = "INFO"
    log_format: str = "json"
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # Performance Settings
    async_worker_count: int = 4
    max_background_tasks: int = 100
    request_timeout: int = 300
    
    # Project Generation Settings
    default_project_type: str = "react"
    supported_frameworks: List[str] = ["react", "vue", "vanilla", "nextjs", "nuxt"]
    max_generation_time: int = 600  # 10 minutes
    enable_file_preview: bool = True
    
    # Deployment Settings
    base_url: str = "http://localhost:8000"
    static_files_path: str = "./static"
    uploads_path: str = "./uploads"
    
    @validator('openai_api_key')
    def validate_openai_key(cls, v):
        if not v or v == "your-openai-api-key":
            raise ValueError("OPENAI_API_KEY must be set")
        return v
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if not v or v == "your-super-secret-jwt-key-change-in-production":
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("JWT_SECRET_KEY must be set in production")
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @validator('cors_origins', pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator('supported_frameworks', pre=True)
    def validate_frameworks(cls, v):
        if isinstance(v, str):
            return [fw.strip() for fw in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable mappings
        fields = {
            'openai_api_key': {'env': 'OPENAI_API_KEY'},
            'jwt_secret_key': {'env': 'JWT_SECRET_KEY'},
            'database_url': {'env': 'DATABASE_URL'},
            'redis_url': {'env': 'REDIS_URL'},
            'environment': {'env': 'ENVIRONMENT'},
            'base_url': {'env': 'BASE_URL'},
        }


# Global settings instance
settings = Settings()

# Export commonly used settings
DEBUG = settings.debug
ENVIRONMENT = settings.environment
OPENAI_API_KEY = settings.openai_api_key
DATABASE_URL = settings.database_url
REDIS_URL = settings.redis_url
JWT_SECRET_KEY = settings.jwt_secret_key