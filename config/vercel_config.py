"""
Vercel-specific configuration for serverless deployment.
Disables database and Redis dependencies that are not available in serverless environment.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class VercelSettings(BaseSettings):
    """Settings for Vercel deployment with read-only filesystem handling"""
    
    # Database settings
    database_url: str = "sqlite:///:memory:"
    
    # Upload settings - Modified for Vercel
    upload_dir: Optional[str] = None  # Will be set based on environment
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # API settings
    api_key: Optional[str] = None
    debug: bool = False
    
    # Environment detection
    is_vercel: bool = False
    is_local: bool = True
    
    def __init__(self, **kwargs):
        """Initialize settings with environment detection"""
        
        # Detect Vercel environment
        is_vercel_env = os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
        
        if is_vercel_env:
            # Running on Vercel - read-only filesystem
            kwargs.setdefault('upload_dir', None)  # Disable uploads
            kwargs.setdefault('is_vercel', True)
            kwargs.setdefault('is_local', False)
            kwargs.setdefault('database_url', 'sqlite:///:memory:')
            kwargs.setdefault('debug', False)
        else:
            # Running locally - can create directories
            upload_path = kwargs.get('upload_dir', 'uploads')
            try:
                if upload_path:
                    # Use /tmp for Vercel compatibility, fallback to local path
                    if os.getenv("VERCEL") == "1":
                        upload_path = "/tmp/uploads"
                    
                    Path(upload_path).mkdir(parents=True, exist_ok=True)
                    kwargs['upload_dir'] = str(upload_path)
            except (OSError, PermissionError):
                # If can't create directory, disable uploads
                kwargs['upload_dir'] = None
            
            kwargs.setdefault('is_vercel', False)
            kwargs.setdefault('is_local', True)
        
        super().__init__(**kwargs)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance safely
def get_vercel_settings():
    """Get settings instance with error handling"""
    try:
        return VercelSettings()
    except Exception as e:
        print(f"Warning: Failed to create settings: {e}")
        # Return minimal safe settings for Vercel
        return VercelSettings(
            upload_dir=None,
            database_url="sqlite:///:memory:",
            debug=False,
            is_vercel=True,
            is_local=False
        )

# Global settings instance
vercel_settings = get_vercel_settings()