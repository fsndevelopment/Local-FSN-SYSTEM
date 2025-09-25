"""
Template Schemas

Pydantic models for template management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TemplateBase(BaseModel):
    name: str = Field(..., description="Template name")
    platform: str = Field(..., description="Platform (instagram, threads, or both)")
    posts_per_day: int = Field(0, ge=0, description="Posts per day")
    likes_per_day: int = Field(0, ge=0, description="Likes per day")
    follows_per_day: int = Field(0, ge=0, description="Follows per day")
    stories_per_day: int = Field(0, ge=0, description="Stories per day")
    comments_per_day: int = Field(0, ge=0, description="Comments per day")
    photos_per_day: int = Field(0, ge=0, description="Photos per day")
    text_posts_per_day: int = Field(0, ge=0, description="Text posts per day")
    captions_per_day: int = Field(0, ge=0, description="Captions per day")
    reels_per_day: int = Field(0, ge=0, description="Reels per day")
    photos_folder: Optional[str] = Field(None, description="Photos folder path")
    text_posts_folder: Optional[str] = Field(None, description="Text posts folder path")
    captions_folder: Optional[str] = Field(None, description="Captions folder path")
    reels_folder: Optional[str] = Field(None, description="Reels folder path")
    stories_folder: Optional[str] = Field(None, description="Stories folder path")
    posting_interval_minutes: int = Field(30, ge=1, description="Minutes between posts")

class TemplateCreate(TemplateBase):
    """Schema for creating a new template"""
    pass

class TemplateUpdate(BaseModel):
    """Schema for updating a template"""
    name: Optional[str] = None
    platform: Optional[str] = None
    posts_per_day: Optional[int] = Field(None, ge=0)
    likes_per_day: Optional[int] = Field(None, ge=0)
    follows_per_day: Optional[int] = Field(None, ge=0)
    stories_per_day: Optional[int] = Field(None, ge=0)
    comments_per_day: Optional[int] = Field(None, ge=0)
    photos_per_day: Optional[int] = Field(None, ge=0)
    text_posts_per_day: Optional[int] = Field(None, ge=0)
    captions_per_day: Optional[int] = Field(None, ge=0)
    reels_per_day: Optional[int] = Field(None, ge=0)
    photos_folder: Optional[str] = None
    text_posts_folder: Optional[str] = None
    captions_folder: Optional[str] = None
    reels_folder: Optional[str] = None
    stories_folder: Optional[str] = None
    posting_interval_minutes: Optional[int] = Field(None, ge=1)

class TemplateResponse(TemplateBase):
    """Schema for template response"""
    id: str
    license_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TemplateListResponse(BaseModel):
    """Schema for template list response"""
    items: list[TemplateResponse]
    total: int
    skip: int
    limit: int

class TemplateExecutionRequest(BaseModel):
    """Schema for template execution request"""
    device_id: int = Field(..., description="Device ID to execute template on")
    account_ids: List[int] = Field(..., description="List of account IDs to use for execution")
    execution_mode: str = Field("normal", description="Execution mode: normal, safe, aggressive")
    start_delay: int = Field(0, ge=0, description="Delay in seconds before starting execution")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template data including xlsx file content")

class TemplateExecutionResponse(BaseModel):
    """Schema for template execution response"""
    success: bool
    template_id: str
    device_id: int
    jobs_created: int
    automation_started: bool
    job_ids: List[int]
    message: str
