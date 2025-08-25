#!/usr/bin/env python3
"""
Simplified Multi-Agent Code Generation System - No Database Required
This version runs without PostgreSQL or Redis for immediate testing.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
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

# Create FastAPI application
app = FastAPI(
    title="Multi-Agent Code Generation System",
    version="1.0.0",
    description="A simplified multi-agent code generation system",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("frontend/pages"):
    app.mount("/static", StaticFiles(directory="frontend/pages"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page."""
    try:
        with open("frontend/pages/front_optimized.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Multi-Agent Code Generation System</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>🤖 Multi-Agent Code Generation System</h1>
            <p>✅ Backend is running successfully!</p>
            <p>📁 Frontend files not found. Please check the frontend/pages directory.</p>
            <p>📚 <a href="/docs">API Documentation</a></p>
            <p>🔍 <a href="/health">Health Check</a></p>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Multi-Agent Code Generation System is running",
        "version": "1.0.0",
        "database": "disabled (simplified mode)",
        "redis": "disabled (simplified mode)"
    }

@app.get("/health/ready")
async def health_ready():
    """Readiness check endpoint."""
    return {"status": "ready"}

@app.get("/health/live")
async def health_live():
    """Liveness check endpoint."""
    return {"status": "alive"}

@app.get("/info")
async def info():
    """System information endpoint."""
    return {
        "name": "Multi-Agent Code Generation System",
        "version": "1.0.0",
        "description": "A simplified multi-agent code generation system",
        "mode": "simplified (no database)",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "frontend": "/"
        }
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for API functionality."""
    return {
        "message": "API is working!",
        "status": "success",
        "timestamp": "2025-08-15T05:30:00Z"
    }

@app.post("/api/generate")
async def generate_code(request: Request):
    """Simplified code generation endpoint."""
    try:
        data = await request.json()
        project_description = data.get("description", "Simple calculator")
        
        # Simulate code generation
        return {
            "status": "success",
            "message": "Code generation completed (simplified mode)",
            "job_id": "simplified-job-123",
            "project_description": project_description,
            "files_generated": [
                "index.html",
                "style.css", 
                "script.js",
                "README.md"
            ],
            "download_url": "/api/download/simplified-job-123"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/download/{job_id}")
async def download_project(job_id: str):
    """Simplified download endpoint."""
    return {
        "status": "success",
        "message": "Download ready (simplified mode)",
        "job_id": job_id,
        "files": [
            "index.html",
            "style.css",
            "script.js", 
            "README.md"
        ]
    }

if __name__ == "__main__":
    logger.info("🚀 Starting Simplified Multi-Agent Code Generation System...")
    logger.info("📝 Mode: Simplified (no database required)")
    logger.info("🌐 Server will be available at: http://localhost:8000")
    logger.info("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "simple_run:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )