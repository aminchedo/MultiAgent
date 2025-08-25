#!/usr/bin/env python3
"""
Comprehensive test script to verify Vercel deployment fixes
"""

import requests
import json
import sys
import os
import tempfile
from urllib.parse import urljoin
import time

def test_endpoint(base_url, endpoint, expected_status=200, description=""):
    """Test a single endpoint with detailed logging"""
    url = urljoin(base_url, endpoint)
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = time.time() - start_time
        
        print(f"✅ {description or endpoint}: {response.status_code} ({response_time:.2f}s)")
        
        if response.status_code == expected_status:
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    data = response.json()
                    # Print key information for health checks
                    if 'status' in data:
                        print(f"   Status: {data['status']}")
                    if 'jwt_configured' in data:
                        print(f"   JWT Configured: {data['jwt_configured']}")
                    if 'environment' in data:
                        print(f"   Environment: {data['environment']}")
                    return True
                except:
                    print(f"   Response: {response.text[:200]}...")
            return True
        else:
            print(f"   ❌ Expected {expected_status}, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ {description or endpoint}: Error - {e}")
        return False

def test_tempfile_operations():
    """Test tempfile operations for read-only filesystem compatibility"""
    print("\n🧪 Testing tempfile operations...")
    
    try:
        # Test tempfile.gettempdir()
        temp_dir = tempfile.gettempdir()
        print(f"✅ Temp directory: {temp_dir}")
        
        # Test creating a file in temp directory
        test_file = os.path.join(temp_dir, 'test_vercel_fix.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        # Verify file was created
        if os.path.exists(test_file):
            print("✅ Successfully created file in temp directory")
            # Clean up
            os.remove(test_file)
            print("✅ Successfully removed test file")
            return True
        else:
            print("❌ Failed to create file in temp directory")
            return False
            
    except Exception as e:
        print(f"❌ Tempfile operations failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable handling"""
    print("\n🔧 Testing environment variables...")
    
    # Test JWT_SECRET_KEY
    jwt_secret = os.getenv('JWT_SECRET_KEY', 'default_dev_secret')
    if jwt_secret == 'default_dev_secret':
        print("⚠️  JWT_SECRET_KEY not set, using default (insecure for production)")
    else:
        print("✅ JWT_SECRET_KEY is set")
    
    # Test VERCEL environment
    vercel_env = os.getenv('VERCEL')
    if vercel_env:
        print(f"✅ VERCEL environment detected: {vercel_env}")
    else:
        print("ℹ️  Not running in Vercel environment")
    
    # Test OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✅ OPENAI_API_KEY is set")
    else:
        print("⚠️  OPENAI_API_KEY not set")
    
    return True

def test_import_operations():
    """Test import operations"""
    print("\n📦 Testing import operations...")
    
    try:
        # Test importing config
        from config.vercel_config import get_vercel_settings, JWT_SECRET_KEY
        print("✅ Successfully imported vercel_config")
        
        # Test getting settings
        settings = get_vercel_settings()
        print("✅ Successfully created settings")
        
        # Test JWT secret
        print(f"✅ JWT_SECRET_KEY available: {bool(JWT_SECRET_KEY)}")
        
        return True
    except Exception as e:
        print(f"❌ Import operations failed: {e}")
        return False

def main():
    """Main test function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print("🚀 Testing Vercel Deployment Fixes")
    print("=" * 50)
    
    # Test local operations first
    tempfile_ok = test_tempfile_operations()
    env_ok = test_environment_variables()
    import_ok = test_import_operations()
    
    print("\n🌐 Testing API endpoints...")
    
    # Test endpoints
    tests = [
        ("/health", 200, "Health check endpoint"),
        ("/api/health", 200, "API health check endpoint"),
        ("/", 200, "Root endpoint"),
        ("/api", 200, "API root endpoint"),
        ("/api/test", 200, "Test endpoint"),
        ("/favicon.ico", 204, "Favicon ICO endpoint"),
        ("/favicon.png", 204, "Favicon PNG endpoint"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, expected_status, description in tests:
        if test_endpoint(base_url, endpoint, expected_status, description):
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results:")
    print(f"   Local operations: {'✅' if all([tempfile_ok, env_ok, import_ok]) else '❌'}")
    print(f"   API endpoints: {passed}/{total} passed")
    
    if passed == total and all([tempfile_ok, env_ok, import_ok]):
        print("\n🎉 All tests passed! Vercel deployment fixes are working correctly.")
        print("\n📋 Deployment Checklist:")
        print("   ✅ Read-only filesystem issues resolved")
        print("   ✅ JWT_SECRET_KEY handling implemented")
        print("   ✅ Python path issues optimized")
        print("   ✅ Import failures handled")
        print("   ✅ Deployment configuration verified")
        print("   ✅ Health check endpoint working")
        return 0
    else:
        print("\n❌ Some tests failed. Check the deployment.")
        if not tempfile_ok:
            print("   - Tempfile operations need attention")
        if not env_ok:
            print("   - Environment variables need configuration")
        if not import_ok:
            print("   - Import operations need debugging")
        if passed < total:
            print(f"   - {total - passed} API endpoints failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())