#!/usr/bin/env python3
"""
Simple functionality test using subprocess and curl
"""

import subprocess
import json
import time
import sys

def run_curl_command(command):
    """Run a curl command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def test_server_health():
    """Test if server is running."""
    print("🔍 STEP 1: Testing Server Health")
    print("=" * 50)
    
    success, output, error = run_curl_command("curl -s http://localhost:8000/api/health")
    
    if success and output:
        print("✅ Server is running and responding")
        print(f"   Response: {output.strip()}")
        return True
    else:
        print("❌ Server is not responding")
        print(f"   Error: {error}")
        return False

def test_python_generation():
    """Test Python speech recognition generation."""
    print("\n🎯 STEP 2: Testing Python Speech Recognition Generation")
    print("=" * 50)
    
    # Test request
    curl_command = '''curl -s -X POST http://localhost:8000/api/generate \\
        -H "Content-Type: application/json" \\
        -d '{"prompt": "Write a Python script that captures audio from the microphone, recognizes spoken Persian (Farsi), and translates it to English text. Include speech_recognition library and googletrans.", "projectType": "cli"}' '''
    
    print("📤 Sending Python speech recognition request...")
    success, output, error = run_curl_command(curl_command)
    
    if success and output:
        try:
            data = json.loads(output)
            job_id = data.get('job_id')
            if job_id:
                print(f"✅ Request successful! Job ID: {job_id}")
                return wait_for_completion_and_analyze(job_id, "Python Speech Recognition")
            else:
                print("❌ No job ID returned")
                print(f"   Response: {output}")
                return False
        except json.JSONDecodeError:
            print("❌ Invalid JSON response")
            print(f"   Response: {output}")
            return False
    else:
        print("❌ Request failed")
        print(f"   Error: {error}")
        return False

def wait_for_completion_and_analyze(job_id, test_name):
    """Wait for job completion and analyze results."""
    print(f"⏳ Waiting for {test_name} job completion...")
    
    max_wait = 30  # 30 seconds max wait
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        success, output, error = run_curl_command(f"curl -s http://localhost:8000/api/status/{job_id}")
        
        if success and output:
            try:
                data = json.loads(output)
                status = data.get('status', 'unknown')
                progress = data.get('progress', 0)
                
                print(f"   Status: {status}, Progress: {progress}%")
                
                if status == 'completed':
                    print(f"✅ {test_name} job completed!")
                    return analyze_generated_files(job_id, test_name)
                elif status == 'failed':
                    print(f"❌ {test_name} job failed!")
                    return False
                    
            except json.JSONDecodeError:
                print("   Error parsing status response")
                
        time.sleep(2)
    
    print(f"⏰ Timeout waiting for {test_name} job completion")
    return False

def analyze_generated_files(job_id, test_name):
    """Analyze the generated files."""
    print(f"🔍 Analyzing generated files for {test_name}...")
    
    success, output, error = run_curl_command(f"curl -s http://localhost:8000/api/download/{job_id}")
    
    if success and output:
        try:
            data = json.loads(output)
            files = data.get('files', [])
            
            print(f"   Generated {len(files)} files")
            
            # Analyze file types
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
                    if python_files:
                        sample_content = python_files[0].get('content', '')[:200]
                        print(f"   Sample content: {sample_content}...")
                    return True
                else:
                    print("❌ FAILED: Python request did not generate Python code!")
                    if react_files:
                        print("   ❌ Generated React code instead!")
                    return False
            else:
                print("⚠️  Unknown test type")
                return True
                
        except json.JSONDecodeError:
            print("❌ Error parsing download response")
            return False
    else:
        print("❌ Failed to download files")
        return False

def main():
    """Run the complete test."""
    print("🚀 REAL FUNCTIONALITY VALIDATION TEST")
    print("=" * 60)
    print("Testing if the system ACTUALLY works in practice!")
    print("=" * 60)
    
    # Test 1: Server Health
    if not test_server_health():
        print("\n❌ CRITICAL FAILURE: Server is not running!")
        return False
    
    # Test 2: Python Speech Recognition (CRITICAL TEST)
    python_success = test_python_generation()
    
    # Final Results
    print("\n" + "=" * 60)
    print("🎯 FINAL VALIDATION RESULTS")
    print("=" * 60)
    
    if python_success:
        print("🎉 SUCCESS: Python speech recognition test passed!")
        print("✅ The critical fix is working!")
        return True
    else:
        print("❌ CRITICAL FAILURE: Python speech recognition test failed!")
        print("❌ The system is still generating React for Python requests!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)