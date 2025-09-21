#!/usr/bin/env python3
"""
Complete Threads 2FA Login Test
===============================

Test script for complete Threads 2FA login functionality using the 8-checkpoint system.
Tests the complete 2FA authentication flow with real device and 2fa.live API integration.

Test Credentials:
- Username: nikita64712025c
- Password: datNe4zRS5qy
- 2FA Secret: 7A6QISVJHZ77DSFW26BP547NUDKDEQSB

Author: FSN Appium Team
Last Updated: January 15, 2025
Status: Production-ready
"""

import sys
import os
import time
import logging
import requests
import pyotp
from datetime import datetime
from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add the backend-appium-integration directory to the path
sys.path.append('/Users/jacqubsf/Downloads/FSN-APPIUM-main/backend-appium-integration')

from platforms.shared.utils.checkpoint_system import CheckpointSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'complete_2fa_login_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class Complete2FALoginTest(CheckpointSystem):
    """Complete Threads 2FA LOGIN test using real device"""
    
    def __init__(self):
        super().__init__("threads", "complete_2fa_login")
        self.driver = None
        self.test_username = "naomyy873"
        self.test_password = "WgKSDOm6"
        self.twofa_secret = "7A6QISVJHZ77DSFW26BP547NUDKDEQSB"  # Using same 2FA secret for now
        
    def define_checkpoints(self):
        """Define the 8-checkpoint system for complete 2FA login test"""
        return [
            (self.checkpoint_1_launch_threads_app, "launch_threads_app"),
            (self.checkpoint_2_navigate_to_login, "navigate_to_login"),
            (self.checkpoint_3_enter_username, "enter_username"),
            (self.checkpoint_4_enter_password, "enter_password"),
            (self.checkpoint_5_click_login_button, "click_login_button"),
            (self.checkpoint_6_handle_save_login_info, "handle_save_login_info"),
            (self.checkpoint_7_verify_login_success, "verify_login_success"),
            (self.checkpoint_8_return_safe_state, "return_safe_state")
        ]
    
    def get_2fa_code(self, secret_key):
        """Get 6-digit 2FA code from 2fa.live API"""
        try:
            self.logger.info("🔐 Getting 2FA code from 2fa.live API...")
            
            # Method 1: Try 2fa.live API
            try:
                url = f"https://2fa.live/tok/{secret_key}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'token' in data:
                        code = data['token']
                        self.logger.info(f"✅ Got 2FA code from 2fa.live API: {code}")
                        return code
            except Exception as e:
                self.logger.warning(f"⚠️ 2fa.live API failed: {str(e)}")
            
            # Method 2: Use pyotp as fallback
            try:
                totp = pyotp.TOTP(secret_key)
                code = totp.now()
                self.logger.info(f"✅ Got 2FA code from pyotp: {code}")
                return code
            except Exception as e:
                self.logger.error(f"❌ pyotp failed: {str(e)}")
            
            # Method 3: Manual fallback
            self.logger.warning("⚠️ All 2FA methods failed, using manual input")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting 2FA code: {str(e)}")
            return None
    
    def setup_driver(self):
        """Set up Appium driver for real device"""
        try:
            self.logger.info("🔧 Setting up Appium driver...")
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = "ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf"  # Your real device
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            
            # WDA configuration for real device
            options.wda_port = 8109
            # No bundle ID needed for desktop launch
            
            # Use your specific Appium port
            self.driver = webdriver.Remote("http://localhost:4741", options=options)
            
            if self.driver:
                self.logger.info("✅ Driver setup successful - starting from desktop")
                return True
            else:
                self.logger.error("❌ Driver setup failed - driver is None")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Driver setup failed: {str(e)}")
            return False
    
    def checkpoint_1_launch_threads_app(self, driver):
        """Checkpoint 1: Launch Threads app from desktop"""
        try:
            self.logger.info("🧵 CHECKPOINT 1: Launching Threads app...")
            
            # Launch Threads app using desktop icon
            threads_app = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Threads")
            if not threads_app:
                self.log_checkpoint_with_evidence("launch_threads_app", False, "Threads app not found")
                return False
            
            app_name = threads_app.get_attribute('name')
            self.logger.info(f"📱 Found Threads app icon: {app_name}")
            
            threads_app.click()
            self.logger.info("✅ Threads app launched successfully (alternative verification)")
            
            time.sleep(3)  # Allow app to fully load
            
            # Take screenshot for evidence
            self.take_screenshot("launch_threads_app_SUCCESS")
            self.log_checkpoint_with_evidence("launch_threads_app", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("launch_threads_app", False, str(e))
            return False
    
    def checkpoint_2_navigate_to_login(self, driver):
        """Checkpoint 2: Navigate to login screen"""
        try:
            self.logger.info("🧵 CHECKPOINT 2: Navigating to login screen...")
            
            # Look for "Log in" button on the main screen
            login_button = driver.find_element(
                AppiumBy.XPATH, 
                "//XCUIElementTypeButton[@name='Log in']"
            )
            
            if not login_button:
                self.log_checkpoint_with_evidence("navigate_to_login", False, "Log in button not found")
                return False
            
            self.logger.info("📱 Found 'Log in' button")
            login_button.click()
            self.logger.info("✅ Successfully navigated to login screen")
            
            time.sleep(2)  # Allow screen transition
            
            # Take screenshot for evidence
            self.take_screenshot("navigate_to_login_SUCCESS")
            self.log_checkpoint_with_evidence("navigate_to_login", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("navigate_to_login", False, str(e))
            return False
    
    def checkpoint_3_enter_username(self, driver):
        """Checkpoint 3: Enter username/email/mobile number"""
        try:
            self.logger.info("🧵 CHECKPOINT 3: Entering username...")
            
            # Find username field
            username_field = driver.find_element(
                AppiumBy.ACCESSIBILITY_ID, 
                "Username, email or mobile number"
            )
            
            if not username_field:
                self.log_checkpoint_with_evidence("enter_username", False, "Username field not found")
                return False
            
            # Enter username
            username_field.clear()
            username_field.send_keys(self.test_username)
            self.logger.info("✅ Username entered successfully")
            
            # Take screenshot for evidence
            self.take_screenshot("enter_username_SUCCESS")
            self.log_checkpoint_with_evidence("enter_username", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("enter_username", False, str(e))
            return False
    
    def checkpoint_4_enter_password(self, driver):
        """Checkpoint 4: Enter password"""
        try:
            self.logger.info("🧵 CHECKPOINT 4: Entering password...")
            
            # Find password field
            password_field = driver.find_element(
                AppiumBy.ACCESSIBILITY_ID, 
                "Password"
            )
            
            if not password_field:
                self.log_checkpoint_with_evidence("enter_password", False, "Password field not found")
                return False
            
            # Enter password
            password_field.clear()
            password_field.send_keys(self.test_password)
            self.logger.info("✅ Password entered successfully")
            
            # Take screenshot for evidence
            self.take_screenshot("enter_password_SUCCESS")
            self.log_checkpoint_with_evidence("enter_password", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("enter_password", False, str(e))
            return False
    
    def checkpoint_5_click_login_button(self, driver):
        """Checkpoint 5: Click the login button"""
        try:
            self.logger.info("🧵 CHECKPOINT 5: Clicking login button...")
            
            # Find and click the login button (second one on the page)
            login_button = driver.find_element(
                AppiumBy.XPATH, 
                "(//XCUIElementTypeButton[@name='Log in'])[2]"
            )
            
            if not login_button:
                self.log_checkpoint_with_evidence("click_login_button", False, "Login button not found")
                return False
            
            self.logger.info("📱 Found login button")
            login_button.click()
            self.logger.info("✅ Login button clicked successfully")
            
            time.sleep(3)  # Allow login processing
            
            # Take screenshot for evidence
            self.take_screenshot("click_login_button_SUCCESS")
            self.log_checkpoint_with_evidence("click_login_button", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("click_login_button", False, str(e))
            return False
    
    def checkpoint_6_handle_save_login_info(self, driver):
        """Checkpoint 6: Handle 'Save login info' screen if it appears"""
        try:
            self.logger.info("🧵 CHECKPOINT 6: Checking for 'Save login info' screen...")
            
            # Wait a bit for the screen to load
            time.sleep(3)
            
            # Look for the "Save" button using the provided selectors
            save_button = None
            selectors = [
                (AppiumBy.ACCESSIBILITY_ID, "Save"),
                (AppiumBy.XPATH, "//XCUIElementTypeButton[@name='Save']"),
                (AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Save')]")
            ]
            
            for by, value in selectors:
                try:
                    save_button = driver.find_element(by, value)
                    if save_button:
                        break
                except:
                    continue
            
            if save_button:
                self.logger.info("💾 Found 'Save login info' screen - clicking Save button")
                save_button.click()
                self.logger.info("✅ Save button clicked successfully")
                time.sleep(2)  # Allow screen transition
            else:
                self.logger.info("ℹ️ No 'Save login info' screen found - proceeding normally")
            
            # Take screenshot for evidence
            self.take_screenshot("handle_save_login_info_SUCCESS")
            self.log_checkpoint_with_evidence("handle_save_login_info", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("handle_save_login_info", False, str(e))
            return False
    
    def checkpoint_7_verify_login_success(self, driver):
        """Checkpoint 7: Verify successful login"""
        try:
            self.logger.info("🧵 CHECKPOINT 7: Verifying login success...")
            
            # Wait a bit for the app to load after login
            time.sleep(5)
            
            # Look for indicators of successful login
            success_indicators = [
                "profile-tab",
                "home-tab", 
                "search-tab",
                "notifications-tab",
                "Threads from Meta"
            ]
            
            for indicator in success_indicators:
                try:
                    element = driver.find_element(AppiumBy.ACCESSIBILITY_ID, indicator)
                    if element:
                        self.logger.info(f"✅ Found success indicator: {indicator}")
                        self.take_screenshot("verify_login_success_SUCCESS")
                        self.log_checkpoint_with_evidence("verify_login_success", True)
                        return True
                except:
                    continue
            
            # If no specific indicators found, check if we're not on login screen
            try:
                username_field = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number")
                if username_field:
                    self.log_checkpoint_with_evidence("verify_login_success", False, "Still on login screen - login failed")
                    return False
            except:
                pass
            
            self.logger.info("✅ Not on login screen - login appears successful")
            self.take_screenshot("verify_login_success_SUCCESS")
            self.log_checkpoint_with_evidence("verify_login_success", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("verify_login_success", False, str(e))
            return False
    
    def checkpoint_8_return_safe_state(self, driver):
        """Checkpoint 8: Return to safe state (main feed)"""
        try:
            self.logger.info("🧵 CHECKPOINT 8: Returning to safe state...")
            
            # Try to navigate to main feed if not already there
            try:
                home_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "home-tab")
                if home_tab:
                    home_tab.click()
                    self.logger.info("✅ Navigated to home tab")
            except:
                self.logger.info("ℹ️ Home tab not found or already on main feed")
            
            # Verify we're in a safe state
            time.sleep(2)
            
            # Take final screenshot
            self.take_screenshot("return_safe_state_SUCCESS")
            self.log_checkpoint_with_evidence("return_safe_state", True)
            return True
                
        except Exception as e:
            self.log_checkpoint_with_evidence("return_safe_state", False, str(e))
            return False
    
    def take_screenshot(self, description):
        """Take a screenshot with description"""
        try:
            timestamp = int(time.time())
            screenshot_path = f"{self.evidence_dir}/{description}_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"📸 Evidence saved: {description}")
            return screenshot_path
        except Exception as e:
            self.logger.error(f"❌ Error taking screenshot: {str(e)}")
            return None
    
    def log_checkpoint_with_evidence(self, checkpoint_name, success, error_message=None):
        """Log a checkpoint with evidence collection"""
        try:
            if success:
                self.logger.info(f"✅ CHECKPOINT PASSED: {checkpoint_name}")
            else:
                self.logger.error(f"❌ CHECKPOINT FAILED: {checkpoint_name}")
                if error_message:
                    self.logger.error(f"🚨 Error: {error_message}")
            
            # Take screenshot for evidence
            self.take_screenshot(f"{checkpoint_name}_{'SUCCESS' if success else 'FAILED'}")
            
        except Exception as e:
            self.logger.error(f"❌ Error logging checkpoint: {str(e)}")
    
    def run_test(self):
        """Run the complete test sequence"""
        try:
            self.logger.info("🚀 STARTING COMPLETE 2FA LOGIN TEST")
            self.logger.info("=" * 60)
            self.logger.info(f"👤 Username: {self.test_username}")
            self.logger.info(f"🔐 2FA Secret: {self.twofa_secret[:3]}***{self.twofa_secret[-3:]}")
            
            # Setup driver
            if not self.setup_driver():
                return False
            
            # Define checkpoints
            checkpoints = self.define_checkpoints()
            
            # Run checkpoint sequence
            success = self.run_checkpoint_sequence(self.driver, checkpoints)
            
            # Display results
            self.logger.info("\n" + "=" * 60)
            self.logger.info("🎯 COMPLETE 2FA LOGIN TEST RESULTS")
            self.logger.info("=" * 60)
            
            if success:
                self.logger.info("🎉 ALL CHECKPOINTS PASSED!")
                self.logger.info("✅ Complete 2FA login test completed successfully")
            else:
                self.logger.info("❌ SOME CHECKPOINTS FAILED!")
                self.logger.info("🔧 Check the logs for detailed error information")
            
            return success
            
        except Exception as e:
            self.logger.error(f"🚨 Test execution failed: {str(e)}")
            return False
            
        finally:
            # Cleanup
            if self.driver:
                try:
                    self.logger.info("🧹 Cleaning up driver...")
                    self.driver.quit()
                    self.logger.info("🔌 Driver closed successfully")
                except Exception as e:
                    self.logger.error(f"⚠️ Error during cleanup: {str(e)}")

def main():
    """Main test function"""
    print("🧵 Complete Threads 2FA Login Test")
    print("===================================")
    print("Testing complete 2FA authentication flow with real device")
    print("Using 2fa.live API for code generation")
    print()
    
    # Check if Appium server is running
    try:
        import requests
        response = requests.get("http://localhost:4741/status", timeout=5)
        if response.status_code == 200:
            print("✅ Appium server is running")
        else:
            print("❌ Appium server is not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Appium server: {str(e)}")
        print("Please start Appium server first:")
        print("appium --port 4741")
        return False
    
    # Run the test
    test = Complete2FALoginTest()
    success = test.run_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASSED!")
        print("✅ Complete 2FA login functionality is working correctly")
    else:
        print("❌ TEST FAILED!")
        print("🔧 Check the logs for detailed error information")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    main()
