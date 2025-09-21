"""
WebSocket Routes for Real-Time Updates

Provides WebSocket endpoints for real-time device status, job progress, and system notifications.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
import structlog
import json
from typing import Optional

from services.websocket_manager import connection_manager, websocket_service

logger = structlog.get_logger()

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """
    Main WebSocket endpoint for real-time updates
    
    Query Parameters:
    - client_id: Optional client identifier for tracking
    """
    logger.info("🔌 WebSocket connection attempt", client_id=client_id, origin=websocket.headers.get("origin"))
    
    client_info = {
        "client_id": client_id,
        "user_agent": websocket.headers.get("user-agent"),
        "origin": websocket.headers.get("origin")
    }
    
    try:
        await connection_manager.connect(websocket, client_info)
        logger.info("✅ WebSocket connected successfully", client_id=client_id)
    except Exception as e:
        logger.error("❌ WebSocket connection failed", error=str(e), client_id=client_id)
        return
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(websocket, message)
            except json.JSONDecodeError:
                await connection_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": websocket_service.connection_manager.connection_metadata.get(websocket, {}).get("connected_at")
                }, websocket)
            except Exception as e:
                logger.error("Error handling client message", error=str(e))
                await connection_manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": websocket_service.connection_manager.connection_metadata.get(websocket, {}).get("connected_at")
                }, websocket)
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected", client_id=client_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), client_id=client_id)
        connection_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle incoming messages from WebSocket clients"""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        await connection_manager.send_personal_message({
            "type": "pong",
            "timestamp": message.get("timestamp"),
            "server_time": websocket_service.connection_manager.connection_metadata.get(websocket, {}).get("connected_at")
        }, websocket)
        
    elif message_type == "subscribe":
        # Handle subscription requests
        subscription_type = message.get("subscription_type")
        if subscription_type in ["devices", "jobs", "system", "all"]:
            await connection_manager.send_personal_message({
                "type": "subscription_confirmed",
                "subscription_type": subscription_type,
                "message": f"Subscribed to {subscription_type} updates"
            }, websocket)
        else:
            await connection_manager.send_personal_message({
                "type": "subscription_error",
                "message": f"Unknown subscription type: {subscription_type}"
            }, websocket)
            
    elif message_type == "get_status":
        # Send current system status
        status = {
            "type": "system_status",
            "devices": await get_device_status_summary(),
            "jobs": await get_job_status_summary(),
            "connections": connection_manager.get_connection_stats()
        }
        await connection_manager.send_personal_message(status, websocket)
        
    else:
        # Unknown message type
        await connection_manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }, websocket)


async def get_device_status_summary():
    """Get summary of device statuses"""
    try:
        # Import here to avoid circular imports
        from services.device_pool_manager import device_pool_manager
        
        devices = device_pool_manager.get_all_devices()
        status_summary = {
            "total": len(devices),
            "active": len([d for d in devices if d.get("status") == "active"]),
            "offline": len([d for d in devices if d.get("status") == "offline"]),
            "error": len([d for d in devices if d.get("status") == "error"])
        }
        return status_summary
    except Exception as e:
        logger.error("Error getting device status summary", error=str(e))
        return {"total": 0, "active": 0, "offline": 0, "error": 0}


async def get_job_status_summary():
    """Get summary of job statuses"""
    try:
        # Import here to avoid circular imports
        from services.concurrent_job_executor import concurrent_job_executor
        
        jobs = concurrent_job_executor.get_job_queue_status()
        status_summary = {
            "total": jobs.get("total_jobs", 0),
            "pending": jobs.get("pending_jobs", 0),
            "running": jobs.get("running_jobs", 0),
            "completed": jobs.get("completed_jobs", 0),
            "failed": jobs.get("failed_jobs", 0)
        }
        return status_summary
    except Exception as e:
        logger.error("Error getting job status summary", error=str(e))
        return {"total": 0, "pending": 0, "running": 0, "completed": 0, "failed": 0}


@router.get("/ws/test")
async def websocket_test_page():
    """Simple HTML page for testing WebSocket connection"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FSN Appium Farm - WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background-color: #d4edda; color: #155724; }
            .disconnected { background-color: #f8d7da; color: #721c24; }
            .message { background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; }
            .error { background-color: #f8d7da; padding: 10px; margin: 5px 0; border-left: 4px solid #dc3545; }
            button { padding: 10px 20px; margin: 5px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            #messages { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>FSN Appium Farm - WebSocket Test</h1>
            
            <div id="status" class="status disconnected">Disconnected</div>
            
            <div>
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <button onclick="ping()">Ping</button>
                <button onclick="subscribe('devices')">Subscribe to Devices</button>
                <button onclick="subscribe('jobs')">Subscribe to Jobs</button>
                <button onclick="subscribe('all')">Subscribe to All</button>
                <button onclick="getStatus()">Get Status</button>
                <button onclick="clearMessages()">Clear Messages</button>
            </div>
            
            <h3>Messages:</h3>
            <div id="messages"></div>
        </div>

        <script>
            let ws = null;
            let reconnectInterval = null;

            function connect() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    addMessage('Already connected', 'info');
                    return;
                }

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/v1/ws?client_id=test_client_${Date.now()}`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    updateStatus('Connected', 'connected');
                    addMessage('Connected to WebSocket server', 'success');
                    clearInterval(reconnectInterval);
                };
                
                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        addMessage(JSON.stringify(data, null, 2), 'message');
                    } catch (e) {
                        addMessage('Received: ' + event.data, 'message');
                    }
                };
                
                ws.onclose = function(event) {
                    updateStatus('Disconnected', 'disconnected');
                    addMessage('WebSocket connection closed', 'error');
                    
                    // Auto-reconnect after 5 seconds
                    if (!reconnectInterval) {
                        reconnectInterval = setInterval(() => {
                            addMessage('Attempting to reconnect...', 'info');
                            connect();
                        }, 5000);
                    }
                };
                
                ws.onerror = function(error) {
                    addMessage('WebSocket error: ' + error, 'error');
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
            }

            function ping() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'ping',
                        timestamp: new Date().toISOString()
                    }));
                } else {
                    addMessage('Not connected', 'error');
                }
            }

            function subscribe(type) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        subscription_type: type
                    }));
                } else {
                    addMessage('Not connected', 'error');
                }
            }

            function getStatus() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'get_status'
                    }));
                } else {
                    addMessage('Not connected', 'error');
                }
            }

            function updateStatus(text, className) {
                const statusEl = document.getElementById('status');
                statusEl.textContent = text;
                statusEl.className = 'status ' + className;
            }

            function addMessage(text, type) {
                const messagesEl = document.getElementById('messages');
                const messageEl = document.createElement('div');
                messageEl.className = type;
                messageEl.textContent = new Date().toLocaleTimeString() + ': ' + text;
                messagesEl.appendChild(messageEl);
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }

            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }

            // Auto-connect on page load
            window.onload = function() {
                connect();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "connections": connection_manager.get_connection_stats(),
        "service_status": "running" if websocket_service.heartbeat_task and not websocket_service.heartbeat_task.done() else "stopped"
    }
