#!/usr/bin/env python3
"""
Dual Deployment Validation Script
Tests both Vercel and Hugging Face deployment configurations
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

def print_status(message: str, status: str = "INFO"):
    """Print colored status message"""
    colors = {
        "INFO": "\033[0;34m",
        "SUCCESS": "\033[0;32m", 
        "WARNING": "\033[1;33m",
        "ERROR": "\033[0;31m"
    }
    reset = "\033[0m"
    color = colors.get(status, colors["INFO"])
    print(f"{color}[{status}]{reset} {message}")

def validate_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_status(f"✅ {filepath} exists", "SUCCESS")
        return True
    else:
        print_status(f"❌ {filepath} missing", "ERROR")
        return False

def validate_json_file(filepath: str) -> bool:
    """Validate JSON file format"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        print_status(f"✅ {filepath} is valid JSON", "SUCCESS")
        return True
    except json.JSONDecodeError as e:
        print_status(f"❌ {filepath} invalid JSON: {e}", "ERROR")
        return False
    except FileNotFoundError:
        print_status(f"❌ {filepath} not found", "ERROR")
        return False

def validate_python_syntax(filepath: str) -> bool:
    """Validate Python file syntax"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", filepath],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_status(f"✅ {filepath} syntax valid", "SUCCESS")
            return True
        else:
            print_status(f"❌ {filepath} syntax error: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        print_status(f"❌ Error checking {filepath}: {e}", "ERROR")
        return False

def validate_requirements() -> bool:
    """Validate requirements.txt has necessary dependencies"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "gradio",
        "pydantic",
        "python-multipart"
    ]
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read().lower()
        
        missing = []
        for package in required_packages:
            if package not in content:
                missing.append(package)
        
        if missing:
            print_status(f"❌ Missing packages in requirements.txt: {', '.join(missing)}", "ERROR")
            return False
        else:
            print_status("✅ All required packages found in requirements.txt", "SUCCESS")
            return True
            
    except FileNotFoundError:
        print_status("❌ requirements.txt not found", "ERROR")
        return False

def validate_vercel_config() -> bool:
    """Validate Vercel configuration"""
    print_status("Validating Vercel deployment configuration...", "INFO")
    
    checks = []
    
    # Check vercel.json exists and is valid
    checks.append(validate_file_exists("vercel.json"))
    checks.append(validate_json_file("vercel.json"))
    
    # Check API files
    checks.append(validate_file_exists("api/index.py"))
    checks.append(validate_file_exists("api/vercel_app.py"))
    checks.append(validate_python_syntax("api/index.py"))
    checks.append(validate_python_syntax("api/vercel_app.py"))
    
    # Check vercel.json configuration
    try:
        with open("vercel.json", "r") as f:
            config = json.load(f)
        
        # Check required sections
        if "routes" in config:
            print_status("✅ Vercel routes configured", "SUCCESS")
            checks.append(True)
        else:
            print_status("❌ No routes in vercel.json", "ERROR")
            checks.append(False)
        
        if "env" in config:
            env_vars = config["env"]
            required_env = ["OPENAI_API_KEY", "JWT_SECRET_KEY"]
            missing_env = [var for var in required_env if var not in env_vars]
            if missing_env:
                print_status(f"⚠️  Missing env vars in vercel.json: {', '.join(missing_env)}", "WARNING")
            else:
                print_status("✅ Environment variables configured", "SUCCESS")
            checks.append(True)
        
        if "builds" in config:
            print_status("✅ Vercel build configuration found", "SUCCESS")
            checks.append(True)
        else:
            print_status("⚠️  No builds section in vercel.json", "WARNING")
            checks.append(True)  # Not critical
            
    except Exception as e:
        print_status(f"❌ Error validating vercel.json: {e}", "ERROR")
        checks.append(False)
    
    return all(checks)

def validate_huggingface_config() -> bool:
    """Validate Hugging Face deployment configuration"""
    print_status("Validating Hugging Face deployment configuration...", "INFO")
    
    checks = []
    
    # Check app.py exists and is valid
    checks.append(validate_file_exists("app.py"))
    checks.append(validate_python_syntax("app.py"))
    
    # Check Dockerfile
    checks.append(validate_file_exists("deployment/docker/Dockerfile"))
    
    # Check if app.py imports gradio
    try:
        with open("app.py", "r") as f:
            content = f.read()
        
        if "gradio" in content:
            print_status("✅ app.py imports Gradio", "SUCCESS")
            checks.append(True)
        else:
            print_status("❌ app.py does not import Gradio", "ERROR")
            checks.append(False)
            
        if "def main" in content:
            print_status("✅ app.py has main function", "SUCCESS")
            checks.append(True)
        else:
            print_status("❌ app.py missing main function", "ERROR")
            checks.append(False)
            
    except FileNotFoundError:
        print_status("❌ app.py not found", "ERROR")
        checks.append(False)
        checks.append(False)
    
    # Check requirements.txt includes gradio
    try:
        with open("requirements.txt", "r") as f:
            content = f.read().lower()
        
        if "gradio" in content:
            print_status("✅ Gradio in requirements.txt", "SUCCESS")
            checks.append(True)
        else:
            print_status("❌ Gradio missing from requirements.txt", "ERROR")
            checks.append(False)
            
    except FileNotFoundError:
        checks.append(False)
    
    return all(checks)

