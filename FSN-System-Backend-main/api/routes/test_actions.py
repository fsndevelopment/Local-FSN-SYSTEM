"""
Test Action Endpoints
Backend-only smoke endpoints for testing FSM actions
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from models.device import Device
from models.account import Account
from models.job import Job, JobType, JobStatus, JobPriority
from agents.device.fsm import (
    ActionContext, ActionPayload, ActionTarget, 
    Platform, DriverType, DeviceCapabilities
)
from agents.device.platforms.instagram.actions import IGScanProfileAction
from agents.device.drivers import DriverFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test", tags=["test_actions"])


class IGScanProfileRequest(BaseModel):
    """Request for Instagram profile scan test"""
    device_udid: str = Field(..., description="Device UDID to use for testing")
    account_username: str = Field(..., description="Instagram account to use")
    target_username: str = Field(..., description="Target Instagram username to scan")
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_udid": "00008110-001234567890ABCD",
                "account_username": "test_account",
                "target_username": "@example_user"
            }
        }


class ActionTestResponse(BaseModel):
    """Response for action test endpoints"""
    success: bool
    execution_time_ms: int
    state_path: list[str]
    data: Dict[str, Any] = None
    error_message: str = None
    error_code: str = None
    telemetry: Dict[str, Any] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "execution_time_ms": 7200,
                "state_path": ["init", "open_app", "ensure_home", "navigate", "find_target", "read", "verify", "log", "done"],
                "data": {
                    "username": "@example_user",
                    "followers_count": 15420,
                    "following_count": 892,
                    "posts_count": 156,
                    "bio": "Digital creator 📸"
                },
                "telemetry": {
                    "counters": {"ui_freeze_trips": 0, "session_restarts": 0}
                }
            }
        }


@router.post("/ig/scan_profile", response_model=ActionTestResponse)
async def test_ig_scan_profile(
    request: IGScanProfileRequest,
    session: AsyncSession = Depends(get_session)
) -> ActionTestResponse:
    """
    Test Instagram profile scan action
    Backend-only smoke endpoint for SCAN_PROFILE PoC
    """
    logger.info(f"Testing IG_SCAN_PROFILE: {request.target_username} on device {request.device_udid}")
    
    try:
        # Get or create test device
        device = await _get_or_create_test_device(session, request.device_udid)
        
        # Get or create test account  
        account = await _get_or_create_test_account(session, request.account_username)
        
        # Create test job
        job = Job(
            account_id=account.id,
            device_id=device.id,
            type=JobType.IG_SCAN_PROFILE,
            platform="instagram",
            payload={
                "target_username": request.target_username,
                "include_posts": True,
                "include_followers": True
            },
            priority=JobPriority.HIGH,
            status=JobStatus.PENDING
        )
        
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
        # Execute action directly (bypass job queue for testing)
        result = await _execute_scan_profile_action(job, device, account, request.target_username)
        
        # Update job status
        job.status = JobStatus.COMPLETED if result["success"] else JobStatus.FAILED
        job.result = result["data"] if result["success"] else None
        job.error_message = result.get("error_message")
        job.completed_at = datetime.utcnow()
        
        await session.commit()
        
        return ActionTestResponse(
            success=result["success"],
            execution_time_ms=result["execution_time_ms"],
            state_path=result["state_path"],
            data=result.get("data"),
            error_message=result.get("error_message"),
            error_code=result.get("error_code"),
            telemetry=result.get("telemetry")
        )
        
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")


async def _execute_scan_profile_action(
    job: Job, 
    device: Device, 
    account: Account, 
    target_username: str
) -> Dict[str, Any]:
    """Execute SCAN_PROFILE action directly"""
    
    start_time = datetime.utcnow()
    
    try:
        # Create action context
        target = ActionTarget(type="username", value=target_username)
        payload = ActionPayload(
            action_type="IG_SCAN_PROFILE",
            target=target,
            parameters={"include_posts": True, "include_followers": True}
        )
        
        # Detect device capabilities (mock for testing)
        capabilities = DeviceCapabilities(
            ui_automation=True,
            frida=False,  # Assume non-JB for testing
            fast_scrape=False,
            performance_score=75
        )
        
        context = ActionContext(
            job=job,
            device=device,
            account=account,
            payload=payload,
            platform=Platform.INSTAGRAM,
            driver_type=DriverType.NONJB
        )
        context.set_capabilities(capabilities)
        
        # Create mock driver (for testing without real device)
        mock_driver = await _create_mock_driver(device.udid, capabilities)
        context.set_driver(mock_driver)
        
        # Execute action
        action = IGScanProfileAction(context)
        success = await action.execute()
        
        end_time = datetime.utcnow()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Get execution summary
        summary = action.get_action_result()
        
        return {
            "success": success,
            "execution_time_ms": execution_time_ms,
            "state_path": summary["execution_path"]["state_path"],
            "data": context.result_data if success else None,
            "error_message": context.error_message,
            "error_code": context.error_code,
            "telemetry": summary.get("watchdog_telemetry")
        }
        
    except Exception as e:
        end_time = datetime.utcnow()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        logger.error(f"Action execution failed: {e}")
        return {
            "success": False,
            "execution_time_ms": execution_time_ms,
            "state_path": ["init", "error"],
            "error_message": str(e),
            "error_code": "E_EXECUTION_FAILED"
        }


async def _get_or_create_test_device(session: AsyncSession, udid: str) -> Device:
    """Get or create test device"""
    from sqlalchemy import select
    
    result = await session.execute(select(Device).where(Device.udid == udid))
    device = result.scalar_one_or_none()
    
    if not device:
        device = Device(
            udid=udid,
            name=f"Test Device {udid[:8]}",
            platform="iOS",
            version="17.0",
            model="iPhone",
            status="active",
            capabilities=["ui_automation"]
        )
        session.add(device)
        await session.commit()
        await session.refresh(device)
    
    return device


async def _get_or_create_test_account(session: AsyncSession, username: str) -> Account:
    """Get or create test account"""
    from sqlalchemy import select
    
    result = await session.execute(select(Account).where(Account.username == username))
    account = result.scalar_one_or_none()
    
    if not account:
        account = Account(
            username=username,
            platform="instagram",
            status="active",
            warmup_phase="completed"
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
    
    return account


async def _create_mock_driver(udid: str, capabilities: DeviceCapabilities):
    """Create mock driver for testing"""
    
    class MockDriver:
        def __init__(self, udid: str, capabilities: DeviceCapabilities):
            self.device_udid = udid
            self.capabilities = capabilities
            self.is_connected = True
        
        async def connect(self) -> bool:
            return True
        
        async def disconnect(self) -> None:
            pass
        
        async def open_app(self, platform) -> bool:
            await asyncio.sleep(0.5)  # Simulate app opening
            return True
        
        async def take_screenshot(self, file_path: str) -> bool:
            # Create dummy screenshot file
            with open(file_path, 'w') as f:
                f.write("mock_screenshot_data")
            return True
        
        async def get_page_source(self) -> str:
            return "<xml>mock_page_source</xml>"
        
        async def find_element(self, strategy: str, value: str, timeout: int = 10):
            await asyncio.sleep(0.1)  # Simulate element search
            return "mock_element"
        
        async def click_element(self, element) -> bool:
            await asyncio.sleep(0.1)
            return True
    
    return MockDriver(udid, capabilities)


@router.get("/health")
async def test_health():
    """Health check for test endpoints"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "available_tests": ["ig/scan_profile"],
        "fsm_framework": "ready"
    }
