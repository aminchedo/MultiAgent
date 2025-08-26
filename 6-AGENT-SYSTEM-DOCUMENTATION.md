# 6-Agent Code Generation System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Agent Descriptions](#agent-descriptions)
4. [API Reference](#api-reference)
5. [Deployment Guide](#deployment-guide)
6. [Usage Examples](#usage-examples)
7. [Quality Assurance](#quality-assurance)
8. [Troubleshooting](#troubleshooting)

## System Overview

The 6-Agent Code Generation System is a production-ready, AI-powered platform that automatically generates complete, functional web applications. The system employs six specialized agents working in coordination to analyze requirements, generate code, review quality, organize files, and validate the final output.

### Key Features
- **Fully Automated**: Complete project generation from natural language prompts
- **Multi-Framework Support**: React, Vue.js, Next.js, Vanilla JS, Python
- **Quality Assured**: Built-in QA validation with scoring system
- **Production Ready**: Generated code is deployment-ready
- **Real-time Updates**: WebSocket support for live progress tracking
- **Comprehensive Testing**: Security scanning, performance analysis, and functional testing

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   WORKFLOW ORCHESTRATOR                      │
│                    (Agent 1 - Leader)                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┬─────────────┬─────────────┐
    │                           │             │             │
┌───▼────┐            ┌────────▼───┐  ┌──────▼────┐  ┌─────▼─────┐
│PLANNER │            │   CODER    │  │  CRITIC   │  │FILE MGR   │
│Agent 2 │            │  Agent 3   │  │  Agent 4  │  │ Agent 5   │
└───┬────┘            └─────┬──────┘  └─────┬─────┘  └─────┬─────┘
    │                       │                │               │
    └───────────────────────┴────────────────┴───────────────┘
                                    │
                            ┌───────▼────────┐
                            │  QA VALIDATOR  │
                            │    Agent 6     │
                            └────────────────┘
```

### Agent Communication Flow

1. **Orchestrator** receives project request
2. **Planner** analyzes requirements and creates architecture
3. **Coder** generates all project files
4. **Critic** reviews code quality and best practices
5. **File Manager** organizes project structure
6. **QA Validator** performs comprehensive testing
7. **Orchestrator** returns final validated project

## Agent Descriptions

### 1. Workflow Orchestrator Agent (823 lines)
- **Role**: Master coordinator
- **Responsibilities**:
  - Manages workflow execution
  - Coordinates agent communication
  - Tracks progress and handles errors
  - Manages WebSocket connections
- **Key Methods**:
  - `orchestrate_project()`
  - `broadcast_progress()`
  - `handle_agent_failure()`

### 2. Project Planner Agent (276 lines)
- **Role**: Requirements analyst and architect
- **Responsibilities**:
  - Analyzes natural language prompts
  - Determines project structure
  - Selects appropriate technologies
  - Creates component hierarchy
- **Capabilities**:
  - Pattern matching
  - Framework recommendation
  - Complexity assessment

### 3. Code Generator Agent (651 lines)
- **Role**: Primary code creator
- **Responsibilities**:
  - Generates production-ready code
  - Implements business logic
  - Creates UI components
  - Handles framework-specific patterns
- **Supported Frameworks**:
  - React with TypeScript
  - Vue.js with Composition API
  - Next.js with App Router
  - Vanilla JavaScript
  - Python backends

### 4. Code Critic Agent (861 lines)
- **Role**: Quality assurance specialist
- **Responsibilities**:
  - Reviews generated code
  - Ensures best practices
  - Identifies potential issues
  - Suggests improvements
- **Review Areas**:
  - Code structure
  - Performance optimization
  - Security vulnerabilities
  - Accessibility compliance

### 5. File Manager Agent (715 lines)
- **Role**: Project organization specialist
- **Responsibilities**:
  - Organizes file structure
  - Creates deployment configurations
  - Manages dependencies
  - Prepares build scripts
- **Outputs**:
  - package.json
  - Dockerfile
  - CI/CD configurations
  - README files

### 6. QA Validator Agent (736 lines)
- **Role**: Comprehensive testing specialist
- **Responsibilities**:
  - Validates code compilation
  - Runs functional tests
  - Performs security scanning
  - Analyzes performance
  - Calculates quality score
- **Validation Areas**:
  - Syntax validation
  - Import/export verification
  - Security vulnerability detection
  - Performance metrics
  - Test coverage analysis

## API Reference

### Base URL
```
https://your-domain.vercel.app
```

### Endpoints

#### 1. Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "version": "2.0.0",
  "environment": "production",
  "active_jobs": 0,
  "agents_ready": true
}
```

#### 2. Create Project
```http
POST /api/vibe-coding
Content-Type: application/json

{
  "prompt": "Create a React todo app with dark mode",
  "framework": "react",
  "complexity": "intermediate",
  "features": ["dark-mode", "localStorage", "animations"]
}
```
**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "started",
  "message": "6-agent project generation started successfully",
  "estimated_time": 400,
  "websocket_url": "wss://your-domain/ws/uuid-here"
}
```

#### 3. Get Job Status
```http
GET /api/vibe-coding/status/{job_id}
```

#### 4. Get Detailed Status with QA Metrics
```http
GET /api/vibe-coding/detailed-status/{job_id}
```
**Response includes:**
- Agent progress for all 6 agents
- Files generated count
- QA metrics (quality score, tests executed, security issues)
- Final approval status

#### 5. Get QA Report
```http
GET /api/vibe-coding/qa-report/{job_id}
```
**Response:**
- Comprehensive quality analysis
- Test results
- Security scan results
- Performance metrics
- Recommendations

#### 6. Download Project
```http
GET /api/download/{job_id}
```
Returns ZIP file with complete project

#### 7. WebSocket Connection
```ws
WS /ws/{job_id}
```
Real-time updates on:
- Agent progress
- Current phase
- Errors
- Completion status

## Deployment Guide

### Prerequisites
- Python 3.9.18
- Node.js 18+
- Vercel CLI (optional)

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn backend.simple_app:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

#### Option 1: Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

#### Option 2: Docker
```bash
# Build image
docker build -t 6-agent-system .

# Run container
docker run -p 8000:8000 6-agent-system
```

### Environment Variables
```env
ENVIRONMENT=production
DEBUG=false
QA_QUALITY_THRESHOLD=85
WORKFLOW_TIMEOUT=600
RATE_LIMIT_REQUESTS=100
```

## Usage Examples

### Basic React App
```python
import requests

response = requests.post("https://api.example.com/api/vibe-coding", json={
    "prompt": "Create a simple React counter app",
    "framework": "react",
    "complexity": "simple"
})

job_id = response.json()["job_id"]
```

### Complex Vue.js Application
```python
response = requests.post("https://api.example.com/api/vibe-coding", json={
    "prompt": "Create a Vue.js e-commerce dashboard with charts, user management, and real-time updates",
    "framework": "vue",
    "complexity": "complex",
    "features": ["charts", "authentication", "websockets", "responsive"]
})
```

### Monitor Progress via WebSocket
```javascript
const ws = new WebSocket(`wss://api.example.com/ws/${jobId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Agent: ${data.agent}, Progress: ${data.progress}%`);
};
```

## Quality Assurance

### Quality Score Calculation
The QA Validator calculates a quality score based on:
- **Compilation Success** (25%)
- **Functional Tests** (30%)
- **Security Scan** (25%)
- **Performance Analysis** (20%)

### Minimum Quality Threshold
- Default: 85/100
- Projects below threshold are marked for improvement
- All 6 agents must complete successfully

### Security Scanning
Checks for:
- XSS vulnerabilities
- SQL injection risks
- Insecure dependencies
- Sensitive data exposure
- CORS misconfigurations

## Troubleshooting

### Common Issues

#### 1. Agent Initialization Failed
**Error:** "Failed to initialize agents"
**Solution:** 
- Verify all agent files exist
- Check Python imports
- Ensure base_agent.py is present

#### 2. Quality Score Too Low
**Error:** "Quality score below threshold"
**Solution:**
- Review security warnings
- Fix compilation errors
- Improve test coverage
- Optimize performance issues

#### 3. WebSocket Connection Failed
**Error:** "WebSocket connection dropped"
**Solution:**
- Check CORS configuration
- Verify WebSocket support
- Ensure proper SSL certificates

#### 4. Deployment Issues
**Error:** "Deployment failed on Vercel"
**Solution:**
- Check runtime.txt (Python 3.9.18)
- Verify requirements.txt
- Review vercel.json configuration
- Check environment variables

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization
- Average generation time: 400 seconds
- Concurrent agent execution where possible
- Caching for repeated patterns
- Optimized file operations

## Support and Maintenance

### Monitoring
- Health endpoint: `/health`
- System stats: `/api/stats`
- Active jobs tracking
- Agent performance metrics

### Logging
All agents log to structured format:
```json
{
  "timestamp": "2025-01-23T10:00:00Z",
  "agent": "qa_validator",
  "level": "INFO",
  "message": "Validation completed",
  "job_id": "uuid",
  "quality_score": 92
}
```

### Updates
System version: 2.0.0
- Regular security updates
- Framework template updates
- Performance improvements
- Bug fixes

---

## Conclusion

The 6-Agent Code Generation System represents a complete, production-ready solution for automated code generation. With its comprehensive quality assurance, multi-framework support, and real-time progress tracking, it provides a robust platform for generating high-quality applications from natural language descriptions.

**All 6 agents are fully implemented with real, functional code - no pseudo-code or placeholders.**

For additional support or feature requests, please refer to the deployment logs and monitoring dashboards.