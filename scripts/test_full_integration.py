#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Vibe Coding Platform
Tests the complete workflow from prompt submission to project download.
"""

import asyncio
import aiohttp
import time
import os
import zipfile
import tempfile
from pathlib import Path

class VibeIntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
    
    async def run_comprehensive_tests(self):
        """Run complete integration tests"""
        print("🚀 STARTING COMPREHENSIVE VIBE CODING PLATFORM TESTS")
        print("=" * 60)
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Modern React Todo App",
                "prompt": "Create a modern React todo app with dark mode and animations",
                "project_type": "web",
                "framework": "react",
                "expected_files": ["package.json", "App.tsx", "components"],
                "min_files": 8
            },
            {
                "name": "Vue Landing Page",
                "prompt": "Build a sleek Vue.js landing page for a tech startup",
                "project_type": "landing",
                "framework": "vue",
                "expected_files": ["package.json", "App.vue", "main.js"],
                "min_files": 6
            },
            {
                "name": "Vanilla Portfolio",
                "prompt": "Design a minimalist portfolio website with smooth scrolling",
                "project_type": "web",
                "framework": "vanilla",
                "expected_files": ["index.html", "style.css", "script.js"],
                "min_files": 4
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🧪 TEST SCENARIO {i}: {scenario['name']}")
            print("-" * 40)
            result = await self.test_complete_workflow(scenario)
            self.test_results.append(result)
            
            # Wait between tests
            await asyncio.sleep(5)
        
        self.generate_final_report()
    
    async def test_complete_workflow(self, scenario):
        """Test complete workflow for a scenario"""
        result = {
            "scenario": scenario["name"],
            "success": False,
            "job_id": None,
            "generation_time": 0,
            "files_generated": 0,
            "download_success": False,
            "phases": {
                "submission": False,
                "planning": False,
                "coding": False,
                "review": False,
                "organization": False,
                "download": False
            },
            "errors": []
        }
        
        start_time = time.time()
        
        try:
            # Phase 1: Submit vibe prompt
            print("  📝 Submitting vibe prompt...")
            job_id = await self.submit_vibe_prompt(scenario)
            if job_id:
                result["job_id"] = job_id
                result["phases"]["submission"] = True
                print(f"    ✅ Job created: {job_id}")
            else:
                result["errors"].append("Failed to submit prompt")
                return result
            
            # Phase 2: Monitor agent processing
            print("  🤖 Monitoring agent processing...")
            processing_result = await self.monitor_agent_processing(job_id)
            
            if processing_result["success"]:
                result["phases"]["planning"] = processing_result["phases"]["planner"]
                result["phases"]["coding"] = processing_result["phases"]["coder"]
                result["phases"]["review"] = processing_result["phases"]["critic"]
                result["phases"]["organization"] = processing_result["phases"]["file_manager"]
                result["files_generated"] = processing_result["files_count"]
                print(f"    ✅ Processing complete: {result['files_generated']} files")
            else:
                result["errors"].extend(processing_result["errors"])
                return result
            
            # Phase 3: Validate generated files
            print("  📄 Validating generated files...")
            files_valid = await self.validate_generated_files(job_id, scenario)
            if files_valid:
                print(f"    ✅ Files validation passed")
            else:
                result["errors"].append("Generated files validation failed")
            
            # Phase 4: Test download functionality
            print("  📦 Testing download functionality...")
            download_result = await self.test_download(job_id, scenario)
            result["download_success"] = download_result["success"]
            result["phases"]["download"] = download_result["success"]
            
            if download_result["success"]:
                print(f"    ✅ Download successful: {download_result['zip_size']} bytes")
            else:
                result["errors"].append(f"Download failed: {download_result['error']}")
            
            # Calculate metrics
            result["generation_time"] = time.time() - start_time
            result["success"] = (
                result["phases"]["submission"] and
                result["phases"]["planning"] and
                result["phases"]["coding"] and
                result["phases"]["organization"] and
                result["files_generated"] >= scenario["min_files"]
            )
            
        except Exception as e:
            result["errors"].append(f"Test exception: {str(e)}")
        
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"  {status} - Generated {result['files_generated']} files in {result['generation_time']:.1f}s")
        
        return result
    
    async def submit_vibe_prompt(self, scenario):
        """Submit vibe prompt to backend"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.backend_url}/api/vibe-coding",
                    json={
                        "prompt": scenario["prompt"],
                        "project_type": scenario["project_type"],
                        "framework": scenario["framework"]
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("job_id")
                    else:
                        print(f"    ❌ Submit failed: HTTP {response.status}")
                        return None
            except Exception as e:
                print(f"    ❌ Submit error: {e}")
                return None
    
    async def monitor_agent_processing(self, job_id):
        """Monitor agent processing until completion"""
        result = {
            "success": False,
            "phases": {"planner": False, "coder": False, "critic": False, "file_manager": False},
            "files_count": 0,
            "errors": []
        }
        
        max_wait_time = 300  # 5 minutes
        poll_interval = 3
        elapsed_time = 0
        
        async with aiohttp.ClientSession() as session:
            while elapsed_time < max_wait_time:
                try:
                    async with session.get(f"{self.backend_url}/api/vibe-coding/status/{job_id}") as response:
                        if response.status == 200:
                            status_data = await response.json()
                            
                            # Update phase status
                            agent_status = status_data.get("agent_status", {})
                            for agent, status in agent_status.items():
                                if status == "completed":
                                    result["phases"][agent] = True
                            
                            # Check completion
                            if status_data.get("status") == "completed":
                                result["success"] = True
                                result["files_count"] = status_data.get("files_generated", 0)
                                return result
                            elif status_data.get("status") == "failed":
                                result["errors"].append(status_data.get("message", "Unknown error"))
                                return result
                            
                            # Show progress
                            active_agent = None
                            for agent, status in agent_status.items():
                                if status == "processing":
                                    active_agent = agent
                                    break
                            
                            if active_agent:
                                print(f"    🔄 {active_agent.title()} agent working... ({elapsed_time}s)")
                        
                        else:
                            result["errors"].append(f"Status check failed: HTTP {response.status}")
                            return result
                            
                except Exception as e:
                    result["errors"].append(f"Monitoring error: {str(e)}")
                    return result
                
                await asyncio.sleep(poll_interval)
                elapsed_time += poll_interval
            
            result["errors"].append("Processing timeout")
            return result
    
    async def validate_generated_files(self, job_id, scenario):
        """Validate the generated files meet expectations"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.backend_url}/api/vibe-coding/files/{job_id}") as response:
                    if response.status == 200:
                        files_data = await response.json()
                        files = files_data.get("files", [])
                        
                        if len(files) < scenario["min_files"]:
                            return False
                        
                        # Check for expected files
                        file_names = [f["name"] for f in files]
                        for expected in scenario["expected_files"]:
                            if not any(expected in name for name in file_names):
                                return False
                        
                        return True
                    return False
            except:
                return False
    
    async def test_download(self, job_id, scenario):
        """Test download functionality"""
        result = {"success": False, "zip_size": 0, "error": None}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.backend_url}/api/download/{job_id}") as response:
                    if response.status == 200:
                        zip_content = await response.read()
                        result["zip_size"] = len(zip_content)
                        
                        # Validate zip content
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                            temp_zip.write(zip_content)
                            temp_zip_path = temp_zip.name
                        
                        try:
                            with zipfile.ZipFile(temp_zip_path, 'r') as zipf:
                                file_names = zipf.namelist()
                                if len(file_names) >= scenario["min_files"]:
                                    result["success"] = True
                                else:
                                    result["error"] = f"Zip contains only {len(file_names)} files"
                        except Exception as e:
                            result["error"] = f"Invalid zip file: {e}"
                        finally:
                            os.unlink(temp_zip_path)
                    else:
                        result["error"] = f"HTTP {response.status}"
            except Exception as e:
                result["error"] = str(e)
        
        return result
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        
        print("\n" + "=" * 60)
        print("🏁 COMPREHENSIVE INTEGRATION TEST REPORT")
        print("=" * 60)
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Test Scenarios: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {total_tests - successful_tests}")
        print(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"\n  Test {i}: {result['scenario']} - {status}")
            print(f"    Generation Time: {result['generation_time']:.1f}s")
            print(f"    Files Generated: {result['files_generated']}")
            print(f"    Agent Phases: {sum(result['phases'].values())}/6 completed")
            print(f"    Download: {'✅' if result['download_success'] else '❌'}")
            
            if result["errors"]:
                print(f"    Errors: {', '.join(result['errors'])}")
        
        # Final assessment
        print(f"\n🎯 PLATFORM READINESS ASSESSMENT:")
        if successful_tests == total_tests:
            print(f"✅ EXCELLENT: Platform is fully functional across all test scenarios")
            print(f"✅ All agent workflows complete successfully")
            print(f"✅ File generation produces working projects")
            print(f"✅ Download system delivers complete projects")
            print(f"🚀 READY FOR PRODUCTION DEPLOYMENT")
        elif successful_tests >= total_tests * 0.8:
            print(f"👍 GOOD: Platform works well for most scenarios")
            print(f"⚠️  Minor issues detected - address before full release")
        elif successful_tests >= total_tests * 0.5:
            print(f"⚠️  FAIR: Platform has basic functionality but significant issues")
            print(f"🔧 Major improvements needed before user release")
        else:
            print(f"❌ POOR: Platform has critical functionality issues")
            print(f"🚨 Not ready for users - requires major fixes")
        
        print("\n" + "=" * 60)

async def main():
    """Run comprehensive integration tests"""
    tester = VibeIntegrationTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())