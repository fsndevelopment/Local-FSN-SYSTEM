"""
Account Switching Routes
Handles switching between accounts on Instagram and Threads
"""

import structlog
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from database.connection import get_db
from services.instagram_account_switching import instagram_account_switching
from services.threads_account_switching import threads_account_switching
from services.crane_account_switching import crane_instagram_account_switching, crane_threads_account_switching

logger = structlog.get_logger()
router = APIRouter()

class AccountSwitchRequest(BaseModel):
    device_udid: str
    target_username: str
    platform: str = "instagram"  # "instagram" or "threads"
    device_type: str = "non_jailbroken"  # "jailbroken" or "non_jailbroken"
    container_id: Optional[str] = None  # For jailbroken devices

class AccountSwitchResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]

class AvailableAccountsResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]

@router.post("/account-switching/switch", response_model=AccountSwitchResponse)
async def switch_account(request: AccountSwitchRequest, db: AsyncSession = Depends(get_db)):
    """Switch to a specific account on the device"""
    try:
        # Check if device is jailbroken and use Crane container switching
        if request.device_type == "jailbroken":
            if not request.container_id:
                raise HTTPException(status_code=400, detail="Container ID required for jailbroken devices")
            
            if request.platform == "instagram":
                result = await crane_instagram_account_switching.complete_crane_account_switch_flow(
                    request.device_udid, 
                    request.container_id,
                    request.platform
                )
            elif request.platform == "threads":
                result = await crane_threads_account_switching.complete_crane_account_switch_flow(
                    request.device_udid, 
                    request.container_id,
                    request.platform
                )
            else:
                raise HTTPException(status_code=400, detail=f"Platform {request.platform} not supported for jailbroken devices")
        else:
            # Use standard in-app account switching for non-jailbroken devices
            if request.platform == "instagram":
                result = await instagram_account_switching.complete_account_switch_flow(
                    request.device_udid, 
                    request.target_username
                )
            elif request.platform == "threads":
                result = await threads_account_switching.complete_account_switch_flow(
                    request.device_udid, 
                    request.target_username
                )
            else:
                raise HTTPException(status_code=400, detail=f"Platform {request.platform} not supported yet")
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return AccountSwitchResponse(**result)
        
    except Exception as e:
        logger.error(f"Account switching error: {e}")
        raise HTTPException(status_code=500, detail=f"Account switching failed: {str(e)}")

