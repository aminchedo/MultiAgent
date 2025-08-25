#!/usr/bin/env python3
"""
Complete End-to-End Integration Test for Vibe Coding Platform
This test validates that the real agents are working and generating actual projects.
"""

import asyncio
import json
import time
import zipfile
import os
from io import BytesIO
import requests

def test_backend_health():
    """Test that the backend is running and healthy."""
    print("🔍 Testing backend health...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_vibe_coding_api():
    """Test the vibe-coding API endpoint with real agent processing."""
    print("\n🚀 Testing vibe-coding API...")
    
    test_prompt = "Create a simple React todo app with TypeScript"
    
    try:
        # Submit vibe request
        response = requests.post(
            "http://localhost:8000/api/vibe-coding",
            json={"prompt": test_prompt, "project_type": "web"},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Vibe coding API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        data = response.json()
        
        if not data.get("success"):
            print(f"❌ Vibe coding request failed: {data}")
            return None
        
        job_id = data.get("job_id")
        print(f"✅ Vibe coding job started: {job_id}")
        print(f"   Message: {data.get('message')}")
        
        return job_id
        
    except Exception as e:
        print(f"❌ Vibe coding API test failed: {e}")
        return None

def monitor_job_progress(job_id, max_wait_time=300):
    """Monitor job progress and return final status."""
    print(f"\n👁️ Monitoring job progress: {job_id}")
    
    start_time = time.time()
    last_progress = -1
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"http://localhost:8000/api/status/{job_id}", timeout=5)
            
            if response.status_code == 200:
                status = response.json()
                
                if status.get("success"):
                    progress = status.get("progress", 0)
                    current_step = status.get("current_step", "Unknown")
                    job_status = status.get("status", "Unknown")
                    
                    # Only print progress updates when there's a change
                    if progress != last_progress:
                        print(f"   📊 Progress: {progress}% - {current_step}")
                        last_progress = progress
                        
                        # Show agent status if available
                        agents = status.get("agents", {})
                        if agents:
                            for agent_name, agent_data in agents.items():
                                agent_status = agent_data.get("status", "unknown")
                                agent_progress = agent_data.get("progress", 0)
                                print(f"     🤖 {agent_name}: {agent_status} ({agent_progress}%)")
                    
                    if job_status == "completed":
                        print(f"✅ Job completed successfully!")
                        print(f"   Files generated: {len(status.get('files', []))}")
                        return status
                    elif job_status == "failed":
                        print(f"❌ Job failed: {status.get('error_message', 'Unknown error')}")
                        return status
                
            time.sleep(3)  # Check every 3 seconds
            
        except Exception as e:
            print(f"⚠️  Status check error: {e}")
            time.sleep(5)
    
    print(f"⏰ Job monitoring timed out after {max_wait_time} seconds")
    return None

def test_project_download(job_id):
    """Test downloading the generated project."""
    print(f"\n💾 Testing project download for job: {job_id}")
    
    try:
        response = requests.get(f"http://localhost:8000/api/download/{job_id}", timeout=30)
        
        if response.status_code == 200:
            # Analyze the downloaded content
            content_length = len(response.content)
            print(f"✅ Download successful: {content_length} bytes")
            
            # Try to extract and analyze the ZIP
            try:
                with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    print(f"   📁 ZIP contains {len(file_list)} files:")
                    
                    for file_name in file_list[:10]:  # Show first 10 files
                        print(f"      - {file_name}")
                    
                    if len(file_list) > 10:
                        print(f"      ... and {len(file_list) - 10} more files")
                    
                    # Check for key project files
                    has_package_json = any("package.json" in f for f in file_list)
                    has_react_files = any(".tsx" in f or ".jsx" in f for f in file_list)
                    has_typescript = any(".ts" in f for f in file_list)
                    
                    print(f"\n   📋 Project Analysis:")
                    print(f"      React project: {'✅' if has_react_files else '❌'}")
                    print(f"      TypeScript: {'✅' if has_typescript else '❌'}")
                    print(f"      Package.json: {'✅' if has_package_json else '❌'}")
                    
                    # Sample a few files to check content quality
                    sample_files = [f for f in file_list if f.endswith(('.js', '.jsx', '.ts', '.tsx', '.json'))][:3]
                    
                    print(f"\n   🔍 Content Quality Check:")
                    for file_name in sample_files:
                        try:
                            with zip_ref.open(file_name) as file:
                                content = file.read().decode('utf-8')
                                if len(content) > 50 and 'TODO' not in content and 'placeholder' not in content.lower():
                                    print(f"      ✅ {file_name}: Contains functional code ({len(content)} chars)")
                                else:
                                    print(f"      ⚠️  {file_name}: May contain placeholder content ({len(content)} chars)")
                        except:
                            print(f"      ❓ {file_name}: Could not analyze content")
                    
                    return {
                        "success": True,
                        "file_count": len(file_list),
                        "has_react": has_react_files,
                        "has_typescript": has_typescript,
                        "has_package_json": has_package_json,
                        "files": file_list
                    }
                    
            except zipfile.BadZipFile:
                print(f"❌ Downloaded file is not a valid ZIP")
                return {"success": False, "error": "Invalid ZIP file"}
            
        else:
            print(f"❌ Download failed: {response.status_code}")
            print(f"Response: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Download test failed: {e}")
        return {"success": False, "error": str(e)}

def generate_test_report(results):
    """Generate a comprehensive test report."""
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE INTEGRATION TEST REPORT")
    print("="*60)
    
    # Backend Health
    print(f"\n🏥 Backend Health: {'✅ PASS' if results['backend_health'] else '❌ FAIL'}")
    
    # API Functionality
    print(f"🔌 API Functionality: {'✅ PASS' if results['job_id'] else '❌ FAIL'}")
    
    # Agent Processing
    if results['final_status']:
        status = results['final_status']['status']
        progress = results['final_status']['progress']
        print(f"🤖 Agent Processing: {'✅ PASS' if status == 'completed' else '❌ FAIL'} ({status}, {progress}%)")
    else:
        print(f"🤖 Agent Processing: ❌ FAIL (No final status)")
    
    # File Generation
    if results['download_result'] and results['download_result']['success']:
        file_count = results['download_result']['file_count']
        print(f"📁 File Generation: ✅ PASS ({file_count} files generated)")
        
        # Quality Checks
        dr = results['download_result']
        print(f"   React Components: {'✅' if dr['has_react'] else '❌'}")
        print(f"   TypeScript Support: {'✅' if dr['has_typescript'] else '❌'}")
        print(f"   Project Configuration: {'✅' if dr['has_package_json'] else '❌'}")
    else:
        print(f"📁 File Generation: ❌ FAIL")
    
    # Overall Assessment
    all_passed = (
        results['backend_health'] and 
        results['job_id'] and 
        results['final_status'] and 
        results['final_status']['status'] == 'completed' and
        results['download_result'] and 
        results['download_result']['success']
    )
    
    print(f"\n🎯 OVERALL ASSESSMENT: {'✅ PLATFORM FUNCTIONAL' if all_passed else '❌ ISSUES DETECTED'}")
    
    if all_passed:
        print("✨ The platform successfully generates real, functional projects!")
        print("✨ Ready for user testing and deployment.")
    else:
        print("⚠️  Platform has functionality issues that need to be addressed.")
        print("⚠️  Not ready for production use.")
    
    print("\n" + "="*60)
    
    return all_passed

def main():
    """Run the complete integration test suite."""
    print("🧪 STARTING COMPREHENSIVE VIBE CODING PLATFORM TEST")
    print("="*60)
    
    results = {
        'backend_health': False,
        'job_id': None,
        'final_status': None,
        'download_result': None
    }
    
    # Test 1: Backend Health
    results['backend_health'] = test_backend_health()
    if not results['backend_health']:
        print("❌ CRITICAL: Backend is not running. Cannot continue tests.")
        return False
    
    # Test 2: Vibe Coding API
    results['job_id'] = test_vibe_coding_api()
    if not results['job_id']:
        print("❌ CRITICAL: Vibe coding API failed. Cannot continue tests.")
        return False
    
    # Test 3: Monitor Job Progress
    results['final_status'] = monitor_job_progress(results['job_id'])
    if not results['final_status']:
        print("❌ CRITICAL: Job monitoring failed or timed out.")
        return False
    
    # Test 4: Download Generated Project
    if results['final_status']['status'] == 'completed':
        results['download_result'] = test_project_download(results['job_id'])
    
    # Generate Final Report
    success = generate_test_report(results)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        exit(1)