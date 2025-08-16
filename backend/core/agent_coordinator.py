"""
Agent Coordination System
Handles task assignment, cross-agent verification, and workflow orchestration.
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

import redis.asyncio as redis
from pydantic import BaseModel

from backend.models.models import JobStatus, AgentType, MessageType
from services.discovery_service import DiscoveryService, AgentInfo
from agents.base_agent import BaseAgent, AgentTask, AgentCapability

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskAssignment:
    """Represents a task assignment to an agent."""
    task_id: str
    agent_id: str
    agent_type: str
    assigned_at: datetime
    priority: TaskPriority
    dependencies: Set[str] = field(default_factory=set)
    timeout: int = 300  # seconds
    retry_count: int = 0
    max_retries: int = 3
    
    
@dataclass
class CrossAgentVerification:
    """Cross-agent verification configuration."""
    verification_id: str
    primary_task_id: str
    primary_agent_id: str
    verifying_agents: List[str]
    verification_criteria: Dict[str, Any]
    required_consensus: float = 0.75  # 75% agreement required
    timeout: int = 120


@dataclass 
class WorkflowExecution:
    """Workflow execution state tracking."""
    workflow_id: str
    name: str
    tasks: List[TaskAssignment]
    status: WorkflowStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentCoordinator:
    """
    Coordinates task assignment and cross-agent verification.
    Implements the production-ready agent coordination system.
    """
    
    def __init__(self, redis_client: redis.Redis, discovery_service: DiscoveryService):
        self.redis = redis_client
        self.discovery = discovery_service
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.task_assignments: Dict[str, TaskAssignment] = {}
        self.verifications: Dict[str, CrossAgentVerification] = {}
        self._coordination_metrics = {
            "tasks_assigned": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "verifications_passed": 0,
            "verifications_failed": 0,
            "avg_task_duration": 0.0
        }
        
    async def submit_task(self, task_description: str, agent_type: str = None,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         dependencies: Set[str] = None,
                         verification_required: bool = True) -> str:
        """
        Submit a task for execution with automatic agent assignment.
        
        Args:
            task_description: Description of the task to perform
            agent_type: Preferred agent type (optional - will auto-select if None)
            priority: Task priority level
            dependencies: Set of task IDs this task depends on
            verification_required: Whether cross-agent verification is needed
            
        Returns:
            task_id: Unique identifier for the submitted task
        """
        task_id = f"task_{uuid.uuid4()}"
        
        try:
            # Select appropriate agent
            if not agent_type:
                agent_type = await self._select_agent_type(task_description)
            
            # Find available agent
            agents = await self.discovery.find_agents_by_type(agent_type)
            if not agents:
                raise ValueError(f"No available agents of type {agent_type}")
            
            # Select best agent based on load and capability
            selected_agent = await self._select_best_agent(agents, task_description)
            
            # Create task assignment
            assignment = TaskAssignment(
                task_id=task_id,
                agent_id=selected_agent.agent_id,
                agent_type=agent_type,
                assigned_at=datetime.utcnow(),
                priority=priority,
                dependencies=dependencies or set()
            )
            
            # Store assignment
            self.task_assignments[task_id] = assignment
            await self._persist_task_assignment(assignment)
            
            # Schedule task execution
            await self._schedule_task_execution(task_id, task_description)
            
            # Setup cross-agent verification if required
            if verification_required:
                await self._setup_cross_agent_verification(task_id, selected_agent.agent_id)
            
            self._coordination_metrics["tasks_assigned"] += 1
            
            logger.info(f"Task {task_id} assigned to agent {selected_agent.agent_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise
    
    async def check_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check the status of a task with detailed information.
        
        Returns comprehensive task status including agent info and verification results.
        """
        if task_id not in self.task_assignments:
            raise ValueError(f"Task {task_id} not found")
        
        assignment = self.task_assignments[task_id]
        
        # Get agent status
        agent_info = await self.discovery.get_agent_info(assignment.agent_id)
        
        # Get task execution status from Redis
        task_data = await self.redis.hget("tasks", task_id)
        task_status = json.loads(task_data) if task_data else {"status": "pending"}
        
        # Check verification status if applicable
        verification_status = None
        for verification in self.verifications.values():
            if verification.primary_task_id == task_id:
                verification_status = await self._get_verification_status(verification.verification_id)
                break
        
        return {
            "task_id": task_id,
            "status": task_status.get("status", "pending"),
            "agent": {
                "id": assignment.agent_id,
                "type": assignment.agent_type,
                "load": agent_info.load if agent_info else None
            },
            "assignment": {
                "assigned_at": assignment.assigned_at.isoformat(),
                "priority": assignment.priority.value,
                "retry_count": assignment.retry_count
            },
            "verification": verification_status,
            "execution_time": task_status.get("execution_time"),
            "error": task_status.get("error")
        }
    
    async def validate_output(self, task_id: str, expected_output: str = None) -> bool:
        """
        Validate task output against expected results.
        
        Performs comprehensive validation including format, content, and quality checks.
        """
        if task_id not in self.task_assignments:
            raise ValueError(f"Task {task_id} not found")
        
        # Get task output from Redis
        output_data = await self.redis.hget("task_outputs", task_id)
        if not output_data:
            return False
        
        output = json.loads(output_data)
        
        # Basic validation checks
        validations = []
        
        # 1. Output format validation
        validations.append(self._validate_output_format(output))
        
        # 2. Content quality validation
        validations.append(await self._validate_content_quality(output))
        
        # 3. Expected output comparison (if provided)
        if expected_output:
            validations.append(self._validate_expected_output(output, expected_output))
        
        # 4. Cross-agent verification results
        verification_result = await self._get_verification_result(task_id)
        if verification_result:
            validations.append(verification_result["passed"])
        
        # All validations must pass
        is_valid = all(validations)
        
        # Update metrics
        if is_valid:
            self._coordination_metrics["tasks_completed"] += 1
        else:
            self._coordination_metrics["tasks_failed"] += 1
        
        # Store validation result
        await self.redis.hset("task_validations", task_id, json.dumps({
            "is_valid": is_valid,
            "validation_checks": validations,
            "validated_at": datetime.utcnow().isoformat()
        }))
        
        return is_valid
    
    async def create_workflow(self, name: str, task_definitions: List[Dict[str, Any]]) -> str:
        """
        Create and execute a multi-task workflow with dependency management.
        
        Args:
            name: Workflow name
            task_definitions: List of task definitions with dependencies
            
        Returns:
            workflow_id: Unique identifier for the workflow
        """
        workflow_id = f"wf_{uuid.uuid4()}"
        
        # Create workflow execution object
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            name=name,
            tasks=[],
            status=WorkflowStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Create task assignments for each task in the workflow
        for task_def in task_definitions:
            task_id = await self.submit_task(
                task_description=task_def["description"],
                agent_type=task_def.get("agent_type"),
                priority=TaskPriority(task_def.get("priority", 2)),
                dependencies=set(task_def.get("dependencies", [])),
                verification_required=task_def.get("verification_required", True)
            )
            
            workflow.tasks.append(self.task_assignments[task_id])
        
        # Store workflow
        self.active_workflows[workflow_id] = workflow
        await self._persist_workflow(workflow)
        
        # Start workflow execution
        await self._execute_workflow(workflow_id)
        
        return workflow_id
    
    async def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get real-time coordination system metrics."""
        # Calculate average task duration
        completed_tasks = await self.redis.llen("completed_tasks")
        if completed_tasks > 0:
            durations = await self.redis.lrange("task_durations", 0, -1)
            if durations:
                avg_duration = sum(float(d) for d in durations) / len(durations)
                self._coordination_metrics["avg_task_duration"] = avg_duration
        
        # Add real-time metrics
        metrics = self._coordination_metrics.copy()
        metrics.update({
            "active_workflows": len(self.active_workflows),
            "pending_tasks": len([t for t in self.task_assignments.values() 
                                if t.assigned_at > datetime.utcnow() - timedelta(seconds=t.timeout)]),
            "active_verifications": len(self.verifications),
            "agent_utilization": await self._calculate_agent_utilization()
        })
        
        return metrics
    
    # Private methods for internal coordination logic
    
    async def _select_agent_type(self, task_description: str) -> str:
        """Intelligently select agent type based on task description."""
        # Simple keyword-based selection (can be enhanced with ML)
        description_lower = task_description.lower()
        
        if any(word in description_lower for word in ["generate", "code", "implement", "create"]):
            return "code_generator"
        elif any(word in description_lower for word in ["test", "verify", "validate"]):
            return "tester"
        elif any(word in description_lower for word in ["plan", "design", "architecture"]):
            return "planner"
        elif any(word in description_lower for word in ["review", "analyze", "check"]):
            return "reviewer"
        elif any(word in description_lower for word in ["security", "vulnerability", "scan"]):
            return "security"
        else:
            return "planner"  # Default to planner for decomposition
    
    async def _select_best_agent(self, agents: List[AgentInfo], task_description: str) -> AgentInfo:
        """Select the best agent based on load, capability, and task requirements."""
        scored_agents = []
        
        for agent in agents:
            score = 0
            
            # Load factor (lower load = higher score)
            score += (1.0 - agent.load) * 40
            
            # CPU usage factor  
            score += (1.0 - agent.cpu_usage) * 30
            
            # Active tasks factor
            score += max(0, (10 - agent.active_tasks)) * 20
            
            # Memory usage factor
            score += (1.0 - agent.memory_usage) * 10
            
            scored_agents.append((agent, score))
        
        # Return agent with highest score
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return scored_agents[0][0]
    
    async def _schedule_task_execution(self, task_id: str, task_description: str):
        """Schedule task for execution by the assigned agent."""
        assignment = self.task_assignments[task_id]
        
        # Check dependencies
        if assignment.dependencies:
            all_deps_complete = True
            for dep_id in assignment.dependencies:
                dep_status = await self.check_task_status(dep_id)
                if dep_status["status"] != "completed":
                    all_deps_complete = False
                    break
            
            if not all_deps_complete:
                # Schedule for later execution when dependencies are met
                await self.redis.zadd("pending_tasks", {task_id: time.time() + 30})
                return
        
        # Send task to agent via Redis queue
        task_data = {
            "task_id": task_id,
            "description": task_description,
            "priority": assignment.priority.value,
            "timeout": assignment.timeout,
            "assigned_at": assignment.assigned_at.isoformat()
        }
        
        agent_queue = f"agent_queue:{assignment.agent_id}"
        await self.redis.lpush(agent_queue, json.dumps(task_data))
        
        # Set task status to running
        await self.redis.hset("tasks", task_id, json.dumps({
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        }))
    
    async def _setup_cross_agent_verification(self, task_id: str, primary_agent_id: str):
        """Setup cross-agent verification for a task."""
        verification_id = f"ver_{uuid.uuid4()}"
        
        # Select verifying agents (different from primary agent)
        all_agents = await self.discovery.get_all_agents()
        verifying_agents = [
            agent.agent_id for agent in all_agents.values() 
            if agent.agent_id != primary_agent_id and agent.agent_type in ["reviewer", "tester", "security"]
        ][:3]  # Max 3 verifying agents
        
        verification = CrossAgentVerification(
            verification_id=verification_id,
            primary_task_id=task_id,
            primary_agent_id=primary_agent_id,
            verifying_agents=verifying_agents,
            verification_criteria={
                "code_quality": 0.8,
                "security_score": 0.9,
                "test_coverage": 0.85
            }
        )
        
        self.verifications[verification_id] = verification
        await self._persist_verification(verification)
    
    async def _persist_task_assignment(self, assignment: TaskAssignment):
        """Persist task assignment to Redis."""
        data = {
            "task_id": assignment.task_id,
            "agent_id": assignment.agent_id,
            "agent_type": assignment.agent_type,
            "assigned_at": assignment.assigned_at.isoformat(),
            "priority": assignment.priority.value,
            "dependencies": list(assignment.dependencies),
            "timeout": assignment.timeout,
            "retry_count": assignment.retry_count,
            "max_retries": assignment.max_retries
        }
        await self.redis.hset("task_assignments", assignment.task_id, json.dumps(data))
    
    async def _persist_workflow(self, workflow: WorkflowExecution):
        """Persist workflow to Redis."""
        data = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "task_ids": [task.task_id for task in workflow.tasks],
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "error_message": workflow.error_message,
            "metadata": workflow.metadata
        }
        await self.redis.hset("workflows", workflow.workflow_id, json.dumps(data))
    
    async def _persist_verification(self, verification: CrossAgentVerification):
        """Persist verification to Redis."""
        data = {
            "verification_id": verification.verification_id,
            "primary_task_id": verification.primary_task_id,
            "primary_agent_id": verification.primary_agent_id,
            "verifying_agents": verification.verifying_agents,
            "verification_criteria": verification.verification_criteria,
            "required_consensus": verification.required_consensus,
            "timeout": verification.timeout
        }
        await self.redis.hset("verifications", verification.verification_id, json.dumps(data))
    
    async def _execute_workflow(self, workflow_id: str):
        """Execute workflow with proper dependency handling."""
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        
        # Start monitoring workflow execution in background
        asyncio.create_task(self._monitor_workflow_execution(workflow_id))
    
    async def _monitor_workflow_execution(self, workflow_id: str):
        """Monitor workflow execution and handle completion/failure."""
        workflow = self.active_workflows[workflow_id]
        
        while workflow.status == WorkflowStatus.RUNNING:
            # Check if all tasks are complete
            all_complete = True
            any_failed = False
            
            for task in workflow.tasks:
                status = await self.check_task_status(task.task_id)
                if status["status"] == "failed":
                    any_failed = True
                    break
                elif status["status"] != "completed":
                    all_complete = False
            
            if any_failed:
                workflow.status = WorkflowStatus.FAILED
                workflow.completed_at = datetime.utcnow()
                workflow.error_message = "One or more tasks failed"
                break
            elif all_complete:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.completed_at = datetime.utcnow()
                break
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        # Persist final workflow state
        await self._persist_workflow(workflow)
    
    async def _get_verification_status(self, verification_id: str) -> Dict[str, Any]:
        """Get the current status of a cross-agent verification."""
        verification_data = await self.redis.hget("verification_results", verification_id)
        if verification_data:
            return json.loads(verification_data)
        return {"status": "pending"}
    
    async def _get_verification_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get verification result for a task."""
        for verification in self.verifications.values():
            if verification.primary_task_id == task_id:
                return await self._get_verification_status(verification.verification_id)
        return None
    
    def _validate_output_format(self, output: Dict[str, Any]) -> bool:
        """Validate output format structure."""
        required_fields = ["result", "metadata", "timestamp"]
        return all(field in output for field in required_fields)
    
    async def _validate_content_quality(self, output: Dict[str, Any]) -> bool:
        """Validate content quality using various metrics."""
        # Implement quality checks (length, completeness, etc.)
        result = output.get("result", "")
        if isinstance(result, str) and len(result) < 10:
            return False
        return True
    
    def _validate_expected_output(self, output: Dict[str, Any], expected: str) -> bool:
        """Validate output against expected results."""
        # Simple comparison - can be enhanced with semantic similarity
        result = str(output.get("result", ""))
        return expected.lower() in result.lower()
    
    async def _calculate_agent_utilization(self) -> float:
        """Calculate overall agent utilization percentage."""
        agents = await self.discovery.get_all_agents()
        if not agents:
            return 0.0
        
        total_load = sum(agent.load for agent in agents.values())
        return (total_load / len(agents)) * 100