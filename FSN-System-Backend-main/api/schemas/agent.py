"""
Agent schemas for API responses
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

# Pairing schemas
class PairTokenRequest(BaseModel):
    license_id: str

class PairTokenResponse(BaseModel):
    pair_token: str
    qr_payload: str
    expires_at: datetime

class AgentPairRequest(BaseModel):
    pair_token: str
    agent_name: str
    platform: str
    app_version: str

class AgentPairResponse(BaseModel):
    agent_id: int
    agent_token: str
    appium_base_path: str

# Agent management schemas
class AgentCreate(BaseModel):
    agent_id: str
    license_id: str
    agent_name: str
    platform: str
    app_version: str
    agent_token: Optional[str] = None

class AgentUpdate(BaseModel):
    status: Optional[str] = None
    last_seen: Optional[datetime] = None

class AgentResponse(BaseModel):
    id: int
    agent_id: str
    license_id: str
    agent_name: str
    platform: str
    app_version: str
    appium_base_path: str
    status: str
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AgentHeartbeat(BaseModel):
    agent_id: int
    udids: List[str]
    uptime: int
    version: str

class DeviceEndpoint(BaseModel):
    udid: str
    local_appium_port: int
    public_url: str
    appium_base_path: str
    wda_local_port: int
    mjpeg_port: int

class AgentRegisterRequest(BaseModel):
    agent_name: str
    license_id: str
    endpoints: List[DeviceEndpoint]

class AgentRegisterResponse(BaseModel):
    agent_id: int

class DeviceRegistration(BaseModel):
    udid: str
    platform: str
    name: str
    status: str
    last_seen: str
    agent_id: str
    tunnel_url: str
    appium_url: str
