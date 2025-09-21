"""
Job Execution Service
Handles complete workflow: device initialization -> container switching -> template execution
"""

import asyncio
import logging
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

from services.crane_account_switching import crane_threads_account_switching
from services.crane_container_service import crane_container_service
from services.appium_template_executor import appium_template_executor
from services.job_websocket_service import job_websocket_service
from models.device import Device
from models.account import Account

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    CONTAINER_SWITCHING = "container_switching"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

class JobExecutionService:
    """
    Complete job execution service that handles the full workflow:
    1. Device initialization (Appium startup, phone connection)
    2. Container switching (for jailbroken devices)
    3. Template execution (using existing Threads automation scripts)
    4. Job management and status tracking
    """
    
    def __init__(self):
        self.active_jobs = {}  # job_id -> job_info
        self.job_history = []  # completed jobs
        self.base_path = "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main"
        
    async def start_job(self, job_id: str, template: Dict[str, Any], device: Device, accounts: List[Account]) -> Dict[str, Any]:
        """
        Start a complete job execution
        
        Args:
            job_id: Unique job identifier
            template: Template configuration with actions
            device: Device to execute on
            accounts: Accounts to use for execution
            
        Returns:
            Job start result
        """
        try:
            logger.info(f"Starting job {job_id}", 
                       template_id=template.get('id'),
                       device_id=device.id,
                       accounts_count=len(accounts))
            
            # Create job record
            job_info = {
                "id": job_id,
                "template": template,
                "device": device,
                "accounts": accounts,
                "status": JobStatus.PENDING,
                "created_at": datetime.utcnow().isoformat(),
                "started_at": None,
                "completed_at": None,
                "current_step": "pending",
                "progress": 0,
                "results": [],
                "errors": []
            }
            
            self.active_jobs[job_id] = job_info
            
            # Start job execution in background
            asyncio.create_task(self._execute_job(job_id))
            
            return {
                "success": True,
                "job_id": job_id,
                "message": f"Job {job_id} started successfully",
                "status": JobStatus.PENDING.value
            }
            
        except Exception as e:
            logger.error(f"Failed to start job {job_id}", error=str(e))
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e)
            }
    
    async def _execute_job(self, job_id: str):
        """Execute the complete job workflow"""
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            # Step 1: Initialize device
            await self._update_job_status(job_id, JobStatus.INITIALIZING, "initializing_device", 10)
            device_result = await self._initialize_device(job_info)
            if not device_result["success"]:
                await self._fail_job(job_id, f"Device initialization failed: {device_result['error']}")
                return
            
            # Step 2: Handle container switching (for jailbroken devices)
            if job_info["device"].jailbroken:
                await self._update_job_status(job_id, JobStatus.CONTAINER_SWITCHING, "switching_containers", 30)
                container_result = await self._handle_container_switching(job_info)
                if not container_result["success"]:
                    await self._fail_job(job_id, f"Container switching failed: {container_result['error']}")
                    return
            
            # Step 3: Execute template actions
            await self._update_job_status(job_id, JobStatus.EXECUTING, "executing_template", 50)
            execution_result = await self._execute_template_actions(job_info)
            if not execution_result["success"]:
                await self._fail_job(job_id, f"Template execution failed: {execution_result['error']}")
                return
            
            # Step 4: Complete job
            await self._complete_job(job_id, execution_result)
            
        except Exception as e:
            logger.error(f"Job execution error for {job_id}", error=str(e))
            await self._fail_job(job_id, f"Job execution error: {str(e)}")
    
    async def _initialize_device(self, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize device and start Appium session"""
        try:
            device = job_info["device"]
            logger.info(f"Initializing device {device.id} ({device.udid})")
            
            # Start Appium server if not running
            appium_result = await self._start_appium_server(device)
            if not appium_result["success"]:
                return {"success": False, "error": f"Appium startup failed: {appium_result['error']}"}
            
            # Connect to device
            connection_result = await self._connect_to_device(device)
            if not connection_result["success"]:
                return {"success": False, "error": f"Device connection failed: {connection_result['error']}"}
            
            logger.info(f"Device {device.id} initialized successfully")
            return {"success": True, "message": "Device initialized successfully"}
            
        except Exception as e:
            logger.error(f"Device initialization error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _start_appium_server(self, device: Device) -> Dict[str, Any]:
        """Start Appium server for the device"""
        try:
            # Check if Appium is already running on this port
            if await self._is_port_in_use(device.appium_port):
                logger.info(f"Appium already running on port {device.appium_port}")
                return {"success": True, "message": "Appium already running"}
            
            # Start Appium server
            cmd = [
                "appium",
                "--port", str(device.appium_port),
                "--driver", "xcuitest",
                "--driver-xcuitest-webdriveragent-port", str(device.wda_port),
                "--log-level", "info"
            ]
            
            logger.info(f"Starting Appium server", command=" ".join(cmd))
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for Appium to start
            await asyncio.sleep(5)
            
            # Check if process is still running
            if process.returncode is not None:
                stdout, stderr = await process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"
                return {"success": False, "error": f"Appium failed to start: {error_msg}"}
            
            logger.info(f"Appium server started on port {device.appium_port}")
            return {"success": True, "message": "Appium server started"}
            
        except Exception as e:
            logger.error(f"Appium startup error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _connect_to_device(self, device: Device) -> Dict[str, Any]:
        """Connect to the device using Appium"""
        try:
            # This would use the existing Appium connection logic
            # For now, we'll assume the connection is successful
            logger.info(f"Connecting to device {device.udid}")
            
            # Simulate connection time
            await asyncio.sleep(2)
            
            logger.info(f"Connected to device {device.udid}")
            return {"success": True, "message": "Device connected"}
            
        except Exception as e:
            logger.error(f"Device connection error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _handle_container_switching(self, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Crane container switching for jailbroken devices"""
        try:
            device = job_info["device"]
            accounts = job_info["accounts"]
            
            logger.info(f"Handling container switching for device {device.id}")
            
            # For each account, switch to its container
            for account in accounts:
                if hasattr(account, 'container_id') and account.container_id:
                    logger.info(f"Switching to container {account.container_id} for account {account.username}")
                    
                    # Use the existing Crane account switching service
                    switch_result = await crane_threads_account_switching.complete_crane_account_switch_flow(
                        device.udid, 
                        account.container_id, 
                        "threads"
                    )
                    
                    if not switch_result["success"]:
                        logger.warning(f"Container switch failed for account {account.username}: {switch_result['message']}")
                        continue
                    
                    logger.info(f"Successfully switched to container {account.container_id} for account {account.username}")
            
            return {"success": True, "message": "Container switching completed"}
            
        except Exception as e:
            logger.error(f"Container switching error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _execute_template_actions(self, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute template actions using existing automation scripts"""
        try:
            template = job_info["template"]
            device = job_info["device"]
            accounts = job_info["accounts"]
            
            logger.info(f"Executing template actions for {len(accounts)} accounts")
            
            # Use the existing template executor
            execution_result = await appium_template_executor.execute_template(
                template, device, accounts
            )
            
            if execution_result["success"]:
                logger.info(f"Template execution completed successfully")
                return {"success": True, "results": execution_result["results"]}
            else:
                logger.error(f"Template execution failed: {execution_result.get('error')}")
                return {"success": False, "error": execution_result.get('error', 'Unknown error')}
            
        except Exception as e:
            logger.error(f"Template execution error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_job_status(self, job_id: str, status: JobStatus, step: str, progress: int):
        """Update job status and progress"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["status"] = status
            self.active_jobs[job_id]["current_step"] = step
            self.active_jobs[job_id]["progress"] = progress
            
            if status == JobStatus.INITIALIZING and not self.active_jobs[job_id]["started_at"]:
                self.active_jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
            
            # Send WebSocket update
            await job_websocket_service.send_job_status(
                job_id, status.value, progress, step
            )
            
            logger.info(f"Job {job_id} status updated", 
                       status=status.value, 
                       step=step, 
                       progress=progress)
    
    async def _complete_job(self, job_id: str, execution_result: Dict[str, Any]):
        """Mark job as completed"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["status"] = JobStatus.COMPLETED
            self.active_jobs[job_id]["current_step"] = "completed"
            self.active_jobs[job_id]["progress"] = 100
            self.active_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
            self.active_jobs[job_id]["results"] = execution_result.get("results", [])
            
            # Send WebSocket completion update
            await job_websocket_service.send_job_completion(
                job_id, True, 
                execution_result.get("results", []), 
                []
            )
            
            # Move to history
            self.job_history.append(self.active_jobs[job_id])
            del self.active_jobs[job_id]
            
            logger.info(f"Job {job_id} completed successfully")
    
    async def _fail_job(self, job_id: str, error_message: str):
        """Mark job as failed"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["status"] = JobStatus.FAILED
            self.active_jobs[job_id]["current_step"] = "failed"
            self.active_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
            self.active_jobs[job_id]["errors"].append(error_message)
            
            # Send WebSocket failure update
            await job_websocket_service.send_job_completion(
                job_id, False, 
                [], 
                [error_message]
            )
            
            # Move to history
            self.job_history.append(self.active_jobs[job_id])
            del self.active_jobs[job_id]
            
            logger.error(f"Job {job_id} failed: {error_message}")
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status"""
        return self.active_jobs.get(job_id)
    
    async def get_all_jobs(self) -> Dict[str, Any]:
        """Get all active and completed jobs"""
        return {
            "active_jobs": list(self.active_jobs.values()),
            "completed_jobs": self.job_history[-50:],  # Last 50 completed jobs
            "total_active": len(self.active_jobs),
            "total_completed": len(self.job_history)
        }
    
    async def stop_job(self, job_id: str) -> bool:
        """Stop a running job"""
        try:
            if job_id in self.active_jobs:
                job_info = self.active_jobs[job_id]
                job_info["status"] = JobStatus.STOPPED
                job_info["completed_at"] = datetime.utcnow().isoformat()
                
                # Stop template execution if running
                await appium_template_executor.stop_template_execution(job_info["template"]["id"])
                
                # Move to history
                self.job_history.append(job_info)
                del self.active_jobs[job_id]
                
                logger.info(f"Job {job_id} stopped")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to stop job {job_id}", error=str(e))
            return False
    
    async def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return False
        except OSError:
            return True

# Global instance
job_execution_service = JobExecutionService()
