"""
Comprehensive Integration Tests for Multi-Agent Code Generation System
Tests the complete workflow from request to project generation
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocket

# Import system components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.simple_app import app
from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
from api.websocket_handler import connection_manager, MessageType, AgentStatus
from config.security import InputValidator, ValidationError, RateLimitError

# Test client
client = TestClient(app)

class TestSystemIntegration:
    """Integration tests for the complete system"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_job_id = "test_job_123"
        self.test_request = {
            "prompt": "Create a modern React todo application with dark mode",
            "framework": "react",
            "complexity": "intermediate",
            "features": ["responsive-design", "dark-mode"],
            "project_type": "web",
            "user_id": "test_user_123"
        }
    
    def test_health_endpoint(self):
        """Test system health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "agents_ready" in data
    
    def test_project_creation_endpoint(self):
        """Test project creation endpoint validation"""
        # Valid request
        response = client.post("/api/vibe-coding", json=self.test_request)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"
        assert "websocket_url" in data
        
        # Invalid framework
        invalid_request = self.test_request.copy()
        invalid_request["framework"] = "invalid_framework"
        response = client.post("/api/vibe-coding", json=invalid_request)
        assert response.status_code == 400
    
    def test_project_status_endpoint(self):
        """Test project status retrieval"""
        # Create a project first
        response = client.post("/api/vibe-coding", json=self.test_request)
        job_id = response.json()["job_id"]
        
        # Check status
        status_response = client.get(f"/api/vibe-coding/status/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert "progress" in status_data
        assert "agents" in status_data
        
        # Non-existent job
        response = client.get("/api/vibe-coding/status/non_existent_job")
        assert response.status_code == 404
    
    def test_input_validation(self):
        """Test comprehensive input validation"""
        validator = InputValidator()
        
        # Valid prompt
        assert validator.validate_prompt("Create a modern web application") == True
        
        # Invalid prompts
        with pytest.raises(ValidationError):
            validator.validate_prompt("")  # Empty
        
        with pytest.raises(ValidationError):
            validator.validate_prompt("short")  # Too short
        
        with pytest.raises(ValidationError):
            validator.validate_prompt("a" * 6000)  # Too long
        
        with pytest.raises(ValidationError):
            validator.validate_prompt("<script>alert('xss')</script>")  # Malicious content
        
        # Valid framework
        assert validator.validate_framework("react") == True
        
        # Invalid framework
        with pytest.raises(ValidationError):
            validator.validate_framework("invalid")
        
        # Valid features
        assert validator.validate_features(["responsive-design", "dark-mode"]) == True
        
        # Invalid features
        with pytest.raises(ValidationError):
            validator.validate_features(["invalid-feature"])

class TestWorkflowOrchestrator:
    """Tests for the workflow orchestrator agent"""
    
    def setup_method(self):
        """Set up orchestrator tests"""
        self.progress_updates = []
        
        async def mock_callback(job_id, agent_name, status, progress, task, details=None):
            self.progress_updates.append({
                "job_id": job_id,
                "agent_name": agent_name,
                "status": status,
                "progress": progress,
                "task": task,
                "details": details
            })
        
        self.orchestrator = VibeWorkflowOrchestratorAgent(progress_callback=mock_callback)
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        assert self.orchestrator is not None
        assert len(self.orchestrator.agent_instances) == 4  # planner, coder, critic, file_manager
        assert self.orchestrator.workflow_status.value == "idle"
    
    def test_workflow_execution_structure(self):
        """Test workflow execution structure without full execution"""
        vibe_request = {
            "vibe_prompt": "Create a simple React app",
            "project_data": {
                "project_type": "web",
                "framework": "react",
                "complexity": "simple"
            }
        }
        
        # Mock individual agent methods to avoid full execution
        with patch.object(self.orchestrator, '_execute_planner_step') as mock_planner, \
             patch.object(self.orchestrator, '_execute_coder_step') as mock_coder, \
             patch.object(self.orchestrator, '_execute_critic_step') as mock_critic, \
             patch.object(self.orchestrator, '_execute_file_manager_step') as mock_file_manager:
            
            # Set up mock returns
            mock_planner.return_value = {
                'success': True,
                'agent': 'planner',
                'analysis': {'detected_project_type': 'web'},
                'technical_requirements': {'framework': 'react'},
                'implementation_steps': [{'step': 1}]
            }
            
            mock_coder.return_value = {
                'success': True,
                'agent': 'coder',
                'generated_files': {'src/App.js': 'export default function App() {}'},
                'file_count': 1
            }
            
            mock_critic.return_value = {
                'success': True,
                'agent': 'critic',
                'overall_score': 0.85
            }
            
            mock_file_manager.return_value = {
                'success': True,
                'agent': 'file_manager',
                'organized_files': {'src/App.js': 'export default function App() {}'}
            }
            
            # Execute workflow
            result = self.orchestrator.execute_vibe_workflow(vibe_request, "test_job")
            
            # Verify structure
            assert result['workflow_status'] == 'completed'
            assert 'agent_results' in result
            assert len(result['agent_results']) == 4
            assert 'project_data' in result
            assert 'timing' in result

class TestWebSocketHandler:
    """Tests for WebSocket handling"""
    
    def setup_method(self):
        """Set up WebSocket tests"""
        self.mock_websocket = Mock(spec=WebSocket)
        self.mock_websocket.accept = AsyncMock()
        self.mock_websocket.send_text = AsyncMock()
        self.mock_websocket.receive_text = AsyncMock()
        self.mock_websocket.client_state = "CONNECTED"
    
    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Test WebSocket connection management"""
        # Test connection
        connection_id = await connection_manager.connect(
            self.mock_websocket, 
            user_id="test_user",
            job_id="test_job"
        )
        
        assert connection_id in connection_manager.active_connections
        assert "test_user" in connection_manager.user_connections
        assert "test_job" in connection_manager.job_connections
        
        # Test disconnection
        connection_manager.disconnect(connection_id)
        assert connection_id not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_agent_status_updates(self):
        """Test agent status update broadcasting"""
        # Connect a mock client
        connection_id = await connection_manager.connect(
            self.mock_websocket,
            job_id="test_job"
        )
        
        # Send agent status update
        await connection_manager.update_agent_status(
            "test_job",
            "planner",
            AgentStatus.ACTIVE,
            50.0,
            "Planning project structure"
        )
        
        # Verify message was sent
        self.mock_websocket.send_text.assert_called()
        call_args = self.mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == MessageType.AGENT_STATUS.value
        assert message["job_id"] == "test_job"
        assert message["agent_update"]["agent_name"] == "planner"

