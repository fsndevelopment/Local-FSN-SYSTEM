"""
Model Schemas

Pydantic models for user model/profile management
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ModelBase(BaseModel):
    name: str = Field(..., description="Model name")
    profile_photo: Optional[str] = Field(None, description="Profile photo URL or path")

class ModelCreate(ModelBase):
    """Schema for creating a new model"""
    pass

class ModelUpdate(BaseModel):
    """Schema for updating a model"""
    name: Optional[str] = None
    profile_photo: Optional[str] = None

class ModelResponse(ModelBase):
    """Schema for model response"""
    id: str
    license_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ModelListResponse(BaseModel):
    """Schema for model list response"""
    items: list[ModelResponse]
    total: int
    skip: int
    limit: int
