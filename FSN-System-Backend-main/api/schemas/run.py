"""
Run execution schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PostingRunRequest(BaseModel):
    """Request to start a posting run"""
    license_id: str = Field(..., description="License ID")
    device_id: int = Field(..., description="Device ID to run on")
    template_id: int = Field(..., description="Posting template ID")
    account_id: Optional[int] = Field(None, description="Account ID to use")

class WarmupRunRequest(BaseModel):
    """Request to start a warmup run"""
    license_id: str = Field(..., description="License ID")
    device_id: int = Field(..., description="Device ID to run on")
    warmup_id: int = Field(..., description="Warmup template ID")
    account_id: Optional[int] = Field(None, description="Account ID to use")

class RunResponse(BaseModel):
    """Response for starting a run"""
    run_id: str = Field(..., description="Run ID")

class RunStatusResponse(BaseModel):
    """Response for run status"""
    run_id: str = Field(..., description="Run ID")
    status: str = Field(..., description="Run status")
    progress_pct: int = Field(..., description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current step")
    last_action: Optional[str] = Field(None, description="Last action")
    error_text: Optional[str] = Field(None, description="Error text if failed")
    started_at: Optional[datetime] = Field(None, description="Start time")
    finished_at: Optional[datetime] = Field(None, description="Finish time")
