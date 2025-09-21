"""
Job WebSocket Routes
Handles real-time job status updates via WebSocket
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
import logging

from api.services.job_websocket_service import job_websocket_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/jobs/ws")
async def job_websocket_endpoint(websocket: WebSocket, job_id: str = Query(None)):
    """WebSocket endpoint for real-time job updates"""
    await job_websocket_service.connect(websocket)
    
    # Subscribe to specific job if job_id provided
    if job_id:
        await job_websocket_service.subscribe_to_job(websocket, job_id)
        logger.info(f"WebSocket subscribed to job {job_id}")
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe_job":
                job_id = message.get("job_id")
                if job_id:
                    await job_websocket_service.subscribe_to_job(websocket, job_id)
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "job_id": job_id,
                        "message": f"Subscribed to job {job_id}"
                    }))
            
            elif message.get("type") == "unsubscribe_job":
                job_id = message.get("job_id")
                if job_id:
                    await job_websocket_service.unsubscribe_from_job(websocket, job_id)
                    await websocket.send_text(json.dumps({
                        "type": "unsubscription_confirmed",
                        "job_id": job_id,
                        "message": f"Unsubscribed from job {job_id}"
                    }))
            
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                }))
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        job_websocket_service.disconnect(websocket)