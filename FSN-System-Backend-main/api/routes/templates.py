"""
PostingTemplate Management Routes

CRUD operations for automation templates tied to licenses
"""

import structlog
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List, Dict, Any
from datetime import datetime

from database.connection import get_db
from middleware.license_middleware import require_valid_license
from schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse,
    TemplateExecutionRequest, TemplateExecutionResponse
)
from services.concurrent_job_executor import concurrent_job_executor
from services.template_job_converter import template_job_converter
from services.appium_template_executor import appium_template_executor
from models.job import JobType, JobPriority, Job
from models.account import Account
from models.device import Device
from models.template import PostingTemplate, WarmupTemplate

logger = structlog.get_logger()
router = APIRouter()

@router.get("/templates", response_model=TemplateListResponse)
async def get_templates(
    skip: int = Query(0, ge=0, description="Number of templates to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of templates to return"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Get all templates for the license"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔍 Getting templates for license_key: {license_key}")
        
        # Build query with license filtering
        conditions = [PostingTemplate.license_key == license_key]
        
        if platform:
            conditions.append(PostingTemplate.platform == platform)
        
        query = select(PostingTemplate).where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(PostingTemplate.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(PostingTemplate.created_at.desc())
        result = await db.execute(query)
        templates = result.scalars().all()
        
        pages = (total + limit - 1) // limit if total > 0 else 0
        
        logger.info(f"Retrieved templates: total={total}, returned={len(templates)}, page={skip//limit + 1}")
        
        return TemplateListResponse(
            items=templates,
            total=total,
            skip=skip,
            limit=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error("Failed to get templates", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve templates")

@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    template_data: TemplateCreate,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Create a new template for the license"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔧 Creating template '{template_data.name}' for license_key: {license_key}")
        
        # Create template with license_key
        template_dict = template_data.model_dump()
        template_dict['license_key'] = license_key
        db_template = PostingTemplate(**template_dict)
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        
        logger.info(f"✅ Successfully created template with ID: {db_template.id}")
        
        return db_template
        
    except Exception as e:
        logger.error("Failed to create template", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create template")

@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific template by ID"""
    try:
        # For now, return a mock response
        # This will be implemented once we add the template model to the database
        raise HTTPException(status_code=404, detail="PostingTemplate not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get template", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve template")

@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Update a template"""
    try:
        # For now, return a mock response
        # This will be implemented once we add the template model to the database
        raise HTTPException(status_code=404, detail="PostingTemplate not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update template", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update template")

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Delete a template"""
    try:
        # For now, return a mock response
        # This will be implemented once we add the template model to the database
        raise HTTPException(status_code=404, detail="PostingTemplate not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete template", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete template")


@router.post("/templates/{template_id}/execute", response_model=TemplateExecutionResponse)
async def execute_template(
    template_id: str,
    request: TemplateExecutionRequest,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Execute a template by converting it to jobs and starting execution"""
    try:
        # Get the specific device
        device_result = await db.execute(
            select(Device).where(Device.id == request.device_id)
        )
        device = device_result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        if device.status not in ['active', 'connected']:
            raise HTTPException(status_code=400, detail="Device not available for execution")
        
        # Get the specific accounts
        accounts_result = await db.execute(
            select(Account).where(Account.id.in_(request.account_ids))
        )
        accounts = accounts_result.scalars().all()
        
        if not accounts:
            raise HTTPException(status_code=400, detail="No accounts found for the specified IDs")
        
        if len(accounts) != len(request.account_ids):
            raise HTTPException(status_code=400, detail="Some accounts not found")
        
        # Use actual template data from request - required for execution
        if hasattr(request, 'template_data') and request.template_data:
            template_data = request.template_data
            logger.info(f"Using template data from request: {template_data}")
        else:
            # No template data provided - cannot execute
            raise HTTPException(status_code=400, detail="Template data is required for execution")
        
        # Start Appium template execution
        execution_result = await appium_template_executor.execute_template(
            template_data, device, accounts
        )
        
        # Create jobs in database for tracking
        created_jobs = []
        if execution_result.get('success'):
            # Create a job record for tracking
            job = Job(
                type=JobType.INSTAGRAM_LIKE_POST.value,  # Default type
                priority=JobPriority.NORMAL.value,
                account_id=accounts[0].id if accounts else None,
                device_id=device.id,
                status="running",
                parameters=json.dumps(template_data),
                created_at=datetime.utcnow()
            )
            db.add(job)
            await db.commit()
            created_jobs.append(job)
            
            logger.info(f"Template {template_id} execution started", 
                       device_id=device.id,
                       accounts_count=len(accounts),
                       execution_result=execution_result.get('success'))
        else:
            logger.error(f"Template {template_id} execution failed", 
                       error=execution_result.get('error'))
        
        job_ids = [job.id for job in created_jobs] if created_jobs else []
        
        return TemplateExecutionResponse(
            success=True,
            template_id=template_id,
            device_id=request.device_id,
            jobs_created=len(created_jobs),
            automation_started=len(created_jobs) > 0,
            job_ids=job_ids,
            message=f"Template {template_id} execution started on device {request.device_id} with {len(accounts)} accounts"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to execute template")


@router.post("/templates/{template_id}/stop")
async def stop_template(
    template_id: str,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Stop execution of a template"""
    try:
        # TODO: Stop all jobs related to this template
        # This would involve:
        # 1. Finding all jobs created from this template
        # 2. Canceling/stopping those jobs
        # 3. Updating job status
        
        logger.info(f"PostingTemplate {template_id} stop requested")
        
        return {
            "success": True,
            "message": f"PostingTemplate {template_id} execution stopped",
            "template_id": template_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to stop template")
