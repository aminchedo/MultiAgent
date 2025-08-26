#!/usr/bin/env python3
"""
Comprehensive Integration Test for Enhanced 6-Agent Code Generation System
Tests the complete workflow from initialization to QA validation and delivery
"""

import asyncio
import json
import time
import sys
from pathlib import Path
import logging
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import enhanced 6-agent components
from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
from agents.vibe_qa_validator_agent import VibeQAValidatorAgent
from agents.vibe_planner_agent import VibePlannerAgent
from agents.vibe_coder_agent import VibeCoderAgent
from agents.vibe_critic_agent import VibeCriticAgent
from agents.vibe_file_manager_agent import VibeFileManagerAgent
from api.websocket_handler import ConnectionManager
from config.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Enhanced6AgentIntegrationTest:
    """Comprehensive test suite for the 6-agent system"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.settings = Settings()
        self.test_results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': [],
            'overall_status': 'unknown'
        }
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result and update counters"""
        status = "✅ PASSED" if success else "❌ FAILED"
        message = f"{status}: {test_name}"
        if details:
            message += f" - {details}"
        
        logger.info(message)
        
        if success:
            self.test_results['tests_passed'] += 1
        else:
            self.test_results['tests_failed'] += 1
            
        self.test_results['test_details'].append({
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': time.time()
        })
    
    async def test_agent_initialization(self) -> bool:
        """Test that all 6 agents can be initialized properly"""
        logger.info("🔧 Testing 6-agent initialization...")
        
        try:
            # Test Orchestrator Agent
            orchestrator = VibeWorkflowOrchestratorAgent()
            self.log_test_result("Orchestrator Agent Initialization", True, "Agent created successfully")
            
            # Test QA Validator Agent
            qa_validator = VibeQAValidatorAgent(websocket_manager=self.connection_manager)
            self.log_test_result("QA Validator Agent Initialization", True, "Agent created with WebSocket support")
            
            # Test Planner Agent
            planner = VibePlannerAgent()
            self.log_test_result("Planner Agent Initialization", True, "Agent created successfully")
            
            # Test Coder Agent
            coder = VibeCoderAgent()
            self.log_test_result("Coder Agent Initialization", True, "Agent created successfully")
            
            # Test Critic Agent
            critic = VibeCriticAgent()
            self.log_test_result("Critic Agent Initialization", True, "Agent created successfully")
            
            # Test File Manager Agent
            file_manager = VibeFileManagerAgent()
            self.log_test_result("File Manager Agent Initialization", True, "Agent created successfully")
            
            return True
            
        except Exception as e:
            self.log_test_result("Agent Initialization", False, f"Failed to initialize agents: {str(e)}")
            return False
    
    async def test_websocket_manager(self) -> bool:
        """Test WebSocket manager for 6-agent tracking"""
        logger.info("🌐 Testing WebSocket manager for 6-agent system...")
        
        try:
            # Test 6-agent initialization
            test_job_id = "test-job-123"
            await self.connection_manager.initialize_6_agent_tracking(test_job_id)
            
            # Verify all 6 agents are tracked
            if test_job_id in self.connection_manager.agent_status:
                agent_status = self.connection_manager.agent_status[test_job_id]
                expected_agents = ['orchestrator', 'planner', 'coder', 'critic', 'file_manager', 'qa_validator']
                
                if all(agent in agent_status for agent in expected_agents):
                    self.log_test_result("WebSocket 6-Agent Tracking", True, "All 6 agents initialized in WebSocket manager")
                else:
                    missing_agents = [agent for agent in expected_agents if agent not in agent_status]
                    self.log_test_result("WebSocket 6-Agent Tracking", False, f"Missing agents: {missing_agents}")
                    return False
            else:
                self.log_test_result("WebSocket 6-Agent Tracking", False, "Job not found in agent status")
                return False
            
            # Test QA metrics update
            test_qa_metrics = {
                'quality_score': 92,
                'tests_passed': 15,
                'total_tests': 18,
                'security_status': 'secure',
                'final_approval': True
            }
            
            await self.connection_manager.update_qa_metrics(test_job_id, test_qa_metrics)
            self.log_test_result("QA Metrics WebSocket Update", True, "QA metrics updated successfully")
            
            return True
            
        except Exception as e:
            self.log_test_result("WebSocket Manager Test", False, f"WebSocket test failed: {str(e)}")
            return False
    
    async def test_qa_validator_functionality(self) -> bool:
        """Test QA Validator comprehensive validation"""
        logger.info("🔍 Testing QA Validator functionality...")
        
        try:
            qa_validator = VibeQAValidatorAgent(websocket_manager=self.connection_manager)
            
            # Create mock project files for testing
            mock_project_files = {
                'frontend_files': {
                    'package.json': json.dumps({
                        "name": "test-project",
                        "version": "1.0.0",
                        "dependencies": {
                            "react": "^18.2.0",
                            "typescript": "^5.0.0"
                        }
                    }),
                    'src/App.tsx': """
import React from 'react';

const App: React.FC = () => {
    return (
        <div className="App">
            <h1>Test Application</h1>
        </div>
    );
};

export default App;
                    """,
                    'tsconfig.json': json.dumps({
                        "compilerOptions": {
                            "target": "es5",
                            "module": "esnext",
                            "strict": true
                        }
                    })
                },
                'backend_files': {
                    'main.py': """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
                    """,
                    'requirements.txt': """
fastapi==0.104.1
uvicorn==0.24.0
                    """
                },
                'test_files': {
                    'src/__tests__/App.test.tsx': """
import { render, screen } from '@testing-library/react';
import App from '../App';

test('renders test application', () => {
    render(<App />);
    const element = screen.getByText(/Test Application/i);
    expect(element).toBeInTheDocument();
});
                    """,
                    'tests/test_main.py': """
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
                    """
                }
            }
            
            # Test QA validation
            test_job_id = "qa-test-job-456"
            validation_results = await qa_validator.validate_project(mock_project_files, test_job_id)
            
            # Verify validation results structure
            required_keys = ['job_id', 'validation_status', 'quality_score', 'final_approval']
            if all(key in validation_results for key in required_keys):
                self.log_test_result("QA Validation Structure", True, "All required validation keys present")
            else:
                missing_keys = [key for key in required_keys if key not in validation_results]
                self.log_test_result("QA Validation Structure", False, f"Missing keys: {missing_keys}")
                return False
            
            # Verify validation completion
            if validation_results['validation_status'] == 'completed':
                self.log_test_result("QA Validation Completion", True, f"Quality Score: {validation_results['quality_score']}%")
            else:
                self.log_test_result("QA Validation Completion", False, f"Status: {validation_results['validation_status']}")
                return False
            
            # Test QA report generation
            qa_report = await qa_validator.generate_qa_report(validation_results)
            if qa_report and len(qa_report) > 100:  # Basic report length check
                self.log_test_result("QA Report Generation", True, f"Generated {len(qa_report)} character report")
            else:
                self.log_test_result("QA Report Generation", False, "Report too short or empty")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("QA Validator Functionality", False, f"QA validation failed: {str(e)}")
            return False
    
    async def test_orchestrator_6_agent_workflow(self) -> bool:
        """Test the complete 6-agent workflow orchestration"""
        logger.info("🎭 Testing 6-agent workflow orchestration...")
        
        try:
            # Create orchestrator with mock progress callback
            async def mock_progress_callback(job_id, agent_name, status, progress, task, details=None):
                logger.info(f"Progress: {agent_name} -> {status} ({progress}%) - {task}")
            
            orchestrator = VibeWorkflowOrchestratorAgent(progress_callback=mock_progress_callback)
            
            # Verify all 6 workflow steps are defined
            expected_agents = ['planner', 'coder', 'critic', 'file_manager', 'qa_validator']
            workflow_agents = [step.agent_name for step in orchestrator.workflow_steps]
            
            if all(agent in workflow_agents for agent in expected_agents):
                self.log_test_result("6-Agent Workflow Definition", True, f"All 5 workflow agents defined: {workflow_agents}")
            else:
                missing = [agent for agent in expected_agents if agent not in workflow_agents]
                self.log_test_result("6-Agent Workflow Definition", False, f"Missing workflow agents: {missing}")
                return False
            
            # Test orchestration method exists
            if hasattr(orchestrator, 'orchestrate_project_creation'):
                self.log_test_result("Orchestration Method Available", True, "orchestrate_project_creation method exists")
            else:
                self.log_test_result("Orchestration Method Available", False, "Missing orchestrate_project_creation method")
                return False
            
            # Test agent initialization
            if len(orchestrator.agent_instances) >= 5:  # Should have at least 5 agents (excluding orchestrator)
                self.log_test_result("Agent Instances Initialization", True, f"Initialized {len(orchestrator.agent_instances)} agents")
            else:
                self.log_test_result("Agent Instances Initialization", False, f"Only {len(orchestrator.agent_instances)} agents initialized")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("6-Agent Orchestrator Workflow", False, f"Orchestrator test failed: {str(e)}")
            return False
    
    async def test_configuration_consistency(self) -> bool:
        """Test configuration consistency across all components"""
        logger.info("⚙️ Testing configuration consistency...")
        
        try:
            # Test settings loading
            settings = Settings()
            
            # Verify 6-agent specific settings
            if hasattr(settings, 'total_agents') and settings.total_agents == 6:
                self.log_test_result("6-Agent Configuration", True, "total_agents = 6")
            else:
                self.log_test_result("6-Agent Configuration", False, f"total_agents = {getattr(settings, 'total_agents', 'undefined')}")
                return False
            
            # Verify QA validation settings
            qa_settings = ['qa_validation_enabled', 'minimum_quality_score', 'qa_timeout_seconds']
            for setting in qa_settings:
                if hasattr(settings, setting):
                    value = getattr(settings, setting)
                    self.log_test_result(f"QA Setting: {setting}", True, f"{setting} = {value}")
                else:
                    self.log_test_result(f"QA Setting: {setting}", False, f"Missing setting: {setting}")
                    return False
            
            # Test WebSocket configuration for 6-agent system
            ws_settings = ['ws_agent_update_interval', 'ws_qa_progress_detail']
            for setting in ws_settings:
                if hasattr(settings, setting):
                    value = getattr(settings, setting)
                    self.log_test_result(f"WebSocket Setting: {setting}", True, f"{setting} = {value}")
                else:
                    self.log_test_result(f"WebSocket Setting: {setting}", False, f"Missing setting: {setting}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Configuration Consistency", False, f"Configuration test failed: {str(e)}")
            return False
    
    async def test_file_structure_integrity(self) -> bool:
        """Test that all required files for 6-agent system exist"""
        logger.info("📁 Testing file structure integrity...")
        
        try:
            required_files = [
                'agents/vibe_workflow_orchestrator_agent.py',
                'agents/vibe_qa_validator_agent.py',
                'agents/vibe_planner_agent.py',
                'agents/vibe_coder_agent.py',
                'agents/vibe_critic_agent.py',
                'agents/vibe_file_manager_agent.py',
                'api/websocket_handler.py',
                'backend/simple_app.py',
                'frontend/enhanced_vibe_frontend.html',
                'config/config.py',
                'config/config.json',
                'package.json'
            ]
            
            missing_files = []
            for file_path in required_files:
                file_obj = project_root / file_path
                if file_obj.exists():
                    self.log_test_result(f"File Exists: {file_path}", True, f"Size: {file_obj.stat().st_size} bytes")
                else:
                    missing_files.append(file_path)
                    self.log_test_result(f"File Exists: {file_path}", False, "File not found")
            
            if not missing_files:
                self.log_test_result("File Structure Integrity", True, "All required files present")
                return True
            else:
                self.log_test_result("File Structure Integrity", False, f"Missing files: {missing_files}")
                return False
                
        except Exception as e:
            self.log_test_result("File Structure Integrity", False, f"File structure test failed: {str(e)}")
            return False
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run complete test suite for 6-agent system"""
        logger.info("🚀 Starting comprehensive 6-agent system test suite...")
        start_time = time.time()
        
        test_methods = [
            self.test_file_structure_integrity,
            self.test_configuration_consistency,
            self.test_agent_initialization,
            self.test_websocket_manager,
            self.test_qa_validator_functionality,
            self.test_orchestrator_6_agent_workflow
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.log_test_result(f"Test Method: {test_method.__name__}", False, f"Unexpected error: {str(e)}")
        
        # Calculate final results
        total_tests = self.test_results['tests_passed'] + self.test_results['tests_failed']
        success_rate = (self.test_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        execution_time = time.time() - start_time
        
        self.test_results['overall_status'] = 'success' if self.test_results['tests_failed'] == 0 else 'failed'
        self.test_results['success_rate'] = success_rate
        self.test_results['execution_time'] = execution_time
        self.test_results['total_tests'] = total_tests
        
        # Log final summary
        logger.info("=" * 60)
        logger.info("🎯 6-AGENT SYSTEM TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Tests Passed: {self.test_results['tests_passed']} ✅")
        logger.info(f"Tests Failed: {self.test_results['tests_failed']} ❌")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Execution Time: {execution_time:.2f} seconds")
        logger.info(f"Overall Status: {self.test_results['overall_status'].upper()}")
        logger.info("=" * 60)
        
        if self.test_results['overall_status'] == 'success':
            logger.info("🎉 ALL TESTS PASSED! 6-agent system is ready for deployment.")
        else:
            logger.error("💥 SOME TESTS FAILED! Please review and fix issues before deployment.")
        
        return self.test_results

async def main():
    """Main test execution function"""
    print("🔥 Enhanced 6-Agent Code Generation System - Integration Test")
    print("=" * 70)
    
    tester = Enhanced6AgentIntegrationTest()
    results = await tester.run_comprehensive_test_suite()
    
    # Write results to file
    results_file = project_root / "6_agent_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Test results saved to: {results_file}")
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_status'] == 'success' else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())