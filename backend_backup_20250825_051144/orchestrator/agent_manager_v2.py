"""
Production-Grade Agent Orchestrator for Multi-Agent Collaboration Framework

This module implements an enhanced, scalable orchestration engine with:
- Async task assignment with backpressure
- Fault tolerance and exactly-once delivery
- Advanced scheduling with cost optimization
- Comprehensive observability
- Dynamic autoscaling
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import heapq
import json
from collections import defaultdict, deque
import time
from contextlib import asynccontextmanager
import pickle

import structlog
from asyncio import Queue, PriorityQueue, Semaphore
import redis.asyncio as redis
from prometheus_client import Counter, Gauge, Histogram, Summary
import asyncpg
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
import networkx as nx
from circuit_breaker import CircuitBreaker

from backend.models.models import AgentType, JobStatus
from backend.memory.context_store import SharedMemoryStore
from backend.grpc.agent_client import AgentServiceClient
from backend.database.db import db_manager
from .config import config, SchedulingStrategy


# Initialize OpenTelemetry
if config.observability.enable_opentelemetry:
    AsyncioInstrumentor().instrument()
    tracer = trace.get_tracer("agent_manager", "1.0.0")
else:
    tracer = None

logger = structlog.get_logger()

# Enhanced Metrics
task_assigned_counter = Counter('agent_tasks_assigned_total', 'Total tasks assigned to agents', ['agent_type', 'priority'])
task_completed_counter = Counter('agent_tasks_completed_total', 'Total tasks completed by agents', ['agent_type', 'status'])
task_failed_counter = Counter('agent_tasks_failed_total', 'Total tasks failed', ['agent_type', 'reason'])
agent_utilization_gauge = Gauge('agent_utilization_ratio', 'Agent utilization ratio', ['agent_type'])
task_duration_histogram = Histogram('agent_task_duration_seconds', 'Task duration in seconds', 
                                  ['agent_type'], buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300])
task_queue_depth_gauge = Gauge('task_queue_depth', 'Current task queue depth', ['priority'])
task_queue_duration_histogram = Histogram('task_queue_duration_seconds', 'Time spent in queue')
pending_tasks_per_agent_gauge = Gauge('pending_tasks_per_agent', 'Pending tasks per agent type', ['agent_type'])
task_assignment_latency = Summary('task_assignment_latency_seconds', 'Task assignment latency')
dag_critical_path_length = Gauge('dag_critical_path_length', 'DAG critical path length')
agent_pool_size_gauge = Gauge('agent_pool_size', 'Current agent pool size', ['agent_type'])
task_throughput_rate = Counter('task_throughput_total', 'Task throughput rate', ['agent_type'])
load_shedding_counter = Counter('load_shedding_total', 'Tasks rejected due to load shedding')


class TaskPriority(Enum):
    """Enhanced task priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class AgentStatus(Enum):
    """Agent availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    DRAINING = "draining"  # Preparing to shut down


@dataclass(order=True)
class EnhancedAgentTask:
    """Enhanced task object with additional metadata"""
    priority: int = field(compare=True)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()), compare=False)
    task_type: str = field(default=None, compare=False)
    payload: Dict[str, Any] = field(default_factory=dict, compare=False)
    dependencies: List[str] = field(default_factory=list, compare=False)
    created_at: datetime = field(default_factory=datetime.utcnow, compare=False)
    assigned_to: Optional[str] = field(default=None, compare=False)
    context_keys: List[str] = field(default_factory=list, compare=False)
    retry_count: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)
    
    # Enhanced fields
    estimated_complexity: float = field(default=1.0, compare=False)
    deadline: Optional[datetime] = field(default=None, compare=False)
    cost_budget: Optional[float] = field(default=None, compare=False)
    parent_task_id: Optional[str] = field(default=None, compare=False)
    idempotency_key: Optional[str] = field(default=None, compare=False)
    checkpoint_data: Optional[Dict[str, Any]] = field(default=None, compare=False)
    enqueued_at: Optional[datetime] = field(default=None, compare=False)
    started_at: Optional[datetime] = field(default=None, compare=False)
    completed_at: Optional[datetime] = field(default=None, compare=False)
    trace_id: Optional[str] = field(default=None, compare=False)
    span_id: Optional[str] = field(default=None, compare=False)


@dataclass
class EnhancedAgentInstance:
    """Enhanced agent instance with additional capabilities"""
    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    current_task: Optional[str] = None
    capabilities: Set[str] = field(default_factory=set)
    performance_score: float = 1.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_task_time: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    grpc_endpoint: Optional[str] = None
    
    # Enhanced fields
    cost_factor: float = 1.0
    current_capacity: float = 1.0
    max_concurrent_tasks: int = 1
    active_tasks: Set[str] = field(default_factory=set)
    error_rate: float = 0.0
    circuit_breaker: Optional[CircuitBreaker] = None
    region: str = "default"
    specializations: Set[str] = field(default_factory=set)
    resource_usage: Dict[str, float] = field(default_factory=dict)


class TaskDAG:
    """Directed Acyclic Graph for task dependencies and optimization"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.task_durations: Dict[str, float] = {}
        
    def add_task(self, task_id: str, estimated_duration: float = 1.0):
        self.graph.add_node(task_id)
        self.task_durations[task_id] = estimated_duration
        
    def add_dependency(self, from_task: str, to_task: str):
        self.graph.add_edge(from_task, to_task)
        
    def get_critical_path(self) -> Tuple[List[str], float]:
        """Calculate critical path using longest path algorithm"""
        if not self.graph:
            return [], 0
            
        # Topological sort
        try:
            topo_order = list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            logger.error("Cycle detected in task DAG")
            return [], 0
            
        # Calculate longest path
        distances = {node: 0 for node in self.graph.nodes()}
        predecessors = {node: None for node in self.graph.nodes()}
        
        for node in topo_order:
            for successor in self.graph.successors(node):
                new_distance = distances[node] + self.task_durations.get(node, 1.0)
                if new_distance > distances[successor]:
                    distances[successor] = new_distance
                    predecessors[successor] = node
        
        # Find the longest path
        end_node = max(distances.items(), key=lambda x: x[1])[0]
        path = []
        current = end_node
        
        while current is not None:
            path.append(current)
            current = predecessors[current]
            
        path.reverse()
        return path, distances[end_node]
    
    def get_parallelizable_tasks(self) -> List[Set[str]]:
        """Get sets of tasks that can be executed in parallel"""
        levels = []
        remaining = set(self.graph.nodes())
        
        while remaining:
            # Find tasks with no dependencies in remaining set
            level = set()
            for task in remaining:
                predecessors = set(self.graph.predecessors(task))
                if not predecessors.intersection(remaining):
                    level.add(task)
            
            if not level:
                break
                
            levels.append(level)
            remaining -= level
            
        return levels
    
    def should_cancel_descendants(self, failed_task: str) -> Set[str]:
        """Determine which tasks should be cancelled when a task fails"""
        return set(nx.descendants(self.graph, failed_task))


