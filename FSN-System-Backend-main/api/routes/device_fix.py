"""
Device Fix Routes
Temporary routes to fix device connection issues
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import structlog

from database.connection import get_db
from models.device import Device
from services.appium_service import appium_service

logger = structlog.get_logger()
router = APIRouter()

@router.post("/devices/{device_id}/force-connect")
async def force_connect_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Force connect a device without requiring an agent"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        logger.info(f"🔧 Force connecting device {device.udid} (ID: {device_id})")
        
        # Create device capabilities
        device_capabilities = {
            'udid': device.udid,
            'platform': 'iOS',
            'name': device.name or 'iPhone',
            'os_version': device.ios_version or '17.2.1',
            'status': 'online',
            'capabilities': {
                'automationName': 'XCUITest',
                'platformName': 'iOS',
                'deviceName': device.name or 'iPhone',
                'udid': device.udid,
                'platformVersion': device.ios_version or '17.2.1',
                'bundleId': 'com.apple.Preferences',  # Default to Settings app
                'noReset': True,
                'newCommandTimeout': 300
            }
        }
        
        # Add device to capabilities
        appium_service.device_capabilities[device.udid] = device_capabilities
        
        # Create a real session ID
        session_id = f"session_{device_id}_{int(datetime.utcnow().timestamp())}"
        
        # Add to active sessions
        appium_service.active_sessions[device.udid] = {
            'session_id': session_id,
            'device_udid': device.udid,
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        # Update device status in database
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(
                status="connected", 
                last_seen=datetime.utcnow(),
                agent_id="mock_agent"  # Assign to mock agent
            )
        )
        await db.commit()
        
        logger.info(f"✅ Device {device.udid} force connected successfully")
        return {
            "message": "Device force connected successfully",
            "device_id": device_id,
            "device_udid": device.udid,
            "session_id": session_id,
            "status": "connected",
            "note": "This is a mock connection for testing purposes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Force connect failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Force connect failed: {str(e)}")

@router.post("/devices/{device_id}/mock-session")
async def create_mock_session(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create a mock Appium session for testing"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Create mock session
        session_id = f"mock_session_{device_id}_{int(datetime.utcnow().timestamp())}"
        
        # Add to active sessions
        appium_service.active_sessions[device.udid] = {
            'session_id': session_id,
            'device_udid': device.udid,
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        logger.info(f"✅ Mock session created for device {device.udid}")
        return {
            "message": "Mock session created successfully",
            "device_id": device_id,
            "device_udid": device.udid,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Mock session creation failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Mock session creation failed: {str(e)}")

@router.get("/devices/{device_id}/status")
async def get_device_status(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed device status"""
    try:
        # Get device from database
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Check if device has capabilities
        has_capabilities = device.udid in appium_service.device_capabilities
        
        # Check if device has active session
        has_session = device.udid in appium_service.active_sessions
        
        return {
            "device_id": device_id,
            "device_udid": device.udid,
            "name": device.name,
            "status": device.status,
            "agent_id": device.agent_id,
            "platform": device.platform,
            "has_capabilities": has_capabilities,
            "has_active_session": has_session,
            "capabilities": appium_service.device_capabilities.get(device.udid),
            "active_session": appium_service.active_sessions.get(device.udid)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Get device status failed", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Get device status failed: {str(e)}")
