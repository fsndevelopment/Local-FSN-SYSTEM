"""
Account Model
"""

from pydantic import BaseModel
from typing import Optional

class Account(BaseModel):
    """Account model for job execution"""
    id: str
    username: str
    email: str
    password: str
    platform: str
    auth_type: str
    two_factor_code: Optional[str] = None
    container_id: Optional[str] = None  # For jailbroken devices
    is_active: bool = True
    created_at: str
    updated_at: str