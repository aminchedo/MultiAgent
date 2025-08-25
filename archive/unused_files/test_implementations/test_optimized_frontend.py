#!/usr/bin/env python3
"""
Test script for optimized frontend functionality
Tests the new UI/UX improvements, performance optimizations, and WebSocket integration
"""

import asyncio
import json
import time
import aiohttp
import websockets
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrontendOptimizationTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws") + "/ws"
        self.session = None
        self.ws = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.ws:
            await self.ws.close()

    async def test_file_structure(self):
        """Test if all optimized files are in place"""
        logger.info("🔍 Testing file structure...")
        
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
            logger.info(f"  {status} {file_path}")
        
        return results

    async def test_static_files(self):
        """Test if static files are accessible"""
        logger.info("🌐 Testing static file accessibility...")
        
        test_urls = [
            f"{self.base_url}/",
            f"{self.base_url}/optimized-styles.css",
            f"{self.base_url}/js/app.js"
        ]
        
        results = {}
        for url in test_urls:
            try:
                async with self.session.get(url, timeout=10) as response:
                    results[url] = {
                        "status": response.status,
                        "content_type": response.headers.get("content-type"),
                        "size": len(await response.read())
                    }
                    status = "✅" if response.status == 200 else "❌"
                    logger.info(f"  {status} {url} ({response.status})")
            except Exception as e:
                results[url] = {"error": str(e)}
                logger.info(f"  ❌ {url} (Error: {e})")
        
        return results

    async def test_api_endpoints(self):
        """Test new API endpoints"""
        logger.info("🔗 Testing API endpoints...")
        
        # Test health endpoint
        try:
            async with self.session.get(f"{self.base_url}/api/health", timeout=10) as response:
                health_data = await response.json()
                logger.info(f"  ✅ Health endpoint: {health_data.get('status', 'unknown')}")
        except Exception as e:
            logger.info(f"  ❌ Health endpoint error: {e}")
        
        # Test check-status endpoint
        try:
            async with self.session.post(f"{self.base_url}/api/check-status", timeout=10) as response:
                if response.status == 200:
                    status_data = await response.json()
                    logger.info(f"  ✅ Check-status endpoint: {status_data.get('status', 'unknown')}")
                else:
                    logger.info(f"  ❌ Check-status endpoint: HTTP {response.status}")
        except Exception as e:
            logger.info(f"  ❌ Check-status endpoint error: {e}")

    async def test_websocket_connection(self):
        """Test WebSocket connectivity and real-time features"""
        logger.info("🔌 Testing WebSocket connection...")
        
        try:
            # Connect to WebSocket
            self.ws = await websockets.connect(self.ws_url, timeout=10)
            logger.info("  ✅ WebSocket connection established")
            
            # Test ping/pong
            await self.ws.send(json.dumps({"type": "ping"}))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get("type") == "connection_established":
                    logger.info("  ✅ WebSocket handshake successful")
                else:
                    logger.info(f"  ℹ️ Received: {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                logger.info("  ⚠️ No immediate response (may be normal)")
            
            # Test subscription
            await self.ws.send(json.dumps({
                "type": "subscribe_to_job",
                "job_id": "test-job"
            }))
            
            return True
            
        except Exception as e:
            logger.info(f"  ❌ WebSocket connection failed: {e}")
            return False

    async def test_project_generation(self):
        """Test project generation with real-time updates"""
        logger.info("🚀 Testing project generation...")
        
        if not self.ws:
            logger.info("  ❌ No WebSocket connection available")
            return False
        
        try:
            # Start project generation
            async with self.session.post(f"{self.base_url}/api/generate", timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"  ✅ Project generation completed: {result.get('status')}")
                    logger.info(f"  📁 Files generated: {len(result.get('files', []))}")
                    return True
                else:
                    logger.info(f"  ❌ Project generation failed: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.info(f"  ❌ Project generation error: {e}")
            return False

    async def test_performance_metrics(self):
        """Test performance improvements"""
        logger.info("⚡ Testing performance metrics...")
        
        # Test page load time
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/", timeout=10) as response:
                content = await response.read()
                load_time = (time.time() - start_time) * 1000  # Convert to ms
                
                logger.info(f"  ⚡ Page load time: {load_time:.2f}ms")
                logger.info(f"  📏 Page size: {len(content)} bytes")
                
                # Check for optimization indicators
                content_str = content.decode('utf-8')
                optimizations = {
                    "preload_links": "preload" in content_str,
                    "optimized_css": "optimized-styles.css" in content_str,
                    "modular_js": "js/app.js" in content_str,
                    "meta_description": 'meta name="description"' in content_str,
                    "theme_color": 'meta name="theme-color"' in content_str,
                }
                
                for opt, present in optimizations.items():
                    status = "✅" if present else "❌"
                    logger.info(f"  {status} {opt.replace('_', ' ').title()}")
                
                return {
                    "load_time": load_time,
                    "size": len(content),
                    "optimizations": optimizations
                }
        except Exception as e:
            logger.info(f"  ❌ Performance test error: {e}")
            return None

    async def test_accessibility_features(self):
        """Test accessibility improvements"""
        logger.info("♿ Testing accessibility features...")
        
        try:
            async with self.session.get(f"{self.base_url}/", timeout=10) as response:
                content = await response.read().decode('utf-8')
                
                accessibility_features = {
                    "skip_link": 'href="#main-content"' in content,
                    "aria_labels": 'role="tab"' in content,
                    "semantic_html": '<main' in content and '<nav' in content,
                    "lang_attribute": 'lang="fa"' in content,
                    "sr_only_class": 'class="sr-only"' in content
                }
                
                for feature, present in accessibility_features.items():
                    status = "✅" if present else "❌"
                    logger.info(f"  {status} {feature.replace('_', ' ').title()}")
                
                return accessibility_features
        except Exception as e:
            logger.info(f"  ❌ Accessibility test error: {e}")
            return None

    async def run_comprehensive_test(self):
        """Run all tests and provide summary"""
        logger.info("🎯 Starting comprehensive frontend optimization test...\n")
        
        results = {}
        
        # File structure test
        results["file_structure"] = await self.test_file_structure()
        print()
        
        # Static files test
        results["static_files"] = await self.test_static_files()
        print()
        
        # API endpoints test
        results["api_endpoints"] = await self.test_api_endpoints()
        print()
        
        # WebSocket test
        results["websocket"] = await self.test_websocket_connection()
        print()
        
        # Project generation test
        if results["websocket"]:
            results["project_generation"] = await self.test_project_generation()
        print()
        
        # Performance test
        results["performance"] = await self.test_performance_metrics()
        print()
        
        # Accessibility test
        results["accessibility"] = await self.test_accessibility_features()
        print()
        
        # Summary
        self.print_summary(results)
        
        return results

    def print_summary(self, results):
        """Print test summary"""
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 50)
        
        total_tests = 0
        passed_tests = 0
        
        # File structure summary
        file_results = results.get("file_structure", {})
        files_present = sum(1 for exists in file_results.values() if exists)
        total_files = len(file_results)
        total_tests += total_files
        passed_tests += files_present
        logger.info(f"📁 File Structure: {files_present}/{total_files} files present")
        
        # Static files summary
        static_results = results.get("static_files", {})
        static_success = sum(1 for result in static_results.values() 
                           if isinstance(result, dict) and result.get("status") == 200)
        total_static = len(static_results)
        total_tests += total_static
        passed_tests += static_success
        logger.info(f"🌐 Static Files: {static_success}/{total_static} accessible")
        
        # WebSocket summary
        ws_success = results.get("websocket", False)
        total_tests += 1
        passed_tests += int(ws_success)
        logger.info(f"🔌 WebSocket: {'✅ Connected' if ws_success else '❌ Failed'}")
        
        # Performance summary
        perf_results = results.get("performance")
        if perf_results:
            load_time = perf_results.get("load_time", 0)
            logger.info(f"⚡ Page Load: {load_time:.2f}ms")
            
            opts = perf_results.get("optimizations", {})
            opts_count = sum(1 for present in opts.values() if present)
            total_opts = len(opts)
            total_tests += total_opts
            passed_tests += opts_count
            logger.info(f"🎯 Optimizations: {opts_count}/{total_opts} implemented")
        
        # Accessibility summary
        a11y_results = results.get("accessibility")
        if a11y_results:
            a11y_count = sum(1 for present in a11y_results.values() if present)
            total_a11y = len(a11y_results)
            total_tests += total_a11y
            passed_tests += a11y_count
            logger.info(f"♿ Accessibility: {a11y_count}/{total_a11y} features present")
        
        # Overall score
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        logger.info(f"\n🎉 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 90:
            logger.info("🌟 Excellent! Frontend optimization is working great!")
        elif success_rate >= 75:
            logger.info("✅ Good! Most optimizations are working correctly.")
        elif success_rate >= 50:
            logger.info("⚠️ Partial success. Some issues need attention.")
        else:
            logger.info("❌ Major issues detected. Please review the implementation.")

async def main():
    """Main test function"""
    async with FrontendOptimizationTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())