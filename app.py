#!/usr/bin/env python3
"""
Hugging Face Spaces entry point for the Multi-Agent Code Generation System.
This file serves as the main entry point for deployment on Hugging Face Spaces.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
import uvicorn
from backend.core.app import app
from config.config import get_settings

def create_directories():
    """Create necessary directories for the application."""
    directories = ["logs", "temp", "uploads", "static"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directory created/verified: {directory}")

def setup_environment():
    """Setup environment for Hugging Face Spaces."""
    # Set default values for HF Spaces
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "7860")
    os.environ.setdefault("SERVER_HOST", "0.0.0.0")
    os.environ.setdefault("SERVER_PORT", "7860")
    os.environ.setdefault("SERVER_WORKERS", "1")
    os.environ.setdefault("SERVER_RELOAD", "false")
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./multiagent.db")
    
    # Set production defaults
    os.environ.setdefault("APP_ENV", "production")
    os.environ.setdefault("SERVER_LOG_LEVEL", "info")
    
    print("🔧 Environment configured for Hugging Face Spaces")

def main():
    """Main entry point for Hugging Face Spaces."""
    print("🚀 Starting Multi-Agent Code Generation System on Hugging Face Spaces")
    
    # Setup environment and directories
    setup_environment()
    create_directories()
    
    # Get settings
    settings = get_settings()
    
    print(f"🌐 Server starting on {settings.server_host}:{settings.server_port}")
    print(f"🤖 AI Engine: OpenAI GPT-4")
    print(f"🔧 Environment: {os.environ.get('APP_ENV', 'production')}")
    
    # Configure for HF Spaces (single worker, no reload)
    uvicorn.run(
        "backend.core.app:app",
        host=settings.server_host,
        port=int(os.environ.get("PORT", settings.server_port)),
        workers=1,  # Single worker for HF Spaces
        reload=False,  # No reload in production
        log_level=settings.server_log_level,
        access_log=True,
        loop="asyncio"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)