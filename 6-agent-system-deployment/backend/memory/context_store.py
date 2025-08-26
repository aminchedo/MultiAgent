"""
Shared Memory Store for Agent Context Sharing

This module provides a Redis-based shared memory system for agents to share
context, intermediate results, and collaborative data.
"""

import json
import pickle
import asyncio
from typing import Any, Optional, Dict, List, Set
from datetime import datetime, timedelta
import hashlib

import redis.asyncio as redis
from redis.asyncio.lock import Lock
import structlog
import msgpack


logger = structlog.get_logger()


class SharedMemoryStore:
    """
    Redis-based shared memory store for agent collaboration.
    
    Supports various data types, TTL, namespacing, and atomic operations.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 namespace: str = "agent_context"):
        self.redis_url = redis_url
        self.namespace = namespace
        self.redis_client: Optional[redis.Redis] = None
        self._connection_pool = None
        
        # Serialization strategies
        self.serializers = {
            'json': (json.dumps, json.loads),
            'pickle': (pickle.dumps, pickle.loads),
            'msgpack': (msgpack.packb, msgpack.unpackb)
        }
        self.default_serializer = 'msgpack'
    
    async def connect(self):
        """Establish connection to Redis"""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=False,
                max_connections=50
            )
            self.redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis shared memory store", url=self.redis_url)
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            await self._connection_pool.disconnect()
            logger.info("Disconnected from Redis")
    
    def _make_key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.namespace}:{key}"
    
    def _serialize(self, value: Any, serializer: str = None) -> bytes:
        """Serialize value for storage"""
        serializer = serializer or self.default_serializer
        if serializer not in self.serializers:
            raise ValueError(f"Unknown serializer: {serializer}")
        
        serializer_func, _ = self.serializers[serializer]
        
        # Add metadata
        wrapped = {
            '_value': value,
            '_serializer': serializer,
            '_timestamp': datetime.utcnow().isoformat(),
            '_type': type(value).__name__
        }
        
        if serializer == 'msgpack':
            return msgpack.packb(wrapped, use_bin_type=True)
        else:
            return serializer_func(wrapped).encode('utf-8')
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        if not data:
            return None
        
        # Try msgpack first (default)
        try:
            wrapped = msgpack.unpackb(data, raw=False)
        except:
            # Fallback to JSON
            try:
                wrapped = json.loads(data.decode('utf-8'))
            except:
                # Final fallback to pickle
                wrapped = pickle.loads(data)
        
        if isinstance(wrapped, dict) and '_value' in wrapped:
            return wrapped['_value']
        return wrapped
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  serializer: str = None) -> bool:
        """
        Set a value in shared memory.
        
        Args:
            key: The key to store under
            value: The value to store
            ttl: Time to live in seconds
            serializer: Serialization method to use
            
        Returns:
            True if successful
        """
        try:
            full_key = self._make_key(key)
            serialized = self._serialize(value, serializer)
            
            if ttl:
                await self.redis_client.setex(full_key, ttl, serialized)
            else:
                await self.redis_client.set(full_key, serialized)
            
            logger.debug("Stored value in shared memory", key=key, ttl=ttl)
            return True
        except Exception as e:
            logger.error("Failed to store value", key=key, error=str(e))
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from shared memory.
        
        Args:
            key: The key to retrieve
            default: Default value if key not found
            
        Returns:
            The stored value or default
        """
        try:
            full_key = self._make_key(key)
            data = await self.redis_client.get(full_key)
            
            if data is None:
                return default
            
            return self._deserialize(data)
        except Exception as e:
            logger.error("Failed to retrieve value", key=key, error=str(e))
            return default
    
    async def delete(self, key: str) -> bool:
        """Delete a key from shared memory"""
        try:
            full_key = self._make_key(key)
            result = await self.redis_client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error("Failed to delete key", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists"""
        full_key = self._make_key(key)
        return await self.redis_client.exists(full_key) > 0
    
    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values at once"""
        full_keys = [self._make_key(k) for k in keys]
        values = await self.redis_client.mget(full_keys)
        
        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                result[key] = self._deserialize(value)
        
        return result
    
    async def set_multiple(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values at once"""
        try:
            # Prepare data
            mapping = {}
            for key, value in data.items():
                full_key = self._make_key(key)
                mapping[full_key] = self._serialize(value)
            
            # Set all values
            await self.redis_client.mset(mapping)
            
            # Apply TTL if specified
            if ttl:
                pipe = self.redis_client.pipeline()
                for full_key in mapping.keys():
                    pipe.expire(full_key, ttl)
                await pipe.execute()
            
            return True
        except Exception as e:
            logger.error("Failed to set multiple values", error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomic increment operation"""
        full_key = self._make_key(key)
        return await self.redis_client.incrby(full_key, amount)
    
    async def append_to_list(self, key: str, value: Any, max_length: Optional[int] = None) -> int:
        """Append to a list in shared memory"""
        full_key = self._make_key(key)
        serialized = self._serialize(value)
        
        pipe = self.redis_client.pipeline()
        pipe.rpush(full_key, serialized)
        
        if max_length:
            pipe.ltrim(full_key, -max_length, -1)
        
        results = await pipe.execute()
        return results[0]
    
    async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get a list from shared memory"""
        full_key = self._make_key(key)
        items = await self.redis_client.lrange(full_key, start, end)
        return [self._deserialize(item) for item in items]
    
    async def add_to_set(self, key: str, *values: Any) -> int:
        """Add values to a set"""
        full_key = self._make_key(key)
        serialized = [self._serialize(v) for v in values]
        return await self.redis_client.sadd(full_key, *serialized)
    
    async def get_set(self, key: str) -> Set[Any]:
        """Get all members of a set"""
        full_key = self._make_key(key)
        members = await self.redis_client.smembers(full_key)
        return {self._deserialize(m) for m in members}
    
    async def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel"""
        full_channel = self._make_key(channel)
        serialized = self._serialize(message)
        return await self.redis_client.publish(full_channel, serialized)
    
    async def subscribe(self, channels: List[str]) -> 'ContextSubscriber':
        """Subscribe to channels for real-time updates"""
        pubsub = self.redis_client.pubsub()
        full_channels = [self._make_key(ch) for ch in channels]
        await pubsub.subscribe(*full_channels)
        
        return ContextSubscriber(pubsub, self)
    
    async def acquire_lock(self, key: str, timeout: int = 10, 
                          blocking: bool = True) -> Optional[Lock]:
        """Acquire a distributed lock"""
        full_key = self._make_key(f"lock:{key}")
        lock = self.redis_client.lock(
            full_key, 
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=5
        )
        
        acquired = await lock.acquire()
        if acquired:
            return lock
        return None
    
    async def store_agent_result(self, agent_id: str, task_id: str, 
                                result: Any, metadata: Dict[str, Any] = None):
        """Store an agent's task result with metadata"""
        key = f"agent_result:{agent_id}:{task_id}"
        
        data = {
            'agent_id': agent_id,
            'task_id': task_id,
            'result': result,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.set(key, data, ttl=3600)  # 1 hour TTL
        
        # Also add to agent's result history
        history_key = f"agent_history:{agent_id}"
        await self.append_to_list(history_key, task_id, max_length=100)
    
    async def get_agent_result(self, agent_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an agent's task result"""
        key = f"agent_result:{agent_id}:{task_id}"
        return await self.get(key)
    
    async def create_checkpoint(self, checkpoint_id: str, data: Dict[str, Any]):
        """Create a checkpoint of current state"""
        key = f"checkpoint:{checkpoint_id}"
        checkpoint = {
            'id': checkpoint_id,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.set(key, checkpoint, ttl=86400)  # 24 hour TTL
        
        # Add to checkpoint index
        await self.add_to_set("checkpoints", checkpoint_id)
    
    async def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Restore from a checkpoint"""
        key = f"checkpoint:{checkpoint_id}"
        checkpoint = await self.get(key)
        
        if checkpoint:
            return checkpoint.get('data')
        return None
    
    async def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern"""
        full_pattern = self._make_key(pattern)
        cursor = b'0'
        keys = []
        
        while cursor:
            cursor, batch = await self.redis_client.scan(
                cursor, 
                match=full_pattern, 
                count=100
            )
            keys.extend(batch)
        
        # Remove namespace prefix
        prefix_len = len(self.namespace) + 1
        return [k.decode('utf-8')[prefix_len:] for k in keys]
    
    async def cleanup_old_data(self, age_hours: int = 24):
        """Clean up old data based on age"""
        pattern = "*"
        keys = await self.get_keys_by_pattern(pattern)
        
        current_time = datetime.utcnow()
        deleted_count = 0
        
        for key in keys:
            data = await self.get(key)
            if isinstance(data, dict) and '_timestamp' in data:
                timestamp = datetime.fromisoformat(data['_timestamp'])
                age = current_time - timestamp
                
                if age.total_seconds() > age_hours * 3600:
                    if await self.delete(key):
                        deleted_count += 1
        
        logger.info("Cleaned up old data", deleted_count=deleted_count)
        return deleted_count


class ContextSubscriber:
    """Helper class for managing subscriptions"""
    
    def __init__(self, pubsub, memory_store: SharedMemoryStore):
        self.pubsub = pubsub
        self.memory_store = memory_store
    
    async def get_message(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Get next message from subscription"""
        message = await self.pubsub.get_message(timeout=timeout)
        
        if message and message['type'] == 'message':
            data = message['data']
            return self.memory_store._deserialize(data)
        
        return None
    
    async def unsubscribe(self):
        """Unsubscribe from all channels"""
        await self.pubsub.unsubscribe()
        await self.pubsub.close()