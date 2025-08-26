"""
Production-Ready Multi-Agent Code Generation Backend
Enhanced FastAPI application with real-time WebSocket support and agent coordination
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import asyncio
import uuid
import os
import zipfile
import tempfile
import time
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog
from pydantic import BaseModel, Field
import aiofiles
from datetime import datetime, timedelta
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our modules
from config.config import settings
from api.websocket_handler import ConnectionManager, MessageType, AgentStatus
connection_manager = ConnectionManager()
from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Pydantic models for request/response
class ProjectRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000, description="Project description")
    project_type: str = Field(default="web", description="Project type")
    framework: str = Field(default="react", description="Frontend framework")
    complexity: str = Field(default="simple", description="Project complexity: simple, intermediate, complex")
    features: List[str] = Field(default=[], description="Additional features to include")
    user_id: Optional[str] = Field(None, description="User identifier")

class ProjectResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None
    websocket_url: str

class ProjectStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    current_phase: str
    agents: Dict[str, Any]
    files_generated: int
    created_at: float
    updated_at: float
    estimated_completion: Optional[float] = None
    error_message: Optional[str] = None

class FileItem(BaseModel):
    path: str
    content: str
    language: str
    size: int

class ProjectFiles(BaseModel):
    job_id: str
    files: List[FileItem]
    total_files: int
    total_size: int

# Global state management
active_jobs: Dict[str, Dict[str, Any]] = {}
generated_projects: Dict[str, Dict[str, Any]] = {}
orchestrator_agent = None

# Enhanced progress callback for 6-agent orchestrator
async def orchestrator_progress_callback(job_id: str, agent_name: str, status: str, 
                                       progress: float, current_task: str, 
                                       details: Optional[Dict] = None):
    """Enhanced callback function to receive progress updates from 6-agent orchestrator."""
    try:
        # Update job status in memory for 6-agent system
        if job_id in active_jobs:
            active_jobs[job_id]["agents"][agent_name] = {
                "status": status,
                "progress": progress,
                "current_task": current_task,
                "details": details or {}
            }
            active_jobs[job_id]["updated_at"] = time.time()
            
            # Calculate overall progress across all 6 agents
            agent_progresses = [agent["progress"] for agent in active_jobs[job_id]["agents"].values()]
            overall_progress = sum(agent_progresses) / len(agent_progresses) if agent_progresses else 0
            active_jobs[job_id]["progress"] = overall_progress
            active_jobs[job_id]["current_phase"] = current_task
        
        # Send enhanced WebSocket update with agent-specific progress
        await connection_manager.broadcast_agent_progress(
            agent_name, job_id, status, int(progress), current_task, details
        )
        
        # Special handling for QA Validator updates
        if agent_name == "qa_validator" and details and details.get("qa_metrics"):
            await connection_manager.update_qa_metrics(job_id, details["qa_metrics"])
        
        # Update overall workflow status if this is a major milestone
        if status in ["completed", "failed"]:
            workflow_status = "completed" if status == "completed" else "failed"
            agent_statuses = {name: agent["status"] for name, agent in active_jobs[job_id]["agents"].items()}
            await connection_manager.broadcast_workflow_status(job_id, workflow_status, agent_statuses)
            
    except Exception as e:
        logger.error(f"Failed to process 6-agent orchestrator progress callback: {e}")

# Security
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional authentication - for future implementation"""
    return None

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Code Generation System",
    version="1.0.0",
    description="Production-ready multi-agent code generation platform with real-time monitoring",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.vercel.app", "localhost", "127.0.0.1"]
    )

