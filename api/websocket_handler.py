"""
WebSocket Handler for Real-time Updates
Provides live updates during code generation process
"""

import json
import asyncio
import logging
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import uuid

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        """Accept a WebSocket connection and return connection ID"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        # Track user connections if user_id provided
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        self.connection_metadata[connection_id] = {
            'user_id': user_id,
            'connected_at': asyncio.get_event_loop().time(),
            'last_ping': asyncio.get_event_loop().time()
        }
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get('user_id')
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Clean up
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id} (user: {user_id})")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(message))
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
    
    async def broadcast(self, message: Dict[str, Any], exclude_connections: Set[str] = None):
        """Broadcast message to all active connections"""
        exclude_connections = exclude_connections or set()
        
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            if connection_id not in exclude_connections:
                await self.send_personal_message(message, connection_id)
    
    async def send_generation_progress(self, job_id: str, progress: float, status: str, user_id: str = None):
        """Send project generation progress update"""
        message = {
            'type': 'generation_progress',
            'job_id': job_id,
            'progress': progress,
            'status': status,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        if user_id:
            await self.send_to_user(message, user_id)
        else:
            await self.broadcast(message)
    
    async def send_file_update(self, file_id: str, updates: Dict[str, Any], user_id: str = None):
        """Send file update notification"""
        message = {
            'type': 'file_update',
            'file_id': file_id,
            'updates': updates,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        if user_id:
            await self.send_to_user(message, user_id)
        else:
            await self.broadcast(message)
    
    async def send_log_update(self, log_entry: Dict[str, Any], user_id: str = None):
        """Send log update"""
        message = {
            'type': 'log_update',
            'log': log_entry,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        if user_id:
            await self.send_to_user(message, user_id)
        else:
            await self.broadcast(message)
    
    async def send_api_status_update(self, provider: str, status: str, user_id: str = None):
        """Send API status update"""
        message = {
            'type': 'api_status_update',
            'provider': provider,
            'status': status,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        if user_id:
            await self.send_to_user(message, user_id)
        else:
            await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_user_count(self) -> int:
        """Get number of unique users connected"""
        return len(self.user_connections)
    
    async def cleanup_stale_connections(self):
        """Remove stale connections that haven't responded to ping"""
        current_time = asyncio.get_event_loop().time()
        stale_threshold = 60  # 60 seconds
        
        stale_connections = []
        for connection_id, metadata in self.connection_metadata.items():
            if current_time - metadata.get('last_ping', 0) > stale_threshold:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            logger.warning(f"Removing stale connection: {connection_id}")
            self.disconnect(connection_id)

# Global connection manager instance
connection_manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, user_id: Optional[str] = None):
    """Main WebSocket endpoint handler"""
    connection_id = await connection_manager.connect(websocket, user_id)
    
    try:
        # Send initial connection confirmation
        await connection_manager.send_personal_message({
            'type': 'connection_established',
            'connection_id': connection_id,
            'user_id': user_id,
            'timestamp': asyncio.get_event_loop().time()
        }, connection_id)
        
        # Handle incoming messages
        while True:
            try:
                # Wait for message with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                await handle_websocket_message(message, connection_id, user_id)
                
                # Update last ping time
                if connection_id in connection_manager.connection_metadata:
                    connection_manager.connection_metadata[connection_id]['last_ping'] = asyncio.get_event_loop().time()
                    
            except asyncio.TimeoutError:
                # Send ping to check if connection is alive
                await connection_manager.send_personal_message({
                    'type': 'ping',
                    'timestamp': asyncio.get_event_loop().time()
                }, connection_id)
                
            except WebSocketDisconnect:
                break
                
            except json.JSONDecodeError:
                await connection_manager.send_personal_message({
                    'type': 'error',
                    'message': 'Invalid JSON format',
                    'timestamp': asyncio.get_event_loop().time()
                }, connection_id)
                
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await connection_manager.send_personal_message({
                    'type': 'error',
                    'message': 'Internal server error',
                    'timestamp': asyncio.get_event_loop().time()
                }, connection_id)
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connection_manager.disconnect(connection_id)

async def handle_websocket_message(message: Dict[str, Any], connection_id: str, user_id: Optional[str]):
    """Handle incoming WebSocket message"""
    message_type = message.get('type')
    
    if message_type == 'pong':
        # Response to ping - update last ping time
        if connection_id in connection_manager.connection_metadata:
            connection_manager.connection_metadata[connection_id]['last_ping'] = asyncio.get_event_loop().time()
    
    elif message_type == 'subscribe_to_job':
        # Subscribe to updates for specific job
        job_id = message.get('job_id')
        if job_id:
            # Add subscription logic here
            await connection_manager.send_personal_message({
                'type': 'subscription_confirmed',
                'job_id': job_id,
                'timestamp': asyncio.get_event_loop().time()
            }, connection_id)
    
    elif message_type == 'unsubscribe_from_job':
        # Unsubscribe from job updates
        job_id = message.get('job_id')
        if job_id:
            await connection_manager.send_personal_message({
                'type': 'unsubscription_confirmed',
                'job_id': job_id,
                'timestamp': asyncio.get_event_loop().time()
            }, connection_id)
    
    elif message_type == 'request_status':
        # Send current status
        await connection_manager.send_personal_message({
            'type': 'status_response',
            'connections': connection_manager.get_connection_count(),
            'users': connection_manager.get_user_count(),
            'timestamp': asyncio.get_event_loop().time()
        }, connection_id)
    
    else:
        # Unknown message type
        await connection_manager.send_personal_message({
            'type': 'error',
            'message': f'Unknown message type: {message_type}',
            'timestamp': asyncio.get_event_loop().time()
        }, connection_id)

# Background task to cleanup stale connections
async def connection_cleanup_task():
    """Background task to clean up stale connections"""
    while True:
        try:
            await connection_manager.cleanup_stale_connections()
            await asyncio.sleep(30)  # Run every 30 seconds
        except Exception as e:
            logger.error(f"Error in connection cleanup task: {e}")
            await asyncio.sleep(60)  # Wait longer if error occurred

# Start cleanup task when module is imported
asyncio.create_task(connection_cleanup_task())