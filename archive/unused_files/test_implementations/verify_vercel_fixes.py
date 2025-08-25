#!/usr/bin/env python3
"""
Vercel Deployment Fixes Verification Script
This script verifies that all the critical fixes for Vercel deployment are in place.
"""

import os
import sys
import json
import re
from pathlib import Path

def print_status(message, status="INFO"):
    """Print a colored status message"""
    colors = {
        "SUCCESS": "\033[92m",
        "ERROR": "\033[91m", 
        "WARNING": "\033[93m",
        "INFO": "\033[94m"
    }
    color = colors.get(status, "\033[0m")
    reset = "\033[0m"
    print(f"{color}[{status}]{reset} {message}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_status(f"✅ {description} found: {filepath}", "SUCCESS")
        return True
    else:
        print_status(f"❌ {description} missing: {filepath}", "ERROR")
        return False

def check_next_config():
    """Check next.config.js for the fixes"""
    print_status("Checking next.config.js...", "INFO")
    
    if not check_file_exists("next.config.js", "next.config.js"):
        return False
    
    with open("next.config.js", "r") as f:
        content = f.read()
    
    issues = []
    
    # Check for undefined destination
    if "undefined" in content:
        issues.append("Contains 'undefined' in destination")
    
    # Check for deprecated experimental.appDir
    if "experimental" in content and "appDir" in content:
        issues.append("Contains deprecated experimental.appDir")
    
    # Check for proper destination handling
    if "destination.*undefined" in content:
        issues.append("Destination handling needs improvement")
    
    # Check for proper fallback
    if "http://localhost:8000/api/:path*" not in content:
        issues.append("Missing proper fallback destination")
    
    if issues:
        for issue in issues:
            print_status(f"❌ {issue}", "ERROR")
        return False
    else:
        print_status("✅ next.config.js is properly configured", "SUCCESS")
        return True

def check_vercel_config():
    """Check vercel.json for the fixes"""
    print_status("Checking vercel.json...", "INFO")
    
    if not check_file_exists("vercel.json", "vercel.json"):
        return False
    
    try:
        with open("vercel.json", "r") as f:
            config = json.load(f)
        
        issues = []
        
        # Check for NODE_ENV in env section
        if "env" not in config:
            issues.append("Missing 'env' section")
        elif "NODE_ENV" not in config["env"]:
            issues.append("Missing NODE_ENV in env section")
        elif config["env"]["NODE_ENV"] != "production":
            issues.append("NODE_ENV should be 'production'")
        
        # Check for proper builds configuration
        if "builds" not in config:
            issues.append("Missing 'builds' section")
        
        # Check for functions configuration (optional in modern Vercel)
        # Functions are now configured in individual files
        
        if issues:
            for issue in issues:
                print_status(f"❌ {issue}", "ERROR")
            return False
        else:
            print_status("✅ vercel.json is properly configured", "SUCCESS")
            return True
            
    except json.JSONDecodeError as e:
        print_status(f"❌ Invalid JSON in vercel.json: {e}", "ERROR")
        return False

def check_environment_files():
    """Check environment files"""
    print_status("Checking environment files...", "INFO")
    
    success = True
    
    # Check .env.local
    if check_file_exists(".env.local", ".env.local"):
        with open(".env.local", "r") as f:
            content = f.read()
            if "NEXT_PUBLIC_API_URL" not in content:
                print_status("❌ .env.local missing NEXT_PUBLIC_API_URL", "ERROR")
                success = False
            if "NODE_ENV" not in content:
                print_status("❌ .env.local missing NODE_ENV", "ERROR")
                success = False
    else:
        success = False
    
    # Check .env.production
    if check_file_exists(".env.production", ".env.production"):
        with open(".env.production", "r") as f:
            content = f.read()
            if "NEXT_PUBLIC_API_URL" not in content:
                print_status("❌ .env.production missing NEXT_PUBLIC_API_URL", "ERROR")
                success = False
            if "NODE_ENV" not in content:
                print_status("❌ .env.production missing NODE_ENV", "ERROR")
                success = False
    else:
        success = False
    
    if success:
        print_status("✅ Environment files are properly configured", "SUCCESS")
    
    return success

def check_package_json():
    """Check package.json for Next.js version and scripts"""
    print_status("Checking package.json...", "INFO")
    
    if not check_file_exists("package.json", "package.json"):
        return False
    
    try:
        with open("package.json", "r") as f:
            config = json.load(f)
        
        issues = []
        
        # Check Next.js version
        if "dependencies" not in config:
            issues.append("Missing dependencies section")
        elif "next" not in config["dependencies"]:
            issues.append("Missing Next.js dependency")
        else:
            next_version = config["dependencies"]["next"]
            print_status(f"✅ Next.js version: {next_version}", "SUCCESS")
        
        # Check for build script
        if "scripts" not in config:
            issues.append("Missing scripts section")
        elif "build" not in config["scripts"]:
            issues.append("Missing build script")
        
        if issues:
            for issue in issues:
                print_status(f"❌ {issue}", "ERROR")
            return False
        else:
            print_status("✅ package.json is properly configured", "SUCCESS")
            return True
            
    except json.JSONDecodeError as e:
        print_status(f"❌ Invalid JSON in package.json: {e}", "ERROR")
        return False

def check_project_structure():
    """Check overall project structure"""
    print_status("Checking project structure...", "INFO")
    
    required_dirs = ["api", "frontend"]
    required_files = ["requirements.txt", "runtime.txt"]
    
    success = True
    
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print_status(f"✅ Directory found: {dir_name}", "SUCCESS")
        else:
            print_status(f"❌ Directory missing: {dir_name}", "ERROR")
            success = False
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print_status(f"✅ File found: {file_name}", "SUCCESS")
        else:
            print_status(f"⚠️  File missing: {file_name}", "WARNING")
    
    return success

def main():
    """Main verification function"""
    print_status("🔍 Starting Vercel Deployment Fixes Verification", "INFO")
    print_status("=" * 50, "INFO")
    
    checks = [
        ("Project Structure", check_project_structure),
        ("package.json", check_package_json),
        ("next.config.js", check_next_config),
        ("vercel.json", check_vercel_config),
        ("Environment Files", check_environment_files),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print_status(f"\n--- {check_name} ---", "INFO")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_status(f"❌ Error checking {check_name}: {e}", "ERROR")
            results.append((check_name, False))
    
    # Summary
    print_status("\n" + "=" * 50, "INFO")
    print_status("VERIFICATION SUMMARY", "INFO")
    print_status("=" * 50, "INFO")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print_status(f"{check_name}: {status}", "SUCCESS" if result else "ERROR")
        if result:
            passed += 1
    
    print_status(f"\nResults: {passed}/{total} checks passed", "INFO")
    
    if passed == total:
        print_status("🎉 All checks passed! Your project is ready for Vercel deployment.", "SUCCESS")
        print_status("\nNext steps:", "INFO")
        print_status("1. Set environment variables in Vercel dashboard", "INFO")
        print_status("2. Deploy using: ./deploy_vercel_fixes.sh", "INFO")
        print_status("3. Test your deployment endpoints", "INFO")
        return 0
    else:
        print_status("⚠️  Some checks failed. Please fix the issues before deploying.", "WARNING")
        print_status("\nCommon fixes:", "INFO")
        print_status("- Run: ./deploy_vercel_fixes.sh to apply fixes", "INFO")
        print_status("- Check the error messages above for specific issues", "INFO")
        return 1

if __name__ == "__main__":
    sys.exit(main())