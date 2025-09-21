"""
Device Model
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any

class Device(BaseModel):
    """Device model for job execution"""
    id: str
    udid: str
    platform: str
    name: str
    status: str
    appium_port: int
    wda_port: int
    mjpeg_port: int
    last_seen: str
    ios_version: str
    model: str
    wda_bundle_id: str
    jailbroken: bool
    settings: Dict[str, Any]
    ngrok_token: Optional[str] = None  # Optional ngrok token for photo posting