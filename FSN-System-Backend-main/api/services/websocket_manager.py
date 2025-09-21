"""
WebSocket Manager for Real-Time Updates

Manages WebSocket connections and broadcasts real-time updates to connected clients.
Supports device status updates, job progress monitoring, and system notifications.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import structlog
from datetime import datetime

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.broadcast_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        
    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "connected_at": datetime.now().isoformat(),
            "client_info": client_info or {},
            "last_ping": time.time()
        }
        
        logger.info(
            "🔌 WebSocket client connected",
            total_connections=len(self.active_connections),
            client_info=client_info
        )
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to FSN Appium Farm real-time updates",
            "timestamp": datetime.now().isoformat(),
            "server_time": time.time()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
            
        logger.info(
            "🔌 WebSocket client disconnected",
            total_connections=len(self.active_connections)
        )
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e))
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
            
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
            
        # Add server time if not present
        if "server_time" not in message:
            message["server_time"] = time.time()
        
        # Send to all active connections
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))
                disconnected_connections.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    async def broadcast_device_status(self, device_id: int, status: str, details: Optional[Dict[str, Any]] = None):
        """Broadcast device status update"""
        message = {
            "type": "device_status_update",
            "device_id": device_id,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_job_progress(self, job_id: int, status: str, progress: Optional[Dict[str, Any]] = None):
        """Broadcast job progress update"""
        message = {
            "type": "job_progress_update",
            "job_id": job_id,
            "status": status,
            "progress": progress or {},
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_system_notification(self, notification_type: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Broadcast system notification"""
        notification = {
            "type": "system_notification",
            "notification_type": notification_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(notification)
    
    async def broadcast_heartbeat(self):
        """Broadcast heartbeat to keep connections alive"""
        heartbeat = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
            "server_time": time.time(),
            "active_connections": len(self.active_connections)
        }
        await self.broadcast(heartbeat)
    
    async def start_heartbeat(self, interval: int = 30):
        """Start periodic heartbeat broadcasting"""
        self.is_running = True
        while self.is_running:
            try:
                await self.broadcast_heartbeat()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error("Heartbeat error", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    def stop_heartbeat(self):
        """Stop heartbeat broadcasting"""
        self.is_running = False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "connected_at": metadata["connected_at"],
                    "client_info": metadata["client_info"],
                    "last_ping": metadata["last_ping"]
                }
                for metadata in self.connection_metadata.values()
            ]
        }


# Global connection manager instance
connection_manager = ConnectionManager()


class WebSocketService:
    """Service for managing WebSocket operations and integrations"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the WebSocket service"""
        logger.info("🚀 Starting WebSocket service")
        
        # Start heartbeat task
        self.heartbeat_task = asyncio.create_task(
            self.connection_manager.start_heartbeat(interval=30)
        )
        
        logger.info("✅ WebSocket service started")
    
    async def stop(self):
        """Stop the WebSocket service"""
        logger.info("🛑 Stopping WebSocket service")
        
        # Stop heartbeat
        self.connection_manager.stop_heartbeat()
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for connection in self.connection_manager.active_connections.copy():
            try:
                await connection.close()
            except Exception as e:
                logger.error("Error closing connection", error=str(e))
        
        logger.info("✅ WebSocket service stopped")
    
    async def notify_device_status_change(self, device_id: int, old_status: str, new_status: str, details: Optional[Dict[str, Any]] = None):
        """Notify about device status change"""
        await self.connection_manager.broadcast_device_status(
            device_id=device_id,
            status=new_status,
            details={
                "old_status": old_status,
                "new_status": new_status,
                **(details or {})
            }
        )
    
    async def notify_job_status_change(self, job_id: int, old_status: str, new_status: str, progress: Optional[Dict[str, Any]] = None):
        """Notify about job status change"""
        await self.connection_manager.broadcast_job_progress(
            job_id=job_id,
            status=new_status,
            progress={
                "old_status": old_status,
                "new_status": new_status,
                **(progress or {})
            }
        )
    
    async def notify_system_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Notify about system events"""
        await self.connection_manager.broadcast_system_notification(
            notification_type=event_type,
            message=message,
            data=data or {}
        )


# Global WebSocket service instance
websocket_service = WebSocketService(connection_manager)
