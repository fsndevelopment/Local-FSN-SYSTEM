"""
Template models for posting and warmup templates
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from database.connection import Base

class PostingTemplate(Base):
    """Posting template for daily automation"""
    
    __tablename__ = "templates_posting"
    
    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # instagram, threads
    name = Column(String(100), nullable=False)
    photos_per_day = Column(Integer, default=0)
    text_posts_per_day = Column(Integer, default=0)
    follows_per_day = Column(Integer, default=0)
    likes_per_day = Column(Integer, default=0)
    captions_file_url = Column(String(500), nullable=True)
    photos_folder_url = Column(String(500), nullable=True)
    scrolling_minutes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PostingTemplate(id={self.id}, name='{self.name}', platform='{self.platform}')>"

class WarmupTemplate(Base):
    """Warmup template for gradual account growth"""
    
    __tablename__ = "templates_warmup"
    
    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # instagram, threads
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    days_json = Column(JSON, nullable=False)  # Array of day objects
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<WarmupTemplate(id={self.id}, name='{self.name}', platform='{self.platform}')>"

class Run(Base):
    """Run execution tracking"""
    
    __tablename__ = "runs"
    
    run_id = Column(String(36), primary_key=True)  # UUID
    license_id = Column(String(100), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    type = Column(String(20), nullable=False)  # posting, warmup
    template_id = Column(Integer, ForeignKey("templates_posting.id"), nullable=True)
    warmup_id = Column(Integer, ForeignKey("templates_warmup.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="queued")  # queued, running, paused, stopped, success, error
    progress_pct = Column(Integer, default=0)
    current_step = Column(String(200), nullable=True)
    last_action = Column(String(200), nullable=True)
    error_text = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Run(run_id='{self.run_id}', type='{self.type}', status='{self.status}')>"

class RunLog(Base):
    """Run execution logs"""
    
    __tablename__ = "run_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(36), ForeignKey("runs.run_id"), nullable=False)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    level = Column(String(10), nullable=False)  # info, warn, error
    message = Column(Text, nullable=False)
    payload_json = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<RunLog(id={self.id}, run_id='{self.run_id}', level='{self.level}')>"