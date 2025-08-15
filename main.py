#!/usr/bin/env python3
"""
Main entry point for the Multi-Agent Code Generation System.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    from backend.core.app import app
    from config.config import get_settings
    
    settings = get_settings()
    
    uvicorn.run(
        "backend.core.app:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
        workers=settings.server_workers,
        log_level=settings.server_log_level
    )