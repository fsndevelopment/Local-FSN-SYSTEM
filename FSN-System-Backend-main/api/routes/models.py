"""
Model Management Routes

CRUD operations for user models/profiles tied to licenses
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime

from database.connection import get_db
from middleware.license_middleware import require_valid_license
from schemas.model import (
    ModelCreate, ModelUpdate, ModelResponse, ModelListResponse
)
from models.account import Model

logger = structlog.get_logger()
router = APIRouter()

# Model class is now imported from models.account

@router.get("/models", response_model=ModelListResponse)
async def get_models(
    skip: int = Query(0, ge=0, description="Number of models to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of models to return"),
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
) -> ModelListResponse:
    """Get all models for the license"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔍 Getting models for license_key: {license_key}")
        
        # Debug: Check all models in database regardless of license
        all_models_query = select(Model)
        all_result = await db.execute(all_models_query)
        all_models = all_result.scalars().all()
        logger.info(f"🔍 DEBUG: Total models in database: {len(all_models)}")
        for model in all_models:
            logger.info(f"🔍 DEBUG: Model '{model.name}' - License: '{model.license_key}' - ID: {model.id}")
        
        # Get total count
        count_query = select(func.count(Model.id)).where(Model.license_key == license_key)
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        logger.info(f"📊 Total models found for license '{license_key}': {total}")
        
        # Get models for this license
        query = (
            select(Model)
            .where(Model.license_key == license_key)
            .order_by(Model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        models = result.scalars().all()
        logger.info(f"📋 Retrieved {len(models)} models from database")
        
        # Convert to response format
        model_responses = []
        for model in models:
            model_responses.append({
                "id": str(model.id),
                "name": model.name,
                "profile_photo": model.profile_photo,
                "license_key": model.license_key,
                "created_at": model.created_at,
                "updated_at": model.updated_at
            })
        
        logger.info(f"✅ Successfully returning {len(model_responses)} models")
        
        # Force the response format to match ModelListResponse
        response_data = {
            "items": model_responses,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
        logger.info(f"🔍 DEBUG: Response data structure: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Failed to get models for license {license_key}", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve models: {str(e)}")

@router.post("/models", response_model=ModelResponse, status_code=201)
async def create_model(
    model_data: ModelCreate,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Create a new model for the license"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔧 Creating model '{model_data.name}' for license_key: {license_key}")
        
        # Create new model instance
        new_model = Model(
            name=model_data.name,
            profile_photo=model_data.profile_photo,
            license_key=license_key
        )
        
        # Add to database
        db.add(new_model)
        await db.commit()
        await db.refresh(new_model)
        
        logger.info(f"✅ Successfully created model with ID: {new_model.id}")
        
        # Return the created model
        return {
            "id": str(new_model.id),
            "name": new_model.name,
            "profile_photo": new_model.profile_photo,
            "license_key": new_model.license_key,
            "created_at": new_model.created_at,
            "updated_at": new_model.updated_at
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create model '{model_data.name}' for license {license_key}", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create model: {str(e)}")

@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific model by ID"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔍 Getting model {model_id} for license_key: {license_key}")
        
        # Convert string ID to integer
        try:
            model_id_int = int(model_id)
        except ValueError:
            logger.error(f"❌ Invalid model ID format: {model_id}")
            raise HTTPException(status_code=400, detail="Invalid model ID format")
        
        # Find the model by ID and license key
        query = select(Model).where(
            and_(
                Model.id == model_id_int,
                Model.license_key == license_key
            )
        )
        
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            logger.warning(f"⚠️ Model {model_id} not found for license {license_key}")
            raise HTTPException(status_code=404, detail="Model not found")
        
        logger.info(f"✅ Found model {model_id} ('{model.name}')")
        
        # Return the model
        return {
            "id": str(model.id),
            "name": model.name,
            "profile_photo": model.profile_photo,
            "license_key": model.license_key,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get model {model_id}", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve model")

@router.put("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    model_data: ModelUpdate,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Update a model"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"✏️ Updating model {model_id} for license_key: {license_key}")
        
        # Convert string ID to integer
        try:
            model_id_int = int(model_id)
        except ValueError:
            logger.error(f"❌ Invalid model ID format: {model_id}")
            raise HTTPException(status_code=400, detail="Invalid model ID format")
        
        # Find the model by ID and license key
        query = select(Model).where(
            and_(
                Model.id == model_id_int,
                Model.license_key == license_key
            )
        )
        
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            logger.warning(f"⚠️ Model {model_id} not found for license {license_key}")
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Update the model fields
        update_data = model_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)
        
        model.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(model)
        
        logger.info(f"✅ Successfully updated model {model_id} ('{model.name}')")
        
        # Return the updated model
        return {
            "id": str(model.id),
            "name": model.name,
            "profile_photo": model.profile_photo,
            "license_key": model.license_key,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update model {model_id}", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update model: {str(e)}")

@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Delete a model"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🗑️ Deleting model {model_id} for license_key: {license_key}")
        
        # Convert string ID to integer
        try:
            model_id_int = int(model_id)
        except ValueError:
            logger.error(f"❌ Invalid model ID format: {model_id}")
            raise HTTPException(status_code=400, detail="Invalid model ID format")
        
        # Find the model by ID and license key
        query = select(Model).where(
            and_(
                Model.id == model_id_int,
                Model.license_key == license_key
            )
        )
        
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            logger.warning(f"⚠️ Model {model_id} not found for license {license_key}")
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Delete the model
        await db.delete(model)
        await db.commit()
        
        logger.info(f"✅ Successfully deleted model {model_id} ('{model.name}')")
        
        return {"message": f"Model '{model.name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete model {model_id}", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")
