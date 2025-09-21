"""
Content models for managing posts, assets, and content queue
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base
from typing import Optional, Dict, Any
from datetime import datetime


class ContentAsset(Base):
    """Content asset (video, image, etc.)"""
    
    __tablename__ = "content_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File Information
    filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)  # Storage path
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    
    # Media Properties
    duration = Column(Float, nullable=True)  # For videos, in seconds
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # Content Organization
    variant_of = Column(Integer, ForeignKey("content_assets.id"), nullable=True)  # Original asset if this is a variant
    tags = Column(JSON, nullable=True)  # Array of tags
    
    # Status
    status = Column(String(20), default="ready")  # ready, processing, failed
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    variants = relationship("ContentAsset", remote_side=[id])
    posts = relationship("Post", back_populates="asset")
    
    def __repr__(self):
        return f"<ContentAsset(filename='{self.filename}', status='{self.status}')>"


class Post(Base):
    """Posted content tracking"""
    
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("content_assets.id"), nullable=True)
    
    # Post Content
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)  # Array of hashtags
    
    # Post Details
    post_type = Column(String(20), nullable=False)  # reel, story, feed
    ig_id = Column(String(100), nullable=True)  # Instagram post ID
    
    # Performance Metrics (updated by SCAN_PROFILE jobs)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    
    # Timing
    posted_at = Column(DateTime(timezone=True), server_default=func.now())
    last_scraped = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # account = relationship("Account", back_populates="posts")  # Temporarily disabled
    asset = relationship("ContentAsset", back_populates="posts")
    
    def __repr__(self):
        return f"<Post(post_type='{self.post_type}', views={self.views}, account_id={self.account_id})>"


class ContentQueue(Base):
    """Content queue for scheduled posts"""
    
    __tablename__ = "content_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("content_assets.id"), nullable=False)
    
    # Content Details
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)
    post_type = Column(String(20), nullable=False)  # reel, story, feed
    
    # Scheduling
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    priority = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), default="queued")  # queued, processing, posted, failed
    
    # Job Reference
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    account = relationship("Account")
    asset = relationship("ContentAsset")
    job = relationship("Job")
    
    def __repr__(self):
        return f"<ContentQueue(post_type='{self.post_type}', status='{self.status}', account_id={self.account_id})>"
