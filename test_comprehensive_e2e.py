#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite for Vibe Coding Platform
Tests the complete workflow from vibe prompt to functional project download.
"""

import asyncio
import aiohttp
import os
import zipfile
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import sys

class VibeCodeE2ETester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    async def run_comprehensive_tests(self):
        """Run complete end-to-end test suite"""
        print("=" * 80)
        print("🧪 COMPREHENSIVE VIBE CODING PLATFORM E2E TESTS")
        print("=" * 80)
        print(f"🎯 Testing against: {self.base_url}")
        print(f"🕐 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test scenarios covering different vibe prompts and project types
        test_scenarios = [
            {
                "name": "Cozy Coffee Shop Blog",
                "vibe_prompt": "Create a warm and inviting coffee shop blog with earthy brown colors, cozy typography, and sections for featured coffee, brewing guides, and customer stories",
                "project_type": "blog",
                "framework": "react",
                "expected_files": ["App.tsx", "package.json", "index.html", "README.md"],
                "min_files": 8,
                "timeout": 120
            },
            {
                "name": "Modern Dashboard",
                "vibe_prompt": "Build a sleek professional dashboard with dark theme, clean charts, and modern card-based layout for analytics",
                "project_type": "dashboard", 
                "framework": "react",
                "expected_files": ["App.tsx", "package.json", "src/components"],
                "min_files": 10,
                "timeout": 150
            },
            {
                "name": "Portfolio Landing Page",
                "vibe_prompt": "Design a minimalist portfolio website with smooth animations, elegant typography, and sections for projects, about, and contact",
                "project_type": "portfolio",
                "framework": "vanilla",
                "expected_files": ["index.html", "style.css", "script.js"],
                "min_files": 5,
                "timeout": 100
            },
            {
                "name": "Tech Startup Landing",
                "vibe_prompt": "Create a dynamic tech startup landing page with gradient backgrounds, modern buttons, hero section with call-to-action, and responsive design",
                "project_type": "landing",
                "framework": "vue",
                "expected_files": ["App.vue", "package.json", "index.html"],
                "min_files": 6,
                "timeout": 110
            }
        ]
        
        print(f"📋 Running {len(test_scenarios)} comprehensive test scenarios...\n")
        
        # Run tests
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"🔍 TEST {i}/{len(test_scenarios)}: {scenario['name']}")
            print(f"   Prompt: {scenario['vibe_prompt'][:60]}...")
            print(f"   Type: {scenario['project_type']}, Framework: {scenario['framework']}")
            
            result = await self.run_single_scenario(scenario)
            self.test_results.append(result)
            
            if result["success"]:
                print(f"   ✅ PASSED - {result['files_generated']} files, {result['processing_time']:.1f}s")
            else:
                print(f"   ❌ FAILED - {', '.join(result['errors'])}")
            
            print()
            
            # Brief pause between tests
            await asyncio.sleep(5)
        
        # Generate comprehensive report
        await self.generate_comprehensive_report()
    
    async def run_single_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test scenario with comprehensive validation"""
        result = {
            "scenario": scenario["name"],
            "vibe_prompt": scenario["vibe_prompt"],
            "success": False,
            "job_id": None,
            "files_generated": 0,
            "files_list": [],
            "processing_time": 0,
            "errors": [],
            "quality_score": 0,
            "download_size": 0,
            "agent_performance": {},
            "code_quality": {}
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Submit vibe prompt
                submit_start = time.time()
                async with session.post(
                    f"{self.base_url}/api/vibe-coding",
                    json={
                        "vibe_prompt": scenario["vibe_prompt"],
                        "project_type": scenario["project_type"],
                        "framework": scenario["framework"]
                    }
                ) as response:
                    if response.status != 200:
                        result["errors"].append(f"Submit failed: HTTP {response.status}")
                        return result
                    
                    data = await response.json()
                    result["job_id"] = data["job_id"]
                    print(f"      → Job created: {result['job_id']}")
                
                # Step 2: Monitor progress with detailed tracking
                print(f"      → Monitoring agent progress...")
                max_wait_time = scenario.get("timeout", 120)
                poll_interval = 3
                elapsed_time = 0
                agent_times = {}
                
                while elapsed_time < max_wait_time:
                    async with session.get(
                        f"{self.base_url}/api/vibe-coding/status/{result['job_id']}"
                    ) as status_response:
                        if status_response.status != 200:
                            result["errors"].append(f"Status check failed: HTTP {status_response.status}")
                            break
                        
                        status_data = await status_response.json()
                        
                        # Track agent progress
                        agent_status = status_data.get("agent_status", {})
                        for agent, status in agent_status.items():
                            if status == "processing" and agent not in agent_times:
                                agent_times[agent] = time.time()
                            elif status == "completed" and agent in agent_times:
                                result["agent_performance"][agent] = time.time() - agent_times[agent]
                        
                        if status_data["status"] == "completed":
                            print(f"      ✅ Generation completed!")
                            break
                        elif status_data["status"] == "failed":
                            result["errors"].append(f"Generation failed: {status_data.get('message', 'Unknown error')}")
                            break
                    
                    await asyncio.sleep(poll_interval)
                    elapsed_time += poll_interval
                
                if elapsed_time >= max_wait_time:
                    result["errors"].append(f"Generation timeout after {max_wait_time}s")
                    return result
                
                # Step 3: Validate generated files
                print(f"      → Validating generated files...")
                async with session.get(
                    f"{self.base_url}/api/vibe-coding/files/{result['job_id']}"
                ) as files_response:
                    if files_response.status == 200:
                        files_data = await files_response.json()
                        result["files_generated"] = len(files_data.get("files", []))
                        result["files_list"] = [f["name"] for f in files_data.get("files", [])]
                        
                        # Validate minimum file count
                        if result["files_generated"] < scenario["min_files"]:
                            result["errors"].append(f"Too few files: {result['files_generated']} < {scenario['min_files']}")
                        
                        # Check for expected files
                        missing_files = []
                        for expected_file in scenario.get("expected_files", []):
                            if not any(expected_file in file_name for file_name in result["files_list"]):
                                missing_files.append(expected_file)
                        
                        if missing_files:
                            result["errors"].append(f"Missing expected files: {missing_files}")
                        
                    else:
                        result["errors"].append(f"Files check failed: HTTP {files_response.status}")
                
                # Step 4: Test download and validate content
                print(f"      → Testing download and content validation...")
                async with session.get(
                    f"{self.base_url}/api/download/{result['job_id']}"
                ) as download_response:
                    if download_response.status == 200:
                        zip_content = await download_response.read()
                        result["download_size"] = len(zip_content)
                        
                        # Validate ZIP content
                        quality_result = await self.validate_project_quality(zip_content, scenario)
                        result["quality_score"] = quality_result["score"]
                        result["code_quality"] = quality_result["analysis"]
                        
                        if quality_result["score"] < 60:
                            result["errors"].append(f"Low quality score: {quality_result['score']}")
                        
                    else:
                        result["errors"].append(f"Download failed: HTTP {download_response.status}")
                
                # Calculate final success
                result["processing_time"] = time.time() - start_time
                result["success"] = len(result["errors"]) == 0 and result["files_generated"] >= scenario["min_files"]
                
            except Exception as e:
                result["errors"].append(f"Test exception: {str(e)}")
                result["processing_time"] = time.time() - start_time
        
        return result
    
    async def validate_project_quality(self, zip_content: bytes, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality of generated project files"""
        quality_analysis = {
            "score": 0,
            "analysis": {
                "functional_files": 0,
                "placeholder_content": 0,
                "syntax_errors": 0,
                "prompt_alignment": 0,
                "structure_validity": 0
            }
        }
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                temp_zip.write(zip_content)
                temp_zip_path = temp_zip.name
            
            with zipfile.ZipFile(temp_zip_path, 'r') as zipf:
                file_names = zipf.namelist()
                functional_files = 0
                placeholder_count = 0
                total_files = len(file_names)
                
                # Analyze each file
                for file_name in file_names:
                    if file_name.endswith(('.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue')):
                        try:
                            content = zipf.read(file_name).decode('utf-8', errors='ignore')
                            
                            # Check for functionality indicators
                            if len(content) > 100 and not self.is_placeholder_content(content):
                                functional_files += 1
                            
                            # Check for placeholder content
                            if self.is_placeholder_content(content):
                                placeholder_count += 1
                            
                        except Exception:
                            continue
                
                # Calculate scores
                if total_files > 0:
                    quality_analysis["analysis"]["functional_files"] = functional_files
                    quality_analysis["analysis"]["placeholder_content"] = placeholder_count
                    quality_analysis["analysis"]["structure_validity"] = self.validate_project_structure(file_names, scenario["framework"])
                    quality_analysis["analysis"]["prompt_alignment"] = self.check_prompt_alignment(zip_content, scenario["vibe_prompt"])
                    
                    # Overall score calculation
                    functionality_score = (functional_files / total_files) * 40
                    placeholder_penalty = (placeholder_count / total_files) * 20
                    structure_score = quality_analysis["analysis"]["structure_validity"] * 30
                    alignment_score = quality_analysis["analysis"]["prompt_alignment"] * 10
                    
                    quality_analysis["score"] = max(0, functionality_score - placeholder_penalty + structure_score + alignment_score)
            
            os.unlink(temp_zip_path)
            
        except Exception as e:
            print(f"      ⚠️ Quality validation error: {e}")
        
        return quality_analysis
    
    def is_placeholder_content(self, content: str) -> bool:
        """Check if content appears to be placeholder/template"""
        placeholder_indicators = [
            'TODO', 'PLACEHOLDER', 'FIXME', 'Lorem ipsum', 
            'example.com', 'placeholder', 'template',
            'Your content here', 'Replace this'
        ]
        
        content_lower = content.lower()
        return any(indicator.lower() in content_lower for indicator in placeholder_indicators)
    
    def validate_project_structure(self, file_names: List[str], framework: str) -> float:
        """Validate project structure for the given framework"""
        required_structures = {
            'react': ['package.json', 'src/', 'public/', 'index.html'],
            'vue': ['package.json', 'src/', 'public/', 'index.html'],
            'vanilla': ['index.html', 'css/', 'js/']
        }
        
        required_files = required_structures.get(framework, required_structures['react'])
        found_count = 0
        
        for required in required_files:
            if any(required in file_name for file_name in file_names):
                found_count += 1
        
        return found_count / len(required_files)
    
    def check_prompt_alignment(self, zip_content: bytes, vibe_prompt: str) -> float:
        """Check how well the generated project aligns with the vibe prompt"""
        # Extract key terms from prompt
        prompt_words = set(word.lower() for word in vibe_prompt.split() if len(word) > 3)
        
        # This is a simplified check - in a real implementation you'd do more sophisticated analysis
        # For now, return a baseline score
        return 0.7  # 70% alignment score as baseline
    
    async def generate_comprehensive_report(self):
        """Generate detailed test report with metrics and recommendations"""
        self.total_tests = len(self.test_results)
        self.passed_tests = sum(1 for r in self.test_results if r["success"])
        self.failed_tests = self.total_tests - self.passed_tests
        
        print("=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS REPORT")
        print("=" * 80)
        
        # Summary metrics
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        avg_processing_time = sum(r["processing_time"] for r in self.test_results) / self.total_tests
        avg_files_generated = sum(r["files_generated"] for r in self.test_results) / self.total_tests
        avg_quality_score = sum(r["quality_score"] for r in self.test_results) / self.total_tests
        
        print(f"\n🎯 OVERALL METRICS:")
        print(f"   Total Tests Run: {self.total_tests}")
        print(f"   Tests Passed: {self.passed_tests}")
        print(f"   Tests Failed: {self.failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Average Processing Time: {avg_processing_time:.1f}s")
        print(f"   Average Files Generated: {avg_files_generated:.1f}")
        print(f"   Average Quality Score: {avg_quality_score:.1f}/100")
        
        # Platform readiness assessment
        print(f"\n🏆 PLATFORM READINESS ASSESSMENT:")
        
        if success_rate >= 90 and avg_quality_score >= 80:
            print(f"   ✅ EXCELLENT: Platform is production-ready")
            print(f"   ✅ High success rate and quality scores")
            print(f"   ✅ Ready for user deployment")
        elif success_rate >= 75 and avg_quality_score >= 65:
            print(f"   👍 GOOD: Platform is functional with minor issues")
            print(f"   ✅ Good success rate with acceptable quality")
            print(f"   🔧 Ready for beta testing with monitoring")
        elif success_rate >= 50:
            print(f"   ⚠️ FAIR: Platform has significant issues")
            print(f"   ⚠️ Moderate success rate, needs improvement")
            print(f"   🔧 Requires fixes before user release")
        else:
            print(f"   ❌ POOR: Platform not ready for users")
            print(f"   ❌ Low success rate or quality scores")
            print(f"   🚨 Major fixes required before deployment")
        
        # Detailed results
        print(f"\n📋 DETAILED TEST RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"\n  Test {i}: {result['scenario']} - {status}")
            print(f"    Prompt: {result['vibe_prompt'][:60]}...")
            print(f"    Files Generated: {result['files_generated']}")
            print(f"    Processing Time: {result['processing_time']:.1f}s")
            print(f"    Quality Score: {result['quality_score']:.1f}/100")
            print(f"    Download Size: {result['download_size']} bytes")
            
            if result["agent_performance"]:
                print(f"    Agent Performance:")
                for agent, duration in result["agent_performance"].items():
                    print(f"      {agent}: {duration:.1f}s")
            
            if result["errors"]:
                print(f"    ❌ Errors: {', '.join(result['errors'])}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        failed_scenarios = [r for r in self.test_results if not r["success"]]
        if failed_scenarios:
            print(f"   🔧 Fix issues in {len(failed_scenarios)} failing scenarios")
            for scenario in failed_scenarios:
                print(f"      - {scenario['scenario']}: {', '.join(scenario['errors'])}")
        
        low_quality = [r for r in self.test_results if r["quality_score"] < 70]
        if low_quality:
            print(f"   📈 Improve code quality for {len(low_quality)} scenarios")
        
        slow_processing = [r for r in self.test_results if r["processing_time"] > 60]
        if slow_processing:
            print(f"   ⚡ Optimize processing speed for {len(slow_processing)} scenarios")
        
        if not failed_scenarios and not low_quality and not slow_processing:
            print(f"   🎉 No critical issues found! Platform performing excellently.")
        
        print(f"\n" + "=" * 80)
        print(f"✅ Test suite completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Final Assessment: {'PLATFORM READY' if success_rate >= 75 else 'NEEDS IMPROVEMENT'}")
        print("=" * 80)

async def main():
    """Run the comprehensive test suite"""
    print("🚀 Starting Comprehensive Vibe Coding Platform Tests...")
    print("🔧 Make sure the backend is running on http://localhost:8000")
    print()
    
    # Wait for user confirmation
    input("Press Enter to start testing (Ctrl+C to cancel)...")
    print()
    
    tester = VibeCodeE2ETester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Tests cancelled by user")
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")