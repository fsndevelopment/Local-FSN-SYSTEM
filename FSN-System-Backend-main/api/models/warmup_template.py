"""
Database models for warmup templates
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean
from sqlalchemy.sql import func
from database.connection import Base


class WarmupTemplate(Base):
    """Warmup template for daily automation without posting"""
    
    __tablename__ = "warmup_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # instagram, threads
    name = Column(String(100), nullable=False)
    
    # Multi-day configuration
    total_days = Column(Integer, default=1)  # Number of days/phases
    days_config = Column(JSON, nullable=False)  # Configuration for each day
    
    # Warmup activities (no posting)
    scroll_minutes_per_day = Column(Integer, default=0)
    likes_per_day = Column(Integer, default=0)
    follows_per_day = Column(Integer, default=0)
    
    # Cooldown settings
    posting_interval_minutes = Column(Integer, default=30)  # Minutes between warmup sessions
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<WarmupTemplate(id={self.id}, name='{self.name}', platform='{self.platform}', days={self.total_days})>"


class WarmupDayConfig(Base):
    """Individual day configuration for warmup templates"""
    
    __tablename__ = "warmup_day_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    warmup_template_id = Column(Integer, nullable=False, index=True)
    day_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    
    # Day-specific settings
    scroll_minutes = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    follows_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<WarmupDayConfig(day={self.day_number}, scroll={self.scroll_minutes}min, likes={self.likes_count}, follows={self.follows_count})>"
