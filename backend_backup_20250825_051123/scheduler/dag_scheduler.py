"""
DAG-based Task Scheduler for Parallel Agent Execution

This module implements a Directed Acyclic Graph (DAG) scheduler for
optimizing parallel execution of agent tasks with dependency management.
"""

import asyncio
from typing import Dict, List, Set, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import networkx as nx
from collections import defaultdict, deque
import heapq
import uuid

import structlog
from prometheus_client import Counter, Gauge, Histogram

from backend.orchestrator.agent_manager import AgentManager, AgentTask, TaskPriority
from backend.memory.context_store import SharedMemoryStore


logger = structlog.get_logger()

# Metrics
tasks_scheduled = Counter('dag_tasks_scheduled_total', 'Total tasks scheduled')
tasks_executed = Counter('dag_tasks_executed_total', 'Total tasks executed')
dag_execution_time = Histogram('dag_execution_seconds', 'DAG execution time')
parallel_tasks_gauge = Gauge('dag_parallel_tasks', 'Number of tasks executing in parallel')


class TaskState(Enum):
    """Task execution states in the DAG"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    """Represents a node in the task DAG"""
    task_id: str
    task_type: str
    agent_type: str
    payload: Dict[str, Any]
    state: TaskState = TaskState.PENDING
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    priority: int = 3
    estimated_duration: float = 60.0  # seconds
    actual_duration: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    context_inputs: List[str] = field(default_factory=list)
    context_outputs: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """Execution plan for a DAG"""
    dag_id: str
    nodes: Dict[str, DAGNode]
    start_nodes: Set[str]
    end_nodes: Set[str]
    critical_path: List[str]
    estimated_duration: float
    parallelism_factor: float


class DAGScheduler:
    """
    Advanced DAG-based scheduler for parallel task execution.
    
    Optimizes task execution by running independent tasks in parallel
    while respecting dependencies and resource constraints.
    """
    
    def __init__(self, 
                 agent_manager: AgentManager,
                 memory_store: SharedMemoryStore,
                 max_parallel_tasks: int = 10):
        self.agent_manager = agent_manager
        self.memory_store = memory_store
        self.max_parallel_tasks = max_parallel_tasks
        
        # DAG storage
        self.dags: Dict[str, nx.DiGraph] = {}
        self.dag_nodes: Dict[str, Dict[str, DAGNode]] = {}
        
        # Execution tracking
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.execution_plans: Dict[str, ExecutionPlan] = {}
        
        # Resource management
        self.resource_pool = asyncio.Semaphore(max_parallel_tasks)
        self.agent_reservations: Dict[str, str] = {}  # task_id -> agent_id
        
        # Optimization parameters
        self.enable_speculative_execution = True
        self.enable_task_batching = True
        self.enable_dynamic_reprioritization = True
        
        logger.info("DAG Scheduler initialized", max_parallel=max_parallel_tasks)
    
    async def create_dag(self, dag_id: str, tasks: List[Dict[str, Any]]) -> ExecutionPlan:
        """
        Create a DAG from task definitions.
        
        Args:
            dag_id: Unique DAG identifier
            tasks: List of task definitions with dependencies
            
        Returns:
            Execution plan for the DAG
        """
        # Create directed graph
        dag = nx.DiGraph()
        nodes = {}
        
        # Create nodes
        for task_def in tasks:
            node = DAGNode(
                task_id=task_def.get('task_id', str(uuid.uuid4())),
                task_type=task_def['task_type'],
                agent_type=task_def.get('agent_type', 'auto'),
                payload=task_def.get('payload', {}),
                dependencies=set(task_def.get('dependencies', [])),
                priority=task_def.get('priority', 3),
                estimated_duration=task_def.get('estimated_duration', 60.0),
                context_inputs=task_def.get('context_inputs', []),
                context_outputs=task_def.get('context_outputs', []),
                constraints=task_def.get('constraints', {})
            )
            
            nodes[node.task_id] = node
            dag.add_node(node.task_id, data=node)
        
        # Create edges based on dependencies
        for task_id, node in nodes.items():
            for dep_id in node.dependencies:
                if dep_id in nodes:
                    dag.add_edge(dep_id, task_id)
                    nodes[dep_id].dependents.add(task_id)
        
        # Validate DAG
        if not nx.is_directed_acyclic_graph(dag):
            raise ValueError(f"Graph contains cycles - not a valid DAG")
        
        # Store DAG
        self.dags[dag_id] = dag
        self.dag_nodes[dag_id] = nodes
        
        # Create execution plan
        plan = await self._create_execution_plan(dag_id, dag, nodes)
        self.execution_plans[dag_id] = plan
        
        logger.info("DAG created", 
                   dag_id=dag_id,
                   nodes=len(nodes),
                   edges=dag.number_of_edges())
        
        return plan
    
    async def _create_execution_plan(self, 
                                   dag_id: str,
                                   dag: nx.DiGraph,
                                   nodes: Dict[str, DAGNode]) -> ExecutionPlan:
        """Create an optimized execution plan"""
        # Find start and end nodes
        start_nodes = {n for n in dag.nodes() if dag.in_degree(n) == 0}
        end_nodes = {n for n in dag.nodes() if dag.out_degree(n) == 0}
        
        # Calculate critical path
        critical_path = self._find_critical_path(dag, nodes)
        
        # Estimate total duration
        estimated_duration = sum(nodes[task_id].estimated_duration 
                               for task_id in critical_path)
        
        # Calculate parallelism factor
        max_parallel = self._calculate_max_parallelism(dag)
        parallelism_factor = max_parallel / max(1, len(nodes))
        
        plan = ExecutionPlan(
            dag_id=dag_id,
            nodes=nodes,
            start_nodes=start_nodes,
            end_nodes=end_nodes,
            critical_path=critical_path,
            estimated_duration=estimated_duration,
            parallelism_factor=parallelism_factor
        )
        
        return plan
    
    def _find_critical_path(self, dag: nx.DiGraph, nodes: Dict[str, DAGNode]) -> List[str]:
        """Find the critical path (longest path) through the DAG"""
        # Use topological sort for processing order
        topo_order = list(nx.topological_sort(dag))
        
        # Calculate earliest start times
        earliest_start = {}
        earliest_finish = {}
        
        for node_id in topo_order:
            if dag.in_degree(node_id) == 0:
                earliest_start[node_id] = 0
            else:
                earliest_start[node_id] = max(
                    earliest_finish[pred] 
                    for pred in dag.predecessors(node_id)
                )
            
            earliest_finish[node_id] = (earliest_start[node_id] + 
                                      nodes[node_id].estimated_duration)
        
        # Find the critical path by backtracking from end nodes
        critical_path = []
        max_finish_time = max(earliest_finish.values()) if earliest_finish else 0
        
        # Find end node with maximum finish time
        critical_end = None
        for node_id in end_nodes:
            if node_id in earliest_finish and earliest_finish[node_id] == max_finish_time:
                critical_end = node_id
                break
        
        if critical_end:
            # Backtrack to find critical path
            path = [critical_end]
            current = critical_end
            
            while dag.in_degree(current) > 0:
                # Find predecessor on critical path
                for pred in dag.predecessors(current):
                    if (earliest_finish[pred] + nodes[current].estimated_duration == 
                        earliest_finish[current]):
                        path.append(pred)
                        current = pred
                        break
            
            critical_path = list(reversed(path))
        
        return critical_path
    
    def _calculate_max_parallelism(self, dag: nx.DiGraph) -> int:
        """Calculate maximum possible parallelism in the DAG"""
        # Use level-based analysis
        levels = self._assign_levels(dag)
        max_parallel = max(len(nodes) for nodes in levels.values()) if levels else 1
        return max_parallel
    
    def _assign_levels(self, dag: nx.DiGraph) -> Dict[int, List[str]]:
        """Assign levels to nodes for parallel execution analysis"""
        levels = defaultdict(list)
        node_levels = {}
        
        # BFS to assign levels
        queue = deque([(n, 0) for n in dag.nodes() if dag.in_degree(n) == 0])
        
        while queue:
            node, level = queue.popleft()
            
            if node in node_levels:
                node_levels[node] = max(node_levels[node], level)
            else:
                node_levels[node] = level
                
                for successor in dag.successors(node):
                    queue.append((successor, level + 1))
        
        # Group by level
        for node, level in node_levels.items():
            levels[level].append(node)
        
        return dict(levels)
    
    async def execute_dag(self, dag_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a DAG with optimized parallel execution.
        
        Args:
            dag_id: DAG to execute
            context: Initial context for execution
            
        Returns:
            Execution results
        """
        with dag_execution_time.time():
            if dag_id not in self.dags:
                raise ValueError(f"DAG {dag_id} not found")
            
            dag = self.dags[dag_id]
            nodes = self.dag_nodes[dag_id]
            plan = self.execution_plans[dag_id]
            
            # Initialize context
            if context:
                await self._store_context(dag_id, context)
            
            # Track execution
            start_time = datetime.utcnow()
            completed_tasks = set()
            failed_tasks = set()
            results = {}
            
            # Initialize ready queue with start nodes
            ready_queue = []
            for node_id in plan.start_nodes:
                self._add_to_ready_queue(ready_queue, nodes[node_id])
            
            # Main execution loop
            while ready_queue or self.running_tasks:
                # Start ready tasks up to parallel limit
                while ready_queue and len(self.running_tasks) < self.max_parallel_tasks:
                    _, _, node = heapq.heappop(ready_queue)
                    
                    # Check if we can allocate an agent
                    if await self._can_allocate_agent(node):
                        # Start task execution
                        task = asyncio.create_task(
                            self._execute_task(dag_id, node)
                        )
                        self.running_tasks[node.task_id] = task
                        parallel_tasks_gauge.inc()
                    else:
                        # Put back in queue if no agent available
                        self._add_to_ready_queue(ready_queue, node)
                        await asyncio.sleep(1)  # Brief wait before retry
                
                # Wait for any task to complete
                if self.running_tasks:
                    done, pending = await asyncio.wait(
                        self.running_tasks.values(),
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Process completed tasks
                    for task in done:
                        task_id = None
                        for tid, t in self.running_tasks.items():
                            if t == task:
                                task_id = tid
                                break
                        
                        if task_id:
                            del self.running_tasks[task_id]
                            parallel_tasks_gauge.dec()
                            
                            node = nodes[task_id]
                            
                            try:
                                result = await task
                                node.state = TaskState.COMPLETED
                                node.result = result
                                completed_tasks.add(task_id)
                                results[task_id] = result
                                
                                # Check dependent tasks
                                for dep_id in node.dependents:
                                    dep_node = nodes[dep_id]
                                    if self._is_task_ready(dep_node, completed_tasks):
                                        dep_node.state = TaskState.READY
                                        self._add_to_ready_queue(ready_queue, dep_node)
                                
                                logger.info("Task completed", task_id=task_id)
                                
                            except Exception as e:
                                node.state = TaskState.FAILED
                                node.error = str(e)
                                failed_tasks.add(task_id)
                                
                                logger.error("Task failed", 
                                           task_id=task_id,
                                           error=str(e))
                                
                                # Handle failure based on strategy
                                await self._handle_task_failure(
                                    dag_id, node, ready_queue, nodes
                                )
                
                # Dynamic reprioritization if enabled
                if self.enable_dynamic_reprioritization and ready_queue:
                    ready_queue = self._reprioritize_queue(
                        ready_queue, nodes, completed_tasks
                    )
                
                # Brief sleep to prevent tight loop
                if not ready_queue and self.running_tasks:
                    await asyncio.sleep(0.1)
            
            # Calculate execution metrics
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            execution_summary = {
                'dag_id': dag_id,
                'status': 'completed' if not failed_tasks else 'partial_failure',
                'total_tasks': len(nodes),
                'completed_tasks': len(completed_tasks),
                'failed_tasks': len(failed_tasks),
                'execution_time': execution_time,
                'estimated_time': plan.estimated_duration,
                'efficiency': plan.estimated_duration / execution_time if execution_time > 0 else 0,
                'results': results,
                'failures': {
                    task_id: nodes[task_id].error 
                    for task_id in failed_tasks
                }
            }
            
            logger.info("DAG execution completed",
                       dag_id=dag_id,
                       completed=len(completed_tasks),
                       failed=len(failed_tasks),
                       time=execution_time)
            
            return execution_summary
    
    async def _execute_task(self, dag_id: str, node: DAGNode) -> Any:
        """Execute a single task"""
        async with self.resource_pool:
            try:
                tasks_executed.inc()
                
                # Load context
                context = await self._load_task_context(dag_id, node)
                
                # Record start time
                start_time = datetime.utcnow()
                node.state = TaskState.RUNNING
                
                # Submit to agent manager
                task_id = await self.agent_manager.submit_task(
                    task_type=node.task_type,
                    payload=node.payload,
                    priority=TaskPriority(node.priority),
                    context_keys=node.context_inputs
                )
                
                # Wait for completion
                while True:
                    status = await self.agent_manager.get_task_status(task_id)
                    
                    if status['status'] == 'completed':
                        result = status['result']
                        break
                    elif status['status'] == 'failed':
                        raise Exception(f"Agent task failed: {status.get('error')}")
                    
                    await asyncio.sleep(1)
                
                # Record duration
                end_time = datetime.utcnow()
                node.actual_duration = (end_time - start_time).total_seconds()
                
                # Store outputs in context
                if node.context_outputs:
                    await self._store_task_outputs(dag_id, node, result)
                
                return result
                
            except Exception as e:
                node.retries += 1
                if node.retries < node.max_retries:
                    # Retry logic
                    await asyncio.sleep(2 ** node.retries)  # Exponential backoff
                    return await self._execute_task(dag_id, node)
                else:
                    raise
    
    def _is_task_ready(self, node: DAGNode, completed_tasks: Set[str]) -> bool:
        """Check if a task is ready to execute"""
        return all(dep_id in completed_tasks for dep_id in node.dependencies)
    
    def _add_to_ready_queue(self, queue: List, node: DAGNode):
        """Add task to ready queue with priority"""
        # Priority calculation: lower number = higher priority
        # Consider: task priority, critical path membership, estimated duration
        priority_score = node.priority
        
        # Boost priority for critical path tasks
        if hasattr(node, '_on_critical_path') and node._on_critical_path:
            priority_score -= 1
        
        # Boost priority for shorter tasks (better parallelism)
        if node.estimated_duration < 30:
            priority_score -= 0.5
        
        heapq.heappush(queue, (priority_score, datetime.utcnow(), node))
        tasks_scheduled.inc()
    
    async def _can_allocate_agent(self, node: DAGNode) -> bool:
        """Check if an agent can be allocated for the task"""
        # If specific agent type requested
        if node.agent_type != 'auto':
            agent = self.agent_manager.get_least_busy_agent(node.task_type)
            return agent is not None
        
        # Auto selection
        return True
    
    async def _handle_task_failure(self, 
                                 dag_id: str,
                                 failed_node: DAGNode,
                                 ready_queue: List,
                                 nodes: Dict[str, DAGNode]):
        """Handle task failure with various strategies"""
        # Strategy 1: Skip non-critical dependents
        if failed_node.constraints.get('allow_failure', False):
            for dep_id in failed_node.dependents:
                dep_node = nodes[dep_id]
                if dep_node.constraints.get('optional_dependency', False):
                    dep_node.state = TaskState.SKIPPED
                    # Remove failed dependency
                    dep_node.dependencies.discard(failed_node.task_id)
                    # Check if now ready
                    completed = {n for n, node in nodes.items() 
                               if node.state == TaskState.COMPLETED}
                    if self._is_task_ready(dep_node, completed):
                        self._add_to_ready_queue(ready_queue, dep_node)
        
        # Strategy 2: Trigger compensating actions
        if 'compensation_task' in failed_node.constraints:
            comp_task = failed_node.constraints['compensation_task']
            # Add compensation task to DAG
            comp_node = DAGNode(
                task_id=f"{failed_node.task_id}_compensation",
                task_type=comp_task['type'],
                agent_type=comp_task.get('agent_type', 'auto'),
                payload=comp_task['payload'],
                priority=1  # High priority
            )
            nodes[comp_node.task_id] = comp_node
            self._add_to_ready_queue(ready_queue, comp_node)
    
    def _reprioritize_queue(self, 
                          queue: List,
                          nodes: Dict[str, DAGNode],
                          completed_tasks: Set[str]) -> List:
        """Dynamically reprioritize tasks based on current state"""
        # Extract all items
        items = []
        while queue:
            items.append(heapq.heappop(queue))
        
        # Recalculate priorities
        new_queue = []
        for _, _, node in items:
            # Boost priority for tasks that unlock many others
            blocking_score = len([
                dep_id for dep_id in node.dependents
                if dep_id not in completed_tasks
            ])
            
            # Adjust priority
            new_priority = node.priority - (blocking_score * 0.1)
            
            heapq.heappush(new_queue, (new_priority, datetime.utcnow(), node))
        
        return new_queue
    
    async def _store_context(self, dag_id: str, context: Dict[str, Any]):
        """Store initial context for DAG execution"""
        for key, value in context.items():
            await self.memory_store.set(f"dag:{dag_id}:{key}", value, ttl=3600)
    
    async def _load_task_context(self, dag_id: str, node: DAGNode) -> Dict[str, Any]:
        """Load context for task execution"""
        context = {}
        
        for key in node.context_inputs:
            # Try DAG-specific context first
            value = await self.memory_store.get(f"dag:{dag_id}:{key}")
            if value is None:
                # Fall back to global context
                value = await self.memory_store.get(key)
            
            if value is not None:
                context[key] = value
        
        return context
    
    async def _store_task_outputs(self, dag_id: str, node: DAGNode, result: Any):
        """Store task outputs in context"""
        for key in node.context_outputs:
            if key in result:
                await self.memory_store.set(
                    f"dag:{dag_id}:{key}",
                    result[key],
                    ttl=3600
                )
    
    def visualize_dag(self, dag_id: str) -> str:
        """Generate a visual representation of the DAG"""
        if dag_id not in self.dags:
            return "DAG not found"
        
        dag = self.dags[dag_id]
        nodes = self.dag_nodes[dag_id]
        
        # Generate DOT format for Graphviz
        dot_lines = ["digraph G {"]
        dot_lines.append('  rankdir=TB;')
        dot_lines.append('  node [shape=box];')
        
        # Add nodes with status coloring
        for node_id, node in nodes.items():
            color = {
                TaskState.PENDING: "gray",
                TaskState.READY: "yellow",
                TaskState.RUNNING: "orange",
                TaskState.COMPLETED: "green",
                TaskState.FAILED: "red",
                TaskState.SKIPPED: "lightgray"
            }.get(node.state, "white")
            
            label = f"{node.task_type}\\n{node.task_id[:8]}"
            dot_lines.append(f'  "{node_id}" [label="{label}", fillcolor={color}, style=filled];')
        
        # Add edges
        for edge in dag.edges():
            dot_lines.append(f'  "{edge[0]}" -> "{edge[1]}";')
        
        dot_lines.append("}")
        
        return "\n".join(dot_lines)
    
    async def get_dag_status(self, dag_id: str) -> Dict[str, Any]:
        """Get current status of DAG execution"""
        if dag_id not in self.dag_nodes:
            return {"error": "DAG not found"}
        
        nodes = self.dag_nodes[dag_id]
        
        status_counts = defaultdict(int)
        for node in nodes.values():
            status_counts[node.state.value] += 1
        
        running_tasks = [
            {
                'task_id': node.task_id,
                'task_type': node.task_type,
                'duration': (datetime.utcnow() - node.started_at).total_seconds()
                if hasattr(node, 'started_at') else 0
            }
            for node in nodes.values()
            if node.state == TaskState.RUNNING
        ]
        
        return {
            'dag_id': dag_id,
            'total_tasks': len(nodes),
            'status_breakdown': dict(status_counts),
            'running_tasks': running_tasks,
            'is_active': len(self.running_tasks) > 0
        }
    
    async def cancel_dag(self, dag_id: str):
        """Cancel DAG execution"""
        if dag_id in self.dag_nodes:
            # Cancel all running tasks
            for task_id, task in list(self.running_tasks.items()):
                if task_id in self.dag_nodes[dag_id]:
                    task.cancel()
                    del self.running_tasks[task_id]
            
            # Update node states
            for node in self.dag_nodes[dag_id].values():
                if node.state in [TaskState.PENDING, TaskState.READY, TaskState.RUNNING]:
                    node.state = TaskState.CANCELLED
            
            logger.info("DAG cancelled", dag_id=dag_id)