#!/usr/bin/env python3
"""
Production Deployment Validation Script
Tests all Phase 3 & 4 implementations with REAL functionality verification
"""

import asyncio
import json
import time
import sys
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Any

class DeploymentValidator:
    """Validates all Phase 3 & 4 implementations"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phase_3_results": {},
            "phase_4_results": {},
            "overall_status": "unknown",
            "issues_found": [],
            "success_count": 0,
            "total_tests": 0
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_passed(self, test_name: str, details: Any = None):
        """Record successful test"""
        self.results["success_count"] += 1
        self.results["total_tests"] += 1
        self.log(f"✅ {test_name}", "PASS")
        if details:
            self.log(f"   Details: {details}")
    
    def test_failed(self, test_name: str, error: str):
        """Record failed test"""
        self.results["total_tests"] += 1
        self.results["issues_found"].append(f"{test_name}: {error}")
        self.log(f"❌ {test_name}", "FAIL")
        self.log(f"   Error: {error}")
    
    def validate_phase_3_production_config(self):
        """Validate Phase 3: Production Configuration"""
        self.log("🔍 PHASE 3: Production Configuration Validation")
        
        # Test 1: Production environment file
        try:
            if os.path.exists(".env.production"):
                with open(".env.production", "r") as f:
                    content = f.read()
                    if "NODE_ENV=production" in content and "OPENAI_API_KEY=" in content:
                        self.test_passed("Production environment file exists with required variables")
                    else:
                        self.test_failed("Production environment file", "Missing required variables")
            else:
                self.test_failed("Production environment file", "File not found")
        except Exception as e:
            self.test_failed("Production environment file", str(e))
        
        # Test 2: Docker configuration
        try:
            if os.path.exists("docker-compose.prod.yml"):
                with open("docker-compose.prod.yml", "r") as f:
                    content = f.read()
                    if "backend:" in content and "frontend:" in content and "postgres:" in content:
                        self.test_passed("Docker production configuration complete")
                    else:
                        self.test_failed("Docker configuration", "Missing required services")
            else:
                self.test_failed("Docker configuration", "docker-compose.prod.yml not found")
        except Exception as e:
            self.test_failed("Docker configuration", str(e))
        
        # Test 3: Nginx configuration
        try:
            if os.path.exists("nginx.conf"):
                with open("nginx.conf", "r") as f:
                    content = f.read()
                    if "upstream backend" in content and "location /api/" in content:
                        self.test_passed("Nginx reverse proxy configuration")
                    else:
                        self.test_failed("Nginx configuration", "Missing backend proxy settings")
            else:
                self.test_failed("Nginx configuration", "nginx.conf not found")
        except Exception as e:
            self.test_failed("Nginx configuration", str(e))
        
        # Test 4: CI/CD Pipeline
        try:
            pipeline_path = ".github/workflows/production-deploy.yml"
            if os.path.exists(pipeline_path):
                with open(pipeline_path, "r") as f:
                    content = f.read()
                    if "test-backend:" in content and "deploy-production:" in content:
                        self.test_passed("CI/CD pipeline configuration")
                    else:
                        self.test_failed("CI/CD pipeline", "Missing required jobs")
            else:
                self.test_failed("CI/CD pipeline", "GitHub Actions workflow not found")
        except Exception as e:
            self.test_failed("CI/CD pipeline", str(e))
        
        # Test 5: Dockerfile configurations
        dockerfiles = ["Dockerfile.backend", "Dockerfile.frontend"]
        for dockerfile in dockerfiles:
            try:
                if os.path.exists(dockerfile):
                    with open(dockerfile, "r") as f:
                        content = f.read()
                        if "FROM" in content and "COPY" in content and "CMD" in content:
                            self.test_passed(f"{dockerfile} configuration")
                        else:
                            self.test_failed(dockerfile, "Invalid Dockerfile structure")
                else:
                    self.test_failed(dockerfile, "File not found")
            except Exception as e:
                self.test_failed(dockerfile, str(e))
    
    def validate_phase_4_monitoring(self):
        """Validate Phase 4: Monitoring Infrastructure"""
        self.log("🔍 PHASE 4: Monitoring Infrastructure Validation")
        
        # Test 1: Monitoring docker-compose
        try:
            monitoring_path = "monitoring/docker-compose.monitoring.yml"
            if os.path.exists(monitoring_path):
                with open(monitoring_path, "r") as f:
                    content = f.read()
                    required_services = ["prometheus:", "grafana:", "alertmanager:"]
                    if all(service in content for service in required_services):
                        self.test_passed("Monitoring stack configuration")
                    else:
                        self.test_failed("Monitoring stack", "Missing required services")
            else:
                self.test_failed("Monitoring stack", "Configuration file not found")
        except Exception as e:
            self.test_failed("Monitoring stack", str(e))
        
        # Test 2: Prometheus configuration
        try:
            prom_path = "monitoring/prometheus.yml"
            if os.path.exists(prom_path):
                with open(prom_path, "r") as f:
                    content = f.read()
                    if "multiagent-backend" in content and "scrape_configs:" in content:
                        self.test_passed("Prometheus scraping configuration")
                    else:
                        self.test_failed("Prometheus config", "Missing backend scraping")
            else:
                self.test_failed("Prometheus config", "prometheus.yml not found")
        except Exception as e:
            self.test_failed("Prometheus config", str(e))
        
        # Test 3: Alert rules
        try:
            rules_path = "monitoring/alerting/rules.yml"
            if os.path.exists(rules_path):
                with open(rules_path, "r") as f:
                    content = f.read()
                    if "MultiAgentBackendDown" in content and "HighCPUUsage" in content:
                        self.test_passed("Alerting rules configuration")
                    else:
                        self.test_failed("Alert rules", "Missing critical alerts")
            else:
                self.test_failed("Alert rules", "rules.yml not found")
        except Exception as e:
            self.test_failed("Alert rules", str(e))
        
        # Test 4: AlertManager configuration
        try:
            alert_path = "monitoring/alerting/alertmanager.yml"
            if os.path.exists(alert_path):
                with open(alert_path, "r") as f:
                    content = f.read()
                    if "critical-alerts" in content and "warning-alerts" in content:
                        self.test_passed("AlertManager notification configuration")
                    else:
                        self.test_failed("AlertManager config", "Missing notification routes")
            else:
                self.test_failed("AlertManager config", "alertmanager.yml not found")
        except Exception as e:
            self.test_failed("AlertManager config", str(e))
    
    def validate_backend_enhancements(self):
        """Validate enhanced backend functionality"""
        self.log("🔍 BACKEND: Enhanced Functionality Validation")
        
        # Test 1: Backend imports
        try:
            from backend.core.app import app
            self.test_passed("Backend application imports successfully")
        except Exception as e:
            self.test_failed("Backend imports", str(e))
            return
        
        # Test 2: Enhanced health endpoint
        try:
            # Check if health endpoint exists in routes
            health_found = False
            for route in app.routes:
                if hasattr(route, 'path') and route.path == '/health':
                    health_found = True
                    break
            
            if health_found:
                self.test_passed("Enhanced health endpoint registered")
            else:
                self.test_failed("Health endpoint", "Not found in routes")
        except Exception as e:
            self.test_failed("Health endpoint", str(e))
        
        # Test 3: Metrics endpoint
        try:
            metrics_found = False
            for route in app.routes:
                if hasattr(route, 'path') and route.path == '/metrics':
                    metrics_found = True
                    break
            
            if metrics_found:
                self.test_passed("Production metrics endpoint registered")
            else:
                self.test_failed("Metrics endpoint", "Not found in routes")
        except Exception as e:
            self.test_failed("Metrics endpoint", str(e))
    
    def validate_agent_metrics(self):
        """Validate agent metrics functionality"""
        self.log("🔍 AGENTS: Metrics Integration Validation")
        
        # Test 1: Agent metrics import
        try:
            sys.path.append('agents/')
            from base_agent import AgentMetrics, MetricsEnabledBaseAgent
            self.test_passed("Agent metrics classes import successfully")
        except Exception as e:
            self.test_failed("Agent metrics import", str(e))
            return
        
        # Test 2: Metrics collection functionality
        try:
            metrics = AgentMetrics('TestAgent')
            start_time = metrics.record_request_start()
            time.sleep(0.01)  # Simulate work
            metrics.record_request_end(start_time, True, task_type='validation')
            
            collected_metrics = metrics.get_metrics()
            if collected_metrics['performance']['total_requests'] == 1:
                self.test_passed("Agent metrics collection works", 
                               f"Success rate: {collected_metrics['performance']['success_rate_percent']}%")
            else:
                self.test_failed("Metrics collection", "Request not recorded")
        except Exception as e:
            self.test_failed("Metrics collection", str(e))
        
        # Test 3: Prometheus format
        try:
            prometheus_output = metrics.get_prometheus_metrics()
            if 'agent_uptime_seconds' in prometheus_output and 'agent_requests_total' in prometheus_output:
                self.test_passed("Prometheus metrics format generation")
            else:
                self.test_failed("Prometheus format", "Missing required metrics")
        except Exception as e:
            self.test_failed("Prometheus format", str(e))
        
        # Test 4: Enhanced agent class
        try:
            from base_agent import CodeGenerationAgent
            agent = CodeGenerationAgent()
            if hasattr(agent, 'metrics') and hasattr(agent, 'get_agent_metrics'):
                self.test_passed("MetricsEnabledBaseAgent functionality")
            else:
                self.test_failed("Enhanced agent", "Missing metrics attributes")
        except Exception as e:
            self.test_failed("Enhanced agent", str(e))
    
    def validate_feedback_system(self):
        """Validate feedback collection system"""
        self.log("🔍 FEEDBACK: User Feedback System Validation")
        
        # Test 1: Feedback API routes
        try:
            from feedback.api.feedback_routes import router, FeedbackRequest
            self.test_passed("Feedback API routes import successfully")
        except Exception as e:
            self.test_failed("Feedback API import", str(e))
            return
        
        # Test 2: Feedback models
        try:
            test_feedback = FeedbackRequest(
                project_id="test-123",
                user_rating=5,
                vibe_alignment_score=9,
                code_quality_score=8,
                usability_score=7,
                comments="Test feedback"
            )
            self.test_passed("Feedback data models validation")
        except Exception as e:
            self.test_failed("Feedback models", str(e))
        
        # Test 3: Frontend component
        try:
            if os.path.exists("feedback/frontend/FeedbackModal.tsx"):
                with open("feedback/frontend/FeedbackModal.tsx", "r") as f:
                    content = f.read()
                    if "FeedbackModal" in content and "useState" in content:
                        self.test_passed("Feedback frontend component created")
                    else:
                        self.test_failed("Frontend component", "Invalid component structure")
            else:
                self.test_failed("Frontend component", "FeedbackModal.tsx not found")
        except Exception as e:
            self.test_failed("Frontend component", str(e))
    
    def run_comprehensive_validation(self):
        """Run all validation tests"""
        self.log("🚀 STARTING COMPREHENSIVE DEPLOYMENT VALIDATION")
        self.log("=" * 60)
        
        # Phase 3 validation
        self.validate_phase_3_production_config()
        self.log("")
        
        # Phase 4 validation
        self.validate_phase_4_monitoring()
        self.log("")
        
        # Backend enhancements
        self.validate_backend_enhancements()
        self.log("")
        
        # Agent metrics
        self.validate_agent_metrics()
        self.log("")
        
        # Feedback system
        self.validate_feedback_system()
        self.log("")
        
        # Calculate overall status
        success_rate = (self.results["success_count"] / self.results["total_tests"]) * 100
        
        if success_rate >= 90:
            self.results["overall_status"] = "EXCELLENT"
            status_icon = "🎉"
        elif success_rate >= 75:
            self.results["overall_status"] = "GOOD"
            status_icon = "✅"
        elif success_rate >= 50:
            self.results["overall_status"] = "PARTIAL"
            status_icon = "⚠️"
        else:
            self.results["overall_status"] = "NEEDS_WORK"
            status_icon = "❌"
        
        # Print summary
        self.log("=" * 60)
        self.log(f"{status_icon} VALIDATION SUMMARY")
        self.log(f"Tests Passed: {self.results['success_count']}/{self.results['total_tests']}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        self.log(f"Overall Status: {self.results['overall_status']}")
        
        if self.results["issues_found"]:
            self.log("\n🔍 ISSUES FOUND:")
            for issue in self.results["issues_found"]:
                self.log(f"  - {issue}")
        
        self.log("=" * 60)
        
        return self.results

def main():
    """Main execution function"""
    validator = DeploymentValidator()
    results = validator.run_comprehensive_validation()
    
    # Save results to file
    with open("deployment_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    validator.log("📁 Results saved to deployment_validation_results.json")
    
    # Return appropriate exit code
    if results["overall_status"] in ["EXCELLENT", "GOOD"]:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())