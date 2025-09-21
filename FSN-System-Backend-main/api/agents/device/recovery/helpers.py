"""
Recovery Helpers for Instagram/Threads Automation
Common recovery functions to handle UI issues and get back to stable states
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..fsm.context import Platform
from ..drivers.base_driver import BaseDriver

logger = logging.getLogger(__name__)


class RecoveryError(Exception):
    """Exception raised when recovery operations fail"""
    pass


async def ensure_home(driver: BaseDriver, platform: Platform, max_attempts: int = 3) -> bool:
    """
    Always return to Instagram/Threads home screen
    This is the most important recovery function - home is our safe state
    """
    logger.info(f"Ensuring home screen for {platform.value}")
    
    for attempt in range(max_attempts):
        try:
            logger.debug(f"Home navigation attempt {attempt + 1}/{max_attempts}")
            
            # First, try to close any modals that might be blocking us
            await close_modals(driver)
            await hide_keyboard(driver)
            
            # Look for home indicators
            if await _is_on_home_screen(driver, platform):
                logger.info("Already on home screen")
                return True
            
            # Try to navigate to home using various methods
            if await _navigate_to_home(driver, platform):
                # Verify we reached home
                await asyncio.sleep(2)  # Wait for transition
                if await _is_on_home_screen(driver, platform):
                    logger.info("Successfully reached home screen")
                    return True
            
            # If direct navigation failed, try app restart
            logger.warning(f"Home navigation failed on attempt {attempt + 1}, trying app restart")
            if await _restart_app(driver, platform):
                await asyncio.sleep(3)  # Wait for app to load
                if await _is_on_home_screen(driver, platform):
                    logger.info("Reached home screen after app restart")
                    return True
            
        except Exception as e:
            logger.error(f"Error in home navigation attempt {attempt + 1}: {e}")
        
        # Wait before retry
        if attempt < max_attempts - 1:
            await asyncio.sleep(2)
    
    logger.error("Failed to reach home screen after all attempts")
    return False


async def close_modals(driver: BaseDriver, max_attempts: int = 5) -> bool:
    """
    Close Instagram/Threads popups, notifications, and modal dialogs
    """
    logger.debug("Attempting to close modals")
    
    # Common modal close selectors (in priority order)
    close_selectors = [
        # Generic close buttons
        ("accessibility_id", "Close"),
        ("accessibility_id", "Dismiss"),
        ("accessibility_id", "Cancel"),
        ("accessibility_id", "Not Now"),
        ("accessibility_id", "Skip"),
        
        # Instagram specific
        ("accessibility_id", "Close, button"),
        ("name", "Close"),
        ("xpath", "//XCUIElementTypeButton[@name='Close']"),
        ("xpath", "//XCUIElementTypeButton[contains(@name, 'close')]"),
        
        # Common notification dismissals
        ("accessibility_id", "Don't Allow"),
        ("accessibility_id", "Maybe Later"),
        ("accessibility_id", "Turn On Later"),
        
        # Back buttons as fallback
        ("accessibility_id", "Back"),
        ("xpath", "//XCUIElementTypeButton[@name='Back']"),
    ]
    
    modals_closed = 0
    
    for attempt in range(max_attempts):
        modal_found = False
        
        for strategy, value in close_selectors:
            try:
                element = await driver.find_element(strategy, value, timeout=2)
                if element:
                    logger.debug(f"Found modal close button: {strategy}={value}")
                    if await driver.click_element(element):
                        modals_closed += 1
                        modal_found = True
                        await asyncio.sleep(1)  # Wait for modal to close
                        break
            except Exception as e:
                logger.debug(f"Modal close attempt failed: {e}")
                continue
        
        if not modal_found:
            break  # No more modals found
    
    if modals_closed > 0:
        logger.info(f"Closed {modals_closed} modal(s)")
        return True
    else:
        logger.debug("No modals found to close")
        return True  # No modals is success


async def hide_keyboard(driver: BaseDriver) -> bool:
    """
    Hide iOS keyboard if visible
    """
    logger.debug("Attempting to hide keyboard")
    
    try:
        # Check if keyboard is visible
        keyboard_selectors = [
            ("class_name", "XCUIElementTypeKeyboard"),
            ("accessibility_id", "Keyboard"),
        ]
        
        keyboard_visible = False
        for strategy, value in keyboard_selectors:
            if await driver.is_element_present(strategy, value):
                keyboard_visible = True
                break
        
        if not keyboard_visible:
            logger.debug("Keyboard not visible")
            return True
        
        # Try to hide keyboard
        hide_methods = [
            # Tap done/return button
            ("accessibility_id", "Done"),
            ("accessibility_id", "Return"),
            ("accessibility_id", "Go"),
            
            # Tap outside keyboard area (safe area at top)
            lambda: driver.tap_coordinates(200, 100),
        ]
        
        for method in hide_methods:
            try:
                if callable(method):
                    if await method():
                        await asyncio.sleep(1)
                        break
                else:
                    strategy, value = method
                    element = await driver.find_element(strategy, value, timeout=2)
                    if element:
                        if await driver.click_element(element):
                            await asyncio.sleep(1)
                            break
            except Exception as e:
                logger.debug(f"Keyboard hide method failed: {e}")
                continue
        
        # Verify keyboard is hidden
        for strategy, value in keyboard_selectors:
            if await driver.is_element_present(strategy, value):
                logger.warning("Keyboard still visible after hide attempts")
                return False
        
        logger.debug("Keyboard hidden successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error hiding keyboard: {e}")
        return False


async def return_home_map() -> Dict[str, List[str]]:
    """
    Return a map of screen types to home navigation paths
    Used for context-aware home navigation
    """
    return {
        "profile_page": [
            "tap_home_tab",
            "back_button",
            "app_restart"
        ],
        "post_detail": [
            "back_button", 
            "tap_home_tab",
            "app_restart"
        ],
        "search_page": [
            "tap_home_tab",
            "app_restart"
        ],
        "settings": [
            "back_button",
            "tap_home_tab", 
            "app_restart"
        ],
        "unknown": [
            "tap_home_tab",
            "back_button",
            "app_restart"
        ]
    }


async def detect_current_screen(driver: BaseDriver, platform: Platform) -> str:
    """
    Detect what screen/page we're currently on
    Returns screen type for context-aware navigation
    """
    try:
        # Instagram screen detection
        if platform == Platform.INSTAGRAM:
            # Home feed indicators
            if await driver.is_element_present("accessibility_id", "Home"):
                return "home_feed"
            
            # Profile page indicators
            if await driver.is_element_present("accessibility_id", "Profile"):
                return "profile_page"
            
            # Post detail indicators
            if await driver.is_element_present("accessibility_id", "Like") or \
               await driver.is_element_present("accessibility_id", "Comment"):
                return "post_detail"
            
            # Search page indicators
            if await driver.is_element_present("accessibility_id", "Search"):
                return "search_page"
            
            # Settings indicators
            if await driver.is_element_present("accessibility_id", "Settings"):
                return "settings"
        
        # Threads screen detection (similar pattern)
        elif platform == Platform.THREADS:
            # TODO: Add Threads-specific screen detection
            pass
        
        return "unknown"
        
    except Exception as e:
        logger.error(f"Error detecting current screen: {e}")
        return "unknown"


# Private helper functions

async def _is_on_home_screen(driver: BaseDriver, platform: Platform) -> bool:
    """Check if we're on the home screen"""
    try:
        if platform == Platform.INSTAGRAM:
            # Look for Instagram home indicators
            home_indicators = [
                ("accessibility_id", "Home"),
                ("accessibility_id", "Feed"),
                ("xpath", "//XCUIElementTypeTabBar//XCUIElementTypeButton[@name='Home']"),
            ]
        elif platform == Platform.THREADS:
            # Look for Threads home indicators
            home_indicators = [
                ("accessibility_id", "Home"),
                ("accessibility_id", "For You"),
            ]
        else:
            return False
        
        for strategy, value in home_indicators:
            if await driver.is_element_present(strategy, value):
                logger.debug(f"Home indicator found: {strategy}={value}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking home screen: {e}")
        return False


