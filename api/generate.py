import sys
import os
import asyncio
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    # Import real backend components
    from backend.nlp.language_detector import detect_language, determine_project_type
    from backend.core.workflow import MultiAgentWorkflow
    REAL_BACKEND_AVAILABLE = True
    print("✅ Real backend imported successfully")
except ImportError as e:
    print(f"❌ Real backend import failed: {e}")
    REAL_BACKEND_AVAILABLE = False

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
import json
import uuid
import jwt
from datetime import datetime

app = FastAPI()

# Vercel function configuration
# @vercel/functions
# maxDuration: 60

# Job storage (replace with database)
jobs_db = {}

def verify_token(authorization: str):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(' ')[1]
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'secret'), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/generate")
async def generate_project(request: Request):
    try:
        # Verify authentication
        auth_header = request.headers.get('authorization')
        user = verify_token(auth_header)
        
        body = await request.json()
        description = body.get('description')
        name = body.get('name', 'Generated Project')
        project_type = body.get('project_type', 'web')
        complexity = body.get('complexity', 'simple')
        
        if not description:
            return JSONResponse(
                status_code=400,
                content={"error": "Description is required"}
            )
        
        # Check if real backend is available
        if not REAL_BACKEND_AVAILABLE:
            return JSONResponse({
                "status": "error",
                "message": "Real backend not available - dependencies missing",
                "backend_mode": "mock",
                "suggestion": "Install CrewAI dependencies and restart"
            }, status_code=503)
        
        print(f"🎯 Processing request: {description[:100]}...")
        
        # Use REAL language detection
        detected_language = detect_language(description)
        determined_project_type = determine_project_type(description, detected_language)
        
        print(f"🔍 Language detected: {detected_language}")
        print(f"📋 Project type: {determined_project_type.value}")
        
        # Validate detection results
        if detected_language == "python" and "python" in description.lower():
            print("✅ Python detection validated")
        elif detected_language == "javascript" and any(word in description.lower() for word in ["react", "javascript", "web"]):
            print("✅ JavaScript detection validated")
        
        # Create real workflow
        workflow = MultiAgentWorkflow()
        
        # Execute with enhanced language-specific agents
        result = await workflow.execute({
            'description': description,
            'name': name,
            'language': detected_language,
            'project_type': determined_project_type.value,
            'user_requirements': body
        })
        
        # Validate result contains correct file types
        files = result.get('files', [])
        python_files = [f for f in files if f.get('name', '').endswith('.py')]
        react_files = [f for f in files if 'react' in f.get('content', '').lower() or f.get('name', '').endswith('.jsx')]
        
        print(f"📁 Generated files: {len(files)}")
        print(f"🐍 Python files: {len(python_files)}")
        print(f"⚛️ React files: {len(react_files)}")
        
        # Create job tracking
        job_id = result.get('job_id', str(uuid.uuid4()))
        job = {
            'id': job_id,
            'user_id': user['user_id'],
            'description': description,
            'project_type': determined_project_type.value,
            'complexity': complexity,
            'status': 'completed',
            'progress': 100,
            'current_agent': 'code_generator',
            'files': files,
            'backend_mode': 'real',
            'language_detected': detected_language,
            'created_at': datetime.utcnow().isoformat(),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        jobs_db[job_id] = job
        
        # Return enhanced response
        return JSONResponse({
            "status": "success",
            "backend_mode": "real",
            "language_detected": detected_language,
            "project_type": determined_project_type.value,
            "job_id": job_id,
            "files": files,
            "validation": {
                "total_files": len(files),
                "python_files": len(python_files),
                "react_files": len(react_files),
                "language_match": detected_language in description.lower()
            }
        })
        
    except HTTPException as he:
        return JSONResponse(
            status_code=he.status_code,
            content={"error": he.detail}
        )
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return JSONResponse({
            "status": "error",
            "backend_mode": "real" if REAL_BACKEND_AVAILABLE else "mock",
            "message": str(e),
            "debug_info": {
                "detected_language": locals().get('detected_language', 'unknown'),
                "project_type": locals().get('determined_project_type', 'unknown')
            }
        }, status_code=500)

# Health check with backend status
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "backend_mode": "real" if REAL_BACKEND_AVAILABLE else "mock",
        "dependencies": {
            "crewai": REAL_BACKEND_AVAILABLE,
            "language_detection": REAL_BACKEND_AVAILABLE
        }
    }

# Export for Vercel
def handler(request):
    return app(request)