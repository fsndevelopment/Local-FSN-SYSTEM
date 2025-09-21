"""
Account Management Schemas

Pydantic schemas for account-related API operations
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AccountStatus(str, Enum):
    """Account status enumeration"""
    ACTIVE = "active"
    WARMING_UP = "warming_up"
    SUSPENDED = "suspended"
    BANNED = "banned"
    INACTIVE = "inactive"


class WarmupPhase(str, Enum):
    """Warmup phase enumeration"""
    PHASE_1 = "phase_1"  # Days 1-3: Basic activity
    PHASE_2 = "phase_2"  # Days 4-7: Increased engagement
    PHASE_3 = "phase_3"  # Days 8-14: Full activity
    COMPLETE = "complete"  # Warmup finished


class Platform(str, Enum):
    """Platform enumeration"""
    INSTAGRAM = "instagram"
    THREADS = "threads"
    BOTH = "both"


class AccountCreate(BaseModel):
    """Schema for creating new accounts"""
    username: str = Field(..., min_length=1, max_length=30, description="Primary username")
    platform: Platform = Field(Platform.INSTAGRAM, description="Target platform(s)")
    instagram_username: Optional[str] = Field(None, description="Instagram username")
    threads_username: Optional[str] = Field(None, description="Threads username")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    password: str = Field(..., min_length=6, description="Account password")
    auth_type: Optional[str] = Field(None, description="Authentication type (2fa, non-2fa)")
    two_factor_code: Optional[str] = Field(None, description="Two-factor authentication code")
    device_id: Optional[int] = Field(None, description="Assigned device ID")
    model_id: Optional[int] = Field(None, description="Model profile ID")
    notes: Optional[str] = Field(None, description="Account notes")
    container_number: Optional[int] = Field(None, description="Container number")
    bio: Optional[str] = Field(None, max_length=150, description="Account bio")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Account-specific settings")


class AccountUpdate(BaseModel):
    """Schema for updating existing accounts"""
    platform: Optional[Platform] = Field(None, description="Target platform(s)")
    instagram_username: Optional[str] = Field(None, description="Instagram username")
    threads_username: Optional[str] = Field(None, description="Threads username")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    password: Optional[str] = Field(None, min_length=6, description="Account password")
    auth_type: Optional[str] = Field(None, description="Authentication type (2fa, non-2fa)")
    two_factor_code: Optional[str] = Field(None, description="Two-factor authentication code")
    device_id: Optional[int] = Field(None, description="Assigned device ID")
    model_id: Optional[int] = Field(None, description="Model profile ID")
    notes: Optional[str] = Field(None, description="Account notes")
    container_number: Optional[int] = Field(None, description="Container number")
    status: Optional[AccountStatus] = Field(None, description="Account status")
    bio: Optional[str] = Field(None, max_length=150, description="Account bio")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    warmup_phase: Optional[WarmupPhase] = Field(None, description="Current warmup phase")
    settings: Optional[Dict[str, Any]] = Field(None, description="Account-specific settings")


class AccountResponse(BaseModel):
    """Schema for account API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    platform: Platform
    instagram_username: Optional[str] = None
    threads_username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    auth_type: Optional[str] = None
    two_factor_code: Optional[str] = None
    device_id: Optional[int] = None
    model_id: Optional[int] = None
    notes: Optional[str] = None
    container_number: Optional[int] = None
    status: AccountStatus
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    warmup_phase: Optional[WarmupPhase] = None
    warmup_start_date: Optional[datetime] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class AccountStats(BaseModel):
    """Schema for account statistics"""
    total_accounts: int = 0
    active_accounts: int = 0
    warming_up_accounts: int = 0
    suspended_accounts: int = 0
    banned_accounts: int = 0
    inactive_accounts: int = 0
    
    # Warmup phase breakdown
    phase_1_accounts: int = 0
    phase_2_accounts: int = 0
    phase_3_accounts: int = 0
    complete_accounts: int = 0


class AccountListResponse(BaseModel):
    """Schema for paginated account list responses"""
    items: List[AccountResponse]
    total: int
    page: int
    size: int
    pages: int


class AccountActivityLog(BaseModel):
    """Schema for account activity logging"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    action_type: str
    description: str
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class ModelProfileResponse(BaseModel):
    """Schema for model profile responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    age_range: Optional[str] = None
    location: Optional[str] = None
    interests: Optional[List[str]] = None
    posting_schedule: Optional[Dict[str, Any]] = None
    engagement_strategy: Optional[Dict[str, Any]] = None
    content_preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
