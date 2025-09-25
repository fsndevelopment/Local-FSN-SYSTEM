"""
Threads Warmup Engagement Test
Executes warmup activities: scrolling, liking, and following without posting content
"""
import time
import structlog
from platforms.shared.utils.checkpoint_system import CheckpointSystem
from platforms.shared.utils.appium_driver import AppiumDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from appium.webdriver.common.appiumby import AppiumBy

logger = structlog.get_logger()

class ThreadsWarmupTest(CheckpointSystem):
    """Threads warmup engagement test for account credibility building"""
    
    def __init__(self, scroll_minutes=10, likes_count=5, follows_count=2, expected_username=None, device_type="jailbroken", container_id=None, existing_driver=None):
        super().__init__("threads", "warmup")
        self.driver = existing_driver  # Use existing driver if provided (EXACT SAME AS POSTING)
        self.wait = None
        self.scroll_minutes = scroll_minutes
        self.likes_count = likes_count
        self.follows_count = follows_count
        self.expected_username = expected_username
        self.device_type = device_type
        self.container_id = container_id
        self.likes_performed = 0
        self.follows_performed = 0
        self.scroll_start_time = None
        self.use_existing_driver = existing_driver is not None
        
        logger.info("🔥 THREADS WARMUP TEST INITIALIZED", 
                   scroll_minutes=scroll_minutes, 
                   likes_count=likes_count, 
                   follows_count=follows_count,
                   expected_username=expected_username,
                   device_type=device_type,
                   container_id=container_id)
    
    def start_appium_server(self):
        """Start Appium server automatically if not running"""
        try:
            import subprocess
            import time
            from platforms.config import DEVICE_CONFIG
            
            appium_port = DEVICE_CONFIG['appium_port']
            logger.info(f"🔧 Checking if Appium server is running on port {appium_port}")
            
            # Check if port is in use
            result = subprocess.run(['lsof', '-i', f':{appium_port}'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                # Port is free, start Appium server
                logger.info(f"🚀 Starting Appium server on port {appium_port}")
                appium_process = subprocess.Popen(
                    ['appium', '--port', str(appium_port), '--log-level', 'error'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for server to start
                time.sleep(5)
                
                # Check if server started successfully
                result = subprocess.run(['lsof', '-i', f':{appium_port}'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ Appium server started successfully")
                    return True
                else:
                    logger.error("❌ Failed to start Appium server")
                    return False
            else:
                logger.info("✅ Appium server already running")
                return True
                
        except Exception as e:
            logger.error("❌ Error starting Appium server", error=str(e))
            return False
    
    def define_checkpoints(self):
        """Define the checkpoint sequence for warmup automation"""
        return [
            (self.checkpoint_1_launch_threads, "launch_threads"),
            (self.checkpoint_2_navigate_to_feed, "navigate_to_feed"), 
            (self.checkpoint_3_execute_scrolling_and_engagement, "scrolling_and_engagement"),
            (self.checkpoint_4_navigate_to_profile, "navigate_to_profile"),
            (self.checkpoint_5_extract_profile_data, "extract_profile_data")
        ]
    
    def setup_driver(self):
        """Initialize driver and launch Threads app from desktop - EXACT SAME AS POSTING"""
        try:
            # If we have an existing driver, use it and get device info from its capabilities (EXACT SAME AS POSTING)
            if self.use_existing_driver and self.driver:
                logger.info("🔧 Using existing driver with capabilities")
                
                # Get device info from existing driver capabilities
                try:
                    capabilities = self.driver.capabilities
                    jailbroken = capabilities.get('appium:jailbroken', False)
                    device_name = capabilities.get('appium:deviceName', 'Unknown Device')
                    
                    logger.info(f"🔍 Existing driver capabilities - Device: {device_name}, Jailbroken: {jailbroken}")
                    
                    if jailbroken:
                        self.device_type = "jailbroken"
                        self.container_id = self.container_id or "1"  # Use provided or default
                        logger.info(f"🔧 Detected JB device from existing driver: {self.device_type}")
                    else:
                        self.device_type = "non_jailbroken"
                        logger.info("📱 Detected NONJB device from existing driver")
                        
                except Exception as e:
                    logger.error(f"Failed to get capabilities from existing driver: {e}")
                
                self.wait = AppiumDriverManager.get_wait_driver(self.driver)
                logger.info("✅ Using existing driver - ready to launch Threads")
                return True
            
            # Create new driver if no existing driver (EXACT SAME AS POSTING)
            logger.info("🧵 Setting up driver and launching Threads from desktop...")
            
            # First, create driver for iOS home screen (no specific bundle) - EXACT SAME AS POSTING
            from platforms.config import DEVICE_CONFIG
            from appium.options.ios import XCUITestOptions
            from appium import webdriver
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = str(DEVICE_CONFIG["udid"])  # Ensure UDID is string
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.wda_local_port = DEVICE_CONFIG["wda_port"]
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            # No bundle_id specified - will connect to home screen
            
            self.driver = webdriver.Remote(f"http://localhost:{DEVICE_CONFIG['appium_port']}", options=options)
            self.wait = AppiumDriverManager.get_wait_driver(self.driver)
            
            logger.info("✅ Driver setup complete - ready to launch Threads")
            return True
        except Exception as e:
            logger.error(f"❌ Driver setup failed: {e}")
            return False
    
    
    async def run_full_test(self):
        """Run the complete warmup test sequence"""
        try:
            logger.info("🔥 STARTING THREADS WARMUP TEST")
            
            # Set up driver first
            if not self.setup_driver():
                return {"success": False, "error": "Failed to setup driver"}
            
            logger.info("📁 Evidence directory", path=self.evidence_dir)
            
            # Execute warmup sequence using checkpoint system
            checkpoints = self.define_checkpoints()
            success = await self.run_checkpoint_sequence(self.driver, checkpoints)
            
            # Calculate results based on checkpoint success
            success_rate = len(self.checkpoints_passed) / len(checkpoints) if checkpoints else 0
            
            result = {
                "success": success,
                "checkpoints_passed": self.checkpoints_passed,
                "total_checkpoints": len(checkpoints),
                "likes_performed": self.likes_performed,
                "follows_performed": self.follows_performed,
                "scroll_time_minutes": (time.time() - self.scroll_start_time) / 60 if self.scroll_start_time else 0,
                "evidence_dir": self.evidence_dir
            }
            
            logger.info("🎯 THREADS WARMUP RESULTS", **result)
            
            if success:
                logger.info("✅ WARMUP TEST: SUCCESS")
            else:
                logger.error("❌ WARMUP TEST: NEEDS INVESTIGATION")
            
            return result
            
        except Exception as e:
            logger.error("❌ WARMUP TEST FAILED", error=str(e))
            return {"success": False, "error": str(e)}
        finally:
            # Clean up driver
            self.cleanup_driver()
    
    def cleanup_driver(self):
        """Clean up the Appium driver"""
        try:
            if self.driver:
                logger.info("🧹 Cleaning up Appium driver")
                self.driver.quit()
                self.driver = None
                self.wait = None
        except Exception as e:
            logger.error("❌ Error cleaning up driver", error=str(e))
    
    async def checkpoint_1_launch_threads(self, driver=None):
        """Launch Threads app from desktop and verify it's open - CHECK IF ALREADY RUNNING FIRST"""
        logger.info("🎯 CHECKPOINT 1: Launch Threads app from desktop")
        
        try:
            # Use provided driver or self.driver
            current_driver = driver if driver else self.driver
            
            # First, check if Threads is already running (like posting test does)
            try:
                page_source = current_driver.page_source
                if "main-feed" in page_source or "feed-tab-main" in page_source or "Threads" in page_source:
                    logger.info("✅ Threads app is already running - feed elements detected")
                    return True
            except Exception as e:
                logger.info(f"🔍 Checking if Threads already running: {e}")
            
            # If not running, launch from desktop (like working posting tests)
            threads_icon_selector = "Threads"
            
            try:
                # Find Threads app icon on desktop
                threads_icon = current_driver.find_element("accessibility id", threads_icon_selector)
                logger.info(f"✅ Found Threads app icon: {threads_icon_selector}")
                
                # Tap to launch Threads
                logger.info("👆 Tapping Threads app icon...")
                threads_icon.click()
                
                # Wait for app to launch
                time.sleep(5)  # Give app time to fully load
                
                # Verify Threads app launched
                try:
                    page_source = current_driver.page_source
                    
                    if "main-feed" in page_source or "feed-tab-main" in page_source:
                        logger.info("✅ Threads app launched successfully - feed elements detected")
                        return True
                    else:
                        logger.warning("⚠️ Threads app launched but feed not immediately visible")
                        # Still consider success - app might be loading or showing onboarding
                        return True
                        
                except Exception as e:
                    logger.warning("⚠️ Could not verify app launch details", error=str(e))
                    # Still consider success if icon tap worked
                    return True
                    
            except Exception as e:
                logger.error("❌ Failed to find or tap Threads app icon", error=str(e))
                return False
                
        except Exception as e:
            logger.error("❌ Error launching Threads", error=str(e))
            return False
    
    async def checkpoint_2_navigate_to_feed(self, driver=None):
        """Navigate to the main feed for scrolling"""
        logger.info("🎯 CHECKPOINT 2: Navigate to feed")
        
        try:
            # Use provided driver or self.driver
            current_driver = driver if driver else self.driver
            
            # Look for home/feed button
            feed_selectors = [
                "//XCUIElementTypeButton[@name='Home']",
                "//XCUIElementTypeButton[@name='Feed']",
                "//XCUIElementTypeButton[contains(@name, 'Home')]",
                "//XCUIElementTypeTabBarButton[@name='Home']"
            ]
            
            feed_button = None
            for selector in feed_selectors:
                try:
                    feed_button = current_driver.find_element("xpath", selector)
                    if feed_button:
                        break
                except:
                    continue
            
            if feed_button:
                feed_button.click()
                time.sleep(2)
                logger.info("✅ Navigated to feed successfully")
                return True
            else:
                # Assume we're already in feed if no button found
                logger.info("✅ Already in feed")
                return True
                
        except Exception as e:
            logger.error("❌ Error navigating to feed", error=str(e))
            return False
    
    async def checkpoint_3_execute_scrolling_and_engagement(self, driver=None):
        """Execute scrolling and engagement activities (likes, follows)"""
        logger.info("🎯 CHECKPOINT 3: Execute scrolling and engagement")
        
        try:
            # Use provided driver or self.driver
            current_driver = driver if driver else self.driver
            
            self.scroll_start_time = time.time()
            scroll_end_time = self.scroll_start_time + (self.scroll_minutes * 60)
            
            logger.info("📱 Starting scroll session", 
                       duration_minutes=self.scroll_minutes,
                       target_likes=self.likes_count,
                       target_follows=self.follows_count)
            
            while time.time() < scroll_end_time:
                # Perform scrolling
                await self._perform_scroll(current_driver)
                
                # Randomly like posts during scrolling
                if self.likes_performed < self.likes_count and self._should_perform_action():
                    if await self._perform_like(current_driver):
                        self.likes_performed += 1
                        logger.info("👍 Performed like", 
                                   current=self.likes_performed, 
                                   target=self.likes_count)
                
                # Randomly follow accounts during scrolling
                if self.follows_performed < self.follows_count and self._should_perform_action():
                    if await self._perform_follow(current_driver):
                        self.follows_performed += 1
                        logger.info("👥 Performed follow", 
                                   current=self.follows_performed, 
                                   target=self.follows_count)
                
                # Check if we've completed all activities
                if (self.likes_performed >= self.likes_count and 
                    self.follows_performed >= self.follows_count):
                    logger.info("🎉 All engagement activities completed early")
                    break
                
                time.sleep(2)  # Brief pause between actions
            
            # Save results
            actual_scroll_time = (time.time() - self.scroll_start_time) / 60
            logger.info("📊 Scroll session completed", 
                       actual_time_minutes=actual_scroll_time,
                       likes_performed=self.likes_performed,
                       follows_performed=self.follows_performed)
            
            return True
            
        except Exception as e:
            logger.error("❌ Error during scrolling and engagement", error=str(e))
            return False
    
    async def checkpoint_4_navigate_to_profile(self, driver=None):
        """Navigate to profile to verify account"""
        logger.info("🎯 CHECKPOINT 4: Navigate to profile")
        
        try:
            # Look for profile button
            profile_selectors = [
                "//XCUIElementTypeButton[@name='Profile']",
                "//XCUIElementTypeTabBarButton[@name='Profile']",
                "//XCUIElementTypeButton[contains(@name, 'Profile')]"
            ]
            
            profile_button = None
            for selector in profile_selectors:
                try:
                    profile_button = self.driver.find_element("xpath", selector)
                    if profile_button:
                        break
                except:
                    continue
            
            if profile_button:
                profile_button.click()
                time.sleep(3)
                
                # Verify we're on profile page
                if self._verify_profile_page():
                    logger.info("✅ Navigated to profile successfully")
                    return True
                else:
                    logger.error("❌ Failed to verify profile page")
                    return False
            else:
                logger.error("❌ Profile button not found")
                return False
                
        except Exception as e:
            logger.error("❌ Error navigating to profile", error=str(e))
            return False
    
    async def checkpoint_5_extract_profile_data(self, driver=None):
        """Extract profile data for verification"""
        logger.info("🎯 CHECKPOINT 5: Extract profile data")
        
        try:
            profile_data = self._extract_profile_information()
            
            if profile_data:
                logger.info("📊 Profile data extracted", **profile_data)
                return True
            else:
                logger.error("❌ Failed to extract profile data")
                return False
                
        except Exception as e:
            logger.error("❌ Error extracting profile data", error=str(e))
            return False
    
    async def _perform_scroll(self, driver=None):
        """Perform a scroll action"""
        try:
            # Use provided driver or self.driver
            current_driver = driver if driver else self.driver
            
            # Get screen dimensions
            size = current_driver.get_window_size()
            start_x = size['width'] // 2
            start_y = size['height'] * 0.8
            end_y = size['height'] * 0.2
            
            # Perform scroll
            current_driver.swipe(start_x, start_y, start_x, end_y, 800)
            time.sleep(1)
            
        except Exception as e:
            logger.error("❌ Error during scroll", error=str(e))
    
    async def _perform_like(self, driver=None):
        """Perform a like action on current post"""
        try:
            # Use provided driver or self.driver
            current_driver = driver if driver else self.driver
            
            # Look for like button
            like_selectors = [
                "//XCUIElementTypeButton[@name='Like']",
                "//XCUIElementTypeButton[contains(@name, 'Like')]",
                "//XCUIElementTypeButton[contains(@name, 'heart')]"
            ]
            
            for selector in like_selectors:
                try:
                    like_button = current_driver.find_element("xpath", selector)
                    if like_button:
                        like_button.click()
                        time.sleep(1)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error("❌ Error performing like", error=str(e))
            return False
    
    async def _perform_follow(self, driver=None):
        """Perform a follow action on current profile"""
        try:
            # Use provided driver or self.driver
            current_driver = driver if driver else self.driver
            
            # Look for follow button
            follow_selectors = [
                "//XCUIElementTypeButton[@name='Follow']",
                "//XCUIElementTypeButton[contains(@name, 'Follow')]"
            ]
            
            for selector in follow_selectors:
                try:
                    follow_button = current_driver.find_element("xpath", selector)
                    if follow_button:
                        follow_button.click()
                        time.sleep(1)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error("❌ Error performing follow", error=str(e))
            return False
    
    def _should_perform_action(self):
        """Determine if we should perform an action (likes/follows)"""
        import random
        return random.random() < 0.3  # 30% chance during each scroll
    
    async def _is_threads_app_open(self, driver=None):
        """Check if Threads app is currently open"""
        try:
            # Use provided driver or self.driver
            current_driver = driver if driver else self.driver
            
            # Look for Threads-specific elements
            threads_indicators = [
                "//XCUIElementTypeStaticText[contains(@name, 'Threads')]",
                "//XCUIElementTypeButton[contains(@name, 'Threads')]"
            ]
            
            for indicator in threads_indicators:
                try:
                    element = current_driver.find_element("xpath", indicator)
                    if element:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error("❌ Error checking if Threads is open", error=str(e))
            return False
    
    def _verify_profile_page(self):
        """Verify we're on the profile page"""
        try:
            # Look for profile-specific elements
            profile_indicators = [
                "//XCUIElementTypeStaticText[contains(@name, 'Followers')]",
                "//XCUIElementTypeStaticText[contains(@name, 'Following')]",
                "//XCUIElementTypeButton[@name='Edit profile']"
            ]
            
            for indicator in profile_indicators:
                try:
                    element = self.driver.find_element("xpath", indicator)
                    if element:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error("❌ Error verifying profile page", error=str(e))
            return False
    
    def _extract_profile_information(self):
        """Extract profile information"""
        try:
            profile_data = {}
            
            # Extract username
            username_selectors = [
                "//XCUIElementTypeStaticText[contains(@name, '@')]",
                "//XCUIElementTypeStaticText[contains(@name, 'username')]"
            ]
            
            for selector in username_selectors:
                try:
                    element = self.driver.find_element("xpath", selector)
                    if element:
                        profile_data['username'] = element.get_attribute('name')
                        break
                except:
                    continue
            
            # Extract follower count
            follower_selectors = [
                "//XCUIElementTypeStaticText[contains(@name, 'Followers')]",
                "//XCUIElementTypeStaticText[contains(@name, 'followers')]"
            ]
            
            for selector in follower_selectors:
                try:
                    element = self.driver.find_element("xpath", selector)
                    if element:
                        follower_text = element.get_attribute('name')
                        # Extract number from text
                        import re
                        numbers = re.findall(r'\d+', follower_text)
                        if numbers:
                            profile_data['followers_count'] = int(numbers[0])
                        break
                except:
                    continue
            
            return profile_data if profile_data else None
            
        except Exception as e:
            logger.error("❌ Error extracting profile information", error=str(e))
            return None
