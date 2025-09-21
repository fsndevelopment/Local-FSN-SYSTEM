"""
Job models for automation task queue management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base
from typing import Optional, Dict, Any
from datetime import datetime
import enum


class JobType(str, enum.Enum):
    """Supported job types - aligned with schemas/job.py"""
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
    SCAN_PROFILE = "SCAN_PROFILE"
    SCROLL_HOME_FEED = "SCROLL_HOME_FEED"
    LIKE_POST = "LIKE_POST"
    LIKE = "LIKE"  # Legacy alias for LIKE_POST
    VIEW_STORY = "VIEW_STORY"
    COMMENT_POST = "COMMENT_POST"
    FOLLOW_USER = "FOLLOW_USER"
    UNFOLLOW_USER = "UNFOLLOW_USER"
    POST_PICTURE = "POST_PICTURE"
    SEARCH_HASHTAG = "SEARCH_HASHTAG"
    SAVE_POST = "SAVE_POST"
    LIKE_COMMENT = "LIKE_COMMENT"
    REPLY_STORY = "REPLY_STORY"
    POST_REEL = "POST_REEL"
    POST_STORY = "POST_STORY"
    SWITCH_PROXY = "SWITCH_PROXY"
    CHANGE_BIO = "CHANGE_BIO"
    SET_PFP = "SET_PFP"
    
    # Additional legacy aliases for compatibility
    LOGIN = "LOGIN"


class JobStatus(str, enum.Enum):
    """Job execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, enum.Enum):
    """Job priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Job(Base):
    """Automation job for Instagram & Threads actions"""
    
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)  # Optional device assignment
    
    # Platform Support
    platform = Column(String(20), nullable=False, default="instagram")  # instagram, threads
    
    # Job Configuration
    type = Column(String(50), nullable=False)  # JobType enum
    payload = Column(JSON, nullable=False)  # Job-specific data
    scroll_type = Column(String(20), nullable=True)  # For scrolling jobs: home_feed, reels, threads_feed
    scroll_count = Column(Integer, nullable=True)  # Number of scrolls to perform
    
    # Scheduling
    not_before = Column(DateTime(timezone=True), nullable=True)  # Earliest execution time
    deadline = Column(DateTime(timezone=True), nullable=True)   # Latest execution time
    priority = Column(String(20), default=JobPriority.NORMAL)
    
    # Execution
    status = Column(String(20), default=JobStatus.PENDING)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    result = Column(JSON, nullable=True)  # Execution result data
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # account = relationship("Account", back_populates="jobs")  # Temporarily disabled
    
    def __repr__(self):
        return f"<Job(type='{self.type}', status='{self.status}', account_id={self.account_id})>"
    
    @property
    def is_ready(self) -> bool:
        """Check if job is ready to execute"""
        if self.status != JobStatus.PENDING:
            return False
        
        if self.not_before and datetime.utcnow() < self.not_before:
            return False
            
        if self.deadline and datetime.utcnow() > self.deadline:
            return False
            
        return True
    
    @property
    def is_expired(self) -> bool:
        """Check if job has expired"""
        if self.deadline and datetime.utcnow() > self.deadline:
            return True
        return False


class Schedule(Base):
    """Automation schedule configuration"""
    
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "spread-12h", "eu-day"
    description = Column(Text, nullable=True)
    
    # Schedule Configuration
    window_json = Column(JSON, nullable=False)  # Time windows configuration
    mix_json = Column(JSON, nullable=False)     # Action mix percentages
    
    # Settings
    active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Schedule(name='{self.name}', active={self.active})>"