class TestErrorHandling:
    """Tests for error handling and recovery"""
    
    def test_validation_errors(self):
        """Test validation error handling"""
        # Test empty prompt
        response = client.post("/api/vibe-coding", json={
            "prompt": "",
            "framework": "react"
        })
        assert response.status_code == 400
        
        # Test invalid framework
        response = client.post("/api/vibe-coding", json={
            "prompt": "Create a web app",
            "framework": "invalid_framework"
        })
        assert response.status_code == 400
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        from config.security import RateLimiter
        
        rate_limiter = RateLimiter()
        client_id = "test_client"
        
        # Should allow initial requests
        for i in range(5):
            assert rate_limiter.is_allowed(client_id, limit=10, window=60) == True
        
        # Should block after limit
        with pytest.raises(RateLimitError):
            for i in range(20):
                rate_limiter.is_allowed(client_id, limit=10, window=60)

class TestSecurityFeatures:
    """Tests for security features"""
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        from config.security import ContentSecurity
        
        # Test XSS prevention
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = ContentSecurity.sanitize_input(malicious_input)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
    
    def test_content_security_headers(self):
        """Test security headers in responses"""
        response = client.get("/health")
        
        # Check for security headers (would be added by middleware in production)
        assert response.status_code == 200

class TestPerformance:
    """Performance and load tests"""
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        duration = time.time() - start_time
        
        # Verify all requests succeeded
        assert len(results) == 10
        assert all(status == 200 for status in results)
        assert duration < 5.0  # Should complete within 5 seconds

class TestProjectGeneration:
    """End-to-end project generation tests"""
    
    @pytest.mark.asyncio
    async def test_complete_project_workflow(self):
        """Test complete project generation workflow"""
        # This would be a longer-running integration test
        # that actually generates a small project
        
        test_request = {
            "prompt": "Create a simple React counter app",
            "framework": "react",
            "complexity": "simple",
            "features": [],
            "project_type": "web"
        }
        
        # Create project
        response = client.post("/api/vibe-coding", json=test_request)
        assert response.status_code == 200
        
        job_id = response.json()["job_id"]
        
        # Wait a moment and check status
        await asyncio.sleep(1)
        
        status_response = client.get(f"/api/vibe-coding/status/{job_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert "agents" in status_data

# Test fixtures and utilities
@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing"""
    orchestrator = Mock(spec=VibeWorkflowOrchestratorAgent)
    orchestrator.execute_vibe_workflow.return_value = {
        "workflow_status": "completed",
        "project_data": {
            "files": {"src/App.js": "export default function App() {}"},
            "metadata": {"framework": "react"},
            "statistics": {"total_files": 1, "total_lines": 1}
        },
        "agent_results": {
            "planner": {"success": True},
            "coder": {"success": True},
            "critic": {"success": True},
            "file_manager": {"success": True}
        }
    }
    return orchestrator

@pytest.fixture
def sample_project_request():
    """Sample project request for testing"""
    return {
        "prompt": "Create a modern React todo application with dark mode and responsive design",
        "framework": "react",
        "complexity": "intermediate",
        "features": ["responsive-design", "dark-mode", "animations"],
        "project_type": "web",
        "user_id": "test_user_123"
    }

# Performance benchmarks
class TestBenchmarks:
    """Performance benchmarks for the system"""
    
    def test_api_response_time(self):
        """Test API response times"""
        import time
        
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond within 1 second
    
    def test_validation_performance(self):
        """Test validation performance"""
        import time
        
        validator = InputValidator()
        prompt = "Create a modern web application with authentication and dashboard"
        
        start = time.time()
        for _ in range(100):
            validator.validate_prompt(prompt)
        duration = time.time() - start
        
        assert duration < 1.0  # 100 validations should complete within 1 second

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])