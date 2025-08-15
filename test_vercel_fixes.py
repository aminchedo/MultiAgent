#!/usr/bin/env python3
"""
Test script to verify Vercel deployment fixes.
This script can be run locally or on Vercel to test the endpoints.
"""

import os
import sys
import json
import requests
from typing import Dict, Any

def test_endpoint(base_url: str, endpoint: str, expected_status: int = 200) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url, timeout=10)
        return {
            "endpoint": endpoint,
            "url": url,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "success": response.status_code == expected_status,
            "response": response.text[:500] if response.text else "No content",
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "url": url,
            "status_code": None,
            "expected_status": expected_status,
            "success": False,
            "error": str(e),
            "response": None,
            "headers": None
        }

def run_tests(base_url: str = "http://localhost:8000") -> None:
    """Run all tests against the specified base URL"""
    print(f"Testing Vercel fixes against: {base_url}")
    print("=" * 60)
    
    # Test endpoints
    test_cases = [
        ("/", 200, "Root endpoint"),
        ("/favicon.ico", [200, 204], "Favicon ICO"),
        ("/favicon.png", [200, 204], "Favicon PNG"),
        ("/api/health", 200, "Health check"),
        ("/api", 200, "API root"),
        ("/api/test", 200, "Test endpoint"),
    ]
    
    results = []
    
    for endpoint, expected_status, description in test_cases:
        print(f"\nTesting {description} ({endpoint})...")
        
        if isinstance(expected_status, list):
            # Try multiple expected status codes
            for status in expected_status:
                result = test_endpoint(base_url, endpoint, status)
                if result["success"]:
                    break
        else:
            result = test_endpoint(base_url, endpoint, expected_status)
        
        results.append(result)
        
        if result["success"]:
            print(f"✅ PASS: {endpoint} - Status {result['status_code']}")
            if result["response"] and len(result["response"]) < 200:
                print(f"   Response: {result['response']}")
        else:
            print(f"❌ FAIL: {endpoint}")
            print(f"   Expected: {expected_status}, Got: {result.get('status_code', 'Error')}")
            if "error" in result:
                print(f"   Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Vercel fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
        
        # Show failed tests
        failed = [r for r in results if not r["success"]]
        if failed:
            print("\nFailed tests:")
            for result in failed:
                print(f"  - {result['endpoint']}: {result.get('error', f'Status {result.get("status_code")}')}")

def main():
    """Main function"""
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Check if we're running on Vercel
    if os.getenv("VERCEL"):
        print("Running on Vercel environment")
        # Try to get the Vercel URL from environment
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            base_url = f"https://{vercel_url}"
            print(f"Using Vercel URL: {base_url}")
    
    try:
        run_tests(base_url)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    main()