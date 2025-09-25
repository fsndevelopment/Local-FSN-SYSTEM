"""
API router for warmup templates
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from database.connection import get_db
from api.models.warmup_template import WarmupTemplate, WarmupDayConfig
from api.schemas.warmup_template import (
    WarmupTemplateCreate,
    WarmupTemplateUpdate,
    WarmupTemplateResponse,
    WarmupTemplateList
)

router = APIRouter(prefix="/api/v1/warmup-templates", tags=["warmup-templates"])

# Mock license key for now - replace with proper auth
CURRENT_LICENSE_KEY = "dev"

@router.get("/", response_model=WarmupTemplateList)
async def get_warmup_templates(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    platform: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of warmup templates"""
    try:
        # Build query
        query = select(WarmupTemplate).where(WarmupTemplate.license_id == CURRENT_LICENSE_KEY)
        
        if platform:
            query = query.where(WarmupTemplate.platform == platform)
        
        # Get total count
        count_query = select(WarmupTemplate.id).where(WarmupTemplate.license_id == CURRENT_LICENSE_KEY)
        if platform:
            count_query = count_query.where(WarmupTemplate.platform == platform)
        
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(WarmupTemplate.created_at.desc())
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return WarmupTemplateList(
            templates=[WarmupTemplateResponse.from_orm(template) for template in templates],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching warmup templates: {str(e)}")

@router.post("/", response_model=WarmupTemplateResponse)
async def create_warmup_template(
    template_data: WarmupTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new warmup template"""
    try:
        # Create warmup template
        warmup_template = WarmupTemplate(
            license_id=CURRENT_LICENSE_KEY,
            platform=template_data.platform,
            name=template_data.name,
            total_days=template_data.total_days,
            days_config=template_data.days_config,
            scroll_minutes_per_day=template_data.scroll_minutes_per_day,
            likes_per_day=template_data.likes_per_day,
            follows_per_day=template_data.follows_per_day,
            posting_interval_minutes=template_data.posting_interval_minutes
        )
        
        db.add(warmup_template)
        await db.commit()
        await db.refresh(warmup_template)
        
        return WarmupTemplateResponse.from_orm(warmup_template)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating warmup template: {str(e)}")

@router.get("/{template_id}", response_model=WarmupTemplateResponse)
async def get_warmup_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific warmup template"""
    try:
        query = select(WarmupTemplate).where(
            WarmupTemplate.id == template_id,
            WarmupTemplate.license_id == CURRENT_LICENSE_KEY
        )
        
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Warmup template not found")
        
        return WarmupTemplateResponse.from_orm(template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching warmup template: {str(e)}")

@router.put("/{template_id}", response_model=WarmupTemplateResponse)
async def update_warmup_template(
    template_id: int,
    template_data: WarmupTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a warmup template"""
    try:
        # Check if template exists
        query = select(WarmupTemplate).where(
            WarmupTemplate.id == template_id,
            WarmupTemplate.license_id == CURRENT_LICENSE_KEY
        )
        
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Warmup template not found")
        
        # Update fields
        update_data = template_data.dict(exclude_unset=True)
        
        if update_data:
            query = update(WarmupTemplate).where(
                WarmupTemplate.id == template_id,
                WarmupTemplate.license_id == CURRENT_LICENSE_KEY
            ).values(**update_data)
            
            await db.execute(query)
            await db.commit()
            
            # Fetch updated template
            query = select(WarmupTemplate).where(WarmupTemplate.id == template_id)
            result = await db.execute(query)
            updated_template = result.scalar_one()
            
            return WarmupTemplateResponse.from_orm(updated_template)
        
        return WarmupTemplateResponse.from_orm(template)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating warmup template: {str(e)}")

@router.delete("/{template_id}")
async def delete_warmup_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a warmup template"""
    try:
        # Check if template exists
        query = select(WarmupTemplate).where(
            WarmupTemplate.id == template_id,
            WarmupTemplate.license_id == CURRENT_LICENSE_KEY
        )
        
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Warmup template not found")
        
        # Delete template (cascade will handle day configs)
        query = delete(WarmupTemplate).where(
            WarmupTemplate.id == template_id,
            WarmupTemplate.license_id == CURRENT_LICENSE_KEY
        )
        
        await db.execute(query)
        await db.commit()
        
        return {"message": "Warmup template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting warmup template: {str(e)}")
