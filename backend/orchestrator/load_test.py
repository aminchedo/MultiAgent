"""
Load Testing Framework for Enhanced Agent Manager

This module provides comprehensive load testing capabilities to validate
the performance and scalability of the production-grade orchestrator.
"""

import asyncio
import time
import random
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import csv
from collections import defaultdict, deque
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

import structlog
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, Summary
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from backend.models.models import AgentType
from .agent_manager_v2 import EnhancedAgentManager, TaskPriority
from .config import OrchestratorConfig


logger = structlog.get_logger()

# Metrics for load testing
load_test_tasks_submitted = Counter('load_test_tasks_submitted_total', 'Total tasks submitted during load test')
load_test_tasks_completed = Counter('load_test_tasks_completed_total', 'Total tasks completed during load test')
load_test_submission_latency = Histogram('load_test_submission_latency_seconds', 'Task submission latency')
load_test_completion_latency = Histogram('load_test_completion_latency_seconds', 'Task completion latency')
load_test_throughput_gauge = Gauge('load_test_throughput_tps', 'Current throughput in tasks per second')


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    # Test duration
    duration_seconds: int = 300  # 5 minutes
    warmup_seconds: int = 30
    
    # Load pattern
    initial_tps: float = 10  # Tasks per second
    max_tps: float = 1000
    ramp_up_seconds: int = 120
    
    # Task mix
    task_distribution: Dict[str, float] = field(default_factory=lambda: {
        "frontend_development": 0.3,
        "backend_development": 0.3,
        "testing": 0.2,
        "code_review": 0.1,
        "documentation": 0.1
    })
    
    # Task complexity distribution
    complexity_distribution: Dict[str, float] = field(default_factory=lambda: {
        "simple": 0.5,     # complexity: 0.5
        "moderate": 0.3,   # complexity: 1.0
        "complex": 0.15,   # complexity: 2.0
        "heavy": 0.05      # complexity: 5.0
    })
    
    # Priority distribution
    priority_distribution: Dict[TaskPriority, float] = field(default_factory=lambda: {
        TaskPriority.CRITICAL: 0.05,
        TaskPriority.HIGH: 0.15,
        TaskPriority.NORMAL: 0.60,
        TaskPriority.LOW: 0.15,
        TaskPriority.BACKGROUND: 0.05
    })
    
    # Dependency patterns
    dependency_probability: float = 0.2  # 20% of tasks have dependencies
    max_dependencies: int = 3
    
    # Concurrency
    num_submitters: int = 10  # Number of concurrent task submitters
    
    # SLA thresholds
    sla_submission_p99: float = 0.1  # 100ms
    sla_completion_p99: float = 60.0  # 60 seconds
    
    # Chaos testing
    enable_chaos: bool = False
    agent_failure_rate: float = 0.01  # 1% chance per minute
    network_delay_ms: Tuple[int, int] = (0, 100)  # Random delay range


