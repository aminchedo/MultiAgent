#!/usr/bin/env python3
"""
Test the API endpoint directly
"""

import requests
import json

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/health")
        print(f"Health check status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_generate_endpoint():
    """Test the generate endpoint"""
    try:
        payload = {
            "description": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text",
            "name": "Persian Speech Translator"
        }
        
        # Create a simple JWT token for testing
        import jwt
        import datetime
        
        secret = "secret"  # Same as in the API
        payload_jwt = {
            "user_id": "test-user",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload_jwt, secret, algorithm="HS256")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post("http://127.0.0.1:8000/api/generate", 
                               json=payload, 
                               headers=headers)
        
        print(f"Generate endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Backend mode: {data.get('backend_mode')}")
            print(f"Language detected: {data.get('language_detected')}")
            print(f"Project type: {data.get('project_type')}")
            print(f"Files generated: {len(data.get('files', []))}")
            
            # Check for Python files
            files = data.get('files', [])
            python_files = [f for f in files if f.get('name', '').endswith('.py')]
            react_files = [f for f in files if 'react' in f.get('content', '').lower() or f.get('name', '').endswith('.jsx')]
            
            print(f"Python files: {len(python_files)}")
            print(f"React files: {len(react_files)}")
            
            # Check for speech recognition content
            main_py_content = ""
            for file in files:
                if file.get('name') == 'main.py':
                    main_py_content = file.get('content', '')
                    break
            
            has_speech_recognition = 'speech_recognition' in main_py_content
            has_googletrans = 'googletrans' in main_py_content
            has_persian = 'persian' in main_py_content.lower() or 'farsi' in main_py_content.lower()
            
            print(f"Speech recognition import: {'✅' if has_speech_recognition else '❌'}")
            print(f"Google translate import: {'✅' if has_googletrans else '❌'}")
            print(f"Persian/Farsi references: {'✅' if has_persian else '❌'}")
            
            # Debug: Show first few lines of main.py
            if main_py_content:
                print(f"\nFirst 5 lines of main.py:")
                lines = main_py_content.split('\n')[:5]
                for i, line in enumerate(lines, 1):
                    print(f"  {i}: {line}")
            
            success = (
                data.get('backend_mode') == 'real' and
                data.get('language_detected') == 'python' and
                len(python_files) > 0 and
                len(react_files) == 0 and
                has_speech_recognition and
                has_googletrans and
                has_persian
            )
            
            print(f"\n🎯 API TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
            return success
        else:
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Generate endpoint failed: {e}")
        return False

def main():
    """Run API tests"""
    print("🧪 TESTING API ENDPOINTS")
    print("=" * 40)
    
    # Test health endpoint
    health_success = test_health_endpoint()
    
    if health_success:
        # Test generate endpoint
        generate_success = test_generate_endpoint()
        
        overall_success = health_success and generate_success
        
        print(f"\n🎯 OVERALL API RESULT: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
        
        if overall_success:
            print("\n🎉 CONGRATULATIONS! The API is working correctly:")
            print("   ✅ Health endpoint returns real backend mode")
            print("   ✅ Generate endpoint uses language detection")
            print("   ✅ Python requests generate Python code")
            print("   ✅ No React files for Python requests")
        else:
            print("\n⚠️  Some API issues remain. Check the output above for details.")
    else:
        print("❌ Health check failed, skipping generate test")

if __name__ == "__main__":
    main()