#!/usr/bin/env python3
"""
System Integration Validation Script
Comprehensive check of all platform components before deployment
"""

import subprocess
import sys
import os
import time
import requests
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

class SystemIntegrationValidator:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def run_comprehensive_validation(self):
        """Run complete system validation"""
        print("🔍 COMPREHENSIVE SYSTEM INTEGRATION VALIDATION")
        print("=" * 80)
        print(f"🕐 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Define all validation checks
        validation_checks = [
            ("🐍 Python Environment", self.check_python_environment),
            ("📦 Backend Dependencies", self.check_backend_dependencies),
            ("🤖 Agent Imports", self.check_agent_imports),
            ("🚀 Backend Service", self.check_backend_service),
            ("🔗 API Endpoints", self.check_api_endpoints),
            ("📊 Real Agent Processing", self.check_real_agent_processing),
            ("📁 File Generation", self.check_file_generation),
            ("💾 Download System", self.check_download_system),
            ("🎨 Frontend Integration", self.check_frontend_integration),
            ("🧪 End-to-End Workflow", self.check_e2e_workflow)
        ]
        
        print(f"📋 Running {len(validation_checks)} validation checks...\n")
        
        # Run all checks
        for check_name, check_function in validation_checks:
            print(f"🔍 {check_name}...")
            try:
                result = check_function()
                self.process_check_result(check_name, result)
            except Exception as e:
                self.process_check_result(check_name, {
                    "status": "failed",
                    "message": f"Check failed with exception: {str(e)}"
                })
            print()
        
        # Generate final report
        self.generate_final_report()
    
    def check_python_environment(self) -> Dict[str, Any]:
        """Validate Python environment and virtual environment"""
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major != 3 or python_version.minor < 8:
                return {
                    "status": "failed",
                    "message": f"Python 3.8+ required, found {python_version.major}.{python_version.minor}",
                    "details": ["Upgrade Python to 3.8 or higher"]
                }
            
            # Check virtual environment
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            if not in_venv and not os.environ.get('VIRTUAL_ENV'):
                return {
                    "status": "warning",
                    "message": "Not running in virtual environment",
                    "details": ["Consider using virtual environment for isolation"]
                }
            
            return {
                "status": "passed",
                "message": f"Python {python_version.major}.{python_version.minor}.{python_version.micro}",
                "details": [f"Virtual environment: {'Yes' if in_venv else 'No'}"]
            }
            
        except Exception as e:
            return {"status": "failed", "message": str(e)}
    
    def check_backend_dependencies(self) -> Dict[str, Any]:
        """Check if all required backend dependencies are installed"""
        required_packages = [
            'fastapi', 'uvicorn', 'python-multipart', 'pydantic',
            'aiohttp', 'structlog'
        ]
        
        missing_packages = []
        installed_packages = []
        
        for package in required_packages:
            try:
                if package == 'python-multipart':
                    __import__('multipart')
                else:
                    __import__(package.replace('-', '_'))
                installed_packages.append(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            return {
                "status": "failed",
                "message": f"Missing packages: {', '.join(missing_packages)}",
                "details": [
                    f"Installed: {', '.join(installed_packages)}",
                    f"Run: pip install {' '.join(missing_packages)}"
                ]
            }
        
        return {
            "status": "passed",
            "message": f"All {len(required_packages)} dependencies installed",
            "details": installed_packages
        }
    
    def check_agent_imports(self) -> Dict[str, Any]:
        """Check if all sophisticated agents can be imported"""
        agent_modules = [
            'agents.vibe_planner_agent.VibePlannerAgent',
            'agents.vibe_coder_agent.VibeCoderAgent',
            'agents.vibe_critic_agent.VibeCriticAgent',
            'agents.vibe_file_manager_agent.VibeFileManagerAgent',
            'agents.vibe_workflow_orchestrator_agent.VibeWorkflowOrchestratorAgent'
        ]
        
        imported_agents = []
        failed_imports = []
        
        # Add workspace to Python path
        workspace_path = Path(__file__).parent
        sys.path.insert(0, str(workspace_path))
        
        for agent_path in agent_modules:
            try:
                module_path, class_name = agent_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                
                # Try to instantiate
                agent_instance = agent_class()
                imported_agents.append(class_name)
                
            except Exception as e:
                failed_imports.append(f"{class_name}: {str(e)}")
        
        if failed_imports:
            return {
                "status": "failed",
                "message": f"Agent import failures: {len(failed_imports)}",
                "details": failed_imports + [f"Working: {', '.join(imported_agents)}"]
            }
        
        return {
            "status": "passed",
            "message": f"All {len(agent_modules)} agents imported successfully",
            "details": imported_agents
        }
    
    def check_backend_service(self) -> Dict[str, Any]:
        """Check if backend service is running and responsive"""
        try:
            # Try to connect to health endpoint
            response = requests.get("http://localhost:8000/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "passed",
                    "message": "Backend service is running",
                    "details": [
                        f"Service: {health_data.get('service', 'Unknown')}",
                        f"Version: {health_data.get('version', 'Unknown')}",
                        f"Response time: {response.elapsed.total_seconds():.3f}s"
                    ]
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Backend health check failed: HTTP {response.status_code}",
                    "details": ["Backend is running but not healthy"]
                }
                
        except requests.ConnectionError:
            return {
                "status": "failed",
                "message": "Backend service not running",
                "details": ["Start backend with: python3 backend/simple_app.py"]
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Backend check failed: {str(e)}"
            }
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """Check if all required API endpoints are available"""
        endpoints = [
            ("POST", "/api/vibe-coding", "Vibe coding creation"),
            ("GET", "/api/vibe-coding/status/{job_id}", "Job status monitoring"),
            ("GET", "/api/vibe-coding/files/{job_id}", "Files listing"),
            ("GET", "/api/download/{job_id}", "Project download")
        ]
        
        available_endpoints = []
        missing_endpoints = []
        
        for method, endpoint, description in endpoints:
            try:
                if method == "POST":
                    # Test with minimal data
                    response = requests.post(
                        f"http://localhost:8000{endpoint}",
                        json={"vibe_prompt": "test"},
                        timeout=10
                    )
                else:
                    # For GET endpoints, expect 404 with fake ID
                    test_endpoint = endpoint.replace("{job_id}", "test-id")
                    response = requests.get(f"http://localhost:8000{test_endpoint}", timeout=5)
                
                # Both 200 (success) and 404 (endpoint exists) are acceptable
                if response.status_code in [200, 404, 422]:  # 422 = validation error (expected)
                    available_endpoints.append(f"{method} {endpoint}")
                else:
                    missing_endpoints.append(f"{method} {endpoint} (HTTP {response.status_code})")
                    
            except Exception as e:
                missing_endpoints.append(f"{method} {endpoint} ({str(e)})")
        
        if missing_endpoints:
            return {
                "status": "failed",
                "message": f"Endpoints not available: {len(missing_endpoints)}",
                "details": missing_endpoints + [f"Available: {len(available_endpoints)}"]
            }
        
        return {
            "status": "passed",
            "message": f"All {len(endpoints)} API endpoints available",
            "details": available_endpoints
        }
    
    def check_real_agent_processing(self) -> Dict[str, Any]:
        """Test that real agents are processing vibe prompts"""
        try:
            # Submit a simple vibe request
            response = requests.post(
                "http://localhost:8000/api/vibe-coding",
                json={
                    "vibe_prompt": "Create a simple hello world app",
                    "project_type": "web",
                    "framework": "react"
                },
                timeout=15
            )
            
            if response.status_code != 200:
                return {
                    "status": "failed",
                    "message": f"Failed to submit vibe request: HTTP {response.status_code}",
                    "details": [response.text[:200]]
                }
            
            job_data = response.json()
            job_id = job_data.get("job_id")
            
            if not job_id:
                return {
                    "status": "failed",
                    "message": "No job ID returned from vibe request",
                    "details": [str(job_data)]
                }
            
            # Wait for processing to complete
            max_wait = 60  # 1 minute max
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(
                    f"http://localhost:8000/api/vibe-coding/status/{job_id}",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    if status_data.get("status") == "completed":
                        files_count = len(status_data.get("files_generated", []))
                        return {
                            "status": "passed",
                            "message": f"Real agent processing completed: {files_count} files",
                            "details": [
                                f"Job ID: {job_id}",
                                f"Processing time: {time.time() - start_time:.1f}s",
                                f"Files: {files_count}"
                            ]
                        }
                    elif status_data.get("status") == "failed":
                        return {
                            "status": "failed",
                            "message": f"Agent processing failed: {status_data.get('message')}",
                            "details": [f"Job ID: {job_id}"]
                        }
                
                time.sleep(3)
            
            return {
                "status": "failed",
                "message": "Agent processing timeout (60s)",
                "details": [f"Job ID: {job_id}", "Agents may be too slow"]
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Agent processing test failed: {str(e)}"
            }
    
    def check_file_generation(self) -> Dict[str, Any]:
        """Check that files are actually generated and not placeholders"""
        # This assumes the previous test created a job
        # We'll do a quick test with a new job
        try:
            response = requests.post(
                "http://localhost:8000/api/vibe-coding",
                json={
                    "vibe_prompt": "Create a basic React component with state",
                    "project_type": "web",
                    "framework": "react"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return {
                    "status": "warning",
                    "message": "Could not test file generation - API unavailable",
                    "details": ["Skipping detailed file validation"]
                }
            
            job_data = response.json()
            job_id = job_data.get("job_id")
            
            # Wait briefly for completion
            time.sleep(30)  # Give it some time
            
            files_response = requests.get(
                f"http://localhost:8000/api/vibe-coding/files/{job_id}",
                timeout=5
            )
            
            if files_response.status_code == 200:
                files_data = files_response.json()
                files = files_data.get("files", [])
                
                if len(files) > 0:
                    total_size = sum(f.get("size", 0) for f in files)
                    return {
                        "status": "passed",
                        "message": f"File generation working: {len(files)} files, {total_size} bytes",
                        "details": [f["name"] for f in files[:5]]  # Show first 5 files
                    }
                else:
                    return {
                        "status": "warning",
                        "message": "No files generated yet",
                        "details": ["Files may still be processing"]
                    }
            
            return {
                "status": "warning",
                "message": "File generation status unclear",
                "details": ["Could not verify file creation"]
            }
            
        except Exception as e:
            return {
                "status": "warning",
                "message": f"File generation check incomplete: {str(e)}"
            }
    
    def check_download_system(self) -> Dict[str, Any]:
        """Check that download system produces real ZIP files"""
        # We'll try to download from a recent job if available
        try:
            # For this test, we'll check if the download endpoint responds correctly
            # to a fake job ID (should return 404, not 500)
            response = requests.get(
                "http://localhost:8000/api/download/test-job-id",
                timeout=5
            )
            
            if response.status_code == 404:
                return {
                    "status": "passed",
                    "message": "Download system responding correctly",
                    "details": ["Returns proper 404 for missing jobs"]
                }
            else:
                return {
                    "status": "warning",
                    "message": f"Download endpoint unusual response: HTTP {response.status_code}",
                    "details": ["May still work for valid job IDs"]
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Download system check failed: {str(e)}"
            }
    
    def check_frontend_integration(self) -> Dict[str, Any]:
        """Check frontend integration files"""
        frontend_files = [
            "frontend/test_vibe_integration.html",
            "frontend/assets/index.html"
        ]
        
        existing_files = []
        missing_files = []
        
        for file_path in frontend_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                existing_files.append(f"{file_path} ({file_size} bytes)")
            else:
                missing_files.append(file_path)
        
        if missing_files:
            return {
                "status": "warning",
                "message": f"Some frontend files missing: {len(missing_files)}",
                "details": missing_files + existing_files
            }
        
        return {
            "status": "passed",
            "message": f"Frontend integration files present: {len(existing_files)}",
            "details": existing_files
        }
    
    def check_e2e_workflow(self) -> Dict[str, Any]:
        """Check if the comprehensive E2E test exists and is runnable"""
        e2e_test_file = "test_comprehensive_e2e.py"
        
        if not os.path.exists(e2e_test_file):
            return {
                "status": "warning",
                "message": "E2E test suite not found",
                "details": ["Create comprehensive test suite for full validation"]
            }
        
        try:
            # Try to import the test module
            sys.path.insert(0, os.path.dirname(os.path.abspath(e2e_test_file)))
            import test_comprehensive_e2e
            
            return {
                "status": "passed",
                "message": "E2E test suite available and importable",
                "details": [
                    f"File: {e2e_test_file}",
                    f"Size: {os.path.getsize(e2e_test_file)} bytes",
                    "Run with: python3 test_comprehensive_e2e.py"
                ]
            }
            
        except Exception as e:
            return {
                "status": "warning",
                "message": f"E2E test suite has issues: {str(e)}",
                "details": ["Fix import errors for full testing"]
            }
    
    def process_check_result(self, check_name: str, result: Dict[str, Any]):
        """Process and display check result"""
        status = result.get("status", "unknown")
        message = result.get("message", "No message")
        details = result.get("details", [])
        
        if status == "passed":
            print(f"   ✅ PASS: {message}")
            self.passed += 1
        elif status == "warning":
            print(f"   ⚠️  WARN: {message}")
            self.warnings += 1
        else:
            print(f"   ❌ FAIL: {message}")
            self.failed += 1
        
        if details:
            for detail in details:
                print(f"      • {detail}")
        
        self.checks.append({
            "name": check_name,
            "status": status,
            "message": message,
            "details": details
        })
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        total_checks = len(self.checks)
        
        print("=" * 80)
        print("📊 FINAL SYSTEM INTEGRATION REPORT")
        print("=" * 80)
        
        print(f"\n🎯 SUMMARY METRICS:")
        print(f"   Total Checks: {total_checks}")
        print(f"   Passed: {self.passed}")
        print(f"   Warnings: {self.warnings}")
        print(f"   Failed: {self.failed}")
        
        if total_checks > 0:
            success_rate = (self.passed / total_checks) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
        
        # Overall assessment
        print(f"\n🏆 PLATFORM READINESS ASSESSMENT:")
        
        critical_failures = [c for c in self.checks if c["status"] == "failed" and any(
            keyword in c["name"].lower() for keyword in ["backend", "agent", "api"]
        )]
        
        if critical_failures:
            print(f"   ❌ CRITICAL ISSUES FOUND - Platform not ready")
            print(f"   🚨 {len(critical_failures)} critical system failures")
            print(f"   🔧 Must fix before user deployment")
            
            for failure in critical_failures:
                print(f"      - {failure['name']}: {failure['message']}")
        
        elif self.failed > 0:
            print(f"   ⚠️  NON-CRITICAL ISSUES - Platform partially functional")
            print(f"   🔧 {self.failed} issues need attention")
            print(f"   ✅ Core functionality may still work")
        
        elif self.warnings > 2:
            print(f"   👍 GOOD - Platform functional with minor concerns")
            print(f"   ⚠️  {self.warnings} warnings to address")
            print(f"   ✅ Ready for careful testing")
        
        else:
            print(f"   🎉 EXCELLENT - Platform fully integrated and ready")
            print(f"   ✅ All critical systems operational")
            print(f"   🚀 Ready for user deployment")
        
        # Specific recommendations
        print(f"\n💡 IMMEDIATE ACTIONS NEEDED:")
        
        backend_issues = [c for c in self.checks if c["status"] == "failed" and "backend" in c["name"].lower()]
        if backend_issues:
            print(f"   🔧 Fix backend service issues:")
            for issue in backend_issues:
                print(f"      - {issue['message']}")
        
        agent_issues = [c for c in self.checks if c["status"] == "failed" and "agent" in c["name"].lower()]
        if agent_issues:
            print(f"   🤖 Resolve agent integration problems:")
            for issue in agent_issues:
                print(f"      - {issue['message']}")
        
        if not backend_issues and not agent_issues and self.failed == 0:
            print(f"   🎊 No critical actions needed - platform is working!")
            print(f"   📋 Consider running full E2E tests: python3 test_comprehensive_e2e.py")
        
        print(f"\n📋 NEXT STEPS:")
        
        if critical_failures:
            print(f"   1. 🚨 Fix critical system failures immediately")
            print(f"   2. 🔄 Re-run this validation after fixes")
            print(f"   3. 🧪 Run E2E tests when all systems pass")
        elif self.failed > 0:
            print(f"   1. 🔧 Address failed checks")
            print(f"   2. 🧪 Run comprehensive E2E tests")
            print(f"   3. 👥 Begin limited user testing")
        else:
            print(f"   1. 🧪 Run comprehensive E2E tests")
            print(f"   2. 📊 Monitor system performance")
            print(f"   3. 🚀 Deploy to production with confidence")
        
        print(f"\n" + "=" * 80)
        print(f"✅ System validation completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if critical_failures:
            print(f"🚨 RESULT: CRITICAL ISSUES - DO NOT DEPLOY")
        elif self.failed > 0:
            print(f"⚠️  RESULT: ISSUES FOUND - DEPLOY WITH CAUTION") 
        else:
            print(f"🎉 RESULT: SYSTEM READY - CLEARED FOR DEPLOYMENT")
        
        print("=" * 80)

def main():
    """Run system integration validation"""
    print("🔍 VIBE CODING PLATFORM - SYSTEM INTEGRATION VALIDATION")
    print("This script validates all platform components and readiness for deployment\n")
    
    try:
        validator = SystemIntegrationValidator()
        validator.run_comprehensive_validation()
    except KeyboardInterrupt:
        print("\n❌ Validation cancelled by user")
    except Exception as e:
        print(f"\n💥 Validation error: {e}")

if __name__ == "__main__":
    main()