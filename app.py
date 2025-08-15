#!/usr/bin/env python3
"""
Main app.py for Hugging Face Spaces deployment
Multi-Agent Code Generation System
"""

import os
import sys
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the backend application
from backend.core.app import app as backend_app

# Create the main Hugging Face compatible app
app = FastAPI(
    title="Multi-Agent Code Generator",
    description="AI-powered code generation with multiple specialized agents using CrewAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for Hugging Face Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check for frontend directory
frontend_dir = "frontend"
if not os.path.exists(frontend_dir):
    # Try alternative directories
    for alt_dir in ["public", "static", "frontend/pages"]:
        if os.path.exists(alt_dir):
            frontend_dir = alt_dir
            break

# Mount static files if frontend exists
if os.path.exists(frontend_dir):
    try:
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
        print(f"✅ Frontend mounted from: {frontend_dir}")
    except Exception as e:
        print(f"⚠️  Warning: Could not mount frontend: {e}")

# Mount the backend API under /api
app.mount("/api", backend_app)

@app.get("/")
async def root():
    """Root endpoint - serve frontend or API info"""
    # Try to serve the main HTML file
    for html_file in ["index.html", "front_optimized.html", "main.html"]:
        html_path = os.path.join(frontend_dir, html_file)
        if os.path.exists(html_path):
            return FileResponse(html_path)
    
    # If no frontend found, return API information
    return {
        "message": "🚀 Multi-Agent Code Generation System",
        "description": "AI-powered code generation with CrewAI agents",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "api": "/api/",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "generate": "/api/generate",
            "status": "/api/status/{job_id}",
            "download": "/api/download/{job_id}"
        },
        "features": [
            "Multi-agent code generation with CrewAI",
            "Support for multiple programming languages",
            "Real-time progress tracking",
            "Code execution and testing",
            "Persian/Farsi UI support"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Hugging Face"""
    return {
        "status": "healthy",
        "service": "Multi-Agent Code Generator",
        "version": "1.0.0",
        "timestamp": "now",
        "components": {
            "database": "SQLite (ready)",
            "cache": "Memory (ready)",
            "agents": "CrewAI (ready)",
            "frontend": "Available" if os.path.exists(frontend_dir) else "Not mounted"
        }
    }

@app.get("/info")
async def system_info():
    """System information endpoint"""
    return {
        "name": "Multi-Agent Code Generator",
        "version": "1.0.0",
        "platform": "Hugging Face Spaces",
        "features": {
            "database": "SQLite",
            "cache": "Memory-based",
            "ai_framework": "CrewAI",
            "agents": ["PlannerAgent", "CodeGeneratorAgent", "TesterAgent", "DocGeneratorAgent"],
            "languages": ["Python", "JavaScript", "TypeScript", "HTML", "CSS"],
            "frameworks": ["FastAPI", "React", "Vue", "Flask", "Django"]
        },
        "endpoints": {
            "frontend": "/",
            "api": "/api/",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    # Get port from environment (Hugging Face uses 7860)
    port = int(os.environ.get("PORT", 7860))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Starting Multi-Agent Code Generator on {host}:{port}")
    print(f"📁 Frontend directory: {frontend_dir}")
    print(f"🤖 Backend API: /api/")
    print(f"📚 API Documentation: /docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # Disable reload in production
        workers=1,     # Single worker for Hugging Face
        log_level="info"
    )