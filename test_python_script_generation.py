#!/usr/bin/env python3
"""
Test script to validate Python script generation fixes.
This script tests the critical issue where the system was generating React components
instead of Python scripts for Python-related requests.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.nlp.intent_processor import IntentProcessor
from backend.models.models import ProjectType
from backend.agents.agents import PlannerAgent, CodeGeneratorAgent
from backend.database.db import db_manager


async def test_project_type_detection():
    """Test that project type detection correctly identifies Python scripts."""
    print("🧪 Testing Project Type Detection...")
    
    # Test cases
    test_cases = [
        {
            "description": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text.",
            "expected_type": ProjectType.CLI_TOOL,
            "expected_language": "python"
        },
        {
            "description": "Create a Python CLI tool for data analysis with pandas and matplotlib",
            "expected_type": ProjectType.CLI_TOOL,
            "expected_language": "python"
        },
        {
            "description": "Build a React web application for task management",
            "expected_type": ProjectType.WEB_APP,
            "expected_language": "javascript"
        },
        {
            "description": "Develop a Node.js API for user authentication",
            "expected_type": ProjectType.API,
            "expected_language": "javascript"
        }
    ]
    
    processor = IntentProcessor()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['description'][:50]}...")
        
        try:
            intent = await processor.process_requirements(test_case['description'])
            
            detected_type = intent.project_type
            detected_language = None
            
            # Extract language from tech stack
            if intent.tech_stack.get('backend') and 'python' in intent.tech_stack['backend']:
                detected_language = 'python'
            elif intent.tech_stack.get('frontend') and any(lang in intent.tech_stack['frontend'] for lang in ['javascript', 'react', 'vue']):
                detected_language = 'javascript'
            
            print(f"   Expected Type: {test_case['expected_type'].value}")
            print(f"   Detected Type: {detected_type.value}")
            print(f"   Expected Language: {test_case['expected_language']}")
            print(f"   Detected Language: {detected_language}")
            
            # Check if detection is correct
            type_correct = detected_type == test_case['expected_type']
            language_correct = detected_language == test_case['expected_language']
            
            if type_correct and language_correct:
                print(f"   ✅ PASS: Correctly detected {detected_type.value} project in {detected_language}")
            else:
                print(f"   ❌ FAIL: Expected {test_case['expected_type'].value} in {test_case['expected_language']}, got {detected_type.value} in {detected_language}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print("\n" + "="*60)


async def test_agent_prompts():
    """Test that agents get language-specific prompts."""
    print("🤖 Testing Agent Language-Specific Prompts...")
    
    # Initialize database
    await db_manager.initialize()
    
    # Test cases
    test_cases = [
        {
            "description": "Python script for speech recognition",
            "project_type": ProjectType.CLI_TOOL,
            "expected_planner_role": "Senior Python CLI Developer",
            "expected_coder_role": "Senior Python CLI Developer"
        },
        {
            "description": "React web application",
            "project_type": ProjectType.WEB_APP,
            "expected_planner_role": "Senior Frontend Developer",
            "expected_coder_role": "Senior Frontend Developer"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['description']}")
        
        try:
            # Test planner agent
            planner = PlannerAgent("test_job", None)
            detected_language = planner._detect_primary_language(test_case['description'])
            role, goal, backstory = planner._get_language_specific_prompt(
                test_case['project_type'], detected_language
            )
            
            print(f"   Planner Role: {role}")
            print(f"   Expected Role: {test_case['expected_planner_role']}")
            
            if test_case['expected_planner_role'] in role:
                print(f"   ✅ PASS: Planner got correct role")
            else:
                print(f"   ❌ FAIL: Planner role mismatch")
            
            # Test code generator agent
            coder = CodeGeneratorAgent("test_job", None)
            coder_role, coder_goal, coder_backstory = coder._get_coder_language_specific_prompt(
                test_case['project_type'], detected_language
            )
            
            print(f"   Coder Role: {coder_role}")
            print(f"   Expected Role: {test_case['expected_coder_role']}")
            
            if test_case['expected_coder_role'] in coder_role:
                print(f"   ✅ PASS: Coder got correct role")
            else:
                print(f"   ❌ FAIL: Coder role mismatch")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print("\n" + "="*60)


async def test_python_script_generation():
    """Test actual Python script generation."""
    print("🐍 Testing Python Script Generation...")
    
    # Initialize database
    await db_manager.initialize()
    
    # Test the specific case that was failing
    test_request = {
        "name": "Persian Speech Recognition",
        "description": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text.",
        "project_type": ProjectType.CLI_TOOL,
        "languages": ["python"],
        "frameworks": [],
        "complexity": "moderate",
        "features": ["speech recognition", "translation", "audio processing"],
        "mode": "full"
    }
    
    try:
        print("📝 Generating project plan...")
        planner = PlannerAgent("test_python_script", None)
        plan = await planner.generate_plan(test_request)
        
        print(f"   Plan generated with {len(plan.get('structure', {}))} files")
        
        # Check if plan contains Python files
        python_files = [f for f in plan.get('structure', {}).keys() if f.endswith('.py')]
        print(f"   Python files in plan: {python_files}")
        
        if python_files:
            print(f"   ✅ PASS: Plan contains Python files")
        else:
            print(f"   ❌ FAIL: Plan contains no Python files")
            print(f"   All files: {list(plan.get('structure', {}).keys())}")
        
        # Test code generation for one Python file
        if python_files:
            print(f"\n🔧 Generating code for {python_files[0]}...")
            coder = CodeGeneratorAgent("test_python_script", None)
            
            # Create a minimal plan with just one Python file
            test_plan = {
                "name": "Persian Speech Recognition",
                "structure": {
                    python_files[0]: "Main Python script for speech recognition and translation"
                }
            }
            
            generated_files = await coder.generate_code(test_plan)
            
            if generated_files:
                file_content = generated_files[0]['content']
                print(f"   Generated {len(file_content)} characters of code")
                
                # Check for Python-specific content
                python_indicators = [
                    'import speech_recognition',
                    'import pyaudio',
                    'from googletrans',
                    'def ',
                    'if __name__',
                    'try:',
                    'except'
                ]
                
                found_indicators = [ind for ind in python_indicators if ind in file_content]
                print(f"   Python indicators found: {found_indicators}")
                
                if len(found_indicators) >= 3:
                    print(f"   ✅ PASS: Generated proper Python code")
                else:
                    print(f"   ❌ FAIL: Generated code doesn't look like Python")
                    print(f"   First 200 chars: {file_content[:200]}")
            else:
                print(f"   ❌ FAIL: No files generated")
                
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)


async def main():
    """Run all tests."""
    print("🚀 Starting Python Script Generation Fix Validation")
    print("="*60)
    
    try:
        await test_project_type_detection()
        await test_agent_prompts()
        await test_python_script_generation()
        
        print("\n🎉 All tests completed!")
        print("\n📋 Summary:")
        print("   - Project type detection should now correctly identify Python scripts")
        print("   - Agents should get language-specific prompts")
        print("   - Python script generation should work properly")
        print("\n🔧 If any tests failed, the fixes may need additional refinement.")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())