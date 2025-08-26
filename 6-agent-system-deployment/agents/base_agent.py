"""
Base Agent Class

This module provides the base class for all agents in the network,
with support for bidirectional streaming, automatic reconnection,
and seamless integration with the discovery service.
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
import psutil
from contextlib import asynccontextmanager

import grpc
from grpc import aio
import redis.asyncio as redis

# Import middleware
from middleware.jwt_auth import JWTTokenManager, JWTClientInterceptor
from middleware.backpressure import ClientBackpressureInterceptor, BackpressureProfiles
from services.discovery_service import AgentInfo, DiscoveryService

# Import generated protobuf classes (these would be generated from agent_comm.proto)
# from proto import agent_comm_pb2, agent_comm_pb2_grpc

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Represents a capability that an agent can provide."""
    name: str
    version: str = "1.0"
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTask:
    """Represents a task assigned to an agent."""
    task_id: str
    payload: bytes
    priority: int = 1
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    dependent_agents: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if task has expired."""
        if self.deadline:
            return time.time() > self.deadline
        return False


class BaseAgent(ABC):
    """
    Base class for all agents in the network.
    
    Features:
    - Automatic service registration and discovery
    - Bidirectional streaming for real-time updates
    - Automatic reconnection on failures
    - Context sharing via Redis
    - Built-in metrics and health monitoring
    - Task queue management
    - Graceful shutdown
    """
    
    def __init__(
        self,
        agent_type: str,
        capabilities: List[AgentCapability],
        redis_url: str = "redis://localhost:6379",
        discovery_url: str = "localhost:50051",
        coordinator_url: str = "localhost:50052",
        agent_id: Optional[str] = None,
        max_queue_size: int = 1000,
        heartbeat_interval: float = 5.0,
        reconnect_interval: float = 5.0,
        max_reconnect_attempts: int = -1,  # -1 for infinite
        enable_tls: bool = False,
        tls_cert_path: Optional[str] = None,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None
    ):
        self.agent_type = agent_type
        self.agent_id = agent_id or f"{agent_type}_{uuid.uuid4().hex[:8]}"
        self.capabilities = capabilities
        
        # URLs
        self.redis_url = redis_url
        self.discovery_url = discovery_url
        self.coordinator_url = coordinator_url
        
        # Configuration
        self.max_queue_size = max_queue_size
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.enable_tls = enable_tls
        self.tls_cert_path = tls_cert_path
        
        # Authentication
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self.token_manager: Optional[JWTTokenManager] = None
        self.auth_token: Optional[str] = None
        
        # Connections
        self.redis: Optional[redis.Redis] = None
        self.discovery_channel: Optional[aio.Channel] = None
        self.coordinator_channel: Optional[aio.Channel] = None
        self.discovery_stub = None
        self.coordinator_stub = None
        
        # State
        self.running = False
        self.connected = False
        self.registered = False
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.active_tasks: Dict[str, AgentTask] = {}
        self.pending_updates: asyncio.Queue = asyncio.Queue()
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._task_processor_task: Optional[asyncio.Task] = None
        self._update_stream_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            'tasks_received': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'updates_sent': 0,
            'updates_received': 0,
            'reconnections': 0
        }
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    @abstractmethod
    async def process_task(self, task: AgentTask) -> Any:
        """
        Process a task. Must be implemented by subclasses.
        
        Args:
            task: The task to process
            
        Returns:
            The result of processing the task
        """
        pass
    
    @abstractmethod
    async def get_custom_metrics(self) -> Dict[str, float]:
        """
        Get custom metrics specific to this agent type.
        
        Returns:
            Dictionary of metric name to value
        """
        return {}
    
    async def start(self):
        """Start the agent."""
        logger.info(f"Starting agent {self.agent_id} ({self.agent_type})")
        
        try:
            # Initialize connections
            await self._init_connections()
            
            # Start background tasks
            self.running = True
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())
            self._task_processor_task = asyncio.create_task(self._task_processor_loop())
            self._update_stream_task = asyncio.create_task(self._update_stream_loop())
            self._metrics_task = asyncio.create_task(self._metrics_loop())
            
            # Register with discovery service
            await self._register()
            
            # Emit started event
            await self._emit_event('agent_started', {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'capabilities': [c.name for c in self.capabilities]
            })
            
            logger.info(f"Agent {self.agent_id} started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the agent gracefully."""
        logger.info(f"Stopping agent {self.agent_id}")
        
        self.running = False
        
        # Cancel background tasks
        tasks = [
            self._heartbeat_task,
            self._reconnect_task,
            self._task_processor_task,
            self._update_stream_task,
            self._metrics_task
        ]
        
        for task in tasks:
            if task:
                task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)
        
        # Deregister from discovery
        if self.registered:
            await self._deregister()
        
        # Close connections
        await self._close_connections()
        
        # Emit stopped event
        await self._emit_event('agent_stopped', {
            'agent_id': self.agent_id,
            'final_metrics': self.metrics
        })
        
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def submit_task(
        self,
        target_agent_id: str,
        payload: bytes,
        priority: int = 1,
        deadline: Optional[float] = None,
        dependent_agents: Optional[List[str]] = None
    ) -> str:
        """
        Submit a task to another agent.
        
        Args:
            target_agent_id: ID of the target agent
            payload: Task payload (serialized protobuf)
            priority: Task priority (0-3)
            deadline: Optional deadline timestamp
            dependent_agents: List of agent IDs this task depends on
            
        Returns:
            Task ID
        """
        task_id = f"{self.agent_id}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Create task request
            request = {
                'task_id': task_id,
                'payload': payload,
                'dependent_agents': dependent_agents or [],
                'metadata': {
                    'source_agent': self.agent_id,
                    'target_agent': target_agent_id
                },
                'priority': priority,
                'deadline': deadline
            }
            
            # Submit via coordinator
            response = await self.coordinator_stub.SubmitTask(request)
            
            if response.success:
                logger.debug(f"Submitted task {task_id} to {target_agent_id}")
                return task_id
            else:
                raise Exception(f"Task submission failed: {response.message}")
                
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise
    
    async def get_shared_context(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get shared context data from Redis.
        
        Args:
            key: Context key
            
        Returns:
            Context data or None if not found
        """
        try:
            data = await self.redis.execute_command(
                'JSON.GET', f'shared_context:{key}'
            )
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get shared context: {e}")
            return None
    
    async def set_shared_context(
        self,
        key: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        Set shared context data in Redis.
        
        Args:
            key: Context key
            data: Context data
            ttl: Optional TTL in seconds
        """
        try:
            await self.redis.execute_command(
                'JSON.SET', f'shared_context:{key}', '.', json.dumps(data)
            )
            
            if ttl:
                await self.redis.expire(f'shared_context:{key}', ttl)
                
            logger.debug(f"Set shared context: {key}")
            
        except Exception as e:
            logger.error(f"Failed to set shared context: {e}")
            raise
    
    async def discover_agents(
        self,
        capabilities: Optional[List[str]] = None,
        agent_type: Optional[str] = None,
        strategy: str = "least_load"
    ) -> List[Dict[str, Any]]:
        """
        Discover other agents in the network.
        
        Args:
            capabilities: Required capabilities
            agent_type: Filter by agent type
            strategy: Load balancing strategy
            
        Returns:
            List of agent information dictionaries
        """
        try:
            request = {
                'required_capabilities': capabilities or [],
                'strategy': strategy.upper(),
                'max_results': 10
            }
            
            response = await self.discovery_stub.DiscoverAgents(request)
            
            return [
                {
                    'agent_id': agent.agent_id,
                    'agent_type': agent.agent_type,
                    'endpoint': agent.endpoint,
                    'capabilities': list(agent.capabilities),
                    'load': agent.resources.cpu_usage
                }
                for agent in response.agents
            ]
            
        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
            return []
    
    async def broadcast_update(
        self,
        update_type: str,
        payload: Any,
        metadata: Optional[Dict[str, str]] = None
    ):
        """
        Broadcast an update to interested agents.
        
        Args:
            update_type: Type of update
            payload: Update payload
            metadata: Optional metadata
        """
        update = {
            'agent_id': self.agent_id,
            'task_id': metadata.get('task_id', '') if metadata else '',
            'type': update_type.upper(),
            'payload': payload,
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        
        await self.pending_updates.put(update)
        self.metrics['updates_sent'] += 1
    
    def on_event(self, event_type: str, handler: Callable):
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _init_connections(self):
        """Initialize connections to Redis and gRPC services."""
        # Connect to Redis
        self.redis = await redis.from_url(self.redis_url)
        
        # Setup JWT token manager if auth is enabled
        if self.private_key_path:
            self.token_manager = JWTTokenManager(
                private_key_path=self.private_key_path,
                token_expiry_seconds=3600
            )
        
        # Create gRPC channels with interceptors
        interceptors = []
        
        # Add JWT interceptor if auth is enabled
        if self.token_manager:
            jwt_interceptor = JWTClientInterceptor(
                self.token_manager,
                {
                    'agent_id': self.agent_id,
                    'agent_type': self.agent_type,
                    'capabilities': [c.name for c in self.capabilities]
                }
            )
            interceptors.append(jwt_interceptor)
        
        # Add backpressure interceptor
        backpressure_interceptor = ClientBackpressureInterceptor(
            **BackpressureProfiles.high_frequency_updates()
        )
        interceptors.append(backpressure_interceptor)
        
        # Create channels
        channel_options = [
            ('grpc.max_receive_message_length', 10 * 1024 * 1024),  # 10MB
            ('grpc.max_send_message_length', 10 * 1024 * 1024),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', True),
            ('grpc.http2.max_pings_without_data', 0)
        ]
        
        if self.enable_tls and self.tls_cert_path:
            # Load TLS credentials
            with open(self.tls_cert_path, 'rb') as f:
                cert = f.read()
            credentials = grpc.ssl_channel_credentials(root_certificates=cert)
            
            self.discovery_channel = aio.secure_channel(
                self.discovery_url,
                credentials,
                options=channel_options,
                interceptors=interceptors
            )
            self.coordinator_channel = aio.secure_channel(
                self.coordinator_url,
                credentials,
                options=channel_options,
                interceptors=interceptors
            )
        else:
            self.discovery_channel = aio.insecure_channel(
                self.discovery_url,
                options=channel_options,
                interceptors=interceptors
            )
            self.coordinator_channel = aio.insecure_channel(
                self.coordinator_url,
                options=channel_options,
                interceptors=interceptors
            )
        
        # Create stubs (would use generated classes)
        # self.discovery_stub = agent_comm_pb2_grpc.AgentRegistryStub(self.discovery_channel)
        # self.coordinator_stub = agent_comm_pb2_grpc.AgentCoordinatorStub(self.coordinator_channel)
        
        # For now, create placeholder stubs
        self.discovery_stub = type('Stub', (), {
            'RegisterAgent': lambda r: asyncio.create_task(asyncio.sleep(0)),
            'DeregisterAgent': lambda r: asyncio.create_task(asyncio.sleep(0)),
            'DiscoverAgents': lambda r: asyncio.create_task(asyncio.sleep(0))
        })()
        
        self.coordinator_stub = type('Stub', (), {
            'SubmitTask': lambda r: asyncio.create_task(asyncio.sleep(0)),
            'StreamUpdates': lambda r: asyncio.create_task(asyncio.sleep(0))
        })()
        
        self.connected = True
        logger.info("Connections initialized")
    
    async def _close_connections(self):
        """Close all connections."""
        if self.redis:
            await self.redis.close()
        
        if self.discovery_channel:
            await self.discovery_channel.close()
        
        if self.coordinator_channel:
            await self.coordinator_channel.close()
        
        self.connected = False
    
    async def _register(self):
        """Register with the discovery service."""
        try:
            # Get local endpoint
            import socket
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            port = 50100 + hash(self.agent_id) % 1000  # Assign port based on ID
            
            request = {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'capabilities': [c.name for c in self.capabilities],
                'endpoint': f"{ip}:{port}",
                'metadata': {
                    'version': '1.0',
                    'started_at': str(datetime.utcnow())
                }
            }
            
            response = await self.discovery_stub.RegisterAgent(request)
            
            if response.success:
                self.registered = True
                self.auth_token = response.auth_token
                logger.info(f"Registered with discovery service as {self.agent_id}")
            else:
                raise Exception("Registration failed")
                
        except Exception as e:
            logger.error(f"Failed to register: {e}")
            raise
    
    async def _deregister(self):
        """Deregister from the discovery service."""
        try:
            request = {'agent_id': self.agent_id}
            await self.discovery_stub.DeregisterAgent(request)
            self.registered = False
            logger.info("Deregistered from discovery service")
        except Exception as e:
            logger.error(f"Failed to deregister: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to maintain registration."""
        while self.running:
            try:
                if self.registered:
                    # Get current metrics
                    process = psutil.Process()
                    cpu_usage = process.cpu_percent() / 100.0
                    memory_usage = process.memory_percent() / 100.0
                    
                    # Calculate load based on queue depth
                    load = min(1.0, self.task_queue.qsize() / self.max_queue_size)
                    
                    # Update status in Redis (discovery service will pick it up)
                    await self.redis.hset(
                        f"agents:active:{self.agent_id}",
                        mapping={
                            'last_heartbeat': str(time.time()),
                            'state': 'READY' if load < 0.8 else 'BUSY',
                            'load': str(load),
                            'cpu_usage': str(cpu_usage),
                            'memory_usage': str(memory_usage),
                            'active_tasks': str(len(self.active_tasks)),
                            'queued_tasks': str(self.task_queue.qsize())
                        }
                    )
                    
                    logger.debug(f"Heartbeat sent (load={load:.2f})")
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def _reconnect_loop(self):
        """Handle automatic reconnection on failures."""
        reconnect_count = 0
        
        while self.running:
            try:
                if not self.connected:
                    if (self.max_reconnect_attempts == -1 or 
                        reconnect_count < self.max_reconnect_attempts):
                        
                        logger.info(f"Attempting reconnection ({reconnect_count + 1})")
                        
                        try:
                            await self._close_connections()
                            await self._init_connections()
                            await self._register()
                            
                            reconnect_count = 0
                            self.metrics['reconnections'] += 1
                            
                            await self._emit_event('agent_reconnected', {
                                'agent_id': self.agent_id,
                                'attempt': reconnect_count
                            })
                            
                        except Exception as e:
                            logger.error(f"Reconnection failed: {e}")
                            reconnect_count += 1
                            self.connected = False
                
                await asyncio.sleep(self.reconnect_interval)
                
            except Exception as e:
                logger.error(f"Reconnect loop error: {e}")
                await asyncio.sleep(self.reconnect_interval)
    
    async def _task_processor_loop(self):
        """Process tasks from the queue."""
        while self.running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                # Check if task is expired
                if task.is_expired():
                    logger.warning(f"Task {task.task_id} expired, skipping")
                    self.metrics['tasks_failed'] += 1
                    continue
                
                # Add to active tasks
                self.active_tasks[task.task_id] = task
                
                try:
                    # Process task
                    logger.debug(f"Processing task {task.task_id}")
                    
                    await self.broadcast_update(
                        'STATUS_CHANGE',
                        {'status': 'processing'},
                        {'task_id': task.task_id}
                    )
                    
                    result = await self.process_task(task)
                    
                    # Broadcast result
                    await self.broadcast_update(
                        'RESULT_AVAILABLE',
                        result,
                        {'task_id': task.task_id}
                    )
                    
                    self.metrics['tasks_completed'] += 1
                    logger.debug(f"Task {task.task_id} completed")
                    
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    
                    await self.broadcast_update(
                        'ERROR_OCCURRED',
                        {'error': str(e)},
                        {'task_id': task.task_id}
                    )
                    
                    self.metrics['tasks_failed'] += 1
                
                finally:
                    # Remove from active tasks
                    self.active_tasks.pop(task.task_id, None)
                
            except asyncio.TimeoutError:
                # No tasks available, continue
                pass
            except Exception as e:
                logger.error(f"Task processor error: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_stream_loop(self):
        """Handle bidirectional update streaming."""
        while self.running:
            try:
                if self.connected and self.coordinator_stub:
                    # Create bidirectional stream
                    async def request_generator():
                        while self.running:
                            try:
                                update = await asyncio.wait_for(
                                    self.pending_updates.get(),
                                    timeout=1.0
                                )
                                yield update
                            except asyncio.TimeoutError:
                                # Send heartbeat update
                                yield {
                                    'agent_id': self.agent_id,
                                    'task_id': '',
                                    'type': 'HEARTBEAT',
                                    'payload': {},
                                    'timestamp': time.time(),
                                    'metadata': {}
                                }
                    
                    # Start streaming
                    stream = self.coordinator_stub.StreamUpdates(request_generator())
                    
                    async for update in stream:
                        self.metrics['updates_received'] += 1
                        
                        # Handle incoming update
                        await self._handle_update(update)
                
            except Exception as e:
                logger.error(f"Update stream error: {e}")
                self.connected = False
                await asyncio.sleep(5.0)
    
    async def _handle_update(self, update: Dict[str, Any]):
        """Handle an incoming update from another agent."""
        try:
            update_type = update.get('type', 'UNKNOWN')
            
            # Emit event for custom handling
            await self._emit_event(f'update_{update_type.lower()}', update)
            
            # Default handling for common update types
            if update_type == 'TASK_REQUEST':
                # Add task to queue
                task = AgentTask(
                    task_id=update['task_id'],
                    payload=update['payload'],
                    priority=update.get('priority', 1),
                    deadline=update.get('deadline'),
                    dependent_agents=update.get('dependent_agents', []),
                    metadata=update.get('metadata', {})
                )
                
                await self.task_queue.put(task)
                self.metrics['tasks_received'] += 1
                
        except Exception as e:
            logger.error(f"Failed to handle update: {e}")
    
    async def _metrics_loop(self):
        """Collect and publish metrics periodically."""
        while self.running:
            try:
                # Collect custom metrics
                custom_metrics = await self.get_custom_metrics()
                
                # Combine with base metrics
                all_metrics = {
                    **self.metrics,
                    **custom_metrics,
                    'queue_depth': self.task_queue.qsize(),
                    'active_tasks': len(self.active_tasks)
                }
                
                # Publish to Redis
                await self.redis.hset(
                    f"agents:metrics:{self.agent_id}",
                    mapping={k: str(v) for k, v in all_metrics.items()}
                )
                
                # Set expiry
                await self.redis.expire(f"agents:metrics:{self.agent_id}", 300)
                
                await asyncio.sleep(30)  # Publish every 30 seconds
                
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(30)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered handlers."""
        handlers = self._event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler error for {event_type}: {e}")


# Example specialized agent implementations
class PlannerAgent(BaseAgent):
    """Example Planner agent implementation."""
    
    def __init__(self, **kwargs):
        capabilities = [
            AgentCapability("planning", "1.0", "Task planning and orchestration"),
            AgentCapability("scheduling", "1.0", "Resource scheduling"),
            AgentCapability("optimization", "1.0", "Workflow optimization")
        ]
        super().__init__("planner", capabilities, **kwargs)
    
    async def process_task(self, task: AgentTask) -> Any:
        """Process planning tasks."""
        # Deserialize task payload
        # task_data = planning_pb2.PlanningRequest()
        # task_data.ParseFromString(task.payload)
        
        # Simulate planning logic
        await asyncio.sleep(0.1)
        
        # Return plan
        return {
            'plan_id': f"plan_{uuid.uuid4().hex[:8]}",
            'steps': [
                {'agent': 'coder', 'action': 'implement'},
                {'agent': 'tester', 'action': 'test'},
                {'agent': 'reviewer', 'action': 'review'}
            ],
            'estimated_duration': 300
        }
    
    async def get_custom_metrics(self) -> Dict[str, float]:
        """Get planner-specific metrics."""
        return {
            'plans_created': 42,
            'average_plan_complexity': 3.5
        }


class SecurityAgent(BaseAgent):
    """Example Security agent implementation."""
    
    def __init__(self, **kwargs):
        capabilities = [
            AgentCapability("vulnerability_scanning", "1.0", "Security vulnerability detection"),
            AgentCapability("code_analysis", "1.0", "Static code security analysis"),
            AgentCapability("dependency_check", "1.0", "Dependency vulnerability checking")
        ]
        super().__init__("security", capabilities, **kwargs)
        self.scan_cache = {}
    
    async def process_task(self, task: AgentTask) -> Any:
        """Process security scanning tasks."""
        # Simulate security scan
        await asyncio.sleep(0.5)
        
        return {
            'scan_id': f"scan_{uuid.uuid4().hex[:8]}",
            'vulnerabilities': [],
            'risk_score': 0.2,
            'recommendations': [
                'Update dependencies to latest versions',
                'Enable security headers'
            ]
        }
    
    async def get_custom_metrics(self) -> Dict[str, float]:
        """Get security-specific metrics."""
        return {
            'vulnerabilities_found': 3,
            'scans_completed': 127,
            'average_risk_score': 0.25
        }


class AgentMetrics:
    """
    Production-ready metrics collection for agents.
    Tracks performance, success rates, and operational metrics.
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time = time.time()
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "average_response_time": 0.0,
            "last_request_time": None,
            "errors": [],
            "request_history": []
        }
        self.logger = logging.getLogger(f"agent.{agent_name}")
    
    def record_request_start(self) -> float:
        """Call this at the start of each agent operation"""
        return time.time()
    
    def record_request_end(self, start_time: float, success: bool, error_msg: str = None, 
                          task_type: str = None, input_size: int = None):
        """Call this at the end of each agent operation with ACTUAL results"""
        response_time = time.time() - start_time
        current_time = datetime.now().isoformat()
        
        self.metrics["total_requests"] += 1
        self.metrics["total_response_time"] += response_time
        self.metrics["average_response_time"] = (
            self.metrics["total_response_time"] / self.metrics["total_requests"]
        )
        self.metrics["last_request_time"] = current_time
        
        # Record in history (keep last 100 requests)
        request_record = {
            "timestamp": current_time,
            "response_time": response_time,
            "success": success,
            "task_type": task_type,
            "input_size": input_size
        }
        
        self.metrics["request_history"].append(request_record)
        if len(self.metrics["request_history"]) > 100:
            self.metrics["request_history"].pop(0)
        
        if success:
            self.metrics["successful_requests"] += 1
            self.logger.info(
                f"Request completed successfully",
                extra={
                    "response_time": response_time,
                    "task_type": task_type,
                    "input_size": input_size
                }
            )
        else:
            self.metrics["failed_requests"] += 1
            if error_msg:
                error_record = {
                    "timestamp": current_time,
                    "error": error_msg,
                    "response_time": response_time,
                    "task_type": task_type
                }
                self.metrics["errors"].append(error_record)
                # Keep only last 50 errors
                if len(self.metrics["errors"]) > 50:
                    self.metrics["errors"].pop(0)
            
            self.logger.error(
                f"Request failed",
                extra={
                    "response_time": response_time,
                    "error": error_msg,
                    "task_type": task_type,
                    "input_size": input_size
                }
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return comprehensive metrics - NO FAKE DATA"""
        uptime = time.time() - self.start_time
        success_rate = (
            (self.metrics["successful_requests"] / self.metrics["total_requests"])
            if self.metrics["total_requests"] > 0 else 0
        )
        
        # Calculate percentiles from recent requests
        recent_times = [
            req["response_time"] 
            for req in self.metrics["request_history"]
            if req["success"]
        ]
        
        percentiles = {}
        if recent_times:
            recent_times.sort()
            percentiles = {
                "p50": recent_times[len(recent_times) // 2] if recent_times else 0,
                "p95": recent_times[int(len(recent_times) * 0.95)] if recent_times else 0,
                "p99": recent_times[int(len(recent_times) * 0.99)] if recent_times else 0
            }
        
        # Determine health status
        status = "healthy"
        if success_rate < 0.5:
            status = "critical"
        elif success_rate < 0.8:
            status = "degraded"
        elif uptime < 60:  # Less than 1 minute uptime
            status = "starting"
        
        return {
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "status": status,
            "performance": {
                "success_rate_percent": round(success_rate * 100, 2),
                "total_requests": self.metrics["total_requests"],
                "successful_requests": self.metrics["successful_requests"],
                "failed_requests": self.metrics["failed_requests"],
                "average_response_time": round(self.metrics["average_response_time"], 3),
                "response_time_percentiles": percentiles
            },
            "recent_activity": {
                "last_request_time": self.metrics["last_request_time"],
                "requests_last_hour": len([
                    req for req in self.metrics["request_history"]
                    if (time.time() - time.mktime(
                        datetime.fromisoformat(req["timestamp"]).timetuple()
                    )) < 3600
                ]),
                "recent_errors": len([
                    err for err in self.metrics["errors"]
                    if (time.time() - time.mktime(
                        datetime.fromisoformat(err["timestamp"]).timetuple()
                    )) < 3600
                ])
            },
            "error_summary": {
                "total_errors": len(self.metrics["errors"]),
                "recent_error_types": list(set([
                    err.get("error", "Unknown")[:50] 
                    for err in self.metrics["errors"][-10:]
                ]))
            }
        }
    
    def get_prometheus_metrics(self) -> str:
        """Return metrics in Prometheus format"""
        metrics = self.get_metrics()
        
        prometheus_lines = [
            f'# HELP agent_uptime_seconds Agent uptime in seconds',
            f'# TYPE agent_uptime_seconds gauge',
            f'agent_uptime_seconds{{agent="{self.agent_name}"}} {metrics["uptime_seconds"]}',
            f'',
            f'# HELP agent_requests_total Total number of requests processed',
            f'# TYPE agent_requests_total counter', 
            f'agent_requests_total{{agent="{self.agent_name}",status="success"}} {metrics["performance"]["successful_requests"]}',
            f'agent_requests_total{{agent="{self.agent_name}",status="failure"}} {metrics["performance"]["failed_requests"]}',
            f'',
            f'# HELP agent_response_time_seconds Average response time in seconds',
            f'# TYPE agent_response_time_seconds gauge',
            f'agent_response_time_seconds{{agent="{self.agent_name}"}} {metrics["performance"]["average_response_time"]}',
            f'',
            f'# HELP agent_success_rate Success rate as a percentage',
            f'# TYPE agent_success_rate gauge',
            f'agent_success_rate{{agent="{self.agent_name}"}} {metrics["performance"]["success_rate_percent"] / 100}',
        ]
        
        return '\n'.join(prometheus_lines)


# Enhanced base agent class with metrics
class MetricsEnabledBaseAgent(BaseAgent):
    """
    Enhanced BaseAgent with built-in metrics collection.
    Use this as the base class for all production agents.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = AgentMetrics(self.__class__.__name__)
    
    async def process_with_metrics(self, task_data: Any, task_type: str = None) -> Any:
        """
        Process a task with automatic metrics collection.
        Override this method in your agent implementations.
        """
        start_time = self.metrics.record_request_start()
        try:
            # Subclasses should implement the actual processing
            result = await self._process_task(task_data, task_type)
            self.metrics.record_request_end(
                start_time, 
                success=True, 
                task_type=task_type,
                input_size=len(str(task_data)) if task_data else 0
            )
            return result
        except Exception as e:
            self.metrics.record_request_end(
                start_time, 
                success=False, 
                error_msg=str(e), 
                task_type=task_type,
                input_size=len(str(task_data)) if task_data else 0
            )
            raise
    
    async def _process_task(self, task_data: Any, task_type: str = None) -> Any:
        """
        Override this method in your agent implementations.
        This is where the actual agent logic goes.
        """
        raise NotImplementedError("Subclasses must implement _process_task")
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """Return comprehensive agent metrics"""
        return self.metrics.get_metrics()
    
    def get_prometheus_metrics(self) -> str:
        """Return metrics in Prometheus format"""
        return self.metrics.get_prometheus_metrics()


# Example specialized agent implementations
class CodeGenerationAgent(MetricsEnabledBaseAgent):
    """Example code generation agent with metrics"""
    
    async def _process_task(self, task_data: Any, task_type: str = None) -> Any:
        """Process code generation request"""
        # Simulate code generation work
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Return generated code (this would be real code generation in production)
        return {
            "generated_code": f"# Generated code for: {task_data}",
            "files_created": 3,
            "lines_of_code": 150
        }


class ReviewAgent(MetricsEnabledBaseAgent):
    """Example code review agent with metrics"""
    
    async def _process_task(self, task_data: Any, task_type: str = None) -> Any:
        """Process code review request"""
        # Simulate code review work
        await asyncio.sleep(0.3)  # Simulate processing time
        
        return {
            "review_comments": ["Good structure", "Consider error handling"],
            "score": 8.5,
            "issues_found": 2
        }