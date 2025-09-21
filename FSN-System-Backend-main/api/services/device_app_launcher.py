"""
Device App Launcher Service
Handles app launching for both JB (jailbroken) and NONJB (non-jailbroken) devices
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .crane_account_switching import CraneAccountSwitching

logger = logging.getLogger(__name__)

class DeviceAppLauncher:
    """
    Handles app launching for different device types
    - JB devices: Uses Crane container switching before app launch
    - NONJB devices: Direct app launch
    """
    
    def __init__(self):
        self.crane_switcher = CraneAccountSwitching()
        self.platform_app_names = {
            "instagram": "Instagram",
            "threads": "Threads"
        }
        self.platform_bundle_ids = {
            "instagram": "com.burbn.instagram",
            "threads": "com.instagram.barcelona"
        }
    
    async def launch_app_for_session(
        self, 
        device_udid: str, 
        platform: str, 
        device_type: str, 
        container_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Launch app for a session based on device type
        
        Args:
            device_udid: Device UDID
            platform: Platform name ('instagram' or 'threads')
            device_type: Device type ('jailbroken' or 'non_jailbroken')
            container_id: Container ID for JB devices
            
        Returns:
            Dict with success status and data
        """
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            # Add overall timeout to prevent hanging
            if device_type == "jailbroken":
                # JB Device: Use Crane container switching
                if not container_id:
                    result['message'] = "Container ID required for jailbroken devices"
                    return result
                
                logger.info(f"🔧 Launching {platform} with Crane container {container_id} on JB device {device_udid}")
                result = await asyncio.wait_for(
                    self._launch_app_with_crane(device_udid, platform, container_id),
                    timeout=120  # 2 minute timeout for Crane operations
                )
                
            else:
                # NONJB Device: Direct app launch
                logger.info(f"📱 Launching {platform} directly on NONJB device {device_udid}")
                result = await asyncio.wait_for(
                    self._launch_app_directly(device_udid, platform),
                    timeout=60  # 1 minute timeout for direct launch
                )
            
            return result
            
        except asyncio.TimeoutError:
            result['message'] = f"App launch timed out after 60-120 seconds"
            logger.error(f"App launch timeout on {device_udid}")
            return result
        except Exception as e:
            result['message'] = f"App launch error: {str(e)}"
            logger.error(f"App launch error on {device_udid}: {e}")
            return result
    
    async def _launch_app_with_crane(
        self, 
        device_udid: str, 
        platform: str, 
        container_id: str
    ) -> Dict[str, Any]:
        """
        Launch app using Crane container switching for JB devices
        """
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            # Use the existing Crane account switching service
            crane_result = await self.crane_switcher.complete_crane_account_switch_flow(
                device_udid, 
                container_id, 
                platform
            )
            
            if crane_result['success']:
                result['success'] = True
                result['message'] = f"Successfully launched {platform} with container {container_id}"
                result['data'] = crane_result['data']
                logger.info(f"✅ Crane app launch successful: {platform} -> container {container_id}")
            else:
                result['message'] = f"Crane app launch failed: {crane_result['message']}"
                logger.error(f"❌ Crane app launch failed: {crane_result['message']}")
            
            return result
            
        except Exception as e:
            result['message'] = f"Crane app launch error: {str(e)}"
            logger.error(f"Crane app launch error on {device_udid}: {e}")
            return result
    
    async def _launch_app_directly(
        self, 
        device_udid: str, 
        platform: str
    ) -> Dict[str, Any]:
        """
        Launch app directly for NONJB devices
        """
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            # Get driver from appium service (assuming it exists)
            from .appium_service import appium_service
            
            if device_udid not in appium_service.active_sessions:
                result['message'] = f"No active session for device {device_udid}"
                return result
            
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, 30)  # Increased timeout
            
            # Navigate to home screen first
            await self._navigate_to_home_screen(driver)
            
            # Launch app using direct icon click
            app_name = self.platform_app_names[platform]
            logger.info(f"🔍 Looking for {app_name} icon on NONJB device...")
            
            # Find app icon
            icon_element = await self._find_app_icon(driver, wait, app_name)
            if not icon_element:
                result['message'] = f"Could not find {app_name} icon"
                return result
            
            # Click app icon
            logger.info(f"👆 Clicking {app_name} icon...")
            icon_element.click()
            await asyncio.sleep(8)  # Increased wait time for app to load
            
            # Verify app launched
            if await self._verify_app_launched(driver, platform):
                result['success'] = True
                result['message'] = f"Successfully launched {platform} directly"
                logger.info(f"✅ Direct app launch successful: {platform}")
            else:
                result['message'] = f"Failed to verify {platform} launch"
                logger.error(f"❌ Failed to verify {platform} launch")
            
            return result
            
        except Exception as e:
            result['message'] = f"Direct app launch error: {str(e)}"
            logger.error(f"Direct app launch error on {device_udid}: {e}")
            return result
    
    async def _navigate_to_home_screen(self, driver) -> bool:
        """Navigate to iOS home screen"""
        try:
            # Press home button to go to home screen
            driver.press_keycode(3)  # Home button keycode
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to home screen: {e}")
            return False
    
    async def _find_app_icon(self, driver, wait, app_name: str):
        """Find app icon using multiple selector strategies"""
        selectors = [
            (AppiumBy.ACCESSIBILITY_ID, app_name),
            (AppiumBy.IOS_CLASS_CHAIN, f"**/XCUIElementTypeIcon[`name == \"{app_name}\"`]"),
            (AppiumBy.IOS_PREDICATE, f"name == \"{app_name}\""),
            (By.XPATH, f"//XCUIElementTypeIcon[@name='{app_name}']")
        ]
        
        for by_type, selector in selectors:
            try:
                # Use shorter timeout for each selector attempt
                short_wait = WebDriverWait(driver, 10)
                icon_element = short_wait.until(EC.element_to_be_clickable((by_type, selector)))
                logger.info(f"✅ Found {app_name} icon with selector: {by_type}")
                return icon_element
            except TimeoutException:
                logger.debug(f"❌ Selector failed: {by_type} = {selector}")
                continue
        
        logger.error(f"❌ Could not find {app_name} icon with any selector")
        return None
    
    async def _verify_app_launched(self, driver, platform: str) -> bool:
        """Verify that the app launched successfully"""
        try:
            if platform == "threads":
                # Look for Threads-specific elements
                verification_selectors = [
                    "Threads-lockup",
                    "feed-tab-main",
                    "create-tab"
                ]
            else:  # instagram
                # Look for Instagram-specific elements
                verification_selectors = [
                    "Instagram-lockup",
                    "feed-tab-main",
                    "camera-tab"
                ]
            
            for selector in verification_selectors:
                try:
                    element = driver.find_element(AppiumBy.ACCESSIBILITY_ID, selector)
                    if element.is_displayed():
                        logger.info(f"✅ App verification successful: found {selector}")
                        return True
                except NoSuchElementException:
                    continue
            
            logger.warning("⚠️ Could not verify app launch with standard selectors")
            return False
            
        except Exception as e:
            logger.error(f"App verification error: {e}")
            return False
    
    async def close_app(self, device_udid: str, platform: str) -> Dict[str, Any]:
        """
        Close the app after session completion
        """
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            from .appium_service import appium_service
            
            if device_udid not in appium_service.active_sessions:
                result['message'] = f"No active session for device {device_udid}"
                return result
            
            driver = appium_service.active_sessions[device_udid]
            
            # Add timeout for app closing
            await asyncio.wait_for(self._close_app_operations(driver, platform), timeout=30)
            
            result['success'] = True
            result['message'] = f"Successfully closed {platform}"
            logger.info(f"✅ App closed successfully: {platform}")
            
            return result
            
        except asyncio.TimeoutError:
            result['message'] = f"App close timed out after 30 seconds"
            logger.error(f"App close timeout on {device_udid}")
            return result
        except Exception as e:
            result['message'] = f"App close error: {str(e)}"
            logger.error(f"App close error on {device_udid}: {e}")
            return result
    
    async def _close_app_operations(self, driver, platform: str):
        """Internal method for app closing operations"""
        # Close app by pressing home button and then using app switcher
        driver.press_keycode(3)  # Home button
        await asyncio.sleep(1)
        
        # Optional: Force close app using appium
        bundle_id = self.platform_bundle_ids[platform]
        driver.terminate_app(bundle_id)
        await asyncio.sleep(2)

# Create singleton instance
device_app_launcher = DeviceAppLauncher()
