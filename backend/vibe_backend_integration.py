#!/usr/bin/env python3
"""
VibeCoding Backend Integration - REAL AGENT PROCESSING
Connects the existing sophisticated agents to the FastAPI backend for genuine functionality.
"""

import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import asyncio
from datetime import datetime
import json
import shutil

# Add agents to path
agents_path = str(Path(__file__).parent.parent / "agents")
sys.path.insert(0, agents_path)
workspace_path = str(Path(__file__).parent.parent)
sys.path.insert(0, workspace_path)

# Import existing sophisticated agents
from agents.vibe_planner_agent import VibePlannerAgent
from agents.vibe_coder_agent import VibeCoderAgent  
from agents.vibe_critic_agent import VibeCriticAgent
from agents.vibe_file_manager_agent import VibeFileManagerAgent

app = FastAPI(title="Vibe Coding Platform - Full Agent Integration", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class VibeRequest(BaseModel):
    prompt: str
    project_type: Optional[str] = "web"
    framework: Optional[str] = "react"

class VibeResponse(BaseModel):
    job_id: str
    status: str
    message: str

class AgentStatus(BaseModel):
    planner: str = "idle"
    coder: str = "idle"
    critic: str = "idle"
    file_manager: str = "idle"

# Job storage (in-memory for now, could be Redis/DB in production)
job_store: Dict[str, Dict[str, Any]] = {}

# Initialize agents (single instances for efficiency)
planner_agent = VibePlannerAgent()
coder_agent = VibeCoderAgent()
critic_agent = VibeCriticAgent()
file_manager_agent = VibeFileManagerAgent()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vibe-coding-full-integration"}

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return {
        "status": "healthy", 
        "service": "vibe-coding-full-integration",
        "agents": {
            "planner": "ready",
            "coder": "ready", 
            "critic": "ready",
            "file_manager": "ready"
        }
    }

@app.post("/api/vibe-coding", response_model=VibeResponse)
async def generate_vibe_project(request: VibeRequest, background_tasks: BackgroundTasks):
    """Start REAL vibe coding process using existing sophisticated agents"""
    job_id = str(uuid.uuid4())
    
    # Initialize job tracking
    job_store[job_id] = {
        "status": "processing",
        "message": "Real agent processing started",
        "created_at": datetime.now().isoformat(),
        "agent_status": AgentStatus().model_dump(),
        "prompt": request.prompt,
        "project_type": request.project_type,
        "framework": request.framework,
        "files_generated": 0,
        "project_path": None,
        "plan": None,
        "files": [],
        "errors": []
    }
    
    # Start REAL processing with existing agents in background
    background_tasks.add_task(process_with_real_agents, job_id, request.prompt, request.project_type, request.framework)
    
    return VibeResponse(
        job_id=job_id,
        status="processing",
        message="Real agent processing started using existing sophisticated agents"
    )

@app.get("/api/vibe-coding/status/{job_id}")
async def get_job_status(job_id: str):
    """Get real-time status of REAL agent processing"""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_store[job_id]

@app.get("/api/vibe-coding/files/{job_id}")
async def get_generated_files(job_id: str):
    """Get list of REAL generated files"""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_store[job_id]
    if job_data["status"] != "completed":
        return {"files": [], "message": "Generation not complete"}
    
    return {"files": job_data.get("files", [])}

@app.get("/api/download/{job_id}")
async def download_project(job_id: str):
    """Download REAL generated project"""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_store[job_id]
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Project not ready for download")
    
    project_path = job_data.get("project_path")
    if not project_path or not os.path.exists(project_path):
        raise HTTPException(status_code=404, detail="Project files not found")
    
    return {"message": "Project ready for download", "job_id": job_id, "path": project_path}

async def process_with_real_agents(job_id: str, prompt: str, project_type: str, framework: str):
    """Process vibe request using REAL existing sophisticated agents"""
    try:
        # PHASE 1: Planning with VibePlannerAgent
        print(f"[{job_id}] Starting Phase 1: VibePlannerAgent analysis")
        job_store[job_id]["agent_status"]["planner"] = "processing"
        job_store[job_id]["message"] = "Analyzing vibe prompt and creating technical plan..."
        
        # Use REAL planner agent
        project_data = {
            "project_type": project_type,
            "framework": framework,
            "description": prompt
        }
        
        # Call REAL method from existing agent
        plan = planner_agent.decompose_vibe_prompt(prompt, project_data)
        job_store[job_id]["plan"] = plan
        job_store[job_id]["agent_status"]["planner"] = "completed"
        
        print(f"[{job_id}] Phase 1 complete. Plan created with {len(plan.get('components', []))} components")
        
        # PHASE 2: Code Generation with VibeCoderAgent
        print(f"[{job_id}] Starting Phase 2: VibeCoderAgent generation")
        job_store[job_id]["agent_status"]["coder"] = "processing"
        job_store[job_id]["message"] = "Generating project files and components..."
        
        # Use REAL coder agent with plan
        generation_result = coder_agent.generate_code_from_plan(plan, int(job_id.replace("-", "")[:8], 16))
        
        if generation_result.get("success"):
            files_data = generation_result.get("generated_files", {})
            job_store[job_id]["agent_status"]["coder"] = "completed"
            print(f"[{job_id}] Phase 2 complete. Generated {len(files_data)} files")
        else:
            raise Exception(f"Code generation failed: {generation_result.get('error', 'Unknown error')}")
        
        # PHASE 3: Code Review with VibeCriticAgent
        print(f"[{job_id}] Starting Phase 3: VibeCriticAgent review")
        job_store[job_id]["agent_status"]["critic"] = "processing"
        job_store[job_id]["message"] = "Reviewing and optimizing code quality..."
        
        # Convert files to format expected by critic
        files_for_review = []
        for file_path, content in files_data.items():
            files_for_review.append({
                "path": file_path,
                "content": content,
                "size": len(content)
            })
        
        # Use REAL critic agent
        review_result = critic_agent.review_generated_code(files_for_review, plan)
        
        if review_result.get("success"):
            # Apply improvements if any
            improved_files = review_result.get("improved_files", files_data)
            job_store[job_id]["agent_status"]["critic"] = "completed"
            print(f"[{job_id}] Phase 3 complete. Code review score: {review_result.get('overall_score', 'N/A')}")
        else:
            # Continue with original files if review fails
            improved_files = files_data
            job_store[job_id]["agent_status"]["critic"] = "completed"
            print(f"[{job_id}] Phase 3 complete with warnings")
        
        # PHASE 4: File Organization with VibeFileManagerAgent
        print(f"[{job_id}] Starting Phase 4: VibeFileManagerAgent organization")
        job_store[job_id]["agent_status"]["file_manager"] = "processing"
        job_store[job_id]["message"] = "Organizing project structure and creating files..."
        
        # Convert files for file manager
        files_for_organization = []
        for file_path, content in improved_files.items():
            files_for_organization.append({
                "path": file_path,
                "content": content,
                "size": len(content)
            })
        
        # Use REAL file manager agent
        organization_result = file_manager_agent.organize_project_structure(files_for_organization, project_type)
        
        if organization_result.get("success"):
            # Create actual project directory
            project_dir = f"/workspace/generated_projects/{job_id}"
            os.makedirs(project_dir, exist_ok=True)
            
            # Write REAL files to disk
            organized_files = organization_result.get("organized_files", {})
            created_files = []
            
            # organized_files is a flat dictionary {file_path: file_data}
            for file_path, file_data in organized_files.items():
                full_path = os.path.join(project_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                content = file_data.get("content", "")
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                created_files.append({
                    "name": file_path,
                    "size": len(content),
                    "type": file_path.split('.')[-1] if '.' in file_path else "unknown",
                    "category": file_data.get("category", "unknown")
                })
            
            job_store[job_id]["files"] = created_files
            job_store[job_id]["project_path"] = project_dir
            job_store[job_id]["files_generated"] = len(created_files)
            job_store[job_id]["agent_status"]["file_manager"] = "completed"
            
            print(f"[{job_id}] Phase 4 complete. Created {len(created_files)} files in {project_dir}")
        else:
            raise Exception(f"File organization failed: {organization_result.get('error', 'Unknown error')}")
        
        # FINAL: Mark as completed
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["message"] = f"Project generated successfully! {len(created_files)} files created using real AI agents."
        
        print(f"[{job_id}] ALL PHASES COMPLETE - Real project generated successfully!")
        
    except Exception as e:
        # Handle REAL errors honestly
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["message"] = f"Generation failed: {str(e)}"
        job_store[job_id]["errors"].append(str(e))
        print(f"[{job_id}] FAILED: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)