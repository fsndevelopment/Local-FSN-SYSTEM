#!/usr/bin/env python3
"""
Shared Appium Driver Configuration
=================================

Universal driver setup that works for both Instagram and Threads.
Proven configuration from Instagram 100% completion.

Author: FSN Appium Team
Last Updated: January 15, 2025
Status: Production-tested configuration
"""

from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Optional
import logging
from platforms.config import Platform, DEVICE_CONFIG, get_platform_config

logger = logging.getLogger(__name__)

class AppiumDriverManager:
    """Manages Appium driver creation and configuration for all platforms"""
    
    @staticmethod
    def create_driver(platform: Platform, custom_port: Optional[int] = None) -> webdriver.Remote:
        """
        Create Appium driver for specified platform
        
        Args:
            platform: Platform enum (INSTAGRAM or THREADS)
            custom_port: Optional custom Appium port (defaults to 4739)
            
        Returns:
            webdriver.Remote: Configured Appium driver
        """
        try:
            config = get_platform_config(platform)
            port = custom_port or DEVICE_CONFIG["appium_port"]
            
            logger.info(f"🔌 Setting up Appium driver for {config.display_name}...")
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = DEVICE_CONFIG["udid"]
            options.bundle_id = config.bundle_id
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.wda_local_port = DEVICE_CONFIG["wda_port"]
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            
            driver = webdriver.Remote(f"http://localhost:{port}", options=options)
            
            logger.info(f"✅ {config.display_name} driver setup complete")
            logger.info(f"📱 Device: {DEVICE_CONFIG['udid']}")
            logger.info(f"📦 Bundle: {config.bundle_id}")
            
            return driver
            
        except Exception as e:
            logger.error(f"❌ Driver setup failed for {platform.value}: {e}")
            raise

    @staticmethod
    def get_wait_driver(driver: webdriver.Remote, timeout: int = 10) -> WebDriverWait:
        """Get WebDriverWait instance for element waiting"""
        return WebDriverWait(driver, timeout)

    @staticmethod
    def safe_quit_driver(driver: Optional[webdriver.Remote]):
        """Safely quit driver with error handling"""
        if driver:
            try:
                driver.quit()
                logger.info("🔌 Appium driver closed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Driver quit warning: {e}")

# Proven selectors that work across platforms (when apps share design patterns)
UNIVERSAL_SELECTORS = {
    # Navigation elements (often similar across Meta apps)
    "back_button": "back-button",
    "close_button": "close-button", 
    "done_button": "Done",
    "cancel_button": "Cancel",
    
    # Common UI elements
    "text_field": "XCUIElementTypeTextField",
    "text_view": "XCUIElementTypeTextView", 
    "button": "XCUIElementTypeButton",
    "cell": "XCUIElementTypeCell",
    
    # Permission dialogs
    "allow_button": "Allow",
    "dont_allow_button": "Don't Allow",
    "ok_button": "OK",
}

def find_element_safe(driver: webdriver.Remote, by: str, value: str, timeout: int = 10):
    """
    Safely find element with timeout and error handling
    
    Args:
        driver: Appium WebDriver
        by: Locator strategy (e.g., AppiumBy.ACCESSIBILITY_ID)
        value: Locator value
        timeout: Timeout in seconds
        
    Returns:
        WebElement or None if not found
    """
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element
    except Exception as e:
        logger.warning(f"⚠️ Element not found: {by}={value} (timeout: {timeout}s)")
        return None

def find_elements_safe(driver: webdriver.Remote, by: str, value: str):
    """
    Safely find multiple elements without timeout
    
    Returns:
        List of WebElements (empty list if none found)
    """
    try:
        elements = driver.find_elements(by, value)
        return elements
    except Exception as e:
        logger.warning(f"⚠️ Elements not found: {by}={value}")
        return []

# Device-specific configurations for different iPhone models
DEVICE_SPECIFIC_CONFIG = {
    # iPhone X/XS/11/12/13/14 (tested configuration)
    "default": {
        "screen_size": (375, 812),  # Points, not pixels
        "safe_area_top": 44,
        "safe_area_bottom": 34,
        "camera_mode_positions": {
            'POST': 0.133,   # 13.3% from left edge
            'STORY': 0.60,   # 60.0% from left edge  
            'REEL': 0.667    # 66.7% from left edge
        }
    }
}

def get_device_config():
    """Get device-specific configuration"""
    return DEVICE_SPECIFIC_CONFIG["default"]

if __name__ == "__main__":
    print("🔌 FSN Appium Shared Driver Configuration")
    print("=========================================")
    print("Production-tested configuration from Instagram 100% completion")
    print(f"\nDevice: {DEVICE_CONFIG['udid']}")
    print(f"iOS Version: {DEVICE_CONFIG['ios_version']}")
    print("\nSupported Platforms:")
    
    from platforms.config import get_all_platforms
    for platform, config in get_all_platforms().items():
        print(f"  📱 {config.display_name}: {config.bundle_id}")
