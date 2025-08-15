#!/usr/bin/env python3
"""
Simplified Deployment Validation Script
Tests file structure and configuration without external dependencies
"""

import os
import sys
import json
import py_compile
from pathlib import Path

class DeploymentValidator:
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {details}")
        
    def test_file_exists(self, file_path: str) -> bool:
        """Test if a file exists"""
        exists = Path(file_path).exists()
        self.log_test(f"File exists: {file_path}", exists, 
                     f"Found" if exists else f"Missing")
        return exists
        
    def test_directory_structure(self):
        """Test required directory structure"""
        print("\n🗂️  Testing Directory Structure...")
        
        required_dirs = [
            "static",
            "static/pages", 
            "static/assets",
            "api",
            "config",
            "frontend",
            "frontend/pages"
        ]
        
        for dir_path in required_dirs:
            exists = Path(dir_path).exists() and Path(dir_path).is_dir()
            self.log_test(f"Directory: {dir_path}", exists, 
                         "Found" if exists else "Missing")
            
    def test_required_files(self):
        """Test required files"""
        print("\n📄 Testing Required Files...")
        
        required_files = [
            "static/index.html",
            "static/pages/index.html", 
            "api/index.py",
            "api/vercel_app.py",
            "config/vercel_config.py",
            "vercel.json",
            "requirements-vercel.txt",
            "package.json"
        ]
        
        for file_path in required_files:
            self.test_file_exists(file_path)
            
    def test_vercel_config(self):
        """Test vercel.json configuration"""
        print("\n⚙️  Testing Vercel Configuration...")
        
        try:
            with open("vercel.json", "r") as f:
                config = json.load(f)
                
            required_keys = ["version", "routes", "functions"]
            has_all_keys = all(key in config for key in required_keys)
            
            self.log_test("vercel.json structure", has_all_keys, 
                         f"Keys: {list(config.keys())}")
            
            # Test functions section (modern Vercel config)
            functions = config.get("functions", {})
            has_python_function = any(
                func_config.get("runtime", "").startswith("python")
                for func_config in functions.values()
            )
            self.log_test("Python function config", has_python_function,
                         "Found Python runtime in functions")
            
            # Test routes
            routes = config.get("routes", [])
            has_routes = len(routes) > 0
            self.log_test("Routes configured", has_routes,
                         f"{len(routes)} routes found")
            
        except Exception as e:
            self.log_test("vercel.json parsing", False, f"Error: {str(e)}")
            
    def test_python_compilation(self):
        """Test Python file compilation"""
        print("\n🐍 Testing Python Files...")
        
        python_files = [
            "api/index.py",
            "api/vercel_app.py"
        ]
        
        # Only test files that exist
        for py_file in python_files:
            if Path(py_file).exists():
                try:
                    py_compile.compile(py_file, doraise=True)
                    self.log_test(f"Python compilation: {py_file}", True, 
                                 "Compiled successfully")
                except Exception as e:
                    self.log_test(f"Python compilation: {py_file}", False, 
                                 f"Error: {str(e)}")
            else:
                self.log_test(f"Python file: {py_file}", False, "File not found")
                
    def test_html_basic_structure(self):
        """Test HTML file basic structure"""
        print("\n🌐 Testing HTML Files...")
        
        html_files = ["static/index.html", "static/pages/index.html"]
        
        for html_file in html_files:
            if Path(html_file).exists():
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    has_doctype = content.strip().startswith('<!DOCTYPE html>')
                    has_html_tag = '<html' in content
                    has_head = '<head>' in content
                    has_body = '<body>' in content
                    has_title = '<title>' in content
                    
                    is_valid = all([has_doctype, has_html_tag, has_head, has_body, has_title])
                    
                    details = f"DOCTYPE: {has_doctype}, HTML: {has_html_tag}, HEAD: {has_head}, BODY: {has_body}, TITLE: {has_title}"
                    self.log_test(f"HTML structure: {html_file}", is_valid, details)
                    
                except Exception as e:
                    self.log_test(f"HTML parsing: {html_file}", False, f"Error: {str(e)}")
            else:
                self.log_test(f"HTML file: {html_file}", False, "File not found")
                
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Multi-Agent Code Generation System - Deployment Validation")
        print("=" * 70)
        
        self.test_directory_structure()
        self.test_required_files()
        self.test_vercel_config()
        self.test_python_compilation()
        self.test_html_basic_structure()
        
        self.print_summary()
        
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
                    
        print("\n🔧 RECOMMENDATIONS:")
        if failed_tests == 0:
            print("✅ All validation tests passed!")
            print("🚀 Deployment structure is ready for Vercel.")
            print("💡 Next steps:")
            print("   1. Run: vercel login")
            print("   2. Run: vercel --prod")
            print("   3. Test deployed endpoints")
        else:
            print("⚠️  Fix the failed tests before deploying.")
            print("📖 Check the VERCEL_DEPLOYMENT.md for troubleshooting.")
            
        return failed_tests == 0

def main():
    """Main validation function"""
    validator = DeploymentValidator()
    success = validator.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()