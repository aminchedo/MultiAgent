"""
Vercel serverless function entry point for the Multi-Agent Code Generation System.
"""

import sys
import os
from pathlib import Path
import traceback
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Add the project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Python path: {sys.path}")
    
    # Import the Vercel-specific FastAPI app
    from api.vercel_app import app
    
    logger.info("Successfully imported vercel_app")
    
    # Export the app for Vercel
    handler = app
    
    logger.info("Handler setup complete")

except Exception as e:
    logger.error(f"Failed to import vercel_app: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Create a minimal error handler if import fails
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    error_app = FastAPI()
    
    @error_app.get("/")
    async def error_root():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Serverless function failed to initialize",
                "details": str(e),
                "status": "error"
            }
        )
    
    @error_app.get("/health")
    async def error_health():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Serverless function failed to initialize",
                "details": str(e),
                "status": "error"
            }
        )
    
    handler = error_app
    logger.info("Error handler setup complete")
