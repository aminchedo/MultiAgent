#!/usr/bin/env python3
"""
Simple test script to verify the UI fix and API functionality.
This script tests local files and configuration without external dependencies.
"""

import sys
import os
import json
from pathlib import Path

def test_local_files():
    """Test that required files exist locally"""
    print("📁 Testing local file structure...")
    
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
        
        # Check for required headers
        headers = config.get('headers', [])
        header_sources = [header.get('source', '') for header in headers]
        
        required_headers = [
            '/health',
            '/favicon.ico',
            '/favicon.png',
            '/static/(.*)',
            '/assets/(.*)',
            '/pages/(.*)'
        ]
        
        all_headers_present = True
        for required_header in required_headers:
            if any(required_header in src for src in header_sources):
                print(f"   ✅ Header: {required_header}")
            else:
                print(f"   ❌ Header: {required_header} - Missing!")
                all_headers_present = False
        
        return all_routes_present and all_headers_present
        
    except Exception as e:
        print(f"   ❌ Error reading vercel.json: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI application structure"""
    print("\n🐍 Testing FastAPI application...")
    
    try:
        # Check if the app can be imported
        sys.path.insert(0, os.path.join(os.getcwd(), 'api'))
        
        # Try to import the app
        try:
            from vercel_app import app
            print("   ✅ FastAPI app imported successfully")
            
            # Check for required endpoints
            routes = [route.path for route in app.routes]
            required_endpoints = ['/', '/api/info', '/health', '/favicon.ico', '/favicon.png']
            
            all_endpoints_present = True
            for endpoint in required_endpoints:
                if endpoint in routes:
                    print(f"   ✅ Endpoint: {endpoint}")
                else:
                    print(f"   ❌ Endpoint: {endpoint} - Missing!")
                    all_endpoints_present = False
            
            return all_endpoints_present
            
        except ImportError as e:
            print(f"   ❌ Failed to import FastAPI app: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing FastAPI app: {e}")
        return False

def test_jwt_script():
    """Test JWT secret generation script"""
    print("\n🔐 Testing JWT secret generation script...")
    
    try:
        # Check if script exists and is executable
        script_path = "scripts/generate_jwt_secret.py"
        if os.path.exists(script_path):
            print("   ✅ JWT script exists")
            
            # Check if it's executable
            if os.access(script_path, os.X_OK):
                print("   ✅ JWT script is executable")
            else:
                print("   ⚠️  JWT script is not executable (will be fixed)")
                os.chmod(script_path, 0o755)
                print("   ✅ JWT script permissions fixed")
            
            return True
        else:
            print("   ❌ JWT script missing")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing JWT script: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Multi-Agent API UI Fix")
    print("=" * 50)
    
    # Test local files
    files_ok = test_local_files()
    
    # Test vercel.json configuration
    config_ok = test_vercel_config()
    
    # Test FastAPI application
    app_ok = test_fastapi_app()
    
    # Test JWT script
    jwt_ok = test_jwt_script()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Local Files: {'✅ PASS' if files_ok else '❌ FAIL'}")
    print(f"   Vercel Config: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   FastAPI App: {'✅ PASS' if app_ok else '❌ FAIL'}")
    print(f"   JWT Script: {'✅ PASS' if jwt_ok else '❌ FAIL'}")
    
    if files_ok and config_ok and app_ok and jwt_ok:
        print("\n🎉 All tests passed! The UI fix is ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Generate a secure JWT secret: python3 scripts/generate_jwt_secret.py")
        print("2. Set JWT_SECRET_KEY in Vercel environment variables")
        print("3. Deploy to Vercel: vercel --prod")
        print("4. Test the deployed application")
        print("\n🔧 Manual testing commands:")
        print("   # Test locally:")
        print("   uvicorn api.vercel_app:app --reload --host 0.0.0.0 --port 8000")
        print("   # Test static files:")
        print("   python3 -m http.server -d public 8080")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())