"""
Agent service for managing local device agents
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from models.agent import Agent
from models.device import Device
from schemas.agent import DeviceRegistration

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing local device agents"""
    
    def __init__(self):
        self.heartbeat_timeout = timedelta(minutes=5)  # 5 minutes timeout
    
    async def update_device_statuses(
        self, 
        db: AsyncSession, 
        agent_id: str, 
        device_udids: List[str]
    ):
        """Update device statuses based on agent heartbeat"""
        try:
            # Mark devices from this agent as online
            await db.execute(
                update(Device)
                .where(
                    and_(
                        Device.agent_id == agent_id,
                        Device.udid.in_(device_udids)
                    )
                )
                .values(
                    status="online",
                    last_seen=datetime.utcnow()
                )
            )
            
            # Mark devices not in the list as offline
            await db.execute(
                update(Device)
                .where(
                    and_(
                        Device.agent_id == agent_id,
                        ~Device.udid.in_(device_udids)
                    )
                )
                .values(
                    status="offline",
                    last_seen=datetime.utcnow()
                )
            )
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update device statuses: {str(e)}")
            raise
    
    async def get_agent_devices(
        self, 
        db: AsyncSession, 
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """Get devices registered by specific agent"""
        try:
            result = await db.execute(
                select(Device)
                .where(Device.agent_id == agent_id)
                .order_by(Device.created_at.desc())
            )
            devices = result.scalars().all()
            
            return [
                {
                    "id": device.id,
                    "udid": device.udid,
                    "name": device.name,
                    "platform": device.platform,
                    "status": device.status,
                    "last_seen": device.last_seen,
                    "created_at": device.created_at
                }
                for device in devices
            ]
            
        except Exception as e:
            logger.error(f"Failed to get agent devices: {str(e)}")
            raise
    
    async def register_device_from_agent(
        self, 
        db: AsyncSession, 
        device_data: DeviceRegistration
    ) -> Dict[str, Any]:
        """Register device from agent"""
        try:
            # Check if device already exists
            result = await db.execute(
                select(Device).where(Device.udid == device_data.udid)
            )
            existing_device = result.scalar_one_or_none()
            
            if existing_device:
                # Update existing device
                await db.execute(
                    update(Device)
                    .where(Device.udid == device_data.udid)
                    .values(
                        name=device_data.name,
                        platform=device_data.platform,
                        status=device_data.status,
                        last_seen=datetime.fromisoformat(device_data.last_seen),
                        agent_id=device_data.agent_id,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                await db.refresh(existing_device)
                
                logger.info(f"Updated existing device: {device_data.udid}")
                return {
                    "id": existing_device.id,
                    "udid": existing_device.udid,
                    "name": existing_device.name,
                    "platform": existing_device.platform,
                    "status": existing_device.status,
                    "agent_id": existing_device.agent_id
                }
            else:
                # Create new device
                device = Device(
                    udid=device_data.udid,
                    name=device_data.name,
                    platform=device_data.platform,
                    status=device_data.status,
                    last_seen=datetime.fromisoformat(device_data.last_seen),
                    agent_id=device_data.agent_id
                )
                
                db.add(device)
                await db.commit()
                await db.refresh(device)
                
                logger.info(f"Registered new device: {device_data.udid}")
                return {
                    "id": device.id,
                    "udid": device.udid,
                    "name": device.name,
                    "platform": device.platform,
                    "status": device.status,
                    "agent_id": device.agent_id
                }
                
        except Exception as e:
            logger.error(f"Failed to register device from agent: {str(e)}")
            raise
    
    async def get_agents_health(self) -> Dict[str, Any]:
        """Get overall agents health status"""
        try:
            # This would typically query the database
            # For now, return a basic health status
            return {
                "total_agents": 0,
                "online_agents": 0,
                "offline_agents": 0,
                "last_check": datetime.utcnow().isoformat(),
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Failed to get agents health: {str(e)}")
            raise
    
    async def get_agent_by_id(
        self, 
        db: AsyncSession, 
        agent_id: str
    ) -> Optional[Agent]:
        """Get agent by ID"""
        try:
            result = await db.execute(
                select(Agent).where(Agent.agent_id == agent_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get agent by ID: {str(e)}")
            raise
    
    async def is_agent_online(
        self, 
        db: AsyncSession, 
        agent_id: str
    ) -> bool:
        """Check if agent is online based on last heartbeat"""
        try:
            agent = await self.get_agent_by_id(db, agent_id)
            
            if not agent:
                return False
            
            if not agent.last_heartbeat:
                return False
            
            # Check if heartbeat is within timeout
            time_since_heartbeat = datetime.utcnow() - agent.last_heartbeat
            return time_since_heartbeat < self.heartbeat_timeout
            
        except Exception as e:
            logger.error(f"Failed to check agent online status: {str(e)}")
            return False
