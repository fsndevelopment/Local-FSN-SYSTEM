"""
Device management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from database.connection import get_db
from models.device import Device
from models.agent import Agent
from models.job import Job
from schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from schemas.job import JobStatus
from services.appium_service import appium_service
from services.device_pool_manager import device_pool_manager
from services.instagram_service import instagram_service
from services.crane_container_service import crane_container_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/devices", response_model=List[DeviceResponse])
async def get_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of devices with optional filtering"""
    try:
        query = select(Device)
        
        if status:
            query = query.where(Device.status == status)
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        devices = result.scalars().all()
        
        logger.info("📱 Retrieved devices", count=len(devices), status_filter=status)
        return devices
        
    except Exception as e:
        logger.error("❌ Failed to retrieve devices", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve devices")


@router.get("/devices/discover")
async def discover_devices(db: AsyncSession = Depends(get_db)):
    """Discover connected devices using Appium and remote agents"""
    try:
        all_devices = []
        
        # First, try to discover devices from remote agents
        from services.agent_service import AgentService
        agent_service = AgentService()
        
        # Get all online agents
        result = await db.execute(select(Agent).where(Agent.status == "online"))
        agents = result.scalars().all()
        
        for agent in agents:
            try:
                # Discover devices from this agent
                agent_devices = await appium_service.discover_remote_devices(agent.agent_id)
                all_devices.extend(agent_devices)
                
                # Register agent's Appium URL
                await appium_service.register_remote_agent(agent.agent_id, agent.appium_url)
                
            except Exception as e:
                logger.warning(f"Failed to discover devices from agent {agent.agent_id}: {e}")
        
        # If no remote agents or no devices found, try local discovery
        if not all_devices:
            # Start local Appium server if not running
            server_started = await appium_service.start_appium_server()
            if server_started:
                local_devices = await appium_service.discover_devices()
                all_devices.extend(local_devices)
        
        logger.info("🔍 Device discovery completed", count=len(all_devices))
        return {
            "discovered_devices": all_devices,
            "count": len(all_devices),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("❌ Device discovery failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Device discovery failed: {str(e)}")


@router.get("/devices/pool/status")
async def get_device_pool_status():
    """Get comprehensive device pool status and metrics"""
    try:
        pool_status = await device_pool_manager.get_pool_status()
        logger.info("📊 Device pool status retrieved", total_devices=pool_status.get('total_devices', 0))
        return pool_status
        
    except Exception as e:
        logger.error("❌ Failed to get device pool status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get device pool status: {str(e)}")


@router.post("/devices/pool/register")
async def register_devices_to_pool():
    """Register/refresh devices in the device pool"""
    try:
        registration_result = await device_pool_manager.discover_and_register_devices()
        
        if 'error' in registration_result:
            raise HTTPException(status_code=500, detail=registration_result['error'])
        
        logger.info("📱 Device pool registration completed", 
                   registered=registration_result.get('registered', 0),
                   updated=registration_result.get('updated', 0))
        
        return {
            "message": "Device pool registration completed",
            "results": registration_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("❌ Device pool registration failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Device pool registration failed: {str(e)}")


@router.get("/devices/pool/available")
async def get_available_devices():
    """Get list of currently available devices for job assignment"""
    try:
        available_udids = await device_pool_manager.get_available_devices()
        
        # Get device details from database
        from database.connection import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            if available_udids:
                result = await db.execute(
                    select(Device).where(Device.udid.in_(available_udids))
                )
                devices = result.scalars().all()
                
                device_list = []
                for device in devices:
                    metrics = device_pool_manager.device_metrics.get(device.udid)
                    device_info = {
                        "id": device.id,
                        "name": device.name,
                        "udid": device.udid,
                        "model": device.model,
                        "ios_version": device.ios_version,
                        "status": device.status,
                        "active_jobs": metrics.active_jobs if metrics else 0,
                        "health_score": metrics.health_score if metrics else 1.0,
                        "success_rate": metrics.success_rate if metrics else 1.0,
                        "is_healthy": metrics.is_healthy() if metrics else True
                    }
                    device_list.append(device_info)
            else:
                device_list = []
        
        return {
            "available_devices": device_list,
            "count": len(device_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("❌ Failed to get available devices", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get available devices: {str(e)}")


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific device by ID"""
    try:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
            
        logger.info("📱 Retrieved device", device_id=device_id, name=device.name)
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to retrieve device", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve device")


@router.put("/devices/{device_id}/jailbroken")
async def update_device_jailbroken_status(
    device_id: int,
    jailbroken: bool,
    db: AsyncSession = Depends(get_db)
):
    """Update device jailbroken status"""
    try:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Update jailbroken status
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(jailbroken=jailbroken, updated_at=datetime.utcnow())
        )
        await db.commit()
        
        logger.info("✅ Updated device jailbroken status", 
                   device_id=device_id, 
                   jailbroken=jailbroken,
                   device_name=device.name)
        
        return {"message": f"Device {device.name} jailbroken status updated to {jailbroken}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to update device jailbroken status", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update device jailbroken status")


@router.post("/devices", response_model=DeviceResponse, status_code=201)
async def create_device(device_data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    """Create new device"""
    try:
        # Check if UDID already exists
        existing = await db.execute(select(Device).where(Device.udid == device_data.udid))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Device with this UDID already exists")
        
        device = Device(**device_data.model_dump())
        db.add(device)
        await db.commit()
        await db.refresh(device)
        
        logger.info("✅ Created device", device_id=device.id, name=device.name, udid=device.udid)
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to create device", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create device")


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int, 
    device_data: DeviceUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update device"""
    try:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Update fields
        update_data = device_data.model_dump(exclude_unset=True)
        if update_data:
            await db.execute(
                update(Device)
                .where(Device.id == device_id)
                .values(**update_data, updated_at=datetime.utcnow())
            )
            await db.commit()
            await db.refresh(device)
        
        logger.info("🔄 Updated device", device_id=device_id, updates=list(update_data.keys()))
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to update device", device_id=device_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update device")


@router.delete("/devices/{device_id}")
async def delete_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Delete device (simplified version)"""
    try:
        # Check if device exists
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        logger.info(f"🗑️ Deleting device {device_id} ({device.name})")
        
        # Simple device deletion - no complex cleanup for now
        await db.execute(delete(Device).where(Device.id == device_id))
        await db.commit()
        
        logger.info(f"✅ Successfully deleted device {device_id}")
        
        return {
            "message": "Device deleted successfully",
            "device_id": device_id,
            "device_name": device.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to delete device", device_id=device_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete device: {str(e)}")


@router.post("/devices/{device_id}/heartbeat")
async def device_heartbeat(device_id: int, db: AsyncSession = Depends(get_db)):
    """Update device last seen timestamp (heartbeat from device agent)"""
    try:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(last_seen=datetime.utcnow(), status="active")
        )
        await db.commit()
        
        logger.debug("💓 Device heartbeat", device_id=device_id)
        return {"message": "Heartbeat received"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device heartbeat failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail="Heartbeat failed")


@router.post("/devices/{device_id}/connect")
async def connect_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Connect to device via Appium"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Create Appium session
        session_id = await appium_service.create_session(device.udid)
        if not session_id:
            raise HTTPException(status_code=503, detail="Failed to connect to device")
        
        # Update device status
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(status="connected", last_seen=datetime.utcnow())
        )
        await db.commit()
        
        logger.info("🔗 Device connected", device_id=device_id, udid=device.udid)
        return {
            "message": "Device connected successfully",
            "session_id": session_id,
            "device_udid": device.udid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device connection failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Disconnect device Appium session"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Close Appium session
        success = await appium_service.close_session(device.udid)
        
        # Update device status
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(status="offline" if success else "error")
        )
        await db.commit()
        
        logger.info("🔌 Device disconnected", device_id=device_id, udid=device.udid)
        return {"message": "Device disconnected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device disconnection failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Disconnection failed: {str(e)}")


@router.post("/devices/{device_id}/instagram/login")
async def instagram_login(
    device_id: int, 
    login_data: Dict[str, str],
    db: AsyncSession = Depends(get_db)
):
    """Login to Instagram on device"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        username = login_data.get("username")
        password = login_data.get("password")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        
        # Perform Instagram login
        result = await instagram_service.login(device.udid, username, password)
        
        if result['success']:
            logger.info("📱 Instagram login successful", device_id=device_id, username=username)
        else:
            logger.warning("📱 Instagram login failed", device_id=device_id, message=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Instagram login error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Instagram login failed: {str(e)}")


@router.get("/appium/health")
async def appium_health():
    """Check Appium service health"""
    try:
        health = await appium_service.health_check()
        return health
    except Exception as e:
        logger.error("❌ Appium health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.post("/devices/{device_id}/start")
async def start_device_process(
    device_id: int, 
    template_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Start automation process for device with assigned template"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Send test WebSocket notification when device starts
        try:
            from ..services.websocket_manager import websocket_service
            await websocket_service.notify_account_processing(
                device_id=str(device.id),
                username="test_user_device_start",
                account_id="test_account_123",
                current_step="Device starting automation",
                progress=5
            )
            logger.info(f"📡 Test WebSocket notification sent for device start: {device.id}")
        except Exception as e:
            logger.error(f"Failed to send test WebSocket notification: {e}")
        
        session_id = None
        
        # Check if device is managed by a remote agent
        # Note: agent_id field doesn't exist in current Device model, so always use local Appium
        if hasattr(device, 'agent_id') and device.agent_id:
            # Use remote agent
            agent_id = device.agent_id
            
            # First, ensure the device is discovered and capabilities are loaded
            agent_devices = await appium_service.discover_remote_devices(agent_id)
            if not agent_devices:
                raise HTTPException(status_code=503, detail="No devices found on agent")
            
            # Check if our device is in the discovered devices
            device_found = False
            for discovered_device in agent_devices:
                if discovered_device['udid'] == device.udid:
                    device_found = True
                    break
            
            if not device_found:
                raise HTTPException(status_code=404, detail=f"Device {device.udid} not found on agent {agent_id}")
            
            session_id = await appium_service.create_remote_session(device.udid, agent_id)
            
            if not session_id:
                raise HTTPException(status_code=503, detail="Failed to create remote device session")
        else:
            # Use local Appium server
            server_started = await appium_service.start_appium_server()
            if not server_started:
                raise HTTPException(status_code=503, detail="Failed to start Appium server")
            
            # Discover local devices first to ensure capabilities are loaded
            try:
                local_devices = await appium_service.discover_devices()
                device_found = False
                for discovered_device in local_devices:
                    if discovered_device['udid'] == device.udid:
                        device_found = True
                        break
                
                if not device_found:
                    logger.warning(f"Device {device.udid} not found in discovery, but attempting to connect anyway")
                    # Don't fail here - some devices might not be discoverable but still connectable
            except Exception as e:
                logger.warning(f"Device discovery failed: {e}, but attempting to connect anyway")
                # Continue with connection attempt even if discovery fails
            
            session_id = await appium_service.create_session(device.udid)
            if not session_id:
                raise HTTPException(status_code=503, detail="Failed to create device session")
        
        # Update device status
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(status="running", last_seen=datetime.utcnow())
        )
        await db.commit()
        
        # If template_id provided, start template-based automation
        if template_id:
            # TODO: Implement template-based automation execution
            # This would create jobs based on the template configuration
            logger.info("🎯 Template-based automation started", 
                       device_id=device_id, template_id=template_id)
        
        logger.info("🚀 Device process started", device_id=device_id, udid=device.udid)
        return {
            "message": "Device process started successfully",
            "session_id": session_id,
            "device_udid": device.udid,
            "status": "running",
            "template_id": template_id,
            "agent_id": device.agent_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device process start failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Process start failed: {str(e)}")


@router.post("/devices/{device_id}/stop")
async def stop_device_process(device_id: int, db: AsyncSession = Depends(get_db)):
    """Stop automation process for device"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Close Appium session
        success = await appium_service.close_session(device.udid)
        
        # Update device status
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(status="stopped", last_seen=datetime.utcnow())
        )
        await db.commit()
        
        logger.info("🛑 Device process stopped", device_id=device_id, udid=device.udid)
        return {
            "message": "Device process stopped successfully",
            "device_udid": device.udid,
            "status": "stopped"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device process stop failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Process stop failed: {str(e)}")


@router.post("/devices/{device_id}/assign-agent")
async def assign_device_to_agent(
    device_id: int,
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Assign an existing device to an agent"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get agent from database
        agent_result = await db.execute(select(Agent).where(Agent.agent_id == agent_id))
        agent = agent_result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update device with agent assignment
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(
                agent_id=agent_id,
                platform=device.platform or "iOS",  # Default to iOS if not set
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
        
        # Register agent's Appium URL
        await appium_service.register_remote_agent(agent_id, agent.appium_url)
        
        # Try to discover the device from the agent
        try:
            agent_devices = await appium_service.discover_remote_devices(agent_id)
            device_found = False
            for discovered_device in agent_devices:
                if discovered_device['udid'] == device.udid:
                    device_found = True
                    break
            
            if not device_found:
                logger.warning(f"Device {device.udid} not found on agent {agent_id} during assignment")
        except Exception as e:
            logger.warning(f"Failed to discover device from agent during assignment: {e}")
        
        logger.info("📱 Device assigned to agent", device_id=device_id, agent_id=agent_id)
        return {
            "message": "Device assigned to agent successfully",
            "device_id": device_id,
            "agent_id": agent_id,
            "device_udid": device.udid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device assignment failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")

@router.post("/devices/{device_id}/discover-and-assign")
async def discover_and_assign_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Discover device from available agents and assign it"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get all online agents
        agent_result = await db.execute(select(Agent).where(Agent.status == "online"))
        agents = agent_result.scalars().all()
        
        if not agents:
            raise HTTPException(status_code=503, detail="No online agents available")
        
        # Try to find the device on any agent
        assigned_agent = None
        for agent in agents:
            try:
                # Register agent's Appium URL
                await appium_service.register_remote_agent(agent.agent_id, agent.appium_url)
                
                # Discover devices from this agent
                agent_devices = await appium_service.discover_remote_devices(agent.agent_id)
                
                # Check if our device is in the discovered devices
                for discovered_device in agent_devices:
                    if discovered_device['udid'] == device.udid:
                        assigned_agent = agent
                        break
                
                if assigned_agent:
                    break
                    
            except Exception as e:
                logger.warning(f"Failed to discover devices from agent {agent.agent_id}: {e}")
                continue
        
        if not assigned_agent:
            raise HTTPException(status_code=404, detail=f"Device {device.udid} not found on any agent")
        
        # Assign device to the agent
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(
                agent_id=assigned_agent.agent_id,
                platform=assigned_agent.platform or "iOS",
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
        
        logger.info("📱 Device discovered and assigned", device_id=device_id, agent_id=assigned_agent.agent_id)
        return {
            "message": "Device discovered and assigned successfully",
            "device_id": device_id,
            "agent_id": assigned_agent.agent_id,
            "device_udid": device.udid,
            "agent_url": assigned_agent.appium_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device discovery and assignment failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Discovery and assignment failed: {str(e)}")

@router.post("/devices/{device_id}/connect")
async def connect_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Connect/start a device (alias for start endpoint)"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Use the existing start_device_process logic
        if device.agent_id:
            # Use remote agent
            agent_id = device.agent_id

            # First, ensure the device is discovered and capabilities are loaded
            agent_devices = await appium_service.discover_remote_devices(agent_id)
            if not agent_devices:
                raise HTTPException(status_code=503, detail="No devices found on agent")

            # Check if our device is in the discovered devices
            device_found = False
            for discovered_device in agent_devices:
                if discovered_device['udid'] == device.udid:
                    device_found = True
                    break

            if not device_found:
                raise HTTPException(status_code=404, detail=f"Device {device.udid} not found on agent {agent_id}")

            session_id = await appium_service.create_remote_session(device.udid, agent_id)

            if not session_id:
                raise HTTPException(status_code=503, detail="Failed to create remote device session")
        else:
            # Use local Appium server
            server_started = await appium_service.start_appium_server()
            if not server_started:
                raise HTTPException(status_code=503, detail="Failed to start Appium server")

            # Discover local devices first to ensure capabilities are loaded
            local_devices = await appium_service.discover_devices()
            device_found = False
            for discovered_device in local_devices:
                if discovered_device['udid'] == device.udid:
                    device_found = True
                    break

            if not device_found:
                raise HTTPException(status_code=404, detail=f"Device {device.udid} not found locally")

            session_id = await appium_service.create_session(device.udid)
            if not session_id:
                raise HTTPException(status_code=503, detail="Failed to create device session")

        # Update device status
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(status="connected", last_seen=datetime.utcnow())
        )
        await db.commit()

        logger.info("🔌 Device connected", device_id=device_id, udid=device.udid, session_id=session_id)
        return {
            "message": "Device connected successfully",
            "device_id": device_id,
            "device_udid": device.udid,
            "session_id": session_id,
            "status": "connected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device connection failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Disconnect/stop a device (alias for stop endpoint)"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Close Appium session
        success = await appium_service.close_session(device.udid)
        
        # Update device status
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(status="offline", last_seen=datetime.utcnow())
        )
        await db.commit()
        
        logger.info("🔌 Device disconnected", device_id=device_id, udid=device.udid)
        return {
            "message": "Device disconnected successfully",
            "device_id": device_id,
            "device_udid": device.udid,
            "status": "offline"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Device disconnection failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Disconnection failed: {str(e)}")

# Proxy pools endpoint removed - not needed for basic cross-device sync functionality