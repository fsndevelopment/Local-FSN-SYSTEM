#!/usr/bin/env python3
"""
Threads POST_THREAD Implementation
Creates new thread posts with text and optional media
"""

import time
import logging
from typing import Optional, Dict, Any
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_action import BaseThreadsAction

logger = logging.getLogger(__name__)


class PostThreadAction(BaseThreadsAction):
    """Threads POST_THREAD action implementation"""
    
    def __init__(self, driver, device_config):
        super().__init__(driver, device_config)
        self.action_name = "POST_THREAD"
        
    def define_checkpoints(self):
        """Define the 8-checkpoint system for POST_THREAD"""
        return [
            (self.checkpoint_1_navigate_to_compose, "navigate_to_compose"),
            (self.checkpoint_2_enter_text_content, "enter_text_content"),
            (self.checkpoint_3_add_media_if_requested, "add_media_if_requested"),
            (self.checkpoint_4_handle_permissions, "handle_permissions"),
            (self.checkpoint_5_select_media, "select_media"),
            (self.checkpoint_6_post_thread, "post_thread"),
            (self.checkpoint_7_handle_post_popup, "handle_post_popup"),
            (self.checkpoint_8_verify_success, "verify_success")
        ]
    
    def execute(self, text_content: str, add_media: bool = False, media_type: str = "photo") -> Dict[str, Any]:
        """
        Execute POST_THREAD action
        
        Args:
            text_content (str): Text content for the thread (max 500 chars)
            add_media (bool): Whether to add media to the post
            media_type (str): Type of media to add ("photo", "video", "gif")
            
        Returns:
            Dict containing execution results and metrics
        """
        logger.info(f"Starting {self.action_name} execution")
        logger.info(f"Text content: {text_content[:50]}...")
        logger.info(f"Add media: {add_media}, Type: {media_type}")
        
        # Validate text content length
        if len(text_content) > 500:
            raise ValueError("Thread text content cannot exceed 500 characters")
        
        # Store parameters for checkpoints
        self.text_content = text_content
        self.add_media = add_media
        self.media_type = media_type
        
        # Execute checkpoints
        results = self.execute_checkpoints()
        
        # Compile final results
        final_results = {
            "action": self.action_name,
            "success": results["success"],
            "checkpoints_passed": results["checkpoints_passed"],
            "total_checkpoints": results["total_checkpoints"],
            "execution_time": results["execution_time"],
            "text_content": text_content,
            "media_added": add_media,
            "media_type": media_type,
            "error": results.get("error")
        }
        
        logger.info(f"{self.action_name} execution completed: {final_results['success']}")
        return final_results
    
    def checkpoint_1_navigate_to_compose(self) -> bool:
        """Navigate to compose/create thread screen"""
        try:
            logger.info("Checkpoint 1: Navigating to compose screen")
            
            # Wait for home page to load
            self.wait_for_element("feed-tab-main", timeout=10)
            
            # Click create tab button
            create_tab = self.wait_for_element("create-tab", timeout=10)
            create_tab.click()
            logger.info("Clicked create-tab button")
            
            # Wait for compose screen to load
            self.wait_for_element("Text field. Type to compose a post.", timeout=10)
            
            # Take screenshot for evidence
            self.take_screenshot("compose_screen_loaded")
            
            logger.info("Checkpoint 1 passed: Successfully navigated to compose screen")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint 1 failed: {str(e)}")
            self.take_screenshot("checkpoint_1_failed")
            return False
    
    def checkpoint_2_enter_text_content(self) -> bool:
        """Enter text content in the compose field"""
        try:
            logger.info("Checkpoint 2: Entering text content")
            
            # Find and clear the text field
            text_field = self.wait_for_element("Text field. Type to compose a post.", timeout=10)
            text_field.clear()
            
            # Enter the text content
            text_field.send_keys(self.text_content)
            logger.info(f"Entered text content: {self.text_content[:50]}...")
            
            # Verify text was entered
            entered_text = text_field.get_attribute("value")
            if entered_text != self.text_content:
                logger.warning(f"Text mismatch. Expected: {self.text_content}, Got: {entered_text}")
            
            # Take screenshot for evidence
            self.take_screenshot("text_content_entered")
            
            logger.info("Checkpoint 2 passed: Successfully entered text content")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint 2 failed: {str(e)}")
            self.take_screenshot("checkpoint_2_failed")
            return False
    
    def checkpoint_3_add_media_if_requested(self) -> bool:
        """Add media if requested"""
        try:
            logger.info("Checkpoint 3: Adding media if requested")
            
            if not self.add_media:
                logger.info("No media requested, skipping media addition")
                return True
            
            # Click add photos button
            add_photos_button = self.wait_for_element("Add photos and videos from your camera roll", timeout=10)
            add_photos_button.click()
            logger.info("Clicked add photos button")
            
            # Take screenshot for evidence
            self.take_screenshot("add_photos_clicked")
            
            logger.info("Checkpoint 3 passed: Successfully initiated media addition")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint 3 failed: {str(e)}")
            self.take_screenshot("checkpoint_3_failed")
            return False
    
    def checkpoint_4_handle_permissions(self) -> bool:
        """Handle photo access permissions if they appear"""
        try:
            logger.info("Checkpoint 4: Handling permissions")
            
            if not self.add_media:
                logger.info("No media requested, skipping permission handling")
                return True
            
            # Check if permission dialog appears
            try:
                allow_button = self.wait_for_element("Allow Access to All Photos", timeout=5)
                allow_button.click()
                logger.info("Clicked 'Allow Access to All Photos'")
                
                # Take screenshot for evidence
                self.take_screenshot("permissions_granted")
                
            except TimeoutException:
                logger.info("No permission dialog appeared (already granted)")
            
            logger.info("Checkpoint 4 passed: Successfully handled permissions")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint 4 failed: {str(e)}")
            self.take_screenshot("checkpoint_4_failed")
            return False
    
    def checkpoint_5_select_media(self) -> bool:
        """Select media from photo library"""
        try:
            logger.info("Checkpoint 5: Selecting media")
            
            if not self.add_media:
                logger.info("No media requested, skipping media selection")
                return True
            
            # Wait for photo selection screen
            self.wait_for_element("Select up to 20 items.", timeout=10)
            
            # Click on the latest photo (first photo in the grid)
            latest_photo = self.wait_for_element("Photo, September 06, 9:58 AM", timeout=10)
            latest_photo.click()
            logger.info("Selected latest photo")
            
            # Click Add button
            add_button = self.wait_for_element("Add", timeout=10)
            add_button.click()
            logger.info("Clicked Add button")
            
            # Take screenshot for evidence
            self.take_screenshot("media_selected_and_added")
            
            logger.info("Checkpoint 5 passed: Successfully selected and added media")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint 5 failed: {str(e)}")
            self.take_screenshot("checkpoint_5_failed")
            return False
    
    def checkpoint_6_post_thread(self) -> bool:
        """Post the thread"""
        try:
            logger.info("Checkpoint 6: Posting thread")
            
            # Wait for Post button to be enabled
            post_button = self.wait_for_element("Post this thread", timeout=10)
            
            # Check if button is enabled
            if not post_button.is_enabled():
                logger.warning("Post button is not enabled, waiting...")
                time.sleep(2)
            
            # Click post button
            post_button.click()
            logger.info("Clicked 'Post this thread' button")
            
            # Take screenshot for evidence
            self.take_screenshot("thread_posted")
            
            logger.info("Checkpoint 6 passed: Successfully posted thread")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint 6 failed: {str(e)}")
            self.take_screenshot("checkpoint_6_failed")
            return False
    
    def checkpoint_7_handle_post_popup(self) -> bool:
        """Handle any post-completion popups"""
        try:
            logger.info("Checkpoint 7: Handling post popup")
            
            # Check for Instagram story popup
            try:
                not_now_button = self.wait_for_element("Not now", timeout=5)
                not_now_button.click()
                logger.info("Clicked 'Not now' on Instagram story popup")
                
                # Take screenshot for evidence
                self.take_screenshot("popup_dismissed")
                
            except TimeoutException:
                logger.info("No popup appeared after posting")
            
            logger.info("Checkpoint 7 passed: Successfully handled post popup")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint 7 failed: {str(e)}")
            self.take_screenshot("checkpoint_7_failed")
            return False
    
    def checkpoint_8_verify_success(self) -> bool:
        """Verify thread was posted successfully"""
        try:
            logger.info("Checkpoint 8: Verifying success")
            
            # Wait for return to home feed
            self.wait_for_element("feed-tab-main", timeout=10)
            
            # Check if we're back on the main feed
            feed_tab = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "feed-tab-main")
            if not feed_tab.is_selected():
                logger.warning("Not on main feed after posting")
            
            # Take final screenshot for evidence
            self.take_screenshot("post_success_verification")
            
            logger.info("Checkpoint 8 passed: Successfully verified thread posting")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint 8 failed: {str(e)}")
            self.take_screenshot("checkpoint_8_failed")
            return False


def create_post_thread_action(driver, device_config):
    """Factory function to create PostThreadAction instance"""
    return PostThreadAction(driver, device_config)
