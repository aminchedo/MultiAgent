#!/usr/bin/env python3
"""
Test script to validate Phase 3 enhancements.
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

class EnhancementTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
    def test_health_endpoint(self) -> bool:
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", True, f"Service: {data.get('service')}")
                    return True
                else:
                    self.log_test("Health Check", False, "Invalid health status")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    def test_templates_endpoint(self) -> bool:
        """Test templates endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/templates", timeout=5)
            if response.status_code == 200:
                data = response.json()
                templates = data.get("templates", [])
                if len(templates) > 0:
                    self.log_test("Templates API", True, f"Found {len(templates)} templates")
                    return True
                else:
                    self.log_test("Templates API", False, "No templates found")
                    return False
            else:
                self.log_test("Templates API", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Templates API", False, str(e))
            return False
    
    def test_api_key_validation(self) -> str:
        """Test API key validation and get JWT token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/validate-key",
                json={"api_key": "default-dev-key"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("valid") and data.get("token"):
                    self.log_test("API Key Validation", True, "Token generated successfully")
                    return data.get("token")
                else:
                    self.log_test("API Key Validation", False, "Invalid response format")
                    return None
            else:
                self.log_test("API Key Validation", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_test("API Key Validation", False, str(e))
            return None
    
    def test_job_creation(self, token: str) -> str:
        """Test job creation endpoint"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            job_data = {
                "description": "Create a simple Python web API with FastAPI",
                "complexity": "simple"
            }
            
            response = requests.post(
                f"{self.base_url}/api/jobs",
                json=job_data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                if job_id:
                    self.log_test("Job Creation", True, f"Job ID: {job_id}")
                    return job_id
                else:
                    self.log_test("Job Creation", False, "No job ID returned")
                    return None
            else:
                self.log_test("Job Creation", False, f"HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Job Creation", False, str(e))
            return None
    
    def test_job_status(self, token: str, job_id: str) -> bool:
        """Test job status endpoint"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.base_url}/api/jobs/{job_id}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                if status:
                    self.log_test("Job Status", True, f"Status: {status}")
                    return True
                else:
                    self.log_test("Job Status", False, "No status returned")
                    return False
            else:
                self.log_test("Job Status", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Job Status", False, str(e))
            return False
    
    def test_system_stats(self, token: str) -> bool:
        """Test system stats endpoint"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.base_url}/api/stats",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("stats", {})
                if stats:
                    self.log_test("System Stats", True, "Stats retrieved successfully")
                    return True
                else:
                    self.log_test("System Stats", False, "No stats returned")
                    return False
            else:
                self.log_test("System Stats", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("System Stats", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all enhancement tests"""
        print("🚀 Starting Phase 3 Enhancement Tests")
        print("=" * 50)
        
        # Test health endpoint
        self.test_health_endpoint()
        
        # Test templates endpoint
        self.test_templates_endpoint()
        
        # Test API key validation
        token = self.test_api_key_validation()
        
        if token:
            # Test job creation
            job_id = self.test_job_creation(token)
            
            if job_id:
                # Test job status
                self.test_job_status(token, job_id)
            
            # Test system stats
            self.test_system_stats(token)
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 All Phase 3 enhancements are working correctly!")
        else:
            print("⚠️  Some enhancements need attention.")
        
        return passed == total

if __name__ == "__main__":
    tester = EnhancementTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)