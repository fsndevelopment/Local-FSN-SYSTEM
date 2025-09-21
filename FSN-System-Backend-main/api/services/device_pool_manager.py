"""
Multi-Device Pool Manager
Handles device discovery, allocation, load balancing, and health monitoring for scaling across multiple iPhones
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from collections import defaultdict, deque
import statistics

from database.connection import AsyncSessionLocal
from models.device import Device
from models.job import Job, JobStatus, JobType
from .appium_service import appium_service
from .websocket_manager import websocket_service

logger = logging.getLogger(__name__)

class DevicePoolStatus(str, Enum):
    """Device pool status tracking"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"

class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies for job distribution"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PERFORMANCE_BASED = "performance_based"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"

class DeviceMetrics:
    """Real-time device performance metrics"""
    
    def __init__(self, device_udid: str):
        self.device_udid = device_udid
        self.active_jobs = 0
        self.completed_jobs = 0
        self.failed_jobs = 0
        self.last_job_time = None
        self.average_execution_time = 0.0
        self.success_rate = 1.0
        self.health_score = 1.0
        self.consecutive_failures = 0
        self.last_health_check = datetime.utcnow()
        
        # Performance tracking
        self.execution_times = deque(maxlen=10)  # Last 10 execution times
        self.recent_errors = deque(maxlen=5)     # Last 5 errors
        
    def update_job_completion(self, execution_time: float, success: bool):
        """Update metrics after job completion"""
        if success:
            self.completed_jobs += 1
            self.consecutive_failures = 0
            self.execution_times.append(execution_time)
            if self.execution_times:
                self.average_execution_time = statistics.mean(self.execution_times)
        else:
            self.failed_jobs += 1
            self.consecutive_failures += 1
            
        self.last_job_time = datetime.utcnow()
        self._calculate_success_rate()
        self._calculate_health_score()
        
    def start_job(self):
        """Track job start"""
        self.active_jobs += 1
        
    def finish_job(self):
        """Track job finish"""
        self.active_jobs = max(0, self.active_jobs - 1)
        
    def add_error(self, error: str):
        """Track recent errors"""
        self.recent_errors.append({
            'error': error,
            'timestamp': datetime.utcnow()
        })
        
    def _calculate_success_rate(self):
        """Calculate success rate based on recent performance"""
        total_jobs = self.completed_jobs + self.failed_jobs
        if total_jobs == 0:
            self.success_rate = 1.0
        else:
            self.success_rate = self.completed_jobs / total_jobs
            
    def _calculate_health_score(self):
        """Calculate overall device health score (0.0 - 1.0)"""
        factors = []
        
        # Success rate factor (0.5 weight)
        factors.append(self.success_rate * 0.5)
        
        # Consecutive failures penalty (0.2 weight)
        failure_penalty = max(0, 1.0 - (self.consecutive_failures * 0.1))
        factors.append(failure_penalty * 0.2)
        
        # Load factor (0.2 weight) - prefer less loaded devices
        load_factor = max(0, 1.0 - (self.active_jobs * 0.2))
        factors.append(load_factor * 0.2)
        
        # Responsiveness factor (0.1 weight)
        if self.average_execution_time > 0:
            # Normalize execution time (assume 30s is baseline)
            responsiveness = max(0, 1.0 - ((self.average_execution_time - 30) / 60))
            factors.append(responsiveness * 0.1)
        else:
            factors.append(0.1)  # Default for new devices
            
        self.health_score = sum(factors)
        
    def is_healthy(self) -> bool:
        """Check if device is considered healthy"""
        return (self.health_score > 0.6 and 
                self.consecutive_failures < 3 and
                self.active_jobs < 5)  # Max concurrent jobs per device

