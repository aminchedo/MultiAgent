#!/usr/bin/env python3
"""
Vercel-optimized Multi-Agent Code Generation System
This version is specifically designed for Vercel serverless deployment.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Code Generation System",
    version="1.0.0",
    description="A Vercel-optimized multi-agent code generation system",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if they exist
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve the main frontend."""
    try:
        # Try to serve the optimized frontend
        if os.path.exists("frontend/pages/front_optimized.html"):
            return FileResponse("frontend/pages/front_optimized.html")
        elif os.path.exists("frontend/pages/index.html"):
            return FileResponse("frontend/pages/index.html")
        else:
            # Fallback HTML
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Multi-Agent Code Generation System</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #333; text-align: center; }
                    .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
                    .endpoints { background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
                    .endpoint { margin: 10px 0; padding: 10px; background: #f9f9f9; border-left: 4px solid #007bff; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 Multi-Agent Code Generation System</h1>
                    <div class="status">
                        <strong>Status:</strong> ✅ Running on Vercel
                    </div>
                    <div class="endpoints">
                        <h3>Available Endpoints:</h3>
                        <div class="endpoint">
                            <strong>Health Check:</strong> <a href="/health">/health</a>
                        </div>
                        <div class="endpoint">
                            <strong>API Documentation:</strong> <a href="/docs">/docs</a>
                        </div>
                        <div class="endpoint">
                            <strong>System Info:</strong> <a href="/info">/info</a>
                        </div>
                        <div class="endpoint">
                            <strong>Test API:</strong> <a href="/api/test">/api/test</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error("Error serving frontend", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to serve frontend", "details": str(e)}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Multi-Agent Code Generation System is running",
        "version": "1.0.0",
        "deployment": "vercel",
        "database": "disabled (simplified mode)",
        "redis": "disabled (simplified mode)"
    }

@app.get("/health/ready")
async def health_ready():
    """Readiness check endpoint."""
    return {"status": "ready", "deployment": "vercel"}

@app.get("/health/live")
async def health_live():
    """Liveness check endpoint."""
    return {"status": "alive", "deployment": "vercel"}

@app.get("/info")
async def system_info():
    """Get system information."""
    return {
        "application": {
            "name": "Multi-Agent Code Generation System",
            "version": "1.0.0",
            "deployment": "vercel"
        },
        "features": {
            "database": "disabled (simplified mode)",
            "redis": "disabled (simplified mode)",
            "agents": "CrewAI (simplified)",
            "frontend": "static files"
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "frontend": "/",
            "api": "/api/*"
        }
    }

@app.get("/api/test")
async def test_api():
    """Test API endpoint."""
    return {
        "message": "API is working!",
        "status": "success",
        "deployment": "vercel"
    }

@app.post("/api/generate")
async def generate_code(request: Request):
    """Basic code generation endpoint for Vercel deployment."""
    try:
        # For Vercel deployment, we'll return a simplified response
        # In a full implementation, this would integrate with CrewAI agents
        return {
            "message": "Code generation endpoint",
            "status": "available",
            "deployment": "vercel",
            "note": "This is a simplified version for Vercel deployment"
        }
    except Exception as e:
        logger.error("Error in code generation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{job_id}")
async def download_code(job_id: str):
    """Download generated code (simplified for Vercel)."""
    return {
        "message": "Download endpoint",
        "job_id": job_id,
        "status": "available",
        "deployment": "vercel",
        "note": "This is a simplified version for Vercel deployment"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": "The requested resource was not found",
            "available_endpoints": [
                "/",
                "/health",
                "/info",
                "/api/test",
                "/docs"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    logger.error("Internal server error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "deployment": "vercel"
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(
        "🚀 Vercel Multi-Agent Code Generation System Started",
        version="1.0.0",
        deployment="vercel"
    )

if __name__ == "__main__":
    logger.info("🚀 Starting Vercel Multi-Agent Code Generation System...")
    logger.info("🌐 Server will be available at: http://localhost:8000")
    logger.info("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "api.vercel_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )