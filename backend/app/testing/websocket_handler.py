"""
WebSocket Handler for Real-time Testing Updates
==============================================

Manages WebSocket connections for real-time testing feedback, progress updates,
and live performance monitoring during agent testing sessions.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, asdict
import uuid
from enum import Enum

from ..core.logging import get_logger
from .schemas import WebSocketMessage, TestProgressUpdate, RealTimeMetrics, PerformanceAlert

logger = get_logger(__name__)

class MessageType(str, Enum):
    # Client -> Server messages
    PING = "ping"
    SUBSCRIBE_TEST = "subscribe_test"
    UNSUBSCRIBE_TEST = "unsubscribe_test" 
    GET_STATUS = "get_status"
    START_TEST = "start_test"
    
    # Server -> Client messages
    PONG = "pong"
    TEST_PROGRESS = "test_progress_update"
    PERFORMANCE_UPDATE = "performance_update"
    ALERT = "alert"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    TEST_COMPLETED = "test_completed"
    CONNECTION_CONFIRMED = "connection_confirmed"

@dataclass
class Connection:
    """WebSocket connection wrapper"""
    websocket: WebSocket
    user_id: str
    connection_id: str
    connected_at: datetime
    subscribed_tests: Set[str]
    last_activity: datetime

class WebSocketManager:
    """
    Manages WebSocket connections for real-time testing updates.
    
    Features:
    - Connection lifecycle management
    - Test session subscriptions
    - Broadcast messaging
    - Performance monitoring
    - Error handling and reconnection
    """
    
    def __init__(self):
        self.connections: Dict[str, Connection] = {}  # connection_id -> Connection
        self.user_connections: Dict[str, List[str]] = {}  # user_id -> [connection_ids]
        self.test_subscribers: Dict[str, Set[str]] = {}  # test_session_id -> {connection_ids}
        self.connection_stats: Dict[str, Any] = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "errors": 0
        }
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept a new WebSocket connection"""
        
        try:
            await websocket.accept()
            
            connection_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            connection = Connection(
                websocket=websocket,
                user_id=user_id,
                connection_id=connection_id,
                connected_at=now,
                subscribed_tests=set(),
                last_activity=now
            )
            
            self.connections[connection_id] = connection
            
            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
            
            # Update stats
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] = len(self.connections)
            
            # Send connection confirmation
            await self._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.CONNECTION_CONFIRMED,
                    data={
                        "connection_id": connection_id,
                        "user_id": user_id,
                        "timestamp": now.isoformat(),
                        "message": "WebSocket connection established successfully"
                    }
                )
            )
            
            logger.info(f"WebSocket connection established: {connection_id} for user {user_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection for user {user_id}: {str(e)}")
            raise
    
    def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection"""
        
        try:
            if connection_id not in self.connections:
                return
            
            connection = self.connections[connection_id]
            user_id = connection.user_id
            
            # Remove from user connections
            if user_id in self.user_connections:
                if connection_id in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(connection_id)
                
                # Clean up empty user connection list
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from test subscriptions
            for test_id, subscribers in self.test_subscribers.items():
                if connection_id in subscribers:
                    subscribers.discard(connection_id)
            
            # Remove empty test subscriptions
            empty_tests = [test_id for test_id, subs in self.test_subscribers.items() if not subs]
            for test_id in empty_tests:
                del self.test_subscribers[test_id]
            
            # Remove connection
            del self.connections[connection_id]
            
            # Update stats
            self.connection_stats["active_connections"] = len(self.connections)
            
            logger.info(f"WebSocket connection closed: {connection_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnection for {connection_id}: {str(e)}")
    
    async def handle_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message from client"""
        
        try:
            if connection_id not in self.connections:
                logger.warning(f"Received message from unknown connection: {connection_id}")
                return
            
            connection = self.connections[connection_id]
            connection.last_activity = datetime.utcnow()
            
            message_type = message_data.get("type")
            data = message_data.get("data", {})
            
            if message_type == MessageType.PING:
                await self._handle_ping(connection_id)
            
            elif message_type == MessageType.SUBSCRIBE_TEST:
                test_session_id = data.get("test_session_id")
                if test_session_id:
                    await self._handle_subscribe_test(connection_id, test_session_id)
            
            elif message_type == MessageType.UNSUBSCRIBE_TEST:
                test_session_id = data.get("test_session_id")
                if test_session_id:
                    await self._handle_unsubscribe_test(connection_id, test_session_id)
            
            elif message_type == MessageType.GET_STATUS:
                await self._handle_get_status(connection_id)
            
            else:
                await self._send_error(connection_id, f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message from {connection_id}: {str(e)}")
            await self._send_error(connection_id, f"Message handling error: {str(e)}")
    
    async def _handle_ping(self, connection_id: str):
        """Handle ping message"""
        
        await self._send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.PONG,
                data={"timestamp": datetime.utcnow().isoformat()}
            )
        )
    
    async def _handle_subscribe_test(self, connection_id: str, test_session_id: str):
        """Subscribe connection to test session updates"""
        
        try:
            if connection_id not in self.connections:
                return
            
            # Add to connection's subscriptions
            connection = self.connections[connection_id]
            connection.subscribed_tests.add(test_session_id)
            
            # Add to test subscribers
            if test_session_id not in self.test_subscribers:
                self.test_subscribers[test_session_id] = set()
            self.test_subscribers[test_session_id].add(connection_id)
            
            # Confirm subscription
            await self._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.STATUS_UPDATE,
                    data={
                        "action": "subscribed",
                        "test_session_id": test_session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Subscribed to test session {test_session_id}"
                    }
                )
            )
            
            logger.info(f"Connection {connection_id} subscribed to test {test_session_id}")
            
        except Exception as e:
            logger.error(f"Error subscribing connection {connection_id} to test {test_session_id}: {str(e)}")
            await self._send_error(connection_id, f"Subscription error: {str(e)}")
    
    async def _handle_unsubscribe_test(self, connection_id: str, test_session_id: str):
        """Unsubscribe connection from test session updates"""
        
        try:
            if connection_id not in self.connections:
                return
            
            connection = self.connections[connection_id]
            connection.subscribed_tests.discard(test_session_id)
            
            if test_session_id in self.test_subscribers:
                self.test_subscribers[test_session_id].discard(connection_id)
                
                # Clean up empty subscriptions
                if not self.test_subscribers[test_session_id]:
                    del self.test_subscribers[test_session_id]
            
            await self._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.STATUS_UPDATE,
                    data={
                        "action": "unsubscribed",
                        "test_session_id": test_session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )
            
            logger.info(f"Connection {connection_id} unsubscribed from test {test_session_id}")
            
        except Exception as e:
            logger.error(f"Error unsubscribing connection {connection_id} from test {test_session_id}: {str(e)}")
    
    async def _handle_get_status(self, connection_id: str):
        """Send connection status information"""
        
        try:
            if connection_id not in self.connections:
                return
            
            connection = self.connections[connection_id]
            
            status_data = {
                "connection_id": connection_id,
                "user_id": connection.user_id,
                "connected_at": connection.connected_at.isoformat(),
                "last_activity": connection.last_activity.isoformat(),
                "subscribed_tests": list(connection.subscribed_tests),
                "server_stats": self.connection_stats.copy()
            }
            
            await self._send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.STATUS_UPDATE,
                    data=status_data
                )
            )
            
        except Exception as e:
            logger.error(f"Error sending status to connection {connection_id}: {str(e)}")
    
    async def broadcast_test_progress(
        self, 
        test_session_id: str, 
        progress_update: TestProgressUpdate
    ):
        """Broadcast test progress update to all subscribed connections"""
        
        try:
            if test_session_id not in self.test_subscribers:
                return
            
            message = WebSocketMessage(
                type=MessageType.TEST_PROGRESS,
                data=asdict(progress_update)
            )
            
            # Send to all subscribers
            disconnected_connections = []
            for connection_id in self.test_subscribers[test_session_id].copy():
                try:
                    await self._send_to_connection(connection_id, message)
                except Exception as e:
                    logger.warning(f"Failed to send progress update to connection {connection_id}: {str(e)}")
                    disconnected_connections.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                self.disconnect(connection_id)
                
        except Exception as e:
            logger.error(f"Error broadcasting test progress for session {test_session_id}: {str(e)}")
    
    async def broadcast_performance_update(
        self,
        test_session_id: str,
        metrics: RealTimeMetrics
    ):
        """Broadcast performance metrics update"""
        
        try:
            if test_session_id not in self.test_subscribers:
                return
            
            message = WebSocketMessage(
                type=MessageType.PERFORMANCE_UPDATE,
                data={
                    "test_session_id": test_session_id,
                    "metrics": asdict(metrics),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            for connection_id in self.test_subscribers[test_session_id].copy():
                try:
                    await self._send_to_connection(connection_id, message)
                except Exception:
                    pass  # Will be cleaned up by heartbeat
                    
        except Exception as e:
            logger.error(f"Error broadcasting performance update: {str(e)}")
    
    async def broadcast_alert(
        self,
        test_session_id: str,
        alert: PerformanceAlert
    ):
        """Broadcast performance alert to subscribed connections"""
        
        try:
            if test_session_id not in self.test_subscribers:
                return
            
            message = WebSocketMessage(
                type=MessageType.ALERT,
                data={
                    "test_session_id": test_session_id,
                    "alert": asdict(alert),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            for connection_id in self.test_subscribers[test_session_id].copy():
                try:
                    await self._send_to_connection(connection_id, message)
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Error broadcasting alert: {str(e)}")
    
    async def send_test_completed(
        self,
        test_session_id: str,
        completion_data: Dict[str, Any]
    ):
        """Send test completion notification"""
        
        try:
            if test_session_id not in self.test_subscribers:
                return
            
            message = WebSocketMessage(
                type=MessageType.TEST_COMPLETED,
                data={
                    "test_session_id": test_session_id,
                    "completion_data": completion_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            for connection_id in self.test_subscribers[test_session_id].copy():
                try:
                    await self._send_to_connection(connection_id, message)
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Error sending test completion notification: {str(e)}")
    
    async def send_to_user(
        self,
        user_id: str,
        message: WebSocketMessage
    ):
        """Send message to all connections for a specific user"""
        
        try:
            if user_id not in self.user_connections:
                return
            
            for connection_id in self.user_connections[user_id].copy():
                try:
                    await self._send_to_connection(connection_id, message)
                except Exception:
                    pass  # Connection will be cleaned up later
                    
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send message to a specific connection"""
        
        try:
            if connection_id not in self.connections:
                return
            
            connection = self.connections[connection_id]
            message_json = json.dumps(asdict(message))
            
            await connection.websocket.send_text(message_json)
            
            self.connection_stats["messages_sent"] += 1
            connection.last_activity = datetime.utcnow()
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected during message send: {connection_id}")
            self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending message to connection {connection_id}: {str(e)}")
            self.connection_stats["errors"] += 1
            # Don't disconnect on send errors - connection might still be viable
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Send error message to connection"""
        
        error_msg = WebSocketMessage(
            type=MessageType.ERROR,
            data={
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self._send_to_connection(connection_id, error_msg)
    
    async def cleanup_stale_connections(self, timeout_minutes: int = 30):
        """Clean up stale connections that haven't been active recently"""
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            stale_connections = []
            
            for connection_id, connection in self.connections.items():
                if connection.last_activity < cutoff_time:
                    stale_connections.append(connection_id)
            
            for connection_id in stale_connections:
                logger.info(f"Cleaning up stale WebSocket connection: {connection_id}")
                self.disconnect(connection_id)
            
            if stale_connections:
                logger.info(f"Cleaned up {len(stale_connections)} stale WebSocket connections")
                
        except Exception as e:
            logger.error(f"Error during stale connection cleanup: {str(e)}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        
        stats = self.connection_stats.copy()
        stats.update({
            "active_connections": len(self.connections),
            "active_users": len(self.user_connections),
            "active_test_subscriptions": len(self.test_subscribers),
            "total_subscriptions": sum(len(subs) for subs in self.test_subscribers.values()),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return stats

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# Background task for connection cleanup
async def websocket_cleanup_task():
    """Background task to cleanup stale connections"""
    
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await websocket_manager.cleanup_stale_connections()
        except Exception as e:
            logger.error(f"Error in WebSocket cleanup task: {str(e)}")

# Start cleanup task
asyncio.create_task(websocket_cleanup_task())