"""
Schedule Configuration API Routes

Handles automation schedule management for Instagram & Threads platforms
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional
import structlog

from ..database.connection import get_db
from ..models.schedule import Schedule
from ..models.account import Account
from ..models.device import Device
from ..schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse,
    ScheduleStats, BulkScheduleCreate, BulkScheduleResponse, Platform,
    ScheduleType, ScheduleStatus
)

router = APIRouter()
logger = structlog.get_logger()


@router.get("/schedules/stats", response_model=ScheduleStats)
async def get_schedule_statistics(db: AsyncSession = Depends(get_db)):
    """Get schedule statistics with platform breakdown"""
    try:
        stats = ScheduleStats()
        
        # Status counts
        status_counts = await db.execute(
            select(Schedule.status, func.count(Schedule.id))
            .group_by(Schedule.status)
        )
        
        for status, count in status_counts.fetchall():
            if status == "active":
                stats.active_schedules = count
            elif status == "paused":
                stats.paused_schedules = count
            elif status == "completed":
                stats.completed_schedules = count
            elif status == "disabled":
                stats.disabled_schedules = count
                
            stats.total_schedules += count
        
        # Platform counts
        platform_counts = await db.execute(
            select(Schedule.platform, func.count(Schedule.id))
            .group_by(Schedule.platform)
        )
        
        for platform, count in platform_counts.fetchall():
            if platform == "instagram":
                stats.instagram_schedules = count
            elif platform == "threads":
                stats.threads_schedules = count
            elif platform == "both":
                stats.dual_platform_schedules = count
        
        logger.info("Schedule statistics retrieved successfully")
        return stats
        
    except Exception as e:
        logger.error("Failed to retrieve schedule statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve schedule statistics")


@router.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(
    platform: Optional[Platform] = Query(None, description="Filter by platform"),
    type: Optional[ScheduleType] = Query(None, description="Filter by schedule type"),
    status: Optional[ScheduleStatus] = Query(None, description="Filter by status"),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    skip: int = Query(0, ge=0, description="Number of schedules to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of schedules to return"),
    db: AsyncSession = Depends(get_db)
):
    """List schedules with filtering and pagination"""
    try:
        # Build query with filters
        query = select(Schedule)
        conditions = []
        
        if platform:
            conditions.append(Schedule.platform == platform.value)
        
        if type:
            conditions.append(Schedule.type == type.value)
            
        if status:
            conditions.append(Schedule.status == status.value)
            
        if account_id:
            conditions.append(Schedule.account_id == account_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(Schedule.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Schedule.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        schedules = result.scalars().all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        
        logger.info("Schedules listed successfully", total=total, returned=len(schedules))
        
        return ScheduleListResponse(
            items=schedules,
            total=total,
            page=(skip // limit) + 1,
            size=len(schedules),
            pages=pages
        )
        
    except Exception as e:
        logger.error("Failed to list schedules", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve schedules")


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Get schedule by ID"""
    try:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        logger.info("Schedule retrieved successfully", schedule_id=schedule_id)
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve schedule", schedule_id=schedule_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve schedule")


@router.post("/schedules", response_model=ScheduleResponse, status_code=201)
async def create_schedule(schedule_data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    """Create new schedule"""
    try:
        # Validate account exists (if specified)
        if schedule_data.account_id:
            account_result = await db.execute(
                select(Account).where(Account.id == schedule_data.account_id)
            )
            if not account_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Account not found")
        
        # Validate device exists (if specified)
        if schedule_data.device_id:
            device_result = await db.execute(
                select(Device).where(Device.id == schedule_data.device_id)
            )
            if not device_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Device not found")
        
        # Create schedule
        db_schedule = Schedule(**schedule_data.model_dump())
        db.add(db_schedule)
        await db.commit()
        await db.refresh(db_schedule)
        
        logger.info("Schedule created successfully", 
                   schedule_id=db_schedule.id, name=db_schedule.name, platform=db_schedule.platform)
        return db_schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create schedule", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create schedule")


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int, 
    schedule_data: ScheduleUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update existing schedule"""
    try:
        # Get existing schedule
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Update fields
        update_data = schedule_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        await db.commit()
        await db.refresh(schedule)
        
        logger.info("Schedule updated successfully", schedule_id=schedule_id)
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update schedule", schedule_id=schedule_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update schedule")


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Delete schedule"""
    try:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        await db.delete(schedule)
        await db.commit()
        
        logger.info("Schedule deleted successfully", schedule_id=schedule_id)
        return {"message": "Schedule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete schedule", schedule_id=schedule_id, error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete schedule")


@router.post("/schedules/bulk", response_model=BulkScheduleResponse, status_code=201)
async def create_bulk_schedules(bulk_data: BulkScheduleCreate, db: AsyncSession = Depends(get_db)):
    """Create multiple schedules in bulk"""
    try:
        created_schedules = []
        failed_schedules = []
        
        for i, schedule_data in enumerate(bulk_data.schedules):
            try:
                # Create schedule
                db_schedule = Schedule(**schedule_data.model_dump())
                db.add(db_schedule)
                await db.flush()  # Get ID without committing
                await db.refresh(db_schedule)
                created_schedules.append(db_schedule)
                
            except Exception as e:
                failed_schedules.append({
                    "index": i,
                    "schedule": schedule_data.model_dump(),
                    "error": str(e)
                })
        
        await db.commit()
        
        logger.info("Bulk schedule creation completed", 
                   created=len(created_schedules), failed=len(failed_schedules))
        
        return BulkScheduleResponse(
            created_count=len(created_schedules),
            failed_count=len(failed_schedules),
            created_schedules=created_schedules,
            failed_schedules=failed_schedules,
            batch_name=bulk_data.batch_name
        )
        
    except Exception as e:
        logger.error("Failed to create bulk schedules", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create bulk schedules")
