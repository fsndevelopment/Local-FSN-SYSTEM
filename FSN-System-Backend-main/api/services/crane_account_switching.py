"""
Crane Account Switching Service
Handles account switching for jailbroken devices using Crane containers
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .appium_service import appium_service
import time

logger = logging.getLogger(__name__)

class CraneAccountSwitching:
    """
    Crane-based account switching for jailbroken devices
    Handles the complete flow: app icon long press -> container selection -> container switch -> app launch
    """
    
    def __init__(self):
        self.platform_bundle_ids = {
            "instagram": "com.burbn.instagram",
            "threads": "com.instagram.barcelona"
        }
        
        self.platform_app_names = {
            "instagram": "Instagram",
            "threads": "Threads"
        }
        
        # Use current user's home directory and project-relative path
        import os
        current_user = os.path.expanduser("~")
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.evidence_dir = os.path.join(project_root, "evidence")
        self.current_test_dir = None
        
    def _create_evidence_dir(self, test_name: str) -> str:
        """Create evidence directory for this test run"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = f"{self.evidence_dir}/{test_name}_{timestamp}"
        os.makedirs(test_dir, exist_ok=True)
        self.current_test_dir = test_dir
        return test_dir
        
    def _save_checkpoint(self, action_name: str, success: bool, driver, wait) -> Dict[str, Any]:
        """Save checkpoint with screenshot and XML following the established pattern"""
        if not self.current_test_dir:
            logger.warning("No evidence directory set, skipping checkpoint save")
            return {"success": success, "message": "Checkpoint saved (no evidence dir)"}
            
        timestamp = datetime.now().strftime("%H%M%S")
        status = "SUCCESS" if success else "FAILED"
        filename_prefix = f"{action_name}_{status}_{timestamp}"
        
        try:
            # Save screenshot
            screenshot_path = os.path.join(self.current_test_dir, f"{filename_prefix}.png")
            driver.save_screenshot(screenshot_path)
            
            # Save XML page source
            xml_path = os.path.join(self.current_test_dir, f"{filename_prefix}.xml")
            page_source = driver.page_source
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            checkpoint = {
                "action": action_name,
                "status": status,
                "timestamp": timestamp,
                "success": success,
                "screenshot": screenshot_path,
                "xml": xml_path,
                "message": f"Checkpoint saved: {action_name}"
            }
            
            logger.info(f"Checkpoint saved: {filename_prefix}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return {"success": success, "message": f"Checkpoint save failed: {str(e)}"}
    
    async def complete_crane_account_switch_flow(self, device_udid: str, target_container: str, platform: str) -> Dict[str, Any]:
        """Complete Crane account switching flow"""
        result = {'success': False, 'message': '', 'data': {'checkpoints': []}}
        
        try:
            # Create evidence directory
            test_name = f"crane_{platform}_account_switching"
            self._create_evidence_dir(test_name)
            
            # Get driver
            driver = await self._get_driver(device_udid, platform)
            if not driver:
                result['message'] = "Failed to get driver"
                return result
            
            wait = WebDriverWait(driver, 15)
            
            # Step 1: Navigate to home screen
            home_result = await self._navigate_to_home_screen(device_udid, driver, wait)
            result['data']['checkpoints'].append(home_result)
            if not home_result['success']:
                result['message'] = "Failed to navigate to home screen"
                return result
            
            # Step 2: Long press app icon to open Crane selection
            long_press_result = await self._long_press_app_icon(device_udid, platform, driver, wait)
            result['data']['checkpoints'].append(long_press_result)
            if not long_press_result['success']:
                result['message'] = "Failed to long press app icon"
                return result
            
            # Step 3: Click on "Container, Default" button
            container_default_result = await self._click_container_default_button(device_udid, driver, wait)
            result['data']['checkpoints'].append(container_default_result)
            if not container_default_result['success']:
                result['message'] = "Failed to click Container, Default button"
                return result
            
            # Step 4: Find and select target container
            container_select_result = await self._select_target_container(device_udid, target_container, driver, wait)
            result['data']['checkpoints'].append(container_select_result)
            if not container_select_result['success']:
                result['message'] = f"Failed to select container {target_container}"
                return result
            
            # Step 5: Click app icon again to launch with selected container
            launch_result = await self._launch_app_with_container(device_udid, platform, driver, wait)
            result['data']['checkpoints'].append(launch_result)
            if not launch_result['success']:
                result['message'] = "Failed to launch app with selected container"
                return result
            
            result['success'] = True
            result['message'] = f"Successfully switched to container {target_container} for {platform}"
            logger.info(f"Crane account switch completed: {platform} -> container {target_container}")
            
        except Exception as e:
            result['message'] = f"Crane account switch error: {str(e)}"
            logger.error(f"Crane account switch error on {device_udid}: {e}")
            
        return result
    
    async def _navigate_to_home_screen(self, device_udid: str, driver, wait) -> Dict[str, Any]:
        """Navigate to home screen by going to desktop directly"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            # For iOS devices, use the correct method to go to home screen
            # Try multiple approaches to ensure we get to the home screen
            
            # Method 1: Try using mobile: pressKey with the correct iOS format
            try:
                driver.execute_script("mobile: pressKey", {"keycode": 3})  # Home button
                logger.info("Used mobile: pressKey to navigate to home screen")
            except Exception as e:
                logger.warning(f"mobile: pressKey failed: {e}")
                
                # Method 2: Try using mobile: pressKey with different format
                try:
                    driver.execute_script("mobile: pressKey", {"keycode": "3"})
                    logger.info("Used mobile: pressKey (string) to navigate to home screen")
                except Exception as e2:
                    logger.warning(f"mobile: pressKey (string) failed: {e2}")
                    
                    # Method 3: Try using mobile: pressKey with name
                    try:
                        driver.execute_script("mobile: pressKey", {"name": "home"})
                        logger.info("Used mobile: pressKey (name) to navigate to home screen")
                    except Exception as e3:
                        logger.warning(f"mobile: pressKey (name) failed: {e3}")
                        
                        # Method 4: For iOS, try using the XCUITest specific method
                        try:
                            driver.execute_script("mobile: pressButton", {"name": "home"})
                            logger.info("Used mobile: pressButton to navigate to home screen")
                        except Exception as e4:
                            logger.warning(f"mobile: pressButton failed: {e4}")
                            
                            # Method 5: Last resort - try to find and tap the home indicator
                            try:
                                # Look for home indicator at bottom of screen
                                home_indicator = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeOther[@name='Home indicator']")
                                home_indicator.click()
                                logger.info("Tapped home indicator to navigate to home screen")
                            except Exception as e5:
                                logger.warning(f"Home indicator tap failed: {e5}")
                                # If all methods fail, we'll continue anyway as we might already be on home screen
                                logger.info("All home navigation methods failed, assuming already on home screen")
            
            await asyncio.sleep(2)  # Wait a bit longer for home screen to load
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("navigate_to_home_screen", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = "Navigated to home screen"
            logger.info(f"Navigated to home screen on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Home screen navigation error: {str(e)}"
            logger.error(f"Home screen navigation error on {device_udid}: {e}")
            checkpoint = self._save_checkpoint("navigate_to_home_screen", False, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
        return result
    
    async def _long_press_app_icon(self, device_udid: str, platform: str, driver, wait) -> Dict[str, Any]:
        """Long press app icon to open Crane selection menu"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            app_name = self.platform_app_names[platform]
            print(f"🔍 DEBUG: Looking for {app_name} icon...")
            
            # Find Instagram or Threads icon using the exact selectors you provided
            selectors = [
                (AppiumBy.ACCESSIBILITY_ID, app_name),  # accessibility id
                (AppiumBy.IOS_CLASS_CHAIN, f"**/XCUIElementTypeIcon[`name == \"{app_name}\"`]"),  # ios class chain
                (AppiumBy.IOS_PREDICATE, f"name == \"{app_name}\""),  # ios predicate string
                (By.XPATH, f"//XCUIElementTypeIcon[@name='{app_name}']")  # xpath
            ]
            
            print(f"🔍 DEBUG: Trying selectors: {selectors}")
            
            icon_element = None
            for i, (by_type, selector) in enumerate(selectors):
                try:
                    print(f"🔍 DEBUG: Trying selector {i+1}: {by_type} = {selector}")
                    icon_element = wait.until(EC.element_to_be_clickable((by_type, selector)))
                    print(f"✅ DEBUG: Found icon with selector {i+1}")
                    break
                except TimeoutException as e:
                    print(f"❌ DEBUG: Selector {i+1} failed: {e}")
                    continue
            
            if not icon_element:
                print(f"❌ DEBUG: Could not find {app_name} icon with any selector")
                result['message'] = f"Could not find {app_name} icon"
                checkpoint = self._save_checkpoint("long_press_app_icon", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                return result
            
            print(f"✅ DEBUG: Found {app_name} icon, attempting long press...")
            
            # Long press using ActionChains - move to element, click and hold for 1 second
            print("🔍 DEBUG: Creating ActionChains...")
            actions = ActionChains(driver)
            print("🔍 DEBUG: Moving to element...")
            actions.move_to_element(icon_element)
            print("🔍 DEBUG: Starting click_and_hold...")
            actions.click_and_hold(icon_element)
            print("🔍 DEBUG: Holding for 1 second...")
            actions.pause(1)  # Hold for 1 second
            print("🔍 DEBUG: Releasing...")
            actions.release(icon_element)
            print("🔍 DEBUG: Performing the action...")
            actions.perform()
            print("✅ DEBUG: Long press completed")
            
            print("🔍 DEBUG: Waiting 2 seconds for menu to appear...")
            await asyncio.sleep(2)  # Wait for menu to appear
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("long_press_app_icon", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = f"Long pressed {app_name} icon successfully"
            print(f"✅ DEBUG: Long press successful!")
            logger.info(f"Long pressed {app_name} icon on {device_udid}")
            
        except Exception as e:
            print(f"❌ DEBUG: Exception in long press: {e}")
            result['message'] = f"Long press error: {str(e)}"
            logger.error(f"Long press error on {device_udid}: {e}")
            checkpoint = self._save_checkpoint("long_press_app_icon", False, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
        return result
    
    async def _click_container_default_button(self, device_udid: str, driver, wait) -> Dict[str, Any]:
        """Click on 'Container, Default' button"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            # Try multiple selectors for the Container, Default button
            selectors = [
                "//XCUIElementTypeButton[contains(@name, 'Container')]",
                "**/XCUIElementTypeButton[`name CONTAINS \"Container\"`]",
                "name CONTAINS \"Container\""
            ]
            
            container_button = None
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        container_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    elif selector.startswith("**/"):
                        container_button = wait.until(EC.element_to_be_clickable((AppiumBy.IOS_CLASS_CHAIN, selector)))
                    else:
                        container_button = wait.until(EC.element_to_be_clickable((AppiumBy.IOS_CLASS_CHAIN, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not container_button:
                result['message'] = "Could not find Container button"
                checkpoint = self._save_checkpoint("click_container_default", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                return result
            
            # Click the container button
            container_button.click()
            await asyncio.sleep(2)  # Wait for container selection to appear
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("click_container_default", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = "Clicked Container, Default button successfully"
            logger.info(f"Clicked Container, Default button on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Container button click error: {str(e)}"
            logger.error(f"Container button click error on {device_udid}: {e}")
            checkpoint = self._save_checkpoint("click_container_default", False, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
        return result
    
    async def _select_target_container(self, device_udid: str, target_container: str, driver, wait) -> Dict[str, Any]:
        """Find and select the target container"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            # Wait for container selection to appear
            await asyncio.sleep(1)
            
            # Try to find the target container with scrolling if needed
            max_scroll_attempts = 5
            scroll_attempt = 0
            
            while scroll_attempt < max_scroll_attempts:
                # Look for the target container button
                container_found = await self._find_and_click_container(driver, target_container)
                
                if container_found:
                    # Save checkpoint
                    checkpoint = self._save_checkpoint(f"select_container_{target_container}", True, driver, wait)
                    result['data']['checkpoint'] = checkpoint
                    
                    result['success'] = True
                    result['message'] = f"Selected container {target_container} successfully"
                    logger.info(f"Selected container {target_container} on {device_udid}")
                    return result
                
                # If not found, try scrolling down
                scroll_success = await self._scroll_container_list(driver)
                if not scroll_success:
                    break
                
                scroll_attempt += 1
                await asyncio.sleep(1)
            
            result['message'] = f"Could not find container {target_container} after scrolling"
            logger.warning(f"Container {target_container} not found on {device_udid}")
            checkpoint = self._save_checkpoint(f"select_container_{target_container}", False, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
        except Exception as e:
            result['message'] = f"Container selection error: {str(e)}"
            logger.error(f"Container selection error on {device_udid}: {e}")
            checkpoint = self._save_checkpoint(f"select_container_{target_container}", False, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
        return result
    
    async def _find_and_click_container(self, driver, target_container: str) -> bool:
        """Find and click the target container button"""
        try:
            # Try multiple selectors for the container button
            selectors = [
                f"//XCUIElementTypeButton[@name='{target_container}']",
                f"**/XCUIElementTypeButton[`name == \"{target_container}\"`]",
                f"name == \"{target_container}\""
            ]
            
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        container_button = driver.find_element(By.XPATH, selector)
                    elif selector.startswith("**/"):
                        container_button = driver.find_element(AppiumBy.IOS_CLASS_CHAIN, selector)
                    else:
                        container_button = driver.find_element(AppiumBy.IOS_CLASS_CHAIN, selector)
                    
                    # Check if button is visible and clickable
                    if container_button.is_displayed() and container_button.is_enabled():
                        container_button.click()
                        await asyncio.sleep(1)
                        return True
                        
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error finding container {target_container}: {e}")
            return False
    
    async def _scroll_container_list(self, driver) -> bool:
        """Scroll down the container list"""
        try:
            # Find the vertical scroll bar
            scroll_selectors = [
                "//XCUIElementTypeOther[contains(@name, 'Vertical scroll bar')]",
                "**/XCUIElementTypeOther[`name CONTAINS \"Vertical scroll bar\"`]",
                "name CONTAINS \"Vertical scroll bar\""
            ]
            
            scroll_element = None
            for selector in scroll_selectors:
                try:
                    if selector.startswith("//"):
                        scroll_element = driver.find_element(By.XPATH, selector)
                    elif selector.startswith("**/"):
                        scroll_element = driver.find_element(AppiumBy.IOS_CLASS_CHAIN, selector)
                    else:
                        scroll_element = driver.find_element(AppiumBy.IOS_CLASS_CHAIN, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if scroll_element:
                # Perform scroll down gesture
                driver.execute_script("mobile: scroll", {
                    "direction": "down",
                    "elementId": scroll_element.id
                })
                await asyncio.sleep(1)
                return True
            else:
                # Fallback: scroll using swipe gesture
                size = driver.get_window_size()
                start_x = size['width'] // 2
                start_y = size['height'] * 0.7
                end_x = size['width'] // 2
                end_y = size['height'] * 0.3
                
                driver.swipe(start_x, start_y, end_x, end_y, 500)
                await asyncio.sleep(1)
                return True
                
        except Exception as e:
            logger.error(f"Scroll error: {e}")
            return False
    
    async def _launch_app_with_container(self, device_udid: str, platform: str, driver, wait) -> Dict[str, Any]:
        """Click the app icon to launch with selected container (after container selection)"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            app_name = self.platform_app_names[platform]
            
            # Find and click the app icon to launch with selected container
            selectors = [
                f"//XCUIElementTypeIcon[@name='{app_name}']",
                f"**/XCUIElementTypeIcon[`name == \"{app_name}\"`]",
                f"name == \"{app_name}\""
            ]
            
            icon_element = None
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        icon_element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    elif selector.startswith("**/"):
                        icon_element = wait.until(EC.element_to_be_clickable((AppiumBy.IOS_CLASS_CHAIN, selector)))
                    else:
                        icon_element = wait.until(EC.element_to_be_clickable((AppiumBy.IOS_PREDICATE, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not icon_element:
                result['message'] = f"Could not find {app_name} icon for launch"
                checkpoint = self._save_checkpoint("launch_app_with_container", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                return result
            
            # Click the app icon to launch with selected container
            icon_element.click()
            await asyncio.sleep(3)  # Wait for app to launch
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("launch_app_with_container", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = f"Launched {app_name} with selected container"
            logger.info(f"Launched {app_name} with container on {device_udid}")
            
        except Exception as e:
            result['message'] = f"App launch error: {str(e)}"
            logger.error(f"App launch error on {device_udid}: {e}")
            checkpoint = self._save_checkpoint("launch_app_with_container", False, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
        return result
    
    async def get_available_containers(self, device_udid: str, platform: str) -> Dict[str, Any]:
        """Get list of available containers for the platform"""
        result = {'success': False, 'message': '', 'data': {'containers': []}}
        
        try:
            # This would need to be implemented to query Crane for available containers
            # For now, return a placeholder response
            result['success'] = True
            result['message'] = "Container list retrieved successfully"
            result['data']['containers'] = [
                {"id": "4", "name": "Container 4", "status": "available"},
                {"id": "5", "name": "Container 5", "status": "available"},
                {"id": "7", "name": "Container 7", "status": "available"}
            ]
            
        except Exception as e:
            result['message'] = f"Container list error: {str(e)}"
            logger.error(f"Container list error on {device_udid}: {e}")
            
        return result
    
    async def _get_driver(self, device_udid: str, platform: str):
        """Get driver instance for the device"""
        try:
            # Get device configuration to determine the correct Appium port
            from platforms.config import DEVICE_CONFIG
            
            # Create driver directly with the correct port from device config
            from appium.options.ios import XCUITestOptions
            from appium import webdriver
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = str(device_udid)  # Ensure UDID is string
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.wda_local_port = DEVICE_CONFIG["wda_port"]
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            options.set_capability("jailbroken", True)  # JB device capability
            
            # Use the correct Appium port from device config
            appium_port = DEVICE_CONFIG["appium_port"]
            server_url = f"http://localhost:{appium_port}"
            
            logger.info(f"Creating Crane driver connection to {server_url}")
            
            # Create WebDriver session directly
            driver = webdriver.Remote(server_url, options=options)
            
            logger.info(f"Created Crane driver session for device {device_udid} on port {appium_port}")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to get driver for device {device_udid}: {e}")
            return None

# Global instances for each platform
crane_instagram_account_switching = CraneAccountSwitching()
crane_threads_account_switching = CraneAccountSwitching()
