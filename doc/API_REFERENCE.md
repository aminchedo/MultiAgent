# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

All API endpoints (except health checks) require JWT authentication.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Authentication successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 86400
}
```

### Using Authentication

Include the JWT token in the Authorization header:

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

## Project Generation

### Generate Project

Create a new project generation job.

```http
POST /api/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "project_type": "web_app",
  "languages": ["python", "javascript"],
  "frameworks": ["fastapi", "react"],
  "complexity": "moderate",
  "features": ["authentication", "database"],
  "mode": "full"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Project name |
| `description` | string | Yes | Detailed project description |
| `project_type` | enum | Yes | Type of project to generate |
| `languages` | array | No | Programming languages (default: ["python"]) |
| `frameworks` | array | No | Frameworks to use |
| `complexity` | enum | No | Project complexity (default: "moderate") |
| `features` | array | No | Specific features to include |
| `mode` | enum | No | Generation mode (default: "full") |

**Project Types:**
- `web_app`: Web application
- `api`: API service
- `mobile_app`: Mobile application
- `desktop_app`: Desktop application
- `cli_tool`: Command-line tool
- `library`: Software library
- `microservice`: Microservice
- `fullstack`: Full-stack application

**Complexity Levels:**
- `simple`: Basic functionality
- `moderate`: Standard features
- `complex`: Advanced functionality
- `enterprise`: Enterprise-scale

**Modes:**
- `full`: Complete project generation
- `dry`: Planning only

**Response:**
```json
{
  "success": true,
  "message": "Project generation started successfully",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "estimated_duration": 180
}
```

### Get Job Status

Check the status of a project generation job.

```http
GET /status/{job_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Job status retrieved successfully",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 65.5,
  "current_step": "Generating code files",
  "step_number": 4,
  "total_steps": 8,
  "files": [
    "src/app.py",
    "src/models.py",
    "tests/test_app.py"
  ],
  "error_message": null,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:30Z",
  "estimated_completion": "2024-01-01T12:08:00Z"
}
```

**Status Values:**
- `pending`: Job queued
- `running`: Job in progress
- `completed`: Job finished successfully
- `failed`: Job failed
- `cancelled`: Job cancelled

### Download Project

Download the generated project as a ZIP file.

```http
GET /download/{job_id}
Authorization: Bearer <token>
```

**Response:** ZIP file download

### Preview File

Get the content of a specific generated file.

```http
GET /preview/{job_id}/{filename:path}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "File retrieved successfully",
  "filename": "app.py",
  "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
  "language": "python",
  "size": 156
}
```

## Code Execution

### Execute Code

Execute code in a sandboxed environment.

```http
POST /api/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "print('Hello, World!')",
  "language": "python",
  "timeout": 30
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Code to execute |
| `language` | string | Yes | Programming language |
| `timeout` | integer | No | Execution timeout in seconds (default: 30) |

**Supported Languages:**
- `python`
- `javascript`

**Response:**
```json
{
  "success": true,
  "message": "Code executed successfully",
  "output": "Hello, World!\n",
  "error": null,
  "execution_time": 0.125,
  "exit_code": 0
}
```

## File Management

### Upload File

Upload a file to modify an existing project.

```http
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "file": <file>,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "path": "src/custom.py"
}
```

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully"
}
```

## Templates

### Get Templates

Retrieve available project templates.

```http
GET /api/templates
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Templates retrieved successfully",
  "templates": [
    {
      "id": "react_app",
      "name": "React Web Application",
      "description": "Modern React application with TypeScript",
      "languages": ["typescript", "javascript"],
      "frameworks": ["react", "vite"],
      "complexity": "moderate"
    }
  ]
}
```

## System Information

### System Statistics

Get system performance metrics.

```http
GET /api/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "System statistics retrieved successfully",
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 23.4,
  "active_jobs": 3,
  "total_jobs": 142,
  "avg_response_time": 150.0,
  "uptime": 86400
}
```

### Health Checks

