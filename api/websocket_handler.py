"""
WebSocket Handler for Real-time Updates
Provides live updates during code generation process
"""

import json
import asyncio
import logging
from typing import Dict, Set, Any, Optional, List
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import uuid
import time
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    AGENT_STATUS = "agent_status"
    AGENT_PROGRESS = "agent_progress" 
    PROGRESS_UPDATE = "progress_update"
    QA_METRICS = "qa_metrics"
    ERROR = "error"
    SUCCESS = "success"
    CONNECTION_STATUS = "connection_status"
    HEARTBEAT = "heartbeat"
    PROJECT_COMPLETE = "project_complete"
    FILE_GENERATED = "file_generated"
    WORKFLOW_STATUS = "workflow_status"

class AgentStatus(Enum):
    """Agent status states"""
    IDLE = "idle"
    WAITING = "waiting"
    STARTING = "starting"
    ACTIVE = "active"
    PROCESSING = "processing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class AgentUpdate:
    """Agent status update data structure"""
    agent_name: str
    status: AgentStatus
    progress: float
    current_task: str
    timestamp: float
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    qa_metrics: Optional[Dict[str, Any]] = None

@dataclass
class QAMetrics:
    """QA validation metrics data structure"""
    quality_score: int
    tests_passed: int
    total_tests: int
    security_status: str
    final_approval: bool
    compilation_status: Optional[Dict[str, bool]] = None
    performance_score: Optional[int] = None
    recommendations: Optional[List[str]] = None

