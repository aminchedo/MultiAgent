"""
Comprehensive backend tests for the Multi-Agent Code Generation System.
Tests all major functionality including agents, API endpoints, database operations, and WebSocket.
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

# Import the application and modules
from app import app
from db import db_manager, DatabaseManager
from agents import (
    PlannerAgent, CodeGeneratorAgent, TesterAgent, DocGeneratorAgent,
    MultiAgentWorkflow, create_and_execute_workflow
)
from models import (
    ProjectGenerationRequest, JobStatus, ProjectType, ComplexityLevel,
    generate_job_id
)
from config import get_settings


# Test configuration
settings = get_settings()
settings.database_url = "sqlite+aiosqlite:///test.db"  # Use SQLite for testing
settings.openai_api_key = "test-key"


@pytest.fixture
async def async_client():
    """Async test client for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_test_manager():
    """Test database manager with SQLite."""
    test_db = DatabaseManager()
    test_db.engine = None  # Will be initialized
    await test_db.initialize()
    yield test_db
    await test_db.close()


@pytest.fixture
def test_job_data():
    """Sample job data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing",
        "project_type": ProjectType.WEB_APP,
        "languages": ["python", "javascript"],
        "frameworks": ["fastapi", "react"],
        "complexity": ComplexityLevel.MODERATE,
        "features": ["authentication", "database"],
        "mode": "full"
    }


@pytest.fixture
def auth_headers():
    """Authentication headers for API tests."""
    # Mock JWT token for testing
    return {"Authorization": "Bearer test-token"}


class TestDatabaseOperations:
    """Test database operations and models."""
    
    @pytest.mark.asyncio
    async def test_create_job(self, db_test_manager, test_job_data):
        """Test job creation in database."""
        job_id = generate_job_id()
        
        job = await db_test_manager.create_job(
            job_id=job_id,
            name=test_job_data["name"],
            description=test_job_data["description"],
            project_type=test_job_data["project_type"],
            languages=test_job_data["languages"],
            frameworks=test_job_data["frameworks"],
            complexity=test_job_data["complexity"],
            features=test_job_data["features"],
            mode=test_job_data["mode"]
        )
        
        assert job.job_id == job_id
        assert job.name == test_job_data["name"]
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0
        assert isinstance(job.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_get_job(self, db_test_manager, test_job_data):
        """Test retrieving job from database."""
        job_id = generate_job_id()
        
        # Create job
        await db_test_manager.create_job(
            job_id=job_id,
            name=test_job_data["name"],
            description=test_job_data["description"],
            project_type=test_job_data["project_type"],
            languages=test_job_data["languages"],
            frameworks=test_job_data["frameworks"],
            complexity=test_job_data["complexity"],
            features=test_job_data["features"]
        )
        
        # Retrieve job
        retrieved_job = await db_test_manager.get_job(job_id)
        
        assert retrieved_job is not None
        assert retrieved_job.job_id == job_id
        assert retrieved_job.name == test_job_data["name"]
    
    @pytest.mark.asyncio
    async def test_update_job_status(self, db_test_manager, test_job_data):
        """Test updating job status."""
        job_id = generate_job_id()
        
        # Create job
        await db_test_manager.create_job(
            job_id=job_id,
            name=test_job_data["name"],
            description=test_job_data["description"],
            project_type=test_job_data["project_type"],
            languages=test_job_data["languages"],
            frameworks=test_job_data["frameworks"],
            complexity=test_job_data["complexity"],
            features=test_job_data["features"]
        )
        
        # Update status
        success = await db_test_manager.update_job_status(
            job_id=job_id,
            status=JobStatus.RUNNING,
            progress=50.0,
            current_step="Testing step",
            step_number=5
        )
        
        assert success is True
        
        # Verify update
        updated_job = await db_test_manager.get_job(job_id)
        assert updated_job.status == JobStatus.RUNNING
        assert updated_job.progress == 50.0
        assert updated_job.current_step == "Testing step"
        assert updated_job.step_number == 5
    
    @pytest.mark.asyncio
    async def test_create_file(self, db_test_manager):
        """Test file creation in database."""
        job_id = generate_job_id()
        
        file_model = await db_test_manager.create_file(
            job_id=job_id,
            filename="test.py",
            path="src/test.py",
            content="print('Hello, World!')",
            language="python"
        )
        
        assert file_model.job_id == job_id
        assert file_model.filename == "test.py"
        assert file_model.path == "src/test.py"
        assert file_model.content == "print('Hello, World!')"
        assert file_model.language == "python"
        assert file_model.size > 0
        assert len(file_model.hash) == 64  # SHA256 hash
    
    @pytest.mark.asyncio
    async def test_create_log(self, db_test_manager):
        """Test log entry creation."""
        job_id = generate_job_id()
        
        log_entry = await db_test_manager.create_log(
            job_id=job_id,
            agent="PlannerAgent",
            message="Test log message",
            level="INFO",
            metadata={"test": "data"}
        )
        
        assert log_entry.job_id == job_id
        assert log_entry.agent == "PlannerAgent"
        assert log_entry.message == "Test log message"
        assert log_entry.level == "INFO"
        assert log_entry.metadata == {"test": "data"}


class TestCrewAIAgents:
    """Test CrewAI agents functionality."""
    
    @pytest.mark.asyncio
    async def test_planner_agent_initialization(self):
        """Test PlannerAgent initialization."""
        job_id = generate_job_id()
        websocket_callback = AsyncMock()
        
        with patch('agents.OpenAI') as mock_openai:
            mock_openai.return_value = Mock()
            
            planner = PlannerAgent(job_id, websocket_callback)
            
            assert planner.job_id == job_id
            assert planner.websocket_callback == websocket_callback
            assert planner.llm is not None
    
    @pytest.mark.asyncio
    async def test_planner_agent_generate_plan(self):
        """Test plan generation by PlannerAgent."""
        job_id = generate_job_id()
        websocket_callback = AsyncMock()
        
        project_data = {
            "name": "Test Web App",
            "description": "A simple web application for testing",
            "project_type": "web_app",
            "languages": ["python", "javascript"],
            "complexity": "moderate"
        }
        
        with patch('agents.OpenAI') as mock_openai, \
             patch('agents.Crew') as mock_crew, \
             patch('agents.db_manager') as mock_db:
            
            # Mock LLM
            mock_llm = Mock()
            mock_openai.return_value = mock_llm
            
            # Mock Crew execution
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = json.dumps({
                "name": "Test Web App",
                "structure": {
                    "src/app.py": "Main application file",
                    "tests/test_app.py": "Test file",
                    "README.md": "Documentation"
                },
                "technologies": ["python", "javascript"],
                "frameworks": ["fastapi", "react"]
            })
            mock_crew.return_value = mock_crew_instance
            
            # Mock database operations
            mock_db.create_log = AsyncMock()
            mock_db.update_job_status = AsyncMock()
            
            planner = PlannerAgent(job_id, websocket_callback)
            plan = await planner.generate_plan(project_data)
            
            assert "name" in plan
            assert "structure" in plan
            assert plan["name"] == "Test Web App"
            assert len(plan["structure"]) > 0
            
            # Verify database interactions
            mock_db.create_log.assert_called()
            mock_db.update_job_status.assert_called()
    
    @pytest.mark.asyncio
    async def test_code_generator_agent(self):
        """Test CodeGeneratorAgent functionality."""
        job_id = generate_job_id()
        websocket_callback = AsyncMock()
        
        plan = {
            "name": "Test Project",
            "structure": {
                "src/app.py": "Main application",
                "tests/test_app.py": "Test file"
            }
        }
        
        with patch('agents.OpenAI') as mock_openai, \
             patch('agents.Crew') as mock_crew, \
             patch('agents.db_manager') as mock_db:
            
            mock_openai.return_value = Mock()
            
            # Mock Crew execution for code generation
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = "# Generated Python code\nprint('Hello, World!')"
            mock_crew.return_value = mock_crew_instance
            
            # Mock database operations
            mock_db.create_log = AsyncMock()
            mock_db.update_job_status = AsyncMock()
            mock_db.create_file = AsyncMock()
            
            coder = CodeGeneratorAgent(job_id, websocket_callback)
            files = await coder.generate_code(plan)
            
            assert len(files) == 2  # Two files in the plan
            assert all("path" in file for file in files)
            assert all("content" in file for file in files)
            assert all("language" in file for file in files)
            
            # Verify database interactions
            mock_db.create_file.assert_called()
            assert mock_db.create_file.call_count == 2
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test complete multi-agent workflow."""
        job_id = generate_job_id()
        websocket_callback = AsyncMock()
        
        project_data = {
            "name": "Test Project",
            "description": "A test project",
            "project_type": "web_app",
            "languages": ["python"],
            "complexity": "simple",
            "mode": "full"
        }
        
        with patch('agents.OpenAI') as mock_openai, \
             patch('agents.Crew') as mock_crew, \
             patch('agents.db_manager') as mock_db:
            
            mock_openai.return_value = Mock()
            
            # Mock different crew responses for each agent
            mock_crew_instance = Mock()
            mock_crew.return_value = mock_crew_instance
            
            # Mock plan generation
            mock_crew_instance.kickoff.side_effect = [
                json.dumps({"name": "Test", "structure": {"app.py": "Main app"}}),  # Planner
                "# Generated code",  # Code generator
                "# Test code",  # Tester
                "# Documentation"  # Doc generator
            ]
            
            # Mock database operations
            mock_db.update_job_status = AsyncMock()
            mock_db.create_file = AsyncMock()
            mock_db.create_log = AsyncMock()
            
            workflow = MultiAgentWorkflow(job_id, websocket_callback)
            result = await workflow.execute_workflow(project_data)
            
            assert "plan" in result
            assert "code_files" in result
            assert "test_files" in result
            assert "doc_files" in result
            assert "total_files" in result
            
            # Verify final status update
            mock_db.update_job_status.assert_called()