Basic health check:

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1704110400.0,
  "version": "1.0.0",
  "service": "Multi-Agent Code Generation System"
}
```

Readiness check (includes database):

```http
GET /health/ready
```

**Response:**
```json
{
  "status": "ready",
  "timestamp": 1704110400.0,
  "version": "1.0.0",
  "database": "connected",
  "total_jobs": 142
}
```

Liveness check:

```http
GET /health/live
```

**Response:**
```json
{
  "status": "alive",
  "timestamp": 1704110400.0,
  "version": "1.0.0"
}
```

## Administration

### List Recent Jobs

Get a list of recent jobs with pagination.

```http
GET /admin/jobs?page=1&per_page=50&status=completed
Authorization: Bearer <token>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 50, max: 100) |
| `status` | string | No | Filter by job status |

**Response:**
```json
{
  "success": true,
  "message": "Jobs retrieved successfully",
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My Web App",
      "status": "completed",
      "project_type": "web_app",
      "languages": ["python", "javascript"],
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:08:00Z",
      "duration": 480.5
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

## WebSocket API

Connect to real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?job_id={job_id}');
```

### Message Types

#### Status Message
```json
{
  "type": "status",
  "content": "Connected to Multi-Agent Code Generation System",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Agent Message
```json
{
  "type": "agent_message",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent": "PlannerAgent",
  "content": "Starting project analysis...",
  "metadata": {
    "step": "planning",
    "progress": 10
  },
  "timestamp": "2024-01-01T12:00:30Z"
}
```

#### Log Entry
```json
{
  "type": "log",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "level": "INFO",
  "content": "Code generation phase started",
  "timestamp": "2024-01-01T12:02:00Z"
}
```

#### Progress Update
```json
{
  "type": "progress",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "progress": 75.5,
    "current_step": "Running tests",
    "step_number": 6,
    "total_steps": 8
  },
  "timestamp": "2024-01-01T12:05:00Z"
}
```

#### Error Message
```json
{
  "type": "error",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Code generation failed: Invalid syntax in template",
  "metadata": {
    "error_code": "SYNTAX_ERROR",
    "agent": "CodeGeneratorAgent"
  },
  "timestamp": "2024-01-01T12:03:00Z"
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "success": false,
  "message": "Error description",
  "timestamp": 1704110400.0,
  "status_code": 400
}
```

### Common HTTP Status Codes

- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Missing or invalid authentication
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `422`: Unprocessable Entity - Validation error
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error
- `503`: Service Unavailable - Service temporarily unavailable

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Default**: 100 requests per hour per IP
- **Authentication**: 10 requests per minute
- **Project Generation**: 5 requests per minute
- **Code Execution**: 20 requests per minute

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704114000
```

## SDK Examples

### Python

```python
import requests

class MultiAgentClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = self._login(username, password)
    
    def _login(self, username, password):
        response = requests.post(f"{self.base_url}/auth/login", json={
            "username": username,
            "password": password
        })
        return response.json()["access_token"]
    
    def generate_project(self, project_data):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=project_data,
            headers=headers
        )
        return response.json()
    
    def get_status(self, job_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/status/{job_id}",
            headers=headers
        )
        return response.json()

# Usage
client = MultiAgentClient("http://localhost:8000", "admin", "admin")
job = client.generate_project({
    "name": "My Project",
    "description": "A web application",
    "project_type": "web_app"
})
print(f"Job ID: {job['job_id']}")
```

### JavaScript

```javascript
class MultiAgentClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.token = null;
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await response.json();
        this.token = data.access_token;
        return data;
    }
    
    async generateProject(projectData) {
        const response = await fetch(`${this.baseUrl}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify(projectData)
        });
        return response.json();
    }
    
    async getStatus(jobId) {
        const response = await fetch(`${this.baseUrl}/status/${jobId}`, {
            headers: {'Authorization': `Bearer ${this.token}`}
        });
        return response.json();
    }
}

// Usage
const client = new MultiAgentClient('http://localhost:8000');
await client.login('admin', 'admin');
const job = await client.generateProject({
    name: 'My Project',
    description: 'A web application',
    project_type: 'web_app'
});
console.log(`Job ID: ${job.job_id}`);
```