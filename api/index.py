"""
Vercel serverless function entry point for the Multi-Agent Code Generation System.
"""

import os
import sys
import logging
import traceback

# Set Vercel environment variables BEFORE any imports
os.environ["VERCEL"] = "1"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger.info(f"Project root: {project_root}")
logger.info(f"Python path: {sys.path}")

def create_minimal_app():
    """Create a minimal FastAPI app for error cases"""
    from fastapi import FastAPI
    
    error_app = FastAPI(title="Error Handler")
    
    @error_app.get("/api/health")
    async def error_health():
        return {
            "status": "error", 
            "message": "Main app failed to load",
            "environment": "vercel"
        }
    
    @error_app.get("/api")
    async def error_root():
        return {
            "error": "Main application failed to initialize",
            "environment": "vercel"
        }
    
    return error_app

# Try to import the main app with better error handling
try:
    logger.info("Attempting to import vercel_app...")
    from api.vercel_app import app
    logger.info("Successfully imported vercel_app")
    
except Exception as e:
    logger.error(f"Failed to import vercel_app: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Create minimal working app
    app = create_minimal_app()
    logger.info("Created minimal error handler app")

# Export for Vercel
handler = app
