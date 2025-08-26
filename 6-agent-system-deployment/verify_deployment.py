#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies that the deployed system is working correctly
"""

import requests
import json
import time

def verify_deployment(base_url="http://localhost:8000"):
    """Verify deployment is working"""
    print("🔍 Verifying 6-Agent System Deployment...")
    
    tests = []
    
    # Test 1: Health Check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        health_ok = response.status_code == 200
        tests.append(("Health Check", health_ok))
        print(f"✅ Health Check: {'PASS' if health_ok else 'FAIL'}")
    except Exception as e:
        tests.append(("Health Check", False))
        print(f"❌ Health Check: FAIL ({e})")
    
    # Test 2: API Stats
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=10)
        stats_ok = response.status_code == 200
        tests.append(("API Stats", stats_ok))
        print(f"✅ API Stats: {'PASS' if stats_ok else 'FAIL'}")
    except Exception as e:
        tests.append(("API Stats", False))
        print(f"❌ API Stats: FAIL ({e})")
    
    # Test 3: Project Creation Endpoint
    try:
        test_request = {
            "prompt": "Create a simple HTML page",
            "framework": "vanilla",
            "complexity": "simple"
        }
        response = requests.post(
            f"{base_url}/api/vibe-coding", 
            json=test_request, 
            timeout=10
        )
        project_ok = response.status_code == 200
        tests.append(("Project Creation", project_ok))
        print(f"✅ Project Creation: {'PASS' if project_ok else 'FAIL'}")
    except Exception as e:
        tests.append(("Project Creation", False))
        print(f"❌ Project Creation: FAIL ({e})")
    
    # Calculate success rate
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    success_rate = (passed / total) * 100
    
    print(f"\n📊 Deployment Verification Results:")
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ DEPLOYMENT VERIFIED - SYSTEM OPERATIONAL")
        return True
    else:
        print("❌ DEPLOYMENT ISSUES DETECTED")
        return False

if __name__ == "__main__":
    verify_deployment()