class DevicePoolManager:
    """Manages multiple devices for concurrent Instagram automation"""
    
    def __init__(self):
        self.device_metrics: Dict[str, DeviceMetrics] = {}
        self.load_balancing_strategy = LoadBalancingStrategy.PERFORMANCE_BASED
        self.round_robin_index = 0
        self.last_discovery = None
        self.discovery_interval = timedelta(minutes=5)  # Rediscover every 5 minutes
        self.health_check_interval = timedelta(minutes=2)  # Health check every 2 minutes
        
        # Device pool configuration
        self.max_jobs_per_device = 3  # Conservative limit for iPhone stability
        self.min_healthy_devices = 1  # Minimum devices needed for operation
        
    async def initialize(self):
        """Initialize device pool manager"""
        logger.info("🏊‍♂️ Initializing Device Pool Manager...")
        
        # Discover and register devices
        await self.discover_and_register_devices()
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor_loop())
        
        logger.info(f"✅ Device Pool Manager initialized with {len(self.device_metrics)} devices")
        
    async def discover_and_register_devices(self) -> Dict[str, Any]:
        """Discover devices and register them in the pool"""
        try:
            # Discover physical devices
            discovered_devices = await appium_service.discover_devices()
            
            async with AsyncSessionLocal() as db:
                registration_results = {
                    'discovered': len(discovered_devices),
                    'registered': 0,
                    'updated': 0,
                    'devices': []
                }
                
                for device_info in discovered_devices:
                    udid = device_info['udid']
                    
                    # Check if device already exists in database
                    result = await db.execute(
                        select(Device).where(Device.udid == udid)
                    )
                    existing_device = result.scalar_one_or_none()
                    
                    if existing_device:
                        # Update existing device
                        await db.execute(
                            update(Device).where(Device.udid == udid).values(
                                name=device_info['name'],
                                ios_version=device_info.get('os_version'),
                                model=device_info.get('capabilities', {}).get('DeviceName', 'iPhone'),
                                status='connected',
                                last_seen=datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                        )
                        registration_results['updated'] += 1
                        device_id = existing_device.id
                    else:
                        # Create new device with auto-assigned ports
                        port_offset = registration_results['registered']
                        new_device = Device(
                            name=device_info['name'],
                            udid=udid,
                            ios_version=device_info.get('os_version'),
                            model=device_info.get('capabilities', {}).get('DeviceName', 'iPhone'),
                            appium_port=4723 + port_offset,
                            wda_port=8100 + port_offset,
                            mjpeg_port=9100 + port_offset,
                            status='connected',
                            settings={'jailbroken': device_info.get('jailbroken', True)}
                        )
                        db.add(new_device)
                        await db.flush()
                        registration_results['registered'] += 1
                        device_id = new_device.id
                    
                    # Initialize device metrics if not exists
                    if udid not in self.device_metrics:
                        self.device_metrics[udid] = DeviceMetrics(udid)
                    
                    registration_results['devices'].append({
                        'id': device_id,
                        'udid': udid,
                        'name': device_info['name'],
                        'platform': device_info['platform'],
                        'os_version': device_info.get('os_version'),
                        'status': 'connected',
                        'health_score': self.device_metrics[udid].health_score
                    })
                
                await db.commit()
                self.last_discovery = datetime.utcnow()
                
                logger.info(f"📱 Device registration complete: {registration_results['registered']} new, {registration_results['updated']} updated")
                return registration_results
                
        except Exception as e:
            logger.error(f"Error discovering/registering devices: {e}")
            return {'error': str(e)}
    
    async def assign_optimal_device(self, job_priority: str = "normal") -> Optional[str]:
        """Assign the optimal device for a job based on load balancing strategy"""
        try:
            available_devices = await self.get_available_devices()
            
            if not available_devices:
                logger.warning("⚠️ No available devices for job assignment")
                return None
            
            # Filter healthy devices
            healthy_devices = [
                udid for udid in available_devices 
                if self.device_metrics[udid].is_healthy()
            ]
            
            if not healthy_devices:
                logger.warning("⚠️ No healthy devices available, using degraded devices")
                healthy_devices = available_devices[:1]  # Use least loaded even if unhealthy
            
            # Apply load balancing strategy
            if self.load_balancing_strategy == LoadBalancingStrategy.PERFORMANCE_BASED:
                selected_udid = self._select_by_performance(healthy_devices)
            elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_LOADED:
                selected_udid = self._select_least_loaded(healthy_devices)
            elif self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
                selected_udid = self._select_round_robin(healthy_devices)
            else:
                selected_udid = healthy_devices[0]  # Default fallback
            
            if selected_udid:
                self.device_metrics[selected_udid].start_job()
                logger.info(f"📱 Assigned device {selected_udid[:8]}... for job (strategy: {self.load_balancing_strategy})")
            
            return selected_udid
            
        except Exception as e:
            logger.error(f"Error assigning device: {e}")
            return None
    
    def _select_by_performance(self, devices: List[str]) -> str:
        """Select device based on performance metrics"""
        if not devices:
            return None
            
        # Sort by health score (highest first), then by load (lowest first)
        scored_devices = [
            (udid, self.device_metrics[udid].health_score, self.device_metrics[udid].active_jobs)
            for udid in devices
        ]
        scored_devices.sort(key=lambda x: (-x[1], x[2]))  # High health, low load
        
        return scored_devices[0][0]
    
    def _select_least_loaded(self, devices: List[str]) -> str:
        """Select device with least active jobs"""
        if not devices:
            return None
            
        return min(devices, key=lambda udid: self.device_metrics[udid].active_jobs)
    
    def _select_round_robin(self, devices: List[str]) -> str:
        """Select device using round-robin"""
        if not devices:
            return None
            
        device = devices[self.round_robin_index % len(devices)]
        self.round_robin_index += 1
        return device
    
    async def get_available_devices(self) -> List[str]:
        """Get list of available device UDIDs"""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Device.udid).where(
                        Device.status.in_(['connected', 'active'])
                    )
                )
                udids = [row[0] for row in result.all()]
                
                # Filter by capacity
                available = [
                    udid for udid in udids 
                    if udid in self.device_metrics and 
                       self.device_metrics[udid].active_jobs < self.max_jobs_per_device
                ]
                
                return available
                
        except Exception as e:
            logger.error(f"Error getting available devices: {e}")
            return []
    
    async def release_device(self, device_udid: str, job_success: bool, execution_time: float = 0.0, error_message: str = None):
        """Release device after job completion"""
        try:
            if device_udid in self.device_metrics:
                metrics = self.device_metrics[device_udid]
                metrics.finish_job()
                metrics.update_job_completion(execution_time, job_success)
                
                if not job_success and error_message:
                    metrics.add_error(error_message)
                
                logger.info(f"📱 Released device {device_udid[:8]}... (success: {job_success}, health: {metrics.health_score:.2f})")
        
        except Exception as e:
            logger.error(f"Error releasing device {device_udid}: {e}")
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get comprehensive device pool status"""
        try:
            async with AsyncSessionLocal() as db:
                # Get device count by status
                result = await db.execute(
                    select(Device.status, Device.udid, Device.name, Device.last_seen)
                )
                devices = result.all()
                
                status_counts = defaultdict(int)
                device_details = []
                
                total_active_jobs = 0
                total_health_score = 0
                healthy_devices = 0
                
                for status, udid, name, last_seen in devices:
                    status_counts[status] += 1
                    
                    metrics = self.device_metrics.get(udid)
                    if metrics:
                        device_details.append({
                            'udid': udid,
                            'name': name,
                            'status': status,
                            'active_jobs': metrics.active_jobs,
                            'health_score': metrics.health_score,
                            'success_rate': metrics.success_rate,
                            'last_seen': last_seen.isoformat() if last_seen else None,
                            'is_healthy': metrics.is_healthy()
                        })
                        
                        total_active_jobs += metrics.active_jobs
                        total_health_score += metrics.health_score
                        
                        if metrics.is_healthy():
                            healthy_devices += 1
                
                # Determine overall pool status
                if healthy_devices == 0:
                    pool_status = DevicePoolStatus.OFFLINE
                elif healthy_devices < self.min_healthy_devices:
                    pool_status = DevicePoolStatus.CRITICAL
                elif healthy_devices < len(device_details) * 0.5:
                    pool_status = DevicePoolStatus.DEGRADED
                else:
                    pool_status = DevicePoolStatus.HEALTHY
                
                average_health = total_health_score / len(device_details) if device_details else 0
                
                return {
                    'pool_status': pool_status,
                    'total_devices': len(device_details),
                    'healthy_devices': healthy_devices,
                    'total_active_jobs': total_active_jobs,
                    'average_health_score': average_health,
                    'load_balancing_strategy': self.load_balancing_strategy,
                    'status_breakdown': dict(status_counts),
                    'devices': device_details,
                    'last_discovery': self.last_discovery.isoformat() if self.last_discovery else None
                }
                
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {'error': str(e)}
    
    async def _health_monitor_loop(self):
        """Background task for device health monitoring"""
        logger.info("🏥 Starting device health monitor...")
        
        while True:
            try:
                await asyncio.sleep(self.health_check_interval.total_seconds())
                await self._perform_health_checks()
                
                # Auto-rediscover devices if needed
                if (self.last_discovery is None or 
                    datetime.utcnow() - self.last_discovery > self.discovery_interval):
                    await self.discover_and_register_devices()
                    
            except asyncio.CancelledError:
                logger.info("🏥 Health monitor stopped")
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all devices"""
        try:
            async with AsyncSessionLocal() as db:
                for udid, metrics in self.device_metrics.items():
                    # Check device responsiveness
                    if udid in appium_service.active_sessions:
                        # Device has active session, mark as healthy
                        metrics.last_health_check = datetime.utcnow()
                    else:
                        # Check if device is still physically connected
                        discovered = await appium_service.discover_devices()
                        device_found = any(d['udid'] == udid for d in discovered)
                        
                        if device_found:
                            # Get device info first
                            device_result = await db.execute(select(Device).where(Device.udid == udid))
                            device = device_result.scalar_one_or_none()
                            
                            if device:
                                # Update database status
                                await db.execute(
                                    update(Device).where(Device.udid == udid).values(
                                        status='connected',
                                        last_seen=datetime.utcnow()
                                    )
                                )
                                
                                # Notify WebSocket clients about device status change
                                try:
                                    await websocket_service.notify_device_status_change(
                                        device_id=device.id,
                                        old_status='offline',
                                        new_status='connected',
                                        details={'udid': udid, 'name': device.name}
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send WebSocket notification for device {udid}: {e}")
                        else:
                            # Get device info first
                            device_result = await db.execute(select(Device).where(Device.udid == udid))
                            device = device_result.scalar_one_or_none()
                            
                            if device:
                                # Mark as offline
                                await db.execute(
                                    update(Device).where(Device.udid == udid).values(
                                        status='offline',
                                        updated_at=datetime.utcnow()
                                    )
                                )
                                
                                # Notify WebSocket clients about device status change
                                try:
                                    await websocket_service.notify_device_status_change(
                                        device_id=device.id,
                                        old_status='connected',
                                        new_status='offline',
                                        details={'udid': udid, 'name': device.name}
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send WebSocket notification for device {udid}: {e}")
                                logger.warning(f"📱 Device {udid[:8]}... marked as offline")
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")

# Global instance
device_pool_manager = DevicePoolManager()