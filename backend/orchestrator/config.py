"""
Configuration module for Agent Orchestrator

This module provides centralized configuration for the orchestrator,
including feature flags, performance tuning, and autoscaling parameters.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import os


class SchedulingStrategy(Enum):
    """Available scheduling strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    COST_BASED = "cost_based"
    PERFORMANCE_BASED = "performance_based"


@dataclass
class AutoscalingConfig:
    """Autoscaling configuration parameters"""
    enabled: bool = True
    min_agents_per_type: int = 2
    max_agents_per_type: int = 100
    target_queue_depth: int = 5
    scale_up_threshold: float = 0.8  # 80% utilization
    scale_down_threshold: float = 0.2  # 20% utilization
    scale_up_rate: int = 2  # Number of agents to add
    scale_down_rate: int = 1  # Number of agents to remove
    cooldown_seconds: int = 60  # Time between scaling decisions
    
    # Cost-aware scaling
    cost_optimization_enabled: bool = True
    max_hourly_cost: float = 1000.0  # Maximum cost per hour
    agent_cost_per_hour: Dict[str, float] = field(default_factory=lambda: {
        "planner": 10.0,
        "code_generator": 15.0,
        "tester": 12.0,
        "reviewer": 8.0,
        "doc_generator": 5.0
    })


@dataclass
class FaultToleranceConfig:
    """Fault tolerance and reliability configuration"""
    enable_exactly_once_delivery: bool = True
    enable_dead_letter_queue: bool = True
    max_task_retries: int = 3
    task_timeout_seconds: int = 300  # 5 minutes
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5  # Failures before opening
    circuit_breaker_timeout: int = 60  # Seconds before half-open
    enable_task_checkpointing: bool = True
    checkpoint_interval_seconds: int = 30


@dataclass
class ObservabilityConfig:
    """Observability and monitoring configuration"""
    enable_opentelemetry: bool = True
    enable_prometheus_metrics: bool = True
    enable_distributed_tracing: bool = True
    trace_sample_rate: float = 0.1  # 10% sampling
    metrics_port: int = 9090
    jaeger_endpoint: str = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_performance_profiling: bool = False


@dataclass
class PerformanceConfig:
    """Performance and optimization configuration"""
    max_concurrent_tasks: int = 10000
    task_queue_size: int = 50000
    batch_size: int = 100  # For batch operations
    connection_pool_size: int = 100
    grpc_max_message_size: int = 100 * 1024 * 1024  # 100MB
    enable_connection_pooling: bool = True
    enable_task_batching: bool = True
    enable_result_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Load shedding
    enable_load_shedding: bool = True
    load_shedding_threshold: float = 0.9  # 90% capacity
    priority_queue_enabled: bool = True


@dataclass
class OrchestratorConfig:
    """Main orchestrator configuration"""
    # Core settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    postgres_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/orchestrator")
    
    # Feature flags
    feature_flags: Dict[str, bool] = field(default_factory=lambda: {
        "cost_based_scheduling": False,  # Phase 2
        "critical_path_analysis": True,   # Phase 1
        "dag_optimization": True,         # Phase 1
        "predictive_scaling": False,      # Phase 3
        "multi_region_support": False,    # Phase 3
        "task_preemption": False,         # Phase 2
        "adaptive_timeout": True,         # Phase 1
        "smart_retries": True,            # Phase 1
    })
    
    # Scheduling
    scheduling_strategy: SchedulingStrategy = SchedulingStrategy.LEAST_BUSY
    enable_gang_scheduling: bool = False  # Schedule related tasks together
    enable_affinity_scheduling: bool = True  # Keep tasks on same agent
    
    # Sub-configurations
    autoscaling: AutoscalingConfig = field(default_factory=AutoscalingConfig)
    fault_tolerance: FaultToleranceConfig = field(default_factory=FaultToleranceConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Agent-specific configurations
    agent_health_check_interval: int = 10  # seconds
    agent_heartbeat_timeout: int = 30  # seconds
    agent_grpc_timeout: int = 60  # seconds
    
    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Create configuration from environment variables"""
        config = cls()
        
        # Override with environment variables
        if os.getenv("ENABLE_COST_BASED_SCHEDULING"):
            config.feature_flags["cost_based_scheduling"] = os.getenv("ENABLE_COST_BASED_SCHEDULING").lower() == "true"
        
        if os.getenv("MAX_CONCURRENT_TASKS"):
            config.performance.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS"))
        
        if os.getenv("SCHEDULING_STRATEGY"):
            config.scheduling_strategy = SchedulingStrategy(os.getenv("SCHEDULING_STRATEGY"))
        
        return config


# Global configuration instance
config = OrchestratorConfig.from_env()