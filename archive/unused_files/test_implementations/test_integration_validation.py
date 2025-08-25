#!/usr/bin/env python3
"""
Integration test to validate the multi-language code generation API.
Tests the actual API endpoints to ensure they generate correct language code.
"""

import requests
import json
import time
import sys
from pathlib import Path

# Test configuration
API_BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{API_BASE_URL}/api/generate"

# Test cases for different languages and project types
TEST_CASES = [
    {
        "name": "Python Speech Recognition",
        "description": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text. Include error handling and real-time processing.",
        "expected_language": "python",
        "expected_type": "cli_tool",
        "expected_keywords": ["speech_recognition", "pyaudio", "googletrans", "fa-IR", "def ", "import "],
        "expected_extensions": [".py", ".txt"]
    },
    {
        "name": "React Web Application",
        "description": "Build a React web application with a dashboard showing user analytics, charts, and real-time data updates. Include modern UI components and responsive design.",
        "expected_language": "javascript",
        "expected_type": "web_app",
        "expected_keywords": ["React", "useState", "useEffect", "JSX", "import React", "export default"],
        "expected_extensions": [".js", ".jsx", ".html", ".css"]
    },
    {
        "name": "Node.js Backend API",
        "description": "Create a Node.js REST API with Express for user authentication, JWT tokens, and MongoDB integration. Include middleware for rate limiting.",
        "expected_language": "javascript",
        "expected_type": "api",
        "expected_keywords": ["express", "app.get", "app.post", "middleware", "JWT", "MongoDB"],
        "expected_extensions": [".js", ".json"]
    },
    {
        "name": "Python Data Science",
        "description": "Create a Python machine learning script that analyzes customer data, performs clustering analysis using scikit-learn, and generates visualization plots with matplotlib.",
        "expected_language": "python",
        "expected_type": "cli_tool",
        "expected_keywords": ["pandas", "sklearn", "matplotlib", "import numpy", "def ", "plt."],
        "expected_extensions": [".py", ".txt"]
    },
    {
        "name": "Java Console Application",
        "description": "Write a Java console application that reads CSV files, processes employee payroll data, and generates detailed reports with exception handling.",
        "expected_language": "java",
        "expected_type": "cli_tool",
        "expected_keywords": ["public class", "import java", "try {", "catch", "public static void main"],
        "expected_extensions": [".java", ".txt"]
    }
]


def test_api_health():
    """Test if the API is running and healthy."""
    print("🏥 Testing API Health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ API is healthy and responding")
            return True
        else:
            print(f"   ❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API not reachable: {e}")
        return False


def test_language_detection_api():
    """Test the language detection through the API."""
    print("\n🔍 Testing Language Detection via API...")
    
    # Test the intent processor endpoint if available
    try:
        test_request = {
            "description": "Write a Python script for speech recognition"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/analyze-intent",
            json=test_request,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Intent analysis working: {data.get('project_type', 'unknown')}")
            return True
        else:
            print(f"   ⚠️  Intent analysis endpoint not available: {response.status_code}")
            return True  # Not critical for main functionality
    except requests.exceptions.RequestException:
        print("   ⚠️  Intent analysis endpoint not available")
        return True  # Not critical for main functionality


def test_code_generation(test_case):
    """Test code generation for a specific test case."""
    print(f"\n🧪 Testing: {test_case['name']}")
    print(f"   Description: {test_case['description'][:60]}...")
    
    # Prepare the request
    request_data = {
        "name": test_case['name'],
        "description": test_case['description'],
        "project_type": test_case['expected_type'],
        "languages": [test_case['expected_language']],
        "complexity": "moderate",
        "mode": "full"
    }
    
    try:
        # Send the request
        print("   📤 Sending generation request...")
        response = requests.post(
            API_ENDPOINT,
            json=request_data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"   ❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
        
        # Parse the response
        result = response.json()
        
        # Check if we got files back
        if 'code_files' not in result:
            print(f"   ❌ No code files in response")
            print(f"   Response keys: {list(result.keys())}")
            return False
        
        code_files = result['code_files']
        print(f"   📁 Generated {len(code_files)} files")
        
        # Analyze the generated files
        success = True
        found_keywords = []
        found_extensions = []
        
        for file_info in code_files:
            file_path = file_info.get('path', '')
            content = file_info.get('content', '')
            language = file_info.get('language', '')
            
            print(f"      📄 {file_path} ({language})")
            
            # Check file extension
            for ext in test_case['expected_extensions']:
                if file_path.endswith(ext):
                    found_extensions.append(ext)
                    break
            
            # Check for expected keywords
            for keyword in test_case['expected_keywords']:
                if keyword in content:
                    found_keywords.append(keyword)
            
            # Check language detection
            if language != test_case['expected_language']:
                print(f"         ⚠️  Language mismatch: expected {test_case['expected_language']}, got {language}")
        
        # Validate results
        print(f"   🔍 Analysis:")
        print(f"      Expected extensions: {test_case['expected_extensions']}")
        print(f"      Found extensions: {list(set(found_extensions))}")
        print(f"      Expected keywords: {test_case['expected_keywords']}")
        print(f"      Found keywords: {list(set(found_keywords))}")
        
        # Success criteria
        extension_match = any(ext in found_extensions for ext in test_case['expected_extensions'])
        keyword_match = len(set(found_keywords)) >= 2  # At least 2 expected keywords
        
        if extension_match and keyword_match:
            print(f"   ✅ PASS: Correct language and content generated")
            return True
        else:
            print(f"   ❌ FAIL: Language/content mismatch")
            if not extension_match:
                print(f"      Missing expected file extensions")
            if not keyword_match:
                print(f"      Missing expected keywords")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON response: {e}")
        return False


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🚀 Starting Comprehensive Integration Testing")
    print("="*60)
    
    # Test API health first
    if not test_api_health():
        print("\n❌ API is not available. Please start the server first.")
        return False
    
    # Test language detection
    test_language_detection_api()
    
    # Run all test cases
    results = []
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'='*20} Test {i}/{len(TEST_CASES)} {'='*20}")
        result = test_code_generation(test_case)
        results.append(result)
        
        # Add delay between tests to avoid overwhelming the server
        if i < len(TEST_CASES):
            print("   ⏳ Waiting 2 seconds before next test...")
            time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("🎉 INTEGRATION TEST RESULTS")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_case, result) in enumerate(zip(TEST_CASES, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i}. {test_case['name']}: {status}")
    
    print(f"\n📊 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Multi-language code generation is working correctly!")
        print("✅ Python scripts generate Python code")
        print("✅ React apps generate JSX components")
        print("✅ Node.js APIs generate Express servers")
        print("✅ Java apps generate Java classes")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        print("🔧 Some language detection or generation issues remain")
        return False


def main():
    """Main test runner."""
    try:
        success = run_comprehensive_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()