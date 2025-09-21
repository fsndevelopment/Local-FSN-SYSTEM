#!/usr/bin/env python3
"""
Instagram LOGIN Test - Authentication Action
===========================================

📸 INSTAGRAM LOGIN FUNCTIONALITY - Phase 2 Implementation

Following proven Instagram patterns with user-provided exact selectors.

Test Flow:
1. Launch Instagram app from desktop
2. Navigate to login screen (Log in button)
3. Enter username/email/mobile number
4. Enter password
5. Click login button
6. Handle verification if required
7. Verify login success
8. Return to safe state

Login Selectors (Instagram-specific):
- Login Button: "Log In" (XCUIElementTypeButton)
- Username Field: "Phone number, username, or email" (accessibility ID)
- Password Field: "Password" (accessibility ID)
- Login Submit: "Log In" button after entering credentials
- Instagram Logo: "Instagram" (accessibility ID)

Author: FSN Appium Team
Started: January 15, 2025
Status: Phase 2 Authentication Implementation
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add backend to path
sys.path.append('/Users/janvorlicek/Desktop/FSN-APPIUM-main/backend-appium-integration')

from platforms.shared.utils.checkpoint_system import CheckpointSystem
from platforms.shared.utils.appium_driver import AppiumDriverManager
from platforms.config import Platform
from appium.webdriver.common.appiumby import AppiumBy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'instagram_login_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class InstagramLoginTest(CheckpointSystem):
    """Instagram LOGIN test using proven 8-checkpoint system"""
    
    def __init__(self):
        super().__init__("instagram", "login")
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Initialize Appium driver for Instagram testing - start from desktop"""
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
            
            # Use backend Appium port
            self.driver = webdriver.Remote("http://localhost:4735", options=options)
            
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
        """Define the 9-checkpoint system for Instagram login"""
        return [
            (self.checkpoint_1_launch_instagram_app, "launch_instagram_app"),
            (self.checkpoint_2_logout_if_logged_in, "logout_if_logged_in"),
            (self.checkpoint_3_navigate_to_login, "navigate_to_login"),
            (self.checkpoint_4_enter_username, "enter_username"),
            (self.checkpoint_5_enter_password, "enter_password"),
            (self.checkpoint_6_click_login_button, "click_login_button"),
            (self.checkpoint_7_handle_verification, "handle_verification"),
            (self.checkpoint_8_verify_login_success, "verify_login_success"),
            (self.checkpoint_9_return_safe_state, "return_safe_state")
        ]
    
    def checkpoint_1_launch_instagram_app(self, driver) -> bool:
        """Checkpoint 1: Launch Instagram app from desktop"""
        try:
            self.logger.info("📸 CHECKPOINT 1: Launching Instagram app from desktop...")
            
            # Launch Instagram app using desktop icon (XCUIElementTypeIcon)
            instagram_app = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Instagram")
            app_name = instagram_app.get_attribute('name')
            self.logger.info(f"📱 Found Instagram app icon: {app_name}")
            
            instagram_app.click()
            time.sleep(5)  # Allow app to fully load
            
            # Verify app launched successfully by looking for Instagram UI elements
            try:
                # Look for Instagram UI elements to confirm launch
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Instagram")
                self.logger.info("✅ Instagram app launched successfully")
                return True
            except:
                # Try alternative verification - look for any Instagram-specific elements
                try:
                    driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeStaticText[contains(@name, 'Instagram')]")
                    self.logger.info("✅ Instagram app launched successfully (alternative verification)")
                    return True
                except:
                    self.logger.error("❌ Instagram app launch verification failed")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 1 failed: {e}")
            return False
    
    def checkpoint_2_logout_if_logged_in(self, driver) -> bool:
        """Checkpoint 2: Logout if already logged in"""
        try:
            self.logger.info("📸 CHECKPOINT 2: Checking if already logged in and logging out...")
            
            # Check if we're on Instagram home screen (already logged in)
            try:
                # Look for Instagram home screen elements
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, "mainfeed-tab")
                self.logger.info("✅ Already logged in - attempting to logout")
                
                # Try to find profile tab and logout
                try:
                    profile_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "profile-tab")
                    profile_tab.click()
                    time.sleep(2)
                    
                    # Look for settings or menu button
                    try:
                        settings_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Settings")
                        settings_button.click()
                        time.sleep(2)
                        
                        # Look for logout option
                        try:
                            logout_button = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Log Out') or contains(@name, 'Sign Out')]")
                            logout_button.click()
                            time.sleep(3)
                            self.logger.info("✅ Successfully logged out")
                        except:
                            self.logger.info("ℹ️  Could not find logout button, continuing...")
                    except:
                        self.logger.info("ℹ️  Could not find settings, continuing...")
                except:
                    self.logger.info("ℹ️  Could not find profile tab, continuing...")
                
                return True
                
            except:
                self.logger.info("✅ Not logged in - proceeding with login")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 2 failed: {e}")
            return False
    
    def checkpoint_3_navigate_to_login(self, driver) -> bool:
        """Checkpoint 3: Navigate to login screen"""
        try:
            self.logger.info("📸 CHECKPOINT 3: Navigating to login screen...")
            
            # Check if we're already on login screen (Instagram often shows login directly)
            try:
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number")
                self.logger.info("✅ Already on login screen - Instagram shows login form directly")
                return True
            except:
                pass
            
            # If not on login screen, look for "Log In" button
            try:
                # Try to find the main "Log In" button
                login_button = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeButton[@name='Log in']")
                self.logger.info("✅ Found 'Log in' button")
                login_button.click()
                time.sleep(3)
                return True
            except:
                # Try alternative selectors for login button
                try:
                    login_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Log in")
                    self.logger.info("✅ Found 'Log in' button (accessibility ID)")
                    login_button.click()
                    time.sleep(3)
                    return True
                except:
                    self.logger.error("❌ Could not find login screen elements")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 3 failed: {e}")
            return False
    
    def checkpoint_4_enter_username(self, driver) -> bool:
        """Checkpoint 4: Enter username/email/mobile number"""
        try:
            self.logger.info("📸 CHECKPOINT 4: Entering username...")
            
            # Find username field
            username_field = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number")
            self.logger.info("✅ Found username field")
            
            # Clear field and enter username
            username_field.clear()
            username_field.send_keys("rwoanzo2u6")  # Real Instagram username
            self.logger.info("✅ Username entered successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 4 failed: {e}")
            return False
    
    def checkpoint_5_enter_password(self, driver) -> bool:
        """Checkpoint 5: Enter password"""
        try:
            self.logger.info("📸 CHECKPOINT 5: Entering password...")
            
            # Find password field
            password_field = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Password")
            self.logger.info("✅ Found password field")
            
            # Clear field and enter password
            password_field.clear()
            password_field.send_keys("dat9S7FN0mls")  # Real Instagram password
            self.logger.info("✅ Password entered successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 5 failed: {e}")
            return False
    
    def checkpoint_6_click_login_button(self, driver) -> bool:
        """Checkpoint 6: Click login button"""
        try:
            self.logger.info("📸 CHECKPOINT 6: Clicking login button...")
            
            # Find and click the login button
            login_button = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeButton[@name='Log in']")
            self.logger.info("✅ Found login button")
            
            login_button.click()
            time.sleep(3)  # Wait for response
            self.logger.info("✅ Login button clicked successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 6 failed: {e}")
            return False
    
    def checkpoint_7_handle_verification(self, driver) -> bool:
        """Checkpoint 7: Handle verification if required"""
        try:
            self.logger.info("📸 CHECKPOINT 7: Checking for verification requirements...")
            
            # Wait 5 seconds for 2FA page to load
            self.logger.info("⏳ Waiting 5 seconds for 2FA page to load...")
            time.sleep(5)
            
            # Check for 2FA code input field
            try:
                # Look for 2FA code input field
                code_field = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeTextField[contains(@name, 'code') or contains(@name, 'Code') or contains(@name, 'verification')]")
                self.logger.info("✅ Found 2FA code input field")
                
                # Generate 6-digit TOTP code from the secret key
                import pyotp
                secret_key = "CDLRYVT3MCBKFXGPHHSCGUTQKSZR36HW"
                totp = pyotp.TOTP(secret_key)
                six_digit_code = totp.now()
                self.logger.info(f"🔐 Generated 6-digit TOTP code: {six_digit_code}")
                
                # Enter the 6-digit 2FA code immediately
                code_field.clear()
                code_field.send_keys(six_digit_code)
                self.logger.info("✅ 2FA code entered successfully")
                
                # Immediately look for submit/continue button and click
                try:
                    submit_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Continue")
                    submit_button.click()
                    self.logger.info("✅ 2FA Continue button clicked immediately")
                    time.sleep(1)  # Short wait for verification
                except:
                    # Try alternative selectors
                    try:
                        submit_button = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeButton[@name='Continue']")
                        submit_button.click()
                        self.logger.info("✅ 2FA Continue button clicked immediately (XPath)")
                        time.sleep(1)  # Short wait for verification
                    except:
                        self.logger.info("ℹ️  No Continue button found, code may auto-submit")
                
                return True
                
            except:
                # Check for other verification indicators
                verification_indicators = [
                    "Enter confirmation code",
                    "Verify your account", 
                    "Two-factor authentication",
                    "Security check",
                    "Enter code"
                ]
                
                for indicator in verification_indicators:
                    try:
                        driver.find_element(AppiumBy.XPATH, f"//XCUIElementTypeStaticText[contains(@name, '{indicator}')]")
                        self.logger.info(f"⚠️  Verification required: {indicator}")
                        self.logger.info("⏸️  Manual verification needed - pausing test")
                        time.sleep(10)  # Give time for manual verification
                        return True
                    except:
                        continue
                
                # Check for error messages
                try:
                    error_element = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeStaticText[contains(@name, 'incorrect') or contains(@name, 'error') or contains(@name, 'invalid')]")
                    error_text = error_element.get_attribute('name')
                    self.logger.warning(f"⚠️  Login error detected: {error_text}")
                    return False
                except:
                    pass
                
                self.logger.info("✅ No verification required")
                return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 7 failed: {e}")
            return False
    
    def checkpoint_8_verify_login_success(self, driver) -> bool:
        """Checkpoint 8: Verify login success"""
        try:
            self.logger.info("📸 CHECKPOINT 8: Verifying login success...")
            
            # Look for Instagram home screen elements
            success_indicators = [
                "mainfeed-tab",  # Home tab
                "search-tab",    # Search tab
                "reels-tab",     # Reels tab
                "profile-tab",   # Profile tab
                "Instagram"      # Instagram logo
            ]
            
            for indicator in success_indicators:
                try:
                    driver.find_element(AppiumBy.ACCESSIBILITY_ID, indicator)
                    self.logger.info(f"✅ Login successful - found {indicator}")
                    return True
                except:
                    continue
            
            # Alternative verification - look for any Instagram-specific UI
            try:
                driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Home') or contains(@name, 'Search') or contains(@name, 'Reels')]")
                self.logger.info("✅ Login successful - found navigation elements")
                return True
            except:
                self.logger.error("❌ Could not verify login success")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 8 failed: {e}")
            return False
    
    def checkpoint_9_return_safe_state(self, driver) -> bool:
        """Checkpoint 9: Return to safe state"""
        try:
            self.logger.info("📸 CHECKPOINT 9: Returning to safe state...")
            
            # Navigate to home screen if not already there
            try:
                home_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "mainfeed-tab")
                home_tab.click()
                time.sleep(2)
                self.logger.info("✅ Navigated to home screen")
            except:
                self.logger.info("ℹ️  Already on home screen or navigation not available")
            
            # Log out if needed (optional - comment out if you want to stay logged in)
            try:
                # Look for profile tab to access settings
                profile_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "profile-tab")
                profile_tab.click()
                time.sleep(2)
                
                # Look for settings/logout option (this may vary)
                # For now, just return to home
                home_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "mainfeed-tab")
                home_tab.click()
                time.sleep(2)
                
                self.logger.info("✅ Returned to safe state (home screen)")
            except:
                self.logger.info("ℹ️  Safe state achieved")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 9 failed: {e}")
            return False

def main():
    """Main test execution"""
    print("📸 INSTAGRAM LOGIN FUNCTIONALITY TEST")
    print("=" * 50)
    print("Starting Instagram login test...")
    print()
    
    # Create test instance
    test = InstagramLoginTest()
    
    # Setup driver
    if not test.setup_driver():
        print("❌ Failed to setup driver. Exiting.")
        return False
    
    # Run the test
    checkpoints = test.define_checkpoints()
    success = test.run_checkpoint_sequence(test.driver, checkpoints)
    
    # Cleanup
    if test.driver:
        test.driver.quit()
    
    if success:
        print("\n🎉 INSTAGRAM LOGIN TEST COMPLETED SUCCESSFULLY!")
        print("✅ All checkpoints passed")
    else:
        print("\n❌ INSTAGRAM LOGIN TEST FAILED!")
        print("❌ Some checkpoints failed - check logs for details")
    
    return success

if __name__ == "__main__":
    main()
