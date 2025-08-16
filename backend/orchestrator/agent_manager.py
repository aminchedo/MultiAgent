"""
Central Agent Orchestrator for Multi-Agent Collaboration Framework

This module implements the core orchestration logic for managing multiple AI agents,
handling task delegation, context sharing, and coordination.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import heapq
import json
from collections import defaultdict

import structlog
from asyncio import Queue, PriorityQueue
import redis.asyncio as redis
from prometheus_client import Counter, Gauge, Histogram
from opentelemetry import trace
from config.config import FEATURE_FLAGS


logger = structlog.get_logger()

# Metrics
task_assigned_counter = Counter('agent_tasks_assigned_total', 'Total tasks assigned to agents', ['agent_type'])
task_completed_counter = Counter('agent_tasks_completed_total', 'Total tasks completed by agents', ['agent_type'])
agent_utilization_gauge = Gauge('agent_utilization_ratio', 'Agent utilization ratio', ['agent_type'])
task_duration_histogram = Histogram('agent_task_duration_seconds', 'Task duration in seconds', ['agent_type'])
# New histogram to track queue latency
task_queue_duration_histogram = Histogram('task_queue_duration_seconds', 'Time tasks spend in queue', ['agent_type'])
# OpenTelemetry tracer
tracer = trace.get_tracer(__name__)


class TaskPriority(Enum):
    """Task priority levels for queue management"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class AgentStatus(Enum):
    """Agent availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass(order=True)
class AgentTask:
    """Task object for agent processing"""
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


@dataclass
class AgentInstance:
    """Represents an active agent instance"""
    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    current_task: Optional[str] = None
    capabilities: Set[str] = field(default_factory=set)
    performance_score: float = 1.0
    # Cost-based scheduling attributes
    cost_factor: float = 1.0
    current_capacity: int = 1
    tasks_completed: int = 0
    average_task_time: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    grpc_endpoint: Optional[str] = None


class AgentManager:
    """
    Central orchestrator for multi-agent collaboration.
    
    Manages task delegation, agent lifecycle, context sharing, and coordination.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.agents: Dict[str, AgentInstance] = {}
        self.task_queue: PriorityQueue[AgentTask] = PriorityQueue()
        self.pending_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, Any] = {}
        self.task_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Shared memory and communication
        self.memory_store = SharedMemoryStore(redis_url)
        self.agent_clients: Dict[str, AgentServiceClient] = {}
        # Redis client for dead-letter queue & autoscaling telemetry
        self.redis = redis.from_url(redis_url, decode_responses=True)
        
        # Task routing rules
        self.task_routing_rules: Dict[str, List[AgentType]] = {
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
        
        # Consensus voting weights
        self.agent_voting_weights: Dict[AgentType, float] = {
            AgentType.PLANNER: 1.5,
            AgentType.CODE_GENERATOR: 1.0,
            AgentType.TESTER: 1.2,
            AgentType.REVIEWER: 1.3,
            AgentType.DOC_GENERATOR: 0.8
        }
        
        self._running = False
        self._task_processor_task = None
        self._heartbeat_monitor_task = None
        self._autoscale_task = None
    
    async def initialize(self):
        """Initialize the agent manager and start background tasks"""
        await self.memory_store.connect()
        self._running = True
        
        # Start background tasks
        self._task_processor_task = asyncio.create_task(self._process_tasks())
        self._heartbeat_monitor_task = asyncio.create_task(self._monitor_agent_heartbeats())
        # Background autoscaling monitor
        self._autoscale_task = asyncio.create_task(self._autoscale_loop())
        
        logger.info("Agent Manager initialized")
    
    async def shutdown(self):
        """Shutdown the agent manager gracefully"""
        self._running = False
        
        if self._task_processor_task:
            self._task_processor_task.cancel()
        if self._heartbeat_monitor_task:
            self._heartbeat_monitor_task.cancel()
        if self._autoscale_task:
            self._autoscale_task.cancel()
            
        await self.memory_store.disconnect()
        
        # Close all gRPC connections
        for client in self.agent_clients.values():
            await client.close()
        
        logger.info("Agent Manager shutdown complete")
    
    async def register_agent(self, 
                           agent_type: AgentType,
                           capabilities: Set[str],
                           grpc_endpoint: Optional[str] = None) -> str:
        """Register a new agent with the orchestrator"""
        agent_id = str(uuid.uuid4())
        
        agent = AgentInstance(
            agent_id=agent_id,
            agent_type=agent_type,
            status=AgentStatus.AVAILABLE,
            capabilities=capabilities,
            grpc_endpoint=grpc_endpoint
        )
        
        self.agents[agent_id] = agent
        
        # Initialize gRPC client if endpoint provided
        if grpc_endpoint:
            self.agent_clients[agent_id] = AgentServiceClient(grpc_endpoint)
            await self.agent_clients[agent_id].connect()
        
        # Update metrics
        agent_utilization_gauge.labels(agent_type=agent_type.value).set(0.0)
        
        logger.info("Agent registered", agent_id=agent_id, agent_type=agent_type.value)
        return agent_id
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the orchestrator"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            
            # Reassign any current tasks
            if agent.current_task:
                task = self.pending_tasks.get(agent.current_task)
                if task:
                    task.assigned_to = None
                    await self.task_queue.put(task)
            
            # Close gRPC connection
            if agent_id in self.agent_clients:
                await self.agent_clients[agent_id].close()
                del self.agent_clients[agent_id]
            
            del self.agents[agent_id]
            logger.info("Agent unregistered", agent_id=agent_id)
    
    async def submit_task(self,
                         task_type: str,
                         payload: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.NORMAL,
                         dependencies: List[str] = None,
                         context_keys: List[str] = None) -> str:
        """Submit a new task for agent processing"""
        task = AgentTask(
            priority=priority.value,
            task_type=task_type,
            payload=payload,
            dependencies=dependencies or [],
            context_keys=context_keys or []
        )
        
        self.pending_tasks[task.task_id] = task
        
        # Track dependencies
        for dep_id in task.dependencies:
            self.task_dependencies[dep_id].add(task.task_id)
        
        # Check if task can be queued immediately
        if not task.dependencies or all(dep in self.completed_tasks for dep in task.dependencies):
            await self.task_queue.put(task)
        
        logger.info("Task submitted", 
                   task_id=task.task_id, 
                   task_type=task_type,
                   priority=priority.value)
        
        # Graceful degradation – drop or divert tasks when overloaded
        if self._is_overloaded():
            await self._dead_letter_task(task, reason="load_shedding")
            logger.warning("Load shedding triggered – task sent to dead-letter queue", task_id=task.task_id)
            return task.task_id
        
        return task.task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a task"""
        if task_id in self.completed_tasks:
            return {
                "status": "completed",
                "result": self.completed_tasks[task_id]
            }
        elif task_id in self.pending_tasks:
            task = self.pending_tasks[task_id]
            return {
                "status": "pending" if not task.assigned_to else "processing",
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat()
            }
        else:
            return None
    
    def get_least_busy_agent(self, task: AgentTask) -> Optional[AgentInstance]:
        """Select optimal agent for the given task (cost-based if flag enabled)"""
        eligible_agent_types = self.task_routing_rules.get(task.task_type, [])
        available_agents = [
            agent for agent in self.agents.values()
            if agent.agent_type in eligible_agent_types
            and agent.status == AgentStatus.AVAILABLE
            and task.task_type in agent.capabilities
        ]
        if not available_agents:
            return None
        if FEATURE_FLAGS.get("cost_based_scheduling", False):
            complexity = task.payload.get("estimated_complexity", 1.0)
            return min(available_agents, key=lambda a: a.cost_factor * complexity / max(a.current_capacity, 1))
        return max(available_agents, key=lambda a: (a.performance_score, -a.tasks_completed))
    
    async def _process_tasks(self):
        """Background task processor"""
        while self._running:
            try:
                # Get next task with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Find suitable agent
                agent = self.get_least_busy_agent(task)
                
                if agent:
                    # Assign task to agent
                    await self._assign_task_to_agent(task, agent)
                else:
                    # No available agent, retry later
                    task.retry_count += 1
                    if task.retry_count < task.max_retries:
                        await asyncio.sleep(5)  # Wait before retry
                        await self.task_queue.put(task)
                    else:
                        await self._handle_task_failure(task, "No available agents")
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Error processing tasks", error=str(e))
    
    async def _assign_task_to_agent(self, task: AgentTask, agent: AgentInstance):
        """Assign a task to a specific agent"""
        task.assigned_to = agent.agent_id
        agent.current_task = task.task_id
        agent.status = AgentStatus.BUSY
        
        # Update metrics
        task_assigned_counter.labels(agent_type=agent.agent_type.value).inc()
        agent_utilization_gauge.labels(agent_type=agent.agent_type.value).set(1.0)
        # Observability – queue latency & tracing
        queue_duration = (datetime.utcnow() - task.created_at).total_seconds()
        task_queue_duration_histogram.labels(agent_type=agent.agent_type.value).observe(queue_duration)
        span = tracer.start_span("assign_task")
        span.set_attribute("agent_type", agent.agent_type.value)
        span.set_attribute("task_type", task.task_type)
        span.set_attribute("task_id", task.task_id)
        span.set_attribute("queue_duration_seconds", queue_duration)
        
        # Load context from shared memory
        context = {}
        for key in task.context_keys:
            value = await self.memory_store.get(key)
            if value:
                context[key] = value
        
        # Send task to agent via gRPC
        if agent.agent_id in self.agent_clients:
            try:
                start_time = datetime.utcnow()
                
                result = await self.agent_clients[agent.agent_id].execute_task(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    payload=task.payload,
                    context=context
                )
                span.end()
                
                # Task completed successfully
                await self._handle_task_completion(task, agent, result, start_time)
                
            except Exception as e:
                logger.error("Agent task execution failed", 
                           agent_id=agent.agent_id,
                           task_id=task.task_id,
                           error=str(e))
                await self._handle_task_failure(task, str(e))
                span.record_exception(e)
                span.end()
        else:
            # Fallback to local execution (for backward compatibility)
            logger.warning("No gRPC client for agent, using local execution",
                         agent_id=agent.agent_id)
    
    async def _handle_task_completion(self, 
                                    task: AgentTask, 
                                    agent: AgentInstance,
                                    result: Any,
                                    start_time: datetime):
        """Handle successful task completion"""
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Update agent stats
        agent.status = AgentStatus.AVAILABLE
        agent.current_task = None
        agent.tasks_completed += 1
        agent.average_task_time = (
            (agent.average_task_time * (agent.tasks_completed - 1) + duration) 
            / agent.tasks_completed
        )
        
        # Store result
        self.completed_tasks[task.task_id] = result
        del self.pending_tasks[task.task_id]
        
        # Store result in shared memory if needed
        if "output_key" in task.payload:
            await self.memory_store.set(task.payload["output_key"], result)
        
        # Update metrics
        task_completed_counter.labels(agent_type=agent.agent_type.value).inc()
        task_duration_histogram.labels(agent_type=agent.agent_type.value).observe(duration)
        agent_utilization_gauge.labels(agent_type=agent.agent_type.value).set(0.0)
        
        # Process dependent tasks
        await self._process_dependent_tasks(task.task_id)
        
        logger.info("Task completed",
                   task_id=task.task_id,
                   agent_id=agent.agent_id,
                   duration=duration)
    
    async def _handle_task_failure(self, task: AgentTask, error: str):
        """Handle task failure"""
        logger.error("Task failed", task_id=task.task_id, error=error)
        
        # Mark as failed
        self.completed_tasks[task.task_id] = {"error": error, "status": "failed"}
        del self.pending_tasks[task.task_id]
        
        # Notify dependent tasks
        await self._process_dependent_tasks(task.task_id)
    
    async def _process_dependent_tasks(self, completed_task_id: str):
        """Process tasks that depend on the completed task"""
        dependent_tasks = self.task_dependencies.get(completed_task_id, set())
        
        for dep_task_id in dependent_tasks:
            if dep_task_id in self.pending_tasks:
                task = self.pending_tasks[dep_task_id]
                
                # Check if all dependencies are satisfied
                if all(dep in self.completed_tasks for dep in task.dependencies):
                    await self.task_queue.put(task)
    
    async def _monitor_agent_heartbeats(self):
        """Monitor agent heartbeats and mark offline agents"""
        while self._running:
            try:
                current_time = datetime.utcnow()
                
                for agent in self.agents.values():
                    time_since_heartbeat = (current_time - agent.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > 30 and agent.status != AgentStatus.OFFLINE:
                        logger.warning("Agent offline", agent_id=agent.agent_id)
                        agent.status = AgentStatus.OFFLINE
                        
                        # Reassign current task if any
                        if agent.current_task:
                            task = self.pending_tasks.get(agent.current_task)
                            if task:
                                task.assigned_to = None
                                await self.task_queue.put(task)
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error("Error in heartbeat monitor", error=str(e))
    
    async def update_agent_heartbeat(self, agent_id: str):
        """Update agent heartbeat timestamp"""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = datetime.utcnow()
            if self.agents[agent_id].status == AgentStatus.OFFLINE:
                self.agents[agent_id].status = AgentStatus.AVAILABLE
    
    async def resolve_conflict(self, 
                             proposals: Dict[str, Any],
                             context: Dict[str, Any]) -> Any:
        """
        Resolve conflicts between agent proposals using weighted voting.
        
        Args:
            proposals: Dict mapping agent_id to their proposals
            context: Additional context for decision making
            
        Returns:
            The winning proposal
        """
        if not proposals:
            return None
        
        if len(proposals) == 1:
            return next(iter(proposals.values()))
        
        # Calculate weighted scores
        scores = defaultdict(float)
        
        for agent_id, proposal in proposals.items():
            agent = self.agents.get(agent_id)
            if agent:
                weight = self.agent_voting_weights.get(agent.agent_type, 1.0)
                performance_factor = agent.performance_score
                
                # Hash proposal for comparison (simplified)
                proposal_key = json.dumps(proposal, sort_keys=True)
                scores[proposal_key] += weight * performance_factor
        
        # Return proposal with highest score
        winning_proposal = max(scores.items(), key=lambda x: x[1])[0]
        return json.loads(winning_proposal)
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get current statistics about agents and tasks"""
        stats = {
            "total_agents": len(self.agents),
            "available_agents": sum(1 for a in self.agents.values() if a.status == AgentStatus.AVAILABLE),
            "busy_agents": sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY),
            "offline_agents": sum(1 for a in self.agents.values() if a.status == AgentStatus.OFFLINE),
            "pending_tasks": len(self.pending_tasks),
            "completed_tasks": len(self.completed_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "agents_by_type": defaultdict(int)
        }
        
        for agent in self.agents.values():
            stats["agents_by_type"][agent.agent_type.value] += 1
        
        return stats

    def _is_overloaded(self) -> bool:
        """Return True when 90 % or more of agents are busy"""
        total = len(self.agents)
        if total == 0:
            return True
        busy = sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY)
        return busy / total >= 0.9

    async def _dead_letter_task(self, task: AgentTask, reason: str):
        """Push task to Redis dead-letter stream for later inspection"""
        await self.redis.xadd(
            "dead_letter_tasks",
            {
                "task_id": task.task_id,
                "reason": reason,
                "payload": json.dumps(task.payload),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def _get_avg_process_time(self, agent_type: AgentType) -> float:
        times = [a.average_task_time for a in self.agents.values() if a.agent_type == agent_type and a.tasks_completed > 0]
        return sum(times) / len(times) if times else 1.0

    def _should_scale(self, agent_type: AgentType) -> bool:
        pending = sum(
            1 for t in self.pending_tasks.values()
            if agent_type in self.task_routing_rules.get(t.task_type, [])
        )
        current_agents = sum(1 for a in self.agents.values() if a.agent_type == agent_type)
        avg_time = self._get_avg_process_time(agent_type)
        return pending > (current_agents * avg_time * 0.8)

    async def _autoscale_loop(self):
        """Monitor workload and suggest scaling actions"""
        while self._running:
            try:
                for agent_type in AgentType:
                    if self._should_scale(agent_type):
                        logger.info("Autoscale triggered", agent_type=agent_type.value)
                        # Integration hook for Kubernetes or external scaler goes here
                await asyncio.sleep(5)
            except Exception as e:
                logger.error("Autoscale loop error", error=str(e))