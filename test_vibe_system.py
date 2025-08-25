#!/usr/bin/env python3
"""
Test Vibe System Implementation

This script tests the complete vibe agent system implementation to verify
that all components work together properly.
"""

import sys
import os
import traceback
import time

# Add project paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test vibe database connection and table structure."""
    print("🔍 Testing database connection...")
    
    try:
        import sqlite3
        
        # Test database connection
        conn = sqlite3.connect("backend/vibe_projects.db")
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"✅ Database connected successfully")
        print(f"📋 Tables found: {table_names}")
        
        # Check vibe_projects table structure
        cursor.execute("PRAGMA table_info(vibe_projects);")
        vibe_columns = cursor.fetchall()
        print(f"📊 vibe_projects columns: {[col[1] for col in vibe_columns]}")
        
        # Check agent_metrics table structure
        cursor.execute("PRAGMA table_info(agent_metrics);")
        metrics_columns = cursor.fetchall()
        print(f"📊 agent_metrics columns: {[col[1] for col in metrics_columns]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_agent_imports():
    """Test that all vibe agents can be imported."""
    print("\n🔍 Testing agent imports...")
    
    try:
        # Test individual agent imports
        from agents.vibe_planner_agent import VibePlannerAgent
        print("✅ VibePlannerAgent imported")
        
        from agents.vibe_coder_agent import VibeCoderAgent
        print("✅ VibeCoderAgent imported")
        
        from agents.vibe_critic_agent import VibeCriticAgent
        print("✅ VibeCriticAgent imported")
        
        from agents.vibe_file_manager_agent import VibeFileManagerAgent
        print("✅ VibeFileManagerAgent imported")
        
        from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
        print("✅ VibeWorkflowOrchestratorAgent imported")
        
        # Test module import
        from agents import VIBE_AGENTS, test_all_agents
        print("✅ Agents module imported")
        
        # Test agent registry
        print(f"📋 Available agents: {list(VIBE_AGENTS.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        traceback.print_exc()
        return False

def test_agent_instantiation():
    """Test that all agents can be instantiated."""
    print("\n🔍 Testing agent instantiation...")
    
    try:
        from agents import test_all_agents
        
        results = test_all_agents()
        
        for agent_name, result in results.items():
            if result['status'] == 'success':
                print(f"✅ {agent_name}: {result['class']} - {len(result['capabilities'])} capabilities")
            else:
                print(f"❌ {agent_name}: {result['error']}")
        
        successful_agents = [name for name, result in results.items() if result['status'] == 'success']
        return len(successful_agents) == len(results)
        
    except Exception as e:
        print(f"❌ Agent instantiation failed: {e}")
        traceback.print_exc()
        return False

def test_planner_agent():
    """Test VibePlannerAgent functionality."""
    print("\n🔍 Testing VibePlannerAgent...")
    
    try:
        from agents.vibe_planner_agent import VibePlannerAgent
        
        agent = VibePlannerAgent()
        print("✅ VibePlannerAgent created")
        
        # Test vibe prompt analysis
        test_prompt = "Create a modern dark mode task manager with authentication and real-time updates"
        result = agent.decompose_vibe_prompt(test_prompt)
        
        print(f"✅ Prompt analyzed successfully")
        print(f"  🎨 UI Styles: {result['vibe_analysis']['detected_ui_styles']}")
        print(f"  📱 Project Type: {result['vibe_analysis']['detected_project_type']}")
        print(f"  ⚙️ Technology: {result['vibe_analysis']['detected_technologies']}")
        print(f"  🚀 Features: {result['vibe_analysis']['detected_features']}")
        print(f"  📊 Complexity: {result['vibe_analysis']['complexity']}")
        print(f"  📋 Steps: {len(result['implementation_steps'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ VibePlannerAgent test failed: {e}")
        traceback.print_exc()
        return False

def test_coder_agent():
    """Test VibeCoderAgent functionality."""
    print("\n🔍 Testing VibeCoderAgent...")
    
    try:
        from agents.vibe_coder_agent import VibeCoderAgent
        
        agent = VibeCoderAgent()
        print("✅ VibeCoderAgent created")
        
        # Create a test plan
        test_plan = {
            'technical_requirements': {
                'framework': 'react',
                'styling': 'tailwind',
                'components': ['App', 'Header', 'TaskList'],
                'features': ['authentication']
            },
            'vibe_analysis': {
                'detected_ui_styles': ['modern', 'dark'],
                'detected_project_type': 'app',
                'detected_technologies': ['react'],
                'detected_features': ['authentication']
            }
        }
        
        result = agent.generate_code_from_plan(test_plan, 1)
        
        print(f"✅ Code generated successfully")
        print(f"  🏗️ Framework: {result['framework']}")
        print(f"  📁 Files created: {result['file_count']}")
        print(f"  🧩 Components: {result['components_created']}")
        print(f"  📋 Generated files: {list(result['generated_files'].keys())[:5]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ VibeCoderAgent test failed: {e}")
        traceback.print_exc()
        return False

def test_orchestrator():
    """Test the complete workflow orchestration."""
    print("\n🔍 Testing VibeWorkflowOrchestratorAgent...")
    
    try:
        from agents.vibe_workflow_orchestrator_agent import VibeWorkflowOrchestratorAgent
        
        orchestrator = VibeWorkflowOrchestratorAgent()
        print("✅ VibeWorkflowOrchestratorAgent created")
        
        # Test workflow execution
        test_request = {
            'vibe_prompt': 'Create a simple modern blog with dark theme',
            'project_type': 'blog',
            'complexity': 'simple'
        }
        
        print("🚀 Executing complete workflow...")
        start_time = time.time()
        
        result = orchestrator.orchestrate_vibe_project(test_request)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Workflow completed in {duration:.2f}s")
        print(f"  🆔 Workflow ID: {result['workflow_id']}")
        print(f"  📊 Status: {result['workflow_status']}")
        print(f"  📈 Progress: {result['progress']['percentage']}%")
        print(f"  🏗️ Project ID: {result.get('project_id', 'N/A')}")
        
        # Check agent results
        agent_results = result.get('agent_results', {})
        print(f"  🤖 Agent Results:")
        for agent_name, agent_result in agent_results.items():
            status = "✅" if agent_result.get('success', False) else "❌"
            print(f"    {status} {agent_name}: {agent_result.get('agent', 'unknown')}")
        
        # Check final project data
        project_data = result.get('project_data', {})
        if project_data:
            print(f"  📊 Project Data:")
            print(f"    🏗️ Framework: {project_data.get('framework', 'N/A')}")
            print(f"    📁 Files: {project_data.get('file_count', 0)}")
            print(f"    🧩 Components: {project_data.get('components_created', 0)}")
            print(f"    ⭐ Quality Score: {project_data.get('quality_score', 'N/A')}")
        
        return result['workflow_status'] == 'completed'
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        traceback.print_exc()
        return False

def test_database_integration():
    """Test database integration with agents."""
    print("\n🔍 Testing database integration...")
    
    try:
        import sqlite3
        
        # Check if vibe project was created
        conn = sqlite3.connect("backend/vibe_projects.db")
        cursor = conn.cursor()
        
        # Get recent projects
        cursor.execute("SELECT id, vibe_prompt, project_type, status FROM vibe_projects ORDER BY id DESC LIMIT 3")
        projects = cursor.fetchall()
        
        print(f"✅ Found {len(projects)} vibe projects in database")
        for project in projects:
            print(f"  📋 Project {project[0]}: {project[1][:30]}... - {project[3]}")
        
        # Get agent metrics
        cursor.execute("SELECT agent_name, COUNT(*) FROM agent_metrics GROUP BY agent_name")
        metrics = cursor.fetchall()
        
        print(f"✅ Found agent metrics for {len(metrics)} agents")
        for metric in metrics:
            print(f"  🤖 {metric[0]}: {metric[1]} operations")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False

def run_all_tests():
    """Run all test functions."""
    print("🚀 Starting Vibe System Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Agent Imports", test_agent_imports),
        ("Agent Instantiation", test_agent_instantiation),
        ("Planner Agent", test_planner_agent),
        ("Coder Agent", test_coder_agent),
        ("Complete Workflow", test_orchestrator),
        ("Database Integration", test_database_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Vibe system is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)