# Initialize orchestrator on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global orchestrator_agent
    
    try:
        logger.info("🚀 Starting Multi-Agent Code Generation System")
        
        # Initialize orchestrator agent with progress callback
        orchestrator_agent = VibeWorkflowOrchestratorAgent(
            progress_callback=orchestrator_progress_callback
        )
        logger.info("✅ Orchestrator agent initialized with WebSocket integration")
        
        # Create necessary directories
        os.makedirs(settings.output_dir, exist_ok=True)
        os.makedirs(settings.temp_dir, exist_ok=True)
        
        logger.info("🎯 System ready for code generation")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🔄 Shutting down Multi-Agent Code Generation System")
    
    # Cancel all active jobs
    for job_id in list(active_jobs.keys()):
        active_jobs[job_id]["status"] = "cancelled"
    
    # Cleanup temp files if enabled
    if settings.cleanup_temp_files:
        try:
            import shutil
            if os.path.exists(settings.temp_dir):
                shutil.rmtree(settings.temp_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.environment,
        "active_jobs": len(active_jobs),
        "agents_ready": orchestrator_agent is not None
    }

# Main project generation endpoint
@app.post("/api/vibe-coding", response_model=ProjectResponse, tags=["Generation"])
async def create_project(
    request: ProjectRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Create a new project with real-time monitoring"""
    try:
        # Validate request
        if request.framework not in settings.supported_frameworks:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported framework. Supported: {settings.supported_frameworks}"
            )
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize 6-agent job tracking
        job_start_time = time.time()
        active_jobs[job_id] = {
            "id": job_id,
            "status": "initializing",
            "progress": 0.0,
            "current_phase": "6-Agent workflow initialization",
            "request": request.dict(),
            "created_at": job_start_time,
            "updated_at": job_start_time,
            "agents": {
                "orchestrator": {"status": "starting", "progress": 0},
                "planner": {"status": "waiting", "progress": 0},
                "coder": {"status": "waiting", "progress": 0},
                "critic": {"status": "waiting", "progress": 0},
                "file_manager": {"status": "waiting", "progress": 0},
                "qa_validator": {"status": "waiting", "progress": 0}
            },
            "files_generated": 0,
            "user_id": request.user_id,
            "qa_results": None,
            "quality_approved": False,
            "agents_count": 6
        }
        
        # Start background generation task
        background_tasks.add_task(execute_project_generation, job_id, request.dict())
        
        # Build WebSocket URL
        base_url = settings.base_url.replace("http://", "ws://").replace("https://", "wss://")
        websocket_url = f"{base_url}/ws/{job_id}"
        
        logger.info(f"🎯 Project generation started: {job_id}")
        
        return ProjectResponse(
            job_id=job_id,
            status="started",
            message="6-agent project generation started successfully",
            estimated_time=400,  # 6-7 minutes estimate for 6-agent system
            websocket_url=websocket_url
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start project generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# QA Report endpoint
@app.get("/api/vibe-coding/qa-report/{job_id}", tags=["QA"])
async def get_qa_report(job_id: str):
    """Get detailed QA validation report for a project"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = active_jobs[job_id]
    if "qa_results" not in job_data or job_data["qa_results"] is None:
        raise HTTPException(status_code=400, detail="QA validation not completed")
    
    qa_results = job_data["qa_results"]
    
    return {
        "job_id": job_id,
        "qa_report": qa_results.get("qa_report", ""),
        "quality_score": qa_results.get("quality_score", 0),
        "final_approval": qa_results.get("final_approval", False),
        "test_results": qa_results.get("test_results", {}),
        "security_scan": qa_results.get("security_scan", {}),
        "performance_metrics": qa_results.get("performance_metrics", {}),
        "recommendations": qa_results.get("recommendations", []),
        "validation_timestamp": qa_results.get("end_time"),
        "compilation_status": qa_results.get("compilation", {}),
        "validation_details": qa_results.get("validation_details", {})
    }

# Enhanced project status endpoint with QA metrics
@app.get("/api/vibe-coding/detailed-status/{job_id}", tags=["Generation"])
async def get_detailed_project_status(job_id: str):
    """Get comprehensive project status including 6-agent details and QA metrics"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = active_jobs[job_id]
    
    # Calculate overall progress based on 6 agents
    agent_progresses = [agent["progress"] for agent in job_data["agents"].values()]
    overall_progress = sum(agent_progresses) / len(agent_progresses) if agent_progresses else 0
    
    # Include QA-specific information
    qa_info = {}
    if job_data.get("qa_results"):
        qa_results = job_data["qa_results"]
        qa_info = {
            "quality_score": qa_results.get("quality_score", 0),
            "final_approval": qa_results.get("final_approval", False),
            "tests_executed": len(qa_results.get("tests_executed", [])),
            "security_issues": qa_results.get("security_scan", {}).get("vulnerabilities_found", 0),
            "performance_score": qa_results.get("performance", {}).get("performance_score", 0),
            "validation_status": qa_results.get("validation_status", "pending")
        }
    
    return {
        "job_id": job_id,
        "status": job_data["status"],
        "progress": overall_progress,
        "current_phase": job_data["current_phase"],
        "agents": job_data["agents"],
        "agents_count": job_data.get("agents_count", 6),
        "files_generated": job_data["files_generated"],
        "created_at": job_data["created_at"],
        "updated_at": job_data["updated_at"],
        "estimated_completion": job_data.get("estimated_completion"),
        "error_message": job_data.get("error_message"),
        "qa_metrics": qa_info,
        "quality_approved": job_data.get("quality_approved", False)
    }

# Project status endpoint
@app.get("/api/vibe-coding/status/{job_id}", response_model=ProjectStatus, tags=["Generation"])
async def get_project_status(job_id: str):
    """Get current project generation status"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = active_jobs[job_id]
    
    return ProjectStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        current_phase=job["current_phase"],
        agents=job["agents"],
        files_generated=job["files_generated"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        estimated_completion=job.get("estimated_completion"),
        error_message=job.get("error_message")
    )

# File listing endpoint
@app.get("/api/vibe-coding/files/{job_id}", response_model=ProjectFiles, tags=["Files"])
async def get_project_files(job_id: str):
    """Get generated project files"""
    if job_id not in generated_projects:
        raise HTTPException(status_code=404, detail="Project files not found")
    
    project = generated_projects[job_id]
    files = []
    total_size = 0
    
    for file_path, content in project.get("files", {}).items():
        content_str = content if isinstance(content, str) else str(content)
        file_size = len(content_str.encode('utf-8'))
        total_size += file_size
        
        files.append(FileItem(
            path=file_path,
            content=content_str,
            language=file_path.split('.')[-1] if '.' in file_path else "text",
            size=file_size
        ))
    
    return ProjectFiles(
        job_id=job_id,
        files=files,
        total_files=len(files),
        total_size=total_size
    )

# Project download endpoint
@app.get("/api/download/{job_id}", tags=["Files"])
async def download_project(job_id: str):
    """Download project as ZIP file"""
    if job_id not in generated_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = generated_projects[job_id]
    
    # Create temporary ZIP file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    try:
        with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path, content in project.get("files", {}).items():
                content_str = content if isinstance(content, str) else str(content)
                zipf.writestr(file_path, content_str)
        
        # Create a streaming response
        async def iterfile():
            with open(temp_file.name, "rb") as file_like:
                yield file_like.read()
        
        return StreamingResponse(
            iterfile(),
            media_type='application/zip',
            headers={'Content-Disposition': f'attachment; filename="project-{job_id}.zip"'}
        )
        
    except Exception as e:
        logger.error(f"❌ Download failed for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create download")
    finally:
        # Cleanup temp file after a delay
        asyncio.create_task(cleanup_temp_file(temp_file.name))

async def cleanup_temp_file(file_path: str, delay: int = 60):
    """Cleanup temporary file after delay"""
    await asyncio.sleep(delay)
    try:
        os.unlink(file_path)
    except Exception:
        pass

# List all projects
@app.get("/api/projects", tags=["Projects"])
async def list_projects(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None)
):
    """List all projects with pagination"""
    projects = []
    
    for job_id, job in active_jobs.items():
        if status and job["status"] != status:
            continue
            
        project_info = {
            "id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "current_phase": job["current_phase"],
            "files_count": job["files_generated"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "framework": job["request"].get("framework", "unknown")
        }
        projects.append(project_info)
    
    # Sort by creation time (newest first)
    projects.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(projects)
    projects = projects[offset:offset + limit]
    
    return {
        "projects": projects,
        "total": total,
        "limit": limit,
        "offset": offset
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time project updates"""
    connection_id = await connection_manager.connect(websocket, job_id=job_id)
    
    try:
        logger.info(f"📡 WebSocket connected for job: {job_id}")
        
        # Send initial status if job exists
        if job_id in active_jobs:
            job = active_jobs[job_id]
            await connection_manager.send_personal_message({
                "type": "initial_status",
                "job_id": job_id,
                "status": job["status"],
                "progress": job["progress"],
                "current_phase": job["current_phase"],
                "agents": job["agents"]
            }, connection_id)
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/pong for connection health
                if message.get("type") == "ping":
                    await connection_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": time.time()
                    }, connection_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"📡 WebSocket disconnected for job: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        connection_manager.disconnect(connection_id)

# Stats endpoint
@app.get("/api/stats", tags=["System"])
async def get_system_stats():
    """Get system statistics"""
    connection_stats = connection_manager.get_connection_stats()
    
    # Calculate job statistics
    job_stats = {
        "total": len(active_jobs),
        "active": len([j for j in active_jobs.values() if j["status"] in ["processing", "initializing"]]),
        "completed": len([j for j in active_jobs.values() if j["status"] == "completed"]),
        "failed": len([j for j in active_jobs.values() if j["status"] == "failed"])
    }
    
    return {
        "connections": connection_stats,
        "jobs": job_stats,
        "projects_generated": len(generated_projects),
        "system": {
            "environment": settings.environment,
            "debug": settings.debug,
            "uptime": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
        }
    }

async def execute_project_generation(job_id: str, request_data: Dict[str, Any]):
    """Execute the complete project generation workflow with real-time updates"""
    start_time = time.time()
    
    try:
        logger.info(f"🔄 Starting project generation for job: {job_id}")
        
        # Update job status
        active_jobs[job_id]["status"] = "processing"
        active_jobs[job_id]["current_phase"] = "Initializing workflow"
        
        # Prepare enhanced vibe request for orchestrator
        vibe_request = {
            "vibe_prompt": request_data["prompt"],
            "project_data": {
                "project_type": request_data.get("project_type", "web"),
                "framework": request_data.get("framework", "react"),
                "complexity": request_data.get("complexity", "simple"),
                "features": request_data.get("features", []),
                "user_preferences": {
                    "responsive_design": "responsive-design" in request_data.get("features", []),
                    "dark_mode": "dark-mode" in request_data.get("features", []),
                    "animations": "animations" in request_data.get("features", []),
                    "api_integration": "api-integration" in request_data.get("features", []),
                    "testing": "testing" in request_data.get("features", []),
                    "deployment": "deployment" in request_data.get("features", [])
                }
            }
        }
        
        # Initialize 6-agent tracking
        await connection_manager.initialize_6_agent_tracking(job_id)
        
        # Execute the enhanced 6-agent workflow
        logger.info(f"🎭 Executing 6-agent workflow with orchestrator for job: {job_id}")
        
        # Use the enhanced orchestration method for 6-agent system
        workflow_result = await orchestrator_agent.orchestrate_project_creation(
            request_data["prompt"], job_id
        )
        
        # Process 6-agent workflow results
        if workflow_result and workflow_result.get("status") == "completed":
            # Store generated project with enhanced 6-agent metadata
            project_files = workflow_result.get("project_files", {})
            statistics = workflow_result.get("statistics", {})
            qa_validation = workflow_result.get("quality_validation", {})
            
            generated_projects[job_id] = {
                "files": project_files,
                "metadata": {
                    "framework": request_data.get("framework", "react"),
                    "project_type": request_data.get("project_type", "web"),
                    "quality_score": qa_validation.get("quality_score", 0),
                    "final_approval": qa_validation.get("final_approval", False),
                    "agents_executed": workflow_result.get("agents_executed", [])
                },
                "statistics": statistics,
                "qa_validation": qa_validation,
                "created_at": start_time,
                "generation_time": workflow_result.get("execution_time", time.time() - start_time),
                "workflow_summary": {
                    "total_agents": 6,
                    "agents_completed": len(workflow_result.get("agents_executed", [])),
                    "quality_score": qa_validation.get("quality_score", 0),
                    "final_approval": qa_validation.get("final_approval", False),
                    "tests_executed": qa_validation.get("test_results", {}).get("total_tests", 0),
                    "security_issues": qa_validation.get("security_scan", {}).get("vulnerabilities_found", 0),
                    "framework": request_data.get("framework", "react")
                }
            }
            
            # Store QA results in active job for reporting
            active_jobs[job_id]["qa_results"] = qa_validation
            active_jobs[job_id]["quality_approved"] = qa_validation.get("final_approval", False)
            
            # Update final status with enhanced 6-agent statistics
            active_jobs[job_id]["status"] = "completed"
            active_jobs[job_id]["progress"] = 100.0
            active_jobs[job_id]["current_phase"] = "6-agent workflow complete"
            active_jobs[job_id]["files_generated"] = statistics.get("total_files", len(project_files))
            active_jobs[job_id]["agents"]["qa_validator"]["status"] = "completed"
            active_jobs[job_id]["agents"]["qa_validator"]["progress"] = 100
            active_jobs[job_id]["updated_at"] = time.time()
            active_jobs[job_id]["quality_score"] = qa_validation.get("quality_score", 0)
            active_jobs[job_id]["generation_summary"] = {
                "total_lines": statistics.get("total_lines", 0),
                "components_created": statistics.get("components_created", 0),
                "generation_time": workflow_result.get("execution_time", time.time() - start_time),
                "final_approval": qa_validation.get("final_approval", False),
                "tests_executed": qa_validation.get("test_results", {}).get("total_tests", 0),
                "framework": request_data.get("framework", "react")
            }
            
            # Send completion notification with enhanced 6-agent data
            download_url = f"{settings.base_url}/api/download/{job_id}"
            await connection_manager.send_to_job({
                "type": "project_complete",
                "job_id": job_id,
                "total_files": statistics.get("total_files", len(project_files)),
                "generation_time": workflow_result.get("execution_time", time.time() - start_time),
                "download_url": download_url,
                "quality_score": qa_validation.get("quality_score", 0),
                "final_approval": qa_validation.get("final_approval", False),
                "qa_summary": {
                    "tests_executed": qa_validation.get("test_results", {}).get("total_tests", 0),
                    "security_issues": qa_validation.get("security_scan", {}).get("vulnerabilities_found", 0),
                    "performance_score": qa_validation.get("performance_metrics", {}).get("performance_score", 0)
                }
            }, job_id)
            
            logger.info(f"✅ 6-agent project generation completed: {job_id}")
            logger.info(f"📊 Generated {statistics.get('total_files', 0)} files, {statistics.get('total_lines', 0)} lines")
            logger.info(f"🎯 Quality Score: {qa_validation.get('quality_score', 0)}%, Approved: {qa_validation.get('final_approval', False)}")
            
        else:
            # Handle workflow failure
            error_log = workflow_result.get("error_log", [])
            error_message = "Workflow execution failed"
            
            if error_log:
                latest_error = error_log[-1]
                error_message = f"{latest_error.get('step', 'Unknown')}: {latest_error.get('error', 'Unknown error')}"
            
            raise Exception(error_message)
            
    except Exception as e:
        logger.error(f"❌ Project generation failed for {job_id}: {e}")
        logger.error(traceback.format_exc())
        
        # Update error status with detailed information
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error_message"] = str(e)
        active_jobs[job_id]["updated_at"] = time.time()
        active_jobs[job_id]["generation_time"] = time.time() - start_time
        
        # Send detailed error notification
        await connection_manager.send_error(job_id, str(e), "generation_error")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"❌ Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": time.time()
        }
    )

# Store start time for uptime calculation
app.state.start_time = time.time()

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Multi-Agent Code Generation Server")
    uvicorn.run(
        "simple_app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.server_reload,
        log_level=settings.server_log_level
    )