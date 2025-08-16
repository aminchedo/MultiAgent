from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Import jobs database
import sys
import os
sys.path.append(os.path.dirname(__file__))
from ..generate import jobs_db

async def handler(request: Request):
    # Extract job_id from path
    path_parts = request.url.path.split('/')
    job_id = path_parts[-1] if path_parts else None
    
    if request.method == "GET":
        try:
            if not job_id or job_id not in jobs_db:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Job not found"}
                )
            
            job = jobs_db[job_id]
            return JSONResponse(content=job)
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": str(e)}
            )
    
    return JSONResponse(
        status_code=405,
        content={"error": "Method not allowed"}
    )