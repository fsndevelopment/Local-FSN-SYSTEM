#!/usr/bin/env python3
"""
Threads LOGIN Test - Authentication Action
=========================================

🧵 THREADS LOGIN FUNCTIONALITY - Phase 2 Implementation

Following proven Instagram patterns with user-provided exact selectors.

Test Flow:
1. Launch Threads app from desktop
2. Navigate to login screen (Log in button)
3. Enter username/email/mobile number
4. Enter password
5. Click login button
6. Handle verification if required
7. Verify login success
8. Return to safe state

Login Selectors (User-Provided):
- Login Button: "Log in" (XCUIElementTypeButton)
- Username Field: "Username, email or mobile number" (accessibility ID)
- Password Field: "Password" (accessibility ID)
- Login Submit: "(//XCUIElementTypeButton[@name='Log in'])[2]" (xpath)

Author: FSN Appium Team
Started: January 15, 2025
Status: Phase 2 Authentication Implementation
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add platforms to path
sys.path.append('/Users/jacqubsf/Downloads/FSN-APPIUM-main/backend-appium-integration')

from platforms.shared.utils.checkpoint_system import CheckpointSystem
from platforms.shared.utils.appium_driver import AppiumDriverManager
from platforms.config import Platform
from appium.webdriver.common.appiumby import AppiumBy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'threads_login_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class ThreadsLoginTest(CheckpointSystem):
    """Threads LOGIN test using proven 8-checkpoint system"""
    
    def __init__(self):
        super().__init__("threads", "login")
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Initialize Appium driver for Threads testing - start from desktop"""
        try:
            self.logger.info("🔧 Setting up Appium driver...")
            
            # Create driver for desktop (no specific app bundle)
            from appium import webdriver
            from appium.options.ios import XCUITestOptions
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = "ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf"
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            # No bundle ID needed for desktop launch
            
            # Use your specific Appium port
            self.driver = webdriver.Remote("http://localhost:4741", options=options)
            
            if self.driver:
                self.wait = AppiumDriverManager.get_wait_driver(self.driver)
                self.logger.info("✅ Driver setup successful - starting from desktop")
                return True
            else:
                self.logger.error("❌ Driver setup failed")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Driver setup failed: {e}")
            return False
    
    def define_checkpoints(self):
        """Define the 8-checkpoint system for Threads login"""
        return [
            (self.checkpoint_1_launch_threads_app, "launch_threads_app"),
            (self.checkpoint_2_navigate_to_login, "navigate_to_login"),
            (self.checkpoint_3_enter_username, "enter_username"),
            (self.checkpoint_4_enter_password, "enter_password"),
            (self.checkpoint_5_click_login_button, "click_login_button"),
            (self.checkpoint_6_handle_verification, "handle_verification"),
            (self.checkpoint_7_verify_login_success, "verify_login_success"),
            (self.checkpoint_8_return_safe_state, "return_safe_state")
        ]
    
    def checkpoint_1_launch_threads_app(self, driver) -> bool:
        """Checkpoint 1: Launch Threads app from desktop"""
        try:
            self.logger.info("🧵 CHECKPOINT 1: Launching Threads app from desktop...")
            
            # Launch Threads app using desktop icon (XCUIElementTypeIcon)
            threads_app = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Threads")
            app_name = threads_app.get_attribute('name')
            self.logger.info(f"📱 Found Threads app icon: {app_name}")
            
            threads_app.click()
            time.sleep(5)  # Allow app to fully load
            
            # Verify app launched successfully by looking for Threads UI elements
            try:
                # Look for Threads UI elements to confirm launch
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Threads-lockup")
                self.logger.info("✅ Threads app launched successfully")
                return True
            except:
                # Try alternative verification - look for any Threads-specific elements
                try:
                    driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeStaticText[contains(@name, 'Threads')]")
                    self.logger.info("✅ Threads app launched successfully (alternative verification)")
                    return True
                except:
                    self.logger.error("❌ Threads app launch verification failed")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 1 failed: {e}")
            return False
    
    def checkpoint_2_navigate_to_login(self, driver) -> bool:
        """Checkpoint 2: Navigate to login screen"""
        try:
            self.logger.info("🧵 CHECKPOINT 2: Navigating to login screen...")
            
            # Look for "Log in" button on the main screen
            login_button = driver.find_element(
                AppiumBy.XPATH, 
                "//XCUIElementTypeButton[@name='Log in']"
            )
            
            self.logger.info("📱 Found 'Log in' button")
            login_button.click()
            time.sleep(2)  # Allow screen transition
            
            # Verify we're on the login screen
            try:
                # Look for username field to confirm login screen
                driver.find_element(
                    AppiumBy.ACCESSIBILITY_ID, 
                    "Username, email or mobile number"
                )
                self.logger.info("✅ Successfully navigated to login screen")
                return True
            except:
                self.logger.error("❌ Login screen verification failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 2 failed: {e}")
            return False
    
    def checkpoint_3_enter_username(self, driver) -> bool:
        """Checkpoint 3: Enter username/email/mobile number"""
        try:
            self.logger.info("🧵 CHECKPOINT 3: Entering username...")
            
            # Real credentials for testing
            test_username = "jacqub.sf@gmail.com"  # Your real email
            
            # Find username field
            username_field = driver.find_element(
                AppiumBy.ACCESSIBILITY_ID, 
                "Username, email or mobile number"
            )
            
            # Clear field and enter username
            username_field.clear()
            username_field.send_keys(test_username)
            
            # Verify text was entered
            entered_text = username_field.get_attribute('value')
            if entered_text == test_username:
                self.logger.info("✅ Username entered successfully")
                return True
            else:
                self.logger.error(f"❌ Username entry failed. Expected: {test_username}, Got: {entered_text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 3 failed: {e}")
            return False
    
    def checkpoint_4_enter_password(self, driver) -> bool:
        """Checkpoint 4: Enter password"""
        try:
            self.logger.info("🧵 CHECKPOINT 4: Entering password...")
            
            # Real password for testing
            test_password = "DADA2022?"  # Your real password
            
            # Find password field
            password_field = driver.find_element(
                AppiumBy.ACCESSIBILITY_ID, 
                "Password"
            )
            
            # Clear field and enter password
            password_field.clear()
            password_field.send_keys(test_password)
            
            # Verify password was entered (check if field is not empty)
            entered_text = password_field.get_attribute('value')
            if len(entered_text) > 0:
                self.logger.info("✅ Password entered successfully")
                return True
            else:
                self.logger.error("❌ Password entry failed - field is empty")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 4 failed: {e}")
            return False
    
    def checkpoint_5_click_login_button(self, driver) -> bool:
        """Checkpoint 5: Click the login button"""
        try:
            self.logger.info("🧵 CHECKPOINT 5: Clicking login button...")
            
            # Find and click the login button (second one on the page)
            login_button = driver.find_element(
                AppiumBy.XPATH, 
                "(//XCUIElementTypeButton[@name='Log in'])[2]"
            )
            
            self.logger.info("📱 Found login button")
            login_button.click()
            time.sleep(3)  # Allow login processing
            
            self.logger.info("✅ Login button clicked successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 5 failed: {e}")
            return False
    
    def checkpoint_6_handle_verification(self, driver) -> bool:
        """Checkpoint 6: Handle 2FA, email verification, or error messages"""
        try:
            self.logger.info("🧵 CHECKPOINT 6: Handling verification and error messages...")
            
            # Wait a bit for any error alerts to appear
            time.sleep(3)
            
            # First check for error alerts (incorrect password, etc.)
            try:
                # Look for error alert with multiple approaches
                error_alert = None
                try:
                    error_alert = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeAlert")
                except:
                    try:
                        error_alert = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeAlert[@name='Incorrect Password']")
                    except:
                        pass
                
                if error_alert:
                    alert_name = error_alert.get_attribute('name')
                    self.logger.warning(f"⚠️ Error alert detected: {alert_name}")
                    
                    # Check for specific error messages
                    try:
                        error_message = driver.find_element(
                            AppiumBy.XPATH, 
                            "//XCUIElementTypeStaticText[contains(@name, 'incorrect') or contains(@name, 'Incorrect')]"
                        )
                        error_text = error_message.get_attribute('name')
                        self.logger.error(f"❌ Login error: {error_text}")
                        
                        # Dismiss the error alert by clicking OK
                        try:
                            ok_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "OK")
                            ok_button.click()
                            self.logger.info("✅ Dismissed error alert")
                            time.sleep(2)
                        except:
                            self.logger.warning("⚠️ Could not find OK button to dismiss alert")
                        
                        return False
                        
                    except:
                        self.logger.warning("⚠️ Error alert found but no specific error message")
                        return False
                else:
                    self.logger.info("ℹ️ No error alert found")
                    
            except Exception as e:
                self.logger.info(f"ℹ️ No error alert found: {e}")
            
            # Check if we're still on login screen
            try:
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number")
                self.logger.warning("⚠️ Still on login screen - checking for other error indicators")
                
                # Look for other error indicators
                try:
                    error_element = driver.find_element(
                        AppiumBy.XPATH, 
                        "//XCUIElementTypeStaticText[contains(@name, 'error') or contains(@name, 'Error') or contains(@name, 'incorrect') or contains(@name, 'wrong')]"
                    )
                    error_text = error_element.get_attribute('name')
                    self.logger.error(f"❌ Login error detected: {error_text}")
                    return False
                except:
                    self.logger.warning("⚠️ No error message found, but still on login screen")
                    return False
                    
            except:
                # Not on login screen anymore - check for verification requirements
                self.logger.info("✅ Moved past login screen - checking for verification requirements")
                
                # Check for 2FA verification screen
                try:
                    verification_element = driver.find_element(
                        AppiumBy.XPATH, 
                        "//XCUIElementTypeStaticText[contains(@name, 'verification') or contains(@name, 'code') or contains(@name, '2FA') or contains(@name, 'authenticator')]"
                    )
                    verification_text = verification_element.get_attribute('name')
                    self.logger.info(f"🔐 Verification required: {verification_text}")
                    self.logger.info("✅ 2FA/Email verification screen detected - this is expected")
                    return True
                        
                except:
                    # Check for email verification
                    try:
                        email_verification = driver.find_element(
                            AppiumBy.XPATH, 
                            "//XCUIElementTypeStaticText[contains(@name, 'email') or contains(@name, 'Email') or contains(@name, 'check your email')]"
                        )
                        email_text = email_verification.get_attribute('name')
                        self.logger.info(f"📧 Email verification required: {email_text}")
                        self.logger.info("✅ Email verification screen detected - this is expected")
                        return True
                    except:
                        # No verification screen - might be successful login
                        self.logger.info("✅ No verification screen detected - proceeding to success check")
                        return True
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 6 failed: {e}")
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
                try:
                    element = driver.find_element(AppiumBy.ACCESSIBILITY_ID, indicator)
                    self.logger.info(f"✅ Found success indicator: {indicator}")
                    return True
                except:
                    continue
            
            # If no specific indicators found, check if we're not on login screen
            try:
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number")
                self.logger.error("❌ Still on login screen - login failed")
                return False
            except:
                self.logger.info("✅ Not on login screen - login appears successful")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 7 failed: {e}")
            return False
    
    def checkpoint_8_return_safe_state(self, driver) -> bool:
        """Checkpoint 8: Return to safe state (main feed)"""
        try:
            self.logger.info("🧵 CHECKPOINT 8: Returning to safe state...")
            
            # Try to navigate to main feed if not already there
            try:
                home_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "home-tab")
                home_tab.click()
                self.logger.info("✅ Navigated to home tab")
            except:
                self.logger.info("ℹ️ Home tab not found or already on main feed")
            
            # Verify we're in a safe state
            time.sleep(2)
            
            # Look for any main app elements to confirm we're in the app
            try:
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Threads from Meta")
                self.logger.info("✅ Successfully returned to safe state")
                return True
            except:
                self.logger.warning("⚠️ Could not verify safe state, but continuing")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 8 failed: {e}")
            return False
    
    def run_login_test(self):
        """Run Threads login test using 8-checkpoint system"""
        self.logger.info("🚀 STARTING THREADS LOGIN TEST")
        self.logger.info("=" * 60)
        
        # Setup driver
        if not self.setup_driver():
            self.logger.error("❌ Driver setup failed - aborting test")
            return False
        
        try:
            # Run checkpoint sequence
            checkpoints = self.define_checkpoints()
            success = self.run_checkpoint_sequence(self.driver, checkpoints)
            
            # Final results
            self.logger.info("\n" + "=" * 60)
            self.logger.info("🎯 THREADS LOGIN TEST RESULTS")
            if success:
                self.logger.info("🎉 LOGIN TEST: SUCCESS!")
                self.logger.info("🧵 THREADS LOGIN IMPLEMENTED SUCCESSFULLY!")
            else:
                self.logger.error("❌ LOGIN TEST: FAILED!")
                
            return success
            
        except Exception as e:
            self.logger.error(f"💥 Test execution failed: {e}")
            return False
            
        finally:
            # Cleanup
            if self.driver:
                self.logger.info("🧹 Cleaning up driver...")
                AppiumDriverManager.safe_quit_driver(self.driver)


def main():
    """Main test execution"""
    print("🧵 Threads Login Functionality Test")
    print("===================================")
    print("Testing login with 8-checkpoint system")
    print("Evidence collection enabled")
    print()
    
    # Create and run test
    test = ThreadsLoginTest()
    success = test.run_login_test()
    
    if success:
        print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print("📁 Check evidence directory for screenshots and XML")
    else:
        print("\n❌ TEST FAILED!")
        print("📁 Check evidence directory and logs for details")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
