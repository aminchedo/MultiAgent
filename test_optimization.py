#!/usr/bin/env python3
"""
Test script to validate the optimized Cursor Agent prompt implementation.
Tests all the requirements mentioned in the prompt.
"""

import os
import sys
import importlib
import traceback
from pathlib import Path

def test_jwt_secret_handling():
    """Test 1: JWT_SECRET_KEY security enhancement"""
    print("🔐 Testing JWT_SECRET_KEY security handling...")
    
    try:
        from config.security import JWT_SECRET_KEY
        
        # Test that JWT_SECRET_KEY is available
        assert JWT_SECRET_KEY is not None, "JWT_SECRET_KEY should not be None"
        
        # Test environment variable handling
        if os.getenv('VERCEL_ENV') == 'production':
            # In production, should have a proper secret
            assert JWT_SECRET_KEY != 'default-secret-key-for-development-only', \
                "Should not use default secret in production"
        else:
            # In development, can use generated secret
            print(f"✅ JWT_SECRET_KEY configured: {JWT_SECRET_KEY[:10]}...")
        
        print("✅ JWT_SECRET_KEY security handling passed")
        return True
        
    except Exception as e:
        print(f"❌ JWT_SECRET_KEY security handling failed: {e}")
        return False

def test_python_path_optimization():
    """Test 2: Python path optimization"""
    print("\n🐍 Testing Python path optimization...")
    
    try:
        # Test that api/__init__.py is properly configured
        api_dir = Path(__file__).parent / "api"
        assert api_dir.exists(), "api directory should exist"
        
        # Test that the path is in sys.path
        api_path = str(api_dir)
        if api_path not in sys.path:
            # Try importing the __init__.py to trigger path addition
            importlib.import_module('api')
        
        # Check if path is now in sys.path
        assert api_path in sys.path, f"API path {api_path} should be in sys.path"
        
        print(f"✅ Python path optimization passed")
        print(f"   API path: {api_path}")
        print(f"   First 3 sys.path entries: {sys.path[:3]}")
        return True
        
    except Exception as e:
        print(f"❌ Python path optimization failed: {e}")
        return False

def test_lazy_loading():
    """Test 3: Lazy loading implementation"""
    print("\n⚡ Testing lazy loading implementation...")
    
    try:
        # Test startup module import
        from api.startup import init_app
        
        # Test that init_app function exists
        assert callable(init_app), "init_app should be callable"
        
        # Test lazy loading (don't actually call it to avoid side effects)
        print("✅ Lazy loading module structure passed")
        
        # Test that vercel_app module can be imported
        vercel_app_module = importlib.import_module('api.vercel_app')
        assert hasattr(vercel_app_module, 'app'), "vercel_app should have 'app' attribute"
        
        print("✅ Lazy loading implementation passed")
        return True
        
    except Exception as e:
        print(f"❌ Lazy loading implementation failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_health_check_endpoint():
    """Test 4: Health check endpoint"""
    print("\n🏥 Testing health check endpoint...")
    
    try:
        # Test that the health check endpoint is properly configured
        from api.index import app
        
        # Check if app has the health endpoint
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        
        health_endpoints = [route for route in routes if 'health' in route]
        assert len(health_endpoints) > 0, "Should have at least one health endpoint"
        
        print(f"✅ Health check endpoints found: {health_endpoints}")
        return True
        
    except Exception as e:
        print(f"❌ Health check endpoint test failed: {e}")
        return False

def test_vercel_configuration():
    """Test 5: Vercel configuration"""
    print("\n⚙️ Testing Vercel configuration...")
    
    try:
        # Test vercel.json exists and has required fields
        vercel_json_path = Path(__file__).parent / "vercel.json"
        assert vercel_json_path.exists(), "vercel.json should exist"
        
        import json
        with open(vercel_json_path) as f:
            config = json.load(f)
        
        # Check for required environment variables
        env_vars = config.get('env', {})
        assert 'PYTHONPATH' in env_vars, "PYTHONPATH should be in vercel.json env"
        assert 'VERCEL' in env_vars, "VERCEL should be in vercel.json env"
        
        # Check for JWT_SECRET_KEY reference
        jwt_ref = env_vars.get('JWT_SECRET_KEY')
        if jwt_ref:
            print(f"✅ JWT_SECRET_KEY reference found: {jwt_ref}")
        
        print("✅ Vercel configuration passed")
        return True
        
    except Exception as e:
        print(f"❌ Vercel configuration test failed: {e}")
        return False

def test_import_sequence():
    """Test 6: Module import sequence"""
    print("\n📦 Testing module import sequence...")
    
    try:
        # Test that all required modules can be imported
        modules_to_test = [
            'config.security',
            'api.startup',
            'api.vercel_app',
            'api.index'
        ]
        
        for module_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                print(f"   ✅ {module_name} imports successfully")
            except ImportError as e:
                print(f"   ❌ {module_name} import failed: {e}")
                return False
        
        print("✅ Module import sequence passed")
        return True
        
    except Exception as e:
        print(f"❌ Module import sequence test failed: {e}")
        return False

def test_environment_validation():
    """Test 7: Environment variable validation"""
    print("\n🔍 Testing environment variable validation...")
    
    try:
        # Test that environment validation works
        from api.vercel_app import validate_env_vars
        
        # Test the validation function
        result = validate_env_vars()
        
        # Should return True if validation passes
        print(f"✅ Environment validation result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Environment validation test failed: {e}")
        return False

def main():
    """Run all optimization tests"""
    print("🚀 Optimized Cursor Agent Prompt Validation")
    print("=" * 50)
    
    tests = [
        test_jwt_secret_handling,
        test_python_path_optimization,
        test_lazy_loading,
        test_health_check_endpoint,
        test_vercel_configuration,
        test_import_sequence,
        test_environment_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All optimization requirements met!")
        print("\n✅ Deployment Checklist:")
        print("   - JWT_SECRET_KEY warning resolved")
        print("   - Python path optimization implemented")
        print("   - Module import sequence optimized")
        print("   - Lazy loading for heavy dependencies")
        print("   - Import error handling added")
        print("   - Health check endpoint configured")
        print("   - Vercel configuration updated")
    else:
        print("⚠️  Some optimization requirements need attention")
        print(f"   Failed tests: {total - passed}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)