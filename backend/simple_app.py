from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import uuid
import os
import sys
from typing import Dict, Any
from pathlib import Path
import structlog

# Add agents to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the sophisticated agents
from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Vibe Coding Platform",
    version="1.0.0",
    description="A production-ready multi-agent code generation system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Job storage for tracking vibe coding progress
job_store: Dict[str, Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "vibe-coding-platform",
        "version": "1.0.0"
    }

@app.get("/api/templates")
async def get_templates():
    """Get available project templates."""
    return {
        "templates": [
            {
                "id": "react-app",
                "name": "React Application",
                "description": "Modern React app with TypeScript",
                "category": "frontend"
            },
            {
                "id": "node-api",
                "name": "Node.js API",
                "description": "Express.js REST API",
                "category": "backend"
            },
            {
                "id": "fullstack",
                "name": "Full Stack App",
                "description": "React frontend + Node.js backend",
                "category": "fullstack"
            }
        ]
    }

@app.post("/api/jobs")
async def create_job(job_data: Dict[str, Any]):
    """Create a new code generation job."""
    job_id = f"job_{len(active_connections) + 1}"
    
    logger.info("Job created", job_id=job_id, description=job_data.get("description"))
    
    return {
        "job_id": job_id,
        "status": "created",
        "message": "Job created successfully"
    }

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and progress."""
    return {
        "job_id": job_id,
        "status": "running",
        "progress": 25,
        "agents": {
            "planner": {"status": "completed", "progress": 100},
            "code_generator": {"status": "running", "progress": 50},
            "tester": {"status": "pending", "progress": 0},
            "doc_generator": {"status": "pending", "progress": 0},
            "reviewer": {"status": "pending", "progress": 0}
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    # Generate a unique connection ID
    connection_id = f"conn_{len(active_connections) + 1}"
    active_connections[connection_id] = websocket
    
    logger.info("WebSocket connected", connection_id=connection_id)
    
    try:
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "message": "Connected to Vibe Coding Platform"
        }))
        
        # Simulate agent progress updates
        for i in range(5):
            await asyncio.sleep(2)
            
            progress_data = {
                "type": "agent_progress",
                "agent_type": "code_generator",
                "data": {
                    "progress": (i + 1) * 20,
                    "status": "running",
                    "current_task": f"Generating file {i + 1}",
                    "messages": [f"Created component {i + 1}"]
                }
            }
            
            await websocket.send_text(json.dumps(progress_data))
            
            # Simulate file generation
            if i % 2 == 0:
                file_data = {
                    "type": "file_generated",
                    "data": {
                        "path": f"src/components/Component{i + 1}.tsx",
                        "content": f"// Component {i + 1}\nimport React from 'react';\n\nexport default function Component{i + 1}() {{\n  return <div>Component {i + 1}</div>;\n}}",
                        "language": "typescript",
                        "size": 150 + i * 50,
                        "created_by": "code_generator",
                        "is_binary": False,
                        "type": "file"
                    }
                }
                await websocket.send_text(json.dumps(file_data))
        
        # Send completion message
        await websocket.send_text(json.dumps({
            "type": "job_complete",
            "data": {
                "status": "completed",
                "message": "Project generation completed successfully!"
            }
        }))
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                logger.info("Received message", message=message)
                
                # Handle different message types
                if message.get("type") == "test":
                    # Echo back for testing
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "data": message
                    }))
                else:
                    # Echo back for other messages
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "data": message
                    }))
                
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", connection_id=connection_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), connection_id=connection_id)
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]

@app.post("/api/vibe-coding")
async def vibe_coding_endpoint(vibe_request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Real vibe coding endpoint that integrates with existing sophisticated agents.
    This replaces any mock functionality with actual agent processing.
    """
    try:
        # Validate request
        if not vibe_request.get('vibe_prompt'):
            raise HTTPException(
                status_code=400,
                detail="vibe_prompt is required"
            )
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job tracking
        job_store[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "message": "Real agent processing started",
            "progress": 0,
            "vibe_prompt": vibe_request['vibe_prompt'],
            "project_type": vibe_request.get('project_type', 'web'),
            "framework": vibe_request.get('framework', 'react'),
            "agent_status": {
                "planner": "pending",
                "coder": "pending", 
                "critic": "pending",
                "file_manager": "pending"
            },
            "files_generated": [],
            "project_path": None,
            "error_log": []
        }
        
        # Start real agent processing in background
        background_tasks.add_task(process_vibe_request_real, job_id, vibe_request)
        
        logger.info("🚀 Real vibe coding job started", job_id=job_id, prompt=vibe_request['vibe_prompt'][:50])
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Real agent processing started using existing sophisticated agents"
        }
        
    except Exception as e:
        logger.error(f"❌ Vibe coding endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start vibe coding: {str(e)}"
        )

