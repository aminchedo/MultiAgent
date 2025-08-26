"""
Vercel serverless function for vibe-coding API endpoint.
Integrates with the sophisticated multi-agent system for real project generation.
"""

import os
import sys
import json
import uuid
import logging
import traceback
from datetime import datetime
from typing import Dict, Any

# Set up Vercel environment
os.environ["VERCEL"] = "1"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Python path for Vercel
def setup_python_path():
    """Setup Python path for accessing agents"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Add agents directory specifically
        agents_dir = os.path.join(project_root, 'agents')
        if agents_dir not in sys.path:
            sys.path.insert(0, agents_dir)
            
        return project_root
    except Exception as e:
        logger.error(f"Failed to setup Python path: {e}")
        return None

project_root = setup_python_path()

# Try to import FastAPI and agents
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    
    # Import our sophisticated agents
    from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
    
    logger.info("✅ Successfully imported FastAPI and agents")
    AGENTS_AVAILABLE = True
    
except ImportError as e:
    logger.error(f"❌ Failed to import dependencies: {e}")
    logger.error(traceback.format_exc())
    AGENTS_AVAILABLE = False

# Request/Response models
class VibeRequest(BaseModel):
    vibe_prompt: str
    project_type: str = "web"
    framework: str = "react"

class VibeResponse(BaseModel):
    job_id: str
    status: str
    message: str

# Job storage (in production, use proper database)
job_store: Dict[str, Dict[str, Any]] = {}

# Create FastAPI app
app = FastAPI(
    title="Vibe Coding API",
    description="Real multi-agent project generation",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "vibe-coding-api",
        "agents_available": AGENTS_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/", response_model=VibeResponse)
async def vibe_coding_endpoint(request: VibeRequest, background_tasks: BackgroundTasks):
    """
    Main vibe coding endpoint for Vercel deployment.
    Generates real projects using sophisticated AI agents.
    """
    try:
        if not AGENTS_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Agent system not available in this environment"
            )
        
        # Validate request
        if not request.vibe_prompt or len(request.vibe_prompt.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="vibe_prompt must be at least 10 characters"
            )
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job tracking
        job_store[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "message": "Real agent processing started",
            "progress": 0,
            "vibe_prompt": request.vibe_prompt,
            "project_type": request.project_type,
            "framework": request.framework,
            "agent_status": {
                "planner": "pending",
                "coder": "pending",
                "critic": "pending",
                "file_manager": "pending"
            },
            "files_generated": [],
            "created_at": datetime.now().isoformat(),
            "error_log": []
        }
        
        # Start real agent processing in background
        background_tasks.add_task(process_vibe_request_real, job_id, request.dict())
        
        logger.info(f"🚀 Vibe coding job started: {job_id}")
        
        return VibeResponse(
            job_id=job_id,
            status="processing",
            message="Real agent processing started using sophisticated agents"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Vibe coding endpoint failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

async def process_vibe_request_real(job_id: str, vibe_request: Dict[str, Any]):
    """
    Process vibe request using real sophisticated agents.
    This runs in the background after the initial response.
    """
    try:
        if not AGENTS_AVAILABLE:
            job_store[job_id]["status"] = "failed"
            job_store[job_id]["message"] = "Agents not available"
            return
        
        # Update job status
        job_store[job_id]["message"] = "Initializing sophisticated AI agents..."
        job_store[job_id]["progress"] = 10
        
        # Initialize the workflow orchestrator
        orchestrator = VibeWorkflowOrchestratorAgent()
        
        # Update agent status
        job_store[job_id]["agent_status"]["planner"] = "processing"
        job_store[job_id]["message"] = "AI Planner analyzing your vibe prompt..."
        job_store[job_id]["progress"] = 25
        
        # Execute the real vibe workflow
        logger.info(f"🤖 Starting real workflow execution for job {job_id}")
        workflow_result = orchestrator.orchestrate_vibe_project(vibe_request)
        
        # Update status based on results
        if workflow_result.get('workflow_status') == 'completed':
            job_store[job_id]["status"] = "completed"
            job_store[job_id]["message"] = "Project generated successfully!"
            job_store[job_id]["progress"] = 100
            
            # Update all agent statuses
            for agent in job_store[job_id]["agent_status"]:
                job_store[job_id]["agent_status"][agent] = "completed"
            
            # Extract file information
            files_generated = []
            file_manager_result = workflow_result.get('agent_results', {}).get('file_manager', {})
            organized_files = file_manager_result.get('organized_files', {})
            
            for file_path, file_info in organized_files.items():
                files_generated.append({
                    "name": file_path,
                    "type": file_info.get('type', 'unknown'),
                    "size": file_info.get('size', len(file_info.get('content', ''))),
                    "category": file_info.get('category', 'unknown')
                })
            
            job_store[job_id]["files_generated"] = files_generated
            
            # Store ZIP info if available
            zip_info = file_manager_result.get('zip_file', {})
            if zip_info.get('success'):
                job_store[job_id]["zip_path"] = zip_info.get('zip_path')
                job_store[job_id]["project_name"] = zip_info.get('project_name')
            
            logger.info(f"✅ Vibe coding completed: {job_id} - {len(files_generated)} files")
            
        else:
            job_store[job_id]["status"] = "failed"
            job_store[job_id]["message"] = f"Generation failed: {workflow_result.get('error_log', ['Unknown error'])}"
            logger.error(f"❌ Vibe coding failed: {job_id}")
        
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["message"] = f"Generation failed: {str(e)}"
        job_store[job_id]["error_log"].append(str(e))
        logger.error(f"❌ Vibe coding error for job {job_id}: {e}")
        logger.error(traceback.format_exc())

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get real-time status of vibe coding job"""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_store[job_id]

@app.get("/files/{job_id}")
async def get_generated_files(job_id: str):
    """Get list of generated files for a job"""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_store[job_id]
    if job_data["status"] != "completed":
        return {"files": [], "message": "Generation not complete"}
    
    return {"files": job_data.get("files_generated", [])}

# For Vercel deployment compatibility
def handler(request, response):
    """Vercel handler function"""
    import uvicorn
    return uvicorn.run(app, host="0.0.0.0", port=8000)