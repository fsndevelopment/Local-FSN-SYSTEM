"""
Threads Account Switching Service
Handles account switching automation for Threads platform
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from .appium_service import appium_service

logger = logging.getLogger(__name__)

class ThreadsAccountSwitching:
    """Service for Threads account switching automation"""

    def __init__(self):
        self.app_package = "com.apple.springboard"  # Use SpringBoard to access home screen
        self.timeout = 15

    def _save_checkpoint(self, action_name: str, success: bool, driver, wait):
        """Save checkpoint with screenshot and XML"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            status = "SUCCESS" if success else "FAILED"
            
            # Take screenshot
            screenshot_path = f"evidence/threads_account_switching_{action_name}_{status}_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            
            # Get page source
            xml_path = f"evidence/threads_account_switching_{action_name}_{status}_{timestamp}.xml"
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            
            return {
                'screenshot': screenshot_path,
                'xml': xml_path,
                'timestamp': timestamp,
                'status': status
            }
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
            return None

    async def _get_driver(self, device_udid: str):
        """Helper to get the Appium driver for a given device UDID - using working test approach"""
        if device_udid not in appium_service.active_sessions:
            # Use the exact same approach as working tests
            from appium import webdriver
            from appium.options.ios import XCUITestOptions
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = device_udid
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            # No bundle ID needed for desktop launch
            
            # Use the same port as other tests (4735)
            driver = webdriver.Remote("http://localhost:4735", options=options)
            appium_service.active_sessions[device_udid] = driver
            return driver
        return appium_service.active_sessions[device_udid]

    async def launch_threads_homepage(self, device_udid: str) -> Dict[str, Any]:
        """Launch Threads app and navigate to homepage"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = await self._get_driver(device_udid)
            wait = WebDriverWait(driver, self.timeout)
            
            # Launch Threads using the exact approach from working tests
            try:
                # Use AppiumBy.ACCESSIBILITY_ID like the working tests do
                threads_app = wait.until(EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Threads")))
                app_name = threads_app.get_attribute('name')
                logger.info(f"Found Threads app icon: {app_name}")
                
                threads_app.click()
                await asyncio.sleep(5)  # Allow app to fully load
                
                # App launched successfully - just assume it worked
                result['success'] = True
                result['message'] = "Threads launched successfully"
                logger.info("Threads app launched successfully")
            
            except Exception as e:
                result['message'] = f"Threads launch error: {str(e)}"
                logger.error(f"Threads launch error on {device_udid}: {e}")
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("launch_threads_homepage", result['success'], driver, wait)
            result['data']['checkpoint'] = checkpoint
            
        except Exception as e:
            result['message'] = f"Threads launch error: {str(e)}"
            logger.error(f"Threads launch error on {device_udid}: {e}")
            if 'driver' in locals():
                checkpoint = self._save_checkpoint("launch_threads_homepage", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                
        return result
    
    async def navigate_to_profile_tab(self, device_udid: str) -> Dict[str, Any]:
        """Navigate to profile tab"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = await self._get_driver(device_udid)
            wait = WebDriverWait(driver, self.timeout)
            
            # Use the exact approach from working tests
            try:
                # User-provided selector for profile tab
                profile_tab_selector = "profile-tab"
                
                # Find profile tab using AppiumBy.ACCESSIBILITY_ID like working tests
                profile_tab = wait.until(EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, profile_tab_selector)))
                logger.info(f"Found profile tab: {profile_tab_selector}")
                
                # Tap profile tab TWICE - first to scroll to top, second to see username
                profile_tab.click()
                await asyncio.sleep(1)
                
                # Second click to see username at top
                profile_tab.click()
                await asyncio.sleep(2)
                
                # Verify we're on profile page
                try:
                    page_source = driver.page_source
                    if "Edit profile" in page_source or "Share profile" in page_source:
                        logger.info("Successfully navigated to profile page")
                    else:
                        logger.warning("Profile tab tapped but profile page not immediately visible")
                except Exception as e:
                    logger.warning(f"Could not verify profile page: {e}")
                
            except TimeoutException:
                # Try XPath fallback like working tests
                try:
                    profile_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//XCUIElementTypeButton[@name='profile-tab']")))
                    logger.info("Found profile tab via XPath fallback")
                    
                    # Tap profile tab TWICE - first to scroll to top, second to see username
                    profile_tab.click()
                    await asyncio.sleep(1)
                    
                    # Second click to see username at top
                    profile_tab.click()
                    await asyncio.sleep(2)
                except TimeoutException:
                    result['message'] = "Profile tab not found with any method"
                    checkpoint = self._save_checkpoint("navigate_to_profile_tab", False, driver, wait)
                    result['data']['checkpoint'] = checkpoint
                    return result
            except Exception as e:
                result['message'] = f"Profile tab navigation failed: {str(e)}"
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
            
        return result

    async def open_account_switcher(self, device_udid: str) -> Dict[str, Any]:
        """Open account switcher by clicking on the username"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = await self._get_driver(device_udid)
            wait = WebDriverWait(driver, self.timeout)
            
            # Find the username button that has the chevron down icon next to it - this opens the account switcher
            try:
                # Look for the username button that has the chevron down icon next to it
                # This is the specific button that opens the account switcher (NOT the profile picture)
                username_button = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, "//XCUIElementTypeButton[not(contains(@name, 'Profile picture')) and following-sibling::XCUIElementTypeOther[XCUIElementTypeImage[@name='ig_icon_chevron_down_filled_12']]]")))
                
                username_name = username_button.get_attribute('name')
                logger.info(f"Found username button with chevron down: {username_name}")
                username_button.click()
                await asyncio.sleep(2)
                    
            except TimeoutException:
                # Fallback: try to find the username button that's not the profile picture
                try:
                    username_button = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, "//XCUIElementTypeButton[not(contains(@name, 'Profile picture')) and not(contains(@name, 'profile-tab')) and not(contains(@name, 'Button')) and not(contains(@name, 'Edit profile')) and not(contains(@name, 'Share profile')) and not(contains(@name, 'Log in as')) and not(contains(@name, ' tab')) and not(contains(@name, 'Threads')) and not(contains(@name, 'Replies')) and not(contains(@name, 'Media')) and not(contains(@name, 'Reposts')) and not(contains(@name, 'Feeds')) and string-length(@name) > 3]")))
                    
                    username_name = username_button.get_attribute('name')
                    logger.info(f"Found username button via fallback: {username_name}")
                    username_button.click()
                    await asyncio.sleep(2)
                except TimeoutException:
                    result['message'] = "Could not find username button to open account switcher"
                    checkpoint = self._save_checkpoint("open_account_switcher", False, driver, wait)
                    result['data']['checkpoint'] = checkpoint
                    return result
            except Exception as e:
                result['message'] = f"Account switcher error: {str(e)}"
                checkpoint = self._save_checkpoint("open_account_switcher", False, driver, wait)
                result['data']['checkpoint'] = checkpoint
                return result
            
            # Save checkpoint
            checkpoint = self._save_checkpoint("open_account_switcher", True, driver, wait)
            result['data']['checkpoint'] = checkpoint
            result['data']['current_username'] = username_name
            
            result['success'] = True
            result['message'] = "Account switcher opened successfully"
            logger.info(f"Opened account switcher on {device_udid} for user: {username_name}")
            
        except Exception as e:
            result['message'] = f"Account switcher error: {str(e)}"
            logger.error(f"Account switcher error on {device_udid}: {e}")
            
        return result

    async def close_account_switcher(self, device_udid: str) -> dict:
        """Close the account switcher by clicking the Button"""
        result = {
            'success': False,
            'message': '',
            'data': {}
        }
        
        try:
            driver = await self._get_driver(device_udid)
            wait = WebDriverWait(driver, self.timeout)
            
            # Click the Button to close account switcher
            try:
                close_button = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, "//XCUIElementTypeButton[@name='Button']")))
                close_button.click()
                await asyncio.sleep(1)
                
                result['success'] = True
                result['message'] = "Account switcher closed successfully"
                
            except TimeoutException:
                result['message'] = "Close button not found"
                
        except Exception as e:
            result['message'] = f"Error closing account switcher: {str(e)}"
            
        return result

    async def get_available_accounts(self, device_udid: str, current_username: str = None) -> Dict[str, Any]:
        """Get list of available accounts from the switcher, excluding current account"""
        result = {'success': False, 'message': '', 'data': {'accounts': []}}
        
        try:
            driver = await self._get_driver(device_udid)
            wait = WebDriverWait(driver, self.timeout)
            
            # Wait for account switcher to be visible
            await asyncio.sleep(2)
            
            # Find all account buttons in the switcher - Threads uses "Log in as @username" format
            account_buttons = driver.find_elements(AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Log in as @')]")
            
            accounts = []
            for button in account_buttons:
                try:
                    button_name = button.get_attribute('name')
                    if button_name and 'Log in as @' in button_name:
                        # Extract username from button name (remove "Log in as @")
                        username = button_name.replace('Log in as @', '').strip()
                        logger.info(f"Found account: '{username}', current: '{current_username}', match: {username == current_username}")
                        # Only add if it's not the current account
                        if not current_username or username != current_username:
                            accounts.append({
                                'username': username,
                                'full_name': button_name
                            })
                            logger.info(f"Added account: {username}")
                        else:
                            logger.info(f"Skipped current account: {username}")
                except Exception as e:
                    logger.warning(f"Error processing account button: {e}")
                    continue
            
            result['data']['accounts'] = accounts
            result['success'] = True
            result['message'] = f"Found {len(accounts)} available accounts (excluding current: {current_username})"
            logger.info(f"Found {len(accounts)} accounts on {device_udid} (excluding {current_username}): {[acc['username'] for acc in accounts]}")
            
        except Exception as e:
            result['message'] = f"Get accounts error: {str(e)}"
            logger.error(f"Get accounts error on {device_udid}: {e}")
            
        return result

    async def switch_to_account(self, device_udid: str, target_username: str) -> Dict[str, Any]:
        """Switch to a specific account by username"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = await self._get_driver(device_udid)
            wait = WebDriverWait(driver, self.timeout)
            
            # Check if switcher is open first, if not, open it
            try:
                # Look for account buttons to see if switcher is open
                account_buttons = driver.find_elements(AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Log in as @')]")
                if not account_buttons:
                    # Account switcher is not open, try to open it first
                    logger.info("Account switcher not open, attempting to open it first")
                    open_result = await self.open_account_switcher(device_udid)
                    if not open_result['success']:
                        result['message'] = f"Failed to open account switcher: {open_result['message']}"
                        return result
                    # Wait a bit for switcher to open
                    await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Error checking account switcher: {e}")
                # Try to open it anyway
                open_result = await self.open_account_switcher(device_udid)
                if not open_result['success']:
                    result['message'] = f"Failed to open account switcher: {open_result['message']}"
                    return result
                await asyncio.sleep(2)
            
            # Find target account button directly - Threads uses "Log in as @username" format
            try:
                target_button = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, f"//XCUIElementTypeButton[contains(@name, 'Log in as @{target_username}')]")))
            except TimeoutException:
                # Try alternative selector
                try:
                    target_button = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, f"//XCUIElementTypeButton[@name='Log in as @{target_username}']")))
                except TimeoutException:
                    # Get available accounts for error message
                    try:
                        available_buttons = driver.find_elements(AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Log in as @')]")
                        available_names = [btn.get_attribute('name').replace('Log in as @', '').strip() for btn in available_buttons]
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

    async def close_account_switcher(self, device_udid: str) -> Dict[str, Any]:
        """Close the account switcher by clicking the close button"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = await self._get_driver(device_udid)
            wait = WebDriverWait(driver, self.timeout)
            
            # Look for the close button - Threads uses "Button" as accessibility ID
            close_button_selectors = [
                (By.XPATH, "//XCUIElementTypeButton[@name='Button']"),
                (By.XPATH, "//XCUIElementTypeButton[contains(@name, 'Button')]"),
                (By.XPATH, "//XCUIElementTypeButton[contains(@name, 'Close')]")
            ]
            
            close_button_clicked = False
            for by, selector in close_button_selectors:
                try:
                    close_button = wait.until(EC.element_to_be_clickable((by, selector)))
                    close_button.click()
                    await asyncio.sleep(2)
                    close_button_clicked = True
                    break
                except TimeoutException:
                    continue
            
            if not close_button_clicked:
                result['message'] = "Close button not found - switcher might already be closed"
                logger.warning(f"Close button not found on {device_udid}")
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

    async def complete_account_switch_flow(self, device_udid: str, target_username: str) -> Dict[str, Any]:
        """Complete account switching flow with all checkpoints"""
        result = {'success': False, 'message': '', 'data': {'checkpoints': []}}
        
        try:
            # Step 1: Launch Threads homepage
            launch_result = await self.launch_threads_homepage(device_udid)
            result['data']['checkpoints'].append(launch_result)
            if not launch_result['success']:
                result['message'] = "Failed to launch Threads"
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
            
            # Step 5: Account switch is complete - Threads automatically closes switcher
            # and navigates to the new account's profile page
            
            result['success'] = True
            result['message'] = f"Successfully completed account switch to {target_username}"
            logger.info(f"Completed account switch flow to {target_username} on {device_udid}")
            
        except Exception as e:
            result['message'] = f"Account switch flow error: {str(e)}"
            logger.error(f"Account switch flow error on {device_udid}: {e}")
            
        return result

# Create global instance
threads_account_switching = ThreadsAccountSwitching()