@app.get("/api/vibe-coding/status/{job_id}")
async def get_vibe_job_status(job_id: str):
    """Get real-time status of vibe coding job with actual agent progress."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_store[job_id]

@app.get("/api/vibe-coding/files/{job_id}")
async def get_vibe_generated_files(job_id: str):
    """Get list of real generated files from vibe coding."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_store[job_id]
    if job_data["status"] != "completed":
        return {"files": [], "message": "Generation not complete"}
    
    return {"files": job_data.get("files_generated", [])}

@app.get("/api/download/{job_id}")
async def download_vibe_project(job_id: str):
    """Download the real generated project as a ZIP file."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_store[job_id]
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Project generation not completed")
    
    zip_path = job_data.get("zip_path")
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Generated project file not found")
    
    from fastapi.responses import FileResponse
    project_name = job_data.get("project_name", f"vibe-project-{job_id}")
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=f"{project_name}.zip",
        headers={"Content-Disposition": f"attachment; filename={project_name}.zip"}
    )

async def process_vibe_request_real(job_id: str, vibe_request: Dict[str, Any]):
    """
    Process vibe request using existing sophisticated agents - REAL IMPLEMENTATION
    This function connects to the existing VibeWorkflowOrchestratorAgent.
    """
    try:
        # Update job status
        job_store[job_id]["message"] = "Initializing sophisticated AI agents..."
        
        # Initialize the existing orchestrator agent
        orchestrator = VibeWorkflowOrchestratorAgent()
        
        # Update status - planning phase
        job_store[job_id]["agent_status"]["planner"] = "processing"
        job_store[job_id]["message"] = "AI Planner analyzing your vibe prompt..."
        job_store[job_id]["progress"] = 10
        
        # Execute the real vibe workflow using existing agents
        logger.info(f"🤖 Starting real workflow execution for job {job_id}")
        workflow_result = orchestrator.orchestrate_vibe_project(vibe_request)
        
        # Update status based on real results
        if workflow_result.get('workflow_status') == 'completed':
            job_store[job_id]["status"] = "completed"
            job_store[job_id]["message"] = "Project generated successfully!"
            job_store[job_id]["progress"] = 100
            
            # Update all agent statuses to completed
            for agent in job_store[job_id]["agent_status"]:
                job_store[job_id]["agent_status"][agent] = "completed"
            
            # Extract real file information from workflow results
            files_generated = []
            project_data = workflow_result.get('project_data', {})
            
            # Get files from file manager result
            file_manager_result = workflow_result.get('agent_results', {}).get('file_manager', {})
            organized_files = file_manager_result.get('organized_files', {})
            
            # Create file list with real file information
            for file_path, file_info in organized_files.items():
                files_generated.append({
                    "name": file_path,
                    "type": file_info.get('type', 'unknown'),
                    "size": file_info.get('size', len(file_info.get('content', ''))),
                    "category": file_info.get('category', 'unknown')
                })
            
            # If no organized files, try to get from coder result
            if not files_generated:
                coder_result = workflow_result.get('agent_results', {}).get('coder', {})
                generated_files = coder_result.get('generated_files', {})
                
                for file_path, content in generated_files.items():
                    files_generated.append({
                        "name": file_path,
                        "type": file_path.split('.')[-1] if '.' in file_path else "unknown",
                        "size": len(content) if isinstance(content, str) else 0,
                        "category": "generated"
                    })
            
            # Store file information
            job_store[job_id]["files_generated"] = files_generated
            
            # Store ZIP file path if available
            zip_info = file_manager_result.get('zip_file', {})
            if zip_info.get('success'):
                job_store[job_id]["zip_path"] = zip_info.get('zip_path')
                job_store[job_id]["project_name"] = zip_info.get('project_name')
            
            job_store[job_id]["project_path"] = workflow_result.get('project_id')
            
            logger.info(f"✅ Vibe coding completed successfully for job {job_id} - Generated {len(files_generated)} files")
            
        else:
            # Handle failure case
            job_store[job_id]["status"] = "failed"
            job_store[job_id]["message"] = f"Generation failed: {workflow_result.get('error_log', ['Unknown error'])}"
            logger.error(f"❌ Vibe coding failed for job {job_id}: {workflow_result.get('error_log')}")
        
    except Exception as e:
        # Handle real errors
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["message"] = f"Generation failed: {str(e)}"
        job_store[job_id]["error_log"].append(str(e))
        logger.error(f"❌ Vibe coding error for job {job_id}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)