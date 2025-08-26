"""
API routes module with JWT authentication, rate limiting, and comprehensive endpoints.
"""

import asyncio
import base64
import io
import json
import os
import zipfile
import tempfile
import subprocess
import psutil
import uuid
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile, File, 
    BackgroundTasks, Query, Request, WebSocket, WebSocketDisconnect
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from config.config import get_settings
from backend.models.models import (
    ProjectGenerationRequest, ProjectGenerationResponse,
    JobStatusResponse, FilePreviewResponse, CodeExecutionRequest,
    CodeExecutionResponse, SystemStatsResponse, AuthRequest,
    AuthResponse, TemplateResponse, JobListResponse, BaseResponse,
    WebSocketMessage, MessageType, JobStatus, generate_job_id
)
from backend.database.db import db_manager
from backend.agents.agents import create_and_execute_workflow
from backend.agents.specialized.vibe_workflow_orchestrator import create_and_execute_enhanced_workflow

# Simple get_current_user function for vibe endpoints
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple user validation for vibe endpoints."""
    try:
        return verify_token(credentials)
    except HTTPException:
        # For development, allow anonymous access to vibe endpoints
        return None


settings = get_settings()
logger = structlog.get_logger()

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Router setup
router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str = None):
        await websocket.accept()
        connection_id = job_id or f"conn_{len(self.active_connections)}"
        self.active_connections[connection_id] = websocket
        return connection_id
    
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
    
    async def send_message(self, message: Dict, connection_id: str = None):
        if connection_id and connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except:
                self.disconnect(connection_id)
        else:
            # Broadcast to all connections
            disconnected = []
            for conn_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.append(conn_id)
            
            for conn_id in disconnected:
                self.disconnect(conn_id)

manager = ConnectionManager()


# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            # Simple database check
            await db_manager.get_job("test")
        except:
            db_status = "degraded"
        
        return {
            "status": "healthy",
            "service": "multi-agent-code-generation",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": db_status,
                "openai": "healthy" if settings.openai_api_key else "unconfigured",
                "redis": "healthy"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Authentication endpoints
@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, auth_request: AuthRequest):
    """Authenticate user and return JWT tokens."""
    # Simple authentication - in production, verify against database
    if auth_request.username == "admin" and auth_request.password == "admin":
        access_token_expires = timedelta(minutes=settings.jwt_expire_minutes)
        access_token = create_access_token(
            data={"sub": auth_request.username}, expires_delta=access_token_expires
        )
        refresh_token = create_access_token(
            data={"sub": auth_request.username, "type": "refresh"}, 
            expires_delta=timedelta(days=7)
        )
        
        return AuthResponse(
            success=True,
            message="Authentication successful",
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_expire_minutes * 60
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )


@router.get("/api/templates", response_model=TemplateResponse)
@limiter.limit("30/minute")
async def get_templates(request: Request):
    """Get available project templates."""
    templates = [
        {
            "id": "react-app",
            "name": "React Application",
            "description": "Modern React app with TypeScript and Tailwind CSS",
            "category": "frontend",
            "complexity": "moderate",
            "features": ["authentication", "routing", "state-management", "styling"],
            "languages": ["typescript", "javascript"],
            "frameworks": ["react", "next.js", "tailwind"]
        },
        {
            "id": "fastapi-backend",
            "name": "FastAPI Backend",
            "description": "Python FastAPI backend with database and authentication",
            "category": "backend",
            "complexity": "moderate",
            "features": ["authentication", "database", "api", "documentation"],
            "languages": ["python"],
            "frameworks": ["fastapi", "sqlalchemy", "pydantic"]
        },
        {
            "id": "fullstack-app",
            "name": "Full-Stack Application",
            "description": "Complete full-stack application with frontend and backend",
            "category": "fullstack",
            "complexity": "complex",
            "features": ["authentication", "database", "api", "frontend", "deployment"],
            "languages": ["python", "typescript", "javascript"],
            "frameworks": ["fastapi", "react", "next.js", "sqlalchemy"]
        }
    ]
    
    return TemplateResponse(
        success=True,
        message="Templates retrieved successfully",
        templates=templates
    )


@router.post("/api/validate-key")
async def validate_api_key(request: Request, api_key_data: dict):
    """Convert API key to JWT token for frontend compatibility"""
    api_key = api_key_data.get("api_key")
    if api_key == os.getenv("API_KEY_SECRET", "default-dev-key"):
        # Generate short-lived JWT
        token = create_access_token(data={"sub": "api_user"})
        return {"valid": True, "token": token}
    raise HTTPException(status_code=401, detail="Invalid API key")


# Project generation endpoints
@router.post("/api/jobs", response_model=ProjectGenerationResponse)
@limiter.limit("5/minute")
async def create_job(
    request: Request,
    project_request: ProjectGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(verify_token)
):
    """Create a new project generation job (alias for /api/generate)."""
    return await generate_project(request, project_request, background_tasks, current_user)


@router.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
@limiter.limit("30/minute")
async def get_job_status_alias(
    request: Request,
    job_id: str,
    current_user: str = Depends(verify_token)
):
    """Get job status (alias for /api/status/{job_id})."""
    return await get_job_status(request, job_id, current_user)


@router.post("/api/vibe-coding", response_model=ProjectGenerationResponse)
@limiter.limit("5/minute")
async def create_vibe_project(
    request: Request,
    background_tasks: BackgroundTasks,
    vibe_prompt: str,
    project_type: str = "web",
    complexity: str = "simple",
    framework: Optional[str] = None,
    styling: Optional[str] = None,
    current_user: str = Depends(verify_token)
):
    """Create a project from a natural language vibe description using the enhanced workflow."""
    job_id = generate_job_id()
    
    try:
        # Create job in database with vibe-specific data
        await db_manager.create_job(
            job_id=job_id,
            name=f"Vibe Project: {vibe_prompt[:50]}...",
            description=vibe_prompt,
            project_type=project_type,
            languages=["javascript", "css", "html"] if project_type == "web" else ["python"],
            frameworks=[framework] if framework else ["react"],
            complexity=complexity,
            features=["vibe_based_generation"],
            mode="vibe"
        )
        
        # Estimate duration based on complexity for vibe projects
        duration_map = {
            "simple": 90,      # 1.5 minutes for vibe projects
            "moderate": 240,   # 4 minutes
            "complex": 420     # 7 minutes
        }
        estimated_duration = duration_map.get(complexity, 240)
        
        # Prepare vibe project data
        vibe_project_data = {
            "vibe_prompt": vibe_prompt,
            "prompt": vibe_prompt,  # For compatibility
            "description": vibe_prompt,
            "project_type": project_type,
            "complexity": complexity,
            "framework": framework,
            "styling": styling,
            "mode": "vibe",
            "vibe_based": True
        }
        
        # Start background task for vibe project generation
        background_tasks.add_task(
            execute_project_generation,
            job_id,
            vibe_project_data
        )
        
        logger.info("Vibe project generation started", job_id=job_id, user=current_user, vibe=vibe_prompt[:100])
        
        return ProjectGenerationResponse(
            success=True,
            message="🚀 Your vibe project is being created! Watch 5 AI agents collaborate to bring your vision to life.",
            job_id=job_id,
            estimated_duration=estimated_duration
        )
        
    except Exception as e:
        logger.error("Failed to start vibe project generation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start vibe project generation: {str(e)}"
        )


@router.post("/api/generate", response_model=ProjectGenerationResponse)
@limiter.limit("5/minute")
async def generate_project(
    request: Request,
    project_request: ProjectGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(verify_token)
):
    """Generate a new project using multi-agent workflow."""
    job_id = generate_job_id()
    
    try:
        # Create job in database
        await db_manager.create_job(
            job_id=job_id,
            name=project_request.name,
            description=project_request.description,
            project_type=project_request.project_type,
            languages=project_request.languages,
            frameworks=project_request.frameworks,
            complexity=project_request.complexity,
            features=project_request.features,
            mode=project_request.mode
        )
        
        # Estimate duration based on complexity
        duration_map = {
            "simple": 60,      # 1 minute
            "moderate": 180,   # 3 minutes
            "complex": 300,    # 5 minutes
            "enterprise": 600  # 10 minutes
        }
        estimated_duration = duration_map.get(project_request.complexity, 180)
        
        # Start background task for project generation
        background_tasks.add_task(
            execute_project_generation,
            job_id,
            project_request.dict()
        )
        
        logger.info("Project generation started", job_id=job_id, user=current_user)
        
        return ProjectGenerationResponse(
            success=True,
            message="Project generation started successfully",
            job_id=job_id,
            estimated_duration=estimated_duration
        )
        
    except Exception as e:
        logger.error("Failed to start project generation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start project generation: {str(e)}"
        )


async def execute_project_generation(job_id: str, project_data: Dict[str, Any]):
    """Background task to execute project generation workflow."""
    try:
        # Create WebSocket callback for real-time updates
        async def websocket_callback(message: Dict):
            await manager.send_message(message, job_id)
        
        # Execute the enhanced multi-agent workflow (supports both traditional and vibe-based requests)
        result = await create_and_execute_enhanced_workflow(
            job_id=job_id,
            project_data=project_data,
            websocket_callback=websocket_callback
        )
        
        logger.info("Project generation completed", job_id=job_id, files=result.get('total_files', 0))
        
    except Exception as e:
        logger.error("Project generation failed", job_id=job_id, error=str(e))
        await db_manager.update_job_status(
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message=str(e)
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
@limiter.limit("30/minute")
async def get_job_status(
    request: Request,
    job_id: str,
    current_user: str = Depends(verify_token)
):
    """Get the status of a project generation job."""
    job = await db_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get file list
    files = await db_manager.get_files(job_id)
    file_list = [f.path for f in files]
    
    return JobStatusResponse(
        success=True,
        message="Job status retrieved successfully",
        job_id=job_id,
        status=JobStatus(job.status),
        progress=job.progress,
        current_step=job.current_step,
        step_number=job.step_number,
        total_steps=job.total_steps,
        files=file_list,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        estimated_completion=job.completed_at
    )


@router.get("/api/status/{job_id}", response_model=JobStatusResponse)
@limiter.limit("30/minute")
async def get_job_status_api(
    request: Request,
    job_id: str,
    current_user: str = Depends(verify_token)
):
    """Alias for /status/{job_id} to match frontend expectations"""
    return await get_job_status(request, job_id, current_user)


@router.get("/download/{job_id}")
@limiter.limit("10/minute")
async def download_project(
    request: Request,
    job_id: str,
    current_user: str = Depends(verify_token)
):
    """Download the generated project as a ZIP file."""
    job = await db_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not completed yet"
        )
    
    # Get all files for the job
    files = await db_manager.get_files(job_id)
    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No files found for this job"
        )
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_model in files:
            zip_file.writestr(file_model.path, file_model.content)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={job.name}.zip"}
    )


@router.get("/api/stats", response_model=SystemStatsResponse)
@limiter.limit("10/minute")
async def get_system_stats(
    request: Request,
    current_user: str = Depends(verify_token)
):
    """Get system statistics and performance metrics."""
    try:
        # Get basic system stats
        import psutil
        
        # Get job statistics
        total_jobs = await db_manager.get_job_count()
        completed_jobs = await db_manager.get_completed_job_count()
        failed_jobs = await db_manager.get_failed_job_count()
        
        # Get system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemStatsResponse(
            success=True,
            message="System stats retrieved successfully",
            stats={
                "jobs": {
                    "total": total_jobs,
                    "completed": completed_jobs,
                    "failed": failed_jobs,
                    "success_rate": (completed_jobs / max(total_jobs, 1)) * 100
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "uptime": time.time() - psutil.boot_time()
                },
                "agents": {
                    "active": len([conn for conn in manager.active_connections.values()]),
                    "total_agents": 5  # Planner, Coder, Tester, Doc Writer, Reviewer
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


@router.get("/api/download/{job_id}")
@limiter.limit("10/minute")
async def download_project_api(
    request: Request,
    job_id: str,
    current_user: str = Depends(verify_token)
):
    """Alias for /download/{job_id}"""
    return await download_project(request, job_id, current_user)


@router.get("/preview/{job_id}/{filename:path}", response_model=FilePreviewResponse)
@limiter.limit("50/minute")
async def preview_file(
    request: Request,
    job_id: str,
    filename: str,
    current_user: str = Depends(verify_token)
):
    """Preview a specific file from the generated project."""
    file_model = await db_manager.get_file(job_id, filename)
    if not file_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FilePreviewResponse(
        success=True,
        message="File retrieved successfully",
        filename=file_model.filename,
        content=file_model.content,
        language=file_model.language,
        size=file_model.size
    )


# Code execution endpoint
@router.post("/api/execute", response_model=CodeExecutionResponse)
@limiter.limit("20/minute")
async def execute_code(
    request: Request,
    execution_request: CodeExecutionRequest,
    current_user: str = Depends(verify_token)
):
    """Execute code in a sandboxed environment."""
    try:
        start_time = datetime.utcnow()
        
        if execution_request.language.lower() == "python":
            # Execute Python code - Use Vercel-safe temp file
            from backend.utils.vercel_utils import create_temp_file_vercel_safe
            temp_file = create_temp_file_vercel_safe(suffix='.py', prefix='temp_code_')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(execution_request.code)
            
            try:
                result = subprocess.run(
                    ["python", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=execution_request.timeout
                )
                output = result.stdout
                error = result.stderr if result.returncode != 0 else None
                exit_code = result.returncode
            finally:
                os.unlink(temp_file)
        
        elif execution_request.language.lower() == "javascript":
            # Execute JavaScript with Node.js
            result = subprocess.run(
                ["node", "-e", execution_request.code],
                capture_output=True,
                text=True,
                timeout=execution_request.timeout
            )
            output = result.stdout
            error = result.stderr if result.returncode != 0 else None
            exit_code = result.returncode
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language: {execution_request.language}"
            )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return CodeExecutionResponse(
            success=True,
            message="Code executed successfully",
            output=output or "",
            error=error,
            execution_time=execution_time,
            exit_code=exit_code
        )
        
    except subprocess.TimeoutExpired:
        return CodeExecutionResponse(
            success=False,
            message="Code execution timed out",
            output="",
            error="Execution timed out",
            execution_time=execution_request.timeout,
            exit_code=-1
        )
    except Exception as e:
        return CodeExecutionResponse(
            success=False,
            message="Code execution failed",
            output="",
            error=str(e),
            execution_time=0,
            exit_code=-1
        )


# File upload endpoint
@router.post("/api/upload", response_model=BaseResponse)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    job_id: str = Query(...),
    path: Optional[str] = Query(None),
    current_user: str = Depends(verify_token)
):
    """Upload a file to modify an existing project."""
    # Verify job exists
    job = await db_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed"
        )
    
    # Determine file path
    file_path = path or file.filename
    
    # Detect language
    language_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.jsx': 'javascript', '.tsx': 'typescript', '.html': 'html',
        '.css': 'css', '.json': 'json', '.md': 'markdown'
    }
    language = language_map.get(file_ext, 'text')
    
    try:
        # Save file to database
        await db_manager.create_file(
            job_id=job_id,
            filename=file.filename,
            path=file_path,
            content=content.decode('utf-8'),
            language=language
        )
        
        return BaseResponse(
            success=True,
            message=f"File {file.filename} uploaded successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


# Templates endpoint
@router.get("/api/templates", response_model=TemplateResponse)
@limiter.limit("30/minute")
async def get_templates(
    request: Request,
    current_user: str = Depends(verify_token)
):
    """Get available project templates."""
    templates = [
        {
            "id": "react_app",
            "name": "React Web Application",
            "description": "Modern React application with TypeScript",
            "languages": ["typescript", "javascript"],
            "frameworks": ["react", "vite"],
            "complexity": "moderate"
        },
        {
            "id": "fastapi_service",
            "name": "FastAPI Microservice",
            "description": "RESTful API service with FastAPI and PostgreSQL",
            "languages": ["python"],
            "frameworks": ["fastapi", "sqlalchemy"],
            "complexity": "moderate"
        },
        {
            "id": "fullstack_app",
            "name": "Full-Stack Application",
            "description": "Complete web application with React frontend and Python backend",
            "languages": ["python", "typescript"],
            "frameworks": ["fastapi", "react", "postgresql"],
            "complexity": "complex"
        },
        {
            "id": "cli_tool",
            "name": "Command Line Tool",
            "description": "Python CLI application with argument parsing",
            "languages": ["python"],
            "frameworks": ["click", "typer"],
            "complexity": "simple"
        },
        {
            "id": "mobile_app",
            "name": "React Native Mobile App",
            "description": "Cross-platform mobile application",
            "languages": ["typescript", "javascript"],
            "frameworks": ["react-native", "expo"],
            "complexity": "complex"
        }
    ]
    
    return TemplateResponse(
        success=True,
        message="Templates retrieved successfully",
        templates=templates
    )


# System statistics endpoint
@router.get("/api/stats", response_model=SystemStatsResponse)
@limiter.limit("60/minute")
async def get_system_stats(
    request: Request,
    current_user: str = Depends(verify_token)
):
    """Get system statistics and metrics."""
    try:
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get database statistics
        db_stats = await db_manager.get_system_stats()
        
        # Calculate uptime (simplified)
        uptime = 86400  # 24 hours in seconds (placeholder)
        
        return SystemStatsResponse(
            success=True,
            message="System statistics retrieved successfully",
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            active_jobs=db_stats.get('active_jobs', 0),
            total_jobs=db_stats.get('total_jobs', 0),
            avg_response_time=150.0,  # Placeholder
            uptime=uptime
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system statistics: {str(e)}"
        )


# Admin endpoints
@router.get("/admin/jobs", response_model=JobListResponse)
@limiter.limit("30/minute")
async def get_recent_jobs(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    status: Optional[JobStatus] = Query(None),
    current_user: str = Depends(verify_token)
):
    """Get recent jobs with pagination."""
    offset = (page - 1) * per_page
    jobs = await db_manager.get_jobs(
        limit=per_page,
        offset=offset,
        status=status
    )
    
    job_summaries = []
    for job in jobs:
        duration = None
        if job.completed_at and job.created_at:
            duration = (job.completed_at - job.created_at).total_seconds()
        
        job_summaries.append({
            "job_id": job.job_id,
            "name": job.name,
            "status": job.status,
            "project_type": job.project_type,
            "languages": job.languages,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "duration": duration
        })
    
    return JobListResponse(
        success=True,
        message="Jobs retrieved successfully",
        jobs=job_summaries,
        total=len(job_summaries),
        page=page,
        per_page=per_page
    )


# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, job_id: Optional[str] = None):
    """WebSocket endpoint for real-time updates."""
    connection_id = await manager.connect(websocket, job_id)
    
    try:
        # Send welcome message
        welcome_message = WebSocketMessage(
            type=MessageType.STATUS,
            content="Connected to Multi-Agent Code Generation System",
            job_id=job_id
        )
        await websocket.send_text(json.dumps(welcome_message.dict()))
        
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back or handle specific message types
            if message.get("type") == "ping":
                pong_message = WebSocketMessage(
                    type=MessageType.STATUS,
                    content="pong",
                    job_id=job_id
                )
                await websocket.send_text(json.dumps(pong_message.dict()))
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)


# Vibe Coding Endpoints
@router.post("/api/vibe-coding")
@limiter.limit("3/minute")
async def vibe_coding_endpoint(
    request: Request,
    vibe_request: Dict[str, Any],
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Vibe Coding endpoint - Generate projects using vibe prompt analysis.
    
    This endpoint orchestrates the entire vibe workflow:
    1. VibePlannerAgent - Analyzes vibe prompt
    2. VibeCoderAgent - Generates code
    3. VibeCriticAgent - Reviews quality
    4. VibeFileManagerAgent - Organizes files
    """
    try:
        # Import vibe agents
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
        
        # Validate request
        if not vibe_request.get('vibe_prompt'):
            raise HTTPException(
                status_code=400,
                detail="vibe_prompt is required"
            )
        
        # Initialize orchestrator
        orchestrator = VibeWorkflowOrchestratorAgent()
        
        # Execute vibe workflow
        logger.info(f"🚀 Starting vibe coding workflow for: {vibe_request['vibe_prompt'][:50]}...")
        workflow_result = orchestrator.orchestrate_vibe_project(vibe_request)
        
        # Return result
        return {
            "success": workflow_result.get('workflow_status') == 'completed',
            "workflow_id": workflow_result.get('workflow_id'),
            "project_id": workflow_result.get('project_id'),
            "workflow_status": workflow_result.get('workflow_status'),
            "progress": workflow_result.get('progress', {}),
            "project_data": workflow_result.get('project_data', {}),
            "summary": workflow_result.get('summary', {}),
            "error_log": workflow_result.get('error_log', []),
            "timing": workflow_result.get('timing', {}),
            "agent_results": {
                agent: {
                    "success": result.get('success', False),
                    "agent": result.get('agent', agent)
                } for agent, result in workflow_result.get('agent_results', {}).items()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Vibe coding workflow failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Vibe coding workflow failed: {str(e)}"
        )


@router.get("/api/vibe-projects/{project_id}")
@limiter.limit("30/minute")
async def get_vibe_project(
    request: Request,
    project_id: int,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Get vibe project details by ID."""
    try:
        # Import database utilities
        import sqlite3
        import json
        
        conn = sqlite3.connect("backend/vibe_projects.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, vibe_prompt, project_type, status, created_at, completed_at, project_files, error_message
            FROM vibe_projects 
            WHERE id = ?
        """, (project_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Vibe project not found")
        
        return {
            "id": result[0],
            "vibe_prompt": result[1],
            "project_type": result[2],
            "status": result[3],
            "created_at": result[4],
            "completed_at": result[5],
            "project_files": json.loads(result[6]) if result[6] else {},
            "error_message": result[7]
        }
        
    except Exception as e:
        logger.error(f"Failed to get vibe project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/vibe-metrics")
@limiter.limit("10/minute")
async def get_vibe_metrics(
    request: Request,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Get vibe agents metrics and performance data."""
    try:
        # Import orchestrator to get agent metrics
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
        
        orchestrator = VibeWorkflowOrchestratorAgent()
        agent_metrics = orchestrator.get_agent_metrics()
        
        # Get database metrics
        import sqlite3
        conn = sqlite3.connect("backend/vibe_projects.db")
        cursor = conn.cursor()
        
        # Get project statistics
        cursor.execute("SELECT COUNT(*) FROM vibe_projects")
        total_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vibe_projects WHERE status = 'completed'")
        completed_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vibe_projects WHERE status = 'failed'")
        failed_projects = cursor.fetchone()[0]
        
        # Get agent operation statistics
        cursor.execute("""
            SELECT agent_name, COUNT(*) as operations, 
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_operations,
                   AVG(response_time) as avg_response_time
            FROM agent_metrics 
            GROUP BY agent_name
        """)
        agent_stats = cursor.fetchall()
        
        conn.close()
        
        # Calculate success rate
        success_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
        
        return {
            "vibe_platform_metrics": {
                "total_projects": total_projects,
                "completed_projects": completed_projects,
                "failed_projects": failed_projects,
                "success_rate": round(success_rate, 2)
            },
            "agent_metrics": agent_metrics,
            "agent_statistics": [
                {
                    "agent_name": stat[0],
                    "total_operations": stat[1],
                    "successful_operations": stat[2],
                    "success_rate": round((stat[2] / stat[1] * 100) if stat[1] > 0 else 0, 2),
                    "avg_response_time": round(stat[3], 3) if stat[3] else 0
                } for stat in agent_stats
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get vibe metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))