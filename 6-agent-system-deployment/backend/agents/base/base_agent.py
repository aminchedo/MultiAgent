"""
Base Agent Class

This module provides the abstract base class for all specialized agents
in the multi-agent system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Set, Optional
from enum import Enum
from datetime import datetime
import asyncio
import uuid

import structlog
from prometheus_client import Counter, Gauge, Histogram

from backend.models.models import AgentType
from backend.memory.context_store import SharedMemoryStore
from backend.grpc.agent_server import AgentServiceServer


logger = structlog.get_logger()

# Metrics
agent_tasks_processed = Counter('agent_tasks_processed_total', 'Total tasks processed by agent', ['agent_type'])
agent_task_errors = Counter('agent_task_errors_total', 'Total task errors by agent', ['agent_type'])
agent_active_tasks = Gauge('agent_active_tasks', 'Number of active tasks', ['agent_type'])


class AgentCapability(Enum):
    """Capabilities that agents can have"""
    # Planning capabilities
    PROJECT_PLANNING = "project_planning"
    ARCHITECTURE_DESIGN = "architecture_design"
    TASK_DECOMPOSITION = "task_decomposition"
    
    # Code generation capabilities
    CODE_GENERATION = "code_generation"
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"
    UI_DEVELOPMENT = "ui_development"
    
    # Testing capabilities
    UNIT_TESTING = "unit_testing"
    INTEGRATION_TESTING = "integration_testing"
    PERFORMANCE_TESTING = "performance_testing"
    
    # Review capabilities
    CODE_REVIEW = "code_review"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    BEST_PRACTICES = "best_practices"
    DEPENDENCY_CHECK = "dependency_check"
    
    # Documentation capabilities
    API_DOCUMENTATION = "api_documentation"
    USER_DOCUMENTATION = "user_documentation"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    
    # Deployment capabilities
    CI_CD_SETUP = "ci_cd_setup"
    CONTAINERIZATION = "containerization"
    CLOUD_DEPLOYMENT = "cloud_deployment"


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.
    
    Provides common functionality for task execution, communication,
    and collaboration with other agents.
    """
    
    def __init__(self, 
                 agent_id: str,
                 agent_type: AgentType,
                 memory_store: SharedMemoryStore,
                 grpc_port: Optional[int] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.memory_store = memory_store
        self.capabilities: Set[AgentCapability] = set()
        
        # Task management
        self.current_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.max_concurrent_tasks = 5
        
        # Performance tracking
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_execution_time = 0.0
        
        # gRPC server
        self.grpc_server = None
        if grpc_port:
            self.grpc_server = AgentServiceServer(self, grpc_port)
        
        # Collaboration
        self.collaboration_handlers = {}
        self._setup_collaboration_handlers()
        
        logger.info(f"Agent initialized", 
                   agent_id=agent_id, 
                   agent_type=agent_type.value)
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        Must be implemented by specialized agents.
        
        Args:
            task: Task details including type, payload, and context
            
        Returns:
            Task execution result
        """
        pass
    
    async def start(self):
        """Start the agent and its gRPC server"""
        if self.grpc_server:
            await self.grpc_server.start()
        
        logger.info(f"Agent started", agent_id=self.agent_id)
    
    async def stop(self):
        """Stop the agent gracefully"""
        # Cancel all active tasks
        for task_id in list(self.current_tasks.keys()):
            await self.cancel_task(task_id)
        
        if self.grpc_server:
            await self.grpc_server.stop()
        
        logger.info(f"Agent stopped", agent_id=self.agent_id)
    
    async def process_task(self, 
                          task_id: str,
                          task_type: str,
                          payload: Dict[str, Any],
                          context: Dict[str, str] = None,
                          dependencies: List[str] = None) -> Dict[str, Any]:
        """
        Process a task with full lifecycle management.
        
        Args:
            task_id: Unique task identifier
            task_type: Type of task to execute
            payload: Task payload
            context: Shared context keys
            dependencies: Task dependencies
            
        Returns:
            Task result
        """
        # Check capacity
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return {
                'success': False,
                'error': 'Agent at maximum capacity'
            }
        
        # Track task
        self.current_tasks[task_id] = {
            'task_id': task_id,
            'task_type': task_type,
            'status': 'processing',
            'started_at': datetime.utcnow()
        }
        
        agent_active_tasks.labels(agent_type=self.agent_type.value).inc()
        agent_tasks_processed.labels(agent_type=self.agent_type.value).inc()
        
        try:
            # Load context from shared memory
            task_context = {}
            if context:
                for key in context:
                    value = await self.memory_store.get(key)
                    if value:
                        task_context[key] = value
            
            # Prepare task
            task = {
                'task_id': task_id,
                'task_type': task_type,
                'payload': payload,
                'context': task_context,
                'dependencies': dependencies or []
            }
            
            # Execute task
            start_time = datetime.utcnow()
            result = await self.execute_task(task)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update metrics
            self.tasks_completed += 1
            self.total_execution_time += execution_time
            
            # Store result in shared memory if requested
            if 'output_key' in payload:
                await self.memory_store.set(
                    payload['output_key'],
                    result,
                    ttl=3600  # 1 hour TTL
                )
            
            # Record in history
            self.task_history.append({
                'task_id': task_id,
                'task_type': task_type,
                'completed_at': datetime.utcnow(),
                'execution_time': execution_time,
                'success': result.get('success', True)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed",
                        task_id=task_id,
                        error=str(e))
            
            self.tasks_failed += 1
            agent_task_errors.labels(agent_type=self.agent_type.value).inc()
            
            return {
                'success': False,
                'error': str(e)
            }
        
        finally:
            # Clean up
            self.current_tasks.pop(task_id, None)
            agent_active_tasks.labels(agent_type=self.agent_type.value).dec()
    
    async def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get progress for a specific task"""
        task = self.current_tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task_id,
            'status': task.get('status', 'unknown'),
            'progress': task.get('progress', 0.0),
            'message': task.get('message', ''),
            'started_at': task.get('started_at')
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id not in self.current_tasks:
            return False
        
        # Mark as cancelled
        self.current_tasks[task_id]['status'] = 'cancelled'
        
        # Actual cancellation logic would go here
        # This might involve cancelling asyncio tasks, subprocesses, etc.
        
        self.current_tasks.pop(task_id, None)
        agent_active_tasks.labels(agent_type=self.agent_type.value).dec()
        
        logger.info(f"Task cancelled", task_id=task_id)
        return True
    
    async def collaborate(self,
                         requesting_agent_id: str,
                         collaboration_type: str,
                         data: Dict[str, Any],
                         context: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Handle collaboration request from another agent.
        
        Args:
            requesting_agent_id: ID of requesting agent
            collaboration_type: Type of collaboration
            data: Collaboration data
            context: Additional context
            
        Returns:
            Collaboration response
        """
        handler = self.collaboration_handlers.get(collaboration_type)
        
        if not handler:
            return {
                'accepted': False,
                'error': f'Unknown collaboration type: {collaboration_type}'
            }
        
        try:
            response_data = await handler(requesting_agent_id, data, context)
            
            return {
                'responding_agent_id': self.agent_id,
                'accepted': True,
                'response_data': response_data,
                'confidence_score': response_data.get('confidence', 0.8)
            }
            
        except Exception as e:
            logger.error(f"Collaboration failed",
                        collaboration_type=collaboration_type,
                        error=str(e))
            
            return {
                'accepted': False,
                'error': str(e)
            }
    
    def _setup_collaboration_handlers(self):
        """Setup default collaboration handlers"""
        # These can be overridden by specialized agents
        self.collaboration_handlers = {
            'review': self._handle_review_request,
            'validate': self._handle_validation_request,
            'enhance': self._handle_enhancement_request,
            'consult': self._handle_consultation_request
        }
    
    async def _handle_review_request(self, 
                                   requesting_agent_id: str,
                                   data: Dict[str, Any],
                                   context: Dict[str, str]) -> Dict[str, Any]:
        """Default review request handler"""
        return {
            'reviewed': True,
            'findings': [],
            'suggestions': [],
            'confidence': 0.5
        }
    
    async def _handle_validation_request(self,
                                       requesting_agent_id: str,
                                       data: Dict[str, Any],
                                       context: Dict[str, str]) -> Dict[str, Any]:
        """Default validation request handler"""
        return {
            'valid': True,
            'errors': [],
            'warnings': [],
            'confidence': 0.5
        }
    
    async def _handle_enhancement_request(self,
                                        requesting_agent_id: str,
                                        data: Dict[str, Any],
                                        context: Dict[str, str]) -> Dict[str, Any]:
        """Default enhancement request handler"""
        return {
            'enhanced': False,
            'reason': 'Enhancement not implemented',
            'confidence': 0.0
        }
    
    async def _handle_consultation_request(self,
                                         requesting_agent_id: str,
                                         data: Dict[str, Any],
                                         context: Dict[str, str]) -> Dict[str, Any]:
        """Default consultation request handler"""
        return {
            'advice': 'No specific advice available',
            'confidence': 0.0
        }
    
    async def share_context(self,
                           key: str,
                           value: Any,
                           target_agents: List[str] = None,
                           ttl: int = 300) -> bool:
        """
        Share context with other agents.
        
        Args:
            key: Context key
            value: Context value
            target_agents: Specific agents to share with (None = all)
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        try:
            # Store in shared memory
            await self.memory_store.set(
                key,
                value,
                ttl=ttl
            )
            
            # Store agent-specific access info
            if target_agents:
                await self.memory_store.set(
                    f"{key}:access",
                    target_agents,
                    ttl=ttl
                )
            
            # Log sharing
            await self.memory_store.append_to_list(
                f"agent:{self.agent_id}:shared_keys",
                {
                    'key': key,
                    'timestamp': datetime.utcnow().isoformat(),
                    'targets': target_agents
                },
                max_length=100
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to share context",
                        key=key,
                        error=str(e))
            return False
    
    async def get_shared_context(self, key: str) -> Optional[Any]:
        """Get shared context if accessible"""
        # Check access permissions
        access_list = await self.memory_store.get(f"{key}:access")
        if access_list and self.agent_id not in access_list:
            return None
        
        return await self.memory_store.get(key)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'capabilities': [cap.value for cap in self.capabilities],
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'current_load': len(self.current_tasks),
            'performance_metrics': {
                'tasks_completed': self.tasks_completed,
                'tasks_failed': self.tasks_failed,
                'success_rate': self.tasks_completed / max(1, self.tasks_completed + self.tasks_failed),
                'avg_execution_time': self.total_execution_time / max(1, self.tasks_completed)
            }
        }
    
    async def update_progress(self, task_id: str, progress: float, message: str = ""):
        """Update task progress"""
        if task_id in self.current_tasks:
            self.current_tasks[task_id]['progress'] = progress
            self.current_tasks[task_id]['message'] = message
            
            # Publish progress update
            await self.memory_store.publish(
                f"task_progress:{task_id}",
                {
                    'task_id': task_id,
                    'progress': progress,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
    
    def get_status(self) -> str:
        """Get current agent status"""
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return "busy"
        elif len(self.current_tasks) > 0:
            return "working"
        else:
            return "available"
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            'healthy': True,
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'status': self.get_status(),
            'active_tasks': len(self.current_tasks),
            'memory_connected': self.memory_store.redis_client is not None
        }