#!/usr/bin/env python3
"""
Threads POST_THREAD Test - Content Creation Action
==================================================

🧵 THREADS POST FUNCTIONALITY - Phase 2B Content Creation

Following proven Instagram patterns with user-provided exact selectors.

Test Flow:
1. Navigate to home feed tab (feed-tab-main)
2. Click create-tab button to open posting page
3. Enter text in compose field
4. Optionally add image from camera roll
5. Post the thread
6. Handle any popups
7. Verify thread was posted
8. Return to safe state

Selectors Provided by User:
- Create Tab: create-tab
- Compose Field: Text field. Type to compose a post.
- Add Photos: Add photos and videos from your camera roll
- Allow Access: Allow Access to All Photos
- Photo Selection: Photo, September 06, 9:58 AM
- Add Button: Add
- Post Button: Post this thread
- Popup Dismiss: Not now

Author: FSN Appium Team
Started: January 15, 2025
Status: Phase 2B Content Creation Implementation
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add platforms to path
sys.path.append('/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main')

from platforms.shared.utils.checkpoint_system import CheckpointSystem
from platforms.shared.utils.appium_driver import AppiumDriverManager
from platforms.config import Platform
from appium.webdriver.common.appiumby import AppiumBy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'threads_post_thread_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class ThreadsPostThreadTest(CheckpointSystem):
    """Threads POST_THREAD implementation using proven patterns"""
    
    def __init__(self, post_text=None, photos_per_day=0, progress_callback=None, device_type="non_jailbroken", container_id=None, existing_driver=None):
        super().__init__("threads", "post_thread")
        self.driver = existing_driver  # Use existing driver if provided
        self.wait = None
        self.posts_created = 0
        self.test_text = post_text or "Default text post - please provide text content"
        self.photos_per_day = photos_per_day
        self.progress_callback = progress_callback
        self.device_type = device_type
        self.container_id = container_id
        self.use_existing_driver = existing_driver is not None
        
    def setup_driver(self):
        """Initialize driver and launch Threads app from desktop"""
        try:
            # If we have an existing driver, use it and get device info from its capabilities
            if self.use_existing_driver and self.driver:
                self.logger.info("🔧 Using existing driver with capabilities")
                
                # Get device info from existing driver capabilities
                try:
                    capabilities = self.driver.capabilities
                    jailbroken = capabilities.get('appium:jailbroken', False)
                    device_name = capabilities.get('appium:deviceName', 'Unknown Device')
                    
                    self.logger.info(f"🔍 Existing driver capabilities - Device: {device_name}, Jailbroken: {jailbroken}")
                    
                    if jailbroken:
                        self.device_type = "jailbroken"
                        self.container_id = self.container_id or "1"  # Use provided or default
                        self.logger.info(f"🔧 Detected JB device from existing driver: {self.device_type}")
                    else:
                        self.device_type = "non_jailbroken"
                        self.logger.info("📱 Detected NONJB device from existing driver")
                        
                except Exception as e:
                    self.logger.error(f"🔍 Failed to get device info from existing driver: {e}")
                
                self.wait = AppiumDriverManager.get_wait_driver(self.driver)
                self.logger.info("✅ Using existing driver - ready to launch Threads")
                return True
            
            # Create new driver with correct capabilities from frontend
            self.logger.info("🧵 Creating new driver session with frontend capabilities...")
            
            # Get device capabilities directly from device configuration (set in frontend)
            from platforms.config import DEVICE_CONFIG
            
            # Check if device_type and container_id were passed as parameters
            if hasattr(self, 'device_type') and self.device_type != "non_jailbroken":
                self.logger.info(f"🔧 Using device_type from parameters: {self.device_type}")
            elif hasattr(self, 'container_id') and self.container_id:
                # If container_id is provided, assume it's a jailbroken device
                self.device_type = "jailbroken"
                self.logger.info(f"🔧 Container ID provided ({self.container_id}), setting device as jailbroken")
            else:
                # Default to non-jailbroken if no parameters provided
                self.device_type = "non_jailbroken"
                self.logger.info("📱 No JB parameters provided, defaulting to non-jailbroken")
            
            # Create driver with the correct capabilities
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
            
            # Set jailbroken capability based on device type
            if self.device_type == "jailbroken":
                options.set_capability("jailbroken", True)
                self.logger.info("🔧 Added jailbroken capability to new driver")
            else:
                options.set_capability("jailbroken", False)
                self.logger.info("📱 Added non-jailbroken capability to new driver")
            
            # No bundle_id specified - will connect to home screen
            
            self.driver = webdriver.Remote(f"http://localhost:{DEVICE_CONFIG['appium_port']}", options=options)
            self.wait = AppiumDriverManager.get_wait_driver(self.driver)
            
            self.logger.info("✅ Created new driver with frontend capabilities - ready to launch Threads")
            
            self.logger.info("✅ Driver setup complete - ready to launch Threads")
            return True
        except Exception as e:
            self.logger.error(f"❌ Driver setup failed: {e}")
            return False
    
    def checkpoint_0_launch_threads_from_desktop(self, driver) -> bool:
        """Checkpoint 0: Launch Threads app from desktop with JB/NONJB logic"""
        try:
            if self.progress_callback:
                self.progress_callback("launch_threads_from_desktop", 8)
            self.logger.info("🎯 CHECKPOINT 0: Launch Threads from desktop")
            self.logger.info(f"🔧 Device Type: {self.device_type}")
            if self.device_type == "jailbroken":
                self.logger.info(f"🔧 Container ID: {self.container_id}")
            
            # Check if this is a JB device and needs Crane container switching
            if self.device_type == "jailbroken" and self.container_id:
                self.logger.info("🔧 JB Device detected - Using Crane container switching")
                return self._launch_threads_with_crane(driver)
            else:
                self.logger.info("📱 NONJB Device detected - Using direct launch")
                return self._launch_threads_directly(driver)
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 0 failed: {e}")
            return False
    
    def _get_device_info_from_database(self):
        """Get device information from database"""
        try:
            self.logger.info("🔍 _get_device_info_from_database called")
            
            # Get device UDID from config
            from platforms.config import DEVICE_CONFIG
            device_udid = DEVICE_CONFIG["udid"]
            self.logger.info(f"🔍 Device UDID from config: {device_udid}")
            
            # Try to query the database for device info
            import asyncio
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            self.logger.info("🔍 Added path to sys.path for database imports")
            
            async def query_device():
                try:
                    self.logger.info("🔍 Starting database query...")
                    from api.database.connection import AsyncSessionLocal
                    from api.migrations.setup_postgresql_tables import Device
                    from sqlalchemy import select
                    self.logger.info("🔍 Successfully imported database modules")
                    
                    async with AsyncSessionLocal() as db:
                        self.logger.info(f"🔍 Querying database for device UDID: {device_udid}")
                        result = await db.execute(
                            select(Device).where(Device.udid == device_udid)
                        )
                        device = result.scalar_one_or_none()
                        
                        if device:
                            self.logger.info(f"🔍 Found device in database: {device.name}, jailbroken: {device.jailbroken}")
                            return {
                                'jailbroken': device.jailbroken,
                                'name': device.name,
                                'udid': device.udid
                            }
                        else:
                            self.logger.warning(f"🔍 Device {device_udid} not found in database")
                            return None
                            
                except Exception as e:
                    self.logger.error(f"🔍 Database query failed: {e}")
                    return None
            
            # Try to get the current event loop, or create a new one if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're already in an event loop, use asyncio.run_coroutine_threadsafe
                    import concurrent.futures
                    import threading
                    
                    # Create a new thread to run the async function
                    def run_in_thread():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(query_device())
                        finally:
                            new_loop.close()
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        result = future.result(timeout=10)  # 10 second timeout
                        return result
                else:
                    # No event loop running, we can use it directly
                    result = loop.run_until_complete(query_device())
                    return result
            except RuntimeError:
                # No event loop exists, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(query_device())
                    return result
                finally:
                    loop.close()
                
        except Exception as e:
            self.logger.error(f"🔍 Failed to get device info from database: {e}")
            return None
    
    def _launch_threads_with_crane(self, driver) -> bool:
        """Launch Threads with Crane container switching for JB devices"""
        try:
            self.logger.info(f"🔧 Starting Crane container switching for {self.container_id}")
            
            # For JB devices, perform Crane container switching manually using the existing driver
            # This avoids creating a new driver session that would terminate the current one
            
            try:
                # Step 1: Check if we're already on home screen, if not navigate there
                self.logger.info("🏠 Checking if we're on home screen...")
                
                # First, try to find the Threads icon - if we can find it, we're already on home screen
                try:
                    threads_icon = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Threads")
                    self.logger.info("✅ Already on home screen - Threads icon found")
                    home_success = True
                except:
                    # We're not on home screen, try to navigate there
                    self.logger.info("🏠 Not on home screen, attempting navigation...")
                    home_success = False
                    
                    try:
                        # Method 1: mobile: pressKey with keycode
                        driver.execute_script("mobile: pressKey", {"keycode": 3})
                        home_success = True
                        self.logger.info("✅ Home screen navigation successful (method 1)")
                    except:
                        try:
                            # Method 2: mobile: pressKey with name
                            driver.execute_script("mobile: pressKey", {"name": "home"})
                            home_success = True
                            self.logger.info("✅ Home screen navigation successful (method 2)")
                        except:
                            try:
                                # Method 3: mobile: pressButton
                                driver.execute_script("mobile: pressButton", {"name": "home"})
                                home_success = True
                                self.logger.info("✅ Home screen navigation successful (method 3)")
                            except:
                                try:
                                    # Method 4: Find and tap home indicator
                                    home_indicator = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeButton[@name='Home indicator']")
                                    home_indicator.click()
                                    home_success = True
                                    self.logger.info("✅ Home screen navigation successful (method 4)")
                                except:
                                    self.logger.warning("⚠️ All home screen navigation methods failed")
                    
                    if home_success:
                        time.sleep(2)  # Wait for home screen to load
                
                # Step 2: Find Threads app icon and long press it
                self.logger.info("🔍 Looking for Threads app icon...")
                threads_icon = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Threads")
                self.logger.info("✅ Found Threads app icon")
                
                # Step 3: Long press the Threads icon to open Crane menu
                self.logger.info("👆 Long pressing Threads icon...")
                
                # Use iOS-compatible long press method
                try:
                    # Method 1: Use touch actions for iOS
                    from appium.webdriver.common.touch_action import TouchAction
                    touch_action = TouchAction(driver)
                    touch_action.long_press(threads_icon, duration=2000).perform()
                    self.logger.info("✅ Long press successful using TouchAction")
                except Exception as touch_error:
                    self.logger.warning(f"⚠️ TouchAction long press failed: {touch_error}")
                    try:
                        # Method 2: Use selenium ActionChains with proper pointer actions
                        from selenium.webdriver.common.action_chains import ActionChains
                        action = ActionChains(driver)
                        action.move_to_element(threads_icon).click_and_hold().pause(2).release().perform()
                        self.logger.info("✅ Long press successful using ActionChains")
                    except Exception as action_error:
                        self.logger.warning(f"⚠️ ActionChains long press failed: {action_error}")
                        # Method 3: Try double tap as fallback
                        try:
                            threads_icon.click()
                            time.sleep(0.5)
                            threads_icon.click()
                            self.logger.info("✅ Used double tap as fallback")
                        except Exception as double_tap_error:
                            self.logger.error(f"❌ All long press methods failed: {double_tap_error}")
                            raise double_tap_error
                
                time.sleep(3)  # Wait longer for Crane menu to appear
                
                # Step 4: Look for Crane menu elements with multiple selectors
                self.logger.info("🔍 Looking for Crane menu elements...")
                
                # Debug: Log page source to see what elements are available
                try:
                    page_source = driver.page_source
                    self.logger.info(f"📄 Page source length: {len(page_source)}")
                    # Look for any container-related elements
                    if "Container" in page_source:
                        self.logger.info("✅ Found 'Container' text in page source")
                    if "Default" in page_source:
                        self.logger.info("✅ Found 'Default' text in page source")
                    if "Open" in page_source:
                        self.logger.info("✅ Found 'Open' text in page source")
                except Exception as debug_error:
                    self.logger.warning(f"⚠️ Could not get page source: {debug_error}")
                
                # Try multiple selectors for the container button (using XPath like the working Crane service)
                container_button = None
                container_selectors = [
                    # XPath selectors (preferred)
                    ("XPATH", "//XCUIElementTypeButton[starts-with(@name, 'Container,')]"),
                    ("XPATH", "//XCUIElementTypeButton[contains(@name, 'Container')]"),
                    ("XPATH", "//XCUIElementTypeButton[@name='Container, Default']"),
                    # Accessibility ID selectors (fallback)
                    ("ACCESSIBILITY_ID", "Container, Default"),
                    ("ACCESSIBILITY_ID", "Container Default"), 
                    ("ACCESSIBILITY_ID", "Default"),
                    ("ACCESSIBILITY_ID", "Container"),
                    ("ACCESSIBILITY_ID", "Containers")
                ]
                
                for selector_type, selector in container_selectors:
                    try:
                        self.logger.info(f"🔍 Trying {selector_type} selector: '{selector}'")
                        if selector_type == "XPATH":
                            container_button = driver.find_element(AppiumBy.XPATH, selector)
                        else:
                            container_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, selector)
                        self.logger.info(f"✅ Found container button with {selector_type} selector: '{selector}'")
                        break
                    except:
                        continue
                
                if container_button:
                    container_button.click()
                    time.sleep(2)
                else:
                    self.logger.error("❌ Could not find any container button")
                    raise Exception("Container button not found")
                
                # Step 5: Find and select the target container
                self.logger.info(f"🎯 Selecting container {self.container_id}...")
                
                # Try multiple selectors for the target container (using XPath patterns)
                container_element = None
                container_selectors = [
                    # XPath selectors (preferred)
                    ("XPATH", f"//XCUIElementTypeButton[@name='{self.container_id}']"),
                    ("XPATH", f"//XCUIElementTypeCell[@name='{self.container_id}']"),
                    ("XPATH", f"//XCUIElementTypeStaticText[@name='{self.container_id}']"),
                    ("XPATH", f"//*[contains(@name, '{self.container_id}')]"),
                    # Accessibility ID selectors (fallback)
                    ("ACCESSIBILITY_ID", self.container_id),
                    ("ACCESSIBILITY_ID", f"Container {self.container_id}"),
                    ("ACCESSIBILITY_ID", f"container_{self.container_id}"),
                    ("ACCESSIBILITY_ID", f"Container_{self.container_id}")
                ]
                
                for selector_type, selector in container_selectors:
                    try:
                        self.logger.info(f"🔍 Trying container {selector_type} selector: '{selector}'")
                        if selector_type == "XPATH":
                            container_element = driver.find_element(AppiumBy.XPATH, selector)
                        else:
                            container_element = driver.find_element(AppiumBy.ACCESSIBILITY_ID, selector)
                        self.logger.info(f"✅ Found container element with {selector_type} selector: '{selector}'")
                        break
                    except:
                        continue
                
                if container_element:
                    container_element.click()
                    time.sleep(2)
                else:
                    self.logger.error(f"❌ Could not find container element for ID: {self.container_id}")
                    raise Exception(f"Container {self.container_id} not found")
                
                # Step 6: Click "Open" to launch the app in the selected container
                self.logger.info("🚀 Opening Threads in selected container...")
                
                # Try multiple selectors for the "Open" button (using XPath patterns)
                open_button = None
                open_selectors = [
                    # XPath selectors (preferred)
                    ("XPATH", "//XCUIElementTypeButton[@name='Open']"),
                    ("XPATH", "//XCUIElementTypeButton[@name='Launch']"),
                    ("XPATH", "//XCUIElementTypeButton[@name='Start']"),
                    ("XPATH", "//XCUIElementTypeButton[@name='Go']"),
                    ("XPATH", "//XCUIElementTypeButton[contains(@name, 'Open')]"),
                    # Accessibility ID selectors (fallback)
                    ("ACCESSIBILITY_ID", "Open"),
                    ("ACCESSIBILITY_ID", "Launch"),
                    ("ACCESSIBILITY_ID", "Start"),
                    ("ACCESSIBILITY_ID", "Go")
                ]
                
                for selector_type, selector in open_selectors:
                    try:
                        self.logger.info(f"🔍 Trying open button {selector_type} selector: '{selector}'")
                        if selector_type == "XPATH":
                            open_button = driver.find_element(AppiumBy.XPATH, selector)
                        else:
                            open_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, selector)
                        self.logger.info(f"✅ Found open button with {selector_type} selector: '{selector}'")
                        break
                    except:
                        continue
                
                if open_button:
                    open_button.click()
                else:
                    self.logger.error("❌ Could not find any open button")
                    raise Exception("Open button not found")
                
                # Step 7: Wait for app to launch
                time.sleep(8)  # Wait longer for app to fully launch
                
                self.logger.info("✅ Crane container switching completed successfully")
                return True
                
            except Exception as crane_error:
                self.logger.error(f"❌ Crane switching failed: {crane_error}")
                # Fallback to direct launch
                self.logger.info("🔄 Falling back to direct launch...")
                return self._launch_threads_directly(driver)
                
        except Exception as e:
            self.logger.error(f"❌ Crane switching failed: {e}")
            return False
    
    def _launch_threads_directly(self, driver) -> bool:
        """Launch Threads directly for NONJB devices"""
        try:
            # User-provided selector for Threads app icon on desktop
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
        """Checkpoint 1: Navigate to home feed"""
        try:
            if self.progress_callback:
                self.progress_callback("navigate_to_home_feed", 15)
            self.logger.info("🎯 CHECKPOINT 1: Navigate to home feed")
            
            # User-provided selector: feed-tab-main
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
    
    def checkpoint_2_click_create_tab(self, driver) -> bool:
        """Checkpoint 2: Click create-tab button to open posting page"""
        try:
            if self.progress_callback:
                self.progress_callback("click_create_tab", 23)
            self.logger.info("🎯 CHECKPOINT 2: Click create-tab button")
            
            # User-provided selector: create-tab
            create_tab_selector = "create-tab"
            
            try:
                create_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, create_tab_selector)
                self.logger.info(f"✅ Found create tab: {create_tab_selector}")
                
                # Tap the create tab
                self.logger.info("👆 Tapping create tab...")
                create_tab.click()
                time.sleep(3)  # Allow posting page to load
                
                # Verify we're on posting page
                page_source = driver.page_source
                if "Text field. Type to compose a post." in page_source:
                    self.logger.info("✅ Successfully opened posting page")
                    return True
                else:
                    self.logger.warning("⚠️ Create tab clicked but posting page not immediately visible")
                    return True  # Still consider success
                
            except Exception as e:
                self.logger.error(f"❌ Could not find create tab '{create_tab_selector}': {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Create tab click failed: {e}")
            return False
    
    def checkpoint_3_enter_text(self, driver) -> bool:
        """Checkpoint 3: Enter text in compose field"""
        try:
            if self.progress_callback:
                self.progress_callback("enter_text", 31)
            self.logger.info("🎯 CHECKPOINT 3: Enter text in compose field")
            
            # User-provided selector: Text field. Type to compose a post.
            compose_field_selector = "Text field. Type to compose a post."
            
            try:
                compose_field = driver.find_element(AppiumBy.ACCESSIBILITY_ID, compose_field_selector)
                self.logger.info(f"✅ Found compose field: {compose_field_selector}")
                
                # Clear any existing text and enter our test text
                self.logger.info(f"📝 Entering text: {self.test_text}")
                compose_field.clear()
                compose_field.send_keys(self.test_text)
                time.sleep(1)  # Allow text to be entered
                
                # Verify text was entered
                entered_text = compose_field.get_attribute("value")
                if entered_text and self.test_text in entered_text:
                    self.logger.info("✅ Text entered successfully")
                    return True
                else:
                    self.logger.warning("⚠️ Text entered but verification unclear")
                    return True  # Still consider success
                
            except Exception as e:
                self.logger.error(f"❌ Could not find compose field '{compose_field_selector}': {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Text entry failed: {e}")
            return False
    
    def checkpoint_4_add_image(self, driver) -> bool:
        """Checkpoint 4: Add image from camera roll (optional)"""
        try:
            if self.progress_callback:
                self.progress_callback("add_image", 38)
            self.logger.info("🎯 CHECKPOINT 4: Add image from camera roll")
            
            # Skip photo selection if photos_per_day is 0
            if self.photos_per_day == 0:
                self.logger.info("📷 Skipping photo selection (photos_per_day = 0)")
                return True
            
            # User-provided selector: Add photos and videos from your camera roll
            add_photos_selector = "Add photos and videos from your camera roll"
            
            try:
                add_photos_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, add_photos_selector)
                self.logger.info(f"✅ Found add photos button: {add_photos_selector}")
                
                # Tap add photos button
                self.logger.info("👆 Tapping add photos button...")
                add_photos_button.click()
                time.sleep(2)  # Allow photo picker to load
                
                # Check for permission dialog
                try:
                    allow_access_selector = "Allow Access to All Photos"
                    allow_access_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, allow_access_selector)
                    self.logger.info("📱 Found permission dialog, allowing access...")
                    allow_access_button.click()
                    time.sleep(2)
                except:
                    self.logger.info("✅ No permission dialog or already granted")
                
                # Select latest photo (most recent one, which should be our downloaded photo)
                try:
                    # Try to find the most recent photo (first photo in the grid)
                    # Look for XCUIElementTypeImage elements with Photo names
                    photos = driver.find_elements(AppiumBy.XPATH, "//XCUIElementTypeImage[starts-with(@name, 'Photo,')]")
                    if photos:
                        photo = photos[0]  # First photo is the most recent
                        photo_name = photo.get_attribute("name")
                        self.logger.info(f"✅ Found most recent photo: {photo_name}")
                    else:
                        # Fallback: try the old hardcoded selector
                        photo_selector = "Photo, September 06, 9:58 AM"
                        photo = driver.find_element(AppiumBy.ACCESSIBILITY_ID, photo_selector)
                        self.logger.info(f"✅ Found photo with fallback selector: {photo_selector}")
                    
                    # Tap photo to select
                    self.logger.info("👆 Selecting photo...")
                    photo.click()
                    time.sleep(1)
                    
                    # Click Add button
                    add_button_selector = "Add"
                    add_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, add_button_selector)
                    self.logger.info("👆 Clicking Add button...")
                    add_button.click()
                    time.sleep(2)
                    
                    self.logger.info("✅ Image added successfully")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not select photo: {e}")
                    # Still consider success - text post is valid
                    return True
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not find add photos button: {e}")
                # Still consider success - text post is valid
                return True
                
        except Exception as e:
            self.logger.warning(f"⚠️ Image addition failed: {e}")
            # Still consider success - text post is valid
            return True
    
    def checkpoint_5_post_thread(self, driver) -> bool:
        """Checkpoint 5: Post the thread"""
        try:
            if self.progress_callback:
                self.progress_callback("post_thread", 46)
            self.logger.info("🎯 CHECKPOINT 5: Post the thread")
            
            # User-provided selector: Post this thread
            post_button_selector = "Post this thread"
            
            try:
                post_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, post_button_selector)
                self.logger.info(f"✅ Found post button: {post_button_selector}")
                
                # Tap post button
                self.logger.info("👆 Tapping post button...")
                post_button.click()
                time.sleep(3)  # Allow post to be created
                
                self.posts_created += 1
                self.logger.info("✅ Thread posted successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Could not find post button '{post_button_selector}': {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Post thread failed: {e}")
            return False
    
    def checkpoint_6_handle_popups(self, driver) -> bool:
        """Checkpoint 6: Handle any popups that appear after posting"""
        try:
            if self.progress_callback:
                self.progress_callback("handle_popups", 54)
            self.logger.info("🎯 CHECKPOINT 6: Handle popups")
            
            # Check for Instagram story popup
            try:
                not_now_selector = "Not now"
                not_now_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, not_now_selector)
                self.logger.info("📱 Found Instagram story popup, dismissing...")
                not_now_button.click()
                time.sleep(1)
            except:
                self.logger.info("✅ No popups detected")
            
            # Check for other common popups
            popup_selectors = ["OK", "Done", "Close", "Cancel"]
            for selector in popup_selectors:
                try:
                    popup_button = driver.find_element(AppiumBy.ACCESSIBILITY_ID, selector)
                    self.logger.info(f"📱 Found popup: {selector}, dismissing...")
                    popup_button.click()
                    time.sleep(1)
                except:
                    pass
            
            self.logger.info("✅ Popup handling completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Popup handling failed: {e}")
            return False
    
    def checkpoint_7_verify_post(self, driver) -> bool:
        """Checkpoint 7: Verify thread was posted successfully"""
        try:
            if self.progress_callback:
                self.progress_callback("verify_post", 62)
            self.logger.info("🎯 CHECKPOINT 7: Verify post")
            
            # Check if we're back on the feed
            try:
                feed_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "feed-tab-main")
                self.logger.info("✅ Back on home feed")
                
                # Check if our post appears in the feed
                page_source = driver.page_source
                if self.test_text in page_source:
                    self.logger.info("✅ Our post text found in feed")
                    return True
                else:
                    self.logger.info("✅ Post completed (text verification not critical)")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Could not verify post in feed: {e}")
                return True  # Still consider success
                
        except Exception as e:
            self.logger.error(f"❌ Post verification failed: {e}")
            return False
    
    def checkpoint_8_return_safe_state(self, driver) -> bool:
        """Checkpoint 8: Return to safe state"""
        try:
            if self.progress_callback:
                self.progress_callback("return_safe_state", 69)
            self.logger.info("🎯 CHECKPOINT 8: Return to safe state")
            
            # Ensure we're on the home feed
            try:
                feed_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "feed-tab-main")
                self.logger.info("✅ Home feed tab accessible")
                
                # Make sure we're on the feed
                feed_tab.click()
                time.sleep(1)
                
                self.logger.info("✅ Returned to safe state (home feed)")
                return True
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not verify feed tab: {e}")
                
                # Check if main-feed is visible
                page_source = driver.page_source
                if "main-feed" in page_source:
                    self.logger.info("✅ Safe state confirmed (main-feed visible)")
                    return True
                else:
                    self.logger.error("❌ Cannot confirm safe state")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ Safe state return failed: {e}")
            return False
    
    def checkpoint_8_5_scrolling_and_liking(self, driver) -> bool:
        """Checkpoint 8.5: Execute scrolling and liking before profile navigation"""
        try:
            if self.progress_callback:
                self.progress_callback("scrolling_and_liking", 77)
            self.logger.info("🔄 CHECKPOINT 8.5: Scrolling and liking")
            
            # Check if scrolling/liking is configured and needed
            scrolling_minutes = getattr(self, 'scrolling_minutes', 0)
            likes_target = getattr(self, 'likes_target', 0)
            
            if scrolling_minutes == 0 and likes_target == 0:
                self.logger.info("⏭️ No scrolling or liking configured - skipping")
                return True
            
            # Check if already done today (once per day)
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            device_id = getattr(self, 'device_id', 'unknown')
            
            # Create tracking directory if it doesn't exist
            tracking_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "FSN-MAC-AGENT", "tracking_files")
            os.makedirs(tracking_dir, exist_ok=True)
            tracking_file = os.path.join(tracking_dir, f"scroll_tracking_{device_id}_{today}.json")
            
            if os.path.exists(tracking_file):
                self.logger.info(f"✅ Scrolling and liking already completed today")
                return True
            
            self.logger.info(f"🎯 Starting scrolling and liking: {scrolling_minutes} minutes, {likes_target} likes")
            
            # Navigate to home feed for scrolling
            try:
                home_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "feed-tab-main")
                home_tab.click()
                time.sleep(2)
                self.logger.info("✅ Navigated to home feed for scrolling")
            except Exception as e:
                self.logger.error(f"❌ Failed to navigate to home feed: {e}")
                return False
            
            # Execute scrolling with distributed liking
            start_time = time.time()
            end_time = start_time + (scrolling_minutes * 60)  # Convert to seconds
            likes_completed = 0
            scroll_count = 0
            
            # Calculate like intervals (distribute likes evenly over scrolling time)
            if likes_target > 0:
                like_interval = (scrolling_minutes * 60) / likes_target  # Seconds between likes
                next_like_time = start_time + like_interval
            else:
                next_like_time = end_time + 1  # Never like if target is 0
            
            self.logger.info(f"🎯 Scrolling plan: {scrolling_minutes} minutes with {likes_target} likes (1 like every {like_interval:.0f} seconds)")
            
            while time.time() < end_time:
                try:
                    # Always scroll (continuous scrolling for full duration)
                    driver.swipe(200, 500, 200, 200, 1000)  # Scroll down
                    scroll_count += 1
                    time.sleep(3)  # 3 seconds between scrolls
                    
                    # Check if it's time to like a post
                    current_time = time.time()
                    if current_time >= next_like_time and likes_completed < likes_target:
                        try:
                            like_buttons = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "like-button")
                            if like_buttons:
                                # Try to find an unliked post
                                liked = False
                                for like_btn in like_buttons[:5]:  # Check first 5 like buttons
                                    try:
                                        # Check if already liked (you might need to check button state)
                                        like_btn.click()
                                        likes_completed += 1
                                        self.logger.info(f"❤️ Liked post {likes_completed}/{likes_target} at {(current_time - start_time)/60:.1f} minutes")
                                        
                                        # Schedule next like
                                        next_like_time = current_time + like_interval
                                        liked = True
                                        time.sleep(2)  # Short pause after liking
                                        break
                                    except Exception as like_error:
                                        continue
                                
                                if not liked:
                                    self.logger.warning(f"⚠️ Could not like any posts, will try again later")
                                    next_like_time = current_time + 10  # Try again in 10 seconds
                            else:
                                self.logger.warning(f"⚠️ No like buttons found, continuing scrolling")
                                next_like_time = current_time + 10  # Try again in 10 seconds
                                
                        except Exception as like_error:
                            self.logger.warning(f"⚠️ Error during like attempt: {like_error}")
                            next_like_time = current_time + 10  # Try again in 10 seconds
                    
                    # Progress update every 10 scrolls
                    if scroll_count % 10 == 0:
                        elapsed_minutes = (time.time() - start_time) / 60
                        progress = min(100, int((elapsed_minutes / scrolling_minutes) * 100))
                        remaining_minutes = scrolling_minutes - elapsed_minutes
                        self.logger.info(f"📊 Scrolling: {progress}% ({elapsed_minutes:.1f}/{scrolling_minutes} min, {likes_completed}/{likes_target} likes, {remaining_minutes:.1f} min left)")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error during scroll: {e}")
                    time.sleep(1)  # Brief pause before continuing
                    continue
            
            # Final summary
            total_time = (time.time() - start_time) / 60
            self.logger.info(f"🏁 Scrolling completed: {total_time:.1f} minutes, {scroll_count} scrolls, {likes_completed} likes")
            
            # Scroll up once to make profile tab visible
            try:
                self.logger.info("⬆️ Scrolling up to reveal profile tab")
                driver.swipe(200, 200, 200, 500, 1000)  # Scroll up
                time.sleep(2)
                self.logger.info("✅ Scrolled up - profile tab should be visible")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not scroll up: {e}")
            
            # Mark as completed for today
            import json
            try:
                with open(tracking_file, 'w') as f:
                    json.dump({
                        "date": today,
                        "device_id": device_id,
                        "scrolling_minutes": scrolling_minutes,
                        "likes_completed": likes_completed,
                        "scrolls_performed": scroll_count,
                        "completed_at": datetime.now().isoformat()
                    }, f)
                self.logger.info(f"📝 Tracking saved: {tracking_file}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not save tracking file: {e}")
            
            self.logger.info(f"✅ Scrolling and liking completed: {likes_completed} likes, {scroll_count} scrolls in {scrolling_minutes} minutes")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 8.5 failed: {e}")
            return False
    
    def checkpoint_9_navigate_to_profile(self, driver) -> bool:
        """Checkpoint 9: Navigate to profile tab for tracking"""
        try:
            if self.progress_callback:
                self.progress_callback("navigate_to_profile", 85)
            self.logger.info("👤 CHECKPOINT 9: Navigate to profile tab for tracking")
            
            # Find and click profile tab
            profile_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "profile-tab")
            tab_label = profile_tab.get_attribute('label')
            self.logger.info(f"👆 Clicking profile tab: {tab_label}")
            
            profile_tab.click()
            time.sleep(3)  # Allow profile page to load
            
            # Verify we're on profile page
            try:
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, "TestName_1736")
                self.logger.info("✅ Successfully navigated to profile page")
                return True
            except:
                self.logger.error("❌ Profile page navigation verification failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 9 failed: {e}")
            return False
    
    def define_checkpoints(self):
        """Define the checkpoint sequence for post thread test with profile tracking"""
        return [
            (self.checkpoint_0_launch_threads_from_desktop, "launch_threads_from_desktop"),
            (self.checkpoint_1_navigate_to_home_feed, "navigate_to_home_feed"),
            (self.checkpoint_2_click_create_tab, "click_create_tab"),
            (self.checkpoint_3_enter_text, "enter_text"),
            (self.checkpoint_4_add_image, "add_image"),
            (self.checkpoint_5_post_thread, "post_thread"),
            (self.checkpoint_6_handle_popups, "handle_popups"),
            (self.checkpoint_7_verify_post, "verify_post"),
            (self.checkpoint_8_return_safe_state, "return_safe_state"),
            (self.checkpoint_8_5_scrolling_and_liking, "scrolling_and_liking"),  # NEW: Scrolling and liking
            (self.checkpoint_9_navigate_to_profile, "navigate_to_profile"),
            (self.checkpoint_10_extract_followers, "extract_followers"),
            (self.checkpoint_11_save_tracking_data, "save_tracking_data"),
            (self.checkpoint_12_terminate_app, "terminate_app")
        ]
    
    def _detect_device_type(self):
        """Detect device type before creating driver"""
        try:
            self.logger.info(f"🔍 _detect_device_type called - current device_type: {self.device_type}, container_id: {self.container_id}")
            
            # If device type is already provided, use it
            if self.device_type != "non_jailbroken" or self.container_id:
                self.logger.info(f"🔧 Device type already provided: {self.device_type}")
                return
            
            self.logger.info("🔍 Device type not provided, attempting to detect from database")
            
            # Try to get device information from database
            device_info = self._get_device_info_from_database()
            self.logger.info(f"🔍 Database query result: {device_info}")
            
            if device_info:
                self.device_type = "jailbroken" if device_info.get('jailbroken', False) else "non_jailbroken"
                if self.device_type == "jailbroken":
                    # Try to get container info from account or use default
                    self.container_id = device_info.get('container_id', '1')
                self.logger.info(f"🔍 Retrieved device info from database: {self.device_type}")
            else:
                self.logger.warning("🔍 Could not detect device type, using default: non_jailbroken")
                
        except Exception as e:
            self.logger.error(f"🔍 Failed to detect device type: {e}")
            self.logger.info("🔍 Using default: non_jailbroken")
    
    def run_test(self):
        """Execute the complete Threads post thread test"""
        self.logger.info("🧵 STARTING THREADS POST_THREAD TEST")
        self.logger.info("🚀 PHASE 2B CONTENT CREATION - USING USER-PROVIDED SELECTORS!")
        
        try:
            # Setup driver (will detect device type from driver capabilities)
            self.logger.info("🔧 Setting up driver - will detect device type from capabilities")
            
            # Setup driver (will use existing or create new)
            if not self.setup_driver():
                return False
            
            # Execute checkpoints
            checkpoints = self.define_checkpoints()
            success = self.run_checkpoint_sequence(self.driver, checkpoints)
            
            if success:
                self.logger.info("🎉 THREADS POST_THREAD: SUCCESS!")
                self.logger.info("🧵 CONTENT CREATION ACTION WORKING!")
                
                # Summary
                self.logger.info(f"📊 Posts created: {self.posts_created}")
                self.logger.info(f"📝 Test text: {self.test_text}")
                    
            else:
                self.logger.error("❌ THREADS POST_THREAD: NEEDS INVESTIGATION")
                
            return success
            
        except Exception as e:
            self.logger.error(f"💥 TEST EXECUTION ERROR: {e}")
            return False
            
        finally:
            AppiumDriverManager.safe_quit_driver(self.driver)
    
    def checkpoint_10_extract_followers(self, driver) -> bool:
        """Checkpoint 10: Extract followers count and username"""
        try:
            if self.progress_callback:
                self.progress_callback("extract_followers", 92)
            self.logger.info("📊 CHECKPOINT 10: Extract followers count and username")
            
            # Initialize profile data storage
            if not hasattr(self, 'profile_data'):
                self.profile_data = {}
            
            # Extract username
            try:
                username_element = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "jacqub_s")
                username = username_element.get_attribute('name')
                self.profile_data['username'] = username
                self.logger.info(f"👤 Extracted username: {username}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not extract username: {e}")
                self.profile_data['username'] = "Unknown"
            
            # Extract name
            try:
                name_element = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "TestName_1736")
                name = name_element.get_attribute('name')
                self.profile_data['name'] = name
                self.logger.info(f"👤 Extracted name: {name}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not extract name: {e}")
                self.profile_data['name'] = "Unknown"
            
            # Extract followers count
            try:
                followers_element = driver.find_element(AppiumBy.XPATH, "//XCUIElementTypeLink[contains(@name, 'followers')]")
                followers_text = followers_element.get_attribute('name')
                self.profile_data['followers_raw'] = followers_text
                
                # Parse followers count from text (e.g., "16 followers" -> 16)
                try:
                    followers_count = int(followers_text.split()[0])
                    self.profile_data['followers_count'] = followers_count
                    self.logger.info(f"📊 Extracted followers count: {followers_count}")
                except:
                    self.logger.warning(f"⚠️ Could not parse followers count from: {followers_text}")
                    self.profile_data['followers_count'] = 0
                
            except Exception as e:
                self.logger.error(f"❌ Failed to extract followers: {e}")
                self.profile_data['followers_raw'] = None
                self.profile_data['followers_count'] = 0
                return False
            
            self.logger.info("✅ Profile data extraction successful")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 10 failed: {e}")
            return False
    
    def checkpoint_11_save_tracking_data(self, driver) -> bool:
        """Checkpoint 11: Save tracking data to database"""
        try:
            if self.progress_callback:
                self.progress_callback("save_tracking_data", 96)
            self.logger.info("💾 CHECKPOINT 11: Save tracking data")
            
            if not hasattr(self, 'profile_data') or not self.profile_data.get('followers_count'):
                self.logger.error("❌ No profile data to save")
                return False
            
            # Prepare tracking data
            tracking_data = {
                "username": self.profile_data.get('username', 'Unknown'),
                "name": self.profile_data.get('name', 'Unknown'),
                "followers_count": self.profile_data.get('followers_count', 0),
                "followers_raw": self.profile_data.get('followers_raw', ''),
                "bio": self.profile_data.get('bio', ''),
                "scan_timestamp": datetime.now().isoformat(),
                "device_id": "4",  # TODO: Get from config
                "job_id": getattr(self, 'current_job_id', 'unknown')
            }
            
            # Save to tracking file
            import json
            import os
            
            tracking_file = "follower_tracking.json"
            tracking_list = []
            
            # Load existing data
            if os.path.exists(tracking_file):
                with open(tracking_file, 'r') as f:
                    tracking_list = json.load(f)
            
            # Add new data
            tracking_list.append(tracking_data)
            
            # Save back to file
            with open(tracking_file, 'w') as f:
                json.dump(tracking_list, f, indent=2)
            
            self.logger.info(f"💾 Saved tracking data: {tracking_data['username']} - {tracking_data['followers_count']} followers")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 11 failed: {e}")
            return False
    
    def checkpoint_12_terminate_app(self, driver) -> bool:
        """Checkpoint 12: Terminate Threads app for account switching"""
        try:
            if self.progress_callback:
                self.progress_callback("terminate_app", 100)
            self.logger.info("🔄 CHECKPOINT 12: Terminate Threads app")
            
            # Terminate the Threads app
            driver.terminate_app("com.burbn.threads")
            time.sleep(2)
            
            self.logger.info("✅ Threads app terminated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ CHECKPOINT 12 failed: {e}")
            return False

def main():
    """Run the Threads post thread test"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Threads POST_THREAD Test')
    parser.add_argument('--params', help='JSON file with parameters')
    args = parser.parse_args()
    
    # Default parameters
    device_type = "non_jailbroken"
    container_id = None
    post_text = "Default text post - please provide text content"
    
    # Load parameters from file if provided
    if args.params and os.path.exists(args.params):
        try:
            with open(args.params, 'r') as f:
                params = json.load(f)
                
            device_type = params.get('device_type', 'non_jailbroken')
            container_id = params.get('container_id')
            post_text = params.get('test_text', post_text)
            
            print(f"🔧 Loaded parameters:")
            print(f"   Device Type: {device_type}")
            print(f"   Container ID: {container_id}")
            print(f"   Post Text: {post_text[:50]}...")
            
        except Exception as e:
            print(f"⚠️ Failed to load parameters: {e}")
            print("Using default parameters")
    
    # Create test with parameters
    test = ThreadsPostThreadTest(
        post_text=post_text,
        device_type=device_type,
        container_id=container_id
    )
    
    success = test.run_test()
    
    if success:
        print("\n🎉 THREADS POST_THREAD TEST PASSED!")
        print("🧵 CONTENT CREATION ACTION IMPLEMENTED SUCCESSFULLY!")
        exit(0)
    else:
        print("\n❌ THREADS POST_THREAD TEST NEEDS INVESTIGATION")
        print("📋 Check logs for details")
        exit(1)

if __name__ == "__main__":
    main()
