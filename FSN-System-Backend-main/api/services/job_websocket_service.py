"""
Job WebSocket Service
Handles real-time job status updates via WebSocket
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class JobWebSocketService:
    """Manages WebSocket connections for real-time job updates"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.job_subscriptions: Dict[str, Set[WebSocket]] = {}  # job_id -> set of websockets
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        
        # Remove from all job subscriptions
        for job_id, subscribers in self.job_subscriptions.items():
            subscribers.discard(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe_to_job(self, websocket: WebSocket, job_id: str):
        """Subscribe a WebSocket to job updates"""
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        
        self.job_subscriptions[job_id].add(websocket)
        logger.info(f"WebSocket subscribed to job {job_id}")
    
    async def unsubscribe_from_job(self, websocket: WebSocket, job_id: str):
        """Unsubscribe a WebSocket from job updates"""
        if job_id in self.job_subscriptions:
            self.job_subscriptions[job_id].discard(websocket)
            if not self.job_subscriptions[job_id]:
                del self.job_subscriptions[job_id]
        
        logger.info(f"WebSocket unsubscribed from job {job_id}")
    
    async def broadcast_job_update(self, job_id: str, update_data: Dict[str, Any]):
        """Broadcast job update to all subscribers"""
        if job_id not in self.job_subscriptions:
            return
        
        message = {
            "type": "job_update",
            "job_id": job_id,
            "data": update_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send to job-specific subscribers
        disconnected = set()
        for websocket in self.job_subscriptions[job_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send job update to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_all(self, message_data: Dict[str, Any]):
        """Broadcast message to all connected WebSockets"""
        message = {
            "type": "broadcast",
            "data": message_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send broadcast to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def send_job_status(self, job_id: str, status: str, progress: int, step: str):
        """Send job status update"""
        update_data = {
            "status": status,
            "progress": progress,
            "current_step": step
        }
        
        await self.broadcast_job_update(job_id, update_data)
    
    async def send_job_completion(self, job_id: str, success: bool, results: list = None, errors: list = None):
        """Send job completion update"""
        update_data = {
            "status": "completed" if success else "failed",
            "progress": 100,
            "current_step": "completed" if success else "failed",
            "results": results or [],
            "errors": errors or []
        }
        
        await self.broadcast_job_update(job_id, update_data)

# Global instance
job_websocket_service = JobWebSocketService()