def validate_common_files() -> bool:
    """Validate common files required by both deployments"""
    print_status("Validating common deployment files...", "INFO")
    
    checks = []
    
    # Core files
    core_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        ".gitignore"
    ]
    
    for file in core_files:
        checks.append(validate_file_exists(file))
    
    # Python files
    python_files = ["main.py"]
    for file in python_files:
        if os.path.exists(file):
            checks.append(validate_python_syntax(file))
    
    # Requirements validation
    checks.append(validate_requirements())
    
    # Check backend directory structure
    backend_dirs = [
        "backend",
        "backend/core",
        "backend/agents",
        "config"
    ]
    
    for dir_path in backend_dirs:
        if os.path.exists(dir_path):
            print_status(f"✅ {dir_path} directory exists", "SUCCESS")
            checks.append(True)
        else:
            print_status(f"⚠️  {dir_path} directory missing", "WARNING")
            # Not critical for basic functionality
    
    return all(checks)

def validate_environment_template() -> bool:
    """Validate .env.example has all necessary variables"""
    print_status("Validating environment template...", "INFO")
    
    try:
        with open(".env.example", "r") as f:
            content = f.read()
        
        required_vars = [
            "OPENAI_API_KEY",
            "JWT_SECRET_KEY",
            "HF_TOKEN"
        ]
        
        missing = []
        for var in required_vars:
            if var not in content:
                missing.append(var)
        
        if missing:
            print_status(f"❌ Missing vars in .env.example: {', '.join(missing)}", "ERROR")
            return False
        else:
            print_status("✅ All required environment variables in template", "SUCCESS")
            return True
            
    except FileNotFoundError:
        print_status("❌ .env.example not found", "ERROR")
        return False

def run_comprehensive_validation() -> Dict[str, bool]:
    """Run all validation checks"""
    print_status("🚀 Starting Dual Deployment Validation", "INFO")
    print("=" * 60)
    
    results = {}
    
    # Common files validation
    print_status("📁 COMMON FILES VALIDATION", "INFO")
    results["common"] = validate_common_files()
    print()
    
    # Environment template validation
    print_status("🔧 ENVIRONMENT TEMPLATE VALIDATION", "INFO")
    results["environment"] = validate_environment_template()
    print()
    
    # Vercel validation
    print_status("🔷 VERCEL DEPLOYMENT VALIDATION", "INFO")
    results["vercel"] = validate_vercel_config()
    print()
    
    # Hugging Face validation  
    print_status("🤗 HUGGING FACE DEPLOYMENT VALIDATION", "INFO")
    results["huggingface"] = validate_huggingface_config()
    print()
    
    return results

def print_summary(results: Dict[str, bool]):
    """Print validation summary"""
    print("=" * 60)
    print_status("📊 VALIDATION SUMMARY", "INFO")
    print("=" * 60)
    
    all_passed = True
    
    for category, passed in results.items():
        status = "SUCCESS" if passed else "ERROR"
        emoji = "✅" if passed else "❌"
        print_status(f"{emoji} {category.upper()}: {'PASSED' if passed else 'FAILED'}", status)
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print_status("🎉 ALL VALIDATIONS PASSED! Both deployments are ready.", "SUCCESS")
        print_status("🔗 You can now deploy to both Vercel and Hugging Face Spaces", "SUCCESS")
    else:
        print_status("⚠️  Some validations failed. Please fix the issues above.", "WARNING")
    
    print("\n" + "=" * 60)
    print_status("📋 NEXT STEPS", "INFO")
    print("=" * 60)
    
    if results.get("vercel", False):
        print("🔷 Vercel Deployment:")
        print("   1. Set environment variables in Vercel dashboard")
        print("   2. Run: vercel --prod")
        print("   3. Or use: ./deploy-vercel.sh")
        print()
    
    if results.get("huggingface", False):
        print("🤗 Hugging Face Deployment:")
        print("   1. Set HF_TOKEN environment variable")
        print("   2. Run: ./deploy-hf.sh")
        print("   3. Set OPENAI_API_KEY in Space settings")
        print()
    
    return all_passed

def main():
    """Main validation function"""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        results = run_comprehensive_validation()
        success = print_summary(results)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print_status("Validation interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Validation failed with error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()