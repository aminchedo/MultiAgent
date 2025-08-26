#!/usr/bin/env python3
"""
Comprehensive System Integration Validator for Vibe Coding Platform
Validates all components, dependencies, and end-to-end functionality.
"""

import os
import sys
import subprocess
import time
import json
import asyncio
import aiohttp
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

class SystemIntegrationValidator:
    def __init__(self):
        self.workspace_root = Path("/workspace")
        self.backend_url = "http://localhost:8000"
        self.validation_results = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "checks": [],
            "overall_status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        self.backend_process = None
    
    def log_check(self, check_name: str, status: str, details: str = "", critical: bool = False):
        """Log a validation check result"""
        check = {
            "name": check_name,
            "status": status,
            "details": details,
            "critical": critical,
            "timestamp": time.strftime('%H:%M:%S')
        }
        self.validation_results["checks"].append(check)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        critical_marker = " [CRITICAL]" if critical else ""
        print(f"{status_icon} {check_name}: {status}{critical_marker}")
        if details:
            print(f"   {details}")
    
    async def run_complete_validation(self):
        """Run comprehensive system validation"""
        print("=" * 80)
        print("🔍 COMPREHENSIVE SYSTEM INTEGRATION VALIDATION")
        print("=" * 80)
        print(f"🕐 Started at: {self.validation_results['timestamp']}")
        print(f"📁 Workspace: {self.workspace_root}")
        print()
        
        try:
            # Phase 1: Environment and Dependencies
            print("📦 PHASE 1: ENVIRONMENT AND DEPENDENCIES")
            print("-" * 50)
            await self.validate_environment()
            await self.validate_dependencies()
            print()
            
            # Phase 2: Agent System Validation
            print("🤖 PHASE 2: AI AGENT SYSTEM VALIDATION")
            print("-" * 50)
            await self.validate_agent_system()
            print()
            
            # Phase 3: Backend Service Validation
            print("🔧 PHASE 3: BACKEND SERVICE VALIDATION")
            print("-" * 50)
            await self.validate_backend_service()
            print()
            
            # Phase 4: API Integration Validation
            print("🌐 PHASE 4: API INTEGRATION VALIDATION")
            print("-" * 50)
            await self.validate_api_integration()
            print()
            
            # Phase 5: End-to-End Workflow Validation
            print("🚀 PHASE 5: END-TO-END WORKFLOW VALIDATION")
            print("-" * 50)
            await self.validate_e2e_workflow()
            print()
            
            # Phase 6: Frontend Integration Validation
            print("🎨 PHASE 6: FRONTEND INTEGRATION VALIDATION")
            print("-" * 50)
            await self.validate_frontend_integration()
            print()
            
            # Phase 7: Quality and Performance Validation
            print("📊 PHASE 7: QUALITY AND PERFORMANCE VALIDATION")
            print("-" * 50)
            await self.validate_quality_and_performance()
            print()
            
        finally:
            # Generate final report
            await self.generate_final_report()
    
    async def validate_environment(self):
        """Validate system environment and basic requirements"""
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.log_check("Python Version", "PASS", f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.log_check("Python Version", "FAIL", f"Python {python_version.major}.{python_version.minor} < 3.8", critical=True)
        
        # Check workspace structure
        required_dirs = ["agents", "backend", "frontend"]
        missing_dirs = []
        for dir_name in required_dirs:
            if not (self.workspace_root / dir_name).exists():
                missing_dirs.append(dir_name)
        
        if not missing_dirs:
            self.log_check("Workspace Structure", "PASS", f"All required directories present: {required_dirs}")
        else:
            self.log_check("Workspace Structure", "FAIL", f"Missing directories: {missing_dirs}", critical=True)
        
        # Check virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.log_check("Virtual Environment", "PASS", "Python virtual environment detected")
        else:
            self.log_check("Virtual Environment", "WARN", "No virtual environment detected")
    
    async def validate_dependencies(self):
        """Validate all required dependencies are installed"""
        required_packages = [
            ("fastapi", "FastAPI web framework"),
            ("uvicorn", "ASGI server"),
            ("pydantic", "Data validation"),
            ("aiohttp", "Async HTTP client"),
            ("structlog", "Structured logging")
        ]
        
        for package, description in required_packages:
            try:
                __import__(package)
                self.log_check(f"Package {package}", "PASS", description)
            except ImportError:
                self.log_check(f"Package {package}", "FAIL", f"Missing: {description}", critical=True)
        
        # Check agent dependencies
        try:
            sys.path.append(str(self.workspace_root))
            from agents.vibe_planner_agent import VibePlannerAgent
            from agents.vibe_coder_agent import VibeCoderAgent
            from agents.vibe_critic_agent import VibeCriticAgent
            from agents.vibe_file_manager_agent import VibeFileManagerAgent
            from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
            self.log_check("Agent Dependencies", "PASS", "All agent modules importable")
        except Exception as e:
            self.log_check("Agent Dependencies", "FAIL", f"Import error: {str(e)}", critical=True)
    
    async def validate_agent_system(self):
        """Validate the AI agent system functionality"""
        try:
            sys.path.append(str(self.workspace_root))
            
            # Test individual agents
            agents_to_test = [
                ("VibePlannerAgent", "agents.vibe_planner_agent", "VibePlannerAgent"),
                ("VibeCoderAgent", "agents.vibe_coder_agent", "VibeCoderAgent"),
                ("VibeCriticAgent", "agents.vibe_critic_agent", "VibeCriticAgent"),
                ("VibeFileManagerAgent", "agents.vibe_file_manager_agent", "VibeFileManagerAgent"),
                ("VibeWorkflowOrchestratorAgent", "agents.vibe_workflow_orchestrator_agent", "VibeWorkflowOrchestratorAgent")
            ]
            
            for agent_name, module_name, class_name in agents_to_test:
                try:
                    module = __import__(module_name, fromlist=[class_name])
                    agent_class = getattr(module, class_name)
                    agent_instance = agent_class()
                    
                    # Test agent capabilities
                    if hasattr(agent_instance, 'get_capabilities'):
                        capabilities = agent_instance.get_capabilities()
                        self.log_check(f"Agent {agent_name}", "PASS", f"Capabilities: {len(capabilities)}")
                    else:
                        self.log_check(f"Agent {agent_name}", "PASS", "Basic instantiation successful")
                        
                except Exception as e:
                    self.log_check(f"Agent {agent_name}", "FAIL", f"Error: {str(e)}", critical=True)
            
            # Test orchestrator workflow
            try:
                from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
                orchestrator = VibeWorkflowOrchestratorAgent()
                
                test_request = {
                    "vibe_prompt": "Create a simple test website",
                    "project_type": "web",
                    "framework": "react"
                }
                
                # This is a basic validation - we'll test full workflow later
                self.log_check("Orchestrator Initialization", "PASS", "Workflow orchestrator ready")
                
            except Exception as e:
                self.log_check("Orchestrator Initialization", "FAIL", f"Error: {str(e)}", critical=True)
                
        except Exception as e:
            self.log_check("Agent System Validation", "FAIL", f"System error: {str(e)}", critical=True)
    
    async def validate_backend_service(self):
        """Validate backend service can start and respond"""
        try:
            # Check if backend is already running
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.backend_url}/health", timeout=5) as response:
                        if response.status == 200:
                            self.log_check("Backend Already Running", "PASS", "Backend service is already active")
                            return
            except:
                pass
            
            # Try to start backend
            self.log_check("Backend Startup", "INFO", "Attempting to start backend service...")
            
            backend_script = self.workspace_root / "backend" / "simple_app.py"
            if not backend_script.exists():
                self.log_check("Backend Script", "FAIL", f"Backend script not found: {backend_script}", critical=True)
                return
            
            # Start backend in background
            cmd = [sys.executable, str(backend_script)]
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.workspace_root)
            )
            
            # Wait for startup
            await asyncio.sleep(10)
            
            # Test health endpoint
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.backend_url}/health", timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.log_check("Backend Health Check", "PASS", f"Service: {data.get('service', 'unknown')}")
                        else:
                            self.log_check("Backend Health Check", "FAIL", f"HTTP {response.status}", critical=True)
            except Exception as e:
                self.log_check("Backend Health Check", "FAIL", f"Connection error: {str(e)}", critical=True)
                
        except Exception as e:
            self.log_check("Backend Service Validation", "FAIL", f"Startup error: {str(e)}", critical=True)
    
    async def validate_api_integration(self):
        """Validate all API endpoints are working"""
        endpoints_to_test = [
            ("/health", "GET", "Health check endpoint"),
            ("/api/vibe-coding", "POST", "Vibe coding generation endpoint"),
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method, description in endpoints_to_test:
                try:
                    if method == "GET":
                        async with session.get(f"{self.backend_url}{endpoint}", timeout=10) as response:
                            if response.status == 200:
                                self.log_check(f"API {endpoint}", "PASS", description)
                            else:
                                self.log_check(f"API {endpoint}", "FAIL", f"HTTP {response.status}")
                    
                    elif method == "POST" and endpoint == "/api/vibe-coding":
                        # Test with minimal payload
                        test_payload = {
                            "vibe_prompt": "Test validation prompt",
                            "project_type": "web",
                            "framework": "react"
                        }
                        async with session.post(
                            f"{self.backend_url}{endpoint}",
                            json=test_payload,
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                if "job_id" in data:
                                    self.log_check(f"API {endpoint}", "PASS", f"Job ID generated: {data['job_id'][:8]}...")
                                else:
                                    self.log_check(f"API {endpoint}", "FAIL", "No job_id in response")
                            else:
                                self.log_check(f"API {endpoint}", "FAIL", f"HTTP {response.status}")
                                
                except Exception as e:
                    self.log_check(f"API {endpoint}", "FAIL", f"Error: {str(e)}")
    
    async def validate_e2e_workflow(self):
        """Validate complete end-to-end workflow"""
        try:
            test_scenarios = [
                {
                    "name": "Quick React App",
                    "vibe_prompt": "Create a simple React app with a welcome message",
                    "project_type": "web",
                    "framework": "react",
                    "timeout": 60,
                    "min_files": 5
                }
            ]
            
            for scenario in test_scenarios:
                self.log_check(f"E2E Test: {scenario['name']}", "INFO", f"Testing: {scenario['vibe_prompt'][:40]}...")
                
                async with aiohttp.ClientSession() as session:
                    # Submit job
                    async with session.post(
                        f"{self.backend_url}/api/vibe-coding",
                        json={
                            "vibe_prompt": scenario["vibe_prompt"],
                            "project_type": scenario["project_type"],
                            "framework": scenario["framework"]
                        }
                    ) as response:
                        if response.status != 200:
                            self.log_check(f"E2E Submit: {scenario['name']}", "FAIL", f"HTTP {response.status}")
                            continue
                        
                        data = await response.json()
                        job_id = data["job_id"]
                        self.log_check(f"E2E Submit: {scenario['name']}", "PASS", f"Job: {job_id[:8]}...")
                    
                    # Monitor progress
                    start_time = time.time()
                    completed = False
                    
                    while time.time() - start_time < scenario["timeout"]:
                        await asyncio.sleep(5)
                        
                        try:
                            async with session.get(f"{self.backend_url}/api/vibe-coding/status/{job_id}") as status_response:
                                if status_response.status == 200:
                                    status_data = await status_response.json()
                                    
                                    if status_data["status"] == "completed":
                                        self.log_check(f"E2E Process: {scenario['name']}", "PASS", f"Completed in {time.time() - start_time:.1f}s")
                                        completed = True
                                        
                                        # Test file generation
                                        async with session.get(f"{self.backend_url}/api/vibe-coding/files/{job_id}") as files_response:
                                            if files_response.status == 200:
                                                files_data = await files_response.json()
                                                file_count = len(files_data.get("files", []))
                                                
                                                if file_count >= scenario["min_files"]:
                                                    self.log_check(f"E2E Files: {scenario['name']}", "PASS", f"{file_count} files generated")
                                                else:
                                                    self.log_check(f"E2E Files: {scenario['name']}", "FAIL", f"Only {file_count} files, expected {scenario['min_files']}")
                                            else:
                                                self.log_check(f"E2E Files: {scenario['name']}", "FAIL", f"Files API error: {files_response.status}")
                                        
                                        # Test download
                                        async with session.get(f"{self.backend_url}/api/download/{job_id}") as download_response:
                                            if download_response.status == 200:
                                                zip_content = await download_response.read()
                                                if len(zip_content) > 1000:  # Reasonable minimum size
                                                    self.log_check(f"E2E Download: {scenario['name']}", "PASS", f"ZIP size: {len(zip_content)} bytes")
                                                else:
                                                    self.log_check(f"E2E Download: {scenario['name']}", "FAIL", f"ZIP too small: {len(zip_content)} bytes")
                                            else:
                                                self.log_check(f"E2E Download: {scenario['name']}", "FAIL", f"Download error: {download_response.status}")
                                        
                                        break
                                        
                                    elif status_data["status"] == "failed":
                                        self.log_check(f"E2E Process: {scenario['name']}", "FAIL", f"Generation failed: {status_data.get('message', 'Unknown error')}")
                                        break
                        except Exception as e:
                            self.log_check(f"E2E Monitor: {scenario['name']}", "FAIL", f"Monitoring error: {str(e)}")
                            break
                    
                    if not completed:
                        self.log_check(f"E2E Timeout: {scenario['name']}", "FAIL", f"Timeout after {scenario['timeout']}s")
                        
        except Exception as e:
            self.log_check("E2E Workflow Validation", "FAIL", f"System error: {str(e)}", critical=True)
    
    async def validate_frontend_integration(self):
        """Validate frontend integration"""
        frontend_files = [
            "frontend/test_vibe_integration.html",
            "frontend/assets/index.html",
            "frontend/pages/index.html"
        ]
        
        for file_path in frontend_files:
            full_path = self.workspace_root / file_path
            if full_path.exists():
                self.log_check(f"Frontend File: {file_path}", "PASS", f"Size: {full_path.stat().st_size} bytes")
                
                # Check for real API integration
                try:
                    content = full_path.read_text(encoding='utf-8', errors='ignore')
                    if '/api/vibe-coding' in content:
                        self.log_check(f"Frontend API Integration: {file_path}", "PASS", "Real API calls detected")
                    else:
                        self.log_check(f"Frontend API Integration: {file_path}", "WARN", "No vibe-coding API calls found")
                except Exception as e:
                    self.log_check(f"Frontend Analysis: {file_path}", "FAIL", f"Read error: {str(e)}")
            else:
                self.log_check(f"Frontend File: {file_path}", "FAIL", "File not found")
    
    async def validate_quality_and_performance(self):
        """Validate code quality and performance metrics"""
        # Test file generation quality
        try:
            test_zip_path = self.workspace_root / "test-download.zip"
            if test_zip_path.exists():
                zip_size = test_zip_path.stat().st_size
                self.log_check("Generated Project Quality", "PASS", f"Sample project size: {zip_size} bytes")
                
                # Analyze ZIP contents
                try:
                    with zipfile.ZipFile(test_zip_path, 'r') as zipf:
                        file_list = zipf.namelist()
                        
                        # Check for functional files
                        functional_files = [f for f in file_list if f.endswith(('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json'))]
                        if len(functional_files) >= 5:
                            self.log_check("Code File Generation", "PASS", f"{len(functional_files)} functional files")
                        else:
                            self.log_check("Code File Generation", "WARN", f"Only {len(functional_files)} functional files")
                        
                        # Check for proper structure
                        has_package_json = any('package.json' in f for f in file_list)
                        has_src_dir = any('src/' in f for f in file_list)
                        has_components = any('components' in f for f in file_list)
                        
                        structure_score = sum([has_package_json, has_src_dir, has_components])
                        if structure_score >= 2:
                            self.log_check("Project Structure Quality", "PASS", f"Proper React structure detected")
                        else:
                            self.log_check("Project Structure Quality", "WARN", f"Structure score: {structure_score}/3")
                            
                except Exception as e:
                    self.log_check("ZIP Analysis", "FAIL", f"Analysis error: {str(e)}")
            else:
                self.log_check("Generated Project Sample", "WARN", "No sample project found for analysis")
                
        except Exception as e:
            self.log_check("Quality Validation", "FAIL", f"Quality check error: {str(e)}")
    
    async def generate_final_report(self):
        """Generate comprehensive validation report"""
        # Analyze results
        total_checks = len(self.validation_results["checks"])
        passed_checks = len([c for c in self.validation_results["checks"] if c["status"] == "PASS"])
        failed_checks = len([c for c in self.validation_results["checks"] if c["status"] == "FAIL"])
        critical_failures = len([c for c in self.validation_results["checks"] if c["status"] == "FAIL" and c["critical"]])
        warnings = len([c for c in self.validation_results["checks"] if c["status"] == "WARN"])
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = "CRITICAL_ISSUES"
        elif failed_checks > total_checks * 0.3:  # More than 30% failures
            overall_status = "MAJOR_ISSUES"
        elif failed_checks > 0 or warnings > total_checks * 0.2:  # Any failures or >20% warnings
            overall_status = "MINOR_ISSUES"
        else:
            overall_status = "FULLY_FUNCTIONAL"
        
        self.validation_results["overall_status"] = overall_status
        
        # Generate report
        print("=" * 80)
        print("📋 COMPREHENSIVE VALIDATION REPORT")
        print("=" * 80)
        
        # Summary
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"   Total Checks: {total_checks}")
        print(f"   Passed: {passed_checks}")
        print(f"   Failed: {failed_checks}")
        print(f"   Critical Failures: {critical_failures}")
        print(f"   Warnings: {warnings}")
        print(f"   Success Rate: {(passed_checks/total_checks)*100:.1f}%")
        
        # Overall assessment
        print(f"\n🏆 OVERALL PLATFORM STATUS: {overall_status}")
        
        if overall_status == "FULLY_FUNCTIONAL":
            print(f"   ✅ EXCELLENT: Platform is fully functional")
            print(f"   ✅ All critical systems operational")
            print(f"   ✅ Ready for production deployment")
            print(f"   🚀 Users can generate real, functional projects")
        elif overall_status == "MINOR_ISSUES":
            print(f"   👍 GOOD: Platform is functional with minor issues")
            print(f"   ✅ Core functionality working")
            print(f"   🔧 Minor improvements recommended")
            print(f"   📝 Ready for beta testing")
        elif overall_status == "MAJOR_ISSUES":
            print(f"   ⚠️ ISSUES: Platform has significant problems")
            print(f"   ⚠️ Core functionality may be impaired")
            print(f"   🔧 Major fixes required before user deployment")
            print(f"   🚨 Not ready for production use")
        else:
            print(f"   ❌ CRITICAL: Platform not functional")
            print(f"   ❌ Critical systems failing")
            print(f"   🚨 Major reconstruction required")
            print(f"   ⛔ Do not deploy to users")
        
        # Failed checks details
        if failed_checks > 0:
            print(f"\n❌ FAILED CHECKS:")
            for check in self.validation_results["checks"]:
                if check["status"] == "FAIL":
                    critical_marker = " [CRITICAL]" if check["critical"] else ""
                    print(f"   - {check['name']}{critical_marker}: {check['details']}")
        
        # Warnings
        if warnings > 0:
            print(f"\n⚠️ WARNINGS:")
            for check in self.validation_results["checks"]:
                if check["status"] == "WARN":
                    print(f"   - {check['name']}: {check['details']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if critical_failures > 0:
            print(f"   🚨 URGENT: Fix {critical_failures} critical issues immediately")
            print(f"   🚨 Platform cannot function with critical failures")
        
        if failed_checks > 0:
            print(f"   🔧 Fix {failed_checks} failed components")
            print(f"   🔧 Test thoroughly after fixes")
        
        if warnings > 0:
            print(f"   📈 Address {warnings} warnings for optimal performance")
        
        if overall_status in ["FULLY_FUNCTIONAL", "MINOR_ISSUES"]:
            print(f"   ✅ Run end-to-end tests with real users")
            print(f"   📊 Monitor performance metrics")
            print(f"   🎯 Platform delivers real value to users")
        
        # Save results
        results_file = self.workspace_root / "validation_results.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(self.validation_results, f, indent=2)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"\n⚠️ Could not save results: {e}")
        
        print(f"\n" + "=" * 80)
        print(f"✅ Validation completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Cleanup
        if self.backend_process:
            try:
                self.backend_process.terminate()
                await asyncio.sleep(3)
                if self.backend_process.poll() is None:
                    self.backend_process.kill()
                print("🔧 Backend service stopped")
            except:
                pass

async def main():
    """Run comprehensive system validation"""
    print("🚀 Starting Comprehensive System Integration Validation...")
    print("🔍 This will validate the entire Vibe Coding Platform")
    print()
    
    validator = SystemIntegrationValidator()
    await validator.run_complete_validation()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Validation cancelled by user")
    except Exception as e:
        print(f"\n💥 Validation error: {e}")
        traceback.print_exc()