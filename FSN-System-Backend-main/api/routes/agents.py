"""
Agent management routes for local device agents
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import secrets
import string

from database.connection import get_db
from models.agent import Agent, PairToken
from schemas.agent import (
    PairTokenRequest, PairTokenResponse, AgentPairRequest, AgentPairResponse,
    AgentCreate, AgentResponse, AgentUpdate, AgentHeartbeat, 
    AgentRegisterRequest, AgentRegisterResponse, DeviceRegistration
)
from services.agent_service import AgentService
from services.jwt_service import jwt_service
from services.qr_service import qr_service

router = APIRouter(prefix="/api/agents", tags=["agents"])
logger = logging.getLogger(__name__)

agent_service = AgentService()

# Pairing endpoints
@router.post("/pair-token", response_model=PairTokenResponse)
async def create_pair_token(
    request: PairTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate pair token and QR code for agent pairing"""
    try:
        # Generate random pair token
        pair_token = ''.join(secrets.choices(string.ascii_letters + string.digits, k=32))
        
        # Create QR payload
        qr_payload = f"fsn://pair?token={pair_token}"
        
        # Set expiration (10 minutes from now)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Store pair token in database
        pair_token_record = PairToken(
            pair_token=pair_token,
            license_id=request.license_id,
            qr_payload=qr_payload,
            expires_at=expires_at
        )
        
        db.add(pair_token_record)
        await db.commit()
        await db.refresh(pair_token_record)
        
        logger.info("✅ Created pair token", license_id=request.license_id, pair_token=pair_token)
        
        return PairTokenResponse(
            pair_token=pair_token,
            qr_payload=qr_payload,
            expires_at=expires_at
        )
        
    except Exception as e:
        logger.error("❌ Failed to create pair token", error=str(e), license_id=request.license_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to create pair token"
        )

@router.post("/pair", response_model=AgentPairResponse)
async def pair_agent(
    request: AgentPairRequest,
    db: AsyncSession = Depends(get_db)
):
    """Pair agent using pair token"""
    try:
        # Verify pair token
        result = await db.execute(
            select(PairToken).where(
                PairToken.pair_token == request.pair_token,
                PairToken.used == False,
                PairToken.expires_at > datetime.utcnow()
            )
        )
        pair_token_record = result.scalar_one_or_none()
        
        if not pair_token_record:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired pair token"
            )
        
        # Mark pair token as used
        await db.execute(
            update(PairToken)
            .where(PairToken.id == pair_token_record.id)
            .values(used=True)
        )
        
        # Generate unique agent ID
        agent_id = f"agent_{secrets.token_hex(16)}"
        
        # Create agent record
        agent = Agent(
            agent_id=agent_id,
            license_id=pair_token_record.license_id,
            agent_name=request.agent_name,
            platform=request.platform,
            app_version=request.app_version,
            status="offline"
        )
        
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        
        # Generate agent JWT token
        agent_token = jwt_service.create_agent_token(agent.id, agent.license_id)
        
        # Update agent with token
        await db.execute(
            update(Agent)
            .where(Agent.id == agent.id)
            .values(agent_token=agent_token)
        )
        await db.commit()
        
        logger.info("✅ Agent paired successfully", agent_id=agent.id, license_id=agent.license_id)
        
        return AgentPairResponse(
            agent_id=agent.id,
            agent_token=agent_token,
            appium_base_path="/wd/hub"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Agent pairing failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Agent pairing failed"
        )