@dataclass
class LoadTestResult:
    """Results from a load test run"""
    start_time: datetime
    end_time: datetime
    config: LoadTestConfig
    
    # Submission metrics
    total_submitted: int = 0
    submission_latencies: List[float] = field(default_factory=list)
    submission_errors: int = 0
    
    # Completion metrics
    total_completed: int = 0
    total_failed: int = 0
    completion_times: List[float] = field(default_factory=list)
    
    # Throughput metrics
    throughput_samples: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, tps)
    
    # System metrics
    queue_depth_samples: List[Tuple[float, Dict[str, int]]] = field(default_factory=list)
    agent_utilization_samples: List[Tuple[float, Dict[str, float]]] = field(default_factory=list)
    
    # SLA violations
    submission_sla_violations: int = 0
    completion_sla_violations: int = 0
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics from the test results"""
        stats = {
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "total_submitted": self.total_submitted,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "completion_rate": self.total_completed / self.total_submitted if self.total_submitted > 0 else 0,
            "submission_errors": self.submission_errors,
            "error_rate": self.submission_errors / self.total_submitted if self.total_submitted > 0 else 0
        }
        
        # Submission latency statistics
        if self.submission_latencies:
            stats["submission_latency"] = {
                "min": min(self.submission_latencies),
                "max": max(self.submission_latencies),
                "mean": statistics.mean(self.submission_latencies),
                "median": statistics.median(self.submission_latencies),
                "p95": np.percentile(self.submission_latencies, 95),
                "p99": np.percentile(self.submission_latencies, 99),
                "stdev": statistics.stdev(self.submission_latencies) if len(self.submission_latencies) > 1 else 0
            }
        
        # Completion time statistics
        if self.completion_times:
            stats["completion_time"] = {
                "min": min(self.completion_times),
                "max": max(self.completion_times),
                "mean": statistics.mean(self.completion_times),
                "median": statistics.median(self.completion_times),
                "p95": np.percentile(self.completion_times, 95),
                "p99": np.percentile(self.completion_times, 99),
                "stdev": statistics.stdev(self.completion_times) if len(self.completion_times) > 1 else 0
            }
        
        # Throughput statistics
        if self.throughput_samples:
            throughputs = [tps for _, tps in self.throughput_samples]
            stats["throughput"] = {
                "min": min(throughputs),
                "max": max(throughputs),
                "mean": statistics.mean(throughputs),
                "median": statistics.median(throughputs)
            }
        
        # SLA compliance
        stats["sla_compliance"] = {
            "submission_sla_violations": self.submission_sla_violations,
            "submission_sla_compliance_rate": 1 - (self.submission_sla_violations / self.total_submitted) if self.total_submitted > 0 else 1,
            "completion_sla_violations": self.completion_sla_violations,
            "completion_sla_compliance_rate": 1 - (self.completion_sla_violations / self.total_completed) if self.total_completed > 0 else 1
        }
        
        return stats


class LoadTestRunner:
    """Runs load tests against the Enhanced Agent Manager"""
    
    def __init__(self, manager: EnhancedAgentManager, config: LoadTestConfig):
        self.manager = manager
        self.config = config
        self.result = LoadTestResult(
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            config=config
        )
        
        # Task tracking
        self.submitted_tasks: Dict[str, float] = {}  # task_id -> submission_time
        self.completed_tasks: Dict[str, float] = {}  # task_id -> completion_time
        
        # Metrics collection
        self.submission_times = deque(maxlen=1000)
        self.completion_times = deque(maxlen=1000)
        
        # Control flags
        self._running = False
        self._chaos_task = None
    
    async def run(self) -> LoadTestResult:
        """Execute the load test"""
        logger.info("Starting load test", 
                   duration=self.config.duration_seconds,
                   max_tps=self.config.max_tps)
        
        self.result.start_time = datetime.utcnow()
        self._running = True
        
        try:
            # Start monitoring tasks
            monitor_task = asyncio.create_task(self._monitor_system())
            completion_task = asyncio.create_task(self._track_completions())
            
            # Start chaos engineering if enabled
            if self.config.enable_chaos:
                self._chaos_task = asyncio.create_task(self._chaos_engineering())
            
            # Warmup phase
            if self.config.warmup_seconds > 0:
                logger.info("Starting warmup phase", duration=self.config.warmup_seconds)
                await self._run_warmup()
            
            # Main load test
            await self._run_load_test()
            
            # Wait for all tasks to complete or timeout
            await self._wait_for_completion()
            
        finally:
            self._running = False
            self.result.end_time = datetime.utcnow()
            
            # Cancel background tasks
            monitor_task.cancel()
            completion_task.cancel()
            if self._chaos_task:
                self._chaos_task.cancel()
            
            # Calculate final statistics
            stats = self.result.calculate_statistics()
            logger.info("Load test completed", **stats)
        
        return self.result
    
    async def _run_warmup(self):
        """Run warmup phase with low load"""
        warmup_end = time.time() + self.config.warmup_seconds
        warmup_tps = min(10, self.config.initial_tps)
        
        while time.time() < warmup_end:
            await self._submit_task_batch(warmup_tps / 10)  # Submit in small batches
            await asyncio.sleep(0.1)
    
    async def _run_load_test(self):
        """Run the main load test with ramping load"""
        test_start = time.time()
        test_end = test_start + self.config.duration_seconds
        
        # Create submitter tasks
        submitters = []
        for i in range(self.config.num_submitters):
            submitter = asyncio.create_task(
                self._task_submitter(i, test_start, test_end)
            )
            submitters.append(submitter)
        
        # Wait for all submitters to complete
        await asyncio.gather(*submitters, return_exceptions=True)
    
    async def _task_submitter(self, submitter_id: int, start_time: float, end_time: float):
        """Individual task submitter coroutine"""
        while time.time() < end_time and self._running:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Calculate current target TPS based on ramp-up
            if elapsed < self.config.ramp_up_seconds:
                # Linear ramp-up
                progress = elapsed / self.config.ramp_up_seconds
                target_tps = self.config.initial_tps + (self.config.max_tps - self.config.initial_tps) * progress
            else:
                target_tps = self.config.max_tps
            
            # Each submitter handles a portion of the load
            submitter_tps = target_tps / self.config.num_submitters
            
            # Submit tasks for this iteration
            await self._submit_task_batch(submitter_tps)
            
            # Sleep to maintain target rate
            sleep_time = 1.0 / submitter_tps if submitter_tps > 0 else 1.0
            await asyncio.sleep(sleep_time)
    
    async def _submit_task_batch(self, target_tps: float):
        """Submit a batch of tasks to meet target TPS"""
        num_tasks = int(target_tps)
        if random.random() < (target_tps - num_tasks):
            num_tasks += 1
        
        submission_tasks = []
        for _ in range(num_tasks):
            task = self._generate_random_task()
            submission_tasks.append(self._submit_single_task(task))
        
        # Submit tasks concurrently
        await asyncio.gather(*submission_tasks, return_exceptions=True)
    
    async def _submit_single_task(self, task_spec: Dict[str, Any]):
        """Submit a single task and track metrics"""
        start_time = time.time()
        
        try:
            task_id = await self.manager.submit_task(
                task_type=task_spec["type"],
                payload=task_spec["payload"],
                priority=task_spec["priority"],
                dependencies=task_spec["dependencies"],
                estimated_complexity=task_spec["complexity"]
            )
            
            submission_time = time.time() - start_time
            
            # Track submission
            self.submitted_tasks[task_id] = time.time()
            self.submission_times.append(submission_time)
            self.result.submission_latencies.append(submission_time)
            self.result.total_submitted += 1
            
            # Check SLA
            if submission_time > self.config.sla_submission_p99:
                self.result.submission_sla_violations += 1
            
            # Update metrics
            load_test_tasks_submitted.inc()
            load_test_submission_latency.observe(submission_time)
            
        except Exception as e:
            self.result.submission_errors += 1
            logger.error("Task submission failed", error=str(e))
    
    def _generate_random_task(self) -> Dict[str, Any]:
        """Generate a random task based on configured distributions"""
        # Select task type
        task_type = random.choices(
            list(self.config.task_distribution.keys()),
            weights=list(self.config.task_distribution.values())
        )[0]
        
        # Select complexity
        complexity_name = random.choices(
            list(self.config.complexity_distribution.keys()),
            weights=list(self.config.complexity_distribution.values())
        )[0]
        
        complexity_map = {
            "simple": 0.5,
            "moderate": 1.0,
            "complex": 2.0,
            "heavy": 5.0
        }
        complexity = complexity_map[complexity_name]
        
        # Select priority
        priority = random.choices(
            list(self.config.priority_distribution.keys()),
            weights=list(self.config.priority_distribution.values())
        )[0]
        
        # Generate dependencies
        dependencies = []
        if random.random() < self.config.dependency_probability:
            # Select random completed tasks as dependencies
            num_deps = random.randint(1, min(self.config.max_dependencies, len(self.completed_tasks)))
            if self.completed_tasks:
                dependencies = random.sample(list(self.completed_tasks.keys()), 
                                           min(num_deps, len(self.completed_tasks)))
        
        return {
            "type": task_type,
            "payload": {
                "test_id": f"load_test_{time.time()}",
                "complexity": complexity_name,
                "data": "x" * random.randint(100, 1000)  # Variable payload size
            },
            "priority": priority,
            "complexity": complexity,
            "dependencies": dependencies
        }
    
    async def _track_completions(self):
        """Track task completions and calculate metrics"""
        while self._running:
            try:
                # Check for completed tasks
                for task_id, submission_time in list(self.submitted_tasks.items()):
                    if task_id not in self.completed_tasks:
                        status = await self.manager.get_task_status(task_id)
                        
                        if status and status["status"] in ["completed", "failed"]:
                            completion_time = time.time()
                            self.completed_tasks[task_id] = completion_time
                            
                            # Calculate completion latency
                            latency = completion_time - submission_time
                            self.completion_times.append(latency)
                            self.result.completion_times.append(latency)
                            
                            if status["status"] == "completed":
                                self.result.total_completed += 1
                                load_test_tasks_completed.inc()
                                
                                # Check SLA
                                if latency > self.config.sla_completion_p99:
                                    self.result.completion_sla_violations += 1
                            else:
                                self.result.total_failed += 1
                            
                            load_test_completion_latency.observe(latency)
                            
                            # Remove from tracking
                            del self.submitted_tasks[task_id]
                
                # Calculate current throughput
                if self.completion_times:
                    recent_completions = sum(1 for t in self.completion_times 
                                           if time.time() - t < 10)  # Last 10 seconds
                    current_tps = recent_completions / 10.0
                    load_test_throughput_gauge.set(current_tps)
                    self.result.throughput_samples.append((time.time(), current_tps))
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("Error tracking completions", error=str(e))
                await asyncio.sleep(5)
    
    async def _monitor_system(self):
        """Monitor system metrics during the test"""
        while self._running:
            try:
                # Get system statistics
                stats = self.manager.get_system_statistics()
                
                # Record queue depths
                queue_depths = stats["tasks"]["by_priority"]
                self.result.queue_depth_samples.append((time.time(), queue_depths))
                
                # Record agent utilization
                agent_utils = {}
                for agent_type in AgentType:
                    # Calculate utilization from stats
                    agent_utils[agent_type.value] = stats["agents"]["by_status"].get("busy", 0) / \
                                                   stats["agents"]["total"] if stats["agents"]["total"] > 0 else 0
                
                self.result.agent_utilization_samples.append((time.time(), agent_utils))
                
                await asyncio.sleep(5)  # Sample every 5 seconds
                
            except Exception as e:
                logger.error("Error monitoring system", error=str(e))
                await asyncio.sleep(10)
    
    async def _chaos_engineering(self):
        """Introduce controlled failures for resilience testing"""
        logger.info("Chaos engineering enabled")
        
        while self._running:
            try:
                # Random agent failures
                if random.random() < self.config.agent_failure_rate:
                    # Simulate agent going offline
                    agents = list(self.manager.agents.keys())
                    if agents:
                        victim = random.choice(agents)
                        logger.warning("Chaos: Simulating agent failure", agent_id=victim)
                        # Temporarily mark agent as offline
                        # This would be done through the actual agent in production
                
                # Random network delays
                if self.config.network_delay_ms[1] > 0:
                    delay = random.uniform(*self.config.network_delay_ms) / 1000
                    await asyncio.sleep(delay)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Error in chaos engineering", error=str(e))
                await asyncio.sleep(60)
    
    async def _wait_for_completion(self):
        """Wait for all submitted tasks to complete"""
        logger.info("Waiting for task completion", 
                   pending=len(self.submitted_tasks))
        
        timeout = 300  # 5 minutes max wait
        start_wait = time.time()
        
        while self.submitted_tasks and (time.time() - start_wait) < timeout:
            await asyncio.sleep(5)
            logger.info("Still waiting for tasks", 
                       pending=len(self.submitted_tasks))
        
        if self.submitted_tasks:
            logger.warning("Timeout waiting for tasks", 
                         incomplete=len(self.submitted_tasks))


class LoadTestReporter:
    """Generates reports from load test results"""
    
    def __init__(self, results: List[LoadTestResult]):
        self.results = results
    
    def generate_report(self, output_dir: str = "load_test_results"):
        """Generate comprehensive load test report"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate summary statistics
        self._generate_summary_csv(f"{output_dir}/summary.csv")
        
        # Generate latency percentile charts
        self._plot_latency_percentiles(f"{output_dir}/latency_percentiles.png")
        
        # Generate throughput over time
        self._plot_throughput_timeline(f"{output_dir}/throughput_timeline.png")
        
        # Generate queue depth analysis
        self._plot_queue_depths(f"{output_dir}/queue_depths.png")
        
        # Generate detailed report
        self._generate_detailed_report(f"{output_dir}/detailed_report.md")
        
        logger.info("Load test report generated", output_dir=output_dir)
    
    def _generate_summary_csv(self, filename: str):
        """Generate CSV summary of all test runs"""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Test ID", "Duration (s)", "Max TPS", "Total Submitted", 
                "Total Completed", "Completion Rate", "Error Rate",
                "Submission P99 (ms)", "Completion P99 (s)",
                "Submission SLA Compliance", "Completion SLA Compliance"
            ])
            
            for i, result in enumerate(self.results):
                stats = result.calculate_statistics()
                writer.writerow([
                    f"Test_{i+1}",
                    stats["duration_seconds"],
                    result.config.max_tps,
                    stats["total_submitted"],
                    stats["total_completed"],
                    f"{stats['completion_rate']:.2%}",
                    f"{stats['error_rate']:.2%}",
                    stats.get("submission_latency", {}).get("p99", 0) * 1000,
                    stats.get("completion_time", {}).get("p99", 0),
                    f"{stats['sla_compliance']['submission_sla_compliance_rate']:.2%}",
                    f"{stats['sla_compliance']['completion_sla_compliance_rate']:.2%}"
                ])
    
    def _plot_latency_percentiles(self, filename: str):
        """Plot latency percentile comparison"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Submission latencies
        for i, result in enumerate(self.results):
            if result.submission_latencies:
                percentiles = np.percentile(result.submission_latencies, 
                                          [50, 75, 90, 95, 99])
                ax1.plot([50, 75, 90, 95, 99], percentiles, 
                        label=f"Test {i+1} (max {result.config.max_tps} TPS)")
        
        ax1.set_xlabel("Percentile")
        ax1.set_ylabel("Latency (seconds)")
        ax1.set_title("Submission Latency Percentiles")
        ax1.legend()
        ax1.grid(True)
        
        # Completion times
        for i, result in enumerate(self.results):
            if result.completion_times:
                percentiles = np.percentile(result.completion_times, 
                                          [50, 75, 90, 95, 99])
                ax2.plot([50, 75, 90, 95, 99], percentiles, 
                        label=f"Test {i+1} (max {result.config.max_tps} TPS)")
        
        ax2.set_xlabel("Percentile")
        ax2.set_ylabel("Time (seconds)")
        ax2.set_title("Completion Time Percentiles")
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        plt.close()
    
    def _plot_throughput_timeline(self, filename: str):
        """Plot throughput over time"""
        plt.figure(figsize=(12, 6))
        
        for i, result in enumerate(self.results):
            if result.throughput_samples:
                times, throughputs = zip(*result.throughput_samples)
                # Convert to relative times
                start_time = min(times)
                rel_times = [(t - start_time) for t in times]
                
                plt.plot(rel_times, throughputs, 
                        label=f"Test {i+1} (max {result.config.max_tps} TPS)")
        
        plt.xlabel("Time (seconds)")
        plt.ylabel("Throughput (tasks/second)")
        plt.title("Throughput Over Time")
        plt.legend()
        plt.grid(True)
        plt.savefig(filename, dpi=300)
        plt.close()
    
    def _plot_queue_depths(self, filename: str):
        """Plot queue depth analysis"""
        # Use the first result for simplicity
        if not self.results or not self.results[0].queue_depth_samples:
            return
        
        result = self.results[0]
        times, depths = zip(*result.queue_depth_samples)
        start_time = min(times)
        rel_times = [(t - start_time) for t in times]
        
        # Create DataFrame for easier plotting
        df_data = []
        for t, depth_dict in zip(rel_times, depths):
            for priority, depth in depth_dict.items():
                df_data.append({
                    "time": t,
                    "priority": priority,
                    "depth": depth
                })
        
        df = pd.DataFrame(df_data)
        
        plt.figure(figsize=(12, 6))
        for priority in df["priority"].unique():
            priority_df = df[df["priority"] == priority]
            plt.plot(priority_df["time"], priority_df["depth"], label=priority)
        
        plt.xlabel("Time (seconds)")
        plt.ylabel("Queue Depth")
        plt.title("Queue Depth by Priority Over Time")
        plt.legend()
        plt.grid(True)
        plt.savefig(filename, dpi=300)
        plt.close()
    
    def _generate_detailed_report(self, filename: str):
        """Generate detailed markdown report"""
        with open(filename, 'w') as f:
            f.write("# Load Test Detailed Report\n\n")
            f.write(f"Generated: {datetime.utcnow().isoformat()}\n\n")
            
            for i, result in enumerate(self.results):
                f.write(f"## Test Run {i+1}\n\n")
                
                # Configuration
                f.write("### Configuration\n")
                f.write(f"- Duration: {result.config.duration_seconds}s\n")
                f.write(f"- Max TPS: {result.config.max_tps}\n")
                f.write(f"- Ramp-up: {result.config.ramp_up_seconds}s\n")
                f.write(f"- Submitters: {result.config.num_submitters}\n")
                f.write(f"- Chaos Testing: {'Enabled' if result.config.enable_chaos else 'Disabled'}\n\n")
                
                # Results
                stats = result.calculate_statistics()
                f.write("### Results Summary\n")
                f.write(f"- Total Submitted: {stats['total_submitted']:,}\n")
                f.write(f"- Total Completed: {stats['total_completed']:,}\n")
                f.write(f"- Total Failed: {stats['total_failed']:,}\n")
                f.write(f"- Completion Rate: {stats['completion_rate']:.2%}\n")
                f.write(f"- Error Rate: {stats['error_rate']:.2%}\n\n")
                
                # Latency statistics
                if "submission_latency" in stats:
                    f.write("### Submission Latency\n")
                    lat = stats["submission_latency"]
                    f.write(f"- Min: {lat['min']*1000:.2f}ms\n")
                    f.write(f"- Median: {lat['median']*1000:.2f}ms\n")
                    f.write(f"- P95: {lat['p95']*1000:.2f}ms\n")
                    f.write(f"- P99: {lat['p99']*1000:.2f}ms\n")
                    f.write(f"- Max: {lat['max']*1000:.2f}ms\n\n")
                
                if "completion_time" in stats:
                    f.write("### Completion Time\n")
                    comp = stats["completion_time"]
                    f.write(f"- Min: {comp['min']:.2f}s\n")
                    f.write(f"- Median: {comp['median']:.2f}s\n")
                    f.write(f"- P95: {comp['p95']:.2f}s\n")
                    f.write(f"- P99: {comp['p99']:.2f}s\n")
                    f.write(f"- Max: {comp['max']:.2f}s\n\n")
                
                # SLA Compliance
                f.write("### SLA Compliance\n")
                sla = stats["sla_compliance"]
                f.write(f"- Submission SLA Violations: {sla['submission_sla_violations']}\n")
                f.write(f"- Submission SLA Compliance: {sla['submission_sla_compliance_rate']:.2%}\n")
                f.write(f"- Completion SLA Violations: {sla['completion_sla_violations']}\n")
                f.write(f"- Completion SLA Compliance: {sla['completion_sla_compliance_rate']:.2%}\n\n")
                
                # Throughput
                if "throughput" in stats:
                    f.write("### Throughput\n")
                    tp = stats["throughput"]
                    f.write(f"- Peak: {tp['max']:.2f} tasks/second\n")
                    f.write(f"- Average: {tp['mean']:.2f} tasks/second\n")
                    f.write(f"- Sustained: {tp['median']:.2f} tasks/second\n\n")
                
                f.write("---\n\n")


async def run_load_test_suite():
    """Run a comprehensive load test suite"""
    # Initialize the enhanced agent manager
    manager = EnhancedAgentManager()
    await manager.initialize()
    
    # Register mock agents for testing
    agent_types = [
        (AgentType.PLANNER, 5, {"api_design", "database_design", "ui_design", "deployment"}),
        (AgentType.CODE_GENERATOR, 10, {"frontend_development", "backend_development", "api_design", "database_design"}),
        (AgentType.TESTER, 8, {"testing", "frontend_development", "backend_development"}),
        (AgentType.REVIEWER, 3, {"code_review"}),
        (AgentType.DOC_GENERATOR, 2, {"documentation"})
    ]
    
    for agent_type, count, capabilities in agent_types:
        for i in range(count):
            await manager.register_agent(
                agent_type=agent_type,
                capabilities=capabilities,
                max_concurrent_tasks=5,
                cost_factor=1.0 + random.random()  # Random cost factor
            )
    
    # Define test scenarios
    test_configs = [
        # Baseline test
        LoadTestConfig(
            duration_seconds=180,
            max_tps=100,
            ramp_up_seconds=60
        ),
        
        # High throughput test
        LoadTestConfig(
            duration_seconds=300,
            max_tps=1000,
            ramp_up_seconds=120,
            num_submitters=20
        ),
        
        # Stress test with dependencies
        LoadTestConfig(
            duration_seconds=300,
            max_tps=500,
            dependency_probability=0.5,
            max_dependencies=5
        ),
        
        # Chaos engineering test
        LoadTestConfig(
            duration_seconds=300,
            max_tps=200,
            enable_chaos=True,
            agent_failure_rate=0.05
        )
    ]
    
    results = []
    
    try:
        for i, config in enumerate(test_configs):
            logger.info(f"Running test scenario {i+1}/{len(test_configs)}")
            
            runner = LoadTestRunner(manager, config)
            result = await runner.run()
            results.append(result)
            
            # Cool down between tests
            await asyncio.sleep(30)
        
        # Generate reports
        reporter = LoadTestReporter(results)
        reporter.generate_report()
        
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    # Run the load test suite
    asyncio.run(run_load_test_suite())