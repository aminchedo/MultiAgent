"""
Agent Discovery Service

This service manages agent registration, discovery, and health monitoring
using Redis as the distributed backend for high availability.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
from redis.asyncio.lock import Lock
import grpc
from grpc import aio

# Import generated protobuf classes (these would be generated from agent_comm.proto)
# from proto import agent_comm_pb2, agent_comm_pb2_grpc

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for agent selection."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_LOAD = "least_load"
    RANDOM = "random"
    WEIGHTED = "weighted"


@dataclass
class AgentInfo:
    """Agent information stored in the registry."""
    agent_id: str
    agent_type: str
    endpoint: str
    capabilities: List[str]
    ip: str
    port: int
    load: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    queued_tasks: int = 0
    state: str = "READY"
    last_heartbeat: float = 0.0
    registered_at: float = 0.0
    metadata: Dict[str, str] = None
    health_score: float = 1.0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_heartbeat == 0.0:
            self.last_heartbeat = time.time()
        if self.registered_at == 0.0:
            self.registered_at = time.time()
    
    def to_redis_hash(self) -> Dict[str, str]:
        """Convert to Redis hash format."""
        data = asdict(self)
        # Convert lists and dicts to JSON strings
        data['capabilities'] = json.dumps(data['capabilities'])
        data['metadata'] = json.dumps(data['metadata'])
        # Convert all values to strings
        return {k: str(v) for k, v in data.items()}
    
    @classmethod
    def from_redis_hash(cls, data: Dict[bytes, bytes]) -> 'AgentInfo':
        """Create from Redis hash data."""
        # Decode bytes to strings
        decoded = {k.decode(): v.decode() for k, v in data.items()}
        
        # Parse JSON fields
        decoded['capabilities'] = json.loads(decoded.get('capabilities', '[]'))
        decoded['metadata'] = json.loads(decoded.get('metadata', '{}'))
        
        # Convert numeric fields
        for field in ['port', 'active_tasks', 'queued_tasks']:
            if field in decoded:
                decoded[field] = int(decoded[field])
        
        for field in ['load', 'cpu_usage', 'memory_usage', 'last_heartbeat', 
                      'registered_at', 'health_score']:
            if field in decoded:
                decoded[field] = float(decoded[field])
        
        return cls(**decoded)


class DiscoveryService:
    """
    Agent Discovery Service with Redis backend.
    
    Features:
    - Dynamic agent registration/deregistration
    - Health monitoring with configurable timeout
    - Load-based routing strategies
    - Capability-based discovery
    - Automatic cleanup of stale agents
    - Real-time status updates via pub/sub
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        health_check_interval: int = 2,
        health_check_timeout: int = 5,
        stale_agent_timeout: int = 30,
        namespace: str = "agents"
    ):
        self.redis_url = redis_url
        self.health_check_interval = health_check_interval
        self.health_check_timeout = health_check_timeout
        self.stale_agent_timeout = stale_agent_timeout
        self.namespace = namespace
        
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Round-robin state
        self._round_robin_counters: Dict[str, int] = {}
    
    async def start(self):
        """Start the discovery service."""
        logger.info("Starting discovery service...")
        
        # Connect to Redis
        self.redis = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False
        )
        
        # Setup pub/sub
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(f"{self.namespace}:events")
        
        self._running = True
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Discovery service started")
    
    async def stop(self):
        """Stop the discovery service."""
        logger.info("Stopping discovery service...")
        
        self._running = False
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close connections
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis:
            await self.redis.close()
        
        logger.info("Discovery service stopped")
    
    async def register_agent(self, agent_info: AgentInfo) -> str:
        """
        Register a new agent in the discovery system.
        
        Returns the assigned agent ID.
        """
        # Generate ID if not provided
        if not agent_info.agent_id:
            agent_info.agent_id = f"{agent_info.agent_type}_{uuid.uuid4().hex[:8]}"
        
        # Store agent info in Redis hash
        key = f"{self.namespace}:active:{agent_info.agent_id}"
        await self.redis.hset(key, mapping=agent_info.to_redis_hash())
        
        # Add to capability sets
        for capability in agent_info.capabilities:
            await self.redis.sadd(
                f"{self.namespace}:capability:{capability}",
                agent_info.agent_id
            )
        
        # Add to type set
        await self.redis.sadd(
            f"{self.namespace}:type:{agent_info.agent_type}",
            agent_info.agent_id
        )
        
        # Add to all agents set
        await self.redis.sadd(f"{self.namespace}:all", agent_info.agent_id)
        
        # Publish registration event
        await self._publish_event({
            'type': 'agent_registered',
            'agent_id': agent_info.agent_id,
            'agent_type': agent_info.agent_type,
            'capabilities': agent_info.capabilities,
            'timestamp': time.time()
        })
        
        logger.info(f"Registered agent: {agent_info.agent_id}")
        return agent_info.agent_id
    
    async def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an agent from the discovery system."""
        # Get agent info first
        agent_info = await self.get_agent(agent_id)
        if not agent_info:
            return False
        
        # Remove from capability sets
        for capability in agent_info.capabilities:
            await self.redis.srem(
                f"{self.namespace}:capability:{capability}",
                agent_id
            )
        
        # Remove from type set
        await self.redis.srem(
            f"{self.namespace}:type:{agent_info.agent_type}",
            agent_id
        )
        
        # Remove from all agents set
        await self.redis.srem(f"{self.namespace}:all", agent_id)
        
        # Delete agent hash
        await self.redis.delete(f"{self.namespace}:active:{agent_id}")
        
        # Publish deregistration event
        await self._publish_event({
            'type': 'agent_deregistered',
            'agent_id': agent_id,
            'timestamp': time.time()
        })
        
        logger.info(f"Deregistered agent: {agent_id}")
        return True
    
    async def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get information about a specific agent."""
        key = f"{self.namespace}:active:{agent_id}"
        data = await self.redis.hgetall(key)
        
        if not data:
            return None
        
        return AgentInfo.from_redis_hash(data)
    
    async def discover_agents(
        self,
        capabilities: Optional[List[str]] = None,
        agent_type: Optional[str] = None,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOAD,
        max_results: int = 10,
        min_health_score: float = 0.5
    ) -> List[AgentInfo]:
        """
        Discover agents based on capabilities and type.
        
        Args:
            capabilities: Required capabilities (ALL must be present)
            agent_type: Filter by agent type
            strategy: Load balancing strategy
            max_results: Maximum number of agents to return
            min_health_score: Minimum health score threshold
        
        Returns:
            List of matching agents sorted by the selected strategy
        """
        # Get candidate agent IDs
        agent_ids = set()
        
        if capabilities:
            # Get agents with all required capabilities (intersection)
            capability_sets = []
            for capability in capabilities:
                members = await self.redis.smembers(
                    f"{self.namespace}:capability:{capability}"
                )
                capability_sets.append({m.decode() for m in members})
            
            if capability_sets:
                agent_ids = set.intersection(*capability_sets)
            else:
                return []
        
        if agent_type:
            # Filter by type
            type_members = await self.redis.smembers(
                f"{self.namespace}:type:{agent_type}"
            )
            type_ids = {m.decode() for m in type_members}
            
            if agent_ids:
                agent_ids = agent_ids.intersection(type_ids)
            else:
                agent_ids = type_ids
        
        if not agent_ids and not capabilities and not agent_type:
            # Get all agents
            all_members = await self.redis.smembers(f"{self.namespace}:all")
            agent_ids = {m.decode() for m in all_members}
        
        # Load agent information
        agents = []
        for agent_id in agent_ids:
            agent = await self.get_agent(agent_id)
            if agent and agent.health_score >= min_health_score:
                agents.append(agent)
        
        # Apply load balancing strategy
        agents = self._apply_strategy(agents, strategy)
        
        # Limit results
        return agents[:max_results]
    
    async def update_agent_status(
        self,
        agent_id: str,
        state: Optional[str] = None,
        load: Optional[float] = None,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        active_tasks: Optional[int] = None,
        queued_tasks: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """Update agent status information."""
        key = f"{self.namespace}:active:{agent_id}"
        
        # Check if agent exists
        if not await self.redis.exists(key):
            return False
        
        # Build update dict
        updates = {}
        if state is not None:
            updates['state'] = str(state)
        if load is not None:
            updates['load'] = str(load)
        if cpu_usage is not None:
            updates['cpu_usage'] = str(cpu_usage)
        if memory_usage is not None:
            updates['memory_usage'] = str(memory_usage)
        if active_tasks is not None:
            updates['active_tasks'] = str(active_tasks)
        if queued_tasks is not None:
            updates['queued_tasks'] = str(queued_tasks)
        
        # Update heartbeat
        updates['last_heartbeat'] = str(time.time())
        
        # Update metadata if provided
        if metadata:
            current_metadata = await self.redis.hget(key, 'metadata')
            if current_metadata:
                current = json.loads(current_metadata.decode())
                current.update(metadata)
                updates['metadata'] = json.dumps(current)
            else:
                updates['metadata'] = json.dumps(metadata)
        
        # Apply updates
        await self.redis.hset(key, mapping=updates)
        
        # Recalculate health score
        await self._update_health_score(agent_id)
        
        # Publish status update event
        await self._publish_event({
            'type': 'agent_status_updated',
            'agent_id': agent_id,
            'updates': updates,
            'timestamp': time.time()
        })
        
        return True
    
    async def heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat timestamp."""
        key = f"{self.namespace}:active:{agent_id}"
        
        if not await self.redis.exists(key):
            return False
        
        await self.redis.hset(key, 'last_heartbeat', str(time.time()))
        return True
    
    def _apply_strategy(
        self,
        agents: List[AgentInfo],
        strategy: LoadBalancingStrategy
    ) -> List[AgentInfo]:
        """Apply load balancing strategy to sort agents."""
        
        if strategy == LoadBalancingStrategy.LEAST_LOAD:
            # Sort by load (ascending)
            return sorted(agents, key=lambda a: a.load)
        
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            # Sort by active tasks (ascending)
            return sorted(agents, key=lambda a: a.active_tasks)
        
        elif strategy == LoadBalancingStrategy.WEIGHTED:
            # Sort by health score (descending) then load (ascending)
            return sorted(
                agents,
                key=lambda a: (-a.health_score, a.load)
            )
        
        elif strategy == LoadBalancingStrategy.RANDOM:
            # Random shuffle
            import random
            shuffled = agents.copy()
            random.shuffle(shuffled)
            return shuffled
        
        elif strategy == LoadBalancingStrategy.ROUND_ROBIN:
            # Round-robin requires state tracking
            # For discovery, we just return in registration order
            return sorted(agents, key=lambda a: a.registered_at)
        
        return agents
    
    async def _update_health_score(self, agent_id: str):
        """Calculate and update agent health score."""
        agent = await self.get_agent(agent_id)
        if not agent:
            return
        
        score = 1.0
        
        # Factor 1: Load (0.0 = best, 1.0 = worst)
        load_penalty = agent.load * 0.3
        score -= load_penalty
        
        # Factor 2: CPU usage
        if agent.cpu_usage > 0.8:
            score -= 0.2
        elif agent.cpu_usage > 0.6:
            score -= 0.1
        
        # Factor 3: Memory usage
        if agent.memory_usage > 0.9:
            score -= 0.2
        elif agent.memory_usage > 0.7:
            score -= 0.1
        
        # Factor 4: Task queue depth
        if agent.queued_tasks > 100:
            score -= 0.2
        elif agent.queued_tasks > 50:
            score -= 0.1
        
        # Factor 5: Recent heartbeat
        time_since_heartbeat = time.time() - agent.last_heartbeat
        if time_since_heartbeat > self.health_check_timeout:
            score -= 0.5
        elif time_since_heartbeat > self.health_check_interval * 2:
            score -= 0.2
        
        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))
        
        # Update score
        await self.redis.hset(
            f"{self.namespace}:active:{agent_id}",
            'health_score',
            str(score)
        )
    
    async def _health_check_loop(self):
        """Background task to perform health checks."""
        while self._running:
            try:
                # Get all active agents
                agent_ids = await self.redis.smembers(f"{self.namespace}:all")
                
                for agent_id_bytes in agent_ids:
                    agent_id = agent_id_bytes.decode()
                    agent = await self.get_agent(agent_id)
                    
                    if not agent:
                        continue
                    
                    # Check if agent is stale
                    time_since_heartbeat = time.time() - agent.last_heartbeat
                    
                    if time_since_heartbeat > self.stale_agent_timeout:
                        # Mark as error state
                        await self.update_agent_status(
                            agent_id,
                            state="ERROR"
                        )
                        logger.warning(
                            f"Agent {agent_id} marked as ERROR "
                            f"(no heartbeat for {time_since_heartbeat:.1f}s)"
                        )
                    elif time_since_heartbeat > self.health_check_timeout:
                        # Update health score
                        await self._update_health_score(agent_id)
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _cleanup_loop(self):
        """Background task to cleanup stale agents."""
        while self._running:
            try:
                # Run cleanup every minute
                await asyncio.sleep(60)
                
                # Get all active agents
                agent_ids = await self.redis.smembers(f"{self.namespace}:all")
                
                for agent_id_bytes in agent_ids:
                    agent_id = agent_id_bytes.decode()
                    agent = await self.get_agent(agent_id)
                    
                    if not agent:
                        continue
                    
                    # Remove agents that have been in ERROR state too long
                    if agent.state == "ERROR":
                        time_since_heartbeat = time.time() - agent.last_heartbeat
                        if time_since_heartbeat > self.stale_agent_timeout * 2:
                            await self.deregister_agent(agent_id)
                            logger.info(
                                f"Cleaned up stale agent {agent_id} "
                                f"(ERROR state for {time_since_heartbeat:.1f}s)"
                            )
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _publish_event(self, event: Dict):
        """Publish an event to the Redis pub/sub channel."""
        try:
            await self.redis.publish(
                f"{self.namespace}:events",
                json.dumps(event)
            )
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")


# gRPC Service Implementation (would use generated pb2_grpc base class)
class AgentRegistryServicer:
    """gRPC service implementation for agent registry."""
    
    def __init__(self, discovery_service: DiscoveryService):
        self.discovery = discovery_service
    
    async def RegisterAgent(self, request, context):
        """Register a new agent."""
        try:
            agent_info = AgentInfo(
                agent_id=request.agent_id,
                agent_type=request.agent_type,
                endpoint=request.endpoint,
                capabilities=list(request.capabilities),
                ip=request.endpoint.split(':')[0],
                port=int(request.endpoint.split(':')[1]),
                metadata=dict(request.metadata)
            )
            
            agent_id = await self.discovery.register_agent(agent_info)
            
            # Generate auth token (would use JWTTokenManager)
            token = f"dummy_token_{agent_id}"  # Placeholder
            
            return {
                'success': True,
                'agent_id': agent_id,
                'auth_token': token,
                'expires_at': int(time.time() + 3600)
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                f"Registration failed: {str(e)}"
            )
    
    async def DeregisterAgent(self, request, context):
        """Deregister an agent."""
        success = await self.discovery.deregister_agent(request.agent_id)
        
        if not success:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Agent {request.agent_id} not found"
            )
        
        return {'success': True, 'message': 'Agent deregistered'}
    
    async def DiscoverAgents(self, request, context):
        """Discover agents by capability."""
        agents = await self.discovery.discover_agents(
            capabilities=list(request.required_capabilities),
            strategy=LoadBalancingStrategy(request.strategy.lower()),
            max_results=request.max_results or 10
        )
        
        # Convert to proto format
        agent_protos = []
        for agent in agents:
            agent_protos.append({
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type,
                'capabilities': agent.capabilities,
                'endpoint': agent.endpoint,
                'metadata': agent.metadata,
                'resources': {
                    'cpu_usage': agent.cpu_usage,
                    'memory_usage': agent.memory_usage,
                    'active_tasks': agent.active_tasks,
                    'queued_tasks': agent.queued_tasks
                }
            })
        
        return {
            'agents': agent_protos,
            'as_of': int(time.time())
        }
    
    async def GetAgentStatus(self, request, context):
        """Get status of a specific agent."""
        agent = await self.discovery.get_agent(request.agent_id)
        
        if not agent:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Agent {request.agent_id} not found"
            )
        
        return {
            'agent_id': agent.agent_id,
            'state': agent.state,
            'load': agent.load,
            'resources': {
                'cpu_usage': agent.cpu_usage,
                'memory_usage': agent.memory_usage,
                'active_tasks': agent.active_tasks,
                'queued_tasks': agent.queued_tasks
            },
            'last_heartbeat': int(agent.last_heartbeat),
            'metadata': agent.metadata
        }
    
    async def StreamAgentUpdates(self, request, context):
        """Stream agent status updates."""
        # Subscribe to Redis pub/sub
        pubsub = self.discovery.redis.pubsub()
        await pubsub.subscribe(f"{self.discovery.namespace}:events")
        
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    event = json.loads(message['data'])
                    
                    # Filter by requested agent IDs if specified
                    if request.agent_ids:
                        if event.get('agent_id') not in request.agent_ids:
                            continue
                    
                    # Create status update
                    if event['type'] in ['agent_status_updated', 'agent_registered']:
                        agent = await self.discovery.get_agent(event['agent_id'])
                        if agent:
                            yield {
                                'status': {
                                    'agent_id': agent.agent_id,
                                    'state': agent.state,
                                    'load': agent.load,
                                    'resources': {
                                        'cpu_usage': agent.cpu_usage,
                                        'memory_usage': agent.memory_usage,
                                        'active_tasks': agent.active_tasks,
                                        'queued_tasks': agent.queued_tasks
                                    },
                                    'last_heartbeat': int(agent.last_heartbeat),
                                    'metadata': agent.metadata
                                },
                                'update_type': event['type'].upper()
                            }
                    
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()