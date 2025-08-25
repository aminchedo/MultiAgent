#!/usr/bin/env python3
"""
Test script for the real backend with language detection
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from backend.nlp.language_detector import detect_language, determine_project_type
    from backend.core.workflow import MultiAgentWorkflow
    print("✅ Real backend imported successfully")
except ImportError as e:
    print(f"❌ Real backend import failed: {e}")
    sys.exit(1)

async def test_persian_speech_recognition():
    """Test the Persian speech recognition request (the original problem)"""
    print("\n🧪 TESTING PERSIAN SPEECH RECOGNITION")
    print("=" * 50)
    
    description = "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text using speech_recognition and googletrans libraries. Include error handling for audio capture failures and translation errors."
    name = "Persian Speech Translator"
    
    print(f"Description: {description[:100]}...")
    
    # Test language detection
    detected_language = detect_language(description)
    project_type = determine_project_type(description, detected_language)
    
    print(f"🔍 Language detected: {detected_language}")
    print(f"📋 Project type: {project_type.value}")
    
    # Test workflow
    workflow = MultiAgentWorkflow()
    result = await workflow.execute({
        'description': description,
        'name': name,
        'language': detected_language,
        'project_type': project_type.value
    })
    
    # Validate results
    files = result.get('files', [])
    python_files = [f for f in files if f.get('name', '').endswith('.py')]
    react_files = [f for f in files if 'react' in f.get('content', '').lower() or f.get('name', '').endswith('.jsx')]
    
    print(f"📁 Generated files: {len(files)}")
    print(f"🐍 Python files: {len(python_files)}")
    print(f"⚛️ React files: {len(react_files)}")
    
    # Check for speech recognition imports
    main_py_content = ""
    for file in files:
        if file.get('name') == 'main.py':
            main_py_content = file.get('content', '')
            break
    
    has_speech_recognition = 'speech_recognition' in main_py_content
    has_googletrans = 'googletrans' in main_py_content
    has_persian = 'persian' in main_py_content.lower() or 'farsi' in main_py_content.lower()
    
    print(f"🎤 Speech recognition import: {'✅' if has_speech_recognition else '❌'}")
    print(f"🌐 Google translate import: {'✅' if has_googletrans else '❌'}")
    print(f"🇮🇷 Persian/Farsi references: {'✅' if has_persian else '❌'}")
    
    success = (
        detected_language == 'python' and
        project_type.value == 'cli_tool' and
        len(python_files) > 0 and
        len(react_files) == 0 and
        has_speech_recognition and
        has_googletrans and
        has_persian
    )
    
    print(f"\n🎯 RESULT: {'✅ SUCCESS - Real backend working!' if success else '❌ FAILED - Issues remain'}")
    return success

async def test_react_web_app():
    """Test React web app generation (backward compatibility)"""
    print("\n🧪 TESTING REACT WEB APP")
    print("=" * 50)
    
    description = "Build a React web application with modern dashboard, charts, and real-time data visualization using React hooks and Material-UI components."
    name = "Dashboard App"
    
    print(f"Description: {description[:100]}...")
    
    # Test language detection
    detected_language = detect_language(description)
    project_type = determine_project_type(description, detected_language)
    
    print(f"🔍 Language detected: {detected_language}")
    print(f"📋 Project type: {project_type.value}")
    
    # Test workflow
    workflow = MultiAgentWorkflow()
    result = await workflow.execute({
        'description': description,
        'name': name,
        'language': detected_language,
        'project_type': project_type.value
    })
    
    # Validate results
    files = result.get('files', [])
    python_files = [f for f in files if f.get('name', '').endswith('.py')]
    react_files = [f for f in files if 'react' in f.get('content', '').lower() or f.get('name', '').endswith('.jsx')]
    
    print(f"📁 Generated files: {len(files)}")
    print(f"🐍 Python files: {len(python_files)}")
    print(f"⚛️ React files: {len(react_files)}")
    
    # Check for React content
    app_jsx_content = ""
    for file in files:
        if file.get('name') == 'src/App.jsx':
            app_jsx_content = file.get('content', '')
            break
    
    has_react_import = 'import React' in app_jsx_content
    has_react_hooks = 'useState' in app_jsx_content or 'useEffect' in app_jsx_content
    has_jsx = 'function App()' in app_jsx_content
    
    print(f"⚛️ React import: {'✅' if has_react_import else '❌'}")
    print(f"🎣 React hooks: {'✅' if has_react_hooks else '❌'}")
    print(f"📝 JSX component: {'✅' if has_jsx else '❌'}")
    
    success = (
        detected_language == 'javascript' and
        project_type.value == 'web_app' and
        len(react_files) > 0 and
        len(python_files) == 0 and
        has_react_import and
        has_jsx
    )
    
    print(f"\n🎯 RESULT: {'✅ SUCCESS - React generation working!' if success else '❌ FAILED - Issues remain'}")
    return success

async def main():
    """Run all tests"""
    print("🚀 TESTING REAL BACKEND WITH LANGUAGE DETECTION")
    print("=" * 60)
    
    # Test 1: Persian speech recognition (the original problem)
    test1_success = await test_persian_speech_recognition()
    
    # Test 2: React web app (backward compatibility)
    test2_success = await test_react_web_app()
    
    # Overall result
    overall_success = test1_success and test2_success
    
    print(f"\n🎯 FINAL RESULT: {'✅ SUCCESS - Real backend working!' if overall_success else '❌ FAILED - Issues remain'}")
    
    if overall_success:
        print("\n🎉 CONGRATULATIONS! The real backend is working correctly:")
        print("   ✅ Python requests generate Python code")
        print("   ✅ React requests generate React code")
        print("   ✅ Language detection is accurate")
        print("   ✅ No more mock backend fallback")
    else:
        print("\n⚠️  Some issues remain. Check the output above for details.")
    
    return overall_success

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())