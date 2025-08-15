"""
Vercel-specific FastAPI application for serverless deployment.
Simplified version without database and Redis dependencies.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import structlog

from config.vercel_config import get_vercel_settings

settings = get_vercel_settings()

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

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Vercel Multi-Agent Code Generation System")
    
    try:
        logger.info("Application startup completed")
        yield
        
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A serverless multi-agent code generation system using CrewAI",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware setup
# Rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    try:
        response = await call_next(request)
        
        duration = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=duration,
        )
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            duration=duration,
        )
        raise

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": time.time(),
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured logging."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error" if not settings.debug else str(exc),
            "timestamp": time.time(),
            "status_code": 500
        }
    )

# Health check endpoints
@app.get("/health")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def health_check(request: Request):
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "service": settings.app_name,
        "deployment": "vercel"
    }

@app.get("/health/ready")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def readiness_check(request: Request):
    """Readiness check for serverless deployment."""
    return {
        "status": "ready",
        "timestamp": time.time(),
        "version": settings.app_version,
        "deployment": "vercel",
        "database": "disabled",
        "redis": "disabled"
    }

@app.get("/health/live")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def liveness_check(request: Request):
    """Liveness check for container orchestration."""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "version": settings.app_version,
        "deployment": "vercel"
    }

# Static files - serve the frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Root endpoint - serve the main frontend
@app.get("/")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def root(request: Request):
    """Root endpoint - serve the main frontend."""
    try:
        return FileResponse("frontend/pages/index.html")
    except FileNotFoundError:
        return {
            "message": "Multi-Agent Code Generation System",
            "version": settings.app_version,
            "docs_url": "/docs" if settings.debug else None,
            "frontend_url": "/static/pages/index.html",
            "status": "running",
            "deployment": "vercel"
        }

# System information endpoint
@app.get("/info")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def system_info(request: Request):
    """Get system information and configuration."""
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "deployment": "vercel"
        },
        "features": {
            "authentication": "JWT",
            "rate_limiting": True,
            "caching": "disabled",
            "database": "disabled",
            "agents": "CrewAI",
            "monitoring": "disabled",
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs" if settings.debug else None,
            "frontend": "/static/pages/index.html",
            "api": "/api/*",
        },
        "limits": {
            "max_file_size": f"{settings.max_file_size / (1024*1024):.1f}MB",
            "allowed_extensions": settings.allowed_extensions,
            "rate_limit": f"{settings.rate_limit_requests}/{settings.rate_limit_window}s",
        }
    }

# Development utilities
if settings.debug:
    @app.get("/debug/config")
    @limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
    async def debug_config(request: Request):
        """Debug endpoint to view current configuration (only in debug mode)."""
        config_dict = settings.dict()
        # Hide sensitive information
        sensitive_keys = ["jwt_secret_key", "openai_api_key"]
        for key in sensitive_keys:
            if key in config_dict:
                config_dict[key] = "***HIDDEN***"
        
        return config_dict
    
    @app.get("/debug/routes")
    @limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
    async def debug_routes(request: Request):
        """Debug endpoint to list all available routes."""
        routes = []
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": getattr(route, 'name', None)
                })
        return {"routes": routes}

# Custom startup message
@app.on_event("startup")
async def startup_message():
    """Log startup message with configuration info."""
    logger.info(
        "🚀 Vercel Multi-Agent Code Generation System Started",
        version=settings.app_version,
        debug=settings.debug,
        deployment="vercel",
        openai_configured=bool(settings.openai_api_key),
    )

# Basic code generation endpoint
@app.post("/api/generate")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def generate_code(request: Request):
    """Basic code generation endpoint for Vercel deployment."""
    try:
        # For now, return a simple response
        # In a full implementation, this would integrate with CrewAI
        return {
            "success": True,
            "message": "Code generation endpoint ready",
            "timestamp": time.time(),
            "deployment": "vercel",
            "note": "This is a simplified version for serverless deployment"
        }
    except Exception as e:
        logger.error("Code generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Code generation failed")

# API status endpoint
@app.get("/api/status")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}s")
async def api_status(request: Request):
    """API status endpoint."""
    return {
        "status": "operational",
        "timestamp": time.time(),
        "version": settings.app_version,
        "deployment": "vercel",
        "features": {
            "code_generation": "basic",
            "database": "disabled",
            "redis": "disabled",
            "rate_limiting": "enabled"
        }
    }