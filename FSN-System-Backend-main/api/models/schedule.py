"""
Schedule Database Models

SQLAlchemy models for schedule configuration
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Time, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.base import Base


class ScheduleStatus:
    """Schedule status constants"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DISABLED = "disabled"


class ScheduleType:
    """Schedule type constants"""
    WARMUP = "warmup"
    POSTING = "posting"
    ENGAGEMENT = "engagement"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"


class RepeatPattern:
    """Repeat pattern constants"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class Schedule(Base):
    """Schedule configuration for Instagram & Threads automation tasks"""
    
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Platform Support
    platform = Column(String(20), nullable=False, default="instagram")  # instagram, threads, both
    
    # Schedule Configuration
    type = Column(String(50), nullable=False)  # ScheduleType enum
    status = Column(String(20), default=ScheduleStatus.ACTIVE)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    
    # Timing Configuration
    start_time = Column(Time, nullable=False)  # Daily start time
    end_time = Column(Time, nullable=False)    # Daily end time
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Repeat Configuration
    repeat_pattern = Column(String(20), default=RepeatPattern.DAILY)
    repeat_interval = Column(Integer, default=1)
    weekdays = Column(JSON, nullable=True)  # Array of weekday numbers
    
    # Action Configuration
    actions_per_hour = Column(Integer, default=10)
    max_daily_actions = Column(Integer, default=100)
    
    # Advanced Configuration
    priority = Column(Integer, default=5)  # 1-10 priority scale
    enabled = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)  # Schedule-specific settings
    
    # Execution Tracking
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    last_execution = Column(DateTime(timezone=True), nullable=True)
    next_execution = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # account = relationship("Account", back_populates="schedules")
    # device = relationship("Device", back_populates="schedules")
    
    def __repr__(self):
        return f"<Schedule(name='{self.name}', platform='{self.platform}', type='{self.type}')>"


class ScheduleExecution(Base):
    """Schedule execution tracking"""
    
    __tablename__ = "schedule_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    
    # Execution Details
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="running")  # running, completed, failed, cancelled
    
    # Action Tracking
    actions_executed = Column(Integer, default=0)
    actions_successful = Column(Integer, default=0)
    actions_failed = Column(Integer, default=0)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    schedule = relationship("Schedule", backref="executions")
    # account = relationship("Account")
    # device = relationship("Device")
    
    def __repr__(self):
        return f"<ScheduleExecution(schedule_id={self.schedule_id}, status='{self.status}')>"
