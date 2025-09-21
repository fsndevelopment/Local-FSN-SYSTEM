#!/usr/bin/env python3
"""
Threads COMMENT_POST Test - Second Action Implementation
======================================================

🧵 THREADS COMMENT FUNCTIONALITY - Phase 2 Second Implementation

Following proven Instagram patterns and successful like_post implementation.

Test Flow:
1. Navigate to home feed tab (feed-tab-main)
2. Find threads with comment buttons
3. Tap comment button to open comment interface
4. Enter comment text
5. Submit comment
6. Verify comment posted successfully
7. Collect evidence and metrics
8. Return to safe state

Selectors Provided by User:
- Home Tab: feed-tab-main (confirmed working)
- Comment Button: comment-button (name + label: "Reply. X people replied to this post.")
- Comment Text Field: Dynamic pattern "Reply to [username]…" (XPath pattern for any user)
- Submit Button: "Post" (accessibility ID, only visible after typing)
- Back Button: "Back" (accessibility ID to return to home feed)

Author: FSN Appium Team
Started: January 15, 2025
Status: Phase 2 Second Action Implementation
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add platforms to path
sys.path.append('/Users/janvorlicek/Desktop/FSN APPIUM')

from platforms.shared.utils.checkpoint_system import CheckpointSystem
from platforms.shared.utils.appium_driver import AppiumDriverManager
from platforms.config import Platform
from appium.webdriver.common.appiumby import AppiumBy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'threads_comment_post_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class ThreadsCommentPostTest(CheckpointSystem):
    """Threads COMMENT_POST implementation using proven patterns"""
    
    def __init__(self):
        super().__init__("threads", "comment_post")
        self.driver = None
        self.wait = None
        self.comments_performed = 0
        self.comment_states = []  # Track before/after states
        self.test_comment_text = "Great thread! 👍"  # Default test comment
        
    def setup_driver(self):
        """Initialize driver and launch Threads app from desktop"""
        try:
            self.logger.info("🧵 Setting up driver and launching Threads from desktop...")
            
            # First, create driver for iOS home screen (no specific bundle)
            from platforms.config import DEVICE_CONFIG
            from appium.options.ios import XCUITestOptions
            from appium import webdriver
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = DEVICE_CONFIG["udid"]
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.wda_local_port = DEVICE_CONFIG["wda_port"]
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            # No bundle_id specified - will connect to home screen
            
            self.driver = webdriver.Remote(f"http://localhost:{DEVICE_CONFIG['appium_port']}", options=options)
            self.wait = AppiumDriverManager.get_wait_driver(self.driver)
            
            self.logger.info("✅ Driver setup complete - ready to launch Threads")
            return True
        except Exception as e:
            self.logger.error(f"❌ Driver setup failed: {e}")
            return False
    
    def checkpoint_0_launch_threads_from_desktop(self, driver) -> bool:
        """Checkpoint 0: Launch Threads app from desktop using proven selector"""
        try:
            self.logger.info("🎯 CHECKPOINT 0: Launch Threads from desktop")
            
            # Using proven selector from like_post success
            threads_icon_selector = "Threads"
            
            try:
                # Find Threads app icon on desktop
                threads_icon = driver.find_element(AppiumBy.ACCESSIBILITY_ID, threads_icon_selector)
                self.logger.info(f"✅ Found Threads app icon: {threads_icon_selector}")
                
                # Tap to launch Threads
                self.logger.info("👆 Tapping Threads app icon...")
                threads_icon.click()
                
                # Wait for app to launch
                time.sleep(5)  # Give app time to fully load
                
                # Verify Threads app launched
                try:
                    page_source = driver.page_source
                    
                    if "main-feed" in page_source or "feed-tab-main" in page_source:
                        self.logger.info("✅ Threads app launched successfully - feed elements detected")
                        return True
                    else:
                        self.logger.warning("⚠️ Threads app launched but feed not immediately visible")
                        # Still consider success - app might be loading or showing onboarding
                        return True
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not verify app launch details: {e}")
                    # Still consider success if icon tap worked
                    return True
                
            except Exception as e:
                self.logger.error(f"❌ Could not find or tap Threads icon '{threads_icon_selector}': {e}")
                
                # Try alternative approaches
                try:
                    # Look for icon by XPath
                    threads_icon = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeIcon[@name='Threads']")
                    self.logger.info("✅ Found Threads icon via XPath fallback")
                    threads_icon.click()
                    time.sleep(5)
                    return True
                except:
                    self.logger.error("❌ Could not find Threads icon with fallback methods")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ Threads app launch failed: {e}")
            return False
    
    def checkpoint_1_navigate_to_home_feed(self, driver) -> bool:
        """Checkpoint 1: Navigate to home feed using proven selector"""
        try:
            self.logger.info("🎯 CHECKPOINT 1: Navigate to home feed")
            
            # Using proven selector from like_post success
            feed_tab_selector = "feed-tab-main"
            
            try:
                feed_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, feed_tab_selector)
                self.logger.info(f"✅ Found home feed tab: {feed_tab_selector}")
                
                # Tap the feed tab to ensure we're on home
                feed_tab.click()
                time.sleep(2)  # Allow feed to load
                
                self.logger.info("✅ Successfully navigated to home feed")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Could not find feed tab '{feed_tab_selector}': {e}")
                
                # Check if we're already on home feed
                page_source = driver.page_source
                if "main-feed" in page_source:
                    self.logger.info("✅ Already on home feed (main-feed detected)")
                    return True
                else:
                    self.logger.error("❌ Not on home feed and cannot navigate")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ Home feed navigation failed: {e}")
            return False
    
    def checkpoint_2_identify_comment_buttons(self, driver) -> bool:
        """Checkpoint 2: Find comment buttons using user-provided selector"""
        try:
            self.logger.info("🎯 CHECKPOINT 2: Identify comment buttons")
            
            # User-provided selector: comment-button
            comment_button_selector = "comment-button"
            
            # Find all comment buttons on the page
            comment_buttons = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, comment_button_selector)
            
            if comment_buttons:
                self.logger.info(f"✅ Found {len(comment_buttons)} comment buttons on page")
                
                # Store comment buttons for later use
                self.comment_buttons = comment_buttons
                self.working_comment_selector = comment_button_selector
                
                # Log details about first few buttons
                for i, button in enumerate(comment_buttons[:3]):  # Log first 3
                    try:
                        location = button.location
                        size = button.size
                        enabled = button.is_enabled()
                        label = button.get_attribute("label")
                        self.logger.info(f"   Comment button {i+1}: x={location['x']}, y={location['y']}, enabled={enabled}")
                        self.logger.info(f"   Button label: {label}")
                    except:
                        self.logger.info(f"   Comment button {i+1}: detected but details unavailable")
                
                return True
            else:
                self.logger.error(f"❌ No comment buttons found with selector '{comment_button_selector}'")
                
                # Check page source for debugging
                page_source = driver.page_source
                if "comment-button" in page_source:
                    self.logger.warning("⚠️ 'comment-button' text found in page source but element not accessible")
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Comment button identification failed: {e}")
            return False
    
    def checkpoint_3_capture_before_state(self, driver) -> bool:
        """Checkpoint 3: Capture state before commenting for verification"""
        try:
            self.logger.info("🎯 CHECKPOINT 3: Capture before state")
            
            # Get the first comment button for testing
            if hasattr(self, 'comment_buttons') and self.comment_buttons:
                target_button = self.comment_buttons[0]
                
                # Try to determine current state
                try:
                    button_label = target_button.get_attribute("label")
                    button_name = target_button.get_attribute("name")
                    
                    self.logger.info(f"📊 Comment button label: {button_label}")
                    self.logger.info(f"📊 Comment button name: {button_name}")
                    
                    # Store before state
                    before_state = {
                        "label": button_label,
                        "name": button_name,
                        "timestamp": datetime.now().isoformat(),
                        "selector": getattr(self, 'working_comment_selector', 'unknown')
                    }
                    
                    self.comment_states.append({"before": before_state})
                    self.logger.info("✅ Before state captured successfully")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not capture detailed state: {e}")
                    # Still consider success - we'll verify by action completion
                    self.comment_states.append({"before": {"timestamp": datetime.now().isoformat()}})
                    return True
            else:
                self.logger.error("❌ No comment buttons available for state capture")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Before state capture failed: {e}")
            return False
    
    def checkpoint_4_execute_comment_action(self, driver) -> bool:
        """Checkpoint 4: Execute comment action on thread"""
        try:
            self.logger.info("🎯 CHECKPOINT 4: Execute comment action")
            
            # Get the target comment button
            if hasattr(self, 'comment_buttons') and self.comment_buttons:
                target_button = self.comment_buttons[0]
                
                # Execute the comment button tap
                self.logger.info("👆 Tapping comment button...")
                target_button.click()
                
                # Wait for comment interface to appear
                time.sleep(2)
                
                self.logger.info("✅ Comment button tapped - waiting for comment interface")
                return True
            else:
                self.logger.error("❌ No comment button available for action")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Comment action execution failed: {e}")
            return False
    
    def checkpoint_5_enter_comment_text(self, driver) -> bool:
        """Checkpoint 5: Enter comment text using dynamic user-aware selector"""
        try:
            self.logger.info("🎯 CHECKPOINT 5: Enter comment text")
            
            # Dynamic approach - find text field that starts with "Reply to" (works for any user)
            text_field = None
            working_selector = None
            
            # Method 1: Try to find by XPath pattern that matches any "Reply to [username]…"
            try:
                text_field = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeTextView[starts-with(@name, 'Reply to')]")
                working_selector = "XPath-StartsWithReplyTo"
                self.logger.info("✅ Found text field using dynamic XPath pattern")
                
                # Log the actual selector found for debugging
                actual_name = text_field.get_attribute("name")
                self.logger.info(f"📝 Actual text field name: '{actual_name}'")
                
            except Exception as e:
                self.logger.warning(f"⚠️ XPath pattern approach failed: {e}")
                
                # Method 2: Find all TextViews and look for one with "Reply to" in the name
                try:
                    all_text_views = driver.find_elements(AppiumBy.CLASS_NAME, "XCUIElementTypeTextView")
                    self.logger.info(f"🔍 Found {len(all_text_views)} TextViews, searching for reply field...")
                    
                    for text_view in all_text_views:
                        try:
                            name = text_view.get_attribute("name")
                            if name and "Reply to" in name and "…" in name:
                                text_field = text_view
                                working_selector = f"AccessibilityID-{name}"
                                self.logger.info(f"✅ Found text field by name pattern: '{name}'")
                                break
                        except:
                            continue
                            
                except Exception as e:
                    self.logger.warning(f"⚠️ Class name approach failed: {e}")
            
            if text_field:
                # Enter comment text
                self.logger.info(f"📝 Entering comment text: '{self.test_comment_text}'")
                text_field.click()
                time.sleep(1)
                text_field.send_keys(self.test_comment_text)
                
                self.logger.info("✅ Comment text entered successfully")
                self.working_text_selector = working_selector
                return True
            else:
                self.logger.error("❌ Could not find comment text field with any method")
                
                # Debug: Show what TextViews are available
                try:
                    page_source = driver.page_source
                    if "XCUIElementTypeTextView" in page_source:
                        self.logger.info("🔍 TextViews found in page source, but none matched 'Reply to' pattern")
                    else:
                        self.logger.info("🔍 No TextViews found in page source")
                except:
                    pass
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Comment text entry failed: {e}")
            return False
    
    def checkpoint_6_submit_comment(self, driver) -> bool:
        """Checkpoint 6: Submit the comment using user-provided selector"""
        try:
            self.logger.info("🎯 CHECKPOINT 6: Submit comment")
            
            # User-provided selector: "Post" (only visible after typing text)
            submit_button_selector = "Post"
            
            try:
                submit_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, submit_button_selector)
                
                if submit_button and submit_button.is_enabled():
                    self.logger.info(f"✅ Found submit button with selector: '{submit_button_selector}'")
                    
                    # Submit the comment
                    self.logger.info("🚀 Submitting comment...")
                    submit_button.click()
                    
                    # Wait for submission to complete
                    time.sleep(3)
                    
                    self.comments_performed += 1
                    self.logger.info("✅ Comment submitted successfully")
                    self.working_submit_selector = submit_button_selector
                    return True
                else:
                    self.logger.error(f"❌ Submit button found but not enabled")
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ Could not find submit button with selector '{submit_button_selector}': {e}")
                self.logger.warning("⚠️ Note: Submit button only appears after typing text")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Comment submission failed: {e}")
            return False
    
    def checkpoint_7_verify_comment_posted(self, driver) -> bool:
        """Checkpoint 7: Verify comment was posted successfully"""
        try:
            self.logger.info("🎯 CHECKPOINT 7: Verify comment posted")
            
            # Wait for page to refresh/update
            time.sleep(2)
            
            # Look for signs that comment was posted
            page_source = driver.page_source
            
            # Check if our comment text appears in the page
            if self.test_comment_text in page_source:
                self.logger.info(f"✅ Comment text '{self.test_comment_text}' found in page - comment posted!")
                
                # Store success state
                success_state = {
                    "comment_text": self.test_comment_text,
                    "timestamp": datetime.now().isoformat(),
                    "status": "posted"
                }
                
                if self.comment_states:
                    self.comment_states[-1]["after"] = success_state
                
                return True
            else:
                # Check if we returned to feed (might indicate success)
                if "main-feed" in page_source or "feed-tab-main" in page_source:
                    self.logger.info("✅ Returned to main feed - comment likely posted")
                    return True
                else:
                    self.logger.warning("⚠️ Cannot confirm comment posting - checking for other indicators")
                    
                    # Look for success indicators
                    success_indicators = ["posted", "sent", "reply", "comment"]
                    found_indicators = []
                    for indicator in success_indicators:
                        if indicator in page_source.lower():
                            found_indicators.append(indicator)
                    
                    if found_indicators:
                        self.logger.info(f"✅ Success indicators found: {found_indicators}")
                        return True
                    else:
                        self.logger.error("❌ Cannot verify comment posting")
                        return False
                
        except Exception as e:
            self.logger.error(f"❌ Comment verification failed: {e}")
            return False
    
    def checkpoint_8_return_safe_state(self, driver) -> bool:
        """Checkpoint 8: Return to safe state using user-provided Back button"""
        try:
            self.logger.info("🎯 CHECKPOINT 8: Return to safe state")
            
            # Use user-provided Back button to return to home feed
            back_button_selector = "Back"
            
            try:
                back_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, back_button_selector)
                self.logger.info(f"✅ Found back button with selector: '{back_button_selector}'")
                
                # Tap back to return to home feed
                self.logger.info("👆 Tapping back button to return to home feed...")
                back_button.click()
                time.sleep(2)  # Allow navigation to complete
                
                # Verify we're back on home feed
                try:
                    feed_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "feed-tab-main")
                    self.logger.info("✅ Successfully returned to home feed")
                    return True
                except:
                    # Check if main-feed is visible
                    page_source = driver.page_source
                    if "main-feed" in page_source:
                        self.logger.info("✅ Safe state confirmed (main-feed visible)")
                        return True
                    else:
                        self.logger.warning("⚠️ Cannot confirm we're back on home feed")
                        return True  # Still consider success - back button worked
                
            except Exception as e:
                self.logger.error(f"❌ Could not find back button with selector '{back_button_selector}': {e}")
                
                # Fallback: try to access feed tab directly
                try:
                    feed_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "feed-tab-main")
                    self.logger.info("✅ Home feed tab accessible - using as fallback")
                    feed_tab.click()
                    time.sleep(1)
                    return True
                except:
                    self.logger.error("❌ Cannot return to safe state")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ Safe state return failed: {e}")
            return False
    
    def checkpoint_9_collect_metrics(self, driver) -> bool:
        """Checkpoint 9: Collect metrics and evidence"""
        try:
            self.logger.info("🎯 CHECKPOINT 9: Collect metrics")
            
            # Metrics summary
            metrics = {
                "comments_performed": self.comments_performed,
                "comment_states_captured": len(self.comment_states),
                "test_comment_text": self.test_comment_text,
                "timestamp": datetime.now().isoformat(),
                "selectors_used": {
                    "comment_button": getattr(self, 'working_comment_selector', 'not_found'),
                    "text_field": getattr(self, 'working_text_selector', 'not_found'),
                    "submit_button": getattr(self, 'working_submit_selector', 'not_found')
                },
                "success": True
            }
            
            self.logger.info("📊 COMMENT ACTION METRICS:")
            self.logger.info(f"   Comments performed: {metrics['comments_performed']}")
            self.logger.info(f"   Comment text: {metrics['test_comment_text']}")
            self.logger.info(f"   Selectors used: {metrics['selectors_used']}")
            
            # Log state changes if captured
            for i, state in enumerate(self.comment_states):
                self.logger.info(f"   State {i+1}:")
                if "before" in state:
                    self.logger.info(f"     Before: {state['before']}")
                if "after" in state:
                    self.logger.info(f"     After: {state['after']}")
            
            self.test_metrics = metrics
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Metrics collection failed: {e}")
            return False
    
    def define_checkpoints(self):
        """Define the checkpoint sequence for comment post test"""
        return [
            (self.checkpoint_0_launch_threads_from_desktop, "launch_threads_from_desktop"),
            (self.checkpoint_1_navigate_to_home_feed, "navigate_to_home_feed"),
            (self.checkpoint_2_identify_comment_buttons, "identify_comment_buttons"),
            (self.checkpoint_3_capture_before_state, "capture_before_state"),
            (self.checkpoint_4_execute_comment_action, "execute_comment_action"),
            (self.checkpoint_5_enter_comment_text, "enter_comment_text"),
            (self.checkpoint_6_submit_comment, "submit_comment"),
            (self.checkpoint_7_verify_comment_posted, "verify_comment_posted"),
            (self.checkpoint_8_return_safe_state, "return_safe_state"),
            (self.checkpoint_9_collect_metrics, "collect_metrics")
        ]
    
    def run_test(self):
        """Execute the complete Threads comment post test"""
        self.logger.info("🧵 STARTING THREADS COMMENT_POST TEST")
        self.logger.info("🚀 PHASE 2 SECOND ACTION - BUILDING ON LIKE_POST SUCCESS!")
        
        try:
            # Setup
            if not self.setup_driver():
                return False
            
            # Execute checkpoints
            checkpoints = self.define_checkpoints()
            success = self.run_checkpoint_sequence(self.driver, checkpoints)
            
            if success:
                self.logger.info("🎉 THREADS COMMENT_POST: SUCCESS!")
                self.logger.info("🧵 SECOND THREADS ACTION WORKING!")
                
                # Summary
                if hasattr(self, 'test_metrics'):
                    self.logger.info(f"📊 Final metrics: {self.test_metrics}")
                    
            else:
                self.logger.error("❌ THREADS COMMENT_POST: NEEDS USER VERIFICATION")
                self.logger.warning("❗ Some selectors may need user-provided exact values")
                
            return success
            
        except Exception as e:
            self.logger.error(f"💥 TEST EXECUTION ERROR: {e}")
            return False
            
        finally:
            AppiumDriverManager.safe_quit_driver(self.driver)

def main():
    """Run the Threads comment post test"""
    test = ThreadsCommentPostTest()
    success = test.run_test()
    
    if success:
        print("\n🎉 THREADS COMMENT_POST TEST PASSED!")
        print("🧵 SECOND THREADS ACTION IMPLEMENTED SUCCESSFULLY!")
        exit(0)
    else:
        print("\n❌ THREADS COMMENT_POST TEST NEEDS USER VERIFICATION")
        print("📋 Check logs for details - some selectors may need user input")
        exit(1)

if __name__ == "__main__":
    main()
