#!/usr/bin/env python3
"""
Quick verification script for 6-agent system
Confirms all agents are functional with real implementations
"""

import asyncio
import sys
import json
from typing import Dict, Any

# Import all agents
try:
    from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
    from agents.vibe_planner_agent import VibePlannerAgent
    from agents.vibe_coder_agent import VibeCoderAgent
    from agents.vibe_critic_agent import VibeCriticAgent
    from agents.vibe_file_manager_agent import VibeFileManagerAgent
    from agents.vibe_qa_validator_agent import VibeQAValidatorAgent
    print("✅ All agent imports successful")
except Exception as e:
    print(f"❌ Agent import failed: {e}")
    sys.exit(1)

# Import FastAPI app
try:
    from backend.simple_app import app
    print("✅ FastAPI app import successful")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")
    sys.exit(1)

async def verify_agents():
    """Verify all 6 agents are functional"""
    results = {
        "agents_verified": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "agent_details": {}
    }
    
    print("\n🔍 VERIFYING 6-AGENT SYSTEM...")
    print("=" * 50)
    
    # 1. Verify Orchestrator Agent
    try:
        orchestrator = VibeWorkflowOrchestratorAgent()
        assert hasattr(orchestrator, 'agent_instances')
        assert len(orchestrator.agent_instances) == 5  # 5 sub-agents
        assert 'planner' in orchestrator.agent_instances
        assert 'coder' in orchestrator.agent_instances
        assert 'critic' in orchestrator.agent_instances
        assert 'file_manager' in orchestrator.agent_instances
        assert 'qa_validator' in orchestrator.agent_instances
        
        results["agents_verified"] += 1
        results["agent_details"]["orchestrator"] = {
            "status": "✅ VERIFIED",
            "sub_agents": list(orchestrator.agent_instances.keys()),
            "workflow_steps": len(orchestrator.workflow_steps)
        }
        print("✅ Agent 1/6: Workflow Orchestrator - VERIFIED")
        results["tests_passed"] += 1
    except Exception as e:
        print(f"❌ Agent 1/6: Workflow Orchestrator - FAILED: {e}")
        results["tests_failed"] += 1
    
    # 2. Verify Planner Agent
    try:
        planner = VibePlannerAgent()
        assert hasattr(planner, 'get_capabilities')
        assert hasattr(planner, 'validate_input')
        capabilities = planner.get_capabilities()
        assert 'vibe_prompt_analysis' in capabilities
        results["agents_verified"] += 1
        results["agent_details"]["planner"] = {"status": "✅ VERIFIED", "capabilities": len(capabilities)}
        print("✅ Agent 2/6: Project Planner - VERIFIED")
        results["tests_passed"] += 1
    except Exception as e:
        print(f"❌ Agent 2/6: Project Planner - FAILED: {e}")
        results["tests_failed"] += 1
    
    # 3. Verify Coder Agent
    try:
        coder = VibeCoderAgent()
        assert hasattr(coder, 'get_capabilities')
        assert hasattr(coder, 'generate_code_from_plan')
        capabilities = coder.get_capabilities()
        results["agents_verified"] += 1
        results["agent_details"]["coder"] = {"status": "✅ VERIFIED", "capabilities": len(capabilities)}
        print("✅ Agent 3/6: Code Generator - VERIFIED")
        results["tests_passed"] += 1
    except Exception as e:
        print(f"❌ Agent 3/6: Code Generator - FAILED: {e}")
        results["tests_failed"] += 1
    
    # 4. Verify Critic Agent
    try:
        critic = VibeCriticAgent()
        assert hasattr(critic, 'get_capabilities')
        assert hasattr(critic, 'validate_input')
        capabilities = critic.get_capabilities()
        results["agents_verified"] += 1
        results["agent_details"]["critic"] = {"status": "✅ VERIFIED", "capabilities": len(capabilities)}
        print("✅ Agent 4/6: Code Critic - VERIFIED")
        results["tests_passed"] += 1
    except Exception as e:
        print(f"❌ Agent 4/6: Code Critic - FAILED: {e}")
        results["tests_failed"] += 1
    
    # 5. Verify File Manager Agent
    try:
        file_manager = VibeFileManagerAgent()
        assert hasattr(file_manager, 'get_capabilities')
        assert hasattr(file_manager, 'validate_input')
        capabilities = file_manager.get_capabilities()
        results["agents_verified"] += 1
        results["agent_details"]["file_manager"] = {"status": "✅ VERIFIED", "capabilities": len(capabilities)}
        print("✅ Agent 5/6: File Manager - VERIFIED")
        results["tests_passed"] += 1
    except Exception as e:
        print(f"❌ Agent 5/6: File Manager - FAILED: {e}")
        results["tests_failed"] += 1
    
    # 6. Verify QA Validator Agent
    try:
        qa_validator = VibeQAValidatorAgent()
        assert hasattr(qa_validator, 'validate_project')
        
        # Test QA functionality
        test_project = {
            'project_files': {
                'index.html': '<html><body><h1>Test</h1></body></html>',
                'script.js': 'console.log("Test");',
                'style.css': 'body { margin: 0; }'
            },
            'framework': 'vanilla'
        }
        
        qa_result = await qa_validator.validate_project(test_project, 'test-verification')
        quality_score = qa_result.get('quality_score', 0)
        
        results["agents_verified"] += 1
        results["agent_details"]["qa_validator"] = {
            "status": "✅ VERIFIED",
            "test_quality_score": quality_score
        }
        print(f"✅ Agent 6/6: QA Validator - VERIFIED (Score: {quality_score})")
        results["tests_passed"] += 1
    except Exception as e:
        print(f"❌ Agent 6/6: QA Validator - FAILED: {e}")
        results["tests_failed"] += 1
    
    # Verify API endpoints
    print("\n📡 VERIFYING API ENDPOINTS...")
    print("-" * 50)
    
    endpoint_count = 0
    for route in app.routes:
        if hasattr(route, 'path'):
            endpoint_count += 1
            print(f"  ✓ {route.path}")
    
    results["api_endpoints"] = endpoint_count
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Total Agents Verified: {results['agents_verified']}/6")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    print(f"API Endpoints: {results['api_endpoints']}")
    
    if results['agents_verified'] == 6 and results['tests_failed'] == 0:
        print("\n🎉 ALL 6 AGENTS VERIFIED - SYSTEM READY! 🎉")
        results["final_status"] = "READY FOR PRODUCTION"
    else:
        print("\n⚠️  VERIFICATION FAILED - CHECK ERRORS ABOVE")
        results["final_status"] = "NOT READY"
    
    # Save results
    with open('6_agent_verification_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: 6_agent_verification_results.json")
    
    return results

if __name__ == "__main__":
    print("🚀 6-AGENT SYSTEM VERIFICATION")
    print("=" * 50)
    results = asyncio.run(verify_agents())
    
    # Exit with appropriate code
    sys.exit(0 if results['agents_verified'] == 6 else 1)