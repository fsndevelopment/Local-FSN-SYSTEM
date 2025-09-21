"""
Pydantic schemas for device-related API operations
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class DeviceBase(BaseModel):
    """Base device schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Device display name")
    udid: str = Field(..., min_length=1, max_length=100, description="Device UDID")
    ios_version: Optional[str] = Field(None, max_length=20, description="iOS version")
    model: Optional[str] = Field(None, max_length=50, description="iPhone model")
    appium_port: int = Field(4723, ge=1024, le=65535, description="Appium server port")
    wda_port: int = Field(8100, ge=1024, le=65535, description="WDA server port")
    mjpeg_port: int = Field(9100, ge=1024, le=65535, description="MJPEG stream port")
    wda_bundle_id: Optional[str] = Field(None, max_length=100, description="WDA Bundle ID (e.g., com.device1.wd1)")
    jailbroken: bool = Field(False, description="Whether device is jailbroken")
    proxy_pool_id: Optional[int] = Field(None, description="Assigned proxy pool ID")
    settings: Optional[Dict[str, Any]] = Field(None, description="Device-specific settings")


class DeviceCreate(DeviceBase):
    """Schema for creating a new device"""
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    ios_version: Optional[str] = Field(None, max_length=20)
    model: Optional[str] = Field(None, max_length=50)
    appium_port: Optional[int] = Field(None, ge=1024, le=65535)
    wda_port: Optional[int] = Field(None, ge=1024, le=65535)
    mjpeg_port: Optional[int] = Field(None, ge=1024, le=65535)
    wda_bundle_id: Optional[str] = Field(None, max_length=100)
    jailbroken: Optional[bool] = Field(None)
    status: Optional[str] = Field(None, description="Device status")
    proxy_pool_id: Optional[int] = Field(None)
    settings: Optional[Dict[str, Any]] = Field(None)


class DeviceResponse(DeviceBase):
    """Schema for device API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: str
    last_seen: datetime
    created_at: datetime
    updated_at: Optional[datetime]


# ProxyPool schemas removed - not needed for basic cross-device sync functionality
