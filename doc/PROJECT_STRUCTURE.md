# Project Structure Documentation

## Multi-Agent Code Generation System - Modular Architecture

This document describes the new modular, scalable, and secure project structure of the Multi-Agent Code Generation System.

## 📁 Project Overview

```
/workspace/
├── main.py                 # Main entry point for the application
├── requirements.txt        # Python dependencies
├── pytest.ini            # Test configuration
├── 
├── backend/               # Backend modules (FastAPI + agents)
│   ├── __init__.py
│   ├── api/               # API layer
│   │   ├── __init__.py
│   │   └── routes.py      # FastAPI routes and endpoints
│   ├── core/              # Core application logic
│   │   ├── __init__.py
│   │   └── app.py         # FastAPI application setup
│   ├── agents/            # Multi-agent system
│   │   ├── __init__.py
│   │   └── agents.py      # CrewAI agents implementation
│   ├── database/          # Database layer
│   │   ├── __init__.py
│   │   └── db.py          # Database models and operations
│   ├── models/            # Data models
│   │   ├── __init__.py
│   │   └── models.py      # Pydantic models and schemas
│   ├── auth/              # Authentication & authorization
│   │   └── __init__.py
│   └── utils/             # Utility functions
│       ├── __init__.py
│       └── injection.py   # System setup utilities
│
├── frontend/              # Frontend assets and pages
│   ├── assets/            # Static assets
│   │   ├── favicon.ico
│   │   └── index.html     # Main frontend assets
│   ├── components/        # Reusable UI components
│   ├── pages/             # Frontend pages
│   │   ├── front.html
│   │   ├── front_optimized.html
│   │   ├── index.html
│   │   └── test_enhanced_ui.html
│   └── styles/            # CSS and styling
│
├── config/                # Configuration management
│   ├── __init__.py
│   ├── config.py          # Configuration classes
│   └── config.json        # Application settings
│
├── tests/                 # Test suite
│   ├── backend.test.py    # Backend tests
│   └── frontend.test.html # Frontend tests
│
├── docs/                  # Documentation
│   ├── PROJECT_STRUCTURE.md
│   ├── API_REFERENCE.md
│   ├── README.md
│   ├── COMMIT_SUMMARY.md
│   ├── UI_IMPROVEMENTS_SUMMARY.md
│   └── LAUNCH_SCRIPTS_README.md
│
├── deployment/            # Deployment configurations
│   ├── docker/            # Docker configurations
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.override.yml
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   └── nginx.conf
│   └── scripts/           # Deployment scripts
│       ├── launch.sh
│       ├── launch.bat
│       ├── launch_app.py
│       └── complete_launcher.py
│
└── temp/                  # Temporary files (moved from root)
    ├── __pycache__/       # Python cache files
    ├── multiagent.db      # Old database file
    ├── app.log            # Log files
    ├── back.py            # Old monolithic backend
    └── *.backup           # Backup files
```

## 🏗️ Architecture Principles

### 1. Modular Design
- **Separation of Concerns**: Each module has a single responsibility
- **Loose Coupling**: Modules communicate through well-defined interfaces
- **High Cohesion**: Related functionality is grouped together

### 2. Security
- **Authentication Module**: Dedicated auth layer for JWT and security
- **Input Validation**: Pydantic models for request/response validation
- **Environment Configuration**: Secure configuration management

### 3. Scalability
- **Microservice Ready**: Modular structure enables easy service separation
- **Async/Await**: FastAPI with async support for high concurrency
- **Database Abstraction**: Clean database layer for easy scaling

### 4. Maintainability
- **Clear Structure**: Intuitive directory organization
- **Documentation**: Comprehensive docs for each module
- **Testing**: Isolated test suites for each component

## 🚀 Module Descriptions

### Backend Modules

#### `backend/core/`
- **Purpose**: Core FastAPI application setup and configuration
- **Key Files**: `app.py` - Main FastAPI app with middleware and health checks

#### `backend/api/`
- **Purpose**: REST API endpoints and routing
- **Key Files**: `routes.py` - All API routes, WebSocket endpoints, and authentication

#### `backend/agents/`
- **Purpose**: Multi-agent AI system using CrewAI
- **Key Files**: `agents.py` - Planner, Coder, Tester, and Documentation agents

