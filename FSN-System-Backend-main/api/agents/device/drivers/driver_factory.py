"""
Driver Factory
Capability-based driver selection and initialization
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from .base_driver import BaseDriver
from .jb_driver import JBDriver
from .nonjb_driver import NonJBDriver
from ..fsm.context import DeviceCapabilities

logger = logging.getLogger(__name__)


class DriverFactory:
    """
    Factory for creating appropriate drivers based on device capabilities
    Handles capability detection and driver selection
    """
    
    @staticmethod
    async def detect_device_capabilities(device_udid: str) -> DeviceCapabilities:
        """
        Detect device capabilities at runtime
        Returns DeviceCapabilities object with detected features
        """
        logger.info(f"Detecting capabilities for device {device_udid}")
        
        capabilities = DeviceCapabilities()
        
        try:
            # Always assume basic UI automation is available
            capabilities.ui_automation = True
            
            # Test for Frida daemon
            capabilities.frida = await DriverFactory._test_frida_daemon(device_udid)
            if capabilities.frida:
                capabilities.fast_scrape = True  # Frida enables fast scraping
                capabilities.frida_version = await DriverFactory._get_frida_version(device_udid)
            
            # Test for custom tweaks
            capabilities.tweak_integration = await DriverFactory._test_tweak_installed(device_udid)
            if capabilities.tweak_integration:
                capabilities.tweak_version = await DriverFactory._get_tweak_version(device_udid)
            
            # Performance benchmarking
            capabilities.performance_score = await DriverFactory._benchmark_device(device_udid)
            
            logger.info(f"Device capabilities detected: {capabilities.__dict__}")
            return capabilities
            
        except Exception as e:
            logger.error(f"Error detecting capabilities: {e}")
            # Return minimal capabilities on error
            return DeviceCapabilities()
    
    @staticmethod
    async def create_driver(device_udid: str, capabilities: Optional[DeviceCapabilities] = None) -> BaseDriver:
        """
        Create appropriate driver based on device capabilities
        """
        if capabilities is None:
            capabilities = await DriverFactory.detect_device_capabilities(device_udid)
        
        # Select driver type based on capabilities
        if capabilities.is_jailbroken():
            logger.info(f"Creating JB driver for device {device_udid}")
            driver = JBDriver(device_udid, capabilities)
        else:
            logger.info(f"Creating NonJB driver for device {device_udid}")
            driver = NonJBDriver(device_udid, capabilities)
        
        return driver
    
    @staticmethod
    async def create_and_connect_driver(device_udid: str, capabilities: Optional[DeviceCapabilities] = None) -> Optional[BaseDriver]:
        """
        Create driver and establish connection
        Returns None if connection fails
        """
        try:
            driver = await DriverFactory.create_driver(device_udid, capabilities)
            
            if await driver.connect():
                logger.info(f"Driver connected successfully for device {device_udid}")
                return driver
            else:
                logger.error(f"Failed to connect driver for device {device_udid}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating/connecting driver: {e}")
            return None
    
    @staticmethod
    def select_optimal_driver_type(capabilities: DeviceCapabilities, action_type: str) -> str:
        """
        Select optimal driver type based on action requirements
        Returns 'jb' or 'nonjb'
        """
        # Fast data extraction actions prefer JB when available
        fast_actions = [
            "IG_SCAN_PROFILE", "IG_GET_FOLLOWERS", "IG_GET_FOLLOWING",
            "TH_GET_POSTS", "TH_SCAN_PROFILE"
        ]
        
        if action_type in fast_actions and capabilities.fast_scrape:
            return "jb"
        
        # UI interaction actions work well with either
        ui_actions = [
            "IG_LIKE", "IG_FOLLOW", "IG_COMMENT", "IG_UNFOLLOW",
            "TH_LIKE", "TH_FOLLOW", "TH_POST", "TH_COMMENT"
        ]
        
        if action_type in ui_actions:
            # Prefer JB for performance if available and device performs well
            if capabilities.is_jailbroken() and (capabilities.performance_score or 0) > 70:
                return "jb"
            else:
                return "nonjb"  # More reliable for UI actions
        
        # Default to JB if available, NonJB otherwise
        return "jb" if capabilities.is_jailbroken() else "nonjb"
    
    # Private capability detection methods
    
    @staticmethod
    async def _test_frida_daemon(device_udid: str) -> bool:
        """Test if Frida daemon is running on device"""
        try:
            # TODO: Implement actual Frida daemon test
            # This would typically involve:
            # 1. Port forwarding to device
            # 2. HTTP request to daemon health endpoint
            # 3. Verify response
            
            logger.debug(f"Testing Frida daemon for device {device_udid}")
            
            # Placeholder implementation
            # In real implementation, this would:
            # - Use iproxy or similar to forward ports
            # - Make HTTP request to http://localhost:27042/health
            # - Return True if daemon responds
            
            return False  # Placeholder - assume no Frida for now
            
        except Exception as e:
            logger.debug(f"Frida daemon test failed: {e}")
            return False
    
    @staticmethod
    async def _get_frida_version(device_udid: str) -> Optional[str]:
        """Get Frida version from daemon"""
        try:
            # TODO: Query Frida daemon for version
            # HTTP GET to /version endpoint
            return None  # Placeholder
        except:
            return None
    
    @staticmethod
    async def _test_tweak_installed(device_udid: str) -> bool:
        """Test if custom tweaks are installed"""
        try:
            # TODO: Test for custom Instagram/Threads tweaks
            # This might involve:
            # - File system checks
            # - Process checks
            # - Custom API endpoints
            
            return False  # Placeholder
        except:
            return False
    
    @staticmethod
    async def _get_tweak_version(device_udid: str) -> Optional[str]:
        """Get custom tweak version"""
        try:
            # TODO: Query tweak version
            return None  # Placeholder
        except:
            return None
    
    @staticmethod
    async def _benchmark_device(device_udid: str) -> Optional[int]:
        """
        Benchmark device performance
        Returns score 0-100 (higher is better)
        """
        try:
            # TODO: Implement device performance benchmarking
            # This could include:
            # - Response time tests
            # - Memory usage checks
            # - CPU performance tests
            # - Network latency tests
            
            # Placeholder - return moderate performance score
            return 75
            
        except Exception as e:
            logger.debug(f"Device benchmarking failed: {e}")
            return None


class DriverRegistry:
    """
    Registry to manage active drivers and their lifecycle
    """
    
    def __init__(self):
        self.active_drivers: Dict[str, BaseDriver] = {}
        self.driver_stats: Dict[str, Dict[str, Any]] = {}
    
    async def get_driver(self, device_udid: str) -> Optional[BaseDriver]:
        """Get existing driver or create new one"""
        if device_udid in self.active_drivers:
            driver = self.active_drivers[device_udid]
            if driver.is_connected:
                return driver
            else:
                # Driver exists but not connected, remove it
                await self.remove_driver(device_udid)
        
        # Create new driver
        driver = await DriverFactory.create_and_connect_driver(device_udid)
        if driver:
            self.active_drivers[device_udid] = driver
            self.driver_stats[device_udid] = {
                "created_at": asyncio.get_event_loop().time(),
                "operations_count": 0,
                "errors_count": 0
            }
        
        return driver
    
    async def remove_driver(self, device_udid: str) -> None:
        """Remove and disconnect driver"""
        if device_udid in self.active_drivers:
            driver = self.active_drivers[device_udid]
            try:
                await driver.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting driver: {e}")
            
            del self.active_drivers[device_udid]
            if device_udid in self.driver_stats:
                del self.driver_stats[device_udid]
    
    async def cleanup_inactive_drivers(self) -> None:
        """Remove drivers that are no longer connected"""
        inactive_devices = []
        
        for device_udid, driver in self.active_drivers.items():
            if not driver.is_connected:
                inactive_devices.append(device_udid)
        
        for device_udid in inactive_devices:
            logger.info(f"Cleaning up inactive driver for device {device_udid}")
            await self.remove_driver(device_udid)
    
    async def disconnect_all(self) -> None:
        """Disconnect all active drivers"""
        for device_udid in list(self.active_drivers.keys()):
            await self.remove_driver(device_udid)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "active_drivers": len(self.active_drivers),
            "driver_types": {
                "jb": len([d for d in self.active_drivers.values() if isinstance(d, JBDriver)]),
                "nonjb": len([d for d in self.active_drivers.values() if isinstance(d, NonJBDriver)])
            },
            "devices": list(self.active_drivers.keys()),
            "stats": self.driver_stats
        }


# Global driver registry instance
driver_registry = DriverRegistry()
