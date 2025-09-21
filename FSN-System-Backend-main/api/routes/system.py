"""
System Management API Routes
Health monitoring, service control, and system statistics
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import structlog
from services.system_manager import system_manager
from services.job_executor import job_executor
from services.account_warmup import account_warmup_system

logger = structlog.get_logger()
router = APIRouter()

@router.get("/system/health")
async def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health status"""
    try:
        health = await system_manager.get_system_health()
        return health
    except Exception as e:
        logger.error("❌ Failed to get system health", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system health")

@router.get("/system/stats")
async def get_system_stats() -> Dict[str, Any]:
    """Get comprehensive system statistics"""
    try:
        stats = await system_manager.get_system_stats()
        return stats
    except Exception as e:
        logger.error("❌ Failed to get system stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system stats")

@router.post("/system/discover-devices")
async def discover_and_connect_devices() -> Dict[str, Any]:
    """Discover and connect to available devices"""
    try:
        result = await system_manager.discover_and_connect_devices()
        logger.info("🔍 Device discovery initiated", result=result)
        return result
    except Exception as e:
        logger.error("❌ Device discovery failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Device discovery failed: {str(e)}")

@router.post("/system/restart/{service_name}")
async def restart_service(service_name: str) -> Dict[str, Any]:
    """Restart a specific service"""
    try:
        result = await system_manager.restart_service(service_name)
        
        if result.get('success'):
            logger.info(f"🔄 Service restarted", service=service_name)
        else:
            logger.warning(f"⚠️  Service restart failed", service=service_name, message=result.get('message'))
        
        return result
    except Exception as e:
        logger.error(f"❌ Failed to restart {service_name}", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to restart {service_name}: {str(e)}")

@router.get("/system/queue/status")
async def get_queue_status() -> Dict[str, Any]:
    """Get job queue status"""
    try:
        status = await job_executor.get_queue_status()
        return status
    except Exception as e:
        logger.error("❌ Failed to get queue status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get queue status")

@router.get("/system/warmup/{account_id}")
async def get_warmup_status(account_id: int) -> Dict[str, Any]:
    """Get warmup status for a specific account"""
    try:
        status = await account_warmup_system.get_warmup_status(account_id)
        return status
    except Exception as e:
        logger.error(f"❌ Failed to get warmup status for account {account_id}", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get warmup status")

@router.post("/system/emergency-stop")
async def emergency_stop() -> Dict[str, Any]:
    """Emergency stop all automation services"""
    try:
        logger.warning("🚨 EMERGENCY STOP initiated")
        await system_manager.stop_all_services()
        
        return {
            "message": "Emergency stop completed",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "stopped"
        }
    except Exception as e:
        logger.error("❌ Emergency stop failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Emergency stop failed: {str(e)}")

@router.post("/system/start")
async def start_system() -> Dict[str, Any]:
    """Start all automation services"""
    try:
        logger.info("🚀 Starting automation system")
        await system_manager.start_all_services()
        
        return {
            "message": "Automation system started",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "running"
        }
    except Exception as e:
        logger.error("❌ Failed to start system", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start system: {str(e)}")
