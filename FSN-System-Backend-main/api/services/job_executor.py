"""
Background Job Execution System
Processes automation jobs with queue management, retries, and monitoring
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.connection import get_db, AsyncSessionLocal
from models.job import Job, JobStatus, JobType
from models.device import Device
from models.account import Account
from .instagram_automation import instagram_automation
from .real_device_instagram import real_device_instagram
from .appium_service import appium_service
from .device_pool_manager import device_pool_manager

logger = logging.getLogger(__name__)

class JobExecutor:
    """Background job execution system with queue management"""
    
    def __init__(self):
        self.running = False
        self.worker_tasks = []
        self.max_workers = 5
        self.job_queue = asyncio.Queue()
        self.retry_delays = [30, 60, 300, 900, 1800]  # Retry delays in seconds
        
    async def start(self):
        """Start the job execution system"""
        if self.running:
            return
            
        self.running = True
        logger.info("🚀 Starting job execution system with multi-device support")
        
        # Initialize device pool manager
        await device_pool_manager.initialize()
        
        # Start worker tasks
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        # Start job queue monitor
        monitor_task = asyncio.create_task(self._queue_monitor())
        self.worker_tasks.append(monitor_task)
        
        logger.info(f"✅ Job executor started with {self.max_workers} workers and multi-device pool")
    
    async def stop(self):
        """Stop the job execution system"""
        if not self.running:
            return
            
        self.running = False
        logger.info("🛑 Stopping job execution system")
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("✅ Job executor stopped")
    
    async def _worker(self, worker_name: str):
        """Background worker to process jobs"""
        logger.info(f"🔧 Worker {worker_name} started")
        
        while self.running:
            try:
                # Get job from queue (wait up to 5 seconds)
                try:
                    job_id = await asyncio.wait_for(self.job_queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process the job
                await self._process_job(job_id, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"🔧 Worker {worker_name} stopped")
    
    async def _queue_monitor(self):
        """Monitor for pending jobs and add to queue"""
        logger.info("📊 Queue monitor started")
        
        while self.running:
            try:
                async with AsyncSessionLocal() as db:
                    # Find pending jobs
                    result = await db.execute(
                        select(Job).where(
                            Job.status == JobStatus.PENDING
                        ).order_by(
                            Job.priority.desc(),
                            Job.created_at.asc()
                        ).limit(10)
                    )
                    pending_jobs = result.scalars().all()
                    
                    # Add jobs to queue
                    for job in pending_jobs:
                        if job.not_before and job.not_before > datetime.utcnow():
                            continue  # Job not ready yet
                        
                        # Mark as queued
                        await db.execute(
                            update(Job).where(Job.id == job.id).values(
                                status=JobStatus.QUEUED,
                                updated_at=datetime.utcnow()
                            )
                        )
                        await db.commit()
                        
                        # Add to processing queue
                        await self.job_queue.put(job.id)
                        logger.info(f"📋 Queued job {job.id}: {job.type}")
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue monitor error: {e}")
                await asyncio.sleep(5)
        
        logger.info("📊 Queue monitor stopped")
    
    async def _process_job(self, job_id: int, worker_name: str):
        """Process a single job"""
        async with AsyncSessionLocal() as db:
            try:
                # Get job details
                result = await db.execute(select(Job).where(Job.id == job_id))
                job = result.scalar_one_or_none()
                
                if not job:
                    logger.warning(f"Job {job_id} not found")
                    return
                
                logger.info(f"🔄 {worker_name} processing job {job_id}: {job.type}")
                
                # Mark job as running
                await db.execute(
                    update(Job).where(Job.id == job_id).values(
                        status=JobStatus.RUNNING,
                        started_at=datetime.utcnow(),
                        worker_id=worker_name,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # Get account and device
                account = await self._get_account(db, job.account_id)
                device = await self._assign_device(db, job)
                
                if not account or not device:
                    await self._fail_job(db, job_id, "Account or device not available")
                    return
                
                # Track execution timing
                start_time = datetime.utcnow()
                
                # Execute the job
                execution_result = await self._execute_job_action(job, account, device)
                
                # Calculate execution time
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds()
                
                # Release device with performance metrics
                await device_pool_manager.release_device(
                    device.udid, 
                    execution_result['success'], 
                    execution_time,
                    execution_result.get('message') if not execution_result['success'] else None
                )
                
                # Update job with results
                if execution_result['success']:
                    await self._complete_job(db, job_id, execution_result)
                else:
                    await self._handle_job_failure(db, job, execution_result)
                
            except Exception as e:
                logger.error(f"Job {job_id} processing error: {e}")
                await self._fail_job(db, job_id, f"Processing error: {str(e)}")
    
    async def _execute_job_action(self, job: Job, account: Account, device: Device) -> Dict[str, Any]:
        """Execute the specific job action"""
        try:
            # Ensure device session exists
            if device.udid not in appium_service.active_sessions:
                session_id = await appium_service.create_session(device.udid)
                if not session_id:
                    return {'success': False, 'message': 'Failed to create device session'}
            
            # Parse job parameters from payload
            params = job.payload or {}
            
            # Execute based on job type using CONFIRMED WORKING real device selectors
            # New Instagram job types (aligned with schemas)
            if job.type == JobType.INSTAGRAM_FOLLOW_USER.value:
                target_username = params.get('target_username')
                if not target_username:
                    return {'success': False, 'message': 'Missing target_username parameter'}
                result = await real_device_instagram.follow_user(device.udid, target_username)
            
            elif job.type == JobType.INSTAGRAM_LIKE_POST.value:
                count = params.get('count', 5)
                result = await real_device_instagram.like_posts(device.udid, count)
            
            elif job.type == JobType.INSTAGRAM_COMMENT_POST.value:
                comments = params.get('comments', ['Great post!', 'Amazing!', 'Love this!'])
                count = params.get('count', 3)
                result = await real_device_instagram.comment_on_posts(device.udid, comments, count)
            
            elif job.type == JobType.INSTAGRAM_VIEW_STORY.value:
                count = params.get('count', 10)
                result = await real_device_instagram.view_stories(device.udid, count)
            
            elif job.type == JobType.INSTAGRAM_POST_STORY.value:
                caption = params.get('caption', 'Posted via FSN Appium!')
                result = await real_device_instagram.post_story(device.udid, caption)
            
            elif job.type == JobType.INSTAGRAM_POST_REEL.value:
                caption = params.get('caption', 'Posted via FSN Appium!')
                result = await real_device_instagram.post_reel(device.udid, caption)
            
            elif job.type == JobType.INSTAGRAM_DIRECT_MESSAGE.value:
                target_username = params.get('target_username')
                message = params.get('message', 'Hello!')
                if not target_username:
                    return {'success': False, 'message': 'Missing target_username parameter'}
                result = await real_device_instagram.send_direct_message(device.udid, target_username, message)
            
            elif job.type == JobType.INSTAGRAM_PROFILE_UPDATE.value:
                bio = params.get('bio', 'Updated via FSN Appium!')
                result = await real_device_instagram.update_profile(device.udid, bio)
            
            # Legacy job types (for backward compatibility)
            elif job.type == JobType.FOLLOW_USER.value:
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
                comments = params.get('comments', ['Great post!', 'Amazing!', 'Love this!'])
                count = params.get('count', 3)
                result = await real_device_instagram.comment_on_posts(device.udid, comments, count)
            
            elif job.type == JobType.VIEW_STORY.value:
                count = params.get('count', 10)
                result = await real_device_instagram.view_stories(device.udid, count)
            
            elif job.type == JobType.SCAN_PROFILE.value:
                target_username = params.get('target_username')
                result = await real_device_instagram.scan_profile(device.udid, target_username)
            
            elif job.type == JobType.POST_PICTURE.value:
                caption = params.get('caption', 'Posted via FSN Appium!')
                result = await real_device_instagram.post_picture(device.udid, caption)
            
            elif job.type == JobType.SEARCH_HASHTAG.value:
                hashtag = params.get('hashtag')
                if not hashtag:
                    return {'success': False, 'message': 'Missing hashtag parameter'}
                # Use CONFIRMED WORKING real device service
                result = await real_device_instagram.search_hashtag(device.udid, hashtag)
            
            elif job.type == JobType.SAVE_POST.value:
                # Use CONFIRMED WORKING real device service
                result = await real_device_instagram.save_post(device.udid)
            
            # Legacy support for old job types (redirect to new service)
            elif job.type == "INSTAGRAM_FOLLOW":
                target_username = params.get('target_username')
                if not target_username:
                    return {'success': False, 'message': 'Missing target_username parameter'}
                result = await real_device_instagram.follow_user(device.udid, target_username)
            
            elif job.type == JobType.INSTAGRAM_LIKE_POST:
                count = params.get('count', 5)
                result = await real_device_instagram.like_posts(device.udid, count)
            
            elif job.type == JobType.INSTAGRAM_COMMENT_POST:
                comments = params.get('comments', ['Great post!', 'Amazing!', 'Love this!'])
                count = params.get('count', 3)
                result = await real_device_instagram.comment_on_posts(device.udid, comments, count)
            
            elif job.type == JobType.INSTAGRAM_VIEW_STORY:
                count = params.get('count', 10)
                result = await real_device_instagram.view_stories(device.udid, count)
            
            # Login still uses old service for now
            elif job.type == "INSTAGRAM_LOGIN":
                result = await instagram_automation.login(
                    device.udid, 
                    account.username, 
                    account.password or ""
                )
            
            elif job.type == JobType.INSTAGRAM_DIRECT_MESSAGE:
                target_username = params.get('target_username')
                message = params.get('message')
                if not target_username or not message:
                    return {'success': False, 'message': 'Missing DM parameters'}
                result = await instagram_automation.send_direct_message(device.udid, target_username, message)
            
            elif job.type == "INSTAGRAM_STATS":
                result = await instagram_automation.get_account_stats(device.udid)
            
            else:
                result = {'success': False, 'message': f'Unknown job type: {job.type}'}
            
            # Add execution metadata
            result['execution_time'] = datetime.utcnow().isoformat()
            result['device_used'] = device.name
            result['account_used'] = account.username
            
            return result
            
        except Exception as e:
            logger.error(f"Job action execution error: {e}")
            return {'success': False, 'message': f'Execution error: {str(e)}'}
    
    async def _get_account(self, db: AsyncSession, account_id: int) -> Optional[Account]:
        """Get account for job execution"""
        try:
            result = await db.execute(select(Account).where(Account.id == account_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting account {account_id}: {e}")
            return None
    
    async def _assign_device(self, db: AsyncSession, job: Job) -> Optional[Device]:
        """Assign optimal device for job execution using device pool manager"""
        try:
            # Prefer specific device if assigned and available
            if job.device_id:
                result = await db.execute(
                    select(Device).where(
                        Device.id == job.device_id,
                        Device.status.in_(['active', 'connected'])
                    )
                )
                device = result.scalar_one_or_none()
                if device:
                    logger.info(f"Using pre-assigned device {device.udid[:8]}... for job {job.id}")
                    return device
            
            # Use device pool manager for optimal assignment
            job_priority = getattr(job, 'priority', 'normal')
            optimal_udid = await device_pool_manager.assign_optimal_device(job_priority)
            
            if not optimal_udid:
                logger.warning(f"No available devices for job {job.id}")
                return None
            
            # Get device record from database
            result = await db.execute(
                select(Device).where(Device.udid == optimal_udid)
            )
            device = result.scalar_one_or_none()
            
            if device:
                # Update job with assigned device
                await db.execute(
                    update(Job).where(Job.id == job.id).values(
                        device_id=device.id,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                logger.info(f"🎯 Optimally assigned device {device.udid[:8]}... to job {job.id}")
            else:
                # Release the assigned device since we couldn't find the DB record
                await device_pool_manager.release_device(optimal_udid, False, 0.0, "Device not found in database")
            
            return device
            
        except Exception as e:
            logger.error(f"Error assigning device for job {job.id}: {e}")
            return None
    
    async def _complete_job(self, db: AsyncSession, job_id: int, result: Dict[str, Any]):
        """Mark job as completed with results"""
        try:
            await db.execute(
                update(Job).where(Job.id == job_id).values(
                    status=JobStatus.COMPLETED,
                    completed_at=datetime.utcnow(),
                    result=result,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            logger.info(f"✅ Job {job_id} completed successfully")
        except Exception as e:
            logger.error(f"Error completing job {job_id}: {e}")
    
    async def _handle_job_failure(self, db: AsyncSession, job: Job, result: Dict[str, Any]):
        """Handle job failure with retry logic"""
        try:
            retry_count = (job.retry_count or 0) + 1
            max_retries = 3
            
            if retry_count <= max_retries:
                # Schedule retry
                retry_delay = self.retry_delays[min(retry_count - 1, len(self.retry_delays) - 1)]
                retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
                
                await db.execute(
                    update(Job).where(Job.id == job.id).values(
                        status=JobStatus.PENDING,
                        retry_count=retry_count,
                        not_before=retry_at,
                        error_message=result.get('message', ''),
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                logger.warning(f"🔄 Job {job.id} scheduled for retry {retry_count}/{max_retries} in {retry_delay}s")
            else:
                # Max retries exceeded, mark as failed
                await self._fail_job(db, job.id, f"Max retries exceeded: {result.get('message', '')}")
                
        except Exception as e:
            logger.error(f"Error handling job failure for {job.id}: {e}")
    
    async def _fail_job(self, db: AsyncSession, job_id: int, error_message: str):
        """Mark job as failed"""
        try:
            await db.execute(
                update(Job).where(Job.id == job_id).values(
                    status=JobStatus.FAILED,
                    completed_at=datetime.utcnow(),
                    error_message=error_message,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            logger.error(f"❌ Job {job_id} failed: {error_message}")
        except Exception as e:
            logger.error(f"Error failing job {job_id}: {e}")
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        async with AsyncSessionLocal() as db:
            try:
                # Count jobs by status
                from sqlalchemy import func
                result = await db.execute(
                    select(Job.status, func.count(Job.id))
                    .group_by(Job.status)
                )
                status_counts = dict(result.fetchall())
                
                return {
                    'running': self.running,
                    'workers': len(self.worker_tasks),
                    'queue_size': self.job_queue.qsize(),
                    'job_counts': status_counts,
                    'timestamp': datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting queue status: {e}")
                return {'error': str(e)}


# Global instance
job_executor = JobExecutor()
