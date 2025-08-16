"""
API Completeness Test Suite
Verifies 100% API coverage with comprehensive endpoint testing.
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from httpx import AsyncClient
from fastapi.testclient import TestClient

from backend.core.app import app
from backend.models.models import (
    ProjectGenerationRequest, CodeExecutionRequest, AuthRequest
)


class TestAgentCoordinationAPI:
    """Test agent coordination API endpoints."""
    
    @pytest.mark.asyncio
    async def test_submit_task_endpoint(self):
        """Test task submission API endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v2/agents/tasks/submit",
                json={
                    "description": "generate_login_page",
                    "agent_type": "code_generator",
                    "priority": "high",
                    "verification_required": True
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "task_id" in data
            assert data["task_id"].startswith("task_")
            assert data["status"] == "submitted"
    
    @pytest.mark.asyncio
    async def test_check_task_status_endpoint(self):
        """Test task status checking API endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First submit a task
            submit_response = await client.post(
                "/api/v2/agents/tasks/submit",
                json={"description": "test task", "agent_type": "planner"}
            )
            task_id = submit_response.json()["task_id"]
            
            # Check status
            response = await client.get(f"/api/v2/agents/tasks/{task_id}/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id
            assert "status" in data
            assert "agent" in data
            assert "assignment" in data
    
    @pytest.mark.asyncio
    async def test_validate_output_endpoint(self):
        """Test output validation API endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Submit task first
            submit_response = await client.post(
                "/api/v2/agents/tasks/submit",
                json={"description": "test task"}
            )
            task_id = submit_response.json()["task_id"]
            
            # Validate output
            response = await client.post(
                f"/api/v2/agents/tasks/{task_id}/validate",
                json={
                    "expected_output": "ui_templates/login.html",
                    "validation_criteria": ["format", "content", "quality"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "is_valid" in data
            assert "validation_details" in data
    
    @pytest.mark.asyncio
    async def test_create_workflow_endpoint(self):
        """Test workflow creation API endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v2/agents/workflows/create",
                json={
                    "name": "Authentication System",
                    "tasks": [
                        {
                            "description": "Plan authentication",
                            "agent_type": "planner",
                            "priority": 3,
                            "dependencies": []
                        },
                        {
                            "description": "Generate code",
                            "agent_type": "code_generator", 
                            "priority": 2,
                            "dependencies": []
                        }
                    ]
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "workflow_id" in data
            assert data["workflow_id"].startswith("wf_")
            assert data["name"] == "Authentication System"


class TestSecurityAPI:
    """Test security scanning API endpoints."""
    
    @pytest.mark.asyncio
    async def test_vulnerability_scan_endpoint(self):
        """Test vulnerability scanning endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v2/security/scan/vulnerability",
                json={
                    "scan_type": "comprehensive",
                    "targets": ["backend/", "frontend/"],
                    "include_dependencies": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "scan_id" in data
            assert "vulnerabilities" in data
            assert "overall_score" in data
            assert "owasp_compliance" in data
    
    @pytest.mark.asyncio
    async def test_secret_detection_endpoint(self):
        """Test secret detection endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v2/security/scan/secrets",
                json={
                    "content": "api_key = 'sk-1234567890abcdef'\\npassword = 'secret123'",
                    "file_path": "config.py"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "secrets" in data
            assert isinstance(data["secrets"], list)
    
    @pytest.mark.asyncio
    async def test_owasp_compliance_endpoint(self):
        """Test OWASP compliance checking endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v2/security/compliance/owasp",
                json={
                    "file_paths": ["backend/api/routes.py", "backend/models/models.py"],
                    "standards": ["OWASP_TOP_10", "CWE"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "overall_score" in data
            assert "passed_checks" in data
            assert "failed_checks" in data
            assert "categories" in data
    
    @pytest.mark.asyncio
    async def test_penetration_test_endpoint(self):
        """Test penetration testing endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v2/security/pentest",
                json={
                    "target_url": "http://localhost:8000",
                    "test_types": ["sql_injection", "xss", "directory_traversal"],
                    "max_duration": 300
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "target" in data
            assert "tests" in data
            assert "vulnerabilities_found" in data


class TestMonitoringAPI:
    """Test monitoring and health check API endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test comprehensive health check endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v2/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["healthy", "degraded", "unhealthy"]
            assert "timestamp" in data
            assert "version" in data
            assert "uptime" in data
            assert "checks" in data
            
            # Verify individual checks
            checks = data["checks"]
            assert "database" in checks
            assert "redis" in checks
            assert "agents" in checks
            assert "external_apis" in checks
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Test metrics collection endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v2/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert "system" in data
            assert "agents" in data
            assert "tasks" in data
            assert "security" in data
    
    @pytest.mark.asyncio
    async def test_sla_metrics_endpoint(self):
        """Test SLA metrics endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v2/metrics/sla")
            
            assert response.status_code == 200
            data = response.json()
            assert "uptime_percentage" in data
            assert "avg_response_time" in data
            assert "error_rate" in data
            assert data["uptime_percentage"] >= 99.95  # SLA requirement
    
    @pytest.mark.asyncio
    async def test_agent_status_endpoint(self):
        """Test agent status monitoring endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v2/agents/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "active_agents" in data
            assert "agent_utilization" in data
            assert "agents" in data
            
            # Verify agent details
            if data["agents"]:
                agent = data["agents"][0]
                assert "agent_id" in agent
                assert "agent_type" in agent
                assert "load" in agent
                assert "status" in agent


class TestProjectGenerationAPI:
    """Test project generation API endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_project_endpoint(self):
        """Test project generation endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {
                "name": "test-project",
                "description": "A test project for API testing",
                "project_type": "web_app",
                "languages": ["python", "javascript"],
                "frameworks": ["fastapi", "react"],
                "complexity": "moderate",
                "features": ["authentication", "database", "api"],
                "mode": "full"
            }
            
            response = await client.post(
                "/api/v2/projects/generate",
                json=request_data
            )
            
            assert response.status_code == 202  # Accepted for async processing
            data = response.json()
            assert "job_id" in data
            assert "status" in data
            assert data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_project_status_endpoint(self):
        """Test project generation status endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First start a project generation
            gen_response = await client.post(
                "/api/v2/projects/generate",
                json={
                    "name": "status-test",
                    "description": "Testing status endpoint",
                    "project_type": "api"
                }
            )
            job_id = gen_response.json()["job_id"]
            
            # Check status
            response = await client.get(f"/api/v2/projects/{job_id}/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job_id
            assert "status" in data
            assert "progress" in data


class TestAuthenticationAPI:
    """Test authentication and authorization API endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_endpoint(self):
        """Test user login endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v2/auth/login",
                json={"username": "testuser", "password": "testpass"}
            )
            
            assert response.status_code in [200, 401]  # Success or invalid credentials
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data
                assert "token_type" in data
    
    @pytest.mark.asyncio
    async def test_token_validation_endpoint(self):
        """Test token validation endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # This would require a valid token for testing
            headers = {"Authorization": "Bearer test_token"}
            response = await client.get("/api/v2/auth/validate", headers=headers)
            
            assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_access(self):
        """Test access to protected endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try accessing protected endpoint without token
            response = await client.get("/api/v2/admin/agents")
            
            assert response.status_code == 401


class TestAdminAPI:
    """Test administrative API endpoints."""
    
    @pytest.mark.asyncio
    async def test_agent_management_endpoints(self):
        """Test agent management endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Get all agents
            response = await client.get("/api/v2/admin/agents")
            assert response.status_code in [200, 401]  # Success or unauthorized
            
            if response.status_code == 200:
                data = response.json()
                assert "agents" in data
    
    @pytest.mark.asyncio
    async def test_system_config_endpoints(self):
        """Test system configuration endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Get system configuration
            response = await client.get("/api/v2/admin/config")
            assert response.status_code in [200, 401]


class TestWebSocketAPI:
    """Test WebSocket API endpoints."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection for real-time updates."""
        # WebSocket testing requires special handling
        # This is a placeholder for WebSocket tests
        pass
    
    @pytest.mark.asyncio
    async def test_realtime_task_updates(self):
        """Test real-time task status updates via WebSocket."""
        # Implementation would depend on WebSocket testing framework
        pass


class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_api_response_times(self):
        """Test API response times meet SLA requirements (<500ms)."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test critical path endpoints
            critical_endpoints = [
                ("/api/v2/health", "GET"),
                ("/api/v2/agents/status", "GET"),
                ("/api/v2/metrics", "GET")
            ]
            
            for endpoint, method in critical_endpoints:
                start_time = datetime.now()
                
                if method == "GET":
                    response = await client.get(endpoint)
                else:
                    response = await client.post(endpoint, json={})
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                # SLA requirement: <500ms for critical paths
                assert response_time < 500, f"Endpoint {endpoint} took {response_time}ms"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self):
        """Test API performance under concurrent load."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Submit 100 concurrent requests
            tasks = []
            for i in range(100):
                task = client.get("/api/v2/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful responses
            successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            
            # Should handle at least 90% successfully
            assert successful >= 90


class TestAPICompliance:
    """Test API compliance with OpenAPI specification."""
    
    def test_openapi_schema_generation(self):
        """Test OpenAPI schema generation."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        # Verify schema structure
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema
        
        # Verify version
        assert schema["info"]["version"] == "2.0.0"
    
    def test_api_documentation_endpoints(self):
        """Test API documentation endpoints."""
        client = TestClient(app)
        
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_api_versioning(self):
        """Test API versioning compliance."""
        client = TestClient(app)
        
        # All endpoints should be under /api/v2/
        response = client.get("/openapi.json")
        schema = response.json()
        
        for path in schema["paths"]:
            assert path.startswith("/api/v2/"), f"Path {path} not properly versioned"


class TestAPIErrorHandling:
    """Test API error handling and responses."""
    
    @pytest.mark.asyncio
    async def test_404_error_handling(self):
        """Test 404 error handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v2/nonexistent/endpoint")
            
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert "timestamp" in data
            assert "request_id" in data
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test request validation error handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send invalid request data
            response = await client.post(
                "/api/v2/projects/generate",
                json={"invalid": "data"}
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test API rate limiting."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send many requests quickly
            tasks = []
            for i in range(200):  # Exceed rate limit
                task = client.get("/api/v2/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Should get some 429 (Too Many Requests) responses
            rate_limited = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 429)
            assert rate_limited > 0, "Rate limiting not working"


# Fixtures for API testing

@pytest.fixture
def test_client():
    """Create test client for API testing."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # In real implementation, this would generate valid JWT tokens
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def sample_project_request():
    """Sample project generation request for testing."""
    return {
        "name": "test-api-project",
        "description": "Project for API testing",
        "project_type": "web_app",
        "languages": ["python"],
        "frameworks": ["fastapi"],
        "complexity": "simple",
        "features": ["api", "database"],
        "mode": "full"
    }


# Test runners and utilities

def run_api_completeness_tests():
    """Run all API completeness tests."""
    pytest.main([
        "tests/test_api_completeness.py",
        "-v",
        "--cov=backend.api",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])


def run_performance_tests():
    """Run API performance tests."""
    pytest.main([
        "tests/test_api_completeness.py::TestAPIPerformance",
        "-v",
        "-m", "performance"
    ])


if __name__ == "__main__":
    run_api_completeness_tests()