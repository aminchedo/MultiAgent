#!/usr/bin/env python3
"""
Test script to validate the generate endpoint functionality
"""

import requests
import json
import sys
from typing import Dict, Any

def test_generate_endpoint(base_url: str = "http://localhost:3000") -> bool:
    """Test the generate endpoint with different types of requests."""
    
    print("🧪 Testing Generate Endpoint")
    print("=" * 50)
    
    # Test 1: Persian Speech Recognition (should return Python)
    print("\n1️⃣ Testing Persian Speech Recognition Request...")
    persian_request = {
        "description": "Create a Python script for Persian speech recognition and English translation",
        "name": "Persian Speech Translator"
    }
    
    try:
        response = requests.post(f"{base_url}/api/generate", 
                               json=persian_request, 
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status')}")
            print(f"🔍 Language Detected: {data.get('language_detected')}")
            print(f"📋 Project Type: {data.get('project_type')}")
            
            # Validate Python generation
            files = data.get('files', [])
            python_files = [f for f in files if f.get('name', '').endswith('.py')]
            react_files = [f for f in files if 'react' in f.get('content', '').lower()]
            
            print(f"📁 Total Files: {len(files)}")
            print(f"🐍 Python Files: {len(python_files)}")
            print(f"⚛️ React Files: {len(react_files)}")
            
            if data.get('language_detected') == 'python' and len(python_files) > 0 and len(react_files) == 0:
                print("✅ PASS: Persian request correctly generated Python code")
            else:
                print("❌ FAIL: Persian request did not generate correct Python code")
                return False
                
        else:
            print(f"❌ FAIL: Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Request failed with error: {e}")
        return False
    
    # Test 2: React Dashboard (should return JavaScript/React)
    print("\n2️⃣ Testing React Dashboard Request...")
    react_request = {
        "description": "Create a React web application with dashboard and charts",
        "name": "React Dashboard"
    }
    
    try:
        response = requests.post(f"{base_url}/api/generate", 
                               json=react_request, 
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status')}")
            print(f"🔍 Language Detected: {data.get('language_detected')}")
            print(f"📋 Project Type: {data.get('project_type')}")
            
            # Validate React generation
            files = data.get('files', [])
            react_files = [f for f in files if f.get('name', '').endswith('.jsx') or 'react' in f.get('content', '').lower()]
            python_files = [f for f in files if f.get('name', '').endswith('.py')]
            
            print(f"📁 Total Files: {len(files)}")
            print(f"⚛️ React Files: {len(react_files)}")
            print(f"🐍 Python Files: {len(python_files)}")
            
            if data.get('language_detected') == 'javascript' and len(react_files) > 0:
                print("✅ PASS: React request correctly generated JavaScript/React code")
            else:
                print("❌ FAIL: React request did not generate correct JavaScript/React code")
                return False
                
        else:
            print(f"❌ FAIL: Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Request failed with error: {e}")
        return False
    
    # Test 3: Health Check
    print("\n3️⃣ Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Status: {data.get('status')}")
            print("✅ PASS: Health endpoint working")
        else:
            print(f"❌ FAIL: Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Health check failed with error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! Generate endpoint is working correctly.")
    print("=" * 50)
    
    return True

def test_production_urls():
    """Test against production URLs if available."""
    production_urls = [
        "https://multi-agent-code-generation-system.vercel.app",
        "https://your-production-domain.vercel.app"  # Replace with actual domain
    ]
    
    for url in production_urls:
        print(f"\n🌐 Testing production URL: {url}")
        try:
            response = requests.get(f"{url}/api/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Production URL {url} is accessible")
                if test_generate_endpoint(url):
                    print(f"✅ Production deployment is working correctly!")
                    return True
            else:
                print(f"❌ Production URL {url} returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Production URL {url} is not accessible: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 Generate Endpoint Validation Test")
    print("=" * 60)
    
    # Test local development
    print("\n🔧 Testing Local Development Server...")
    local_success = test_generate_endpoint()
    
    # Test production if local fails
    if not local_success:
        print("\n🌐 Testing Production Deployment...")
        production_success = test_production_urls()
        
        if not production_success:
            print("\n❌ Both local and production tests failed!")
            sys.exit(1)
    else:
        print("\n✅ Local development server is working correctly!")
        print("💡 To test production, deploy to Vercel and update the production URLs in this script.")
    
    print("\n🎯 Test Summary:")
    print("- ✅ Generate endpoint created and functional")
    print("- ✅ Language detection working correctly")
    print("- ✅ Python requests generate Python code (no React contamination)")
    print("- ✅ React requests generate JavaScript/React code")
    print("- ✅ Health endpoint accessible")
    print("\n🚀 Ready for production deployment!")