#### `backend/database/`
- **Purpose**: Database models, connections, and operations
- **Key Files**: `db.py` - SQLAlchemy models, Redis cache, and database manager

#### `backend/models/`
- **Purpose**: Data models and schemas
- **Key Files**: `models.py` - Pydantic models for request/response validation

#### `backend/auth/`
- **Purpose**: Authentication and authorization (ready for future expansion)
- **Usage**: JWT tokens, user management, role-based access control

#### `backend/utils/`
- **Purpose**: Utility functions and helpers
- **Key Files**: `injection.py` - System setup and dependency injection utilities

### Frontend Structure

#### `frontend/pages/`
- **Purpose**: Complete HTML pages and user interfaces
- **Key Files**: 
  - `front_optimized.html` - Main production UI
  - `index.html` - Landing page
  - `test_enhanced_ui.html` - Testing interface

#### `frontend/assets/`
- **Purpose**: Static assets like images, icons, and shared resources
- **Key Files**: `favicon.ico`, shared HTML components

#### `frontend/components/`
- **Purpose**: Reusable UI components (ready for future modularization)

#### `frontend/styles/`
- **Purpose**: CSS files and styling resources (ready for future expansion)

### Configuration

#### `config/`
- **Purpose**: Centralized configuration management
- **Key Files**:
  - `config.py` - Configuration classes and settings
  - `config.json` - Application settings and environment variables

### Deployment

#### `deployment/docker/`
- **Purpose**: Docker containerization
- **Key Files**:
  - `Dockerfile` - Multi-stage production-ready container
  - `docker-compose.yml` - Full stack deployment
  - `nginx.conf` - Reverse proxy configuration

#### `deployment/scripts/`
- **Purpose**: Deployment and launch scripts
- **Key Files**:
  - `launch_app.py` - Development launcher
  - `launch.sh` - Unix/Linux launcher
  - `launch.bat` - Windows launcher

## 🔧 Import Structure

### New Import Patterns

With the modular structure, imports follow this pattern:

```python
# Configuration
from config.config import get_settings

# Backend modules
from backend.core.app import app
from backend.api.routes import router
from backend.agents.agents import create_and_execute_workflow
from backend.database.db import db_manager
from backend.models.models import ProjectGenerationRequest
```

### Entry Point

The main entry point is now `main.py` at the project root:

```python
# Run the application
python main.py

# Or using the deployment scripts
python deployment/scripts/launch_app.py
```

## 📊 Benefits of New Structure

### 1. Development Benefits
- **Faster Development**: Clear module boundaries
- **Easier Debugging**: Isolated components
- **Better Testing**: Module-specific test suites
- **Code Reusability**: Modular components

### 2. Deployment Benefits
- **Docker Optimization**: Cleaner container builds
- **Microservice Migration**: Easy service separation
- **Environment Management**: Centralized configuration
- **Scaling**: Independent module scaling

### 3. Maintenance Benefits
- **Code Organization**: Intuitive file locations
- **Documentation**: Module-specific docs
- **Dependency Management**: Clear import hierarchy
- **Refactoring**: Isolated change impact

## 🔄 Migration Notes

### From Old Structure
- `app.py` → `backend/core/app.py`
- `routes.py` → `backend/api/routes.py`
- `agents.py` → `backend/agents/agents.py`
- `db.py` → `backend/database/db.py`
- `models.py` → `backend/models/models.py`
- `config.py` → `config/config.py`

### Temporary Files
All unnecessary files have been moved to `temp/`:
- Cache files (`__pycache__/`)
- Log files (`*.log`)
- Backup files (`*.backup`)
- Old database files (`multiagent.db`)
- Legacy monolithic backend (`back.py`)

## 🛠️ Development Workflow

### 1. Starting Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### 2. Running Tests
```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/backend.test.py
```

### 3. Docker Development
```bash
# Build and run with Docker
cd deployment/docker
docker-compose up --build
```

### 4. Adding New Features
1. Identify the appropriate module (`backend/api/`, `backend/agents/`, etc.)
2. Add new functionality following the module's pattern
3. Update imports in dependent modules
4. Add tests in the `tests/` directory
5. Update documentation

This modular structure provides a solid foundation for scaling the Multi-Agent Code Generation System while maintaining security, performance, and maintainability.