"""
Schedule API Schemas

Pydantic models for schedule configuration endpoints
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, time
from enum import Enum


class Platform(str, Enum):
    """Platform enumeration"""
    INSTAGRAM = "instagram"
    THREADS = "threads"
    BOTH = "both"


class ScheduleType(str, Enum):
    """Schedule type enumeration"""
    WARMUP = "warmup"
    POSTING = "posting"
    ENGAGEMENT = "engagement"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"


class ScheduleStatus(str, Enum):
    """Schedule status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DISABLED = "disabled"


class RepeatPattern(str, Enum):
    """Repeat pattern enumeration"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ScheduleCreate(BaseModel):
    """Schema for creating new schedules"""
    name: str = Field(..., min_length=1, max_length=100, description="Schedule name")
    description: Optional[str] = Field(None, max_length=500, description="Schedule description")
    
    # Platform Support
    platform: Platform = Field(..., description="Target platform(s)")
    
    # Schedule Configuration
    type: ScheduleType = Field(..., description="Type of scheduled automation")
    account_id: Optional[int] = Field(None, description="Specific account (null for all)")
    device_id: Optional[int] = Field(None, description="Specific device (null for any)")
    
    # Timing Configuration
    start_time: time = Field(..., description="Daily start time")
    end_time: time = Field(..., description="Daily end time")
    start_date: datetime = Field(..., description="Schedule start date")
    end_date: Optional[datetime] = Field(None, description="Schedule end date (null for indefinite)")
    
    # Repeat Configuration
    repeat_pattern: RepeatPattern = Field(RepeatPattern.DAILY, description="How often to repeat")
    repeat_interval: int = Field(1, ge=1, description="Interval for repeat pattern")
    weekdays: Optional[List[int]] = Field(None, description="Days of week (0=Monday, 6=Sunday)")
    
    # Action Configuration
    actions_per_hour: int = Field(10, ge=1, le=100, description="Actions per hour limit")
    max_daily_actions: int = Field(100, ge=1, le=1000, description="Maximum daily actions")
    
    # Advanced Configuration
    priority: int = Field(5, ge=1, le=10, description="Schedule priority (1=low, 10=high)")
    enabled: bool = Field(True, description="Whether schedule is enabled")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Schedule-specific settings")


class ScheduleUpdate(BaseModel):
    """Schema for updating existing schedules"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Schedule name")
    description: Optional[str] = Field(None, max_length=500, description="Schedule description")
    
    platform: Optional[Platform] = Field(None, description="Target platform(s)")
    type: Optional[ScheduleType] = Field(None, description="Type of scheduled automation")
    account_id: Optional[int] = Field(None, description="Specific account (null for all)")
    device_id: Optional[int] = Field(None, description="Specific device (null for any)")
    
    start_time: Optional[time] = Field(None, description="Daily start time")
    end_time: Optional[time] = Field(None, description="Daily end time")
    start_date: Optional[datetime] = Field(None, description="Schedule start date")
    end_date: Optional[datetime] = Field(None, description="Schedule end date")
    
    repeat_pattern: Optional[RepeatPattern] = Field(None, description="How often to repeat")
    repeat_interval: Optional[int] = Field(None, ge=1, description="Interval for repeat pattern")
    weekdays: Optional[List[int]] = Field(None, description="Days of week")
    
    actions_per_hour: Optional[int] = Field(None, ge=1, le=100, description="Actions per hour limit")
    max_daily_actions: Optional[int] = Field(None, ge=1, le=1000, description="Maximum daily actions")
    
    priority: Optional[int] = Field(None, ge=1, le=10, description="Schedule priority")
    status: Optional[ScheduleStatus] = Field(None, description="Schedule status")
    enabled: Optional[bool] = Field(None, description="Whether schedule is enabled")
    settings: Optional[Dict[str, Any]] = Field(None, description="Schedule-specific settings")


class ScheduleResponse(BaseModel):
    """Schema for schedule API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    platform: Platform
    type: ScheduleType
    status: ScheduleStatus
    account_id: Optional[int] = None
    device_id: Optional[int] = None
    
    start_time: time
    end_time: time
    start_date: datetime
    end_date: Optional[datetime] = None
    
    repeat_pattern: RepeatPattern
    repeat_interval: int
    weekdays: Optional[List[int]] = None
    
    actions_per_hour: int
    max_daily_actions: int
    
    priority: int
    enabled: bool
    settings: Optional[Dict[str, Any]] = None
    
    # Execution stats
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None


class ScheduleStats(BaseModel):
    """Schema for schedule statistics"""
    total_schedules: int = 0
    active_schedules: int = 0
    paused_schedules: int = 0
    completed_schedules: int = 0
    disabled_schedules: int = 0
    
    # Platform breakdown
    instagram_schedules: int = 0
    threads_schedules: int = 0
    dual_platform_schedules: int = 0
    
    # Type breakdown
    warmup_schedules: int = 0
    posting_schedules: int = 0
    engagement_schedules: int = 0
    maintenance_schedules: int = 0
    custom_schedules: int = 0
    
    # Performance metrics
    total_executions: int = 0
    successful_executions: int = 0
    success_rate: float = 0.0
    avg_actions_per_hour: float = 0.0


class ScheduleListResponse(BaseModel):
    """Schema for paginated schedule list responses"""
    items: List[ScheduleResponse]
    total: int
    page: int
    size: int
    pages: int


class ScheduleExecution(BaseModel):
    """Schema for schedule execution tracking"""
    id: int
    schedule_id: int
    account_id: Optional[int] = None
    device_id: Optional[int] = None
    
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # "running", "completed", "failed", "cancelled"
    
    actions_executed: int = 0
    actions_successful: int = 0
    actions_failed: int = 0
    
    error_message: Optional[str] = None
    execution_log: Optional[Dict[str, Any]] = None


class BulkScheduleCreate(BaseModel):
    """Schema for bulk schedule creation"""
    schedules: List[ScheduleCreate] = Field(..., min_length=1, max_length=50, description="List of schedules to create")
    batch_name: Optional[str] = Field(None, description="Optional batch identifier")


class BulkScheduleResponse(BaseModel):
    """Schema for bulk schedule creation response"""
    created_count: int
    failed_count: int
    created_schedules: List[ScheduleResponse]
    failed_schedules: List[Dict[str, Any]]
    batch_name: Optional[str] = None
