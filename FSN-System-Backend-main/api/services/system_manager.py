"""
System Manager - Coordinates all automation services
Manages job executor, warmup system, device monitoring, and system health
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from .job_executor import job_executor
from .account_warmup import account_warmup_system
from .appium_service import appium_service

logger = logging.getLogger(__name__)

class SystemManager:
    """Coordinates all automation services"""
    
    def __init__(self):
        self.running = False
        self.health_monitor_task = None
        
    async def start_all_services(self):
        """Start all automation services"""
        if self.running:
            return
            
        logger.info("🚀 Starting FSN Appium Farm automation system")
        
        try:
            # Start Appium server
            logger.info("📱 Starting Appium server...")
            appium_started = await appium_service.start_appium_server()
            if not appium_started:
                logger.warning("⚠️  Appium server failed to start, but continuing...")
            else:
                logger.info("✅ Appium server started")
            
            # Start job executor
            logger.info("⚙️  Starting job executor...")
            await job_executor.start()
            logger.info("✅ Job executor started")
            
            # Start account warmup system
            logger.info("🌡️ Starting account warmup system...")
            await account_warmup_system.start()
            logger.info("✅ Account warmup system started")
            
            # Start health monitoring
            logger.info("💓 Starting health monitor...")
            self.health_monitor_task = asyncio.create_task(self._health_monitor())
            
            self.running = True
            logger.info("🎉 All automation services started successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to start automation services: {e}")
            await self.stop_all_services()
            raise
    
    async def stop_all_services(self):
        """Stop all automation services"""
        if not self.running:
            return
            
        logger.info("🛑 Stopping FSN Appium Farm automation system")
        
        try:
            # Stop health monitor
            if self.health_monitor_task:
                self.health_monitor_task.cancel()
                try:
                    await self.health_monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Stop account warmup system
            logger.info("🌡️ Stopping account warmup system...")
            await account_warmup_system.stop()
            logger.info("✅ Account warmup system stopped")
            
            # Stop job executor
            logger.info("⚙️  Stopping job executor...")
            await job_executor.stop()
            logger.info("✅ Job executor stopped")
            
            self.running = False
            logger.info("✅ All automation services stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping services: {e}")
    
    async def _health_monitor(self):
        """Monitor system health and log status"""
        logger.info("💓 Health monitor started")
        
        while self.running:
            try:
                # Get system health
                health = await self.get_system_health()
                
                # Log health summary every 5 minutes
                if datetime.now().minute % 5 == 0:
                    self._log_health_summary(health)
                
                # Check for critical issues
                await self._check_critical_issues(health)
                
                # Wait 1 minute before next check
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
        
        logger.info("💓 Health monitor stopped")
    
    def _log_health_summary(self, health: Dict[str, Any]):
        """Log health summary"""
        try:
            appium_status = "✅" if health['appium']['server_running'] else "❌"
            job_status = "✅" if health['job_executor']['running'] else "❌"
            warmup_status = "✅" if health['account_warmup']['running'] else "❌"
            
            logger.info(
                f"💓 System Health: "
                f"Appium {appium_status} | "
                f"Jobs {job_status} ({health['job_executor']['queue_size']} queued) | "
                f"Warmup {warmup_status} | "
                f"Devices: {health['appium']['discovered_devices']}"
            )
        except Exception as e:
            logger.error(f"Error logging health summary: {e}")
    
    async def _check_critical_issues(self, health: Dict[str, Any]):
        """Check for critical system issues"""
        try:
            # Check if job executor stopped
            if not health['job_executor']['running']:
                logger.error("🚨 CRITICAL: Job executor stopped!")
                # Could restart here
            
            # Check if too many jobs are queued
            queue_size = health['job_executor']['queue_size']
            if queue_size > 100:
                logger.warning(f"⚠️  High job queue size: {queue_size}")
            
            # Check if no devices available
            if health['appium']['discovered_devices'] == 0:
                logger.warning("⚠️  No devices discovered")
            
        except Exception as e:
            logger.error(f"Error checking critical issues: {e}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            # Get health from all services
            appium_health = await appium_service.health_check()
            job_health = await job_executor.get_queue_status()
            
            return {
                'system': {
                    'running': self.running,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'appium': appium_health,
                'job_executor': job_health,
                'account_warmup': {
                    'running': account_warmup_system.running
                }
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def discover_and_connect_devices(self) -> Dict[str, Any]:
        """Discover devices and attempt to connect to them"""
        try:
            logger.info("🔍 Discovering and connecting devices...")
            
            # Discover devices
            devices = await appium_service.discover_devices()
            
            results = {
                'discovered': len(devices),
                'connected': 0,
                'failed': 0,
                'devices': []
            }
            
            # Attempt to connect to each device
            for device in devices:
                try:
                    session_id = await appium_service.create_session(device['udid'])
                    if session_id:
                        results['connected'] += 1
                        device['connection_status'] = 'connected'
                        logger.info(f"✅ Connected to {device['name']}")
                    else:
                        results['failed'] += 1
                        device['connection_status'] = 'failed'
                        logger.warning(f"❌ Failed to connect to {device['name']}")
                except Exception as e:
                    results['failed'] += 1
                    device['connection_status'] = 'error'
                    device['error'] = str(e)
                    logger.error(f"❌ Error connecting to {device['name']}: {e}")
                
                results['devices'].append(device)
            
            logger.info(f"🔍 Device discovery complete: {results['connected']}/{results['discovered']} connected")
            return results
            
        except Exception as e:
            logger.error(f"Error discovering devices: {e}")
            return {'error': str(e)}
    
    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a specific service"""
        try:
            logger.info(f"🔄 Restarting {service_name}...")
            
            if service_name == 'job_executor':
                await job_executor.stop()
                await asyncio.sleep(2)
                await job_executor.start()
                
            elif service_name == 'account_warmup':
                await account_warmup_system.stop()
                await asyncio.sleep(2)
                await account_warmup_system.start()
                
            elif service_name == 'appium':
                # Restart Appium server
                appium_started = await appium_service.start_appium_server()
                if not appium_started:
                    return {'success': False, 'message': 'Failed to restart Appium server'}
                
            else:
                return {'success': False, 'message': f'Unknown service: {service_name}'}
            
            logger.info(f"✅ {service_name} restarted successfully")
            return {'success': True, 'message': f'{service_name} restarted'}
            
        except Exception as e:
            logger.error(f"Error restarting {service_name}: {e}")
            return {'success': False, 'message': str(e)}
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            from database.connection import get_db
            from models.job import Job
            from models.account import Account
            from models.device import Device
            from sqlalchemy import select, func
            
            from database.connection import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                # Job statistics
                job_stats = await session.execute(
                    select(Job.status, func.count(Job.id))
                    .group_by(Job.status)
                )
                job_counts = dict(job_stats.fetchall())
                
                # Account statistics
                account_stats = await session.execute(
                    select(Account.warmup_phase, func.count(Account.id))
                    .group_by(Account.warmup_phase)
                )
                account_counts = dict(account_stats.fetchall())
                
                # Device statistics
                device_stats = await session.execute(
                    select(Device.status, func.count(Device.id))
                    .group_by(Device.status)
                )
                device_counts = dict(device_stats.fetchall())
                
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'system_running': self.running,
                    'jobs': job_counts,
                    'accounts': account_counts,
                    'devices': device_counts,
                    'active_sessions': len(appium_service.active_sessions),
                    'queue_size': job_executor.job_queue.qsize() if hasattr(job_executor, 'job_queue') else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {'error': str(e)}


# Global instance
system_manager = SystemManager()
