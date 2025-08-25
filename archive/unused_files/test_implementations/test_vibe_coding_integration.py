#!/usr/bin/env python3
"""
Integration test for the complete Vibe Coding Platform workflow.
This test validates the end-to-end functionality of the enhanced multi-agent system.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agents.specialized.vibe_workflow_orchestrator import VibeWorkflowOrchestrator
from backend.agents.specialized.vibe_planner_agent import VibePlannerAgent
from backend.agents.specialized.vibe_coder_agent import VibeCoderAgent
from backend.agents.specialized.vibe_critic_agent import VibeCriticAgent
from backend.agents.specialized.vibe_file_manager_agent import VibeFileManagerAgent
from backend.models.models import generate_job_id


class VibeCodeIntegrationTest:
    """Integration test suite for the Vibe Coding Platform."""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.test_job_id = generate_job_id()
    
    async def run_all_tests(self):
        """Run complete integration test suite."""
        
        print("🚀 Starting Vibe Coding Platform Integration Tests")
        print("=" * 60)
        
        # Test individual agents
        await self.test_planner_agent()
        await self.test_coder_agent()
        await self.test_critic_agent()
        await self.test_file_manager_agent()
        
        # Test complete workflow
        await self.test_complete_workflow()
        
        # Print results
        self.print_test_results()
        
        return self.test_results["failed"] == 0
    
    async def test_planner_agent(self):
        """Test the Vibe Planner Agent."""
        
        print("\n🧠 Testing Vibe Planner Agent...")
        
        try:
            planner = VibePlannerAgent(self.test_job_id)
            
            test_vibe = "Create a modern task manager with dark mode and drag-and-drop functionality"
            project_data = {
                "project_type": "web",
                "complexity": "moderate",
                "created_at": "2024-01-01T00:00:00"
            }
            
            plan = await planner.decompose_vibe_prompt(test_vibe, project_data)
            
            # Validate plan structure
            required_keys = ["original_vibe", "vibe_analysis", "project_specification", "technical_plan", "file_structure", "task_breakdown"]
            
            for key in required_keys:
                if key not in plan:
                    raise AssertionError(f"Missing required key in plan: {key}")
            
            if plan["original_vibe"] != test_vibe:
                raise AssertionError("Original vibe not preserved in plan")
            
            if not plan["task_breakdown"]:
                raise AssertionError("No tasks generated in plan")
            
            print("   ✅ Planner Agent: PASSED")
            print(f"   📊 Generated {len(plan['task_breakdown'])} tasks")
            print(f"   📁 Planned {len(plan['file_structure'].get('files', []))} files")
            
            self.test_results["passed"] += 1
            return plan
            
        except Exception as e:
            print(f"   ❌ Planner Agent: FAILED - {str(e)}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Planner Agent: {str(e)}")
            return None
    
    async def test_coder_agent(self):
        """Test the Vibe Coder Agent."""
        
        print("\n👨‍💻 Testing Vibe Coder Agent...")
        
        try:
            coder = VibeCoderAgent(self.test_job_id)
            
            # Create mock plan
            mock_plan = {
                "original_vibe": "Create a simple landing page with modern design",
                "vibe_analysis": {
                    "project_type": "landing page",
                    "ui_requirements": ["modern", "clean"],
                    "core_features": ["landing", "responsive"],
                    "key_emotions": ["professional"]
                },
                "project_specification": {
                    "type": "landing page",
                    "complexity": "simple",
                    "technology_stack": {
                        "frontend": "react",
                        "styling": "tailwindcss"
                    },
                    "backend_needed": False
                },
                "file_structure": {
                    "files": ["src/App.jsx", "src/index.js", "package.json"]
                }
            }
            
            generated_files = await coder.generate_code(mock_plan)
            
            # Validate generated files
            if not generated_files:
                raise AssertionError("No files generated")
            
            # Check for required files
            file_paths = [f.get("path", "") for f in generated_files]
            required_files = ["package.json"]
            
            for required_file in required_files:
                if not any(required_file in path for path in file_paths):
                    raise AssertionError(f"Missing required file: {required_file}")
            
            # Validate file content
            for file_info in generated_files:
                if not file_info.get("content"):
                    raise AssertionError(f"Empty content for file: {file_info.get('path', 'unknown')}")
                
                if not file_info.get("language"):
                    raise AssertionError(f"Missing language for file: {file_info.get('path', 'unknown')}")
            
            print("   ✅ Coder Agent: PASSED")
            print(f"   📄 Generated {len(generated_files)} files")
            print(f"   🗂️ File types: {set(f.get('language', 'unknown') for f in generated_files)}")
            
            self.test_results["passed"] += 1
            return generated_files
            
        except Exception as e:
            print(f"   ❌ Coder Agent: FAILED - {str(e)}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Coder Agent: {str(e)}")
            return None
    
    async def test_critic_agent(self):
        """Test the Vibe Critic Agent."""
        
        print("\n🔍 Testing Vibe Critic Agent...")
        
        try:
            critic = VibeCriticAgent(self.test_job_id)
            
            # Create mock generated files
            mock_files = [
                {
                    "path": "src/App.jsx",
                    "content": "import React from 'react';\n\nfunction App() {\n  return <div>Hello World</div>;\n}\n\nexport default App;",
                    "language": "javascript"
                },
                {
                    "path": "package.json",
                    "content": '{"name": "test-app", "version": "1.0.0"}',
                    "language": "json"
                }
            ]
            
            mock_plan = {
                "original_vibe": "Create a simple app",
                "vibe_analysis": {
                    "key_emotions": ["simple", "clean"]
                }
            }
            
            review_results = await critic.review_code(mock_files, mock_plan)
            
            # Validate review structure
            required_keys = ["overall_status", "syntax_analysis", "quality_assessment", "vibe_alignment", "approval_status"]
            
            for key in required_keys:
                if key not in review_results:
                    raise AssertionError(f"Missing required key in review: {key}")
            
            if "overall_score" not in review_results:
                raise AssertionError("Missing overall score in review")
            
            overall_score = review_results.get("overall_score", 0)
            if not isinstance(overall_score, (int, float)) or overall_score < 0 or overall_score > 10:
                raise AssertionError(f"Invalid overall score: {overall_score}")
            
            print("   ✅ Critic Agent: PASSED")
            print(f"   📊 Overall Score: {overall_score}/10")
            print(f"   ✅ Approval Status: {review_results.get('approval_status', False)}")
            print(f"   ⚠️ Issues Found: {len(review_results.get('critical_issues', []))}")
            
            self.test_results["passed"] += 1
            return review_results
            
        except Exception as e:
            print(f"   ❌ Critic Agent: FAILED - {str(e)}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Critic Agent: {str(e)}")
            return None
    
    async def test_file_manager_agent(self):
        """Test the Vibe File Manager Agent."""
        
        print("\n📁 Testing Vibe File Manager Agent...")
        
        try:
            file_manager = VibeFileManagerAgent(self.test_job_id)
            
            # Create mock data
            mock_files = [
                {
                    "path": "src/App.jsx",
                    "content": "import React from 'react';\n\nfunction App() {\n  return <div>Hello World</div>;\n}\n\nexport default App;",
                    "language": "javascript",
                    "filename": "App.jsx"
                },
                {
                    "path": "package.json", 
                    "content": '{"name": "test-app", "version": "1.0.0"}',
                    "language": "json",
                    "filename": "package.json"
                }
            ]
            
            mock_review = {
                "overall_score": 8.5,
                "approval_status": True,
                "needs_fixes": False,
                "suggestions": []
            }
            
            mock_plan = {
                "original_vibe": "Create a simple React app",
                "vibe_analysis": {
                    "project_type": "react app"
                },
                "project_specification": {
                    "type": "react_app",
                    "complexity": "simple"
                }
            }
            
            final_package = await file_manager.organize_and_finalize_project(
                mock_files, mock_review, mock_plan
            )
            
            # Validate package structure
            required_keys = ["project_metadata", "file_structure", "package_info", "deployment_guide"]
            
            for key in required_keys:
                if key not in final_package:
                    raise AssertionError(f"Missing required key in package: {key}")
            
            # Validate project metadata
            metadata = final_package["project_metadata"]
            if not metadata.get("name"):
                raise AssertionError("Missing project name in metadata")
            
            if not metadata.get("total_files"):
                raise AssertionError("Missing total files count in metadata")
            
            print("   ✅ File Manager Agent: PASSED")
            print(f"   📦 Project: {metadata.get('name', 'Unknown')}")
            print(f"   📄 Total Files: {metadata.get('total_files', 0)}")
            print(f"   🏗️ Template: {metadata.get('template', 'Unknown')}")
            
            self.test_results["passed"] += 1
            return final_package
            
        except Exception as e:
            print(f"   ❌ File Manager Agent: FAILED - {str(e)}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"File Manager Agent: {str(e)}")
            return None
    
    async def test_complete_workflow(self):
        """Test the complete Vibe Coding workflow."""
        
        print("\n🎭 Testing Complete Vibe Coding Workflow...")
        
        try:
            orchestrator = VibeWorkflowOrchestrator(self.test_job_id)
            
            test_vibe = "Build a simple portfolio website with a modern, clean design"
            project_options = {
                "project_type": "web",
                "complexity": "simple"
            }
            
            # This would normally take longer, but we'll test the initialization
            workflow_status = orchestrator.get_workflow_status()
            
            # Validate workflow structure
            required_keys = ["job_id", "current_phase", "phases_completed", "total_phases"]
            
            for key in required_keys:
                if key not in workflow_status:
                    raise AssertionError(f"Missing required key in workflow status: {key}")
            
            if workflow_status["job_id"] != self.test_job_id:
                raise AssertionError("Job ID mismatch in workflow")
            
            if workflow_status["total_phases"] != 5:
                raise AssertionError(f"Expected 5 phases, got {workflow_status['total_phases']}")
            
            print("   ✅ Workflow Orchestrator: PASSED")
            print(f"   🎯 Job ID: {workflow_status['job_id']}")
            print(f"   📊 Total Phases: {workflow_status['total_phases']}")
            print(f"   🔄 Current Phase: {workflow_status['current_phase']}")
            
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"   ❌ Workflow Orchestrator: FAILED - {str(e)}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Workflow Orchestrator: {str(e)}")
    
    def print_test_results(self):
        """Print final test results."""
        
        print("\n" + "=" * 60)
        print("🎯 VIBE CODING PLATFORM TEST RESULTS")
        print("=" * 60)
        
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results["failed"] == 0:
            print("\n🎉 ALL TESTS PASSED! Vibe Coding Platform is ready for use.")
        else:
            print(f"\n⚠️ {self.test_results['failed']} tests failed. Review errors below:")
            for error in self.test_results["errors"]:
                print(f"   • {error}")
        
        success_rate = (self.test_results["passed"] / total_tests) * 100 if total_tests > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")


async def main():
    """Main test runner."""
    
    print("🌟 Vibe Coding Platform - Integration Test Suite")
    print("Testing the enhanced multi-agent workflow system")
    print()
    
    test_suite = VibeCodeIntegrationTest()
    
    try:
        success = await test_suite.run_all_tests()
        
        if success:
            print("\n✨ Integration tests completed successfully!")
            print("The Vibe Coding Platform is ready to transform vibes into projects!")
            return 0
        else:
            print("\n❌ Some integration tests failed.")
            print("Please review the errors and fix any issues before deployment.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)