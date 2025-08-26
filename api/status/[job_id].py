"""
Vercel serverless function for vibe-coding job status tracking.
Dynamic route: /api/status/[job_id]
"""

import os
import sys
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Set up Vercel environment
os.environ["VERCEL"] = "1"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Vibe Coding Status API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import job store (in production, use proper database)
# For now, we'll create a simple in-memory store
job_store = {}

@app.get("/{job_id}")
async def get_job_status(job_id: str):
    """
    Get real-time status of vibe coding job.
    Returns detailed progress information including agent statuses.
    """
    try:
        # In a real deployment, this would connect to a database
        # For now, return a mock response that matches our API structure
        
        if job_id == "test-job-id":
            return {
                "job_id": job_id,
                "status": "completed",
                "message": "Test job completed successfully",
                "progress": 100,
                "vibe_prompt": "Test vibe prompt",
                "project_type": "web",
                "framework": "react",
                "agent_status": {
                    "planner": "completed",
                    "coder": "completed",
                    "critic": "completed",
                    "file_manager": "completed"
                },
                "files_generated": [
                    {
                        "name": "package.json",
                        "type": "configuration",
                        "size": 732,
                        "category": "configuration"
                    },
                    {
                        "name": "src/App.tsx",
                        "type": "typescript-react",
                        "size": 470,
                        "category": "component"
                    }
                ],
                "created_at": "2025-08-26T01:00:00Z"
            }
        
        # For unknown job IDs, return 404
        raise HTTPException(status_code=404, detail="Job not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting job status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for status API"""
    return {
        "status": "healthy",
        "service": "vibe-coding-status-api",
        "endpoint": "status"
    }

# Vercel handler
def handler(request, response):
    """Vercel handler function"""
    import uvicorn
    return uvicorn.run(app, host="0.0.0.0", port=8000)