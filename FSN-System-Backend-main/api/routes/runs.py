"""
Run execution routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import structlog

from database.connection import get_db
from models.template import PostingTemplate, WarmupTemplate, Run
from schemas.run import (
    PostingRunRequest, WarmupRunRequest, RunResponse, RunStatusResponse
)
from services.run_executor import run_executor

router = APIRouter(prefix="/api/runs", tags=["runs"])
logger = structlog.get_logger()

@router.post("/posting", response_model=RunResponse)
async def start_posting_run(
    request: PostingRunRequest,
    db: AsyncSession = Depends(get_db)
):
    """Start a posting run"""
    try:
        # Validate template exists
        template_result = await db.execute(
            select(PostingTemplate).where(PostingTemplate.id == request.template_id)
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Posting template not found"
            )
        
        # Validate device exists and is online
        from models.device import Device
        device_result = await db.execute(
            select(Device).where(Device.id == request.device_id)
        )
        device = device_result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=404,
                detail="Device not found"
            )
        
        if not device.is_online:
            raise HTTPException(
                status_code=503,
                detail="Device is offline"
            )
        
        # Start the run
        run_id = await run_executor.start_posting_run(
            license_id=request.license_id,
            device_id=request.device_id,
            template_id=request.template_id,
            account_id=request.account_id
        )
        
        logger.info("✅ Started posting run", run_id=run_id, template_id=request.template_id)
        
        return RunResponse(run_id=run_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to start posting run", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to start posting run"
        )

@router.post("/warmup", response_model=RunResponse)
async def start_warmup_run(
    request: WarmupRunRequest,
    db: AsyncSession = Depends(get_db)
):
    """Start a warmup run"""
    try:
        # Validate template exists
        template_result = await db.execute(
            select(WarmupTemplate).where(WarmupTemplate.id == request.warmup_id)
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Warmup template not found"
            )
        
        # Validate device exists and is online
        from models.device import Device
        device_result = await db.execute(
            select(Device).where(Device.id == request.device_id)
        )
        device = device_result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=404,
                detail="Device not found"
            )
        
        if not device.is_online:
            raise HTTPException(
                status_code=503,
                detail="Device is offline"
            )
        
        # Start the run
        run_id = await run_executor.start_warmup_run(
            license_id=request.license_id,
            device_id=request.device_id,
            warmup_id=request.warmup_id,
            account_id=request.account_id
        )
        
        logger.info("✅ Started warmup run", run_id=run_id, warmup_id=request.warmup_id)
        
        return RunResponse(run_id=run_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to start warmup run", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to start warmup run"
        )

@router.get("/{run_id}", response_model=RunStatusResponse)
async def get_run_status(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get run status"""
    try:
        status = await run_executor.get_run_status(run_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail="Run not found"
            )
        
        return RunStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get run status", error=str(e), run_id=run_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to get run status"
        )

@router.post("/{run_id}/stop")
async def stop_run(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Stop a running run"""
    try:
        success = await run_executor.stop_run(run_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Run not found or not running"
            )
        
        logger.info("✅ Stopped run", run_id=run_id)
        return {"message": "Run stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to stop run", error=str(e), run_id=run_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to stop run"
        )
