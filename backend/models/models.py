"""
Pydantic models for API requests, responses, and data validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectType(str, Enum):
    """Project type enumeration."""
    WEB_APP = "web_app"
    API = "api"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    FULLSTACK = "fullstack"


class ComplexityLevel(str, Enum):
    """Complexity level enumeration."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class AgentType(str, Enum):
    """Agent type enumeration."""
    PLANNER = "planner"
    CODE_GENERATOR = "code_generator"
    TESTER = "tester"
    DOC_GENERATOR = "doc_generator"
    REVIEWER = "reviewer"


class MessageType(str, Enum):
    """WebSocket message type enumeration."""
    STATUS = "status"
    LOG = "log"
    AGENT_MESSAGE = "agent_message"
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETION = "completion"


# Request Models
class ProjectGenerationRequest(BaseModel):
    """Request model for project generation."""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(..., min_length=10, max_length=2000, description="Project description")
    project_type: ProjectType = Field(..., description="Type of project to generate")
    languages: List[str] = Field(default=["python"], description="Programming languages to use")
    frameworks: List[str] = Field(default=[], description="Frameworks to include")
    complexity: ComplexityLevel = Field(default=ComplexityLevel.MODERATE, description="Project complexity level")
    features: List[str] = Field(default=[], description="Specific features to include")
    mode: str = Field(default="full", description="Generation mode: 'dry' for planning only, 'full' for complete")
    
    @validator("languages")
    def validate_languages(cls, v):
        if not v:
            return ["python"]
        return v


class CodeExecutionRequest(BaseModel):
    """Request model for code execution."""
    code: str = Field(..., min_length=1, description="Code to execute")
    language: str = Field(..., description="Programming language")
    job_id: Optional[str] = Field(None, description="Associated job ID")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")


class FileUploadRequest(BaseModel):
    """Request model for file upload."""
    filename: str = Field(..., description="Original filename")
    content: str = Field(..., description="File content (base64 encoded for binary files)")
    job_id: str = Field(..., description="Associated job ID")
    path: Optional[str] = Field(None, description="Relative path within project")


class AuthRequest(BaseModel):
    """Request model for authentication."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str = Field(..., description="Refresh token")


# Response Models
class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProjectGenerationResponse(BaseResponse):
    """Response model for project generation."""
    job_id: str = Field(..., description="Unique job identifier")
    estimated_duration: int = Field(..., description="Estimated completion time in seconds")


class JobStatusResponse(BaseResponse):
    """Response model for job status."""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: float = Field(..., ge=0, le=100, description="Completion percentage")
    current_step: str = Field(..., description="Current processing step")
    step_number: int = Field(..., ge=0, description="Current step number")
    total_steps: int = Field(..., ge=0, description="Total number of steps")
    files: List[str] = Field(default=[], description="Generated files list")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class FilePreviewResponse(BaseResponse):
    """Response model for file preview."""
    filename: str = Field(..., description="File name")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="Programming language/syntax")
    size: int = Field(..., description="File size in bytes")


class CodeExecutionResponse(BaseResponse):
    """Response model for code execution."""
    output: str = Field(..., description="Execution output")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    exit_code: int = Field(..., description="Process exit code")


class SystemStatsResponse(BaseResponse):
    """Response model for system statistics."""
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    memory_usage: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    disk_usage: float = Field(..., ge=0, le=100, description="Disk usage percentage")
    active_jobs: int = Field(..., ge=0, description="Number of active jobs")
    total_jobs: int = Field(..., ge=0, description="Total number of jobs")
    avg_response_time: float = Field(..., ge=0, description="Average API response time in ms")
    uptime: float = Field(..., ge=0, description="System uptime in seconds")


class AuthResponse(BaseResponse):
    """Response model for authentication."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TemplateResponse(BaseResponse):
    """Response model for project templates."""
    templates: List[Dict[str, Any]] = Field(..., description="Available project templates")


class JobSummary(BaseModel):
    """Summary model for job listings."""
    job_id: str = Field(..., description="Job identifier")
    name: str = Field(..., description="Project name")
    status: JobStatus = Field(..., description="Job status")
    project_type: ProjectType = Field(..., description="Project type")
    languages: List[str] = Field(..., description="Programming languages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    duration: Optional[float] = Field(None, description="Job duration in seconds")


class JobListResponse(BaseResponse):
    """Response model for job listings."""
    jobs: List[JobSummary] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: MessageType = Field(..., description="Message type")
    job_id: Optional[str] = Field(None, description="Associated job ID")
    agent: Optional[str] = Field(None, description="Agent name")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class ProgressUpdate(BaseModel):
    """Progress update model."""
    job_id: str = Field(..., description="Job identifier")
    progress: float = Field(..., ge=0, le=100, description="Completion percentage")
    current_step: str = Field(..., description="Current step description")
    step_number: int = Field(..., ge=0, description="Current step number")
    total_steps: int = Field(..., ge=0, description="Total number of steps")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


# Database Models (for SQLAlchemy)
class ProjectFile(BaseModel):
    """Model for project files."""
    id: Optional[int] = None
    job_id: str = Field(..., description="Associated job ID")
    filename: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="Programming language")
    size: int = Field(..., description="File size in bytes")
    hash: str = Field(..., description="File content hash")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LogEntry(BaseModel):
    """Model for log entries."""
    id: Optional[int] = None
    job_id: str = Field(..., description="Associated job ID")
    agent: str = Field(..., description="Agent name")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentTask(BaseModel):
    """Model for agent tasks."""
    id: Optional[int] = None
    job_id: str = Field(..., description="Associated job ID")
    agent_type: AgentType = Field(..., description="Agent type")
    task_name: str = Field(..., description="Task name")
    status: JobStatus = Field(..., description="Task status")
    input_data: Dict[str, Any] = Field(..., description="Task input data")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Task output data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Utility functions
def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())


def generate_task_id() -> str:
    """Generate a unique task ID."""
    return str(uuid.uuid4())