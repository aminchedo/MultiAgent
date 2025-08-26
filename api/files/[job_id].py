"""
Vercel serverless function for listing generated project files.
Dynamic route: /api/files/[job_id]
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Set up Vercel environment
os.environ["VERCEL"] = "1"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Vibe Coding Files API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/{job_id}")
async def get_generated_files(job_id: str):
    """
    Get list of generated files for a specific job.
    Returns detailed file information including names, types, and sizes.
    """
    try:
        # For demonstration, return sample file list
        # In production, this would query the actual job results
        
        if job_id == "test-job-id":
            return {
                "files": [
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
                    },
                    {
                        "name": "src/main.tsx",
                        "type": "typescript-react",
                        "size": 231,
                        "category": "entry-point"
                    },
                    {
                        "name": "index.html",
                        "type": "markup",
                        "size": 362,
                        "category": "template"
                    },
                    {
                        "name": "src/index.css",
                        "type": "stylesheet",
                        "size": 669,
                        "category": "styling"
                    },
                    {
                        "name": "vite.config.ts",
                        "type": "typescript",
                        "size": 179,
                        "category": "configuration"
                    },
                    {
                        "name": "tsconfig.json",
                        "type": "configuration",
                        "size": 561,
                        "category": "configuration"
                    },
                    {
                        "name": "README.md",
                        "type": "documentation",
                        "size": 693,
                        "category": "documentation"
                    }
                ],
                "total_files": 8,
                "total_size": 3897
            }
        
        # For unknown job IDs, return empty list
        return {
            "files": [],
            "message": "Job not found or generation not complete"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get files: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for files API"""
    return {
        "status": "healthy",
        "service": "vibe-coding-files-api",
        "endpoint": "files"
    }

# Vercel handler
def handler(request, response):
    """Vercel handler function"""
    import uvicorn
    return uvicorn.run(app, host="0.0.0.0", port=8000)