@router.post("/account-switching/launch", response_model=AccountSwitchResponse)
async def launch_app(request: AccountSwitchRequest, db: AsyncSession = Depends(get_db)):
    """Launch the app and navigate to profile tab"""
    try:
        if request.platform == "instagram":
            # Launch and navigate to profile
            launch_result = await instagram_account_switching.launch_instagram_homepage(request.device_udid)
            if not launch_result['success']:
                raise HTTPException(status_code=400, detail=launch_result['message'])
                
            profile_result = await instagram_account_switching.navigate_to_profile_tab(request.device_udid)
            if not profile_result['success']:
                raise HTTPException(status_code=400, detail=profile_result['message'])
            
            result = {
                'success': True,
                'message': 'Instagram launched and navigated to profile tab',
                'data': {
                    'launch_checkpoint': launch_result['data'],
                    'profile_checkpoint': profile_result['data']
                }
            }
        elif request.platform == "threads":
            # Launch and navigate to profile
            launch_result = await threads_account_switching.launch_threads_homepage(request.device_udid)
            if not launch_result['success']:
                raise HTTPException(status_code=400, detail=launch_result['message'])
                
            profile_result = await threads_account_switching.navigate_to_profile_tab(request.device_udid)
            if not profile_result['success']:
                raise HTTPException(status_code=400, detail=profile_result['message'])
            
            result = {
                'success': True,
                'message': 'Threads launched and navigated to profile tab',
                'data': {
                    'launch_checkpoint': launch_result['data'],
                    'profile_checkpoint': profile_result['data']
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Platform {request.platform} not supported yet")
            
        return AccountSwitchResponse(**result)
        
    except Exception as e:
        logger.error(f"App launch error: {e}")
        raise HTTPException(status_code=500, detail=f"App launch failed: {str(e)}")

@router.post("/account-switching/open-switcher", response_model=AccountSwitchResponse)
async def open_account_switcher(request: AccountSwitchRequest, db: AsyncSession = Depends(get_db)):
    """Open the account switcher dropdown"""
    try:
        if request.platform == "instagram":
            result = await instagram_account_switching.open_account_switcher(request.device_udid)
        elif request.platform == "threads":
            result = await threads_account_switching.open_account_switcher(request.device_udid)
        else:
            raise HTTPException(status_code=400, detail=f"Platform {request.platform} not supported yet")
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return AccountSwitchResponse(**result)
        
    except Exception as e:
        logger.error(f"Open switcher error: {e}")
        raise HTTPException(status_code=500, detail=f"Open switcher failed: {str(e)}")

@router.post("/account-switching/available-accounts", response_model=AvailableAccountsResponse)
async def get_available_accounts(request: AccountSwitchRequest, db: AsyncSession = Depends(get_db)):
    """Get list of available accounts on the device"""
    try:
        if request.platform == "instagram":
            result = await instagram_account_switching.get_available_accounts(request.device_udid)
        elif request.platform == "threads":
            result = await threads_account_switching.get_available_accounts(request.device_udid)
        else:
            raise HTTPException(status_code=400, detail=f"Platform {request.platform} not supported yet")
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return AvailableAccountsResponse(**result)
        
    except Exception as e:
        logger.error(f"Get available accounts error: {e}")
        raise HTTPException(status_code=500, detail=f"Get available accounts failed: {str(e)}")

@router.post("/account-switching/switch-only", response_model=AccountSwitchResponse)
async def switch_to_account_only(request: AccountSwitchRequest, db: AsyncSession = Depends(get_db)):
    """Switch to account (assumes switcher is already open)"""
    try:
        if request.platform == "instagram":
            result = await instagram_account_switching.switch_to_account(request.device_udid, request.target_username)
        elif request.platform == "threads":
            result = await threads_account_switching.switch_to_account(request.device_udid, request.target_username)
        else:
            raise HTTPException(status_code=400, detail=f"Platform {request.platform} not supported yet")
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return AccountSwitchResponse(**result)
        
    except Exception as e:
        logger.error(f"Account switch error: {e}")
        raise HTTPException(status_code=500, detail=f"Account switch failed: {str(e)}")

@router.post("/account-switching/close-switcher", response_model=AccountSwitchResponse)
async def close_account_switcher(request: AccountSwitchRequest, db: AsyncSession = Depends(get_db)):
    """Close the account switcher dropdown"""
    try:
        if request.platform == "instagram":
            result = await instagram_account_switching.close_account_switcher(request.device_udid)
        else:
            raise HTTPException(status_code=400, detail=f"Platform {request.platform} not supported yet")
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return AccountSwitchResponse(**result)
        
    except Exception as e:
        logger.error(f"Close switcher error: {e}")
        raise HTTPException(status_code=500, detail=f"Close switcher failed: {str(e)}")

@router.post("/account-switching/containers", response_model=AvailableAccountsResponse)
async def get_available_containers(request: AccountSwitchRequest, db: AsyncSession = Depends(get_db)):
    """Get list of available containers for jailbroken devices"""
    try:
        if request.device_type != "jailbroken":
            raise HTTPException(status_code=400, detail="Container list only available for jailbroken devices")
        
        if request.platform == "instagram":
            result = await crane_instagram_account_switching.get_available_containers(
                request.device_udid, 
                request.platform
            )
        elif request.platform == "threads":
            result = await crane_threads_account_switching.get_available_containers(
                request.device_udid, 
                request.platform
            )
        else:
            raise HTTPException(status_code=400, detail=f"Platform {request.platform} not supported for containers")
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return AvailableAccountsResponse(**result)
        
    except Exception as e:
        logger.error(f"Get containers error: {e}")
        raise HTTPException(status_code=500, detail=f"Get containers failed: {str(e)}")
