#!/usr/bin/env python3
"""
Final Validation Script for Real Backend Deployment

This script comprehensively tests the real backend to ensure:
1. Language detection is working correctly
2. Python requests generate Python code with appropriate libraries
3. React requests generate React code
4. No cross-contamination between language types
"""

import requests
import json
import jwt
import datetime

def create_test_token():
    """Create a valid JWT token for testing"""
    secret = "secret"
    payload = {
        "user_id": "test-user",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def test_persian_speech_recognition():
    """Test the original problem: Persian speech recognition"""
    print("🧪 TEST 1: PERSIAN SPEECH RECOGNITION")
    print("=" * 50)
    
    payload = {
        "description": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text using speech_recognition and googletrans libraries. Include error handling for audio capture failures and translation errors.",
        "name": "Persian Speech Translator"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {create_test_token()}"
    }
    
    try:
        response = requests.post("http://127.0.0.1:8000/api/generate", 
                               json=payload, 
                               headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Request successful")
            print(f"🔍 Backend mode: {data.get('backend_mode')}")
            print(f"🔍 Language detected: {data.get('language_detected')}")
            print(f"🔍 Project type: {data.get('project_type')}")
            
            files = data.get('files', [])
            python_files = [f for f in files if f.get('name', '').endswith('.py')]
            react_files = [f for f in files if 'react' in f.get('content', '').lower() or f.get('name', '').endswith('.jsx')]
            
            print(f"📁 Files generated: {len(files)}")
            print(f"🐍 Python files: {len(python_files)}")
            print(f"⚛️ React files: {len(react_files)}")
            
            # Check main.py content
            main_py_content = ""
            for file in files:
                if file.get('name') == 'main.py':
                    main_py_content = file.get('content', '')
                    break
            
            has_speech_recognition = 'speech_recognition' in main_py_content
            has_googletrans = 'googletrans' in main_py_content
            has_persian = 'persian' in main_py_content.lower() or 'farsi' in main_py_content.lower()
            has_audio_capture = 'microphone' in main_py_content.lower() or 'audio' in main_py_content.lower()
            
            print(f"🎤 Speech recognition import: {'✅' if has_speech_recognition else '❌'}")
            print(f"🌐 Google translate import: {'✅' if has_googletrans else '❌'}")
            print(f"🇮🇷 Persian/Farsi references: {'✅' if has_persian else '❌'}")
            print(f"🎙️ Audio capture functionality: {'✅' if has_audio_capture else '❌'}")
            
            success = (
                data.get('backend_mode') == 'real' and
                data.get('language_detected') == 'python' and
                data.get('project_type') == 'cli_tool' and
                len(python_files) > 0 and
                len(react_files) == 0 and
                has_speech_recognition and
                has_googletrans and
                has_persian and
                has_audio_capture
            )
            
            print(f"\n🎯 RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
            return success
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_react_web_app():
    """Test React web app generation (backward compatibility)"""
    print("\n🧪 TEST 2: REACT WEB APP")
    print("=" * 50)
    
    payload = {
        "description": "Build a React web application with modern dashboard, charts, and real-time data visualization using React hooks and Material-UI components.",
        "name": "Dashboard App"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {create_test_token()}"
    }
    
    try:
        response = requests.post("http://127.0.0.1:8000/api/generate", 
                               json=payload, 
                               headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Request successful")
            print(f"🔍 Backend mode: {data.get('backend_mode')}")
            print(f"🔍 Language detected: {data.get('language_detected')}")
            print(f"🔍 Project type: {data.get('project_type')}")
            
            files = data.get('files', [])
            python_files = [f for f in files if f.get('name', '').endswith('.py')]
            react_files = [f for f in files if 'react' in f.get('content', '').lower() or f.get('name', '').endswith('.jsx')]
            
            print(f"📁 Files generated: {len(files)}")
            print(f"🐍 Python files: {len(python_files)}")
            print(f"⚛️ React files: {len(react_files)}")
            
            # Check App.jsx content
            app_jsx_content = ""
            for file in files:
                if file.get('name') == 'src/App.jsx':
                    app_jsx_content = file.get('content', '')
                    break
            
            has_react_import = 'import React' in app_jsx_content
            has_react_hooks = 'useState' in app_jsx_content or 'useEffect' in app_jsx_content
            has_jsx = 'function App()' in app_jsx_content
            has_modern_ui = 'dashboard' in app_jsx_content.lower() or 'chart' in app_jsx_content.lower()
            
            print(f"⚛️ React import: {'✅' if has_react_import else '❌'}")
            print(f"🎣 React hooks: {'✅' if has_react_hooks else '❌'}")
            print(f"📝 JSX component: {'✅' if has_jsx else '❌'}")
            print(f"🎨 Modern UI elements: {'✅' if has_modern_ui else '❌'}")
            
            success = (
                data.get('backend_mode') == 'real' and
                data.get('language_detected') == 'javascript' and
                data.get('project_type') == 'web_app' and
                len(react_files) > 0 and
                len(python_files) == 0 and
                has_react_import and
                has_jsx
            )
            
            print(f"\n🎯 RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
            return success
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint"""
    print("🧪 TEST 0: HEALTH ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful")
            print(f"🔍 Status: {data.get('status')}")
            print(f"🔍 Backend mode: {data.get('backend_mode')}")
            print(f"🔍 Dependencies: {data.get('dependencies')}")
            
            success = (
                data.get('status') == 'healthy' and
                data.get('backend_mode') == 'real' and
                data.get('dependencies', {}).get('crewai') == True and
                data.get('dependencies', {}).get('language_detection') == True
            )
            
            print(f"\n🎯 RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
            return success
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Run comprehensive validation"""
    print("🚀 FINAL VALIDATION OF REAL BACKEND DEPLOYMENT")
    print("=" * 60)
    
    # Test 0: Health endpoint
    health_success = test_health_endpoint()
    
    if not health_success:
        print("\n❌ Health check failed. Backend may not be running.")
        return False
    
    # Test 1: Persian speech recognition (the original problem)
    test1_success = test_persian_speech_recognition()
    
    # Test 2: React web app (backward compatibility)
    test2_success = test_react_web_app()
    
    # Overall result
    overall_success = health_success and test1_success and test2_success
    
    print(f"\n🎯 FINAL VALIDATION RESULT: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    if overall_success:
        print("\n🎉 CONGRATULATIONS! The real backend deployment is COMPLETE!")
        print("\n✅ ACHIEVEMENTS:")
        print("   ✅ Real backend is active (not mock)")
        print("   ✅ Language detection is working accurately")
        print("   ✅ Python requests generate Python code with appropriate libraries")
        print("   ✅ React requests generate React code")
        print("   ✅ No cross-contamination between language types")
        print("   ✅ Persian speech recognition generates speech_recognition + googletrans")
        print("   ✅ API endpoints are working correctly")
        print("\n🎯 MISSION ACCOMPLISHED:")
        print("   The system now correctly generates Python code for Python requests")
        print("   and React code for React requests, with intelligent language detection!")
    else:
        print("\n⚠️  Some validation tests failed. Check the output above for details.")
    
    return overall_success

if __name__ == "__main__":
    main()