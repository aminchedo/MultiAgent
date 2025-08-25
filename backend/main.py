"""
Main FastAPI application with Vibe Agents integration.

This is the main backend application that integrates with the Vibe Agents system
for intelligent code generation and project management.
"""

import asyncio
import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import the Vibe Agents
import sys
sys.path.append('/workspace')

from agents.vibe_workflow_orchestrator import VibeWorkflowOrchestratorAgent


# Pydantic models for API requests/responses
class VibeRequest(BaseModel):
    vibe_prompt: str = Field(..., min_length=10, max_length=5000, description="Natural language description of the project")
    project_type: str = Field(default="web_app", description="Type of project (web_app, api, mobile_app, dashboard, etc.)")
    complexity: str = Field(default="moderate", description="Project complexity (simple, moderate, complex, enterprise)")
    project_id: Optional[int] = Field(default=None, description="Optional project ID")


class VibeResponse(BaseModel):
    project_id: int
    status: str
    message: str
    workflow_id: Optional[str] = None


class ProjectStatusResponse(BaseModel):
    project_id: int
    status: str
    progress: float
    current_stage: str
    workflow_status: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    database_status: str
    agents_status: str


class MetricsResponse(BaseModel):
    total_projects: int
    successful_projects: int
    failed_projects: int
    average_processing_time: float
    agent_metrics: Dict[str, Any]


# Database initialization
def init_database():
    """Initialize SQLite database with required tables."""
    
    db_path = Path("/workspace/backend/vibe_projects.db")
    
    # Create database file if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create vibe_projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vibe_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vibe_prompt TEXT NOT NULL,
            project_type TEXT NOT NULL,
            complexity TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            workflow_id TEXT,
            workflow_status TEXT,
            current_stage TEXT,
            progress REAL DEFAULT 0.0,
            files_generated INTEGER DEFAULT 0,
            final_quality_score REAL DEFAULT 0.0,
            production_ready BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            processing_time REAL,
            deliverables TEXT,  -- JSON string of deliverables
            metadata TEXT       -- JSON string of additional metadata
        )
    ''')
    
    # Create agent_metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            agent_name TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            execution_time REAL NOT NULL,
            response_time REAL NOT NULL,
            quality_score REAL,
            retry_count INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,  -- JSON string of additional data
            FOREIGN KEY (project_id) REFERENCES vibe_projects(id)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vibe_projects_status ON vibe_projects(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vibe_projects_created_at ON vibe_projects(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_metrics_project_id ON agent_metrics(project_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_name ON agent_metrics(agent_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_metrics_created_at ON agent_metrics(created_at)')
    
    conn.commit()
    conn.close()


# Database helper functions
def get_db_connection():
    """Get database connection."""
    db_path = Path("/workspace/backend/vibe_projects.db")
    return sqlite3.connect(str(db_path), check_same_thread=False)


def create_project_record(vibe_prompt: str, project_type: str, complexity: str) -> int:
    """Create a new project record and return project ID."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO vibe_projects (vibe_prompt, project_type, complexity, status)
        VALUES (?, ?, ?, 'pending')
    ''', (vibe_prompt, project_type, complexity))
    
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return project_id


