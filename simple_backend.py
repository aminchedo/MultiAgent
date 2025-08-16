#!/usr/bin/env python3
"""
Simple mock backend for testing the frontend without external dependencies.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import time
import json
from typing import Dict, Any, List
import asyncio

app = FastAPI(title="Mock Multi-Agent Code Generation API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for jobs
jobs: Dict[str, Dict[str, Any]] = {}

class GenerateRequest(BaseModel):
    prompt: str
    projectType: str = "web"
    complexity: str = "simple"

class JobResponse(BaseModel):
    id: str
    status: str
    progress: int
    current_agent: str
    description: str
    files: List[Dict[str, Any]] = []

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Mock backend is running"}

@app.post("/api/generate")
async def generate_project(request: GenerateRequest):
    """Create a new generation job."""
    job_id = str(uuid.uuid4())
    
    # Create initial job
    jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0,
        "current_agent": "planner",
        "description": request.prompt,
        "files": [],
        "created_at": time.time()
    }
    
    # Start background task to simulate job progress
    asyncio.create_task(simulate_job_progress(job_id))
    
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/api/download/{job_id}")
async def download_project(job_id: str):
    """Download the generated project."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    # Create a mock ZIP file content
    mock_files = [
        {"path": "package.json", "content": '{"name": "mock-project", "version": "1.0.0"}'},
        {"path": "src/App.js", "content": "import React from 'react';\n\nfunction App() {\n  return <div>Hello World</div>;\n}\n\nexport default App;"},
        {"path": "README.md", "content": "# Mock Project\n\nThis is a mock project generated for testing."}
    ]
    
    # Return mock ZIP content (in real implementation, this would be a ZIP file)
    return {"files": mock_files, "message": "Mock project downloaded"}

async def simulate_job_progress(job_id: str):
    """Simulate job progress through different agents."""
    agents = ["planner", "code_generator", "tester", "doc_generator", "reviewer"]
    
    for i, agent in enumerate(agents):
        # Update job status
        jobs[job_id]["current_agent"] = agent
        jobs[job_id]["progress"] = (i + 1) * 20
        jobs[job_id]["status"] = "running"
        
        # Simulate agent working
        await asyncio.sleep(3)  # Wait 3 seconds per agent
        
        # Add some mock files
        if agent == "code_generator":
            jobs[job_id]["files"].extend([
                {"path": f"src/components/{agent}.js", "language": "javascript", "size": 150, "created_by": agent},
                {"path": f"src/utils/{agent}.js", "language": "javascript", "size": 200, "created_by": agent}
            ])
        elif agent == "doc_generator":
            jobs[job_id]["files"].append(
                {"path": "README.md", "language": "markdown", "size": 300, "created_by": agent}
            )
    
    # Mark job as completed
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["progress"] = 100
    jobs[job_id]["current_agent"] = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)