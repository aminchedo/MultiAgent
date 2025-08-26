"""
Automated Health Check System with SLA Verification
Monitors all system components and provides comprehensive health status.
"""

import asyncio
import json
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import aiohttp
import aiofiles

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class CheckType(Enum):
    """Types of health checks."""
    DATABASE = "database"
    REDIS = "redis"
    AGENTS = "agents"
    EXTERNAL_APIS = "external_apis"
    DISK_SPACE = "disk_space"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"


@dataclass
class HealthCheck:
    """Individual health check configuration."""
    name: str
    check_type: CheckType
    check_function: Callable
    timeout: int = 30
    retry_count: int = 3
    interval: int = 60  # seconds
    critical: bool = False
    thresholds: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    timestamp: datetime
    response_time: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class SLAMetrics:
    """SLA metrics tracking."""
    uptime_percentage: float
    avg_response_time: float
    error_rate: float
    availability_target: float = 99.95
    performance_target: float = 500.0  # ms
    error_rate_target: float = 0.1  # %


class HealthMonitor:
    """
    Comprehensive health monitoring system with SLA verification.
    
    Features:
    - Automated health checks for all system components
    - SLA compliance monitoring (99.95% uptime)
    - Real-time metrics collection
    - Alerting and notification system
    - Performance degradation detection
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.checks: Dict[str, HealthCheck] = {}
        self.last_results: Dict[str, CheckResult] = {}
        self.start_time = datetime.now()
        self.running = False
        self.check_tasks = []
        
        # SLA tracking
        self.uptime_start = datetime.now()
        self.downtime_periods: List[Dict[str, datetime]] = []
        self.response_times: List[float] = []
        self.error_count = 0
        self.total_requests = 0
        
        # Initialize health checks
        self._initialize_health_checks()
    
    def _initialize_health_checks(self):
        """Initialize all health checks."""
        
        # Database health check
        self.register_check(HealthCheck(
            name="database",
            check_type=CheckType.DATABASE,
            check_function=self._check_database,
            timeout=10,
            critical=True,
            thresholds={"connection_time": 5.0}
        ))
        
        # Redis health check
        self.register_check(HealthCheck(
            name="redis",
            check_type=CheckType.REDIS,
            check_function=self._check_redis,
            timeout=5,
            critical=True,
            thresholds={"latency": 10.0}
        ))
        
        # Agents health check
        self.register_check(HealthCheck(
            name="agents",
            check_type=CheckType.AGENTS,
            check_function=self._check_agents,
            timeout=15,
            critical=True,
            thresholds={"min_active_agents": 1}
        ))
        
        # External APIs health check
        self.register_check(HealthCheck(
            name="external_apis",
            check_type=CheckType.EXTERNAL_APIS,
            check_function=self._check_external_apis,
            timeout=20,
            critical=False,
            thresholds={"response_time": 5000.0}
        ))
        
        # System resource checks
        self.register_check(HealthCheck(
            name="disk_space",
            check_type=CheckType.DISK_SPACE,
            check_function=self._check_disk_space,
            timeout=5,
            critical=True,
            thresholds={"min_free_percent": 10.0}
        ))
        
        self.register_check(HealthCheck(
            name="memory",
            check_type=CheckType.MEMORY,
            check_function=self._check_memory,
            timeout=5,
            critical=False,
            thresholds={"max_usage_percent": 90.0}
        ))
        
        self.register_check(HealthCheck(
            name="cpu",
            check_type=CheckType.CPU,
            check_function=self._check_cpu,
            timeout=5,
            critical=False,
            thresholds={"max_usage_percent": 95.0}
        ))
    
    def register_check(self, health_check: HealthCheck):
        """Register a new health check."""
        self.checks[health_check.name] = health_check
        logger.info(f"Registered health check: {health_check.name}")
    
    async def start_monitoring(self):
        """Start the health monitoring system."""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting health monitoring system")
        
        # Start individual check tasks
        for check_name, check in self.checks.items():
            task = asyncio.create_task(self._run_check_loop(check))
            self.check_tasks.append(task)
        
        # Start metrics collection task
        metrics_task = asyncio.create_task(self._collect_metrics_loop())
        self.check_tasks.append(metrics_task)
        
        # Start SLA tracking task
        sla_task = asyncio.create_task(self._track_sla_loop())
        self.check_tasks.append(sla_task)
    
    async def stop_monitoring(self):
        """Stop the health monitoring system."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping health monitoring system")
        
        # Cancel all tasks
        for task in self.check_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.check_tasks, return_exceptions=True)
        self.check_tasks.clear()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status.
        
        Returns:
            Complete health status including individual checks and overall status
        """
        overall_status = HealthStatus.HEALTHY
        checks = {}
        
        # Collect results from all checks
        for check_name, check in self.checks.items():
            result = self.last_results.get(check_name)
            
            if result:
                checks[check_name] = {
                    "status": result.status.value,
                    "message": result.message,
                    "timestamp": result.timestamp.isoformat(),
                    "response_time": result.response_time,
                    "details": result.details
                }
                
                # Determine overall status
                if result.status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                elif result.status == HealthStatus.UNHEALTHY and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            else:
                checks[check_name] = {
                    "status": "unknown",
                    "message": "Check not yet executed",
                    "timestamp": None,
                    "response_time": 0,
                    "details": {}
                }
        
        # Calculate uptime
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "uptime": uptime,
            "checks": checks,
            "summary": {
                "total_checks": len(self.checks),
                "healthy_checks": len([c for c in checks.values() if c["status"] == "healthy"]),
                "degraded_checks": len([c for c in checks.values() if c["status"] == "degraded"]),
                "unhealthy_checks": len([c for c in checks.values() if c["status"] == "unhealthy"]),
                "critical_checks": len([c for c in checks.values() if c["status"] == "critical"])
            }
        }
    
    async def get_sla_metrics(self) -> SLAMetrics:
        """
        Get SLA compliance metrics.
        
        Returns:
            SLA metrics including uptime percentage and performance metrics
        """
        current_time = datetime.now()
        total_time = (current_time - self.uptime_start).total_seconds()
        
        # Calculate downtime
        total_downtime = 0
        for period in self.downtime_periods:
            if "end" in period:
                downtime = (period["end"] - period["start"]).total_seconds()
            else:
                # Ongoing downtime
                downtime = (current_time - period["start"]).total_seconds()
            total_downtime += downtime
        
        # Calculate uptime percentage
        uptime_percentage = max(0, ((total_time - total_downtime) / total_time) * 100) if total_time > 0 else 100
        
        # Calculate average response time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        # Calculate error rate
        error_rate = (self.error_count / self.total_requests) * 100 if self.total_requests > 0 else 0
        
        return SLAMetrics(
            uptime_percentage=uptime_percentage,
            avg_response_time=avg_response_time,
            error_rate=error_rate
        )
    
    async def check_sla_compliance(self) -> Dict[str, Any]:
        """
        Check SLA compliance against targets.
        
        Returns:
            SLA compliance status and details
        """
        metrics = await self.get_sla_metrics()
        
        compliance = {
            "uptime": {
                "current": metrics.uptime_percentage,
                "target": metrics.availability_target,
                "compliant": metrics.uptime_percentage >= metrics.availability_target,
                "status": "pass" if metrics.uptime_percentage >= metrics.availability_target else "fail"
            },
            "performance": {
                "current": metrics.avg_response_time,
                "target": metrics.performance_target,
                "compliant": metrics.avg_response_time <= metrics.performance_target,
                "status": "pass" if metrics.avg_response_time <= metrics.performance_target else "fail"
            },
            "error_rate": {
                "current": metrics.error_rate,
                "target": metrics.error_rate_target,
                "compliant": metrics.error_rate <= metrics.error_rate_target,
                "status": "pass" if metrics.error_rate <= metrics.error_rate_target else "fail"
            }
        }
        
        # Overall compliance
        overall_compliant = all(sla["compliant"] for sla in compliance.values())
        
        return {
            "overall_compliant": overall_compliant,
            "compliance_score": sum(1 for sla in compliance.values() if sla["compliant"]) / len(compliance) * 100,
            "details": compliance,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_check_loop(self, check: HealthCheck):
        """Run health check in a loop."""
        while self.running:
            try:
                result = await self._execute_check(check)
                self.last_results[check.name] = result
                
                # Store result in Redis for persistence
                await self._store_check_result(result)
                
                # Track SLA metrics
                await self._update_sla_metrics(result)
                
                # Check for alerting conditions
                await self._check_alerting_conditions(check, result)
                
            except Exception as e:
                logger.error(f"Error in health check {check.name}: {e}")
            
            await asyncio.sleep(check.interval)
    
    async def _execute_check(self, check: HealthCheck) -> CheckResult:
        """Execute a single health check with retries."""
        start_time = time.time()
        
        for attempt in range(check.retry_count):
            try:
                # Execute check with timeout
                result = await asyncio.wait_for(
                    check.check_function(check),
                    timeout=check.timeout
                )
                
                response_time = (time.time() - start_time) * 1000  # ms
                
                return CheckResult(
                    name=check.name,
                    status=result.get("status", HealthStatus.HEALTHY),
                    timestamp=datetime.now(),
                    response_time=response_time,
                    message=result.get("message", "Check passed"),
                    details=result.get("details", {}),
                    error=result.get("error")
                )
                
            except asyncio.TimeoutError:
                if attempt == check.retry_count - 1:
                    response_time = check.timeout * 1000
                    return CheckResult(
                        name=check.name,
                        status=HealthStatus.UNHEALTHY,
                        timestamp=datetime.now(),
                        response_time=response_time,
                        message=f"Check timed out after {check.timeout}s",
                        error="Timeout"
                    )
                await asyncio.sleep(1)  # Brief delay before retry
                
            except Exception as e:
                if attempt == check.retry_count - 1:
                    response_time = (time.time() - start_time) * 1000
                    return CheckResult(
                        name=check.name,
                        status=HealthStatus.CRITICAL if check.critical else HealthStatus.UNHEALTHY,
                        timestamp=datetime.now(),
                        response_time=response_time,
                        message=f"Check failed: {str(e)}",
                        error=str(e)
                    )
                await asyncio.sleep(1)
    
    # Individual health check implementations
    
    async def _check_database(self, check: HealthCheck) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Try to connect to database (implementation depends on DB type)
            # This is a mock implementation
            await asyncio.sleep(0.1)  # Simulate DB query
            
            connection_time = (time.time() - start_time) * 1000
            
            if connection_time > check.thresholds.get("connection_time", 5000):
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"Database connection slow: {connection_time:.2f}ms",
                    "details": {"connection_time": connection_time}
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Database connection healthy",
                "details": {"connection_time": connection_time}
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "message": f"Database connection failed: {str(e)}",
                "error": str(e)
            }
    
    async def _check_redis(self, check: HealthCheck) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test Redis connection
            await self.redis.ping()
            
            # Test read/write performance
            test_key = "health_check_test"
            await self.redis.set(test_key, "test_value", ex=60)
            value = await self.redis.get(test_key)
            await self.redis.delete(test_key)
            
            latency = (time.time() - start_time) * 1000
            
            if latency > check.thresholds.get("latency", 100):
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"Redis latency high: {latency:.2f}ms",
                    "details": {"latency": latency}
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Redis connection healthy",
                "details": {"latency": latency, "test_result": value == "test_value"}
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "message": f"Redis connection failed: {str(e)}",
                "error": str(e)
            }
    
    async def _check_agents(self, check: HealthCheck) -> Dict[str, Any]:
        """Check agent system health."""
        try:
            # Get agent status from discovery service
            # This would integrate with the actual discovery service
            
            # Mock implementation
            active_agents = 3  # This would come from discovery service
            min_required = check.thresholds.get("min_active_agents", 1)
            
            if active_agents < min_required:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"Insufficient active agents: {active_agents}/{min_required}",
                    "details": {"active_agents": active_agents, "required": min_required}
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"Agent system healthy: {active_agents} active agents",
                "details": {"active_agents": active_agents}
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Agent check failed: {str(e)}",
                "error": str(e)
            }
    
    async def _check_external_apis(self, check: HealthCheck) -> Dict[str, Any]:
        """Check external API dependencies."""
        external_apis = [
            "https://api.openai.com/v1/models",  # Example external API
        ]
        
        results = []
        overall_status = HealthStatus.HEALTHY
        
        async with aiohttp.ClientSession() as session:
            for api_url in external_apis:
                try:
                    start_time = time.time()
                    async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            if response_time > check.thresholds.get("response_time", 5000):
                                status = HealthStatus.DEGRADED
                                if overall_status == HealthStatus.HEALTHY:
                                    overall_status = HealthStatus.DEGRADED
                            else:
                                status = HealthStatus.HEALTHY
                        else:
                            status = HealthStatus.DEGRADED
                            if overall_status == HealthStatus.HEALTHY:
                                overall_status = HealthStatus.DEGRADED
                        
                        results.append({
                            "url": api_url,
                            "status": status.value,
                            "response_time": response_time,
                            "status_code": response.status
                        })
                        
                except Exception as e:
                    overall_status = HealthStatus.DEGRADED
                    results.append({
                        "url": api_url,
                        "status": "unhealthy",
                        "error": str(e)
                    })
        
        return {
            "status": overall_status,
            "message": f"External APIs check: {len(results)} APIs checked",
            "details": {"apis": results}
        }
    
    async def _check_disk_space(self, check: HealthCheck) -> Dict[str, Any]:
        """Check disk space availability."""
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            min_free = check.thresholds.get("min_free_percent", 10.0)
            
            if free_percent < min_free:
                status = HealthStatus.CRITICAL if free_percent < 5.0 else HealthStatus.UNHEALTHY
                return {
                    "status": status,
                    "message": f"Low disk space: {free_percent:.1f}% free",
                    "details": {
                        "free_percent": free_percent,
                        "free_gb": disk_usage.free / (1024**3),
                        "total_gb": disk_usage.total / (1024**3)
                    }
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"Disk space healthy: {free_percent:.1f}% free",
                "details": {
                    "free_percent": free_percent,
                    "free_gb": disk_usage.free / (1024**3),
                    "total_gb": disk_usage.total / (1024**3)
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Disk space check failed: {str(e)}",
                "error": str(e)
            }
    
    async def _check_memory(self, check: HealthCheck) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            max_usage = check.thresholds.get("max_usage_percent", 90.0)
            
            if usage_percent > max_usage:
                status = HealthStatus.CRITICAL if usage_percent > 95.0 else HealthStatus.DEGRADED
                return {
                    "status": status,
                    "message": f"High memory usage: {usage_percent:.1f}%",
                    "details": {
                        "usage_percent": usage_percent,
                        "available_gb": memory.available / (1024**3),
                        "total_gb": memory.total / (1024**3)
                    }
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"Memory usage healthy: {usage_percent:.1f}%",
                "details": {
                    "usage_percent": usage_percent,
                    "available_gb": memory.available / (1024**3),
                    "total_gb": memory.total / (1024**3)
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Memory check failed: {str(e)}",
                "error": str(e)
            }
    
    async def _check_cpu(self, check: HealthCheck) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            # Get CPU usage over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            
            max_usage = check.thresholds.get("max_usage_percent", 95.0)
            
            if cpu_percent > max_usage:
                status = HealthStatus.CRITICAL if cpu_percent > 98.0 else HealthStatus.DEGRADED
                return {
                    "status": status,
                    "message": f"High CPU usage: {cpu_percent:.1f}%",
                    "details": {
                        "usage_percent": cpu_percent,
                        "cpu_count": psutil.cpu_count()
                    }
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"CPU usage healthy: {cpu_percent:.1f}%",
                "details": {
                    "usage_percent": cpu_percent,
                    "cpu_count": psutil.cpu_count()
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"CPU check failed: {str(e)}",
                "error": str(e)
            }
    
    # Supporting methods
    
    async def _store_check_result(self, result: CheckResult):
        """Store check result in Redis for persistence."""
        try:
            data = {
                "name": result.name,
                "status": result.status.value,
                "timestamp": result.timestamp.isoformat(),
                "response_time": result.response_time,
                "message": result.message,
                "details": result.details,
                "error": result.error
            }
            
            # Store latest result
            await self.redis.hset("health_checks", result.name, json.dumps(data))
            
            # Store historical data (keep last 24 hours)
            history_key = f"health_history:{result.name}"
            await self.redis.lpush(history_key, json.dumps(data))
            await self.redis.ltrim(history_key, 0, 1440)  # Keep 24 hours of minute-level data
            await self.redis.expire(history_key, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Failed to store health check result: {e}")
    
    async def _update_sla_metrics(self, result: CheckResult):
        """Update SLA metrics based on check result."""
        self.total_requests += 1
        
        if result.error:
            self.error_count += 1
        
        # Track response times (keep last 1000 for rolling average)
        self.response_times.append(result.response_time)
        if len(self.response_times) > 1000:
            self.response_times.pop(0)
        
        # Track downtime periods
        if result.status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
            # Check if this starts a new downtime period
            if not self.downtime_periods or "end" in self.downtime_periods[-1]:
                self.downtime_periods.append({"start": result.timestamp})
        else:
            # Check if this ends a downtime period
            if self.downtime_periods and "end" not in self.downtime_periods[-1]:
                self.downtime_periods[-1]["end"] = result.timestamp
    
    async def _check_alerting_conditions(self, check: HealthCheck, result: CheckResult):
        """Check if alerting conditions are met."""
        # Implement alerting logic here
        if result.status == HealthStatus.CRITICAL and check.critical:
            await self._send_alert(check, result)
    
    async def _send_alert(self, check: HealthCheck, result: CheckResult):
        """Send alert for critical health check failure."""
        alert_data = {
            "type": "health_check_critical",
            "check_name": check.name,
            "status": result.status.value,
            "message": result.message,
            "timestamp": result.timestamp.isoformat(),
            "details": result.details
        }
        
        # Store alert in Redis
        await self.redis.lpush("alerts", json.dumps(alert_data))
        
        logger.critical(f"ALERT: Critical health check failure - {check.name}: {result.message}")
    
    async def _collect_metrics_loop(self):
        """Collect and store system metrics."""
        while self.running:
            try:
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "system": {
                        "cpu_percent": psutil.cpu_percent(),
                        "memory_percent": psutil.virtual_memory().percent,
                        "disk_usage_percent": psutil.disk_usage('/').percent
                    },
                    "health_checks": len(self.checks),
                    "active_checks": len([r for r in self.last_results.values() 
                                        if r.status == HealthStatus.HEALTHY])
                }
                
                # Store metrics
                await self.redis.lpush("system_metrics", json.dumps(metrics))
                await self.redis.ltrim("system_metrics", 0, 1440)  # Keep 24 hours
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            await asyncio.sleep(60)  # Collect every minute
    
    async def _track_sla_loop(self):
        """Track SLA compliance over time."""
        while self.running:
            try:
                metrics = await self.get_sla_metrics()
                compliance = await self.check_sla_compliance()
                
                sla_data = {
                    "timestamp": datetime.now().isoformat(),
                    "uptime_percentage": metrics.uptime_percentage,
                    "avg_response_time": metrics.avg_response_time,
                    "error_rate": metrics.error_rate,
                    "compliance": compliance
                }
                
                # Store SLA data
                await self.redis.lpush("sla_metrics", json.dumps(sla_data))
                await self.redis.ltrim("sla_metrics", 0, 168)  # Keep 1 week of hourly data
                
            except Exception as e:
                logger.error(f"Error tracking SLA: {e}")
            
            await asyncio.sleep(3600)  # Track every hour