"""
Instagram Account Switching Service
Handles switching between multiple Instagram accounts on the same device
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from .appium_service import appium_service

logger = logging.getLogger(__name__)

class InstagramAccountSwitching:
    """Instagram account switching automation with checkpoint system"""
    
    def __init__(self):
        self.app_package = "com.burbn.instagram"
        self.timeout = 15
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
            
            # Save XML source
            xml_path = os.path.join(self.current_test_dir, f"{filename_prefix}.xml")
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
                
            logger.info(f"Checkpoint saved: {filename_prefix}")
            return {
                "success": success,
                "message": f"Checkpoint {status}",
                "screenshot": screenshot_path,
                "xml": xml_path,
                "timestamp": timestamp
            }
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return {"success": False, "message": f"Checkpoint save failed: {e}"}
    
    async def launch_instagram_homepage(self, device_udid: str) -> Dict[str, Any]:
        """Launch Instagram and navigate to homepage"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            # Create evidence directory
            self._create_evidence_dir("instagram_account_switching")
            
            # Ensure we have a session
            if device_udid not in appium_service.active_sessions:
                session_id = await appium_service.create_session(device_udid, self.app_package)
                if not session_id:
                    result['message'] = "Failed to create device session"
                    return result
            
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Launch Instagram
            driver.activate_app(self.app_package)
            await asyncio.sleep(3)
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("launch_instagram_homepage", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = "Instagram launched successfully"
            logger.info(f"Instagram launched on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Launch error: {str(e)}"
            logger.error(f"Instagram launch error on {device_udid}: {e}")
            if 'driver' in locals():
                checkpoint = self._save_checkpoint("launch_instagram_homepage", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                
        return result
    
    async def navigate_to_profile_tab(self, device_udid: str) -> Dict[str, Any]:
        """Navigate to profile tab"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Click profile tab button
            profile_tab_selectors = [
                "//XCUIElementTypeButton[@name='profile-tab']",
                "//XCUIElementTypeButton[@label='Profile']",
                "//XCUIElementTypeButton[contains(@name, 'profile')]"
            ]
            
            profile_tab_clicked = False
            for selector in profile_tab_selectors:
                try:
                    profile_tab = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    profile_tab.click()
                    await asyncio.sleep(2)
                    profile_tab_clicked = True
                    break
                except TimeoutException:
                    continue
            
            if not profile_tab_clicked:
                result['message'] = "Profile tab not found"
                checkpoint = self._save_checkpoint("navigate_to_profile_tab", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                return result
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("navigate_to_profile_tab", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = "Successfully navigated to profile tab"
            logger.info(f"Navigated to profile tab on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Profile navigation error: {str(e)}"
            logger.error(f"Profile navigation error on {device_udid}: {e}")
            if 'driver' in locals():
                checkpoint = self._save_checkpoint("navigate_to_profile_tab", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                
        return result
    
    async def open_account_switcher(self, device_udid: str) -> Dict[str, Any]:
        """Open the account switcher dropdown"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Click user switch title button
            user_switch_selectors = [
                "//XCUIElementTypeButton[@name='user-switch-title-button']",
                "//XCUIElementTypeButton[contains(@name, 'user-switch')]",
                "//XCUIElementTypeButton[contains(@label, 'linaaarogers11439')]"  # Fallback for current user
            ]
            
            switcher_opened = False
            for selector in user_switch_selectors:
                try:
                    user_switch_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    user_switch_button.click()
                    await asyncio.sleep(2)
                    switcher_opened = True
                    break
                except TimeoutException:
                    continue
            
            if not switcher_opened:
                result['message'] = "Account switcher button not found"
                checkpoint = self._save_checkpoint("open_account_switcher", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                return result
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("open_account_switcher", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = "Account switcher opened successfully"
            logger.info(f"Account switcher opened on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Account switcher error: {str(e)}"
            logger.error(f"Account switcher error on {device_udid}: {e}")
            if 'driver' in locals():
                checkpoint = self._save_checkpoint("open_account_switcher", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                
        return result
    
    async def get_available_accounts(self, device_udid: str) -> Dict[str, Any]:
        """Get list of available accounts from the switcher"""
        result = {'success': False, 'message': '', 'data': {'accounts': []}}
        
        try:
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Wait for account switcher to be visible
            await asyncio.sleep(2)
            
            # Find all account buttons in the switcher
            account_buttons = driver.find_elements(By.XPATH, "//XCUIElementTypeButton[contains(@name, ', Shared access')]")
            
            accounts = []
            for button in account_buttons:
                try:
                    button_name = button.get_attribute('name')
                    if button_name and ', Shared access' in button_name:
                        # Extract username from button name
                        username = button_name.split(',')[0].strip()
                        accounts.append({
                            'username': username,
                            'full_name': button_name
                            # Removed 'element': button to avoid JSON serialization issues
                        })
                except Exception as e:
                    logger.warning(f"Error processing account button: {e}")
                    continue
            
            result['data']['accounts'] = accounts
            result['success'] = True
            result['message'] = f"Found {len(accounts)} available accounts"
            logger.info(f"Found {len(accounts)} accounts on {device_udid}: {[acc['username'] for acc in accounts]}")
            
        except Exception as e:
            result['message'] = f"Get accounts error: {str(e)}"
            logger.error(f"Get accounts error on {device_udid}: {e}")
            
        return result
    
    async def close_account_switcher(self, device_udid: str) -> Dict[str, Any]:
        """Close the account switcher dropdown by clicking the drag handle"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Look for the drag handle to close the switcher
            drag_handle_selectors = [
                "//XCUIElementTypeButton[@name='feed-controls-menu-drag-handle']",
                "//XCUIElementTypeButton[contains(@name, 'drag-handle')]",
                "//XCUIElementTypeButton[contains(@name, 'feed-controls')]"
            ]
            
            drag_handle_clicked = False
            for selector in drag_handle_selectors:
                try:
                    drag_handle = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    drag_handle.click()
                    await asyncio.sleep(2)  # Wait for dropdown to close
                    drag_handle_clicked = True
                    break
                except TimeoutException:
                    continue
            
            if not drag_handle_clicked:
                result['message'] = "Drag handle not found - switcher might already be closed"
                logger.warning(f"Drag handle not found on {device_udid}")
                return result
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("close_account_switcher", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = "Account switcher closed successfully"
            logger.info(f"Closed account switcher on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Close switcher error: {str(e)}"
            logger.error(f"Close switcher error on {device_udid}: {e}")
            
        return result
    
    async def switch_to_account(self, device_udid: str, target_username: str) -> Dict[str, Any]:
        """Switch to a specific account by username"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Check if switcher is open first
            try:
                # Look for account buttons to see if switcher is open
                account_buttons = driver.find_elements(By.XPATH, "//XCUIElementTypeButton[contains(@name, ', Shared access')]")
                if not account_buttons:
                    result['message'] = "Account switcher is not open. Please open it first."
                    return result
            except Exception:
                result['message'] = "Account switcher is not open. Please open it first."
                return result
            
            # Find target account button directly
            target_selectors = [
                f"//XCUIElementTypeButton[@name='{target_username}, Shared access']",
                f"//XCUIElementTypeButton[contains(@name, '{target_username},')]",
                f"//XCUIElementTypeButton[starts-with(@name, '{target_username},')]"
            ]
            
            target_button = None
            for selector in target_selectors:
                try:
                    target_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not target_button:
                # Get available accounts for error message
                try:
                    available_buttons = driver.find_elements(By.XPATH, "//XCUIElementTypeButton[contains(@name, ', Shared access')]")
                    available_names = [btn.get_attribute('name').split(',')[0].strip() for btn in available_buttons]
                    result['message'] = f"Account '{target_username}' not found. Available: {available_names}"
                except:
                    result['message'] = f"Account '{target_username}' not found. Available: []"
                return result
            
            # Click on target account
            target_button.click()
            await asyncio.sleep(3)  # Wait for account switch to complete
            
            # Save checkpoint
            checkpoint = self._save_checkpoint(f"switch_to_account_{target_username}", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            
            result['success'] = True
            result['message'] = f"Successfully switched to account: {target_username}"
            logger.info(f"Switched to account {target_username} on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Account switch error: {str(e)}"
            logger.error(f"Account switch error on {device_udid}: {e}")
            if 'driver' in locals():
                checkpoint = self._save_checkpoint(f"switch_to_account_{target_username}", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                
        return result
    
    async def complete_account_switch_flow(self, device_udid: str, target_username: str) -> Dict[str, Any]:
        """Complete account switching flow with all checkpoints"""
        result = {'success': False, 'message': '', 'data': {'checkpoints': []}}
        
        try:
            # Step 1: Launch Instagram homepage
            launch_result = await self.launch_instagram_homepage(device_udid)
            result['data']['checkpoints'].append(launch_result)
            if not launch_result['success']:
                result['message'] = "Failed to launch Instagram"
                return result
            
            # Step 2: Navigate to profile tab
            profile_result = await self.navigate_to_profile_tab(device_udid)
            result['data']['checkpoints'].append(profile_result)
            if not profile_result['success']:
                result['message'] = "Failed to navigate to profile tab"
                return result
            
            # Step 3: Open account switcher
            switcher_result = await self.open_account_switcher(device_udid)
            result['data']['checkpoints'].append(switcher_result)
            if not switcher_result['success']:
                result['message'] = "Failed to open account switcher"
                return result
            
            # Step 4: Switch to target account
            switch_result = await self.switch_to_account(device_udid, target_username)
            result['data']['checkpoints'].append(switch_result)
            if not switch_result['success']:
                result['message'] = f"Failed to switch to account: {target_username}"
                return result
            
            # Step 5: Account switch is complete - Instagram automatically closes switcher
            # and navigates to the new account's profile page
            
            result['success'] = True
            result['message'] = f"Successfully completed account switch to {target_username}"
            logger.info(f"Completed account switch flow to {target_username} on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Account switch flow error: {str(e)}"
            logger.error(f"Account switch flow error on {device_udid}: {e}")
            
        return result

# Create global instance
instagram_account_switching = InstagramAccountSwitching()