class TestAPIEndpoints:
    """Test FastAPI endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_generate_project_endpoint(self, async_client):
        """Test project generation endpoint."""
        project_data = {
            "name": "Test API Project",
            "description": "A test project via API",
            "project_type": "web_app",
            "languages": ["python"],
            "frameworks": ["fastapi"],
            "complexity": "simple",
            "features": ["api"],
            "mode": "full"
        }
        
        with patch('routes.verify_token') as mock_auth, \
             patch('routes.db_manager') as mock_db, \
             patch('routes.create_and_execute_workflow') as mock_workflow:
            
            # Mock authentication
            mock_auth.return_value = "test_user"
            
            # Mock database
            mock_db.create_job = AsyncMock()
            
            # Mock workflow execution
            mock_workflow.return_value = AsyncMock()
            
            response = await async_client.post(
                "/api/generate",
                json=project_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "job_id" in data
            assert "estimated_duration" in data
    
    @pytest.mark.asyncio
    async def test_job_status_endpoint(self, async_client):
        """Test job status endpoint."""
        job_id = str(uuid.uuid4())
        
        with patch('routes.verify_token') as mock_auth, \
             patch('routes.db_manager') as mock_db:
            
            mock_auth.return_value = "test_user"
            
            # Mock job data
            mock_job = Mock()
            mock_job.job_id = job_id
            mock_job.status = JobStatus.RUNNING
            mock_job.progress = 75.0
            mock_job.current_step = "Testing"
            mock_job.step_number = 6
            mock_job.total_steps = 8
            mock_job.created_at = datetime.utcnow()
            mock_job.updated_at = datetime.utcnow()
            mock_job.error_message = None
            mock_job.completed_at = None
            
            mock_db.get_job = AsyncMock(return_value=mock_job)
            mock_db.get_files = AsyncMock(return_value=[])
            
            response = await async_client.get(
                f"/status/{job_id}",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["job_id"] == job_id
            assert data["status"] == JobStatus.RUNNING
            assert data["progress"] == 75.0
    
    @pytest.mark.asyncio
    async def test_code_execution_endpoint(self, async_client):
        """Test code execution endpoint."""
        execution_data = {
            "code": "print('Hello, World!')",
            "language": "python",
            "timeout": 30
        }
        
        with patch('routes.verify_token') as mock_auth, \
             patch('routes.subprocess.run') as mock_subprocess:
            
            mock_auth.return_value = "test_user"
            
            # Mock subprocess execution
            mock_result = Mock()
            mock_result.stdout = "Hello, World!\n"
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = await async_client.post(
                "/api/execute",
                json=execution_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Hello, World!" in data["output"]
            assert data["exit_code"] == 0
    
    @pytest.mark.asyncio
    async def test_system_stats_endpoint(self, async_client):
        """Test system statistics endpoint."""
        with patch('routes.verify_token') as mock_auth, \
             patch('routes.psutil') as mock_psutil, \
             patch('routes.db_manager') as mock_db:
            
            mock_auth.return_value = "test_user"
            
            # Mock system metrics
            mock_psutil.cpu_percent.return_value = 45.5
            mock_psutil.virtual_memory.return_value = Mock(percent=67.2)
            mock_psutil.disk_usage.return_value = Mock(percent=78.9)
            
            # Mock database stats
            mock_db.get_system_stats = AsyncMock(return_value={
                "active_jobs": 5,
                "total_jobs": 42,
                "avg_completion_time": 180.5
            })
            
            response = await async_client.get(
                "/api/stats",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["cpu_usage"] == 45.5
            assert data["memory_usage"] == 67.2
            assert data["disk_usage"] == 78.9
            assert data["active_jobs"] == 5
            assert data["total_jobs"] == 42
    
    @pytest.mark.asyncio
    async def test_templates_endpoint(self, async_client):
        """Test project templates endpoint."""
        with patch('routes.verify_token') as mock_auth:
            mock_auth.return_value = "test_user"
            
            response = await async_client.get(
                "/api/templates",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "templates" in data
            assert len(data["templates"]) > 0
            
            # Check template structure
            template = data["templates"][0]
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "languages" in template
    
    @pytest.mark.asyncio
    async def test_authentication_required(self, async_client):
        """Test that endpoints require authentication."""
        response = await async_client.get("/api/stats")
        assert response.status_code == 401
        
        response = await async_client.post("/api/generate", json={})
        assert response.status_code == 401


class TestWebSocketConnections:
    """Test WebSocket functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection and messaging."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        with client.websocket_connect("/ws") as websocket:
            # Test initial connection
            data = websocket.receive_json()
            assert data["type"] == "status"
            assert "Connected" in data["content"]
            
            # Test ping-pong
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "status"
            assert response["content"] == "pong"
    
    @pytest.mark.asyncio
    async def test_websocket_with_job_id(self):
        """Test WebSocket connection with job ID."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        job_id = str(uuid.uuid4())
        
        with client.websocket_connect(f"/ws?job_id={job_id}") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "status"
            assert data["job_id"] == job_id


class TestUtilityFunctions:
    """Test utility functions and helpers."""
    
    def test_generate_job_id(self):
        """Test job ID generation."""
        job_id1 = generate_job_id()
        job_id2 = generate_job_id()
        
        assert job_id1 != job_id2
        assert len(job_id1) == 36  # UUID4 length with hyphens
        assert isinstance(job_id1, str)
    
    def test_project_generation_request_validation(self):
        """Test ProjectGenerationRequest model validation."""
        # Valid request
        valid_data = {
            "name": "Test Project",
            "description": "A valid test project description that is long enough",
            "project_type": "web_app",
            "languages": ["python"],
            "complexity": "moderate"
        }
        
        request = ProjectGenerationRequest(**valid_data)
        assert request.name == "Test Project"
        assert request.project_type == ProjectType.WEB_APP
        assert request.complexity == ComplexityLevel.MODERATE
    
    def test_project_generation_request_defaults(self):
        """Test ProjectGenerationRequest default values."""
        minimal_data = {
            "name": "Test",
            "description": "A minimal test project description",
            "project_type": "api"
        }
        
        request = ProjectGenerationRequest(**minimal_data)
        assert request.languages == ["python"]  # Default value
        assert request.frameworks == []  # Default value
        assert request.complexity == ComplexityLevel.MODERATE  # Default
        assert request.mode == "full"  # Default


# Test configuration and setup
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])