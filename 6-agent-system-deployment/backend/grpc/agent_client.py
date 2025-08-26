"""
gRPC Client for Agent Communication

This module provides the client implementation for agent-to-agent and
orchestrator-to-agent communication via gRPC.
"""

import asyncio
import json
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime
import grpc
from google.protobuf import struct_pb2, any_pb2, timestamp_pb2

import structlog

# Note: These imports assume the protobuf files have been compiled
# Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. agent.proto
from . import agent_pb2
from . import agent_pb2_grpc


logger = structlog.get_logger()


def dict_to_struct(data: Dict[str, Any]) -> struct_pb2.Struct:
    """Convert Python dict to protobuf Struct"""
    struct = struct_pb2.Struct()
    struct.update(data)
    return struct


def struct_to_dict(struct: struct_pb2.Struct) -> Dict[str, Any]:
    """Convert protobuf Struct to Python dict"""
    return json.loads(json.dumps(dict(struct)))


def datetime_to_timestamp(dt: datetime) -> timestamp_pb2.Timestamp:
    """Convert Python datetime to protobuf Timestamp"""
    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


class AgentServiceClient:
    """
    gRPC client for communicating with agent services.
    
    Provides high-level methods for task execution, collaboration,
    and context sharing between agents.
    """
    
    def __init__(self, endpoint: str, timeout: int = 30):
        self.endpoint = endpoint
        self.timeout = timeout
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[agent_pb2_grpc.AgentServiceStub] = None
        self._connected = False
    
    async def connect(self):
        """Establish gRPC connection"""
        try:
            # Create channel with retry and keepalive options
            options = [
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
                ('grpc.keepalive_permit_without_calls', True),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
            ]
            
            self.channel = grpc.aio.insecure_channel(
                self.endpoint,
                options=options
            )
            
            self.stub = agent_pb2_grpc.AgentServiceStub(self.channel)
            
            # Test connection with a capabilities request
            await self.get_capabilities("")
            
            self._connected = True
            logger.info("Connected to agent service", endpoint=self.endpoint)
            
        except Exception as e:
            logger.error("Failed to connect to agent service", 
                        endpoint=self.endpoint, error=str(e))
            raise
    
    async def close(self):
        """Close gRPC connection"""
        if self.channel:
            await self.channel.close()
            self._connected = False
            logger.info("Closed connection to agent service", endpoint=self.endpoint)
    
    async def execute_task(self,
                          task_id: str,
                          task_type: str,
                          payload: Dict[str, Any],
                          context: Dict[str, str] = None,
                          dependencies: list = None,
                          priority: int = 3,
                          deadline: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Execute a task on the agent.
        
        Args:
            task_id: Unique task identifier
            task_type: Type of task to execute
            payload: Task payload data
            context: Context information
            dependencies: List of dependent task IDs
            priority: Task priority (1-5)
            deadline: Task deadline
            
        Returns:
            Task execution result
        """
        if not self._connected:
            raise RuntimeError("Not connected to agent service")
        
        request = agent_pb2.TaskRequest(
            task_id=task_id,
            task_type=task_type,
            payload=dict_to_struct(payload),
            context=context or {},
            dependencies=dependencies or [],
            priority=priority
        )
        
        if deadline:
            request.deadline.CopyFrom(datetime_to_timestamp(deadline))
        
        try:
            response = await self.stub.ExecuteTask(
                request,
                timeout=self.timeout
            )
            
            result = {
                'task_id': response.task_id,
                'success': response.success,
                'result': struct_to_dict(response.result) if response.result else {},
                'error_message': response.error_message,
                'artifacts': [self._artifact_to_dict(a) for a in response.artifacts],
                'output_context': dict(response.output_context),
                'metrics': self._metrics_to_dict(response.metrics) if response.metrics else {}
            }
            
            if response.success:
                logger.info("Task executed successfully", 
                           task_id=task_id, 
                           endpoint=self.endpoint)
            else:
                logger.error("Task execution failed", 
                            task_id=task_id,
                            error=response.error_message)
            
            return result
            
        except grpc.RpcError as e:
            logger.error("gRPC error during task execution",
                        task_id=task_id,
                        code=e.code(),
                        details=e.details())
            raise
    
    async def stream_task_progress(self, task_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream real-time progress updates for a task.
        
        Args:
            task_id: Task to monitor
            
        Yields:
            Progress update dictionaries
        """
        if not self._connected:
            raise RuntimeError("Not connected to agent service")
        
        request = agent_pb2.TaskProgressRequest(task_id=task_id)
        
        try:
            async for update in self.stub.StreamTaskProgress(request):
                yield {
                    'task_id': update.task_id,
                    'progress': update.progress,
                    'status': update.status,
                    'message': update.message,
                    'timestamp': update.timestamp.ToDatetime() if update.timestamp else None,
                    'completed_steps': list(update.completed_steps),
                    'remaining_steps': list(update.remaining_steps)
                }
        except grpc.RpcError as e:
            logger.error("Error streaming task progress",
                        task_id=task_id,
                        code=e.code(),
                        details=e.details())
            raise
    
    async def heartbeat(self, agent_id: str, status: str = "AVAILABLE",
                       resource_usage: Dict[str, float] = None) -> bool:
        """
        Send heartbeat to maintain connection and report status.
        
        Args:
            agent_id: Agent identifier
            status: Current agent status
            resource_usage: Resource utilization metrics
            
        Returns:
            True if acknowledged
        """
        if not self._connected:
            return False
        
        # Map status string to enum
        status_map = {
            "AVAILABLE": agent_pb2.AVAILABLE,
            "BUSY": agent_pb2.BUSY,
            "OFFLINE": agent_pb2.OFFLINE,
            "ERROR": agent_pb2.ERROR,
            "MAINTENANCE": agent_pb2.MAINTENANCE
        }
        
        request = agent_pb2.HeartbeatRequest(
            agent_id=agent_id,
            status=status_map.get(status, agent_pb2.UNKNOWN),
            resource_usage=resource_usage or {}
        )
        
        try:
            response = await self.stub.Heartbeat(request, timeout=5)
            return response.acknowledged
        except grpc.RpcError:
            return False
    
    async def get_capabilities(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent capabilities and metadata.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent capabilities dictionary
        """
        if not self._connected:
            raise RuntimeError("Not connected to agent service")
        
        request = agent_pb2.CapabilitiesRequest(agent_id=agent_id)
        
        try:
            response = await self.stub.GetCapabilities(request, timeout=10)
            
            return {
                'agent_id': response.agent_id,
                'agent_type': response.agent_type,
                'supported_tasks': list(response.supported_tasks),
                'languages': list(response.languages),
                'frameworks': list(response.frameworks),
                'metadata': dict(response.metadata),
                'limits': self._limits_to_dict(response.limits) if response.limits else {}
            }
        except grpc.RpcError as e:
            logger.error("Failed to get capabilities",
                        agent_id=agent_id,
                        code=e.code())
            raise
    
    async def collaborate(self,
                         requesting_agent_id: str,
                         collaboration_type: str,
                         data: Dict[str, Any],
                         context: Dict[str, str] = None,
                         timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Request collaboration from another agent.
        
        Args:
            requesting_agent_id: ID of requesting agent
            collaboration_type: Type of collaboration
            data: Collaboration data
            context: Additional context
            timeout_seconds: Collaboration timeout
            
        Returns:
            Collaboration response
        """
        if not self._connected:
            raise RuntimeError("Not connected to agent service")
        
        request = agent_pb2.CollaborationRequest(
            requesting_agent_id=requesting_agent_id,
            collaboration_type=collaboration_type,
            data=dict_to_struct(data),
            context=context or {},
            timeout_seconds=timeout_seconds
        )
        
        try:
            response = await self.stub.CollaborateRequest(
                request,
                timeout=timeout_seconds + 5
            )
            
            return {
                'responding_agent_id': response.responding_agent_id,
                'accepted': response.accepted,
                'response_data': struct_to_dict(response.response_data) if response.response_data else {},
                'suggestions': [self._suggestion_to_dict(s) for s in response.suggestions],
                'confidence_score': response.confidence_score
            }
        except grpc.RpcError as e:
            logger.error("Collaboration request failed",
                        type=collaboration_type,
                        code=e.code())
            raise
    
    async def share_context(self,
                           sharing_agent_id: str,
                           target_agent_ids: list,
                           shared_data: Dict[str, Any],
                           ttl_seconds: int = 300,
                           required_keys: list = None) -> Dict[str, Any]:
        """
        Share context data with other agents.
        
        Args:
            sharing_agent_id: ID of sharing agent
            target_agent_ids: Target agent IDs
            shared_data: Data to share
            ttl_seconds: Time to live for shared data
            required_keys: Keys that must be acknowledged
            
        Returns:
            Sharing response
        """
        if not self._connected:
            raise RuntimeError("Not connected to agent service")
        
        # Convert shared data to Any protobuf
        any_data = {}
        for key, value in shared_data.items():
            any_msg = any_pb2.Any()
            if isinstance(value, dict):
                any_msg.Pack(dict_to_struct(value))
            else:
                # For non-dict types, wrap in a Value message
                value_msg = struct_pb2.Value()
                if isinstance(value, str):
                    value_msg.string_value = value
                elif isinstance(value, (int, float)):
                    value_msg.number_value = float(value)
                elif isinstance(value, bool):
                    value_msg.bool_value = value
                else:
                    value_msg.string_value = json.dumps(value)
                any_msg.Pack(value_msg)
            any_data[key] = any_msg
        
        request = agent_pb2.ContextShareRequest(
            sharing_agent_id=sharing_agent_id,
            target_agent_ids=target_agent_ids,
            shared_data=any_data,
            ttl_seconds=ttl_seconds,
            required_keys=required_keys or []
        )
        
        try:
            response = await self.stub.ShareContext(request, timeout=10)
            
            return {
                'success': response.success,
                'acknowledged_by': list(response.acknowledged_by),
                'errors': dict(response.errors)
            }
        except grpc.RpcError as e:
            logger.error("Context sharing failed", code=e.code())
            raise
    
    async def cancel_task(self, task_id: str, reason: str = "", force: bool = False) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task to cancel
            reason: Cancellation reason
            force: Force cancellation
            
        Returns:
            True if cancelled
        """
        if not self._connected:
            raise RuntimeError("Not connected to agent service")
        
        request = agent_pb2.CancelTaskRequest(
            task_id=task_id,
            reason=reason,
            force=force
        )
        
        try:
            response = await self.stub.CancelTask(request, timeout=10)
            
            if response.cancelled:
                logger.info("Task cancelled", task_id=task_id)
            else:
                logger.warning("Task cancellation failed", 
                              task_id=task_id, 
                              message=response.message)
            
            return response.cancelled
        except grpc.RpcError as e:
            logger.error("Error cancelling task",
                        task_id=task_id,
                        code=e.code())
            return False
    
    def _artifact_to_dict(self, artifact: agent_pb2.Artifact) -> Dict[str, Any]:
        """Convert Artifact protobuf to dict"""
        return {
            'name': artifact.name,
            'type': artifact.type,
            'content': artifact.content,
            'path': artifact.path,
            'metadata': dict(artifact.metadata)
        }
    
    def _suggestion_to_dict(self, suggestion: agent_pb2.Suggestion) -> Dict[str, Any]:
        """Convert Suggestion protobuf to dict"""
        return {
            'type': suggestion.type,
            'description': suggestion.description,
            'code_snippet': suggestion.code_snippet,
            'line_number': suggestion.line_number,
            'impact_score': suggestion.impact_score
        }
    
    def _metrics_to_dict(self, metrics: agent_pb2.TaskMetrics) -> Dict[str, Any]:
        """Convert TaskMetrics protobuf to dict"""
        return {
            'execution_time_ms': metrics.execution_time_ms,
            'tokens_used': metrics.tokens_used,
            'cpu_usage': metrics.cpu_usage,
            'memory_usage_bytes': metrics.memory_usage_bytes,
            'custom_metrics': dict(metrics.custom_metrics)
        }
    
    def _limits_to_dict(self, limits: agent_pb2.ResourceLimits) -> Dict[str, Any]:
        """Convert ResourceLimits protobuf to dict"""
        return {
            'max_concurrent_tasks': limits.max_concurrent_tasks,
            'max_memory_bytes': limits.max_memory_bytes,
            'max_execution_time_seconds': limits.max_execution_time_seconds,
            'rate_limit_per_minute': limits.rate_limit_per_minute
        }