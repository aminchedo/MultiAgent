"""
Vercel-specific configuration for serverless deployment.
Disables database and Redis dependencies that are not available in serverless environment.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

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
            kwargs.setdefault('upload_dir', None)  # Disable uploads by default
            kwargs.setdefault('is_vercel', True)
            kwargs.setdefault('is_local', False)
            kwargs.setdefault('database_url', 'sqlite:///:memory:')
            kwargs.setdefault('debug', False)
        else:
            # Running locally - can create directories
            upload_path = kwargs.get('upload_dir', 'uploads')
            kwargs.setdefault('upload_dir', upload_path)
            kwargs.setdefault('is_vercel', False)
            kwargs.setdefault('is_local', True)
        
        super().__init__(**kwargs)
    
    def ensure_upload_dir(self) -> Optional[str]:
        """Lazily create upload directory when needed (only for local development)"""
        if self.is_vercel:
            # On Vercel, use /tmp for temporary uploads
            upload_path = "/tmp/uploads"
            try:
                Path(upload_path).mkdir(parents=True, exist_ok=True)
                logger.info(f"Created temporary upload directory: {upload_path}")
                return upload_path
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not create upload directory {upload_path}: {e}")
                return None
        else:
            # Local development
            if self.upload_dir:
                try:
                    Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created upload directory: {self.upload_dir}")
                    return self.upload_dir
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not create upload directory {self.upload_dir}: {e}")
                    return None
            return None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance safely - no directory operations at module level
def get_vercel_settings():
    """Get settings instance with error handling"""
    try:
        settings = VercelSettings()
        logger.info("Vercel settings created successfully")
        return settings
    except Exception as e:
        logger.error(f"Failed to create settings: {e}")
        # Return minimal safe settings for Vercel
        return VercelSettings(
            upload_dir=None,
            database_url="sqlite:///:memory:",
            debug=False,
            is_vercel=True,
            is_local=False
        )

# Global settings instance - created without directory operations
# This prevents read-only filesystem errors during import
vercel_settings = get_vercel_settings()