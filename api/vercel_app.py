from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Validate required environment variables
def validate_env_vars():
    """Validate that required environment variables are present"""
    required_vars = ["OPENAI_API_KEY", "JWT_SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        return False
    return True

# Check environment variables
env_valid = validate_env_vars()

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Code Generation API",
    description="AI-powered code generation system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import settings safely
try:
    from config.vercel_config import get_vercel_settings
    settings = get_vercel_settings()
    logger.info("Settings loaded successfully")
    UPLOAD_ENABLED = settings.upload_dir is not None
except Exception as e:
    logger.error(f"Failed to load settings: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    settings = None
    UPLOAD_ENABLED = False

# Health check endpoint
@app.get("/api/health")
async def health_check():
    try:
        return {
            "status": "healthy",
            "message": "API is running",
            "environment": "vercel" if os.getenv("VERCEL") else "local",
            "upload_enabled": UPLOAD_ENABLED,
            "settings_loaded": settings is not None,
            "env_vars_valid": env_valid
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "environment": "vercel" if os.getenv("VERCEL") else "local"
        }

# Root endpoint
@app.get("/api")
async def root():
    try:
        return {
            "message": "Multi-Agent Code Generation API",
            "version": "1.0.0",
            "environment": "vercel" if os.getenv("VERCEL") else "local"
        }
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "error": "Internal server error",
            "message": str(e),
            "environment": "vercel" if os.getenv("VERCEL") else "local"
        }

# Test endpoint
@app.get("/api/test")
async def test_endpoint():
    try:
        return {
            "message": "Test endpoint working",
            "timestamp": "2025-08-15",
            "environment_vars": {
                "VERCEL": os.getenv("VERCEL"),
                "AWS_LAMBDA_FUNCTION_NAME": os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
            },
            "features": {
                "upload_enabled": UPLOAD_ENABLED,
                "settings_loaded": settings is not None
            }
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "error": "Test endpoint failed",
            "message": str(e),
            "environment": "vercel" if os.getenv("VERCEL") else "local"
        }

# Conditional upload endpoint
if UPLOAD_ENABLED:
    @app.post("/api/upload")
    async def upload_file():
        return {"message": "Upload functionality available"}
else:
    @app.post("/api/upload")
    async def upload_disabled():
        raise HTTPException(
            status_code=503,
            detail="File upload is disabled in serverless environment"
        )

# Error handlers
@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}")
    return {
        "error": "Internal server error",
        "message": str(exc),
        "environment": "vercel" if os.getenv("VERCEL") else "local"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)