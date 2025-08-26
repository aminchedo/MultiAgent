from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio
import uuid
import os
<<<<<<< HEAD
import zipfile
import tempfile
import time
=======
import sys
>>>>>>> cursor/bc-e2fa0403-b40e-4c65-9a69-dda967a8b502-84c3
from typing import Dict, Any
from pathlib import Path
import structlog
import sys
sys.path.append('/workspace')

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

<<<<<<< HEAD
# Store job data
job_data: Dict[str, Dict] = {}

# Store generated projects
generated_projects: Dict[str, Dict] = {}
=======
# Job storage for tracking vibe coding progress
job_store: Dict[str, Dict[str, Any]] = {}
>>>>>>> cursor/bc-e2fa0403-b40e-4c65-9a69-dda967a8b502-84c3

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

@app.post("/api/vibe-coding")
async def create_vibe_project(
    vibe_request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Create a project from a natural language vibe description using real agents."""
    try:
        # Import the real vibe agents - add full path
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from agents.vibe_planner_agent import VibePlannerAgent
        from agents.vibe_coder_agent import VibeCoderAgent
        from agents.vibe_critic_agent import VibeCriticAgent
        from agents.vibe_file_manager_agent import VibeFileManagerAgent
        
        # Validate request
        if not vibe_request.get('prompt'):
            raise HTTPException(status_code=400, detail="prompt is required")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Store job data
        job_data[job_id] = {
            "job_id": job_id,
            "prompt": vibe_request['prompt'],
            "project_type": vibe_request.get('project_type', 'web'),
            "status": "processing",
            "created_at": time.time(),
            "progress": 0,
            "current_step": "Planning",
            "agents": {
                "planner": {"status": "starting", "progress": 0},
                "coder": {"status": "pending", "progress": 0},
                "critic": {"status": "pending", "progress": 0},
                "file_manager": {"status": "pending", "progress": 0}
            }
        }
        
        # Start background task for real agent processing
        background_tasks.add_task(
            execute_real_vibe_workflow,
            job_id,
            vibe_request
        )
        
        logger.info("🚀 Real vibe project generation started", 
                   job_id=job_id, 
                   prompt=vibe_request['prompt'][:100])
        
        return {
            "success": True,
            "message": "🚀 Your vibe project is being created! Real AI agents are working on your vision.",
            "job_id": job_id,
            "estimated_duration": 120
        }
        
    except Exception as e:
        logger.error("Failed to start vibe project generation", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start vibe project generation: {str(e)}"
        )

@app.post("/api/jobs")
async def create_job(job_request: Dict[str, Any]):
    """Create a new code generation job."""
    job_id = f"job_{len(job_data) + 1}"
    
    logger.info("Job created", job_id=job_id, description=job_request.get("description"))
    
    return {
        "job_id": job_id,
        "status": "created",
        "message": "Job created successfully"
    }

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get real job status and progress."""
    if job_id not in job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_data[job_id]
    files = []
    
    # Get generated files if job is completed
    if job_id in generated_projects:
        project = generated_projects[job_id]
        files = list(project.get('files', {}).keys())
    
    return {
        "success": True,
        "message": "Job status retrieved successfully",
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "current_step": job["current_step"],
        "step_number": job["progress"] // 25,
        "total_steps": 4,
        "files": files,
        "error_message": job.get("error_message"),
        "created_at": job["created_at"],
        "updated_at": job.get("updated_at", job["created_at"]),
        "estimated_completion": job.get("completed_at")
    }

@app.get("/api/download/{job_id}")
async def download_project(job_id: str):
    """Download the generated project as a ZIP file."""
    if job_id not in job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_data[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed yet")
    
    if job_id not in generated_projects:
        raise HTTPException(status_code=404, detail="No project files found")
    
    project = generated_projects[job_id]
    
    # Create ZIP file in memory
    import io
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        files_dict = project.get('files', {})
        
        # Handle the case where files is a dict of file objects vs. simple strings
        if isinstance(files_dict, dict):
            for file_path, file_data in files_dict.items():
                # If file_data is a dict with content, use that
                if isinstance(file_data, dict) and 'content' in file_data:
                    content = file_data['content']
                else:
                    # Otherwise treat it as the content itself
                    content = str(file_data) if file_data else f"# {file_path}\n\n# Generated by Vibe Coding Platform"
                
                zip_file.writestr(file_path, content)
        
        # If no files, add a basic structure
        if not files_dict:
            zip_file.writestr("README.md", "# Vibe Generated Project\n\nThis project was generated by the Vibe Coding Platform.")
            zip_file.writestr("package.json", json.dumps({
                "name": "vibe-generated-project",
                "version": "1.0.0",
                "description": "Generated by Vibe Coding Platform",
                "main": "index.js"
            }, indent=2))
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=vibe_project_{job_id[:8]}.zip"}
    )

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

<<<<<<< HEAD
async def execute_real_vibe_workflow(job_id: str, vibe_request: Dict[str, Any]):
    """Execute the real vibe workflow using existing agents."""
    try:
        # Import real agents - add full path
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from agents.vibe_planner_agent import VibePlannerAgent
        from agents.vibe_coder_agent import VibeCoderAgent
        from agents.vibe_critic_agent import VibeCriticAgent
        from agents.vibe_file_manager_agent import VibeFileManagerAgent
        
        logger.info(f"🚀 Starting real agent workflow for job {job_id}")
        
        # Step 1: Planning Agent
        job_data[job_id]["current_step"] = "Planning"
        job_data[job_id]["progress"] = 10
        job_data[job_id]["agents"]["planner"]["status"] = "running"
        
        planner = VibePlannerAgent()
        plan_input = {
            'vibe_prompt': vibe_request['prompt'],
            'project_type': vibe_request.get('project_type', 'web')
        }
        
        logger.info(f"🔍 Planner analyzing vibe: {vibe_request['prompt'][:50]}...")
        plan_result = planner.decompose_vibe_prompt(vibe_request['prompt'], plan_input)
        logger.info(f"📋 Plan result keys: {list(plan_result.keys()) if plan_result else 'None'}")
        
        job_data[job_id]["progress"] = 25
        job_data[job_id]["agents"]["planner"]["status"] = "completed"
        job_data[job_id]["agents"]["planner"]["progress"] = 100
        
        # Step 2: Code Generation Agent
        job_data[job_id]["current_step"] = "Code Generation"
        job_data[job_id]["progress"] = 30
        job_data[job_id]["agents"]["coder"]["status"] = "running"
        
        coder = VibeCoderAgent()
        logger.info(f"⚡ Coder generating code from plan...")
        code_result = coder.generate_code_from_plan(plan_result, int(job_id.replace('-', '')[:8], 16))
        logger.info(f"💻 Code result keys: {list(code_result.keys()) if code_result else 'None'}")
        logger.info(f"💻 Generated files: {len(code_result.get('code_files', []))}")
        
        job_data[job_id]["progress"] = 50
        job_data[job_id]["agents"]["coder"]["status"] = "completed"
        job_data[job_id]["agents"]["coder"]["progress"] = 100
        
        # Step 3: Quality Review Agent
        job_data[job_id]["current_step"] = "Quality Review"
        job_data[job_id]["progress"] = 60
        job_data[job_id]["agents"]["critic"]["status"] = "running"
        
        critic = VibeCriticAgent()
        logger.info(f"🔍 Critic reviewing code quality...")
        review_result = critic.review_generated_code(code_result.get('code_files', []), plan_result)
        logger.info(f"🔍 Review result keys: {list(review_result.keys()) if review_result else 'None'}")
        logger.info(f"🔍 Reviewed files: {len(review_result.get('files', []))}")
        
        job_data[job_id]["progress"] = 75
        job_data[job_id]["agents"]["critic"]["status"] = "completed"
        job_data[job_id]["agents"]["critic"]["progress"] = 100
        
        # Step 4: File Organization Agent
        job_data[job_id]["current_step"] = "File Organization"
        job_data[job_id]["progress"] = 80
        job_data[job_id]["agents"]["file_manager"]["status"] = "running"
        
        file_manager = VibeFileManagerAgent()
        logger.info(f"📁 File manager organizing project structure...")
        final_result = file_manager.organize_project_structure(review_result.get('files', []), vibe_request.get('project_type', 'web'))
        logger.info(f"📁 Final result keys: {list(final_result.keys()) if final_result else 'None'}")
        logger.info(f"📁 Organized files: {len(final_result.get('organized_files', {}))}")
        logger.info(f"📁 Final result success: {final_result.get('success', False)}")
        
        # Store the generated project
        generated_projects[job_id] = {
            "job_id": job_id,
            "files": final_result.get('organized_files', {}),
            "structure": final_result.get('project_structure', {}),
            "metadata": final_result.get('optimization_report', {}),
            "file_manifest": final_result.get('file_manifest', {}),
            "zip_info": final_result.get('zip_file', {})
        }
        
        # Mark job as completed
        job_data[job_id]["status"] = "completed"
        job_data[job_id]["progress"] = 100
        job_data[job_id]["current_step"] = "Completed"
        job_data[job_id]["completed_at"] = time.time()
        job_data[job_id]["updated_at"] = time.time()
        job_data[job_id]["agents"]["file_manager"]["status"] = "completed"
        job_data[job_id]["agents"]["file_manager"]["progress"] = 100
        
        file_count = len(generated_projects[job_id]["files"])
        logger.info(f"✅ Real agent workflow completed successfully! Generated {file_count} files for job {job_id}")
        
    except Exception as e:
        logger.error(f"❌ Real agent workflow failed for job {job_id}: {e}")
        job_data[job_id]["status"] = "failed"
        job_data[job_id]["error_message"] = str(e)
        job_data[job_id]["updated_at"] = time.time()
=======
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
>>>>>>> cursor/bc-e2fa0403-b40e-4c65-9a69-dda967a8b502-84c3

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)