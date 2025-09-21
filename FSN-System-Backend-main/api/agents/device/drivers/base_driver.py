"""
Base Driver Interface
Abstract interface for device automation drivers (JB and Non-JB)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..fsm.context import Platform, DeviceCapabilities

logger = logging.getLogger(__name__)


class BaseDriver(ABC):
    """
    Abstract base class for device automation drivers
    Defines the interface that both JB and Non-JB drivers must implement
    """
    
    def __init__(self, device_udid: str, capabilities: DeviceCapabilities):
        self.device_udid = device_udid
        self.capabilities = capabilities
        self.is_connected = False
        self.last_activity = datetime.utcnow()
        
        # Session management
        self.session_id: Optional[str] = None
        self.app_bundle_id: Optional[str] = None
        
        # Performance tracking
        self.operations_count = 0
        self.errors_count = 0
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to device"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from device"""
        pass
    
    @abstractmethod
    async def is_app_installed(self, bundle_id: str) -> bool:
        """Check if app is installed on device"""
        pass
    
    @abstractmethod
    async def open_app(self, platform: Platform) -> bool:
        """Launch Instagram or Threads app"""
        pass
    
    @abstractmethod
    async def close_app(self) -> bool:
        """Close current app"""
        pass
    
    @abstractmethod
    async def take_screenshot(self, file_path: str) -> bool:
        """Take screenshot and save to file"""
        pass
    
    @abstractmethod
    async def get_page_source(self) -> str:
        """Get current page XML source"""
        pass
    
    @abstractmethod
    async def find_element(self, strategy: str, value: str, timeout: int = 10) -> Optional[Any]:
        """Find UI element using specified strategy"""
        pass
    
    @abstractmethod
    async def find_elements(self, strategy: str, value: str, timeout: int = 10) -> List[Any]:
        """Find multiple UI elements"""
        pass
    
    @abstractmethod
    async def click_element(self, element: Any) -> bool:
        """Click on UI element"""
        pass
    
    @abstractmethod
    async def send_keys(self, element: Any, text: str) -> bool:
        """Send text to UI element"""
        pass
    
    @abstractmethod
    async def scroll(self, direction: str, distance: int = 300) -> bool:
        """Scroll in specified direction"""
        pass
    
    @abstractmethod
    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 1000) -> bool:
        """Perform swipe gesture"""
        pass
    
    @abstractmethod
    async def tap_coordinates(self, x: int, y: int) -> bool:
        """Tap at specific coordinates"""
        pass
    
    @abstractmethod
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        pass
    
    # Common functionality (implemented in base class)
    
    async def wait_for_element(self, strategy: str, value: str, timeout: int = 10) -> Optional[Any]:
        """Wait for element to appear"""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            element = await self.find_element(strategy, value, timeout=1)
            if element:
                return element
            await asyncio.sleep(0.5)
        
        return None
    
    async def wait_for_element_to_disappear(self, strategy: str, value: str, timeout: int = 10) -> bool:
        """Wait for element to disappear"""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            element = await self.find_element(strategy, value, timeout=1)
            if not element:
                return True
            await asyncio.sleep(0.5)
        
        return False
    
    async def is_element_present(self, strategy: str, value: str) -> bool:
        """Check if element is present"""
        element = await self.find_element(strategy, value, timeout=1)
        return element is not None
    
    def get_platform_bundle_id(self, platform: Platform) -> str:
        """Get app bundle ID for platform"""
        if platform == Platform.INSTAGRAM:
            return "com.burbn.instagram"
        elif platform == Platform.THREADS:
            return "com.instagram.barcelona"
        else:
            raise ValueError(f"Unknown platform: {platform}")
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        self.operations_count += 1
    
    def record_error(self) -> None:
        """Record an error occurrence"""
        self.errors_count += 1
        logger.warning(f"Driver error count: {self.errors_count}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get driver performance statistics"""
        uptime = (datetime.utcnow() - self.last_activity).total_seconds()
        
        return {
            "device_udid": self.device_udid,
            "driver_type": self.__class__.__name__,
            "is_connected": self.is_connected,
            "session_id": self.session_id,
            "operations_count": self.operations_count,
            "errors_count": self.errors_count,
            "error_rate": self.errors_count / max(self.operations_count, 1),
            "uptime_seconds": uptime,
            "capabilities": {
                "jailbroken": self.capabilities.is_jailbroken(),
                "frida": self.capabilities.frida,
                "fast_scrape": self.capabilities.fast_scrape,
                "ui_automation": self.capabilities.ui_automation
            }
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(udid={self.device_udid}, connected={self.is_connected})"
