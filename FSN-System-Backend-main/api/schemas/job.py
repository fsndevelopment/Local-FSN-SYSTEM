"""
Job Queue Management Schemas

Pydantic schemas for job queue API operations
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    """Platform enumeration"""
    INSTAGRAM = "instagram"
    THREADS = "threads"


class JobType(str, Enum):
    """Job type enumeration for Instagram & Threads"""
    # Instagram Jobs
    INSTAGRAM_FOLLOW_USER = "instagram_follow_user"
    INSTAGRAM_UNFOLLOW_USER = "instagram_unfollow_user"
    INSTAGRAM_LIKE_POST = "instagram_like_post"
    INSTAGRAM_COMMENT_POST = "instagram_comment_post"
    INSTAGRAM_POST_REEL = "instagram_post_reel"
    INSTAGRAM_POST_STORY = "instagram_post_story"
    INSTAGRAM_VIEW_STORY = "instagram_view_story"
    INSTAGRAM_DIRECT_MESSAGE = "instagram_direct_message"
    INSTAGRAM_PROFILE_UPDATE = "instagram_profile_update"
    INSTAGRAM_ACCOUNT_WARMUP = "instagram_account_warmup"
    
    # Threads Jobs
    THREADS_FOLLOW_USER = "threads_follow_user"
    THREADS_UNFOLLOW_USER = "threads_unfollow_user"
    THREADS_LIKE_POST = "threads_like_post"
    THREADS_COMMENT_POST = "threads_comment_post"
    THREADS_CREATE_POST = "threads_create_post"
    THREADS_REPOST = "threads_repost"
    THREADS_QUOTE_POST = "threads_quote_post"
    THREADS_DIRECT_MESSAGE = "threads_direct_message"
    THREADS_PROFILE_UPDATE = "threads_profile_update"
    THREADS_ACCOUNT_WARMUP = "threads_account_warmup"
    
    # Scrolling Jobs - Phase 5
    INSTAGRAM_SCROLL_HOME_FEED = "instagram_scroll_home_feed"
    INSTAGRAM_SCROLL_REELS = "instagram_scroll_reels"
    THREADS_SCROLL_HOME_FEED = "threads_scroll_home_feed"
    
    # Legacy Support (for backward compatibility)
    LIKE_POST = "LIKE_POST"
    LIKE = "LIKE"  # Legacy alias for LIKE_POST
    FOLLOW_USER = "FOLLOW_USER"
    VIEW_STORY = "VIEW_STORY"
    COMMENT_POST = "COMMENT_POST"
    LOGIN = "LOGIN"


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    """Job priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class JobCreate(BaseModel):
    """Schema for creating new jobs"""
    account_id: int = Field(..., description="Account to execute job on")
    platform: Platform = Field(..., description="Target platform")
    type: JobType = Field(..., description="Type of job to execute")
    payload: Dict[str, Any] = Field(..., description="Job-specific data")
    scroll_type: Optional[str] = Field(None, description="For scrolling jobs: home_feed, reels, threads_feed")
    scroll_count: Optional[int] = Field(None, description="Number of scrolls to perform")
    priority: Optional[JobPriority] = Field(JobPriority.NORMAL, description="Job priority")
    not_before: Optional[datetime] = Field(None, description="Earliest execution time")
    deadline: Optional[datetime] = Field(None, description="Latest execution time")
    max_attempts: Optional[int] = Field(3, description="Maximum retry attempts")


class JobUpdate(BaseModel):
    """Schema for updating existing jobs"""
    status: Optional[JobStatus] = Field(None, description="Job status")
    priority: Optional[JobPriority] = Field(None, description="Job priority")
    not_before: Optional[datetime] = Field(None, description="Earliest execution time")
    deadline: Optional[datetime] = Field(None, description="Latest execution time")
    max_attempts: Optional[int] = Field(None, description="Maximum retry attempts")
    payload: Optional[Dict[str, Any]] = Field(None, description="Job-specific data")


class JobResponse(BaseModel):
    """Schema for job API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    platform: Platform
    type: JobType
    status: JobStatus
    priority: JobPriority
    payload: Dict[str, Any]
    scroll_type: Optional[str] = None
    scroll_count: Optional[int] = None
    not_before: Optional[datetime] = None
    deadline: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class JobStats(BaseModel):
    """Schema for job statistics"""
    total_jobs: int = 0
    pending_jobs: int = 0
    running_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    retrying_jobs: int = 0
    
    # Platform breakdown
    instagram_jobs: int = 0
    threads_jobs: int = 0
    
    # Job type breakdown
    follow_jobs: int = 0
    like_jobs: int = 0
    comment_jobs: int = 0
    post_jobs: int = 0
    warmup_jobs: int = 0
    
    # Platform-specific metrics
    instagram_success_rate: float = 0.0
    threads_success_rate: float = 0.0
    
    # Performance metrics
    success_rate: float = 0.0
    avg_execution_time: Optional[float] = None
    jobs_per_hour: float = 0.0


class JobListResponse(BaseModel):
    """Schema for paginated job list responses"""
    items: List[JobResponse]
    total: int
    page: int
    size: int
    pages: int


class JobExecutionResult(BaseModel):
    """Schema for job execution results"""
    job_id: int
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float
    timestamp: datetime


class JobQueueInfo(BaseModel):
    """Schema for job queue information"""
    queue_name: str
    pending_jobs: int
    running_jobs: int
    workers_active: int
    workers_total: int
    avg_wait_time: Optional[float] = None
    throughput_per_hour: float = 0.0


class BulkJobCreate(BaseModel):
    """Schema for creating multiple jobs at once"""
    jobs: List[JobCreate] = Field(..., min_items=1, max_items=100)
    batch_name: Optional[str] = Field(None, description="Optional batch identifier")


class BulkJobResponse(BaseModel):
    """Schema for bulk job creation response"""
    created_count: int
    failed_count: int
    created_jobs: List[JobResponse]
    errors: List[Dict[str, Any]]
    batch_id: Optional[str] = None
