#!/usr/bin/env python3
"""
Basic Structure Test for Enhanced 6-Agent Code Generation System
Tests file existence and basic structure without external dependencies
"""

import json
import time
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Basic6AgentStructureTest:
    """Basic structure test suite for the 6-agent system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
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
    
    def test_agent_files_exist(self) -> bool:
        """Test that all 6 agent files exist"""
        logger.info("📁 Testing agent file existence...")
        
        agent_files = [
            'agents/vibe_workflow_orchestrator_agent.py',
            'agents/vibe_qa_validator_agent.py',
            'agents/vibe_planner_agent.py',
            'agents/vibe_coder_agent.py',
            'agents/vibe_critic_agent.py',
            'agents/vibe_file_manager_agent.py'
        ]
        
        all_exist = True
        for agent_file in agent_files:
            file_path = self.project_root / agent_file
            if file_path.exists():
                size = file_path.stat().st_size
                self.log_test_result(f"Agent File: {agent_file.split('/')[-1]}", True, f"Size: {size} bytes")
            else:
                self.log_test_result(f"Agent File: {agent_file.split('/')[-1]}", False, "File not found")
                all_exist = False
        
        return all_exist
    
    def test_qa_validator_structure(self) -> bool:
        """Test QA Validator agent file structure"""
        logger.info("🔍 Testing QA Validator structure...")
        
        qa_file = self.project_root / 'agents/vibe_qa_validator_agent.py'
        if not qa_file.exists():
            self.log_test_result("QA Validator File", False, "File not found")
            return False
        
        # Read and check content
        with open(qa_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            'validate_project',
            'generate_qa_report',
            '_validate_compilation',
            '_run_functional_tests',
            '_run_security_scan',
            '_test_performance',
            '_calculate_quality_score'
        ]
        
        all_methods_present = True
        for method in required_methods:
            if f"def {method}" in content or f"async def {method}" in content:
                self.log_test_result(f"QA Method: {method}", True, "Method found")
            else:
                self.log_test_result(f"QA Method: {method}", False, "Method missing")
                all_methods_present = False
        
        return all_methods_present
    
    def test_orchestrator_enhancements(self) -> bool:
        """Test orchestrator enhancements for 6-agent system"""
        logger.info("🎭 Testing orchestrator enhancements...")
        
        orchestrator_file = self.project_root / 'agents/vibe_workflow_orchestrator_agent.py'
        if not orchestrator_file.exists():
            self.log_test_result("Orchestrator File", False, "File not found")
            return False
        
        with open(orchestrator_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for QA Validator import
        if "VibeQAValidatorAgent" in content:
            self.log_test_result("QA Validator Import", True, "Import found")
        else:
            self.log_test_result("QA Validator Import", False, "Import missing")
            return False
        
        # Check for enhanced orchestration method
        if "orchestrate_project_creation" in content:
            self.log_test_result("Enhanced Orchestration Method", True, "Method found")
        else:
            self.log_test_result("Enhanced Orchestration Method", False, "Method missing")
            return False
        
        # Check for QA validator in workflow steps
        if "'qa_validator'" in content:
            self.log_test_result("QA Validator in Workflow", True, "Found in workflow")
        else:
            self.log_test_result("QA Validator in Workflow", False, "Missing from workflow")
            return False
        
        return True
    
    def test_frontend_6_agent_support(self) -> bool:
        """Test frontend support for 6-agent system"""
        logger.info("🖥️ Testing frontend 6-agent support...")
        
        frontend_file = self.project_root / 'frontend/enhanced_vibe_frontend.html'
        if not frontend_file.exists():
            self.log_test_result("Frontend File", False, "File not found")
            return False
        
        with open(frontend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for QA Validator agent card
        if 'agent-qa_validator' in content:
            self.log_test_result("QA Validator UI Card", True, "Agent card found")
        else:
            self.log_test_result("QA Validator UI Card", False, "Agent card missing")
            return False
        
        # Check for QA metrics display
        if 'qa-metrics' in content:
            self.log_test_result("QA Metrics UI", True, "QA metrics UI found")
        else:
            self.log_test_result("QA Metrics UI", False, "QA metrics UI missing")
            return False
        
        # Check for enhanced WebSocket handling
        if 'updateQAMetrics' in content:
            self.log_test_result("QA Metrics JavaScript", True, "QA update function found")
        else:
            self.log_test_result("QA Metrics JavaScript", False, "QA update function missing")
            return False
        
        return True
    
    def test_backend_6_agent_support(self) -> bool:
        """Test backend support for 6-agent system"""
        logger.info("⚙️ Testing backend 6-agent support...")
        
        backend_file = self.project_root / 'backend/simple_app.py'
        if not backend_file.exists():
            self.log_test_result("Backend File", False, "File not found")
            return False
        
        with open(backend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for QA report endpoint
        if '/api/vibe-coding/qa-report/' in content:
            self.log_test_result("QA Report Endpoint", True, "Endpoint found")
        else:
            self.log_test_result("QA Report Endpoint", False, "Endpoint missing")
            return False
        
        # Check for enhanced orchestration call
        if 'orchestrate_project_creation' in content:
            self.log_test_result("Enhanced Orchestration Call", True, "Call found")
        else:
            self.log_test_result("Enhanced Orchestration Call", False, "Call missing")
            return False
        
        # Check for 6-agent tracking
        if 'qa_validator' in content:
            self.log_test_result("QA Validator Backend Support", True, "Found in backend")
        else:
            self.log_test_result("QA Validator Backend Support", False, "Missing from backend")
            return False
        
        return True
    
    def test_configuration_files(self) -> bool:
        """Test configuration files for 6-agent system"""
        logger.info("⚙️ Testing configuration files...")
        
        # Test config.py
        config_py = self.project_root / 'config/config.py'
        if config_py.exists():
            with open(config_py, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'total_agents: int = 6' in content:
                self.log_test_result("Config.py 6-Agent Setting", True, "total_agents = 6")
            else:
                self.log_test_result("Config.py 6-Agent Setting", False, "Setting missing")
                return False
                
            if 'qa_validation_enabled' in content:
                self.log_test_result("QA Validation Config", True, "QA settings found")
            else:
                self.log_test_result("QA Validation Config", False, "QA settings missing")
                return False
        else:
            self.log_test_result("Config.py File", False, "File not found")
            return False
        
        # Test config.json
        config_json = self.project_root / 'config/config.json'
        if config_json.exists():
            with open(config_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('agents', {}).get('total_agents') == 6:
                self.log_test_result("Config.json 6-Agent Setting", True, "total_agents = 6")
            else:
                self.log_test_result("Config.json 6-Agent Setting", False, "Setting missing")
                return False
                
            if 'qa_validation' in data.get('agents', {}):
                self.log_test_result("QA Validation JSON Config", True, "QA config found")
            else:
                self.log_test_result("QA Validation JSON Config", False, "QA config missing")
                return False
        else:
            self.log_test_result("Config.json File", False, "File not found")
            return False
        
        # Test package.json
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            with open(package_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if '6-agent' in data.get('name', ''):
                self.log_test_result("Package.json Name Update", True, "6-agent in name")
            else:
                self.log_test_result("Package.json Name Update", False, "Name not updated")
                return False
                
            if 'qa-validation' in data.get('keywords', []):
                self.log_test_result("Package.json QA Keywords", True, "QA keywords found")
            else:
                self.log_test_result("Package.json QA Keywords", False, "QA keywords missing")
                return False
        else:
            self.log_test_result("Package.json File", False, "File not found")
            return False
        
        return True
    
    def test_websocket_enhancements(self) -> bool:
        """Test WebSocket enhancements for 6-agent system"""
        logger.info("🌐 Testing WebSocket enhancements...")
        
        ws_file = self.project_root / 'api/websocket_handler.py'
        if not ws_file.exists():
            self.log_test_result("WebSocket File", False, "File not found")
            return False
        
        with open(ws_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for QA metrics support
        if 'QAMetrics' in content:
            self.log_test_result("QA Metrics Class", True, "QAMetrics class found")
        else:
            self.log_test_result("QA Metrics Class", False, "QAMetrics class missing")
            return False
        
        # Check for 6-agent tracking method
        if 'initialize_6_agent_tracking' in content:
            self.log_test_result("6-Agent Tracking Method", True, "Method found")
        else:
            self.log_test_result("6-Agent Tracking Method", False, "Method missing")
            return False
        
        # Check for QA metrics update method
        if 'update_qa_metrics' in content:
            self.log_test_result("QA Metrics Update Method", True, "Method found")
        else:
            self.log_test_result("QA Metrics Update Method", False, "Method missing")
            return False
        
        return True
    
    def run_basic_test_suite(self) -> dict:
        """Run basic test suite for 6-agent system structure"""
        logger.info("🚀 Starting basic 6-agent system structure test...")
        start_time = time.time()
        
        test_methods = [
            self.test_agent_files_exist,
            self.test_qa_validator_structure,
            self.test_orchestrator_enhancements,
            self.test_frontend_6_agent_support,
            self.test_backend_6_agent_support,
            self.test_configuration_files,
            self.test_websocket_enhancements
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test_result(f"Test Method: {test_method.__name__}", False, f"Error: {str(e)}")
        
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
        logger.info("🎯 6-AGENT SYSTEM STRUCTURE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Tests Passed: {self.test_results['tests_passed']} ✅")
        logger.info(f"Tests Failed: {self.test_results['tests_failed']} ❌")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Execution Time: {execution_time:.2f} seconds")
        logger.info(f"Overall Status: {self.test_results['overall_status'].upper()}")
        logger.info("=" * 60)
        
        if self.test_results['overall_status'] == 'success':
            logger.info("🎉 ALL STRUCTURE TESTS PASSED! 6-agent system structure is correct.")
        else:
            logger.error("💥 SOME TESTS FAILED! Please review structure issues.")
        
        return self.test_results

def main():
    """Main test execution function"""
    print("🔥 Enhanced 6-Agent Code Generation System - Structure Test")
    print("=" * 70)
    
    tester = Basic6AgentStructureTest()
    results = tester.run_basic_test_suite()
    
    # Write results to file
    results_file = Path(__file__).parent / "6_agent_structure_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Test results saved to: {results_file}")
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_status'] == 'success' else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()