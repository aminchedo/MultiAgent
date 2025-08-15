"""
Vercel serverless function entry point for the Multi-Agent Code Generation System.
"""

import os
import sys
import logging
import traceback

# Set Vercel environment variables BEFORE any imports
os.environ["VERCEL"] = "1"

# Set up logging with proper configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optimize Python path modifications
def setup_python_path():
    """Optimize sys.path modifications for Vercel"""
    try:
        # Get absolute path to project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # Add project root to Python path if not already present
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            logger.info(f"Added project root to Python path: {project_root}")
        
        # Log Python path for debugging
        logger.info(f"Python path: {sys.path[:3]}...")  # Log first 3 entries
        return project_root
    except Exception as e:
        logger.error(f"Failed to setup Python path: {e}")
        return None

# Setup Python path
project_root = setup_python_path()

def create_minimal_app():
    """Create a minimal FastAPI app for error cases"""
    try:
        from fastapi import FastAPI
        
        error_app = FastAPI(title="Error Handler")
        
        @error_app.get("/health")
        async def health_check():
            return {
                "status": "error", 
                "message": "Main app failed to load",
                "environment": "vercel",
                "error_type": "import_failure"
            }
        
        @error_app.get("/api/health")
        async def api_health_check():
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
        
        @error_app.get("/")
        async def root():
            return {
                "message": "API Error Handler",
                "status": "error",
                "environment": "vercel"
            }
        
        return error_app
    except Exception as e:
        logger.error(f"Failed to create minimal app: {e}")
        # Return a basic dict as fallback
        return {"error": "Complete initialization failure"}

# Import error handling with detailed logging
def import_main_app():
    """Import main app with comprehensive error handling"""
    try:
        logger.info("Attempting to import vercel_app...")
        
        # Try relative import first
        try:
            from .vercel_app import app
            logger.info("Successfully imported vercel_app using relative import")
            return app
        except ImportError as e:
            logger.warning(f"Relative import failed: {e}")
            
            # Try absolute import
            try:
                from api.vercel_app import app
                logger.info("Successfully imported vercel_app using absolute import")
                return app
            except ImportError as e2:
                logger.error(f"Absolute import also failed: {e2}")
                raise ImportError(f"Both relative and absolute imports failed: {e}, {e2}")
                
    except ImportError as e:
        logger.error(f"Module import failed: {str(e)}")
        logger.error(f"Import traceback: {traceback.format_exc()}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during import: {str(e)}")
        logger.error(f"Unexpected error traceback: {traceback.format_exc()}")
        return None

# Try to import the main app with comprehensive error handling
app = import_main_app()

if app is None:
    logger.error("Failed to import main app, creating minimal error handler")
    app = create_minimal_app()

# Add health check endpoint to main app if it exists
if hasattr(app, 'get'):
    # Add health check endpoint
    @app.get('/health')
    async def health_check():
        return {
            'status': 'ok',
            'environment': 'vercel',
            'app_loaded': True
        }

# Export for Vercel - this is the correct way to export a FastAPI app
# Vercel's Python runtime will automatically detect this as an ASGI application
if hasattr(app, 'debug'):
    app.debug = False  # Ensure debug is disabled for production

logger.info("API index.py loaded successfully")
