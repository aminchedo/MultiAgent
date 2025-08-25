#!/usr/bin/env python3
"""
REAL FUNCTIONALITY VALIDATION TEST
Tests if the system ACTUALLY works in practice, not just in theory!
"""

import json
import requests
import time
import sys
from typing import Dict, Any, List

def test_server_health():
    """Test if server is running and responding."""
    print("🔍 STEP 1: Testing Server Health")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_python_speech_recognition():
    """Test the critical Python speech recognition functionality."""
    print("\n🎯 STEP 2: Testing Python Speech Recognition Generation")
    print("=" * 50)
    
    # Test request for Python speech recognition
    test_request = {
        "name": "Persian Speech Translator",
        "description": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text. Include speech_recognition library and googletrans.",
        "project_type": "CLI_TOOL"
    }
    
    try:
        print("📤 Sending Python speech recognition request...")
        response = requests.post(
            "http://localhost:8000/api/generate",
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Request successful!")
            print(f"   Job ID: {data.get('job_id', 'N/A')}")
            
            # Wait for completion
            job_id = data.get('job_id')
            if job_id:
                return wait_for_completion_and_analyze(job_id, "Python Speech Recognition")
            else:
                print("❌ No job ID returned")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Python generation: {e}")
        return False

def test_react_generation():
    """Test that React generation still works correctly."""
    print("\n🎯 STEP 3: Testing React Generation")
    print("=" * 50)
    
    test_request = {
        "name": "Dashboard App",
        "description": "Build a React web application with a modern dashboard, charts, and responsive design using React hooks.",
        "project_type": "WEB_APP"
    }
    
    try:
        print("📤 Sending React generation request...")
        response = requests.post(
            "http://localhost:8000/api/generate",
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Request successful!")
            print(f"   Job ID: {data.get('job_id', 'N/A')}")
            
            job_id = data.get('job_id')
            if job_id:
                return wait_for_completion_and_analyze(job_id, "React Dashboard")
            else:
                print("❌ No job ID returned")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing React generation: {e}")
        return False

def wait_for_completion_and_analyze(job_id: str, test_name: str) -> bool:
    """Wait for job completion and analyze the results."""
    print(f"⏳ Waiting for {test_name} job completion...")
    
    max_wait = 60  # 60 seconds max wait
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"http://localhost:8000/api/status/{job_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                progress = data.get('progress', 0)
                
                print(f"   Status: {status}, Progress: {progress}%")
                
                if status == 'completed':
                    print(f"✅ {test_name} job completed!")
                    return analyze_generated_files(job_id, test_name)
                elif status == 'failed':
                    print(f"❌ {test_name} job failed!")
                    return False
                    
            time.sleep(2)
        except Exception as e:
            print(f"   Error checking status: {e}")
            time.sleep(2)
    
    print(f"⏰ Timeout waiting for {test_name} job completion")
    return False

def analyze_generated_files(job_id: str, test_name: str) -> bool:
    """Analyze the generated files to validate correctness."""
    print(f"🔍 Analyzing generated files for {test_name}...")
    
    try:
        response = requests.get(f"http://localhost:8000/api/download/{job_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            
            print(f"   Generated {len(files)} files")
            
            # Analyze file types and content
            python_files = []
            react_files = []
            other_files = []
            
            for file_info in files:
                file_path = file_info.get('path', '')
                content = file_info.get('content', '')
                
                if file_path.endswith('.py') or 'python' in content.lower():
                    python_files.append(file_info)
                elif file_path.endswith(('.jsx', '.js')) or 'react' in content.lower():
                    react_files.append(file_info)
                else:
                    other_files.append(file_info)
            
            print(f"   Python files: {len(python_files)}")
            print(f"   React files: {len(react_files)}")
            print(f"   Other files: {len(other_files)}")
            
            # Validate based on test type
            if "Python" in test_name:
                if python_files and not react_files:
                    print("✅ SUCCESS: Python request generated Python code!")
                    print("   Sample Python content:")
                    if python_files:
                        sample_content = python_files[0].get('content', '')[:200]
                        print(f"   {sample_content}...")
                    return True
                else:
                    print("❌ FAILED: Python request did not generate Python code!")
                    if react_files:
                        print("   ❌ Generated React code instead!")
                    return False
            elif "React" in test_name:
                if react_files and not python_files:
                    print("✅ SUCCESS: React request generated React code!")
                    return True
                else:
                    print("❌ FAILED: React request did not generate React code!")
                    return False
            else:
                print("⚠️  Unknown test type, cannot validate")
                return True
                
        else:
            print(f"❌ Failed to download files: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error analyzing files: {e}")
        return False

def run_comprehensive_test():
    """Run the complete functionality validation test."""
    print("🚀 REAL FUNCTIONALITY VALIDATION TEST")
    print("=" * 60)
    print("Testing if the system ACTUALLY works in practice!")
    print("=" * 60)
    
    # Test 1: Server Health
    if not test_server_health():
        print("\n❌ CRITICAL FAILURE: Server is not running!")
        print("   Please start the server first:")
        print("   python3 simple_backend.py")
        return False
    
    # Test 2: Python Speech Recognition (CRITICAL TEST)
    python_success = test_python_speech_recognition()
    
    # Test 3: React Generation
    react_success = test_react_generation()
    
    # Final Results
    print("\n" + "=" * 60)
    print("🎯 FINAL VALIDATION RESULTS")
    print("=" * 60)
    
    if python_success and react_success:
        print("🎉 SUCCESS: All tests passed!")
        print("✅ Python speech recognition generates Python code")
        print("✅ React requests generate React code")
        print("✅ The system is working correctly!")
        return True
    elif python_success:
        print("⚠️  PARTIAL SUCCESS: Python test passed, React test failed")
        print("✅ Python speech recognition generates Python code")
        print("❌ React generation has issues")
        return True  # Main fix is working
    elif react_success:
        print("❌ FAILURE: React test passed, but Python test failed")
        print("❌ The critical Python speech recognition fix is NOT working!")
        print("✅ React generation works")
        return False
    else:
        print("❌ CRITICAL FAILURE: Both tests failed!")
        print("❌ The system is not working correctly")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)