# Agent authentication dependency
async def get_agent_from_token(
    authorization: Optional[str] = Header(None)
) -> Agent:
    """Extract and validate agent from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Verify token
        payload = jwt_service.verify_agent_token(token)
        agent_id = payload.get("agent_id")
        license_id = payload.get("license_id")
        
        if not agent_id or not license_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )
        
        # Get database session
        async for db in get_db():
            result = await db.execute(
                select(Agent).where(Agent.id == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise HTTPException(
                    status_code=404,
                    detail="Agent not found"
                )
            
            if agent.license_id != license_id:
                raise HTTPException(
                    status_code=403,
                    detail="Agent license mismatch"
                )
            
            return agent
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Agent authentication failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail="Agent authentication failed"
        )

@router.post("/register", response_model=AgentRegisterResponse)
async def register_agent(
    request: AgentRegisterRequest,
    agent: Agent = Depends(get_agent_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Register device endpoints from agent"""
    try:
        # Update agent status to online
        await db.execute(
            update(Agent)
            .where(Agent.id == agent.id)
            .values(
                status="online",
                last_seen=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        
        # Register each device endpoint
        for endpoint in request.endpoints:
            # Update or create device record
            from models.device import Device
            result = await db.execute(
                select(Device).where(Device.udid == endpoint.udid)
            )
            device = result.scalar_one_or_none()
            
            if device:
                # Update existing device
                await db.execute(
                    update(Device)
                    .where(Device.udid == endpoint.udid)
                    .values(
                        agent_id=agent.id,
                        appium_port=endpoint.local_appium_port,
                        wda_port=endpoint.wda_local_port,
                        mjpeg_port=endpoint.mjpeg_port,
                        public_url=endpoint.public_url,
                        appium_base_path=endpoint.appium_base_path,
                        is_online=True,
                        last_seen=datetime.utcnow()
                    )
                )
            else:
                # Create new device
                device = Device(
                    udid=endpoint.udid,
                    license_id=agent.license_id,
                    name=f"Device {endpoint.udid[:8]}",
                    platform="iOS",  # Default to iOS for now
                    agent_id=agent.id,
                    appium_port=endpoint.local_appium_port,
                    wda_port=endpoint.wda_local_port,
                    mjpeg_port=endpoint.mjpeg_port,
                    public_url=endpoint.public_url,
                    appium_base_path=endpoint.appium_base_path,
                    is_online=True,
                    last_seen=datetime.utcnow()
                )
                db.add(device)
        
        await db.commit()
        
        logger.info("✅ Agent registered devices", agent_id=agent.id, device_count=len(request.endpoints))
        
        return AgentRegisterResponse(agent_id=agent.id)
        
    except Exception as e:
        logger.error("❌ Agent registration failed", error=str(e), agent_id=agent.id)
        raise HTTPException(
            status_code=500,
            detail="Agent registration failed"
        )

@router.post("/heartbeat")
async def agent_heartbeat(
    heartbeat_data: AgentHeartbeat,
    agent: Agent = Depends(get_agent_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Receive heartbeat from agent"""
    try:
        # Update agent heartbeat
        await db.execute(
            update(Agent)
            .where(Agent.id == agent.id)
            .values(
                status="online",
                last_seen=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        
        # Update device statuses if provided
        if heartbeat_data.udids:
            from models.device import Device
            for udid in heartbeat_data.udids:
                await db.execute(
                    update(Device)
                    .where(Device.udid == udid, Device.agent_id == agent.id)
                    .values(
                        is_online=True,
                        last_seen=datetime.utcnow()
                    )
                )
        
        await db.commit()
        
        logger.debug("💓 Heartbeat received from agent", agent_id=agent.id, udids=heartbeat_data.udids)
        return {"ok": True}
        
    except Exception as e:
        logger.error("❌ Heartbeat processing failed", error=str(e), agent_id=agent.id)
        raise HTTPException(
            status_code=500,
            detail="Heartbeat processing failed"
        )

@router.get("/active/{license_id}")
async def get_active_agent(
    license_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get active agent for license with device endpoints"""
    try:
        # Get active agent for license
        result = await db.execute(
            select(Agent).where(
                Agent.license_id == license_id,
                Agent.status == "online"
            )
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            return {"agent": None, "devices": []}
        
        # Get devices for this agent
        from models.device import Device
        devices_result = await db.execute(
            select(Device).where(Device.agent_id == agent.id)
        )
        devices = devices_result.scalars().all()
        
        return {
            "agent": agent,
            "devices": devices
        }
        
    except Exception as e:
        logger.error("❌ Failed to get active agent", error=str(e), license_id=license_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to get active agent"
        )

@router.get("/", response_model=List[AgentResponse])
async def get_agents(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all registered agents"""
    try:
        query = select(Agent)
        
        if status:
            query = query.where(Agent.status == status)
        
        result = await db.execute(query)
        agents = result.scalars().all()
        
        return agents
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve agents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve agents"
        )

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific agent by ID"""
    try:
        result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail="Agent not found"
            )
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve agent"
        )

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update agent information"""
    try:
        # Check if agent exists
        result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail="Agent not found"
            )
        
        # Update agent
        update_data = agent_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await db.execute(
            update(Agent)
            .where(Agent.agent_id == agent_id)
            .values(**update_data)
        )
        
        await db.commit()
        await db.refresh(agent)
        
        logger.info(f"✅ Updated agent: {agent_id}")
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Agent update failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent update failed: {str(e)}"
        )

@router.delete("/{agent_id}")
async def unregister_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Unregister agent"""
    try:
        result = await db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail="Agent not found"
            )
        
        # Mark agent as offline instead of deleting
        await db.execute(
            update(Agent)
            .where(Agent.agent_id == agent_id)
            .values(
                status="offline",
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        
        logger.info(f"✅ Unregistered agent: {agent_id}")
        return {"message": "Agent unregistered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Agent unregistration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent unregistration failed: {str(e)}"
        )

@router.get("/{agent_id}/devices")
async def get_agent_devices(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get devices registered by specific agent"""
    try:
        devices = await agent_service.get_agent_devices(db, agent_id)
        return {"devices": devices}
        
    except Exception as e:
        logger.error(f"❌ Failed to get agent devices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get agent devices"
        )

@router.post("/devices/register")
async def register_device_from_agent(
    device_data: DeviceRegistration,
    db: AsyncSession = Depends(get_db)
):
    """Register device from agent"""
    try:
        device = await agent_service.register_device_from_agent(db, device_data)
        logger.info(f"✅ Registered device from agent: {device_data.udid}")
        return device
        
    except Exception as e:
        logger.error(f"❌ Device registration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Device registration failed: {str(e)}"
        )

@router.get("/health/status")
async def get_agents_health():
    """Get overall agents health status"""
    try:
        health_status = await agent_service.get_agents_health()
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Failed to get agents health: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get agents health"
        )
