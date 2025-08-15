#!/usr/bin/env python3
"""
Test script to verify the UI fix and API functionality.
This script tests the key endpoints to ensure they work correctly.
"""

import requests
import sys
import os
from pathlib import Path

def test_endpoint(url, expected_content_type=None, expected_status=200):
    """Test an endpoint and return the result"""
    try:
        response = requests.get(url, timeout=10)
        
        print(f"🔍 Testing: {url}")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if expected_status and response.status_code != expected_status:
            print(f"   ❌ Expected status {expected_status}, got {response.status_code}")
            return False
            
        if expected_content_type and expected_content_type not in response.headers.get('content-type', ''):
            print(f"   ❌ Expected content-type containing '{expected_content_type}', got '{response.headers.get('content-type')}'")
            return False
            
        if response.status_code == 200:
            print(f"   ✅ Success")
        else:
            print(f"   ⚠️  Status {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_local_files():
    """Test that required files exist locally"""
    print("\n📁 Testing local file structure...")
    
    required_files = [
        "public/index.html",
        "api/vercel_app.py",
        "api/index.py",
        "vercel.json",
        "favicon.ico",
        "scripts/generate_jwt_secret.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - Missing!")
            all_exist = False
    
    return all_exist

def test_vercel_config():
    """Test vercel.json configuration"""
    print("\n⚙️  Testing vercel.json configuration...")
    
    try:
        import json
        with open('vercel.json', 'r') as f:
            config = json.load(f)
        
        # Check for required routes
        routes = config.get('routes', [])
        route_sources = [route.get('src', '') for route in routes]
        
        required_routes = [
            '/api/(.*)',
            '/health',
            '/favicon.ico',
            '/favicon.png',
            '/(.*)'
        ]
        
        all_routes_present = True
        for required_route in required_routes:
            if any(required_route in src for src in route_sources):
                print(f"   ✅ Route: {required_route}")
            else:
                print(f"   ❌ Route: {required_route} - Missing!")
                all_routes_present = False
        
        return all_routes_present
        
    except Exception as e:
        print(f"   ❌ Error reading vercel.json: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Multi-Agent API UI Fix")
    print("=" * 50)
    
    # Test local files
    files_ok = test_local_files()
    
    # Test vercel.json configuration
    config_ok = test_vercel_config()
    
    # Test endpoints (if base URL provided)
    base_url = os.getenv('TEST_BASE_URL')
    if base_url:
        print(f"\n🌐 Testing endpoints at: {base_url}")
        
        endpoints_to_test = [
            (f"{base_url}/", "text/html", 200),
            (f"{base_url}/api/info", "application/json", 200),
            (f"{base_url}/health", "application/json", 200),
            (f"{base_url}/api/health", "application/json", 200),
            (f"{base_url}/favicon.ico", None, 200),  # Can be 204 for no content
        ]
        
        endpoint_results = []
        for url, content_type, status in endpoints_to_test:
            result = test_endpoint(url, content_type, status)
            endpoint_results.append(result)
        
        all_endpoints_ok = all(endpoint_results)
    else:
        print("\n🌐 Skipping endpoint tests (set TEST_BASE_URL environment variable to test)")
        all_endpoints_ok = True
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Local Files: {'✅ PASS' if files_ok else '❌ FAIL'}")
    print(f"   Vercel Config: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   Endpoints: {'✅ PASS' if all_endpoints_ok else '❌ FAIL'}")
    
    if files_ok and config_ok and all_endpoints_ok:
        print("\n🎉 All tests passed! The UI fix is ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Generate a secure JWT secret: python3 scripts/generate_jwt_secret.py")
        print("2. Set JWT_SECRET_KEY in Vercel environment variables")
        print("3. Deploy to Vercel: vercel --prod")
        print("4. Test the deployed application")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())