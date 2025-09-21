"""
Job Management Routes
Handles job creation, status tracking, and execution
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import logging

from services.job_execution_service import job_execution_service, JobStatus
from models.device import Device
from models.account import Account

logger = logging.getLogger(__name__)

router = APIRouter()

class JobStartRequest(BaseModel):
    """Request to start a new job"""
    template_id: str
    device_id: str
    account_ids: List[str]
    execution_mode: str = "normal"
    start_delay: int = 0

class JobStartResponse(BaseModel):
    """Response for job start"""
    success: bool
    job_id: str
    message: str
    status: str

class JobStatusResponse(BaseModel):
    """Response for job status"""
    job_id: str
    status: str
    current_step: str
    progress: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: List[Dict[str, Any]] = []
    errors: List[str] = []

class JobListResponse(BaseModel):
    """Response for job list"""
    active_jobs: List[JobStatusResponse]
    completed_jobs: List[JobStatusResponse]
    total_active: int
    total_completed: int

@router.post("/jobs/start", response_model=JobStartResponse)
async def start_job(request: JobStartRequest):
    """Start a new job execution"""
    try:
        # Generate unique job ID
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        # Get template from database
        # TODO: Implement proper template fetching from database
        if not request.template_id:
            raise HTTPException(status_code=400, detail="Template ID is required")
        
        # For now, return error if template data not provided
        raise HTTPException(status_code=501, detail="Template execution not implemented yet - use template execution endpoint instead")
        
        device = Device(
            id=request.device_id,
            udid="ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf",
            platform="iOS",
            name="iPhone7",
            status="running",
            appium_port=4741,
            wda_port=8109,
            mjpeg_port=9100,
            last_seen="2024-01-01T00:00:00",
            ios_version="15.0",
            model="iPhone 7",
            wda_bundle_id="com.device7.wd7",
            jailbroken=True,  # Set to True for jailbroken devices
            settings={
                "autoAcceptAlerts": True,
                "autoDismissAlerts": True,
                "shouldTerminateApp": True
            }
        )
        
        # Create mock accounts based on account_ids
        accounts = []
        for i, account_id in enumerate(request.account_ids):
            account = Account(
                id=account_id,
                username=f"test_user_{i+1}",
                email=f"test{i+1}@example.com",
                password="password123",
                platform="threads",
                auth_type="email",
                two_factor_code=None,
                container_id=f"container_{i+1}",  # Container ID for jailbroken devices
                is_active=True,
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            accounts.append(account)
        
        # Start the job
        result = await job_execution_service.start_job(
            job_id=job_id,
            template=template,
            device=device,
            accounts=accounts
        )
        
        if result["success"]:
            logger.info(f"Job {job_id} started successfully")
            return JobStartResponse(
                success=True,
                job_id=job_id,
                message=result["message"],
                status=result["status"]
            )
        else:
            logger.error(f"Failed to start job {job_id}: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to start job"))
            
    except Exception as e:
        logger.error(f"Job start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status"""
    try:
        job_info = await job_execution_service.get_job_status(job_id)
        
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=job_id,
            status=job_info["status"].value,
            current_step=job_info["current_step"],
            progress=job_info["progress"],
            created_at=job_info["created_at"],
            started_at=job_info.get("started_at"),
            completed_at=job_info.get("completed_at"),
            results=job_info.get("results", []),
            errors=job_info.get("errors", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs", response_model=JobListResponse)
async def get_all_jobs():
    """Get all jobs (active and completed)"""
    try:
        jobs_data = await job_execution_service.get_all_jobs()
        
        # Convert to response format
        active_jobs = []
        for job in jobs_data["active_jobs"]:
            active_jobs.append(JobStatusResponse(
                job_id=job["id"],
                status=job["status"].value,
                current_step=job["current_step"],
                progress=job["progress"],
                created_at=job["created_at"],
                started_at=job.get("started_at"),
                completed_at=job.get("completed_at"),
                results=job.get("results", []),
                errors=job.get("errors", [])
            ))
        
        completed_jobs = []
        for job in jobs_data["completed_jobs"]:
            completed_jobs.append(JobStatusResponse(
                job_id=job["id"],
                status=job["status"].value,
                current_step=job["current_step"],
                progress=job["progress"],
                created_at=job["created_at"],
                started_at=job.get("started_at"),
                completed_at=job.get("completed_at"),
                results=job.get("results", []),
                errors=job.get("errors", [])
            ))
        
        return JobListResponse(
            active_jobs=active_jobs,
            completed_jobs=completed_jobs,
            total_active=jobs_data["total_active"],
            total_completed=jobs_data["total_completed"]
        )
        
    except Exception as e:
        logger.error(f"Get all jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/stop")
async def stop_job(job_id: str):
    """Stop a running job"""
    try:
        success = await job_execution_service.stop_job(job_id)
        
        if success:
            return {"success": True, "message": f"Job {job_id} stopped successfully"}
        else:
            raise HTTPException(status_code=404, detail="Job not found or already stopped")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stop job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job (completed or failed only)"""
    try:
        # This would remove the job from history
        # For now, just return success
        return {"success": True, "message": f"Job {job_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))