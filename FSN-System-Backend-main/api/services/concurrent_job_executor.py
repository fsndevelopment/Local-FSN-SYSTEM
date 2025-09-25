"""
Concurrent Job Executor
Enhanced job execution system with true multi-device parallelism for Instagram automation
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from collections import defaultdict

from database.connection import AsyncSessionLocal
from models.job import Job, JobStatus, JobType
from models.device import Device
from models.account import Account
from .device_pool_manager import device_pool_manager
from .real_device_instagram import real_device_instagram
from .appium_service import appium_service
from .websocket_manager import websocket_service
from .scroll_service import scroll_service

logger = logging.getLogger(__name__)

class JobBatch:
    """Represents a batch of jobs that can be executed concurrently"""
    
    def __init__(self, batch_id: str):
        self.batch_id = batch_id
        self.jobs: List[Job] = []
        self.assigned_devices: Dict[int, str] = {}  # job_id -> device_udid
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status = "pending"
        
    def add_job(self, job: Job, device_udid: str):
        """Add job to batch with assigned device"""
        self.jobs.append(job)
        self.assigned_devices[job.id] = device_udid
        
    def get_execution_time(self) -> float:
        """Get total batch execution time"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

class ConcurrentJobExecutor:
    """Advanced job executor with true multi-device concurrent execution"""
    
    def __init__(self):
        self.running = False
        self.concurrent_batches: Dict[str, JobBatch] = {}
        self.device_locks: Dict[str, asyncio.Lock] = {}  # Device-specific locks
        self.max_concurrent_batches = 3  # Maximum parallel job batches
        self.batch_size = 5  # Jobs per batch
        
        # Performance tracking
        self.total_jobs_processed = 0
        self.total_execution_time = 0.0
        self.concurrent_performance_gains = []
        
    async def start(self):
        """Start the concurrent job execution system"""
        if self.running:
            return
            
        self.running = True
        logger.info("🚀 Starting Concurrent Job Executor with multi-device parallelism")
        
        # Initialize device pool manager
        await device_pool_manager.initialize()
        
        # Start concurrent execution monitor
        asyncio.create_task(self._concurrent_execution_monitor())
        
        logger.info(f"✅ Concurrent executor started (max batches: {self.max_concurrent_batches})")
        
    async def stop(self):
        """Stop the concurrent job execution system"""
        if not self.running:
            return
            
        self.running = False
        
        # Wait for all batches to complete
        if self.concurrent_batches:
            logger.info("⏳ Waiting for concurrent batches to complete...")
            while self.concurrent_batches:
                await asyncio.sleep(1)
                
        logger.info("✅ Concurrent Job Executor stopped")
        
    async def execute_job_batch(self, job_ids: List[int], priority: str = "normal") -> Dict[str, Any]:
        """Execute a batch of jobs concurrently across multiple devices"""
        try:
            batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            batch = JobBatch(batch_id)
            
            async with AsyncSessionLocal() as db:
                # Get jobs from database
                result = await db.execute(
                    select(Job).where(
                        Job.id.in_(job_ids),
                        Job.status == JobStatus.PENDING
                    )
                )
                jobs = result.scalars().all()
                
                if not jobs:
                    return {'success': False, 'message': 'No pending jobs found'}
                
                # Assign devices to jobs
                assigned_jobs = []
                for job in jobs:
                    device_udid = await device_pool_manager.assign_optimal_device(priority)
                    if device_udid:
                        batch.add_job(job, device_udid)
                        assigned_jobs.append(job)
                        
                        # Mark job as running
                        await db.execute(
                            update(Job).where(Job.id == job.id).values(
                                status=JobStatus.RUNNING,
                                started_at=datetime.utcnow(),
                                worker_id=batch_id,
                                updated_at=datetime.utcnow()
                            )
                        )
                        
                        # Notify WebSocket clients about job status change
                        try:
                            await websocket_service.notify_job_status_change(
                                job_id=job.id,
                                old_status='pending',
                                new_status='running',
                                progress={'batch_id': batch_id, 'device_udid': device_udid}
                            )
                        except Exception as e:
                            logger.error(f"Failed to send WebSocket notification for job {job.id}: {e}")
                
                await db.commit()
                
                if not assigned_jobs:
                    return {'success': False, 'message': 'No devices available for job execution'}
                
                # Execute batch concurrently
                self.concurrent_batches[batch_id] = batch
                execution_result = await self._execute_batch_concurrent(batch)
                
                # Clean up
                del self.concurrent_batches[batch_id]
                
                return execution_result
                
        except Exception as e:
            logger.error(f"Error executing job batch: {e}")
            return {'success': False, 'message': f'Batch execution failed: {str(e)}'}
    
    async def _execute_batch_concurrent(self, batch: JobBatch) -> Dict[str, Any]:
        """Execute all jobs in a batch concurrently"""
        batch.start_time = datetime.utcnow()
        batch.status = "running"
        
        logger.info(f"🔥 Executing batch {batch.batch_id} with {len(batch.jobs)} jobs across {len(set(batch.assigned_devices.values()))} devices")
        
        # Create concurrent tasks for each job
        tasks = []
        for job in batch.jobs:
            device_udid = batch.assigned_devices[job.id]
            task = asyncio.create_task(
                self._execute_single_job_concurrent(job, device_udid, batch.batch_id)
            )
            tasks.append(task)
        
        # Wait for all jobs to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        batch.end_time = datetime.utcnow()
        batch.status = "completed"
        
        # Process results
        successful_jobs = 0
        failed_jobs = 0
        total_execution_time = batch.get_execution_time()
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Job {batch.jobs[i].id} failed with exception: {result}")
                failed_jobs += 1
            elif result and result.get('success', False):
                successful_jobs += 1
            else:
                failed_jobs += 1
        
        # Update performance metrics
        self.total_jobs_processed += len(batch.jobs)
        self.total_execution_time += total_execution_time
        
        # Calculate theoretical vs actual execution time for performance gain analysis
        avg_job_time = 45.0  # Assume 45s average per job
        theoretical_sequential_time = len(batch.jobs) * avg_job_time
        performance_gain = max(0, (theoretical_sequential_time - total_execution_time) / theoretical_sequential_time * 100)
        self.concurrent_performance_gains.append(performance_gain)
        
        logger.info(f"✅ Batch {batch.batch_id} completed: {successful_jobs} successful, {failed_jobs} failed in {total_execution_time:.1f}s (gain: {performance_gain:.1f}%)")
        
        return {
            'success': True,
            'batch_id': batch.batch_id,
            'total_jobs': len(batch.jobs),
            'successful_jobs': successful_jobs,
            'failed_jobs': failed_jobs,
            'execution_time': total_execution_time,
            'performance_gain_percent': performance_gain,
            'devices_used': len(set(batch.assigned_devices.values()))
        }
    
    async def _execute_single_job_concurrent(self, job: Job, device_udid: str, batch_id: str) -> Dict[str, Any]:
        """Execute a single job within a concurrent batch"""
        try:
            # Get device lock to prevent conflicts
            if device_udid not in self.device_locks:
                self.device_locks[device_udid] = asyncio.Lock()
            
            async with self.device_locks[device_udid]:
                # Get account and device info
                async with AsyncSessionLocal() as db:
                    # Get account
                    account_result = await db.execute(
                        select(Account).where(Account.id == job.account_id)
                    )
                    account = account_result.scalar_one_or_none()
                    
                    # Get device
                    device_result = await db.execute(
                        select(Device).where(Device.udid == device_udid)
                    )
                    device = device_result.scalar_one_or_none()
                    
                    if not account or not device:
                        raise Exception("Account or device not found")
                    
                    # Notify WebSocket about account processing start
                    try:
                        from .websocket_manager import websocket_service
                        await websocket_service.notify_account_processing(
                            device_id=str(device.id),
                            username=account.username,
                            account_id=str(account.id),
                            current_step="Starting concurrent job execution",
                            progress=0
                        )
                        logger.info(f"📡 WebSocket notification sent: Account {account.username} starting on device {device.id}")
                    except Exception as e:
                        logger.error(f"Failed to send WebSocket notification: {e}")
                    
                    # Execute job action
                    start_time = datetime.utcnow()
                    execution_result = await self._execute_job_action_concurrent(job, account, device)
                    end_time = datetime.utcnow()
                    
                    execution_time = (end_time - start_time).total_seconds()
                    
                    # Release device
                    await device_pool_manager.release_device(
                        device_udid,
                        execution_result['success'],
                        execution_time,
                        execution_result.get('message') if not execution_result['success'] else None
                    )
                    
                    # Update job status
                    if execution_result['success']:
                        await db.execute(
                            update(Job).where(Job.id == job.id).values(
                                status=JobStatus.COMPLETED,
                                completed_at=end_time,
                                result=execution_result,
                                updated_at=end_time
                            )
                        )
                        
                        # Notify WebSocket clients about job completion with username
                        try:
                            await websocket_service.notify_account_processing(
                                device_id=str(device.id),
                                username=account.username,
                                account_id=str(account.id),
                                current_step="Job completed successfully",
                                progress=100
                            )
                            logger.info(f"📡 WebSocket notification sent: Account {account.username} completed on device {device.id}")
                        except Exception as e:
                            logger.error(f"Failed to send WebSocket notification for job {job.id}: {e}")
                        logger.info(f"✅ Job {job.id} completed successfully on device {device_udid[:8]}...")
                    else:
                        await db.execute(
                            update(Job).where(Job.id == job.id).values(
                                status=JobStatus.FAILED,
                                completed_at=end_time,
                                error_message=execution_result.get('message', ''),
                                updated_at=end_time
                            )
                        )
                        
                        # Notify WebSocket clients about job failure
                        try:
                            await websocket_service.notify_job_status_change(
                                job_id=job.id,
                                old_status='running',
                                new_status='failed',
                                progress={
                                    'execution_time': execution_time,
                                    'error_message': execution_result.get('message', ''),
                                    'device_udid': device_udid
                                }
                            )
                        except Exception as e:
                            logger.error(f"Failed to send WebSocket notification for job {job.id}: {e}")
                        logger.warning(f"❌ Job {job.id} failed on device {device_udid[:8]}...") 
                    
                    await db.commit()
                    
                    return execution_result
                    
        except Exception as e:
            logger.error(f"Error executing job {job.id} on device {device_udid}: {e}")
            
            # Release device on error
            await device_pool_manager.release_device(device_udid, False, 0.0, str(e))
            
            return {'success': False, 'message': str(e)}
    
    async def _execute_job_action_concurrent(self, job: Job, account: Account, device: Device) -> Dict[str, Any]:
        """Execute the specific job action (similar to original but optimized for concurrency)"""
        try:
            # Ensure device session exists
            if device.udid not in appium_service.active_sessions:
                session_id = await appium_service.create_session(device.udid)
                if not session_id:
                    return {'success': False, 'message': 'Failed to create device session'}
            
            # Parse job parameters
            params = job.payload or {}
            
            # Execute based on job type using confirmed working actions
            # DEBUG: Log the job type and available attributes
            logger.info(f"CONCURRENT DEBUG: job.type = '{job.type}' (type: {type(job.type)})")
            logger.info(f"CONCURRENT DEBUG: Available JobType attributes: {[attr for attr in dir(JobType) if not attr.startswith('_') and not callable(getattr(JobType, attr))]}")
            
            if job.type == JobType.FOLLOW_USER.value:
                target_username = params.get('target_username')
                if not target_username:
                    return {'success': False, 'message': 'Missing target_username parameter'}
                result = await real_device_instagram.follow_user(device.udid, target_username)
            
            elif job.type == JobType.LIKE_POST.value:
                count = params.get('count', 5)
                result = await real_device_instagram.like_posts(device.udid, count)
            
            elif job.type == JobType.LIKE.value:  # Legacy LIKE alias
                count = params.get('count', 5)
                result = await real_device_instagram.like_posts(device.udid, count)
            
            elif job.type == JobType.COMMENT_POST.value:
                comment_text = params.get('comment_text', 'Great post! 👍')
                count = params.get('count', 3)
                result = await real_device_instagram.comment_posts(device.udid, comment_text, count)
            
            elif job.type == JobType.VIEW_STORY.value:
                target_username = params.get('target_username')
                if target_username:
                    result = await real_device_instagram.view_stories(device.udid, target_username)
                else:
                    result = await real_device_instagram.view_random_stories(device.udid)
            
            elif job.type == JobType.SCAN_PROFILE.value:
                target_username = params.get('target_username')
                if not target_username:
                    return {'success': False, 'message': 'Missing target_username parameter'}
                result = await real_device_instagram.scan_profile(device.udid, target_username)
            
            elif job.type == JobType.SCROLL_HOME_FEED.value:
                duration = params.get('duration', 300)  # 5 minutes default
                result = await real_device_instagram.scroll_home_feed(device.udid, duration)
            
            elif job.type == JobType.POST_PICTURE.value:
                image_path = params.get('image_path')
                caption = params.get('caption', '')
                if not image_path:
                    return {'success': False, 'message': 'Missing image_path parameter'}
                result = await real_device_instagram.post_picture(device.udid, image_path, caption)
            
            elif job.type == JobType.SEARCH_HASHTAG.value:
                hashtag = params.get('hashtag')
                if not hashtag:
                    return {'success': False, 'message': 'Missing hashtag parameter'}
                result = await real_device_instagram.search_hashtag(device.udid, hashtag)
            
            elif job.type == JobType.SAVE_POST.value:
                count = params.get('count', 3)
                result = await real_device_instagram.save_posts(device.udid, count)
            
            elif job.type == JobType.UNFOLLOW_USER.value:
                target_username = params.get('target_username')
                if not target_username:
                    return {'success': False, 'message': 'Missing target_username parameter'}
                result = await real_device_instagram.unfollow_user(device.udid, target_username)
            
            # Phase 5: Scrolling Jobs
            elif job.type == JobType.INSTAGRAM_SCROLL_HOME_FEED.value:
                scroll_count = job.scroll_count or params.get('scroll_count', 10)
                result = await scroll_service.execute_scroll_job(job, device)
            
            elif job.type == JobType.INSTAGRAM_SCROLL_REELS.value:
                scroll_count = job.scroll_count or params.get('scroll_count', 10)
                result = await scroll_service.execute_scroll_job(job, device)
            
            elif job.type == JobType.THREADS_SCROLL_HOME_FEED.value:
                scroll_count = job.scroll_count or params.get('scroll_count', 10)
                result = await scroll_service.execute_scroll_job(job, device)
            
            else:
                return {'success': False, 'message': f'Unsupported job type: {job.type}'}
            
            # Validate result format
            if not isinstance(result, dict) or 'success' not in result:
                return {'success': False, 'message': 'Invalid action result format'}
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing job action {job.type}: {e}")
            return {'success': False, 'message': f'Action execution failed: {str(e)}'}
    
    async def _concurrent_execution_monitor(self):
        """Background monitor for concurrent execution optimization"""
        logger.info("📊 Starting concurrent execution monitor...")
        
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Log performance metrics
                if self.concurrent_batches:
                    active_batches = len(self.concurrent_batches)
                    total_devices = len(set(
                        device_udid for batch in self.concurrent_batches.values()
                        for device_udid in batch.assigned_devices.values()
                    ))
                    
                    logger.info(f"📊 Concurrent execution: {active_batches} active batches using {total_devices} devices")
                
                # Calculate average performance gain
                if self.concurrent_performance_gains:
                    avg_gain = sum(self.concurrent_performance_gains) / len(self.concurrent_performance_gains)
                    logger.info(f"🚀 Average performance gain from concurrency: {avg_gain:.1f}%")
                
            except asyncio.CancelledError:
                logger.info("📊 Concurrent execution monitor stopped")
                break
            except Exception as e:
                logger.error(f"Concurrent execution monitor error: {e}")
    
    async def get_concurrent_status(self) -> Dict[str, Any]:
        """Get status of concurrent execution system"""
        active_batches_info = []
        total_active_jobs = 0
        devices_in_use = set()
        
        for batch_id, batch in self.concurrent_batches.items():
            batch_info = {
                'batch_id': batch_id,
                'status': batch.status,
                'total_jobs': len(batch.jobs),
                'devices_assigned': len(set(batch.assigned_devices.values())),
                'start_time': batch.start_time.isoformat() if batch.start_time else None,
                'running_time': (datetime.utcnow() - batch.start_time).total_seconds() if batch.start_time else 0
            }
            active_batches_info.append(batch_info)
            total_active_jobs += len(batch.jobs)
            devices_in_use.update(batch.assigned_devices.values())
        
        avg_performance_gain = 0
        if self.concurrent_performance_gains:
            avg_performance_gain = sum(self.concurrent_performance_gains) / len(self.concurrent_performance_gains)
        
        return {
            'system_running': self.running,
            'active_batches': len(self.concurrent_batches),
            'total_active_jobs': total_active_jobs,
            'devices_in_use': len(devices_in_use),
            'total_jobs_processed': self.total_jobs_processed,
            'total_execution_time': self.total_execution_time,
            'average_performance_gain_percent': avg_performance_gain,
            'max_concurrent_batches': self.max_concurrent_batches,
            'batch_size': self.batch_size,
            'active_batches_details': active_batches_info
        }

# Global instance
concurrent_job_executor = ConcurrentJobExecutor()