async def _navigate_to_home(driver: BaseDriver, platform: Platform) -> bool:
    """Navigate to home using UI elements"""
    try:
        # Try tapping home tab
        if await _tap_home_tab(driver, platform):
            return True
        
        # Try back button navigation
        if await _navigate_back_to_home(driver):
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error navigating to home: {e}")
        return False


async def _tap_home_tab(driver: BaseDriver, platform: Platform) -> bool:
    """Tap the home tab in the bottom navigation"""
    try:
        if platform == Platform.INSTAGRAM:
            home_selectors = [
                ("accessibility_id", "Home"),
                ("xpath", "//XCUIElementTypeTabBar//XCUIElementTypeButton[@name='Home']"),
                ("xpath", "//XCUIElementTypeButton[@name='Home']"),
            ]
        elif platform == Platform.THREADS:
            home_selectors = [
                ("accessibility_id", "Home"),
                ("xpath", "//XCUIElementTypeTabBar//XCUIElementTypeButton[@name='Home']"),
            ]
        else:
            return False
        
        for strategy, value in home_selectors:
            element = await driver.find_element(strategy, value, timeout=3)
            if element:
                logger.debug(f"Tapping home tab: {strategy}={value}")
                return await driver.click_element(element)
        
        return False
        
    except Exception as e:
        logger.error(f"Error tapping home tab: {e}")
        return False


async def _navigate_back_to_home(driver: BaseDriver, max_back_presses: int = 5) -> bool:
    """Navigate back to home using back buttons"""
    try:
        for i in range(max_back_presses):
            # Look for back button
            back_selectors = [
                ("accessibility_id", "Back"),
                ("xpath", "//XCUIElementTypeButton[@name='Back']"),
                ("xpath", "//XCUIElementTypeNavigationBar//XCUIElementTypeButton[1]"),
            ]
            
            back_pressed = False
            for strategy, value in back_selectors:
                element = await driver.find_element(strategy, value, timeout=2)
                if element:
                    logger.debug(f"Pressing back button: {strategy}={value}")
                    if await driver.click_element(element):
                        back_pressed = True
                        await asyncio.sleep(1)
                        break
            
            if not back_pressed:
                break  # No more back buttons
        
        return True  # Even if no backs were pressed, we tried
        
    except Exception as e:
        logger.error(f"Error navigating back: {e}")
        return False


async def _restart_app(driver: BaseDriver, platform: Platform) -> bool:
    """Restart the app as a recovery method"""
    try:
        logger.info("Restarting app for recovery")
        
        # Close app
        if not await driver.close_app():
            logger.warning("Failed to close app, continuing anyway")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Reopen app
        if await driver.open_app(platform):
            logger.info("App restarted successfully")
            return True
        else:
            logger.error("Failed to reopen app after restart")
            return False
            
    except Exception as e:
        logger.error(f"Error restarting app: {e}")
        return False
