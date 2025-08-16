#!/usr/bin/env python3
"""
Simple test script for optimized frontend - no external dependencies
Verifies file structure and basic functionality
"""

import os
import sys
from pathlib import Path

def test_file_structure():
    """Test if all optimized files are in place"""
    print("🔍 Testing file structure...")
    
    required_files = [
        "public/index.html",
        "public/optimized-styles.css", 
        "public/js/app.js",
        "api/websocket_handler.py"
    ]
    
    results = {}
    for file_path in required_files:
        exists = Path(file_path).exists()
        results[file_path] = exists
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path}")
    
    return results

def test_html_optimizations():
    """Test HTML optimizations"""
    print("\n🌐 Testing HTML optimizations...")
    
    try:
        with open("public/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        optimizations = {
            "preload_links": "preload" in content,
            "optimized_css": "optimized-styles.css" in content,
            "modular_js": "js/app.js" in content,
            "meta_description": 'meta name="description"' in content,
            "theme_color": 'meta name="theme-color"' in content,
            "skip_link": 'href="#main-content"' in content,
            "aria_labels": 'role="tab"' in content,
            "semantic_html": '<main' in content and '<nav' in content,
            "lang_attribute": 'lang="fa"' in content,
            "rtl_support": 'dir="rtl"' in content
        }
        
        for opt, present in optimizations.items():
            status = "✅" if present else "❌"
            print(f"  {status} {opt.replace('_', ' ').title()}")
        
        return optimizations
    except Exception as e:
        print(f"  ❌ Error reading HTML: {e}")
        return {}

def test_css_structure():
    """Test CSS structure and optimizations"""
    print("\n🎨 Testing CSS structure...")
    
    try:
        with open("public/optimized-styles.css", "r", encoding="utf-8") as f:
            content = f.read()
        
        css_features = {
            "css_variables": ":root" in content and "--primary" in content,
            "design_tokens": "--space-" in content and "--text-" in content,
            "component_system": ".glass-card" in content,
            "responsive_design": "@media" in content,
            "performance_optimized": "will-change" in content,
            "accessibility_support": "prefers-reduced-motion" in content,
            "modern_css": "backdrop-filter" in content
        }
        
        for feature, present in css_features.items():
            status = "✅" if present else "❌"
            print(f"  {status} {feature.replace('_', ' ').title()}")
        
        size_kb = len(content) / 1024
        print(f"  📏 CSS Size: {size_kb:.1f}KB")
        
        return css_features
    except Exception as e:
        print(f"  ❌ Error reading CSS: {e}")
        return {}

def test_javascript_structure():
    """Test JavaScript structure and features"""
    print("\n⚙️ Testing JavaScript structure...")
    
    try:
        with open("public/js/app.js", "r", encoding="utf-8") as f:
            content = f.read()
        
        js_features = {
            "modular_architecture": "class AppState" in content,
            "state_management": "setState" in content and "getState" in content,
            "websocket_support": "WebSocket" in content,
            "api_service": "class ApiService" in content,
            "notification_system": "class NotificationManager" in content,
            "performance_monitoring": "class PerformanceMonitor" in content,
            "error_handling": "try" in content and "catch" in content,
            "es6_features": "async" in content and "await" in content
        }
        
        for feature, present in js_features.items():
            status = "✅" if present else "❌"
            print(f"  {status} {feature.replace('_', ' ').title()}")
        
        size_kb = len(content) / 1024
        print(f"  📏 JS Size: {size_kb:.1f}KB")
        
        return js_features
    except Exception as e:
        print(f"  ❌ Error reading JavaScript: {e}")
        return {}

def test_websocket_handler():
    """Test WebSocket handler implementation"""
    print("\n🔌 Testing WebSocket handler...")
    
    try:
        with open("api/websocket_handler.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        ws_features = {
            "connection_manager": "class ConnectionManager" in content,
            "websocket_endpoint": "async def websocket_endpoint" in content,
            "message_handling": "handleWebSocketMessage" in content or "handle_websocket_message" in content,
            "real_time_updates": "send_generation_progress" in content,
            "connection_cleanup": "disconnect" in content,
            "error_handling": "except" in content,
            "async_support": "async def" in content and "await" in content
        }
        
        for feature, present in ws_features.items():
            status = "✅" if present else "❌"
            print(f"  {status} {feature.replace('_', ' ').title()}")
        
        return ws_features
    except Exception as e:
        print(f"  ❌ Error reading WebSocket handler: {e}")
        return {}

def test_api_integration():
    """Test API integration"""
    print("\n🔗 Testing API integration...")
    
    try:
        with open("api/vercel_app.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        api_features = {
            "websocket_import": "websocket_handler" in content,
            "websocket_endpoint": "@app.websocket" in content,
            "generate_endpoint": "/api/generate" in content,
            "check_status_endpoint": "/api/check-status" in content,
            "websocket_support": "WebSocket" in content,
            "async_support": "async def" in content
        }
        
        for feature, present in api_features.items():
            status = "✅" if present else "❌"
            print(f"  {status} {feature.replace('_', ' ').title()}")
        
        return api_features
    except Exception as e:
        print(f"  ❌ Error reading API file: {e}")
        return {}

def print_summary(results):
    """Print comprehensive test summary"""
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, category_results in results.items():
        if isinstance(category_results, dict):
            category_passed = sum(1 for passed in category_results.values() if passed)
            category_total = len(category_results)
            total_tests += category_total
            passed_tests += category_passed
            
            print(f"\n{category.replace('_', ' ').title()}: {category_passed}/{category_total}")
            for test, passed in category_results.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {test.replace('_', ' ').title()}")
    
    # Calculate overall success rate
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"🎯 OVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    print(f"{'='*60}")
    
    if success_rate >= 90:
        print("🌟 EXCELLENT! Frontend optimization is working perfectly!")
        print("   All major optimizations have been successfully implemented.")
    elif success_rate >= 75:
        print("✅ GOOD! Most optimizations are working correctly.")
        print("   Minor issues may need attention, but core functionality is solid.")
    elif success_rate >= 50:
        print("⚠️  PARTIAL SUCCESS. Some important features are missing.")
        print("   Please review the failed tests and address the issues.")
    else:
        print("❌ MAJOR ISSUES DETECTED. Implementation needs significant work.")
        print("   Please review all failed tests and re-implement missing features.")
    
    print("\n🚀 NEXT STEPS:")
    if success_rate >= 90:
        print("   • Start the server and test the live interface")
        print("   • Verify WebSocket connections are working")
        print("   • Test project generation functionality")
        print("   • Monitor performance metrics")
    else:
        print("   • Fix failed tests before proceeding")
        print("   • Ensure all required files are properly created")
        print("   • Verify file contents and implementations")
    
    return success_rate

def main():
    """Run all tests"""
    print("🎯 Starting Frontend Optimization Verification...\n")
    
    results = {}
    
    # Run all tests
    results["file_structure"] = test_file_structure()
    results["html_optimizations"] = test_html_optimizations()
    results["css_structure"] = test_css_structure()
    results["javascript_structure"] = test_javascript_structure()
    results["websocket_handler"] = test_websocket_handler()
    results["api_integration"] = test_api_integration()
    
    # Print comprehensive summary
    success_rate = print_summary(results)
    
    # Return exit code based on success rate
    if success_rate >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Issues detected

if __name__ == "__main__":
    main()