def update_project_status(project_id: int, **updates):
    """Update project status and metadata."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build dynamic update query
    set_clause = []
    values = []
    
    for field, value in updates.items():
        if field in ['status', 'workflow_id', 'workflow_status', 'current_stage', 'progress', 
                    'files_generated', 'final_quality_score', 'production_ready', 'error_message',
                    'completed_at', 'processing_time', 'deliverables', 'metadata']:
            set_clause.append(f"{field} = ?")
            if field in ['deliverables', 'metadata'] and isinstance(value, (dict, list)):
                values.append(json.dumps(value))
            else:
                values.append(value)
    
    if set_clause:
        set_clause.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE vibe_projects SET {', '.join(set_clause)} WHERE id = ?"
        values.append(project_id)
        
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()


def get_project_status(project_id: int) -> Optional[Dict[str, Any]]:
    """Get project status by ID."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, vibe_prompt, project_type, complexity, status, workflow_id, workflow_status,
               current_stage, progress, files_generated, final_quality_score, production_ready,
               error_message, created_at, updated_at, completed_at, processing_time,
               deliverables, metadata
        FROM vibe_projects WHERE id = ?
    ''', (project_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        'id': row[0],
        'vibe_prompt': row[1],
        'project_type': row[2],
        'complexity': row[3],
        'status': row[4],
        'workflow_id': row[5],
        'workflow_status': row[6],
        'current_stage': row[7],
        'progress': row[8],
        'files_generated': row[9],
        'final_quality_score': row[10],
        'production_ready': bool(row[11]),
        'error_message': row[12],
        'created_at': row[13],
        'updated_at': row[14],
        'completed_at': row[15],
        'processing_time': row[16],
        'deliverables': json.loads(row[17]) if row[17] else None,
        'metadata': json.loads(row[18]) if row[18] else None
    }


def record_agent_metric(project_id: int, agent_name: str, operation_type: str, 
                       success: bool, execution_time: float, response_time: float,
                       quality_score: Optional[float] = None, retry_count: int = 0,
                       error_message: Optional[str] = None, metadata: Optional[Dict] = None):
    """Record agent performance metrics."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO agent_metrics (
            project_id, agent_name, operation_type, success, execution_time,
            response_time, quality_score, retry_count, error_message, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        project_id, agent_name, operation_type, success, execution_time,
        response_time, quality_score, retry_count, error_message,
        json.dumps(metadata) if metadata else None
    ))
    
    conn.commit()
    conn.close()


# Initialize FastAPI app
app = FastAPI(
    title="Vibe Coding Platform",
    version="1.0.0",
    description="AI-powered code generation platform using Vibe Agents"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    print("Database initialized successfully")

# Global orchestrator instance
orchestrator = VibeWorkflowOrchestratorAgent()

# Background task for processing vibe requests
async def process_vibe_request(project_id: int, vibe_request: VibeRequest):
    """Background task to process vibe coding request."""
    
    start_time = time.time()
    
    try:
        # Update project status to running
        update_project_status(
            project_id,
            status='running',
            current_stage='initialization'
        )
        
        # Prepare request for orchestrator
        orchestrator_request = {
            "vibe_prompt": vibe_request.vibe_prompt,
            "project_type": vibe_request.project_type,
            "complexity": vibe_request.complexity,
            "project_id": project_id
        }
        
        # Execute the workflow
        result = await orchestrator.orchestrate_vibe_project(orchestrator_request)
        
        processing_time = time.time() - start_time
        
        if result.get("workflow_status") == "success":
            # Update project with successful result
            update_project_status(
                project_id,
                status='completed',
                workflow_id=result.get('workflow_id'),
                workflow_status='success',
                current_stage='completed',
                progress=100.0,
                files_generated=result.get('files_generated', 0),
                final_quality_score=result.get('final_quality_score', 0),
                production_ready=result.get('production_ready', False),
                completed_at=datetime.utcnow().isoformat(),
                processing_time=processing_time,
                deliverables=result.get('deliverables'),
                metadata=result.get('metadata')
            )
            
            # Record successful metrics for each agent involved
            workflow_state = result.get('workflow_state', {})
            for stage_name, stage_result in workflow_state.get('stage_results', {}).items():
                agent_name = _get_agent_name_for_stage(stage_name)
                quality_score = _extract_quality_score(stage_result)
                retry_count = workflow_state.get('retry_counts', {}).get(stage_name, 0)
                
                record_agent_metric(
                    project_id=project_id,
                    agent_name=agent_name,
                    operation_type=stage_name,
                    success=True,
                    execution_time=processing_time / len(workflow_state.get('completed_stages', [1])),
                    response_time=processing_time,
                    quality_score=quality_score,
                    retry_count=retry_count,
                    metadata={"stage_result": "success"}
                )
                
        else:
            # Update project with failure
            error_message = result.get('error', 'Unknown error occurred')
            update_project_status(
                project_id,
                status='failed',
                workflow_id=result.get('workflow_id'),
                workflow_status='failed',
                error_message=error_message,
                processing_time=processing_time,
                metadata=result.get('metadata')
            )
            
            # Record failure metrics
            record_agent_metric(
                project_id=project_id,
                agent_name='VibeWorkflowOrchestratorAgent',
                operation_type='full_workflow',
                success=False,
                execution_time=processing_time,
                response_time=processing_time,
                error_message=error_message,
                metadata={"workflow_result": "failed"}
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Unexpected error: {str(e)}"
        
        # Update project with error
        update_project_status(
            project_id,
            status='failed',
            error_message=error_message,
            processing_time=processing_time
        )
        
        # Record error metrics
        record_agent_metric(
            project_id=project_id,
            agent_name='VibeWorkflowOrchestratorAgent',
            operation_type='full_workflow',
            success=False,
            execution_time=processing_time,
            response_time=processing_time,
            error_message=error_message,
            metadata={"error_type": "unexpected_error"}
        )


def _get_agent_name_for_stage(stage_name: str) -> str:
    """Map stage name to agent name."""
    mapping = {
        'planning': 'VibePlannerAgent',
        'coding': 'VibeCoderAgent', 
        'review': 'VibeCriticAgent',
        'organization': 'VibeFileManagerAgent',
        'final_review': 'VibeCriticAgent'
    }
    return mapping.get(stage_name, 'UnknownAgent')


def _extract_quality_score(stage_result: Dict[str, Any]) -> Optional[float]:
    """Extract quality score from stage result."""
    if isinstance(stage_result, dict):
        return stage_result.get('overall_score') or stage_result.get('score') or stage_result.get('metrics', {}).get('organization_score')
    return None


# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    
    # Check database connectivity
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Check agents status (basic instantiation test)
    try:
        test_orchestrator = VibeWorkflowOrchestratorAgent()
        agents_status = "healthy"
    except Exception:
        agents_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" and agents_status == "healthy" else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        database_status=db_status,
        agents_status=agents_status
    )


@app.post("/api/vibe-coding", response_model=VibeResponse)
async def create_vibe_project(vibe_request: VibeRequest, background_tasks: BackgroundTasks):
    """Create a new vibe coding project."""
    
    try:
        # Create project record
        project_id = create_project_record(
            vibe_request.vibe_prompt,
            vibe_request.project_type,
            vibe_request.complexity
        )
        
        # Start background processing
        background_tasks.add_task(process_vibe_request, project_id, vibe_request)
        
        return VibeResponse(
            project_id=project_id,
            status="accepted",
            message="Vibe coding request accepted and queued for processing"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@app.get("/api/projects/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status_endpoint(project_id: int):
    """Get the status of a vibe coding project."""
    
    project = get_project_status(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectStatusResponse(
        project_id=project['id'],
        status=project['status'],
        progress=project['progress'],
        current_stage=project['current_stage'] or 'pending',
        workflow_status=project['workflow_status'] or 'pending',
        error=project['error_message']
    )


@app.get("/api/projects/{project_id}")
async def get_project_details(project_id: int):
    """Get complete project details including deliverables."""
    
    project = get_project_status(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@app.get("/api/projects/{project_id}/files")
async def get_project_files(project_id: int):
    """Get project files and structure."""
    
    project = get_project_status(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Project not completed yet")
    
    deliverables = project.get('deliverables', {})
    
    return {
        "project_id": project_id,
        "files": deliverables.get('project_files', []),
        "structure": deliverables.get('project_structure', {}),
        "documentation": deliverables.get('documentation', {}),
        "setup_instructions": deliverables.get('setup_instructions', [])
    }


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get platform and agent metrics."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get project metrics
    cursor.execute("SELECT COUNT(*) FROM vibe_projects")
    total_projects = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vibe_projects WHERE status = 'completed'")
    successful_projects = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vibe_projects WHERE status = 'failed'")
    failed_projects = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(processing_time) FROM vibe_projects WHERE processing_time IS NOT NULL")
    avg_processing_time = cursor.fetchone()[0] or 0.0
    
    # Get agent metrics
    cursor.execute('''
        SELECT agent_name, 
               COUNT(*) as total_operations,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_operations,
               AVG(execution_time) as avg_execution_time,
               AVG(response_time) as avg_response_time,
               AVG(quality_score) as avg_quality_score
        FROM agent_metrics 
        GROUP BY agent_name
    ''')
    
    agent_metrics = {}
    for row in cursor.fetchall():
        agent_name, total_ops, successful_ops, avg_exec_time, avg_resp_time, avg_quality = row
        agent_metrics[agent_name] = {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "success_rate": (successful_ops / total_ops * 100) if total_ops > 0 else 0,
            "average_execution_time": avg_exec_time or 0,
            "average_response_time": avg_resp_time or 0,
            "average_quality_score": avg_quality or 0
        }
    
    conn.close()
    
    return MetricsResponse(
        total_projects=total_projects,
        successful_projects=successful_projects,
        failed_projects=failed_projects,
        average_processing_time=avg_processing_time,
        agent_metrics=agent_metrics
    )


@app.get("/api/projects")
async def list_projects(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List projects with optional filtering."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    where_clause = ""
    params = []
    
    if status:
        where_clause = "WHERE status = ?"
        params.append(status)
    
    query = f'''
        SELECT id, vibe_prompt, project_type, complexity, status, workflow_status,
               progress, files_generated, final_quality_score, production_ready,
               created_at, updated_at, completed_at
        FROM vibe_projects 
        {where_clause}
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    '''
    
    params.extend([limit, offset])
    cursor.execute(query, params)
    
    projects = []
    for row in cursor.fetchall():
        projects.append({
            'id': row[0],
            'vibe_prompt': row[1][:100] + '...' if len(row[1]) > 100 else row[1],  # Truncate for list view
            'project_type': row[2],
            'complexity': row[3],
            'status': row[4],
            'workflow_status': row[5],
            'progress': row[6],
            'files_generated': row[7],
            'final_quality_score': row[8],
            'production_ready': bool(row[9]),
            'created_at': row[10],
            'updated_at': row[11],
            'completed_at': row[12]
        })
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM vibe_projects {where_clause}"
    cursor.execute(count_query, params[:-2] if status else [])
    total_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "projects": projects,
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Vibe Coding Platform API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )