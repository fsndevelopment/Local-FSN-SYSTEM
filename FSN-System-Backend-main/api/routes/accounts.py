"""
Account Management Routes

Complete CRUD operations for Instagram account management
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List

from database.connection import get_db
from middleware.license_middleware import require_valid_license
from models.account import Account, Model
from models.device import Device
from schemas.account import (
    AccountCreate, AccountUpdate, AccountResponse, AccountStats,
    AccountListResponse, ModelProfileResponse, AccountStatus, WarmupPhase
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("/accounts", response_model=AccountListResponse)
async def get_accounts(
    skip: int = Query(0, ge=0, description="Number of accounts to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of accounts to return"),
    status: Optional[AccountStatus] = Query(None, description="Filter by account status"),
    warmup_phase: Optional[WarmupPhase] = Query(None, description="Filter by warmup phase"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    search: Optional[str] = Query(None, description="Search by username"),
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of accounts with filtering"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔍 Getting accounts for license_key: {license_key}")
        
        # Build base query with license filtering (removed eager loading to avoid foreign key issues)
        conditions = [Account.license_key == license_key]  # Always filter by license_key
        
        query = select(Account)
        
        # Apply additional filters
        if status:
            conditions.append(Account.status == status)
        if warmup_phase:
            conditions.append(Account.warmup_phase == warmup_phase)
        if device_id:
            conditions.append(Account.device_id == device_id)
        if search:
            conditions.append(Account.username.ilike(f"%{search}%"))
        
        query = query.where(and_(*conditions))
        
        # Get total count with license filtering
        count_query = select(func.count(Account.id)).where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Account.created_at.desc())
        result = await db.execute(query)
        accounts = result.scalars().all()
        
        pages = (total + limit - 1) // limit if total > 0 else 0
        
        logger.info("Retrieved accounts", total=total, returned=len(accounts), page=skip//limit + 1)
        
        return AccountListResponse(
            items=accounts,
            total=total,
            page=skip // limit + 1,
            size=len(accounts),
            pages=pages
        )
        
    except Exception as e:
        logger.error("Failed to retrieve accounts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve accounts")


@router.get("/accounts/stats", response_model=AccountStats)
async def get_account_stats(db: AsyncSession = Depends(get_db)):
    """Get account statistics"""
    try:
        # Count accounts by status
        status_counts = await db.execute(
            select(Account.status, func.count(Account.id))
            .group_by(Account.status)
        )
        
        # Count accounts by warmup phase
        warmup_counts = await db.execute(
            select(Account.warmup_phase, func.count(Account.id))
            .where(Account.warmup_phase.is_not(None))
            .group_by(Account.warmup_phase)
        )
        
        # Initialize stats
        stats = AccountStats()
        
        # Process status counts
        for status, count in status_counts.fetchall():
            if status == AccountStatus.ACTIVE:
                stats.active_accounts = count
            elif status == AccountStatus.WARMING_UP:
                stats.warming_up_accounts = count
            elif status == AccountStatus.SUSPENDED:
                stats.suspended_accounts = count
            elif status == AccountStatus.BANNED:
                stats.banned_accounts = count
            elif status == AccountStatus.INACTIVE:
                stats.inactive_accounts = count
            
            stats.total_accounts += count
        
        # Process warmup phase counts
        for phase, count in warmup_counts.fetchall():
            if phase == WarmupPhase.PHASE_1:
                stats.phase_1_accounts = count
            elif phase == WarmupPhase.PHASE_2:
                stats.phase_2_accounts = count
            elif phase == WarmupPhase.PHASE_3:
                stats.phase_3_accounts = count
            elif phase == WarmupPhase.COMPLETE:
                stats.complete_accounts = count
        
        logger.info("Retrieved account statistics", total=stats.total_accounts)
        return stats
        
    except Exception as e:
        logger.error("Failed to retrieve account statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve account statistics")


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific account by ID"""
    try:
        query = select(Account).where(Account.id == account_id)
        
        result = await db.execute(query)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        logger.info("Retrieved account", account_id=account_id, username=account.username)
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve account", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve account")


@router.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate, 
    license_info: dict = Depends(require_valid_license),
    db: AsyncSession = Depends(get_db)
):
    """Create new Instagram account"""
    try:
        license_key = license_info.get("license_key")
        logger.info(f"🔧 Creating account '{account_data.username}' for license_key: {license_key}")
        
        # Check if username already exists for this license
        existing = await db.execute(
            select(Account).where(
                and_(
                    Account.username == account_data.username,
                    Account.license_key == license_key
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists for this license")
        
        # Validate device exists if provided
        if account_data.device_id:
            device_result = await db.execute(
                select(Device).where(Device.id == account_data.device_id)
            )
            if not device_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Device not found")
        
        # Validate model exists if provided
        if account_data.model_id:
            model_result = await db.execute(
                select(Model).where(Model.id == account_data.model_id)
            )
            if not model_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Model profile not found")
        
        # Create account with license_key
        account_dict = account_data.model_dump()
        account_dict['license_key'] = license_key
        db_account = Account(**account_dict)
        db.add(db_account)
        await db.commit()
        await db.refresh(db_account)
        
        logger.info(f"✅ Successfully created account with ID: {db_account.id}")
        
        # Refresh account data for response
        await db.refresh(db_account)
        
        logger.info("Account created successfully", account_id=db_account.id, username=db_account.username)
        return db_account
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create account", username=account_data.username, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create account")


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int, 
    account_data: AccountUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update existing account"""
    try:
        # Get existing account
        query = select(Account).where(Account.id == account_id)
        result = await db.execute(query)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Validate device exists if provided
        if account_data.device_id:
            device_result = await db.execute(
                select(Device).where(Device.id == account_data.device_id)
            )
            if not device_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Device not found")
        
        # Validate model exists if provided
        if account_data.model_id:
            model_result = await db.execute(
                select(Model).where(Model.id == account_data.model_id)
            )
            if not model_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Model profile not found")
        
        # Update account fields
        update_data = account_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)
        
        await db.commit()
        await db.refresh(account)
        
        logger.info("Account updated successfully", account_id=account_id, username=account.username)
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update account", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update account")


@router.delete("/accounts/{account_id}")
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """Delete account"""
    try:
        # Get existing account
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        username = account.username
        await db.delete(account)
        await db.commit()
        
        logger.info("Account deleted successfully", account_id=account_id, username=username)
        return {"message": f"Account '{username}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete account", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete account")


@router.post("/accounts/{account_id}/activity")
async def log_account_activity(
    account_id: int,
    action_type: str,
    description: str,
    success: bool = True,
    error_message: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Log account activity (for automation tracking)"""
    try:
        # Verify account exists
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Update last_activity
        account.last_activity = func.now()
        
        await db.commit()
        
        logger.info("Account activity logged", 
                   account_id=account_id, 
                   action_type=action_type, 
                   success=success)
        
        return {"message": "Activity logged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to log account activity", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to log account activity")


@router.get("/models", response_model=List[ModelProfileResponse])
async def get_model_profiles(db: AsyncSession = Depends(get_db)):
    """Get all model profiles"""
    try:
        result = await db.execute(select(Model).order_by(Model.created_at.desc()))
        models = result.scalars().all()
        
        logger.info("Retrieved model profiles", count=len(models))
        return models
        
    except Exception as e:
        logger.error("Failed to retrieve model profiles", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve model profiles")
