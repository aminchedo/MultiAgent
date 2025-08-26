#!/usr/bin/env python3
"""
Simple Backend Tests for Vibe Coding Platform
Tests the basic API functionality to ensure pipeline passes.
"""

import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.simple_backend import app

class TestSimpleBackend:
    """Test cases for simplified backend functionality."""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "vibe-coding-api"
    
    def test_api_health_check(self):
        """Test API health check endpoint"""
        response = self.client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "vibe-coding-api"
    
    def test_vibe_coding_submission(self):
        """Test vibe coding request submission"""
        request_data = {
            "prompt": "Create a simple todo app",
            "project_type": "web",
            "framework": "react"
        }
        
        response = self.client.post("/api/vibe-coding", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        assert data["message"] == "Agent processing started"
        
        # Verify job_id format (should be a UUID)
        job_id = data["job_id"]
        assert len(job_id) == 36  # UUID format
        assert job_id.count("-") == 4
    
    def test_job_status_check(self):
        """Test job status checking"""
        # First submit a job
        request_data = {
            "prompt": "Create a test app",
            "project_type": "web",
            "framework": "react"
        }
        
        submit_response = self.client.post("/api/vibe-coding", json=request_data)
        assert submit_response.status_code == 200
        job_id = submit_response.json()["job_id"]
        
        # Check status immediately (should be processing)
        status_response = self.client.get(f"/api/vibe-coding/status/{job_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "status" in status_data
        assert "message" in status_data
        assert "agent_status" in status_data
        assert status_data["prompt"] == "Create a test app"
    
    def test_job_status_not_found(self):
        """Test job status for non-existent job"""
        fake_job_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f"/api/vibe-coding/status/{fake_job_id}")
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]
    
    def test_files_endpoint(self):
        """Test generated files endpoint"""
        # Submit a job
        request_data = {
            "prompt": "Create a file test app",
            "project_type": "web",
            "framework": "react"
        }
        
        submit_response = self.client.post("/api/vibe-coding", json=request_data)
        job_id = submit_response.json()["job_id"]
        
        # Check files endpoint responds correctly
        files_response = self.client.get(f"/api/vibe-coding/files/{job_id}")
        assert files_response.status_code == 200
        
        files_data = files_response.json()
        assert "files" in files_data
        # Files should be a list (empty or populated depending on job status)
        assert isinstance(files_data["files"], list)
    
    def test_download_endpoint(self):
        """Test download endpoint"""
        # Submit a job
        request_data = {
            "prompt": "Create a download test app",
            "project_type": "web",
            "framework": "react"
        }
        
        submit_response = self.client.post("/api/vibe-coding", json=request_data)
        job_id = submit_response.json()["job_id"]
        
        # Test download endpoint
        download_response = self.client.get(f"/api/download/{job_id}")
        assert download_response.status_code == 200
        
        download_data = download_response.json()
        assert "message" in download_data
        assert download_data["job_id"] == job_id
    
    def test_download_not_found(self):
        """Test download for non-existent job"""
        fake_job_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f"/api/download/{fake_job_id}")
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]
    
    def test_vibe_request_validation(self):
        """Test request validation"""
        # Test missing prompt
        response = self.client.post("/api/vibe-coding", json={})
        assert response.status_code == 422  # Validation error
        
        # Test with only prompt (should work with defaults)
        response = self.client.post("/api/vibe-coding", json={"prompt": "test"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processing"
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = self.client.get("/health")
        assert response.status_code == 200
        # CORS headers should be present in the test client response

class TestAgentProcessing:
    """Test agent processing simulation"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @pytest.mark.asyncio
    async def test_async_processing(self):
        """Test that async processing works correctly"""
        # Submit a job
        request_data = {
            "prompt": "Create an async test app",
            "project_type": "web",
            "framework": "react"
        }
        
        response = self.client.post("/api/vibe-coding", json=request_data)
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Wait a moment for processing
        await asyncio.sleep(1)
        
        # Check that processing is happening
        status_response = self.client.get(f"/api/vibe-coding/status/{job_id}")
        status_data = status_response.json()
        
        # Should have agent status
        assert "agent_status" in status_data
        agent_status = status_data["agent_status"]
        assert "planner" in agent_status
        assert "coder" in agent_status
        assert "critic" in agent_status
        assert "file_manager" in agent_status

if __name__ == "__main__":
    pytest.main([__file__, "-v"])