"""
Jailbroken Device Driver
Implements device automation using Frida/daemon + WDA fallback for JB devices
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import aiohttp
import json

from .base_driver import BaseDriver
from ..fsm.context import Platform, DeviceCapabilities

logger = logging.getLogger(__name__)


class FridaDaemon:
    """Interface to Frida daemon running on jailbroken device"""
    
    def __init__(self, device_udid: str, daemon_port: int = 27042):
        self.device_udid = device_udid
        self.daemon_port = daemon_port
        self.base_url = f"http://localhost:{daemon_port}"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self) -> bool:
        """Connect to Frida daemon"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connection
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    logger.info(f"Connected to Frida daemon on port {self.daemon_port}")
                    return True
                else:
                    logger.error(f"Frida daemon health check failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to connect to Frida daemon: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Frida daemon"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def call(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API call to Frida daemon"""
        if not self.session:
            raise RuntimeError("Not connected to Frida daemon")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.post(url, json=params or {}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Frida daemon call failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Frida daemon call to {endpoint} failed: {e}")
            raise


class JBDriver(BaseDriver):
    """
    Jailbroken device driver with Frida/daemon integration
    Uses Frida for fast data extraction and WDA for UI navigation
    """
    
    def __init__(self, device_udid: str, capabilities: DeviceCapabilities):
        super().__init__(device_udid, capabilities)
        
        if not capabilities.frida:
            raise ValueError("JBDriver requires Frida capability")
        
        # Frida integration
        self.frida_daemon = FridaDaemon(device_udid)
        self.frida_connected = False
        
        # WDA fallback for UI operations
        self.wda_session: Optional[Any] = None  # WDA session for UI automation
        self.wda_connected = False
        
        # Hybrid execution strategy
        self.prefer_frida = True  # Try Frida first, fallback to WDA
    
    async def connect(self) -> bool:
        """Establish connection to both Frida and WDA"""
        logger.info(f"Connecting JB driver to device {self.device_udid}")
        
        # Connect to Frida daemon
        self.frida_connected = await self.frida_daemon.connect()
        if self.frida_connected:
            logger.info("Frida daemon connected successfully")
        else:
            logger.warning("Frida daemon connection failed, will use WDA only")
        
        # Connect to WDA (fallback)
        self.wda_connected = await self._connect_wda()
        if self.wda_connected:
            logger.info("WDA session connected successfully")
        else:
            logger.error("WDA connection failed")
        
        # Need at least one connection method
        self.is_connected = self.frida_connected or self.wda_connected
        
        if self.is_connected:
            logger.info(f"JB driver connected (Frida: {self.frida_connected}, WDA: {self.wda_connected})")
        
        return self.is_connected
    
    async def disconnect(self) -> None:
        """Disconnect from device"""
        logger.info("Disconnecting JB driver")
        
        if self.frida_connected:
            await self.frida_daemon.disconnect()
            self.frida_connected = False
        
        if self.wda_connected:
            await self._disconnect_wda()
            self.wda_connected = False
        
        self.is_connected = False
    
    async def _connect_wda(self) -> bool:
        """Connect to WDA session (placeholder - implement with actual WDA client)"""
        try:
            # TODO: Implement actual WDA connection
            # from appium import webdriver
            # desired_caps = {...}
            # self.wda_session = webdriver.Remote('http://localhost:8100', desired_caps)
            logger.info("WDA connection placeholder - implement with actual WDA client")
            return True
        except Exception as e:
            logger.error(f"WDA connection failed: {e}")
            return False
    
    async def _disconnect_wda(self) -> None:
        """Disconnect WDA session"""
        if self.wda_session:
            try:
                # TODO: Implement actual WDA disconnect
                # self.wda_session.quit()
                pass
            except Exception as e:
                logger.warning(f"WDA disconnect error: {e}")
            finally:
                self.wda_session = None
    
    # Fast data extraction using Frida
    
    async def fast_scan_profile(self, username: str) -> Dict[str, Any]:
        """Use Frida to directly extract Instagram profile data"""
        if not self.frida_connected:
            raise RuntimeError("Frida not connected for fast profile scan")
        
        try:
            result = await self.frida_daemon.call("/instagram/profile", {
                "username": username,
                "include_posts": True,
                "include_followers": True,
                "include_stats": True
            })
            
            logger.info(f"Fast profile scan completed for {username}")
            return result
            
        except Exception as e:
            logger.error(f"Fast profile scan failed: {e}")
            raise
    
    async def fast_get_followers(self, username: str, count: int = 100) -> List[Dict[str, Any]]:
        """Use Frida to extract follower list"""
        if not self.frida_connected:
            raise RuntimeError("Frida not connected for fast follower extraction")
        
        try:
            result = await self.frida_daemon.call("/instagram/followers", {
                "username": username,
                "count": count
            })
            
            return result.get("followers", [])
            
        except Exception as e:
            logger.error(f"Fast follower extraction failed: {e}")
            raise
    
    # UI automation methods (WDA fallback)
    
    async def is_app_installed(self, bundle_id: str) -> bool:
        """Check if app is installed"""
        if self.frida_connected:
            try:
                result = await self.frida_daemon.call("/system/app_installed", {
                    "bundle_id": bundle_id
                })
                return result.get("installed", False)
            except:
                pass
        
        # Fallback to WDA
        return await self._wda_is_app_installed(bundle_id)
    
    async def open_app(self, platform: Platform) -> bool:
        """Launch Instagram or Threads app"""
        bundle_id = self.get_platform_bundle_id(platform)
        app_name = "Instagram" if platform == Platform.INSTAGRAM else "Threads"
        
        logger.info(f"Opening {app_name} app")
        
        # Try Frida first for faster app launch
        if self.frida_connected and self.prefer_frida:
            try:
                result = await self.frida_daemon.call("/system/launch_app", {
                    "bundle_id": bundle_id
                })
                
                if result.get("success", False):
                    self.app_bundle_id = bundle_id
                    self.update_activity()
                    return True
                    
            except Exception as e:
                logger.warning(f"Frida app launch failed, falling back to WDA: {e}")
        
        # Fallback to WDA
        return await self._wda_open_app(bundle_id)
    
    async def close_app(self) -> bool:
        """Close current app"""
        if not self.app_bundle_id:
            return True
        
        # Try Frida first
        if self.frida_connected:
            try:
                result = await self.frida_daemon.call("/system/close_app", {
                    "bundle_id": self.app_bundle_id
                })
                
                if result.get("success", False):
                    self.app_bundle_id = None
                    return True
                    
            except Exception as e:
                logger.warning(f"Frida app close failed: {e}")
        
        # Fallback to WDA
        return await self._wda_close_app()
    
    async def take_screenshot(self, file_path: str) -> bool:
        """Take screenshot and save to file"""
        # Use WDA for screenshots (more reliable)
        return await self._wda_take_screenshot(file_path)
    
    async def get_page_source(self) -> str:
        """Get current page XML source"""
        return await self._wda_get_page_source()
    
    async def find_element(self, strategy: str, value: str, timeout: int = 10) -> Optional[Any]:
        """Find UI element using WDA"""
        return await self._wda_find_element(strategy, value, timeout)
    
    async def find_elements(self, strategy: str, value: str, timeout: int = 10) -> List[Any]:
        """Find multiple UI elements using WDA"""
        return await self._wda_find_elements(strategy, value, timeout)
    
    async def click_element(self, element: Any) -> bool:
        """Click on UI element using WDA"""
        return await self._wda_click_element(element)
    
    async def send_keys(self, element: Any, text: str) -> bool:
        """Send text to UI element using WDA"""
        return await self._wda_send_keys(element, text)
    
    async def scroll(self, direction: str, distance: int = 300) -> bool:
        """Scroll in specified direction using WDA"""
        return await self._wda_scroll(direction, distance)
    
    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 1000) -> bool:
        """Perform swipe gesture using WDA"""
        return await self._wda_swipe(start_x, start_y, end_x, end_y, duration)
    
    async def tap_coordinates(self, x: int, y: int) -> bool:
        """Tap at specific coordinates using WDA"""
        return await self._wda_tap_coordinates(x, y)
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        info = {
            "udid": self.device_udid,
            "driver_type": "jb",
            "frida_connected": self.frida_connected,
            "wda_connected": self.wda_connected,
            "capabilities": self.capabilities.__dict__
        }
        
        # Try to get additional info from Frida
        if self.frida_connected:
            try:
                frida_info = await self.frida_daemon.call("/system/device_info")
                info.update(frida_info)
            except:
                pass
        
        return info
    
    # WDA fallback methods (placeholders - implement with actual WDA client)
    
    async def _wda_is_app_installed(self, bundle_id: str) -> bool:
        """WDA app installation check"""
        # TODO: Implement with actual WDA
        return True
    
    async def _wda_open_app(self, bundle_id: str) -> bool:
        """WDA app launch"""
        # TODO: Implement with actual WDA
        self.app_bundle_id = bundle_id
        self.update_activity()
        return True
    
    async def _wda_close_app(self) -> bool:
        """WDA app close"""
        # TODO: Implement with actual WDA
        self.app_bundle_id = None
        return True
    
    async def _wda_take_screenshot(self, file_path: str) -> bool:
        """WDA screenshot"""
        # TODO: Implement with actual WDA
        self.update_activity()
        return True
    
    async def _wda_get_page_source(self) -> str:
        """WDA page source"""
        # TODO: Implement with actual WDA
        return "<xml>placeholder</xml>"
    
    async def _wda_find_element(self, strategy: str, value: str, timeout: int) -> Optional[Any]:
        """WDA element finding"""
        # TODO: Implement with actual WDA
        self.update_activity()
        return None
    
    async def _wda_find_elements(self, strategy: str, value: str, timeout: int) -> List[Any]:
        """WDA multiple elements finding"""
        # TODO: Implement with actual WDA
        return []
    
    async def _wda_click_element(self, element: Any) -> bool:
        """WDA element click"""
        # TODO: Implement with actual WDA
        self.update_activity()
        return True
    
    async def _wda_send_keys(self, element: Any, text: str) -> bool:
        """WDA send keys"""
        # TODO: Implement with actual WDA
        self.update_activity()
        return True
    
    async def _wda_scroll(self, direction: str, distance: int) -> bool:
        """WDA scroll"""
        # TODO: Implement with actual WDA
        self.update_activity()
        return True
    
    async def _wda_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int) -> bool:
        """WDA swipe"""
        # TODO: Implement with actual WDA
        self.update_activity()
        return True
    
    async def _wda_tap_coordinates(self, x: int, y: int) -> bool:
        """WDA tap coordinates"""
        # TODO: Implement with actual WDA
        self.update_activity()
        return True
