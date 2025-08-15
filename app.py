"""
Main FastAPI application for the Multi-Agent Code Generation System.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import structlog
from prometheus_fastapi_instrumentator import Instrumentator

from config import get_settings
from routes import router, limiter
from db import db_manager


settings = get_settings()

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


# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Multi-Agent Code Generation System")
    
    try:
        # Initialize database
        await db_manager.initialize()
        logger.info("Database initialized successfully")
        
        # Initialize Prometheus metrics if enabled
        if settings.enable_prometheus:
            instrumentator = Instrumentator()
            instrumentator.instrument(app).expose(app, endpoint=settings.metrics_endpoint)
            logger.info("Prometheus metrics enabled", endpoint=settings.metrics_endpoint)
        
        logger.info("Application startup completed")
        
        yield
        
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down application")
        await db_manager.close()
        logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A production-ready multi-agent code generation system using CrewAI",
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

# Trusted hosts middleware (security)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
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
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    try:
        response = await call_next(request)
        
        # Log response
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
        # Log errors
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
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "service": settings.app_name
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check with database connectivity."""
    try:
        # Check database connectivity
        stats = await db_manager.get_system_stats()
        
        return {
            "status": "ready",
            "timestamp": time.time(),
            "version": settings.app_version,
            "database": "connected",
            "total_jobs": stats.get("total_jobs", 0)
        }
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Service not ready - database connection failed"
        )


@app.get("/health/live")
async def liveness_check():
    """Liveness check for container orchestration."""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "version": settings.app_version
    }


# Include API routes
app.include_router(router)


# Static files - serve the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


# Root endpoint - redirect to frontend
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "Multi-Agent Code Generation System",
        "version": settings.app_version,
        "docs_url": "/docs" if settings.debug else None,
        "frontend_url": "/static/index.html",
        "websocket_url": "/ws",
        "status": "running"
    }


# System information endpoint
@app.get("/info")
async def system_info():
    """Get system information and configuration."""
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
        },
        "features": {
            "authentication": "JWT",
            "rate_limiting": True,
            "caching": "Redis",
            "database": "PostgreSQL",
            "agents": "CrewAI",
            "monitoring": "Prometheus" if settings.enable_prometheus else None,
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs" if settings.debug else None,
            "frontend": "/static/index.html",
            "websocket": "/ws",
            "api": "/api/*",
            "auth": "/auth/login",
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
    async def debug_config():
        """Debug endpoint to view current configuration (only in debug mode)."""
        config_dict = settings.dict()
        # Hide sensitive information
        sensitive_keys = ["jwt_secret_key", "openai_api_key", "database_url"]
        for key in sensitive_keys:
            if key in config_dict:
                config_dict[key] = "***HIDDEN***"
        
        return config_dict
    
    @app.get("/debug/routes")
    async def debug_routes():
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
        "🚀 Multi-Agent Code Generation System Started",
        version=settings.app_version,
        debug=settings.debug,
        host=settings.host,
        port=settings.port,
        database_url=settings.database_url.split('@')[0] + "@***",  # Hide credentials
        openai_configured=bool(settings.openai_api_key),
        prometheus_enabled=settings.enable_prometheus,
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
        log_level="info" if not settings.debug else "debug",
        access_log=True,
    )