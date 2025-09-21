#!/usr/bin/env python3
"""
Threads Base Action Class
========================

Base class for all Threads automation actions with integrated logging system.
Provides common functionality and integrates with the checkpoint system.

Key Features:
- Integrated logging system
- Checkpoint system integration
- Common error handling
- Performance tracking
- Evidence collection

Author: FSN Appium Team
Last Updated: January 15, 2025
Status: Production-ready
"""

import time
import logging
from typing import Dict, Any, Optional, List
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..shared.utils.checkpoint_system import CheckpointSystem
from .utils.logging_system import ThreadsLoggingSystem

class BaseThreadsAction(CheckpointSystem):
    """Base class for all Threads automation actions"""
    
    def __init__(self, driver: WebDriver, device_config: Dict[str, Any]):
        super().__init__("threads", self.__class__.__name__.lower())
        self.driver = driver
        self.device_config = device_config
        self.wait = WebDriverWait(driver, 10)
        
        # Initialize logging system
        device_id = device_config.get("udid", "unknown")
        self.logger_system = ThreadsLoggingSystem(device_id=device_id)
        
        # Action tracking
        self.current_action_id = None
        self.start_time = None
        
    def start_action_logging(self, action_name: str, action_type: str, **kwargs) -> str:
        """Start logging for the current action"""
        self.current_action_id = self.logger_system.start_action(
            action_name, action_type, **kwargs
        )
        self.start_time = time.time()
        return self.current_action_id
    
    def log_checkpoint_with_evidence(self, checkpoint_name: str, success: bool, 
                                   error_message: str = None) -> None:
        """Log a checkpoint with evidence collection"""
        self.logger_system.log_checkpoint(
            checkpoint_name, success, self.driver, error_message
        )
    
    def log_error_with_evidence(self, error_type: str, error_message: str) -> None:
        """Log an error with evidence collection"""
        self.logger_system.log_error(error_type, error_message, self.driver)
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "seconds") -> None:
        """Log a performance metric"""
        self.logger_system.log_performance(metric_name, value, unit)
    
    def end_action_logging(self, success: bool) -> Dict[str, Any]:
        """End action logging and return results"""
        if self.start_time:
            duration = time.time() - self.start_time
            self.log_performance_metric("total_duration", duration)
        
        return self.logger_system.end_action(success, self.driver)
    
    def safe_find_element(self, by: AppiumBy, value: str, timeout: int = 10) -> Optional[Any]:
        """Safely find an element with error logging"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.log_error_with_evidence(
                "element_not_found", 
                f"Element not found: {by}={value} (timeout: {timeout}s)"
            )
            return None
        except Exception as e:
            self.log_error_with_evidence(
                "element_find_error", 
                f"Error finding element {by}={value}: {str(e)}"
            )
            return None
    
    def safe_click_element(self, element, element_description: str = "element") -> bool:
        """Safely click an element with error logging"""
        try:
            element.click()
            self.logger.info(f"✅ Successfully clicked {element_description}")
            return True
        except Exception as e:
            self.log_error_with_evidence(
                "click_error", 
                f"Error clicking {element_description}: {str(e)}"
            )
            return False
    
    def safe_send_keys(self, element, text: str, element_description: str = "element") -> bool:
        """Safely send keys to an element with error logging"""
        try:
            element.clear()
            element.send_keys(text)
            self.logger.info(f"✅ Successfully entered text in {element_description}")
            return True
        except Exception as e:
            self.log_error_with_evidence(
                "send_keys_error", 
                f"Error sending keys to {element_description}: {str(e)}"
            )
            return False
    
    def wait_for_element_visible(self, by: AppiumBy, value: str, timeout: int = 10) -> bool:
        """Wait for element to be visible with error logging"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            self.log_error_with_evidence(
                "element_not_visible", 
                f"Element not visible: {by}={value} (timeout: {timeout}s)"
            )
            return False
        except Exception as e:
            self.log_error_with_evidence(
                "visibility_wait_error", 
                f"Error waiting for element visibility {by}={value}: {str(e)}"
            )
            return False
    
    def handle_common_modals(self) -> bool:
        """Handle common modals and popups that might appear"""
        try:
            # List of common modal selectors to check
            modal_selectors = [
                (AppiumBy.ACCESSIBILITY_ID, "Close"),
                (AppiumBy.ACCESSIBILITY_ID, "Cancel"),
                (AppiumBy.ACCESSIBILITY_ID, "Dismiss"),
                (AppiumBy.ACCESSIBILITY_ID, "OK"),
                (AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Close')]"),
                (AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Cancel')]"),
                (AppiumBy.XPATH, "//XCUIElementTypeButton[contains(@name, 'Dismiss')]")
            ]
            
            for by, value in modal_selectors:
                try:
                    element = self.driver.find_element(by, value)
                    if element.is_displayed():
                        self.logger.info(f"🔧 Handling modal: {value}")
                        element.click()
                        time.sleep(1)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.log_error_with_evidence("modal_handling_error", f"Error handling modals: {str(e)}")
            return False
    
    def take_screenshot(self, description: str = "screenshot") -> Optional[str]:
        """Take a screenshot with description"""
        try:
            timestamp = int(time.time())
            screenshot_path = f"{self.logger_system.log_dir}/{description}_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"📸 Screenshot saved: {description}")
            return screenshot_path
        except Exception as e:
            self.log_error_with_evidence("screenshot_error", f"Error taking screenshot: {str(e)}")
            return None
    
    def save_page_source(self, description: str = "page_source") -> Optional[str]:
        """Save page source XML with description"""
        try:
            timestamp = int(time.time())
            xml_path = f"{self.logger_system.log_dir}/{description}_{timestamp}.xml"
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            self.logger.info(f"📄 Page source saved: {description}")
            return xml_path
        except Exception as e:
            self.log_error_with_evidence("xml_save_error", f"Error saving page source: {str(e)}")
            return None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get current logging session summary"""
        return self.logger_system.get_session_summary()
    
    def save_session_summary(self) -> str:
        """Save current logging session summary"""
        return self.logger_system.save_session_summary()


# Common selectors for Threads app
class ThreadsSelectors:
    """Common selectors for Threads app elements"""
    
    # Navigation
    HOME_TAB = (AppiumBy.ACCESSIBILITY_ID, "home-tab")
    SEARCH_TAB = (AppiumBy.ACCESSIBILITY_ID, "search-tab")
    PROFILE_TAB = (AppiumBy.ACCESSIBILITY_ID, "profile-tab")
    NOTIFICATIONS_TAB = (AppiumBy.ACCESSIBILITY_ID, "notifications-tab")
    
    # Login
    LOGIN_BUTTON = (AppiumBy.XPATH, "//XCUIElementTypeButton[@name='Log in']")
    USERNAME_FIELD = (AppiumBy.ACCESSIBILITY_ID, "Username, email or mobile number")
    PASSWORD_FIELD = (AppiumBy.ACCESSIBILITY_ID, "Password")
    LOGIN_SUBMIT_BUTTON = (AppiumBy.XPATH, "(//XCUIElementTypeButton[@name='Log in'])[2]")
    
    # Common buttons
    LIKE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Like")
    COMMENT_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Reply")
    SHARE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Share")
    FOLLOW_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Follow")
    
    # Modals and popups
    CLOSE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Close")
    CANCEL_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Cancel")
    OK_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "OK")


if __name__ == "__main__":
    print("🧵 Threads Base Action Class")
    print("===========================")
    print("Base class for all Threads automation actions")
    print("Integrated logging and checkpoint system")
    print("Common error handling and utilities")
