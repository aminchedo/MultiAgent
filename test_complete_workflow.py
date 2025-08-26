#!/usr/bin/env python3
"""
Complete End-to-End Workflow Test
Tests the full 6-agent system with real project generation
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any
from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkflowTester:
    """Complete workflow testing class"""
    
    def __init__(self):
        self.orchestrator = None
        self.test_results = {}
        
    async def initialize_system(self):
        """Initialize the 6-agent system"""
        logger.info("🚀 Initializing 6-agent system...")
        
        try:
            # Create progress callback for real-time updates
            async def progress_callback(progress_data):
                logger.info(f"📊 Progress Update: {progress_data}")
            
            self.orchestrator = VibeWorkflowOrchestratorAgent(progress_callback=progress_callback)
            
            # Verify all agents are initialized
            agent_count = len(self.orchestrator.agent_instances)
            logger.info(f"✅ System initialized with {agent_count} specialist agents + 1 orchestrator = {agent_count + 1} total agents")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def test_simple_project_generation(self):
        """Test complete project generation with simple vanilla project"""
        logger.info("🔄 Testing Simple Vanilla Project Generation...")
        
        test_request = {
            'prompt': 'Create a simple interactive to-do list with add, delete, and mark complete functionality',
            'framework': 'vanilla',
            'complexity': 'simple',
            'features': ['responsive_design', 'local_storage']
        }
        
        start_time = time.time()
        
        try:
            # Test the complete workflow
            result = self.orchestrator.execute_vibe_workflow(
                vibe_request=test_request,
                job_id='test-simple-vanilla'
            )
            
            execution_time = time.time() - start_time
            
            # Analyze results
            success = result.get('status') == 'completed'
            files_generated = len(result.get('project_files', {}))
            quality_score = result.get('final_quality_score', 0)
            
            self.test_results['simple_project'] = {
                'success': success,
                'execution_time': execution_time,
                'files_generated': files_generated,
                'quality_score': quality_score,
                'agents_completed': result.get('agents_completed', []),
                'project_files': list(result.get('project_files', {}).keys())
            }
            
            logger.info(f"📊 Simple Project Results:")
            logger.info(f"   Success: {success}")
            logger.info(f"   Execution Time: {execution_time:.2f}s")
            logger.info(f"   Files Generated: {files_generated}")
            logger.info(f"   Quality Score: {quality_score}")
            logger.info(f"   Agents Completed: {result.get('agents_completed', [])}")
            
            if files_generated > 0:
                logger.info("   Generated Files:")
                for file_path in result.get('project_files', {}).keys():
                    logger.info(f"     - {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Simple project generation failed: {e}")
            self.test_results['simple_project'] = {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
            return False
    
    async def test_react_project_generation(self):
        """Test React project generation"""
        logger.info("🔄 Testing React Project Generation...")
        
        test_request = {
            'prompt': 'Create a modern React todo app with TypeScript, state management, and component styling',
            'framework': 'react',
            'complexity': 'intermediate',
            'features': ['typescript', 'state_management', 'responsive_design', 'testing']
        }
        
        start_time = time.time()
        
        try:
            result = self.orchestrator.execute_vibe_workflow(
                vibe_request=test_request,
                job_id='test-react-intermediate'
            )
            
            execution_time = time.time() - start_time
            
            success = result.get('status') == 'completed'
            files_generated = len(result.get('project_files', {}))
            quality_score = result.get('final_quality_score', 0)
            
            self.test_results['react_project'] = {
                'success': success,
                'execution_time': execution_time,
                'files_generated': files_generated,
                'quality_score': quality_score,
                'agents_completed': result.get('agents_completed', []),
                'project_files': list(result.get('project_files', {}).keys())
            }
            
            logger.info(f"📊 React Project Results:")
            logger.info(f"   Success: {success}")
            logger.info(f"   Execution Time: {execution_time:.2f}s")
            logger.info(f"   Files Generated: {files_generated}")
            logger.info(f"   Quality Score: {quality_score}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ React project generation failed: {e}")
            self.test_results['react_project'] = {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
            return False
    
    async def test_agent_capabilities(self):
        """Test individual agent capabilities"""
        logger.info("🔄 Testing Individual Agent Capabilities...")
        
        capabilities_test = {}
        
        for agent_name, agent_instance in self.orchestrator.agent_instances.items():
            try:
                capabilities = agent_instance.get_capabilities()
                
                # Test input validation
                test_input = {
                    'test_field': 'test_value',
                    'framework': 'react',
                    'complexity': 'simple'
                }
                
                validation_result = agent_instance.validate_input(test_input)
                
                capabilities_test[agent_name] = {
                    'capabilities_count': len(capabilities),
                    'capabilities': capabilities,
                    'validation_working': validation_result is not None,
                    'status': 'operational'
                }
                
                logger.info(f"   ✅ {agent_name}: {len(capabilities)} capabilities")
                
            except Exception as e:
                capabilities_test[agent_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                logger.error(f"   ❌ {agent_name}: {e}")
        
        self.test_results['agent_capabilities'] = capabilities_test
        
        # Test orchestrator capabilities
        orchestrator_capabilities = self.orchestrator.get_capabilities()
        logger.info(f"   ✅ orchestrator: {len(orchestrator_capabilities)} capabilities")
        
        return len(capabilities_test) == 5  # Should have 5 specialist agents
    
    async def test_qa_validation_comprehensive(self):
        """Test comprehensive QA validation"""
        logger.info("🔄 Testing Comprehensive QA Validation...")
        
        try:
            qa_agent = self.orchestrator.agent_instances['qa_validator']
            
            # Test with various project types
            test_projects = {
                'vanilla': {
                    'index.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test App</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app">
        <h1>Test Application</h1>
        <button onclick="testFunction()">Click me</button>
    </div>
    <script src="script.js"></script>
</body>
</html>''',
                    'script.js': '''
function testFunction() {
    console.log("Button clicked!");
    document.getElementById("app").style.backgroundColor = "#f0f0f0";
}

// Initialize app
document.addEventListener("DOMContentLoaded", function() {
    console.log("App initialized");
});
''',
                    'style.css': '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    padding: 20px;
    background-color: #ffffff;
}

#app {
    max-width: 800px;
    margin: 0 auto;
    text-align: center;
}

button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #0056b3;
}
'''
                }
            }
            
            qa_results = {}
            
            for project_type, files in test_projects.items():
                logger.info(f"   Testing QA validation for {project_type} project...")
                
                result = await qa_agent.validate_project(files, f'qa-test-{project_type}')
                
                qa_results[project_type] = {
                    'quality_score': result.get('quality_score', 0),
                    'test_status': result.get('test_status', 'unknown'),
                    'files_tested': len(files),
                    'validation_passed': result.get('quality_score', 0) > 50
                }
                
                logger.info(f"     Quality Score: {result.get('quality_score', 0)}")
                logger.info(f"     Validation: {'✅ PASS' if result.get('quality_score', 0) > 50 else '❌ FAIL'}")
            
            self.test_results['qa_validation'] = qa_results
            
            # Check if all validations passed
            all_passed = all(result['validation_passed'] for result in qa_results.values())
            
            return all_passed
            
        except Exception as e:
            logger.error(f"❌ QA validation testing failed: {e}")
            self.test_results['qa_validation'] = {'error': str(e)}
            return False
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📋 Generating Comprehensive Test Report...")
        
        report = {
            'test_execution_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_status': 'operational',
            'total_tests': len(self.test_results),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': self.test_results,
            'summary': {}
        }
        
        # Calculate pass/fail statistics
        for test_name, test_result in self.test_results.items():
            if isinstance(test_result, dict) and test_result.get('success', False):
                report['passed_tests'] += 1
            else:
                report['failed_tests'] += 1
        
        # Generate summary
        report['summary'] = {
            'agent_system_operational': len(self.orchestrator.agent_instances) == 5,
            'workflow_orchestration_working': 'simple_project' in self.test_results,
            'qa_validation_functional': 'qa_validation' in self.test_results,
            'all_agents_responsive': 'agent_capabilities' in self.test_results,
            'overall_success_rate': (report['passed_tests'] / report['total_tests'] * 100) if report['total_tests'] > 0 else 0
        }
        
        # Save report to file
        with open('workflow_test_results.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Test Report Summary:")
        logger.info(f"   Total Tests: {report['total_tests']}")
        logger.info(f"   Passed: {report['passed_tests']}")
        logger.info(f"   Failed: {report['failed_tests']}")
        logger.info(f"   Success Rate: {report['summary']['overall_success_rate']:.1f}%")
        logger.info(f"   Report saved to: workflow_test_results.json")
        
        return report

async def main():
    """Main test execution function"""
    logger.info("🔥 Starting Complete 6-Agent System Workflow Test")
    logger.info("=" * 60)
    
    tester = WorkflowTester()
    
    # Phase 1: System Initialization
    logger.info("📍 PHASE 1: System Initialization")
    if not await tester.initialize_system():
        logger.error("❌ System initialization failed. Aborting tests.")
        return False
    
    # Phase 2: Agent Capabilities Testing
    logger.info("\n📍 PHASE 2: Agent Capabilities Testing")
    await tester.test_agent_capabilities()
    
    # Phase 3: QA Validation Testing
    logger.info("\n📍 PHASE 3: QA Validation Testing")
    await tester.test_qa_validation_comprehensive()
    
    # Phase 4: Simple Project Generation
    logger.info("\n📍 PHASE 4: Simple Project Generation")
    await tester.test_simple_project_generation()
    
    # Phase 5: React Project Generation
    logger.info("\n📍 PHASE 5: React Project Generation")
    await tester.test_react_project_generation()
    
    # Phase 6: Generate Test Report
    logger.info("\n📍 PHASE 6: Test Report Generation")
    report = await tester.generate_test_report()
    
    # Final Results
    logger.info("\n" + "=" * 60)
    logger.info("🏆 WORKFLOW TESTING COMPLETE")
    logger.info(f"🎯 Overall Success Rate: {report['summary']['overall_success_rate']:.1f}%")
    
    if report['summary']['overall_success_rate'] >= 80:
        logger.info("✅ 6-AGENT SYSTEM FULLY OPERATIONAL")
        return True
    else:
        logger.error("❌ SYSTEM REQUIRES ATTENTION")
        return False

if __name__ == "__main__":
    asyncio.run(main())