from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Dict, Any
import structlog

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)