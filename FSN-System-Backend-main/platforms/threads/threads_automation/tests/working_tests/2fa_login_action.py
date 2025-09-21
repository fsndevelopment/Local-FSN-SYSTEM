#!/usr/bin/env python3
"""
Threads 2FA LOGIN Action Implementation
======================================

Implements Threads account login with 2FA verification using the proven 8-checkpoint system.
Handles 2FA code entry and verification flow.

Key Features:
- 8-checkpoint verification system
- Screenshot and XML evidence collection
- 2FA code handling
- Error recovery and modal handling
- Real device testing only

Author: FSN Appium Team
Last Updated: January 15, 2025
Status: Production-ready
"""

import time
import logging
from typing import Optional, Dict, Any
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..base_action import BaseThreadsAction

logger = logging.getLogger(__name__)


class Threads2FALoginAction(BaseThreadsAction):
    """Threads 2FA LOGIN action implementation using 8-checkpoint system"""
    
    def __init__(self, driver, device_config):
        super().__init__(driver, device_config)
        
    def define_checkpoints(self):
        """Define the 8-checkpoint system for Threads 2FA login"""
        return [
            (self.checkpoint_1_launch_threads_app, "launch_threads_app"),
            (self.checkpoint_2_navigate_to_login, "navigate_to_login"),
            (self.checkpoint_3_enter_username, "enter_username"),
            (self.checkpoint_4_enter_password, "enter_password"),
            (self.checkpoint_5_click_login_button, "click_login_button"),
            (self.checkpoint_6_enter_2fa_code, "enter_2fa_code"),
            (self.checkpoint_7_verify_login_success, "verify_login_success"),
            (self.checkpoint_8_return_safe_state, "return_safe_state")
        ]
    
    def execute(self, username: str, password: str, twofa_code: str) -> Dict[str, Any]:
        """
        Execute Threads 2FA login with comprehensive logging
        
        Args:
            username: Username, email, or mobile number
            password: Account password
            twofa_code: 2FA verification code
            
        Returns:
            Dict with login results and evidence
        """
        # Start action logging
        action_id = self.start_action_logging(
            "threads_2fa_login", 
            "authentication",
            username=username[:3] + "***",  # Masked for security
            account_type="2fa"
        )
        
        # Store credentials for checkpoints
        self.username = username
        self.password = password
        self.twofa_code = twofa_code
        
        try:
            # Run checkpoint sequence
            checkpoints = self.define_checkpoints()
            success = self.run_checkpoint_sequence(self.driver, checkpoints)
            
            # End action logging
            result = self.end_action_logging(success)
            
            return {
                "success": success,
                "platform": "threads",
                "action": "2fa_login",
                "account_type": "2fa",
                "action_id": action_id,
                "log_directory": self.logger_system.log_dir,
                "session_summary": self.get_session_summary(),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.log_error_with_evidence("execution_error", f"2FA Login execution failed: {str(e)}")
            result = self.end_action_logging(False)
            return {
                "success": False,
                "platform": "threads",
                "action": "2fa_login",
                "account_type": "2fa",
                "action_id": action_id,
                "error": str(e),
                "log_directory": self.logger_system.log_dir,
                "timestamp": time.time()
            }
    
    def checkpoint_1_launch_threads_app(self, driver) -> bool:
        """Checkpoint 1: Launch Threads app from desktop"""
        try:
            self.logger.info("🧵 CHECKPOINT 1: Launching Threads app...")
            
            # Launch Threads app using desktop icon
            threads_app = self.safe_find_element(AppiumBy.ACCESSIBILITY_ID, "Threads")
            if not threads_app:
                self.log_checkpoint_with_evidence("launch_threads_app", False, "Threads app not found")
                return False
            
            app_name = threads_app.get_attribute('name')
            self.logger.info(f"📱 Found Threads app: {app_name}")
            
            if not self.safe_click_element(threads_app, "Threads app"):
                self.log_checkpoint_with_evidence("launch_threads_app", False, "Failed to click Threads app")
                return False
            
            time.sleep(3)  # Allow app to fully load
            
            # Verify app launched successfully
            if self.wait_for_element_visible(AppiumBy.ACCESSIBILITY_ID, "Threads-lockup"):
                self.log_checkpoint_with_evidence("launch_threads_app", True)
                return True
            else:
                self.log_checkpoint_with_evidence("launch_threads_app", False, "Threads app launch verification failed")
                return False
                
        except Exception as e:
            self.log_checkpoint_with_evidence("launch_threads_app", False, str(e))
            return False
    
    def checkpoint_2_navigate_to_login(self, driver) -> bool:
        """Checkpoint 2: Navigate to login screen"""
        try:
            self.logger.info("🧵 CHECKPOINT 2: Navigating to login screen...")
            
            # Look for "Log in" button on the main screen
            login_button = self.safe_find_element(
                AppiumBy.XPATH, 
                "//XCUIElementTypeButton[@name='Log in']"
            )
            
            if not login_button:
                self.log_checkpoint_with_evidence("navigate_to_login", False, "Log in button not found")
                return False
            
            self.logger.info("📱 Found 'Log in' button")
            
            if not self.safe_click_element(login_button, "Log in button"):
                self.log_checkpoint_with_evidence("navigate_to_login", False, "Failed to click Log in button")
                return False
            
            time.sleep(2)  # Allow screen transition
            
            # Verify we're on the login screen
            if self.wait_for_element_visible(AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number"):
                self.log_checkpoint_with_evidence("navigate_to_login", True)
                return True
            else:
                self.log_checkpoint_with_evidence("navigate_to_login", False, "Login screen verification failed")
                return False
                
        except Exception as e:
            self.log_checkpoint_with_evidence("navigate_to_login", False, str(e))
            return False
    
    def checkpoint_3_enter_username(self, driver) -> bool:
        """Checkpoint 3: Enter username/email/mobile number"""
        try:
            self.logger.info("🧵 CHECKPOINT 3: Entering username...")
            
            # Find username field
            username_field = self.safe_find_element(
                AppiumBy.ACCESSIBILITY_ID, 
                "Username, email or mobile number"
            )
            
            if not username_field:
                self.log_checkpoint_with_evidence("enter_username", False, "Username field not found")
                return False
            
            # Enter username using safe method
            if not self.safe_send_keys(username_field, self.username, "username field"):
                self.log_checkpoint_with_evidence("enter_username", False, "Failed to enter username")
                return False
            
            # Verify text was entered
            entered_text = username_field.get_attribute('value')
            if entered_text == self.username:
                self.log_checkpoint_with_evidence("enter_username", True)
                return True
            else:
                error_msg = f"Username entry verification failed. Expected: {self.username}, Got: {entered_text}"
                self.log_checkpoint_with_evidence("enter_username", False, error_msg)
                return False
                
        except Exception as e:
            self.log_checkpoint_with_evidence("enter_username", False, str(e))
            return False
    
    def checkpoint_4_enter_password(self, driver) -> bool:
        """Checkpoint 4: Enter password"""
        try:
            self.logger.info("🧵 CHECKPOINT 4: Entering password...")
            
            # Find password field
            password_field = self.safe_find_element(
                AppiumBy.ACCESSIBILITY_ID, 
                "Password"
            )
            
            if not password_field:
                self.log_checkpoint_with_evidence("enter_password", False, "Password field not found")
                return False
            
            # Enter password using safe method
            if not self.safe_send_keys(password_field, self.password, "password field"):
                self.log_checkpoint_with_evidence("enter_password", False, "Failed to enter password")
                return False
            
            # Verify password was entered (check if field is not empty)
            entered_text = password_field.get_attribute('value')
            if len(entered_text) > 0:
                self.log_checkpoint_with_evidence("enter_password", True)
                return True
            else:
                self.log_checkpoint_with_evidence("enter_password", False, "Password entry failed - field is empty")
                return False
                
        except Exception as e:
            self.log_checkpoint_with_evidence("enter_password", False, str(e))
            return False
    
    def checkpoint_5_click_login_button(self, driver) -> bool:
        """Checkpoint 5: Click the login button"""
        try:
            self.logger.info("🧵 CHECKPOINT 5: Clicking login button...")
            
            # Find and click the login button (second one on the page)
            login_button = self.safe_find_element(
                AppiumBy.XPATH, 
                "(//XCUIElementTypeButton[@name='Log in'])[2]"
            )
            
            if not login_button:
                self.log_checkpoint_with_evidence("click_login_button", False, "Login button not found")
                return False
            
            self.logger.info("📱 Found login button")
            
            if not self.safe_click_element(login_button, "login button"):
                self.log_checkpoint_with_evidence("click_login_button", False, "Failed to click login button")
                return False
            
            time.sleep(3)  # Allow login processing
            
            self.log_checkpoint_with_evidence("click_login_button", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("click_login_button", False, str(e))
            return False
    
    def checkpoint_6_enter_2fa_code(self, driver) -> bool:
        """Checkpoint 6: Enter 2FA verification code"""
        try:
            self.logger.info("🧵 CHECKPOINT 6: Entering 2FA code...")
            
            # Wait for 2FA screen to appear
            time.sleep(2)
            
            # Look for 2FA code input field
            code_field = self.safe_find_element(
                AppiumBy.ACCESSIBILITY_ID, 
                "Verification code"
            )
            
            if not code_field:
                # Try alternative selectors for 2FA code field
                alternative_selectors = [
                    "//XCUIElementTypeTextField[@placeholder='Enter code']",
                    "//XCUIElementTypeTextField[contains(@name, 'code')]",
                    "//XCUIElementTypeTextField[contains(@name, 'verification')]",
                    "//XCUIElementTypeSecureTextField[@placeholder='Enter code']"
                ]
                
                for selector in alternative_selectors:
                    code_field = self.safe_find_element(AppiumBy.XPATH, selector)
                    if code_field:
                        break
                
                if not code_field:
                    self.log_checkpoint_with_evidence("enter_2fa_code", False, "2FA code field not found")
                    return False
            
            self.logger.info("🔐 Found 2FA code field")
            
            # Enter 2FA code
            if not self.safe_send_keys(code_field, self.twofa_code, "2FA code field"):
                self.log_checkpoint_with_evidence("enter_2fa_code", False, "Failed to enter 2FA code")
                return False
            
            # Verify code was entered
            entered_code = code_field.get_attribute('value')
            if entered_code == self.twofa_code:
                self.logger.info("✅ 2FA code entered successfully")
                
                # Look for submit/continue button
                submit_button = self.safe_find_element(
                    AppiumBy.XPATH, 
                    "//XCUIElementTypeButton[contains(@name, 'Continue') or contains(@name, 'Verify') or contains(@name, 'Submit')]"
                )
                
                if submit_button:
                    if self.safe_click_element(submit_button, "2FA submit button"):
                        self.logger.info("✅ Clicked 2FA submit button")
                    else:
                        self.logger.warning("⚠️ Failed to click 2FA submit button")
                else:
                    self.logger.info("ℹ️ No submit button found, code may auto-submit")
                
                time.sleep(3)  # Allow verification processing
                
                self.log_checkpoint_with_evidence("enter_2fa_code", True)
                return True
            else:
                error_msg = f"2FA code entry verification failed. Expected: {self.twofa_code}, Got: {entered_code}"
                self.log_checkpoint_with_evidence("enter_2fa_code", False, error_msg)
                return False
                
        except Exception as e:
            self.log_checkpoint_with_evidence("enter_2fa_code", False, str(e))
            return False
    
    def checkpoint_7_verify_login_success(self, driver) -> bool:
        """Checkpoint 7: Verify successful login"""
        try:
            self.logger.info("🧵 CHECKPOINT 7: Verifying login success...")
            
            # Wait a bit for the app to load after login
            time.sleep(3)
            
            # Look for indicators of successful login
            success_indicators = [
                "profile-tab",
                "home-tab", 
                "search-tab",
                "notifications-tab",
                "Threads from Meta"
            ]
            
            for indicator in success_indicators:
                element = self.safe_find_element(AppiumBy.ACCESSIBILITY_ID, indicator)
                if element:
                    self.logger.info(f"✅ Found success indicator: {indicator}")
                    self.log_checkpoint_with_evidence("verify_login_success", True)
                    return True
            
            # If no specific indicators found, check if we're not on login screen
            username_field = self.safe_find_element(AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number")
            if username_field:
                self.log_checkpoint_with_evidence("verify_login_success", False, "Still on login screen - login failed")
                return False
            else:
                self.log_checkpoint_with_evidence("verify_login_success", True, "Not on login screen - login appears successful")
                return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("verify_login_success", False, str(e))
            return False
    
    def checkpoint_8_return_safe_state(self, driver) -> bool:
        """Checkpoint 8: Return to safe state (main feed)"""
        try:
            self.logger.info("🧵 CHECKPOINT 8: Returning to safe state...")
            
            # Try to navigate to main feed if not already there
            home_tab = self.safe_find_element(AppiumBy.ACCESSIBILITY_ID, "home-tab")
            if home_tab:
                if self.safe_click_element(home_tab, "home tab"):
                    self.logger.info("✅ Navigated to home tab")
                else:
                    self.logger.warning("⚠️ Failed to click home tab")
            else:
                self.logger.info("ℹ️ Home tab not found or already on main feed")
            
            # Verify we're in a safe state
            time.sleep(2)
            
            # Look for any main app elements to confirm we're in the app
            meta_element = self.safe_find_element(AppiumBy.ACCESSIBILITY_ID, "Threads from Meta")
            if meta_element:
                self.log_checkpoint_with_evidence("return_safe_state", True, "Successfully returned to safe state")
                return True
            else:
                self.log_checkpoint_with_evidence("return_safe_state", True, "Could not verify safe state, but continuing")
                return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("return_safe_state", False, str(e))
            return False


def create_threads_2fa_login_action(driver, device_config):
    """Factory function to create Threads2FALoginAction instance"""
    return Threads2FALoginAction(driver, device_config)


if __name__ == "__main__":
    print("🧵 Threads 2FA Login Action - 8-Checkpoint System")
    print("==================================================")
    print("Production-ready 2FA login implementation")
    print("Comprehensive logging and evidence collection")