@dataclass
class ProjectUpdate:
    """Project generation update data structure"""
    job_id: str
    overall_progress: float
    current_phase: str
    agents: Dict[str, AgentUpdate]
    files_generated: int
    estimated_completion: Optional[float] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class ConnectionManager:
    """Enhanced WebSocket connection manager with agent status tracking"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.job_connections: Dict[str, Set[str]] = {}  # job_id -> connection_ids
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.agent_status: Dict[str, Dict[str, AgentUpdate]] = {}  # job_id -> agent_name -> status
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None, job_id: Optional[str] = None) -> str:
        """Accept a WebSocket connection and return connection ID"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        # Track user connections if user_id provided
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        # Track job connections if job_id provided
        if job_id:
            if job_id not in self.job_connections:
                self.job_connections[job_id] = set()
            self.job_connections[job_id].add(connection_id)
        
        self.connection_metadata[connection_id] = {
            'user_id': user_id,
            'job_id': job_id,
            'connected_at': time.time(),
            'last_ping': time.time()
        }
        
        # Start heartbeat for this connection
        self.heartbeat_tasks[connection_id] = asyncio.create_task(
            self._heartbeat_loop(connection_id)
        )
        
        # Send connection confirmation
        await self.send_personal_message({
            'type': MessageType.CONNECTION_STATUS.value,
            'status': 'connected',
            'connection_id': connection_id,
            'timestamp': time.time()
        }, connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id}, job: {job_id})")
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get('user_id')
            job_id = metadata.get('job_id')
            
            # Cancel heartbeat task
            if connection_id in self.heartbeat_tasks:
                self.heartbeat_tasks[connection_id].cancel()
                del self.heartbeat_tasks[connection_id]
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from job connections
            if job_id and job_id in self.job_connections:
                self.job_connections[job_id].discard(connection_id)
                if not self.job_connections[job_id]:
                    del self.job_connections[job_id]
            
            # Clean up
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id} (user: {user_id}, job: {job_id})")
    
    async def _heartbeat_loop(self, connection_id: str):
        """Send periodic heartbeat messages"""
        try:
            while connection_id in self.active_connections:
                await asyncio.sleep(30)  # 30 second intervals
                if connection_id in self.active_connections:
                    await self.send_personal_message({
                        'type': MessageType.HEARTBEAT.value,
                        'timestamp': time.time()
                    }, connection_id)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat error for {connection_id}: {e}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(message, default=str))
                    # Update last ping time
                    if connection_id in self.connection_metadata:
                        self.connection_metadata[connection_id]['last_ping'] = time.time()
                else:
                    self.disconnect(connection_id)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            connection_ids = list(self.user_connections[user_id])
            for connection_id in connection_ids:
                await self.send_personal_message(message, connection_id)
    
    async def send_to_job(self, message: Dict[str, Any], job_id: str):
        """Send message to all connections tracking a specific job"""
        if job_id in self.job_connections:
            connection_ids = list(self.job_connections[job_id])
            for connection_id in connection_ids:
                await self.send_personal_message(message, connection_id)
    
    async def broadcast(self, message: Dict[str, Any], exclude_connections: Set[str] = None):
        """Broadcast message to all active connections"""
        exclude_connections = exclude_connections or set()
        
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            if connection_id not in exclude_connections:
                await self.send_personal_message(message, connection_id)
    
    async def update_agent_status(self, job_id: str, agent_name: str, status: AgentStatus, 
                                progress: float, current_task: str, details: Optional[Dict] = None,
                                error_message: Optional[str] = None):
        """Update agent status and broadcast to relevant connections"""
        # Create agent update
        agent_update = AgentUpdate(
            agent_name=agent_name,
            status=status,
            progress=progress,
            current_task=current_task,
            timestamp=time.time(),
            details=details,
            error_message=error_message
        )
        
        # Store agent status
        if job_id not in self.agent_status:
            self.agent_status[job_id] = {}
        self.agent_status[job_id][agent_name] = agent_update
        
        # Broadcast update
        message = {
            'type': MessageType.AGENT_STATUS.value,
            'job_id': job_id,
            'agent_update': asdict(agent_update),
            'timestamp': time.time()
        }
        
        await self.send_to_job(message, job_id)
        
        logger.info(f"Agent status updated: {job_id}/{agent_name} -> {status.value} ({progress}%)")
    
    async def update_project_progress(self, job_id: str, overall_progress: float, 
                                    current_phase: str, files_generated: int = 0,
                                    estimated_completion: Optional[float] = None):
        """Update overall project progress"""
        # Get current agent statuses
        agents = self.agent_status.get(job_id, {})
        
        # Create project update
        project_update = ProjectUpdate(
            job_id=job_id,
            overall_progress=overall_progress,
            current_phase=current_phase,
            agents=agents,
            files_generated=files_generated,
            estimated_completion=estimated_completion
        )
        
        # Broadcast update
        message = {
            'type': MessageType.PROGRESS_UPDATE.value,
            'project_update': asdict(project_update),
            'timestamp': time.time()
        }
        
        await self.send_to_job(message, job_id)
        
        logger.info(f"Project progress updated: {job_id} -> {overall_progress}% ({current_phase})")
    
    async def broadcast_agent_progress(self, agent_name: str, job_id: str, 
                                     status: str, progress: int, message: str, details: Optional[Dict] = None):
        """Enhanced progress broadcasting with agent-specific details for 6-agent system"""
        update_message = {
            'type': MessageType.AGENT_PROGRESS.value,
            'agent': agent_name,
            'job_id': job_id,
            'status': status,
            'progress': progress,
            'message': message,
            'timestamp': time.time(),
            'details': details or {}
        }
        
        # Special handling for QA Validator with metrics
        if agent_name == 'qa_validator' and details:
            update_message['qa_metrics'] = {
                'quality_score': details.get('quality_score', 0),
                'tests_passed': details.get('tests_passed', 0),
                'total_tests': details.get('total_tests', 0),
                'security_status': details.get('security_status', 'pending'),
                'final_approval': details.get('final_approval', False)
            }
        
        await self.send_to_job(update_message, job_id)
        logger.info(f"Agent progress broadcast: {agent_name} -> {status} ({progress}%)")
    
    async def broadcast_to_job(self, job_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a specific job"""
        await self.send_to_job(message, job_id)
    
    async def update_qa_metrics(self, job_id: str, qa_metrics: Dict[str, Any]):
        """Update and broadcast QA validation metrics"""
        message = {
            'type': MessageType.QA_METRICS.value,
            'job_id': job_id,
            'qa_metrics': qa_metrics,
            'timestamp': time.time()
        }
        
        await self.send_to_job(message, job_id)
        logger.info(f"QA metrics updated for job {job_id}: Quality Score {qa_metrics.get('quality_score', 0)}%")
    
    async def broadcast_workflow_status(self, job_id: str, status: str, agents_status: Dict[str, str]):
        """Broadcast overall workflow status with all 6 agents"""
        message = {
            'type': MessageType.WORKFLOW_STATUS.value,
            'job_id': job_id,
            'workflow_status': status,
            'agents': agents_status,
            'timestamp': time.time()
        }
        
        await self.send_to_job(message, job_id)
        logger.info(f"Workflow status broadcast for job {job_id}: {status}")
    
    async def initialize_6_agent_tracking(self, job_id: str):
        """Initialize tracking for all 6 agents"""
        agent_names = ['orchestrator', 'planner', 'coder', 'critic', 'file_manager', 'qa_validator']
        
        if job_id not in self.agent_status:
            self.agent_status[job_id] = {}
        
        for agent_name in agent_names:
            initial_status = 'active' if agent_name == 'orchestrator' else 'waiting'
            self.agent_status[job_id][agent_name] = AgentUpdate(
                agent_name=agent_name,
                status=AgentStatus.ACTIVE if agent_name == 'orchestrator' else AgentStatus.WAITING,
                progress=0.0,
                current_task=f"Initializing {agent_name}",
                timestamp=time.time()
            )
        
        # Broadcast initial status
        await self.broadcast_workflow_status(job_id, 'initializing', {
            agent: 'active' if agent == 'orchestrator' else 'waiting' 
            for agent in agent_names
        })
        
        logger.info(f"Initialized 6-agent tracking for job {job_id}")
    
    async def send_error(self, job_id: str, error_message: str, error_type: str = "general",
                        agent_name: Optional[str] = None):
        """Send error message to job connections"""
        message = {
            'type': MessageType.ERROR.value,
            'job_id': job_id,
            'error_message': error_message,
            'error_type': error_type,
            'agent_name': agent_name,
            'timestamp': time.time()
        }
        
        await self.send_to_job(message, job_id)
        
        logger.error(f"Error sent for job {job_id}: {error_message}")
    
    async def send_file_generated(self, job_id: str, file_path: str, file_type: str):
        """Notify about a newly generated file"""
        message = {
            'type': MessageType.FILE_GENERATED.value,
            'job_id': job_id,
            'file_path': file_path,
            'file_type': file_type,
            'timestamp': time.time()
        }
        
        await self.send_to_job(message, job_id)
    
    async def send_project_complete(self, job_id: str, total_files: int, 
                                  generation_time: float, download_url: str):
        """Notify about project completion"""
        message = {
            'type': MessageType.PROJECT_COMPLETE.value,
            'job_id': job_id,
            'total_files': total_files,
            'generation_time': generation_time,
            'download_url': download_url,
            'timestamp': time.time()
        }
        
        await self.send_to_job(message, job_id)
        
        # Clean up job from agent status tracking
        if job_id in self.agent_status:
            del self.agent_status[job_id]
        
        logger.info(f"Project completed: {job_id} ({total_files} files, {generation_time:.2f}s)")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics"""
        return {
            'total_connections': len(self.active_connections),
            'user_connections': len(self.user_connections),
            'job_connections': len(self.job_connections),
            'active_jobs': len(self.agent_status),
            'heartbeat_tasks': len(self.heartbeat_tasks)
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status for a specific job"""
        if job_id not in self.agent_status:
            return None
        
        agents = {}
        for agent_name, agent_update in self.agent_status[job_id].items():
            agents[agent_name] = asdict(agent_update)
        
        return {
            'job_id': job_id,
            'agents': agents,
            'connected_clients': len(self.job_connections.get(job_id, set())),
            'last_update': max([agent.timestamp for agent in self.agent_status[job_id].values()])
        }

# Global connection manager instance
connection_manager = ConnectionManager()

# Helper functions for agents to send updates
async def send_agent_status(job_id: str, agent_name: str, status: str, progress: float, 
                           current_task: str, details: Optional[Dict] = None,
                           error_message: Optional[str] = None):
    """Helper function for agents to send status updates"""
    agent_status = AgentStatus(status) if isinstance(status, str) else status
    await connection_manager.update_agent_status(
        job_id, agent_name, agent_status, progress, current_task, details, error_message
    )

async def send_project_progress(job_id: str, progress: float, phase: str, files_count: int = 0):
    """Helper function to send project progress updates"""
    await connection_manager.update_project_progress(job_id, progress, phase, files_count)

async def send_error_notification(job_id: str, error: str, error_type: str = "general", 
                                agent: Optional[str] = None):
    """Helper function to send error notifications"""
    await connection_manager.send_error(job_id, error, error_type, agent)

async def send_completion_notification(job_id: str, files_count: int, duration: float, download_url: str):
    """Helper function to send completion notifications"""
    await connection_manager.send_project_complete(job_id, files_count, duration, download_url)