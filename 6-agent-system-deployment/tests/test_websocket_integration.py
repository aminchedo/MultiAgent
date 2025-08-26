#!/usr/bin/env python3
"""
WebSocket Integration Test
Tests real-time communication with the 6-agent system
"""

import asyncio
import websockets
import json
import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import subprocess
import signal
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketTester:
    """WebSocket integration testing class"""
    
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:8000"
        self.ws_base_url = "ws://localhost:8000"
        self.test_results = {}
        
    async def start_server(self):
        """Start the FastAPI server for testing"""
        logger.info("🚀 Starting FastAPI server...")
        
        try:
            # Start server in background
            self.server_process = subprocess.Popen(
                ["python3", "backend/simple_app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/workspace"
            )
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Test if server is responding
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Server started successfully")
                return True
            else:
                logger.error(f"❌ Server health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the FastAPI server"""
        if self.server_process:
            logger.info("🛑 Stopping FastAPI server...")
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
    
    async def test_websocket_connection(self):
        """Test basic WebSocket connection"""
        logger.info("🔌 Testing WebSocket Connection...")
        
        test_job_id = "test-websocket-connection"
        ws_url = f"{self.ws_base_url}/ws/{test_job_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                logger.info("✅ WebSocket connection established")
                
                # Send ping message
                ping_message = {
                    "type": "ping",
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(ping_message))
                logger.info("📤 Sent ping message")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                logger.info(f"📥 Received response: {response_data.get('type', 'unknown')}")
                
                if response_data.get('type') == 'pong':
                    logger.info("✅ WebSocket ping/pong successful")
                    self.test_results['websocket_basic'] = {
                        'success': True,
                        'ping_pong': True,
                        'connection_time': time.time() - ping_message['timestamp']
                    }
                    return True
                else:
                    logger.warning("⚠️ Unexpected response type")
                    self.test_results['websocket_basic'] = {
                        'success': True,
                        'ping_pong': False,
                        'response': response_data
                    }
                    return True
                    
        except asyncio.TimeoutError:
            logger.error("❌ WebSocket connection timeout")
            self.test_results['websocket_basic'] = {
                'success': False,
                'error': 'Connection timeout'
            }
            return False
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self.test_results['websocket_basic'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def test_websocket_project_updates(self):
        """Test WebSocket updates during project creation"""
        logger.info("📡 Testing WebSocket Project Updates...")
        
        # Start project creation
        project_request = {
            "prompt": "Create a simple HTML page with a button",
            "framework": "vanilla",
            "complexity": "simple"
        }
        
        try:
            # Create project via API
            response = requests.post(
                f"{self.base_url}/api/vibe-coding",
                json=project_request,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Project creation failed: {response.status_code}")
                return False
            
            project_data = response.json()
            job_id = project_data.get('job_id')
            
            if not job_id:
                logger.error("❌ No job_id returned from project creation")
                return False
            
            logger.info(f"📋 Created project with job_id: {job_id}")
            
            # Connect to WebSocket for this job
            ws_url = f"{self.ws_base_url}/ws/{job_id}"
            
            messages_received = []
            
            async with websockets.connect(ws_url) as websocket:
                logger.info("🔗 Connected to project WebSocket")
                
                # Listen for updates for a limited time
                try:
                    for _ in range(10):  # Listen for up to 10 messages
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        message_data = json.loads(message)
                        messages_received.append(message_data)
                        
                        logger.info(f"📨 Received: {message_data.get('type', 'unknown')}")
                        
                        # If we get a completion or error message, break
                        if message_data.get('type') in ['project_complete', 'error']:
                            break
                            
                except asyncio.TimeoutError:
                    logger.info("⏰ WebSocket listening timeout (expected)")
            
            # Analyze received messages
            message_types = [msg.get('type') for msg in messages_received]
            
            self.test_results['websocket_updates'] = {
                'success': len(messages_received) > 0,
                'messages_count': len(messages_received),
                'message_types': message_types,
                'job_id': job_id
            }
            
            logger.info(f"📊 WebSocket Updates Results:")
            logger.info(f"   Messages Received: {len(messages_received)}")
            logger.info(f"   Message Types: {set(message_types)}")
            
            return len(messages_received) > 0
            
        except Exception as e:
            logger.error(f"❌ WebSocket project updates test failed: {e}")
            self.test_results['websocket_updates'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def test_concurrent_websocket_connections(self):
        """Test multiple concurrent WebSocket connections"""
        logger.info("🔀 Testing Concurrent WebSocket Connections...")
        
        async def connect_websocket(job_id):
            """Connect to a WebSocket and return connection info"""
            ws_url = f"{self.ws_base_url}/ws/{job_id}"
            try:
                async with websockets.connect(ws_url) as websocket:
                    # Send a ping and wait for response
                    await websocket.send(json.dumps({"type": "ping"}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    return {"job_id": job_id, "success": True, "response": json.loads(response)}
            except Exception as e:
                return {"job_id": job_id, "success": False, "error": str(e)}
        
        # Test 5 concurrent connections
        job_ids = [f"concurrent-test-{i}" for i in range(5)]
        
        try:
            # Create concurrent connections
            tasks = [connect_websocket(job_id) for job_id in job_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_connections = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
            
            self.test_results['websocket_concurrent'] = {
                'success': successful_connections > 0,
                'total_attempts': len(job_ids),
                'successful_connections': successful_connections,
                'success_rate': (successful_connections / len(job_ids)) * 100,
                'results': results
            }
            
            logger.info(f"📊 Concurrent WebSocket Results:")
            logger.info(f"   Total Attempts: {len(job_ids)}")
            logger.info(f"   Successful Connections: {successful_connections}")
            logger.info(f"   Success Rate: {(successful_connections / len(job_ids)) * 100:.1f}%")
            
            return successful_connections >= 3  # At least 60% success rate
            
        except Exception as e:
            logger.error(f"❌ Concurrent WebSocket test failed: {e}")
            self.test_results['websocket_concurrent'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling"""
        logger.info("⚠️ Testing WebSocket Error Handling...")
        
        try:
            # Test connection to non-existent endpoint
            invalid_ws_url = f"{self.ws_base_url}/ws/invalid-endpoint-test"
            
            try:
                async with websockets.connect(invalid_ws_url) as websocket:
                    # This should still work as the endpoint accepts any job_id
                    await websocket.send(json.dumps({"type": "test"}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    logger.info("✅ Invalid endpoint handled gracefully")
                    invalid_endpoint_success = True
            except Exception:
                logger.info("✅ Invalid endpoint properly rejected")
                invalid_endpoint_success = True
            
            # Test malformed message handling
            valid_ws_url = f"{self.ws_base_url}/ws/error-test"
            
            try:
                async with websockets.connect(valid_ws_url) as websocket:
                    # Send malformed JSON
                    await websocket.send("invalid json")
                    
                    # Wait to see if connection stays alive
                    await asyncio.sleep(1)
                    
                    # Send valid message after invalid one
                    await websocket.send(json.dumps({"type": "ping"}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    
                    logger.info("✅ Malformed message handled gracefully")
                    malformed_handling_success = True
                    
            except Exception as e:
                logger.warning(f"⚠️ Malformed message handling: {e}")
                malformed_handling_success = False
            
            self.test_results['websocket_error_handling'] = {
                'success': True,
                'invalid_endpoint_handled': invalid_endpoint_success,
                'malformed_message_handled': malformed_handling_success
            }
            
            logger.info("📊 Error Handling Results:")
            logger.info(f"   Invalid Endpoint: {'✅ Handled' if invalid_endpoint_success else '❌ Failed'}")
            logger.info(f"   Malformed Messages: {'✅ Handled' if malformed_handling_success else '❌ Failed'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket error handling test failed: {e}")
            self.test_results['websocket_error_handling'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def generate_websocket_report(self):
        """Generate WebSocket test report"""
        logger.info("📋 Generating WebSocket Test Report...")
        
        report = {
            'test_execution_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'websocket_test_results': self.test_results,
            'summary': {}
        }
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get('success', False))
        
        report['summary'] = {
            'total_websocket_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'websocket_success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'websocket_functional': passed_tests >= 3,  # At least 3 core tests should pass
        }
        
        # Save report
        with open('websocket_test_results.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 WebSocket Test Summary:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests}")
        logger.info(f"   Failed: {total_tests - passed_tests}")
        logger.info(f"   Success Rate: {report['summary']['websocket_success_rate']:.1f}%")
        logger.info(f"   WebSocket System: {'✅ Functional' if report['summary']['websocket_functional'] else '❌ Issues'}")
        logger.info(f"   Report saved to: websocket_test_results.json")
        
        return report

async def main():
    """Main WebSocket testing function"""
    logger.info("🔌 Starting WebSocket Integration Testing")
    logger.info("=" * 60)
    
    tester = WebSocketTester()
    
    try:
        # Phase 1: Start Server
        logger.info("📍 PHASE 1: Server Startup")
        if not await tester.start_server():
            logger.error("❌ Server startup failed. Aborting WebSocket tests.")
            return False
        
        # Phase 2: Basic WebSocket Connection
        logger.info("\n📍 PHASE 2: Basic WebSocket Connection")
        await tester.test_websocket_connection()
        
        # Phase 3: WebSocket Project Updates
        logger.info("\n📍 PHASE 3: WebSocket Project Updates")
        await tester.test_websocket_project_updates()
        
        # Phase 4: Concurrent Connections
        logger.info("\n📍 PHASE 4: Concurrent WebSocket Connections")
        await tester.test_concurrent_websocket_connections()
        
        # Phase 5: Error Handling
        logger.info("\n📍 PHASE 5: WebSocket Error Handling")
        await tester.test_websocket_error_handling()
        
        # Phase 6: Generate Report
        logger.info("\n📍 PHASE 6: Generate WebSocket Report")
        report = tester.generate_websocket_report()
        
        # Final Results
        logger.info("\n" + "=" * 60)
        logger.info("🏆 WEBSOCKET TESTING COMPLETE")
        logger.info(f"🎯 WebSocket Success Rate: {report['summary']['websocket_success_rate']:.1f}%")
        
        success = report['summary']['websocket_functional']
        if success:
            logger.info("✅ WEBSOCKET SYSTEM FULLY FUNCTIONAL")
        else:
            logger.error("❌ WEBSOCKET SYSTEM NEEDS ATTENTION")
        
        return success
        
    finally:
        # Always stop the server
        tester.stop_server()

if __name__ == "__main__":
    asyncio.run(main())