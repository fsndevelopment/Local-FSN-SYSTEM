"""
Pydantic schemas for warmup templates
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class WarmupDayConfig(BaseModel):
    """Schema for individual day configuration"""
    day_number: int = Field(..., ge=1, description="Day number (1, 2, 3, etc.)")
    scroll_minutes: int = Field(0, ge=0, description="Minutes to scroll on this day")
    likes_count: int = Field(0, ge=0, description="Number of likes on this day")
    follows_count: int = Field(0, ge=0, description="Number of follows on this day")
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_number": 1,
                "scroll_minutes": 10,
                "likes_count": 5,
                "follows_count": 2
            }
        }


class WarmupTemplateBase(BaseModel):
    """Base schema for warmup template"""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    platform: str = Field(..., description="Platform (threads, instagram)")
    total_days: int = Field(1, ge=1, le=365, description="Total number of days")
    days_config: List[WarmupDayConfig] = Field(..., min_items=1, description="Configuration for each day")
    scroll_minutes_per_day: int = Field(0, ge=0, description="Default scroll minutes per day")
    likes_per_day: int = Field(0, ge=0, description="Default likes per day")
    follows_per_day: int = Field(0, ge=0, description="Default follows per day")
    posting_interval_minutes: int = Field(30, ge=1, description="Minutes between warmup sessions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "7-Day Threads Warmup",
                "platform": "threads",
                "total_days": 7,
                "days_config": [
                    {
                        "day_number": 1,
                        "scroll_minutes": 10,
                        "likes_count": 5,
                        "follows_count": 2
                    },
                    {
                        "day_number": 2,
                        "scroll_minutes": 15,
                        "likes_count": 8,
                        "follows_count": 3
                    }
                ],
                "scroll_minutes_per_day": 10,
                "likes_per_day": 5,
                "follows_per_day": 2,
                "posting_interval_minutes": 30
            }
        }


class WarmupTemplateCreate(WarmupTemplateBase):
    """Schema for creating a new warmup template"""
    pass


class WarmupTemplateUpdate(BaseModel):
    """Schema for updating a warmup template"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    platform: Optional[str] = None
    total_days: Optional[int] = Field(None, ge=1, le=365)
    days_config: Optional[List[WarmupDayConfig]] = None
    scroll_minutes_per_day: Optional[int] = Field(None, ge=0)
    likes_per_day: Optional[int] = Field(None, ge=0)
    follows_per_day: Optional[int] = Field(None, ge=0)
    posting_interval_minutes: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class WarmupTemplateResponse(WarmupTemplateBase):
    """Schema for warmup template response"""
    id: int
    license_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class WarmupTemplateList(BaseModel):
    """Schema for warmup template list response"""
    templates: List[WarmupTemplateResponse]
    total: int
    page: int
    per_page: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "templates": [],
                "total": 0,
                "page": 1,
                "per_page": 10
            }
        }


class WarmupExecutionRequest(BaseModel):
    """Schema for warmup execution request"""
    device_id: str = Field(..., description="Device ID to execute warmup on")
    warmup_template_id: str = Field(..., description="Warmup template ID to execute")
    account_phases: Dict[str, str] = Field(..., description="Account phases mapping (account_id -> 'warmup' or 'posting')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device-123",
                "warmup_template_id": "template-456",
                "account_phases": {
                    "account-1": "warmup",
                    "account-2": "posting"
                }
            }
        }


class WarmupProgress(BaseModel):
    """Schema for warmup progress tracking"""
    account_id: str
    current_day: int
    completed_today: bool
    last_warmup_date: Optional[str] = None
    warmup_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    next_warmup_day: int
    warmup_template_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "account-123",
                "current_day": 3,
                "completed_today": True,
                "last_warmup_date": "2025-01-23",
                "warmup_stats": {
                    "day_1": {
                        "likes": 5,
                        "follows": 2,
                        "scroll_minutes": 10,
                        "completed_at": "2025-01-21T10:30:00Z"
                    },
                    "day_2": {
                        "likes": 8,
                        "follows": 3,
                        "scroll_minutes": 15,
                        "completed_at": "2025-01-22T14:20:00Z"
                    }
                },
                "next_warmup_day": 4,
                "warmup_template_id": "template-456"
            }
        }


class WarmupStatus(BaseModel):
    """Schema for warmup status response"""
    account_id: str
    phase: str = Field(..., description="Current phase: 'warmup' or 'posting'")
    status: str = Field(..., description="Status: 'ready', 'processing', 'cooldown', 'completed'")
    current_day: Optional[int] = None
    total_days: Optional[int] = None
    progress_percentage: Optional[float] = None
    cooldown_remaining_minutes: Optional[int] = None
    today_stats: Optional[Dict[str, int]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "account-123",
                "phase": "warmup",
                "status": "processing",
                "current_day": 3,
                "total_days": 7,
                "progress_percentage": 42.9,
                "cooldown_remaining_minutes": 0,
                "today_stats": {
                    "likes": 8,
                    "follows": 3,
                    "scroll_minutes": 15
                }
            }
        }
