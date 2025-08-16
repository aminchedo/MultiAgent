#!/usr/bin/env python3
"""
Incremental Fixes Verification Script
Tests the newly created /api/generate endpoint
"""

import requests
import json
import time
import sys

def test_endpoint(url, description, expected_language, test_name):
    """Test the generate endpoint with given parameters"""
    print(f"\n🧪 Testing: {test_name}")
    print(f"📝 Description: {description[:60]}...")
    
    payload = {
        "description": description,
        "name": f"Test {test_name}"
    }
    
    try:
        response = requests.post(
            f"{url}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            detected_lang = data.get('language_detected', 'unknown')
            files = data.get('files', [])
            backend_mode = data.get('backend_mode', 'unknown')
            
            print(f"✅ Status: {data.get('status', 'unknown')}")
            print(f"🔧 Backend Mode: {backend_mode}")
            print(f"🔍 Language Detected: {detected_lang}")
            print(f"📁 Files Generated: {len(files)}")
            
            # Language validation
            if detected_lang == expected_language:
                print(f"✅ Language Detection: CORRECT ({detected_lang})")
            else:
                print(f"❌ Language Detection: FAILED (expected {expected_language}, got {detected_lang})")
                return False
            
            # File type validation
            python_files = [f for f in files if f['name'].endswith('.py')]
            react_files = [f for f in files if 'React' in f.get('content', '') or f['name'].endswith('.jsx')]
            
            print(f"🐍 Python files: {len(python_files)}")
            print(f"⚛️  React files: {len(react_files)}")
            
            # Cross-contamination check
            if expected_language == 'python' and react_files:
                print("❌ CONTAMINATION: Python request generated React files!")
                return False
            elif expected_language == 'javascript' and python_files and not react_files:
                print("❌ CONTAMINATION: JavaScript request generated only Python files!")
                return False
            
            print("✅ No cross-contamination detected")
            return True
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🔧 INCREMENTAL FIXES VERIFICATION")
    print("=" * 50)
    
    # Test local development server
    base_url = "http://localhost:3000"
    
    test_cases = [
        {
            "description": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text",
            "expected_language": "python",
            "test_name": "Persian Speech Recognition"
        },
        {
            "description": "Build a React web application with dashboard and charts for data visualization",
            "expected_language": "javascript",
            "test_name": "React Dashboard"
        },
        {
            "description": "Create a Node.js REST API with Express and MongoDB for user management",
            "expected_language": "javascript", 
            "test_name": "Node.js API"
        },
        {
            "description": "Python CLI tool for data processing and analysis",
            "expected_language": "python",
            "test_name": "Python CLI Tool"
        }
    ]
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Health check failed - server not responding properly")
            return False
    except:
        print("❌ Server not running. Please start with: npm run dev")
        print("ℹ️  This script tests the local development server")
        return False
    
    print("✅ Server health check passed")
    
    # Run all test cases
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        success = test_endpoint(
            base_url,
            test_case["description"],
            test_case["expected_language"],
            test_case["test_name"]
        )
        
        if success:
            passed += 1
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"✅ Tests Passed: {passed}/{total}")
    print(f"❌ Tests Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ /api/generate endpoint is working correctly")
        print("✅ Language detection is accurate")
        print("✅ No cross-contamination between languages")
        print("✅ System ready for deployment")
        return True
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        print("🔧 Please review the endpoint implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)