class EnhancedAgentManager:
    """
    Production-grade orchestrator with advanced features for high-scale operations.
    """
    
    def __init__(self):
        self.config = config
        self.agents: Dict[str, EnhancedAgentInstance] = {}
        
        # Enhanced task queues with priority and backpressure
        self.task_queues: Dict[TaskPriority, asyncio.Queue] = {}
        self.pending_tasks: Dict[str, EnhancedAgentTask] = {}
        self.completed_tasks: Dict[str, Any] = {}
        self.task_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Task DAG for optimization
        self.task_dag = TaskDAG()
        
        # Shared memory and communication
        self.memory_store = SharedMemoryStore(config.redis_url)
        self.agent_clients: Dict[str, AgentServiceClient] = {}
        
        # Database connection for exactly-once delivery
        self.db_pool: Optional[asyncpg.Pool] = None
        
        # Redis for dead-letter queue
        self.redis_client: Optional[redis.Redis] = None
        
        # Semaphore for concurrency control
        self.task_semaphore = Semaphore(config.performance.max_concurrent_tasks)
        
        # Circuit breakers for agents
        self.agent_circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Autoscaling state
        self.last_scaling_decision: Dict[AgentType, datetime] = {}
        self.scaling_metrics: Dict[AgentType, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Load shedding state
        self.load_shedding_active = False
        self.rejected_tasks_count = 0
        
        # Background tasks
        self._running = False
        self._task_processors: List[asyncio.Task] = []
        self._heartbeat_monitor_task = None
        self._autoscaler_task = None
        self._metrics_collector_task = None
        self._dag_optimizer_task = None
        
    async def initialize(self):
        """Initialize the enhanced agent manager"""
        try:
            # Initialize task queues
            for priority in TaskPriority:
                self.task_queues[priority] = asyncio.Queue(
                    maxsize=config.performance.task_queue_size // len(TaskPriority)
                )
            
            # Connect to shared memory
            await self.memory_store.connect()
            
            # Initialize database pool for exactly-once delivery
            if config.fault_tolerance.enable_exactly_once_delivery:
                self.db_pool = await asyncpg.create_pool(
                    config.postgres_url,
                    min_size=10,
                    max_size=config.performance.connection_pool_size
                )
                await self._init_database_schema()
            
            # Initialize Redis for dead-letter queue
            if config.fault_tolerance.enable_dead_letter_queue:
                self.redis_client = await redis.from_url(
                    config.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            
            self._running = True
            
            # Start multiple task processors for parallelism
            num_processors = min(config.performance.max_concurrent_tasks // 100, 10)
            for i in range(num_processors):
                processor = asyncio.create_task(self._process_tasks(i))
                self._task_processors.append(processor)
            
            # Start background tasks
            self._heartbeat_monitor_task = asyncio.create_task(self._monitor_agent_heartbeats())
            self._autoscaler_task = asyncio.create_task(self._autoscale_agents())
            self._metrics_collector_task = asyncio.create_task(self._collect_metrics())
            self._dag_optimizer_task = asyncio.create_task(self._optimize_dag())
            
            logger.info("Enhanced Agent Manager initialized", 
                       num_processors=num_processors,
                       max_concurrent_tasks=config.performance.max_concurrent_tasks)
            
        except Exception as e:
            logger.error("Failed to initialize agent manager", error=str(e))
            raise
    
    async def _init_database_schema(self):
        """Initialize database schema for task tracking"""
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id UUID PRIMARY KEY,
                    idempotency_key VARCHAR(255) UNIQUE,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    assigned_to UUID,
                    completed_at TIMESTAMP,
                    result JSONB,
                    error TEXT,
                    checkpoint_data JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_idempotency ON tasks(idempotency_key);
                CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
            ''')
    
    @asynccontextmanager
    async def _acquire_task_lock(self, task_id: str):
        """Acquire advisory lock for task assignment (exactly-once delivery)"""
        if not self.db_pool:
            yield True
            return
            
        async with self.db_pool.acquire() as conn:
            # Use PostgreSQL advisory locks
            lock_id = int(uuid.UUID(task_id).int % 2**31)
            acquired = await conn.fetchval(
                'SELECT pg_try_advisory_xact_lock($1)',
                lock_id
            )
            
            if acquired:
                yield True
            else:
                yield False
    
    async def submit_task(self,
                         task_type: str,
                         payload: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.NORMAL,
                         dependencies: List[str] = None,
                         context_keys: List[str] = None,
                         estimated_complexity: float = 1.0,
                         deadline: Optional[datetime] = None,
                         idempotency_key: Optional[str] = None,
                         parent_task_id: Optional[str] = None) -> str:
        """Submit a new task with enhanced features"""
        
        # Check for load shedding
        if self._should_shed_load():
            load_shedding_counter.inc()
            raise Exception("System overloaded, task rejected")
        
        # Check idempotency
        if idempotency_key and self.db_pool:
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchrow(
                    'SELECT task_id FROM tasks WHERE idempotency_key = $1',
                    idempotency_key
                )
                if existing:
                    return str(existing['task_id'])
        
        # Create task with tracing context
        task = EnhancedAgentTask(
            priority=priority.value,
            task_type=task_type,
            payload=payload,
            dependencies=dependencies or [],
            context_keys=context_keys or [],
            estimated_complexity=estimated_complexity,
            deadline=deadline,
            idempotency_key=idempotency_key,
            parent_task_id=parent_task_id,
            enqueued_at=datetime.utcnow()
        )
        
        # Add tracing context if available
        if tracer:
            ctx = trace.get_current_span().get_span_context()
            task.trace_id = format(ctx.trace_id, '032x')
            task.span_id = format(ctx.span_id, '016x')
        
        # Store in database for persistence
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO tasks (task_id, idempotency_key, status, created_at)
                    VALUES ($1, $2, $3, $4)
                ''', uuid.UUID(task.task_id), idempotency_key, 'pending', task.created_at)
        
        self.pending_tasks[task.task_id] = task
        
        # Add to DAG
        self.task_dag.add_task(task.task_id, estimated_complexity)
        for dep_id in task.dependencies:
            self.task_dependencies[dep_id].add(task.task_id)
            self.task_dag.add_dependency(dep_id, task.task_id)
        
        # Check if task can be queued immediately
        if not task.dependencies or all(dep in self.completed_tasks for dep in task.dependencies):
            await self._enqueue_task(task)
        
        # Update metrics
        task_queue_depth_gauge.labels(priority=priority.name).inc()
        
        logger.info("Task submitted", 
                   task_id=task.task_id,
                   task_type=task_type,
                   priority=priority.name,
                   complexity=estimated_complexity)
        
        return task.task_id
    
    async def _enqueue_task(self, task: EnhancedAgentTask):
        """Enqueue task with priority and backpressure handling"""
        priority = TaskPriority(task.priority)
        queue = self.task_queues[priority]
        
        # Apply backpressure if queue is full
        if queue.full():
            # Try higher priority queue
            for higher_priority in TaskPriority:
                if higher_priority.value < priority.value:
                    higher_queue = self.task_queues[higher_priority]
                    if not higher_queue.full():
                        task.priority = higher_priority.value
                        await higher_queue.put(task)
                        return
            
            # If all queues full, wait with timeout
            try:
                await asyncio.wait_for(queue.put(task), timeout=5.0)
            except asyncio.TimeoutError:
                await self._send_to_dead_letter_queue(task, "Queue full timeout")
                raise
        else:
            await queue.put(task)
    
    def _should_shed_load(self) -> bool:
        """Determine if load shedding should be activated"""
        if not config.performance.enable_load_shedding:
            return False
            
        # Calculate system load
        total_queued = sum(q.qsize() for q in self.task_queues.values())
        total_capacity = sum(q.maxsize for q in self.task_queues.values())
        
        load_ratio = total_queued / total_capacity if total_capacity > 0 else 0
        
        if load_ratio > config.performance.load_shedding_threshold:
            if not self.load_shedding_active:
                logger.warning("Load shedding activated", load_ratio=load_ratio)
                self.load_shedding_active = True
            return True
        elif load_ratio < config.performance.load_shedding_threshold * 0.8:
            if self.load_shedding_active:
                logger.info("Load shedding deactivated", load_ratio=load_ratio)
                self.load_shedding_active = False
            return False
        
        return self.load_shedding_active
    
    async def _process_tasks(self, processor_id: int):
        """Enhanced task processor with advanced features"""
        logger.info(f"Task processor {processor_id} started")
        
        while self._running:
            try:
                # Process tasks from all priority queues
                task = None
                for priority in TaskPriority:
                    queue = self.task_queues[priority]
                    if not queue.empty():
                        task = await queue.get()
                        break
                
                if not task:
                    await asyncio.sleep(0.1)
                    continue
                
                # Acquire semaphore for concurrency control
                async with self.task_semaphore:
                    # Start span for task processing
                    span_name = f"process_task_{task.task_type}"
                    if tracer and task.trace_id:
                        # Continue trace from task submission
                        ctx = trace.SpanContext(
                            trace_id=int(task.trace_id, 16),
                            span_id=int(task.span_id, 16),
                            is_remote=True,
                            trace_flags=trace.TraceFlags(0x01)
                        )
                        with tracer.start_as_current_span(span_name, context=ctx) as span:
                            await self._process_single_task(task, span)
                    else:
                        await self._process_single_task(task, None)
                        
            except Exception as e:
                logger.error(f"Error in task processor {processor_id}", error=str(e))
                await asyncio.sleep(1)
    
    async def _process_single_task(self, task: EnhancedAgentTask, span: Optional[trace.Span]):
        """Process a single task with full error handling and observability"""
        start_time = time.time()
        
        try:
            # Record queue time
            if task.enqueued_at:
                queue_time = (datetime.utcnow() - task.enqueued_at).total_seconds()
                task_queue_duration_histogram.observe(queue_time)
                if span:
                    span.set_attribute("queue_time_seconds", queue_time)
            
            # Find suitable agent based on scheduling strategy
            agent = await self._select_agent(task)
            
            if not agent:
                # No available agent, retry later
                task.retry_count += 1
                if task.retry_count < task.max_retries:
                    await asyncio.sleep(min(2 ** task.retry_count, 60))
                    await self._enqueue_task(task)
                else:
                    await self._handle_task_failure(task, "No available agents", span)
                return
            
            # Assign task with exactly-once semantics
            async with self._acquire_task_lock(task.task_id) as lock_acquired:
                if not lock_acquired:
                    logger.warning("Failed to acquire task lock", task_id=task.task_id)
                    return
                
                await self._assign_task_to_agent(task, agent, span)
                
        except Exception as e:
            logger.error("Task processing failed", task_id=task.task_id, error=str(e))
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
            await self._handle_task_failure(task, str(e), span)
        finally:
            # Record assignment latency
            assignment_time = time.time() - start_time
            task_assignment_latency.observe(assignment_time)
            if span:
                span.set_attribute("assignment_latency_seconds", assignment_time)
    
    async def _select_agent(self, task: EnhancedAgentTask) -> Optional[EnhancedAgentInstance]:
        """Select agent based on configured scheduling strategy"""
        strategy = config.scheduling_strategy
        
        if strategy == SchedulingStrategy.COST_BASED and config.feature_flags["cost_based_scheduling"]:
            return await self._cost_based_scheduling(task)
        elif strategy == SchedulingStrategy.PERFORMANCE_BASED:
            return self._performance_based_scheduling(task)
        elif strategy == SchedulingStrategy.ROUND_ROBIN:
            return self._round_robin_scheduling(task)
        else:
            return self._least_busy_scheduling(task)
    
    async def _cost_based_scheduling(self, task: EnhancedAgentTask) -> Optional[EnhancedAgentInstance]:
        """Cost-optimized agent selection"""
        eligible_agents = self._get_eligible_agents(task.task_type)
        if not eligible_agents:
            return None
        
        # Calculate cost score for each agent
        def cost_score(agent: EnhancedAgentInstance) -> float:
            # Factor in: cost per hour, current utilization, estimated task time
            base_cost = agent.cost_factor
            utilization_penalty = len(agent.active_tasks) / agent.max_concurrent_tasks
            complexity_factor = task.estimated_complexity
            
            # Estimate task completion time based on agent's average
            estimated_time = agent.average_task_time * complexity_factor
            
            # Total cost = hourly rate * estimated hours * utilization penalty
            total_cost = base_cost * (estimated_time / 3600) * (1 + utilization_penalty)
            
            # Apply deadline penalty if applicable
            if task.deadline:
                time_to_deadline = (task.deadline - datetime.utcnow()).total_seconds()
                if estimated_time > time_to_deadline * 0.8:
                    total_cost *= 2  # Penalty for tight deadline
            
            return total_cost
        
        # Select agent with lowest cost score
        return min(eligible_agents, key=cost_score)
    
    def _performance_based_scheduling(self, task: EnhancedAgentTask) -> Optional[EnhancedAgentInstance]:
        """Performance-optimized agent selection"""
        eligible_agents = self._get_eligible_agents(task.task_type)
        if not eligible_agents:
            return None
        
        # Select agent with best performance score and capacity
        return max(eligible_agents, 
                  key=lambda a: (a.performance_score * a.current_capacity, 
                               -a.error_rate,
                               -len(a.active_tasks)))
    
    def _round_robin_scheduling(self, task: EnhancedAgentTask) -> Optional[EnhancedAgentInstance]:
        """Simple round-robin scheduling"""
        eligible_agents = self._get_eligible_agents(task.task_type)
        if not eligible_agents:
            return None
        
        # Sort by tasks completed to ensure even distribution
        return min(eligible_agents, key=lambda a: a.tasks_completed)
    
    def _least_busy_scheduling(self, task: EnhancedAgentTask) -> Optional[EnhancedAgentInstance]:
        """Select least busy agent"""
        eligible_agents = self._get_eligible_agents(task.task_type)
        if not eligible_agents:
            return None
        
        return min(eligible_agents, key=lambda a: len(a.active_tasks) / a.max_concurrent_tasks)
    
    def _get_eligible_agents(self, task_type: str) -> List[EnhancedAgentInstance]:
        """Get agents eligible for a task type"""
        eligible_agent_types = self.task_routing_rules.get(task_type, [])
        
        agents = []
        for agent in self.agents.values():
            if (agent.agent_type in eligible_agent_types and
                agent.status in [AgentStatus.AVAILABLE, AgentStatus.BUSY] and
                task_type in agent.capabilities and
                len(agent.active_tasks) < agent.max_concurrent_tasks):
                
                # Check circuit breaker if enabled
                if agent.circuit_breaker and agent.circuit_breaker.is_open:
                    continue
                    
                agents.append(agent)
        
        return agents
    
    async def _assign_task_to_agent(self, 
                                   task: EnhancedAgentTask, 
                                   agent: EnhancedAgentInstance,
                                   span: Optional[trace.Span]):
        """Assign task to agent with full tracking"""
        task.assigned_to = agent.agent_id
        task.started_at = datetime.utcnow()
        agent.active_tasks.add(task.task_id)
        
        # Update database
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE tasks 
                    SET status = 'assigned', assigned_to = $1 
                    WHERE task_id = $2
                ''', uuid.UUID(agent.agent_id), uuid.UUID(task.task_id))
        
        # Update metrics
        task_assigned_counter.labels(
            agent_type=agent.agent_type.value,
            priority=TaskPriority(task.priority).name
        ).inc()
        pending_tasks_per_agent_gauge.labels(agent_type=agent.agent_type.value).inc()
        
        # Load context from shared memory
        context = {}
        for key in task.context_keys:
            value = await self.memory_store.get(key)
            if value:
                context[key] = value
        
        # Add parent task results if available
        if task.parent_task_id and task.parent_task_id in self.completed_tasks:
            context['parent_result'] = self.completed_tasks[task.parent_task_id]
        
        # Execute task via gRPC with circuit breaker
        if agent.agent_id in self.agent_clients:
            try:
                # Apply circuit breaker pattern
                if agent.circuit_breaker:
                    if not await agent.circuit_breaker.call_async(
                        self._execute_task_on_agent,
                        agent, task, context, span
                    ):
                        raise Exception("Circuit breaker open")
                else:
                    await self._execute_task_on_agent(agent, task, context, span)
                    
            except Exception as e:
                logger.error("Agent task execution failed",
                           agent_id=agent.agent_id,
                           task_id=task.task_id,
                           error=str(e))
                
                # Update agent error rate
                agent.tasks_failed += 1
                agent.error_rate = agent.tasks_failed / (agent.tasks_completed + agent.tasks_failed)
                
                await self._handle_task_failure(task, str(e), span)
    
    async def _execute_task_on_agent(self,
                                    agent: EnhancedAgentInstance,
                                    task: EnhancedAgentTask,
                                    context: Dict[str, Any],
                                    span: Optional[trace.Span]):
        """Execute task on agent with timeout and checkpointing"""
        client = self.agent_clients[agent.agent_id]
        
        # Set timeout based on task complexity and configuration
        timeout = min(
            config.fault_tolerance.task_timeout_seconds * task.estimated_complexity,
            3600  # Max 1 hour
        )
        
        # Add checkpointing if enabled
        checkpoint_task = None
        if config.fault_tolerance.enable_task_checkpointing:
            checkpoint_task = asyncio.create_task(
                self._checkpoint_task_periodically(task, agent)
            )
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                client.execute_task(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    payload=task.payload,
                    context=context,
                    checkpoint_data=task.checkpoint_data
                ),
                timeout=timeout
            )
            
            # Task completed successfully
            await self._handle_task_completion(task, agent, result, span)
            
        except asyncio.TimeoutError:
            logger.error("Task timeout", task_id=task.task_id, timeout=timeout)
            await self._handle_task_failure(task, f"Timeout after {timeout}s", span)
            
        finally:
            if checkpoint_task:
                checkpoint_task.cancel()
    
    async def _checkpoint_task_periodically(self, 
                                          task: EnhancedAgentTask,
                                          agent: EnhancedAgentInstance):
        """Periodically save task checkpoint data"""
        interval = config.fault_tolerance.checkpoint_interval_seconds
        
        while True:
            await asyncio.sleep(interval)
            
            try:
                # Get checkpoint from agent
                client = self.agent_clients[agent.agent_id]
                checkpoint = await client.get_task_checkpoint(task.task_id)
                
                if checkpoint:
                    task.checkpoint_data = checkpoint
                    
                    # Save to database
                    if self.db_pool:
                        async with self.db_pool.acquire() as conn:
                            await conn.execute('''
                                UPDATE tasks 
                                SET checkpoint_data = $1 
                                WHERE task_id = $2
                            ''', json.dumps(checkpoint), uuid.UUID(task.task_id))
                            
            except Exception as e:
                logger.warning("Failed to checkpoint task", 
                             task_id=task.task_id, 
                             error=str(e))
    
    async def _handle_task_completion(self,
                                     task: EnhancedAgentTask,
                                     agent: EnhancedAgentInstance,
                                     result: Any,
                                     span: Optional[trace.Span]):
        """Handle successful task completion"""
        task.completed_at = datetime.utcnow()
        duration = (task.completed_at - task.started_at).total_seconds()
        
        # Update agent statistics
        agent.active_tasks.remove(task.task_id)
        agent.tasks_completed += 1
        agent.average_task_time = (
            (agent.average_task_time * (agent.tasks_completed - 1) + duration)
            / agent.tasks_completed
        )
        agent.performance_score = min(1.0, agent.performance_score * 1.01)  # Improve score
        
        # Store result
        self.completed_tasks[task.task_id] = result
        del self.pending_tasks[task.task_id]
        
        # Update database
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE tasks 
                    SET status = 'completed', completed_at = $1, result = $2 
                    WHERE task_id = $3
                ''', task.completed_at, json.dumps(result), uuid.UUID(task.task_id))
        
        # Store result in shared memory if needed
        if "output_key" in task.payload:
            await self.memory_store.set(task.payload["output_key"], result)
        
        # Update metrics
        task_completed_counter.labels(
            agent_type=agent.agent_type.value,
            status='success'
        ).inc()
        task_duration_histogram.labels(agent_type=agent.agent_type.value).observe(duration)
        task_throughput_rate.labels(agent_type=agent.agent_type.value).inc()
        pending_tasks_per_agent_gauge.labels(agent_type=agent.agent_type.value).dec()
        
        # Process dependent tasks
        await self._process_dependent_tasks(task.task_id)
        
        # Update span
        if span:
            span.set_attribute("task_duration_seconds", duration)
            span.set_attribute("agent_id", agent.agent_id)
            span.set_status(Status(StatusCode.OK))
        
        logger.info("Task completed",
                   task_id=task.task_id,
                   agent_id=agent.agent_id,
                   duration=duration)
    
    async def _handle_task_failure(self,
                                  task: EnhancedAgentTask,
                                  error: str,
                                  span: Optional[trace.Span]):
        """Handle task failure with dead-letter queue support"""
        logger.error("Task failed", task_id=task.task_id, error=error)
        
        # Update metrics
        task_failed_counter.labels(
            agent_type=task.task_type,
            reason='error'
        ).inc()
        
        # Update span
        if span:
            span.set_status(Status(StatusCode.ERROR, error))
        
        # Check if should retry
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            logger.info("Retrying task", task_id=task.task_id, retry=task.retry_count)
            
            # Exponential backoff
            await asyncio.sleep(min(2 ** task.retry_count, 60))
            await self._enqueue_task(task)
        else:
            # Send to dead-letter queue
            await self._send_to_dead_letter_queue(task, error)
            
            # Mark as failed
            self.completed_tasks[task.task_id] = {"error": error, "status": "failed"}
            del self.pending_tasks[task.task_id]
            
            # Update database
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    await conn.execute('''
                        UPDATE tasks 
                        SET status = 'failed', error = $1, completed_at = $2 
                        WHERE task_id = $3
                    ''', error, datetime.utcnow(), uuid.UUID(task.task_id))
            
            # Cancel dependent tasks if configured
            if config.feature_flags["dag_optimization"]:
                cancelled_tasks = self.task_dag.should_cancel_descendants(task.task_id)
                for cancelled_id in cancelled_tasks:
                    if cancelled_id in self.pending_tasks:
                        await self._cancel_task(cancelled_id, f"Parent task {task.task_id} failed")
    
    async def _send_to_dead_letter_queue(self, task: EnhancedAgentTask, error: str):
        """Send failed task to dead-letter queue for manual processing"""
        if not self.redis_client or not config.fault_tolerance.enable_dead_letter_queue:
            return
        
        try:
            # Serialize task with error information
            dlq_entry = {
                "task": task.__dict__,
                "error": error,
                "failed_at": datetime.utcnow().isoformat(),
                "retry_count": task.retry_count
            }
            
            # Add to Redis stream
            await self.redis_client.xadd(
                "task_dead_letter_queue",
                {"data": json.dumps(dlq_entry, default=str)}
            )
            
            logger.info("Task sent to dead-letter queue", task_id=task.task_id)
            
        except Exception as e:
            logger.error("Failed to send task to DLQ", task_id=task.task_id, error=str(e))
    
    async def _cancel_task(self, task_id: str, reason: str):
        """Cancel a pending task"""
        if task_id not in self.pending_tasks:
            return
        
        task = self.pending_tasks[task_id]
        
        # Mark as cancelled
        self.completed_tasks[task_id] = {"status": "cancelled", "reason": reason}
        del self.pending_tasks[task_id]
        
        # Update database
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE tasks 
                    SET status = 'cancelled', error = $1, completed_at = $2 
                    WHERE task_id = $3
                ''', reason, datetime.utcnow(), uuid.UUID(task_id))
        
        logger.info("Task cancelled", task_id=task_id, reason=reason)
    
    async def _process_dependent_tasks(self, completed_task_id: str):
        """Process tasks that depend on the completed task"""
        dependent_tasks = self.task_dependencies.get(completed_task_id, set())
        
        for dep_task_id in dependent_tasks:
            if dep_task_id in self.pending_tasks:
                task = self.pending_tasks[dep_task_id]
                
                # Check if all dependencies are satisfied
                if all(dep in self.completed_tasks for dep in task.dependencies):
                    await self._enqueue_task(task)
    
    async def _monitor_agent_heartbeats(self):
        """Enhanced heartbeat monitoring with health checks"""
        while self._running:
            try:
                current_time = datetime.utcnow()
                
                for agent in list(self.agents.values()):
                    time_since_heartbeat = (current_time - agent.last_heartbeat).total_seconds()
                    
                    # Perform health check if configured
                    if (config.fault_tolerance.enable_circuit_breaker and 
                        agent.agent_id in self.agent_clients):
                        
                        try:
                            # gRPC health check
                            client = self.agent_clients[agent.agent_id]
                            health_status = await asyncio.wait_for(
                                client.check_health(),
                                timeout=5.0
                            )
                            
                            if health_status.status == "SERVING":
                                agent.last_heartbeat = current_time
                                if agent.status == AgentStatus.OFFLINE:
                                    agent.status = AgentStatus.AVAILABLE
                                    logger.info("Agent back online", agent_id=agent.agent_id)
                            else:
                                agent.status = AgentStatus.ERROR
                                
                        except Exception as e:
                            logger.warning("Agent health check failed", 
                                         agent_id=agent.agent_id, 
                                         error=str(e))
                    
                    # Mark offline if no heartbeat
                    if (time_since_heartbeat > config.agent_heartbeat_timeout and 
                        agent.status != AgentStatus.OFFLINE):
                        
                        logger.warning("Agent offline", agent_id=agent.agent_id)
                        agent.status = AgentStatus.OFFLINE
                        
                        # Reassign active tasks
                        for task_id in list(agent.active_tasks):
                            if task_id in self.pending_tasks:
                                task = self.pending_tasks[task_id]
                                task.assigned_to = None
                                agent.active_tasks.remove(task_id)
                                await self._enqueue_task(task)
                
                await asyncio.sleep(config.agent_health_check_interval)
                
            except Exception as e:
                logger.error("Error in heartbeat monitor", error=str(e))
                await asyncio.sleep(10)
    
    async def _autoscale_agents(self):
        """Dynamic autoscaling based on load and performance"""
        while self._running:
            try:
                if not config.autoscaling.enabled:
                    await asyncio.sleep(60)
                    continue
                
                current_time = datetime.utcnow()
                
                for agent_type in AgentType:
                    # Check cooldown
                    last_decision = self.last_scaling_decision.get(agent_type)
                    if (last_decision and 
                        (current_time - last_decision).total_seconds() < config.autoscaling.cooldown_seconds):
                        continue
                    
                    # Calculate scaling metrics
                    agents_of_type = [a for a in self.agents.values() if a.agent_type == agent_type]
                    if not agents_of_type:
                        continue
                    
                    # Calculate average utilization
                    total_active = sum(len(a.active_tasks) for a in agents_of_type)
                    total_capacity = sum(a.max_concurrent_tasks for a in agents_of_type)
                    utilization = total_active / total_capacity if total_capacity > 0 else 0
                    
                    # Calculate pending tasks for this agent type
                    pending_count = sum(1 for t in self.pending_tasks.values() 
                                      if t.task_type in self._get_task_types_for_agent(agent_type))
                    
                    # Calculate pending tasks per agent
                    pending_per_agent = pending_count / len(agents_of_type) if agents_of_type else 0
                    
                    # Update metrics for HPA
                    pending_tasks_per_agent_gauge.labels(agent_type=agent_type.value).set(pending_per_agent)
                    agent_pool_size_gauge.labels(agent_type=agent_type.value).set(len(agents_of_type))
                    
                    # Store metrics for decision making
                    self.scaling_metrics[agent_type].append({
                        'timestamp': current_time,
                        'utilization': utilization,
                        'pending_per_agent': pending_per_agent,
                        'agent_count': len(agents_of_type)
                    })
                    
                    # Make scaling decision
                    should_scale_up = (
                        utilization > config.autoscaling.scale_up_threshold or
                        pending_per_agent > config.autoscaling.target_queue_depth
                    )
                    
                    should_scale_down = (
                        utilization < config.autoscaling.scale_down_threshold and
                        pending_per_agent < config.autoscaling.target_queue_depth * 0.5 and
                        len(agents_of_type) > config.autoscaling.min_agents_per_type
                    )
                    
                    if should_scale_up:
                        # Check cost constraints
                        if config.autoscaling.cost_optimization_enabled:
                            current_cost = self._calculate_current_hourly_cost()
                            agent_cost = config.autoscaling.agent_cost_per_hour.get(
                                agent_type.value, 10.0
                            )
                            
                            if current_cost + agent_cost > config.autoscaling.max_hourly_cost:
                                logger.warning("Scaling up blocked by cost constraint",
                                             agent_type=agent_type.value,
                                             current_cost=current_cost)
                                continue
                        
                        # Scale up
                        scale_count = min(
                            config.autoscaling.scale_up_rate,
                            config.autoscaling.max_agents_per_type - len(agents_of_type)
                        )
                        
                        for _ in range(scale_count):
                            await self._spawn_new_agent(agent_type)
                        
                        self.last_scaling_decision[agent_type] = current_time
                        logger.info("Scaled up agents",
                                   agent_type=agent_type.value,
                                   count=scale_count,
                                   utilization=utilization,
                                   pending_per_agent=pending_per_agent)
                        
                    elif should_scale_down:
                        # Scale down
                        scale_count = min(
                            config.autoscaling.scale_down_rate,
                            len(agents_of_type) - config.autoscaling.min_agents_per_type
                        )
                        
                        # Select least busy agents for removal
                        agents_to_remove = sorted(
                            agents_of_type,
                            key=lambda a: len(a.active_tasks)
                        )[:scale_count]
                        
                        for agent in agents_to_remove:
                            agent.status = AgentStatus.DRAINING
                            asyncio.create_task(self._drain_and_remove_agent(agent.agent_id))
                        
                        self.last_scaling_decision[agent_type] = current_time
                        logger.info("Scaled down agents",
                                   agent_type=agent_type.value,
                                   count=scale_count,
                                   utilization=utilization)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error("Error in autoscaler", error=str(e))
                await asyncio.sleep(60)
    
    def _calculate_current_hourly_cost(self) -> float:
        """Calculate current hourly cost of all agents"""
        total_cost = 0.0
        
        for agent in self.agents.values():
            agent_cost = config.autoscaling.agent_cost_per_hour.get(
                agent.agent_type.value, 10.0
            )
            total_cost += agent_cost
        
        return total_cost
    
    def _get_task_types_for_agent(self, agent_type: AgentType) -> Set[str]:
        """Get task types that can be handled by an agent type"""
        task_types = set()
        
        for task_type, agent_types in self.task_routing_rules.items():
            if agent_type in agent_types:
                task_types.add(task_type)
        
        return task_types
    
    async def _spawn_new_agent(self, agent_type: AgentType):
        """Spawn a new agent instance (placeholder for actual implementation)"""
        # In production, this would:
        # 1. Start a new pod/container via Kubernetes API
        # 2. Wait for it to be ready
        # 3. Register it with the orchestrator
        
        logger.info("Spawning new agent", agent_type=agent_type.value)
        # Placeholder - actual implementation would interact with k8s
    
    async def _drain_and_remove_agent(self, agent_id: str):
        """Gracefully drain and remove an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        # Wait for active tasks to complete
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while agent.active_tasks and (time.time() - start_time) < max_wait:
            await asyncio.sleep(5)
        
        # Force reassign any remaining tasks
        for task_id in list(agent.active_tasks):
            if task_id in self.pending_tasks:
                task = self.pending_tasks[task_id]
                task.assigned_to = None
                agent.active_tasks.remove(task_id)
                await self._enqueue_task(task)
        
        # Unregister agent
        await self.unregister_agent(agent_id)
        
        logger.info("Agent drained and removed", agent_id=agent_id)
    
    async def _collect_metrics(self):
        """Collect and update various metrics"""
        while self._running:
            try:
                # Update queue depth metrics
                for priority in TaskPriority:
                    queue = self.task_queues[priority]
                    task_queue_depth_gauge.labels(priority=priority.name).set(queue.qsize())
                
                # Update agent utilization
                for agent_type in AgentType:
                    agents_of_type = [a for a in self.agents.values() if a.agent_type == agent_type]
                    if agents_of_type:
                        total_active = sum(len(a.active_tasks) for a in agents_of_type)
                        total_capacity = sum(a.max_concurrent_tasks for a in agents_of_type)
                        utilization = total_active / total_capacity if total_capacity > 0 else 0
                        agent_utilization_gauge.labels(agent_type=agent_type.value).set(utilization)
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error("Error collecting metrics", error=str(e))
                await asyncio.sleep(30)
    
    async def _optimize_dag(self):
        """Continuously optimize task DAG"""
        while self._running:
            try:
                if not config.feature_flags["dag_optimization"]:
                    await asyncio.sleep(60)
                    continue
                
                # Calculate critical path
                if self.task_dag.graph:
                    critical_path, path_length = self.task_dag.get_critical_path()
                    dag_critical_path_length.set(path_length)
                    
                    # Log if critical path is too long
                    if path_length > 100:
                        logger.warning("Long critical path detected",
                                     length=path_length,
                                     path=critical_path[:10])  # First 10 tasks
                
                # Identify parallelizable tasks
                parallel_groups = self.task_dag.get_parallelizable_tasks()
                
                # Gang schedule if enabled
                if config.enable_gang_scheduling and parallel_groups:
                    for group in parallel_groups:
                        # Find tasks in the group that are pending
                        pending_in_group = [
                            task_id for task_id in group 
                            if task_id in self.pending_tasks and 
                            self.pending_tasks[task_id].assigned_to is None
                        ]
                        
                        if len(pending_in_group) > 1:
                            # Try to assign to agents in the same region/cluster
                            await self._gang_schedule_tasks(pending_in_group)
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error("Error in DAG optimizer", error=str(e))
                await asyncio.sleep(60)
    
    async def _gang_schedule_tasks(self, task_ids: List[str]):
        """Schedule related tasks together for better performance"""
        # Group tasks by type
        tasks_by_type = defaultdict(list)
        for task_id in task_ids:
            task = self.pending_tasks.get(task_id)
            if task:
                tasks_by_type[task.task_type].append(task)
        
        # Try to assign tasks of the same type to the same agent
        for task_type, tasks in tasks_by_type.items():
            eligible_agents = self._get_eligible_agents(task_type)
            
            # Sort by available capacity
            eligible_agents.sort(
                key=lambda a: a.max_concurrent_tasks - len(a.active_tasks),
                reverse=True
            )
            
            # Assign tasks to agents with most capacity
            for task in tasks:
                if eligible_agents:
                    agent = eligible_agents[0]
                    if len(agent.active_tasks) < agent.max_concurrent_tasks:
                        await self._assign_task_to_agent(task, agent, None)
                    else:
                        # Move to next agent
                        eligible_agents.pop(0)
                        if eligible_agents:
                            agent = eligible_agents[0]
                            await self._assign_task_to_agent(task, agent, None)
    
    async def register_agent(self,
                           agent_type: AgentType,
                           capabilities: Set[str],
                           grpc_endpoint: Optional[str] = None,
                           max_concurrent_tasks: int = 1,
                           cost_factor: float = 1.0,
                           region: str = "default") -> str:
        """Register an enhanced agent with the orchestrator"""
        agent_id = str(uuid.uuid4())
        
        # Create circuit breaker if enabled
        circuit_breaker = None
        if config.fault_tolerance.enable_circuit_breaker:
            circuit_breaker = CircuitBreaker(
                failure_threshold=config.fault_tolerance.circuit_breaker_threshold,
                recovery_timeout=config.fault_tolerance.circuit_breaker_timeout,
                expected_exception=Exception
            )
        
        agent = EnhancedAgentInstance(
            agent_id=agent_id,
            agent_type=agent_type,
            status=AgentStatus.AVAILABLE,
            capabilities=capabilities,
            grpc_endpoint=grpc_endpoint,
            max_concurrent_tasks=max_concurrent_tasks,
            cost_factor=cost_factor,
            circuit_breaker=circuit_breaker,
            region=region
        )
        
        self.agents[agent_id] = agent
        
        # Initialize gRPC client if endpoint provided
        if grpc_endpoint:
            self.agent_clients[agent_id] = AgentServiceClient(grpc_endpoint)
            await self.agent_clients[agent_id].connect()
        
        # Update metrics
        agent_pool_size_gauge.labels(agent_type=agent_type.value).inc()
        
        logger.info("Enhanced agent registered",
                   agent_id=agent_id,
                   agent_type=agent_type.value,
                   max_concurrent_tasks=max_concurrent_tasks,
                   cost_factor=cost_factor)
        
        return agent_id
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the orchestrator"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        
        # Reassign any active tasks
        for task_id in list(agent.active_tasks):
            if task_id in self.pending_tasks:
                task = self.pending_tasks[task_id]
                task.assigned_to = None
                await self._enqueue_task(task)
        
        # Close gRPC connection
        if agent_id in self.agent_clients:
            await self.agent_clients[agent_id].close()
            del self.agent_clients[agent_id]
        
        # Update metrics
        agent_pool_size_gauge.labels(agent_type=agent.agent_type.value).dec()
        
        del self.agents[agent_id]
        logger.info("Agent unregistered", agent_id=agent_id)
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get enhanced task status with additional metadata"""
        # Check completed tasks
        if task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            status = "failed" if isinstance(result, dict) and "error" in result else "completed"
            
            # Get additional info from database
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        'SELECT * FROM tasks WHERE task_id = $1',
                        uuid.UUID(task_id)
                    )
                    if row:
                        return {
                            "status": status,
                            "result": result,
                            "created_at": row['created_at'].isoformat(),
                            "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None,
                            "assigned_to": str(row['assigned_to']) if row['assigned_to'] else None,
                            "checkpoint_data": row['checkpoint_data']
                        }
            
            return {
                "status": status,
                "result": result
            }
        
        # Check pending tasks
        elif task_id in self.pending_tasks:
            task = self.pending_tasks[task_id]
            return {
                "status": "processing" if task.assigned_to else "pending",
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
                "enqueued_at": task.enqueued_at.isoformat() if task.enqueued_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "retry_count": task.retry_count,
                "priority": TaskPriority(task.priority).name,
                "estimated_complexity": task.estimated_complexity
            }
        
        return None
    
    async def reprocess_dead_letter_task(self, dlq_entry_id: str) -> str:
        """Manually reprocess a task from the dead-letter queue"""
        if not self.redis_client:
            raise Exception("Dead-letter queue not enabled")
        
        # Read from DLQ
        entries = await self.redis_client.xread({f"task_dead_letter_queue": dlq_entry_id}, count=1)
        
        if not entries:
            raise Exception(f"DLQ entry {dlq_entry_id} not found")
        
        stream_name, messages = entries[0]
        entry_id, data = messages[0]
        
        # Deserialize task
        dlq_data = json.loads(data['data'])
        task_data = dlq_data['task']
        
        # Create new task with reset retry count
        task = EnhancedAgentTask(**task_data)
        task.retry_count = 0
        task.task_id = str(uuid.uuid4())  # New ID to avoid conflicts
        
        # Resubmit task
        self.pending_tasks[task.task_id] = task
        await self._enqueue_task(task)
        
        # Remove from DLQ
        await self.redis_client.xdel("task_dead_letter_queue", entry_id)
        
        logger.info("Reprocessed dead-letter task",
                   original_id=task_data['task_id'],
                   new_id=task.task_id)
        
        return task.task_id
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            "agents": {
                "total": len(self.agents),
                "by_status": defaultdict(int),
                "by_type": defaultdict(int),
                "by_region": defaultdict(int)
            },
            "tasks": {
                "pending": len(self.pending_tasks),
                "completed": len(self.completed_tasks),
                "in_queues": sum(q.qsize() for q in self.task_queues.values()),
                "by_priority": {p.name: self.task_queues[p].qsize() for p in TaskPriority}
            },
            "performance": {
                "avg_queue_depth": sum(q.qsize() for q in self.task_queues.values()) / len(self.task_queues),
                "load_shedding_active": self.load_shedding_active,
                "rejected_tasks": self.rejected_tasks_count,
                "critical_path_length": 0
            },
            "cost": {
                "hourly_cost": self._calculate_current_hourly_cost(),
                "cost_per_agent_type": {}
            }
        }
        
        # Agent statistics
        for agent in self.agents.values():
            stats["agents"]["by_status"][agent.status.value] += 1
            stats["agents"]["by_type"][agent.agent_type.value] += 1
            stats["agents"]["by_region"][agent.region] += 1
        
        # Cost breakdown
        for agent_type in AgentType:
            agent_count = stats["agents"]["by_type"].get(agent_type.value, 0)
            cost_per_hour = config.autoscaling.agent_cost_per_hour.get(agent_type.value, 10.0)
            stats["cost"]["cost_per_agent_type"][agent_type.value] = agent_count * cost_per_hour
        
        # Critical path
        if self.task_dag.graph:
            _, path_length = self.task_dag.get_critical_path()
            stats["performance"]["critical_path_length"] = path_length
        
        return stats
    
    async def shutdown(self):
        """Gracefully shutdown the enhanced agent manager"""
        logger.info("Shutting down Enhanced Agent Manager")
        self._running = False
        
        # Cancel all background tasks
        tasks_to_cancel = (
            self._task_processors +
            [self._heartbeat_monitor_task, self._autoscaler_task,
             self._metrics_collector_task, self._dag_optimizer_task]
        )
        
        for task in tasks_to_cancel:
            if task:
                task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        
        # Close connections
        await self.memory_store.disconnect()
        
        if self.db_pool:
            await self.db_pool.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        # Close all gRPC connections
        for client in self.agent_clients.values():
            await client.close()
        
        logger.info("Enhanced Agent Manager shutdown complete")


# Task routing rules (moved from base class)
task_routing_rules = {
    "frontend_development": [AgentType.CODE_GENERATOR, AgentType.TESTER],
    "backend_development": [AgentType.CODE_GENERATOR, AgentType.TESTER],
    "api_design": [AgentType.PLANNER, AgentType.CODE_GENERATOR],
    "database_design": [AgentType.PLANNER, AgentType.CODE_GENERATOR],
    "ui_design": [AgentType.PLANNER, AgentType.CODE_GENERATOR],
    "testing": [AgentType.TESTER],
    "documentation": [AgentType.DOC_GENERATOR],
    "code_review": [AgentType.REVIEWER],
    "deployment": [AgentType.PLANNER, AgentType.CODE_GENERATOR]
}