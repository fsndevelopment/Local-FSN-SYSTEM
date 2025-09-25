"""
Warmup Templates Management Routes

CRUD operations for warmup templates tied to licenses
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List, Dict, Any
from datetime import datetime

from database.connection import get_db
from middleware.license_middleware import require_valid_license
from schemas.warmup_template import (
    WarmupTemplateCreate,
    WarmupTemplateUpdate,
)
from models.template import WarmupTemplate

logger = structlog.get_logger()
router = APIRouter()

@router.get("/warmup-templates")
async def get_warmup_templates(
    skip: int = Query(0, ge=0, description="Number of warmup templates to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of warmup templates to return"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    phase: Optional[str] = Query(None, description="Filter by warmup phase"),
    search: Optional[str] = Query(None, description="Search by name"),
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Get all warmup templates for the license"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔍 Getting warmup templates for license_key: {license_key}")
        
        # Build query with license filtering
        conditions = [WarmupTemplate.license_id == license_key]
        
        if platform:
            conditions.append(WarmupTemplate.platform == platform)
        if phase:
            conditions.append(WarmupTemplate.phase == phase)
        
        query = select(WarmupTemplate).where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(WarmupTemplate.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(WarmupTemplate.created_at.desc())
        result = await db.execute(query)
        warmup_templates = result.scalars().all()
        
        pages = (total + limit - 1) // limit if total > 0 else 0
        
        logger.info(f"Retrieved warmup templates: total={total}, returned={len(warmup_templates)}, page={skip//limit + 1}")

        # Shape response as a plain dict to avoid mismatched schema issues
        items = []
        for t in warmup_templates:
            items.append({
                "id": t.id,
                "name": t.name,
                "platform": t.platform,
                "description": getattr(t, "description", None),
                "days_config": t.days_json or [],
                "license_id": t.license_id,
                "created_at": t.created_at,
                "updated_at": t.created_at,
                "is_active": True,
            })

        return {
            "items": items,
            "total": int(total or 0),
            "skip": skip,
            "limit": limit,
            "pages": pages,
        }
        
    except Exception as e:
        logger.error("Failed to get warmup templates", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve warmup templates")

@router.get("/warmup-templates/{template_id}")
async def get_warmup_template(
    template_id: int,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific warmup template by ID"""
    try:
        # For now, return 404 since we don't have the model implemented
        raise HTTPException(status_code=404, detail="Warmup template not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get warmup template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve warmup template")

@router.post("/warmup-templates")
async def create_warmup_template(
    template_data: WarmupTemplateCreate,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Create a new warmup template"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔧 Creating warmup template '{template_data.name}' for license_key: {license_key}")
        
        # Map schema to DB model
        db_template = WarmupTemplate(
            license_id=license_key,
            platform=template_data.platform,
            name=template_data.name,
            description=None,
            days_json=[
                {
                    "day_number": d.day_number,
                    "scroll_minutes": d.scroll_minutes,
                    "likes_count": d.likes_count,
                    "follows_count": d.follows_count,
                }
                for d in template_data.days_config
            ],
        )
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        
        logger.info(f"✅ Successfully created warmup template with ID: {db_template.id}")
        
        # Shape response body
        return {
            "id": db_template.id,
            "name": db_template.name,
            "platform": db_template.platform,
            "description": db_template.description,
            "days_config": db_template.days_json,
            "license_id": db_template.license_id,
            "created_at": db_template.created_at,
            "updated_at": db_template.created_at,
            "is_active": True,
        }
        
    except Exception as e:
        logger.error("Failed to create warmup template", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create warmup template")

@router.put("/warmup-templates/{template_id}")
async def update_warmup_template(
    template_id: int,
    template_data: WarmupTemplateUpdate,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing warmup template"""
    try:
        # For now, return 501 since we don't have the model implemented
        raise HTTPException(status_code=501, detail="Warmup template update not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update warmup template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update warmup template")

@router.delete("/warmup-templates/{template_id}")
async def delete_warmup_template(
    template_id: int,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Delete a warmup template"""
    try:
        # For now, return 501 since we don't have the model implemented
        raise HTTPException(status_code=501, detail="Warmup template deletion not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete warmup template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete warmup template")

@router.post("/warmup-templates/{template_id}/duplicate", response_model=TemplateResponse)
async def duplicate_warmup_template(
    template_id: int,
    new_name: str,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate a warmup template"""
    try:
        # For now, return 501 since we don't have the model implemented
        raise HTTPException(status_code=501, detail="Warmup template duplication not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to duplicate warmup template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to duplicate warmup template")

@router.post("/warmup-templates/{template_id}/execute")
async def execute_warmup_template(
    template_id: int,
    account_ids: List[int],
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Execute a warmup template"""
    try:
        # For now, return 501 since we don't have the model implemented
        raise HTTPException(status_code=501, detail="Warmup template execution not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute warmup template", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to execute warmup template")
