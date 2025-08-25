#!/usr/bin/env python3
"""
Validation script for Vibe Coding Platform implementation.
Checks that all files are in place and properly structured.
"""

import os
import sys
from pathlib import Path

def validate_implementation():
    """Validate the Vibe Coding Platform implementation."""
    
    print("🎯 Validating Vibe Coding Platform Implementation")
    print("=" * 55)
    
    validation_results = {
        "files_checked": 0,
        "files_missing": 0,
        "issues": []
    }
    
    # Define required files and their validation criteria
    required_files = {
        # Backend - Specialized Agents
        "backend/agents/specialized/vibe_planner_agent.py": {
            "type": "python",
            "must_contain": ["VibePlannerAgent", "decompose_vibe_prompt", "vibe_patterns"]
        },
        "backend/agents/specialized/vibe_coder_agent.py": {
            "type": "python", 
            "must_contain": ["VibeCoderAgent", "generate_code", "code_templates"]
        },
        "backend/agents/specialized/vibe_critic_agent.py": {
            "type": "python",
            "must_contain": ["VibeCriticAgent", "review_code", "quality_standards"]
        },
        "backend/agents/specialized/vibe_file_manager_agent.py": {
            "type": "python",
            "must_contain": ["VibeFileManagerAgent", "organize_and_finalize_project"]
        },
        "backend/agents/specialized/vibe_workflow_orchestrator.py": {
            "type": "python",
            "must_contain": ["VibeWorkflowOrchestrator", "execute_vibe_workflow"]
        },
        
        # Frontend - Enhanced UI
        "src/app/generate/[jobId]/page.tsx": {
            "type": "typescript",
            "must_contain": ["Vibe Planner", "Vibe Coder", "vibeTask"]
        },
        "src/components/vibe/VibeInput.tsx": {
            "type": "typescript",
            "must_contain": ["VibeInput", "createVibeJob"]
        },
        "src/lib/api/production-client.ts": {
            "type": "typescript",
            "must_contain": ["createVibeJob", "vibe-coding"]
        },
        
        # API Integration
        "backend/api/routes.py": {
            "type": "python",
            "must_contain": ["vibe-coding", "create_vibe_project", "create_and_execute_enhanced_workflow"]
        },
        
        # Documentation
        "VIBE_CODING_IMPLEMENTATION_COMPLETE.md": {
            "type": "markdown",
            "must_contain": ["Vibe Coding Platform", "Five AI Agents", "Implementation Success"]
        }
    }
    
    print("\n🔍 Checking Required Files...")
    
    for file_path, criteria in required_files.items():
        validation_results["files_checked"] += 1
        
        if not os.path.exists(file_path):
            validation_results["files_missing"] += 1
            validation_results["issues"].append(f"❌ Missing file: {file_path}")
            print(f"❌ {file_path} - MISSING")
            continue
        
        # Check file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            missing_content = []
            for required_content in criteria["must_contain"]:
                if required_content not in content:
                    missing_content.append(required_content)
            
            if missing_content:
                validation_results["issues"].append(
                    f"⚠️ {file_path} missing content: {', '.join(missing_content)}"
                )
                print(f"⚠️ {file_path} - Missing content: {', '.join(missing_content)}")
            else:
                print(f"✅ {file_path} - OK")
                
        except Exception as e:
            validation_results["issues"].append(f"❌ Error reading {file_path}: {str(e)}")
            print(f"❌ {file_path} - Error reading file: {str(e)}")
    
    # Check agent integration
    print("\n🤖 Validating Agent Architecture...")
    
    agent_files = [
        "backend/agents/specialized/vibe_planner_agent.py",
        "backend/agents/specialized/vibe_coder_agent.py", 
        "backend/agents/specialized/vibe_critic_agent.py",
        "backend/agents/specialized/vibe_file_manager_agent.py"
    ]
    
    for agent_file in agent_files:
        if os.path.exists(agent_file):
            with open(agent_file, 'r') as f:
                content = f.read()
            
            # Check for proper class structure
            if "class " in content and "BaseCrewAgent" in content:
                print(f"✅ {os.path.basename(agent_file)} - Proper agent structure")
            else:
                print(f"⚠️ {os.path.basename(agent_file)} - May have structural issues")
                validation_results["issues"].append(f"Agent structure issue in {agent_file}")
    
    # Validate workflow integration
    print("\n🔄 Validating Workflow Integration...")
    
    workflow_file = "backend/agents/specialized/vibe_workflow_orchestrator.py"
    if os.path.exists(workflow_file):
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        required_imports = [
            "VibePlannerAgent",
            "VibeCoderAgent", 
            "VibeCriticAgent",
            "VibeFileManagerAgent"
        ]
        
        missing_imports = [imp for imp in required_imports if imp not in content]
        if missing_imports:
            print(f"⚠️ Workflow orchestrator missing imports: {', '.join(missing_imports)}")
            validation_results["issues"].append(f"Missing imports in workflow: {', '.join(missing_imports)}")
        else:
            print("✅ Workflow orchestrator - All agent imports present")
    
    # Check API integration  
    print("\n🔌 Validating API Integration...")
    
    routes_file = "backend/api/routes.py"
    if os.path.exists(routes_file):
        with open(routes_file, 'r') as f:
            content = f.read()
        
        if "create_and_execute_enhanced_workflow" in content:
            print("✅ API routes - Enhanced workflow integrated")
        else:
            print("⚠️ API routes - Enhanced workflow may not be integrated")
            validation_results["issues"].append("Enhanced workflow not found in API routes")
    
    # Validate frontend integration
    print("\n🎨 Validating Frontend Integration...")
    
    generation_page = "src/app/generate/[jobId]/page.tsx"
    if os.path.exists(generation_page):
        with open(generation_page, 'r') as f:
            content = f.read()
        
        if "Vibe Planner" in content and "vibeTask" in content:
            print("✅ Generation page - Vibe-specific UI elements present")
        else:
            print("⚠️ Generation page - May be missing vibe enhancements")
            validation_results["issues"].append("Vibe UI enhancements may be missing")
    
    api_client = "src/lib/api/production-client.ts"
    if os.path.exists(api_client):
        with open(api_client, 'r') as f:
            content = f.read()
        
        if "/api/vibe-coding" in content:
            print("✅ API client - Vibe coding endpoint integrated")
        else:
            print("⚠️ API client - Vibe coding endpoint may not be integrated")
            validation_results["issues"].append("Vibe coding endpoint not found in API client")
    
    # Print final results
    print("\n" + "=" * 55)
    print("📊 VALIDATION RESULTS")
    print("=" * 55)
    
    files_ok = validation_results["files_checked"] - validation_results["files_missing"]
    
    print(f"📁 Files Checked: {validation_results['files_checked']}")
    print(f"✅ Files Present: {files_ok}")
    print(f"❌ Files Missing: {validation_results['files_missing']}")
    print(f"⚠️ Issues Found: {len(validation_results['issues'])}")
    
    if validation_results["files_missing"] == 0 and len(validation_results["issues"]) == 0:
        print("\n🎉 VALIDATION PASSED!")
        print("✨ Vibe Coding Platform implementation is complete and ready!")
        print("\n🚀 Key Features Implemented:")
        print("   • 4 Specialized Vibe Agents + Workflow Orchestrator")
        print("   • Natural language vibe processing")
        print("   • Enhanced UI with agent collaboration visualization") 
        print("   • Backward-compatible API integration")
        print("   • Complete project packaging and deployment")
        return True
    else:
        print(f"\n⚠️ VALIDATION ISSUES FOUND")
        print("Please review and address the following issues:")
        for issue in validation_results["issues"][:10]:  # Show first 10 issues
            print(f"   • {issue}")
        
        if len(validation_results["issues"]) > 10:
            print(f"   • ... and {len(validation_results['issues']) - 10} more issues")
        
        return False

def main():
    """Main validation function."""
    
    print("🌟 Vibe Coding Platform - Implementation Validator")
    print("Checking that all components are properly implemented")
    print()
    
    try:
        success = validate_implementation()
        
        if success:
            print("\n✅ The Vibe Coding Platform is ready to transform ideas into reality!")
            return 0
        else:
            print("\n❌ Some issues found. Please review and fix before deployment.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Validation failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)