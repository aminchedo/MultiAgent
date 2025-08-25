"""
Vercel-specific utilities for handling file operations in serverless environment.
"""

import os
from pathlib import Path
from typing import Union, Optional


def get_vercel_safe_path(file_path: Union[str, Path]) -> Path:
    """
    Convert any file path to a Vercel-safe path using /tmp directory.
    
    Args:
        file_path: Original file path
        
    Returns:
        Path object pointing to a writable location
    """
    if os.getenv("VERCEL") == "1":
        # On Vercel, always use /tmp
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # If it's already in /tmp, return as is
        if str(file_path).startswith("/tmp"):
            return file_path
        
        # Otherwise, move it to /tmp/uploads
        filename = file_path.name
        return Path("/tmp/uploads") / filename
    else:
        # Local development - use original path
        return Path(file_path)


def ensure_vercel_directory(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists and is writable, using /tmp on Vercel.
    
    Args:
        directory: Directory path to create
        
    Returns:
        Path object of the created directory
    """
    if os.getenv("VERCEL") == "1":
        # On Vercel, always use /tmp
        if isinstance(directory, str):
            directory = Path(directory)
        
        # If it's already in /tmp, use as is
        if str(directory).startswith("/tmp"):
            safe_dir = directory
        else:
            # Move to /tmp
            safe_dir = Path("/tmp") / directory.name
        
        # Create directory
        safe_dir.mkdir(parents=True, exist_ok=True)
        return safe_dir
    else:
        # Local development - use original path
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory


def write_file_vercel_safe(file_path: Union[str, Path], content: str) -> tuple[Path, str]:
    """
    Write content to a file using Vercel-safe path.
    
    Args:
        file_path: Target file path
        content: Content to write
        
    Returns:
        Tuple of (actual_path, status_message)
    """
    try:
        safe_path = get_vercel_safe_path(file_path)
        
        # Ensure parent directory exists
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        safe_path.write_text(content, encoding='utf-8')
        
        return safe_path, f"Successfully wrote file: {safe_path}"
    except Exception as e:
        return Path(file_path), f"Error writing file {file_path}: {str(e)}"


def create_temp_file_vercel_safe(suffix: str = "", prefix: str = "temp_") -> Path:
    """
    Create a temporary file using Vercel-safe location.
    
    Args:
        suffix: File suffix (e.g., '.py')
        prefix: File prefix
        
    Returns:
        Path to the created temporary file
    """
    if os.getenv("VERCEL") == "1":
        # On Vercel, use /tmp with unique name
        import uuid
        filename = f"{prefix}{uuid.uuid4().hex[:8]}{suffix}"
        temp_path = Path("/tmp") / filename
        return temp_path
    else:
        # Local development - use system temp directory
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, delete=False) as f:
            return Path(f.name)


def is_vercel_environment() -> bool:
    """
    Check if running in Vercel environment.
    
    Returns:
        True if running on Vercel, False otherwise
    """
    return os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None


def get_upload_directory() -> Optional[Path]:
    """
    Get the appropriate upload directory for the current environment.
    
    Returns:
        Path to upload directory, or None if uploads are disabled
    """
    if is_vercel_environment():
        # On Vercel, use /tmp/uploads
        upload_dir = Path("/tmp/uploads")
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            return upload_dir
        except (OSError, PermissionError):
            return None
    else:
        # Local development - use configured upload directory
        from config.config import get_settings
        settings = get_settings()
        if settings.upload_dir:
            try:
                upload_path = Path(settings.upload_dir)
                upload_path.mkdir(parents=True, exist_ok=True)
                return upload_path
            except (OSError, PermissionError):
                return None
        return None