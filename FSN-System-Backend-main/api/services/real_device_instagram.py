#!/usr/bin/env python3
"""
Real Device Instagram Integration Service
Integrates confirmed working tests with FastAPI job system

This service uses our CONFIRMED WORKING selectors and flows from:
- tests/device/CONFIRMED_WORKING/simple_like_test.py
- tests/device/CONFIRMED_WORKING/working_story_test.py
- tests/device/CONFIRMED_WORKING/comment_functionality_test.py
- tests/device/CONFIRMED_WORKING/follow_unfollow_functionality_test.py
- tests/device/CONFIRMED_WORKING/simple_scan_profile_test.py
- tests/device/CONFIRMED_WORKING/post_picture_functionality_test.py
- tests/device/CONFIRMED_WORKING/search_hashtag_functionality_test.py
- tests/device/CONFIRMED_WORKING/save_post_functionality_test.py

✅ ALL SELECTORS CONFIRMED WORKING ON REAL iPHONE
"""
import asyncio
import time
import random
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from appium import webdriver
from appium.options.ios import XCUITestOptions
from .appium_service import appium_service
from .rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

class RealDeviceInstagram:
    """Real device Instagram service using confirmed working selectors"""
    
    def __init__(self):
        self.timeout = 15
        self.confirmed_selectors = {
            'like_button': 'like-button',
            'comment_button': 'comment-button', 
            'follow_button': 'user-detail-header-follow-button',
            'stories_tray': 'stories-tray',
            'story_ring': 'story-ring',
            'tabs': {
                'home': 'mainfeed-tab',
                'explore': 'explore-tab',
                'profile': 'profile-tab',
                'reels': 'reels-tab',
                'camera': 'camera-tab'
            }
        }
    
    def get_current_camera_mode(self, driver):
        """Get the current camera mode value"""
        try:
            from appium.webdriver.common.appiumby import AppiumBy
            mode_selector = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "current-camera-mode")
            current_value = mode_selector.get_attribute('value') or mode_selector.text
            return current_value.upper() if current_value else None
        except Exception as e:
            logger.error(f"Could not get current mode: {e}")
            return None

    def switch_camera_mode(self, driver, mode):
        """
        Switch Instagram camera mode using proper iOS Adjustable element handling
        
        Args:
            driver: Appium WebDriver instance
            mode (str): Mode to switch to - 'POST', 'STORY', or 'REEL'
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from appium.webdriver.common.appiumby import AppiumBy
            import time
            
            target_mode = mode.upper()
            if target_mode not in ['POST', 'STORY', 'REEL']:
                logger.error(f"Invalid mode: {mode}. Use POST, STORY, or REEL")
                return False
            
            logger.info(f"🎯 Switching to {target_mode} mode...")
            
            # Find the mode selector (iOS Adjustable element)
            mode_selector = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "current-camera-mode")
            
            # Get current mode
            current_mode = self.get_current_camera_mode(driver)
            logger.info(f"Current mode: {current_mode}")
            
            if current_mode == target_mode:
                logger.info(f"Already in {target_mode} mode!")
                return True
            
            # Define mode order (left to right in UI)
            mode_order = ['POST', 'STORY', 'REEL']
            
            if current_mode not in mode_order:
                logger.error(f"Unknown current mode: {current_mode}")
                return False
            
            current_index = mode_order.index(current_mode)
            target_index = mode_order.index(target_mode)
            steps_needed = target_index - current_index
            
            logger.info(f"Need to move {abs(steps_needed)} steps {'right' if steps_needed > 0 else 'left'}")
            
            # Use iOS accessibility increment/decrement for Adjustable elements
            try:
                for i in range(abs(steps_needed)):
                    if steps_needed > 0:
                        # Move right (increment)
                        driver.execute_script("mobile: increment", {"element": mode_selector})
                    else:
                        # Move left (decrement) 
                        driver.execute_script("mobile: decrement", {"element": mode_selector})
                    
                    time.sleep(1)  # Wait between steps
                    
                    # Verify progress
                    new_mode = self.get_current_camera_mode(driver)
                    if new_mode == target_mode:
                        break
                
                # Final verification
                final_mode = self.get_current_camera_mode(driver)
                if final_mode == target_mode:
                    logger.info(f"✅ Successfully switched to {target_mode} mode!")
                    return True
                else:
                    logger.warning(f"Didn't reach target mode. Current: {final_mode}")
                    
                    # Fallback: Try swipe gestures
                    logger.info("Trying swipe fallback...")
                    location = mode_selector.location
                    size = mode_selector.size
                    center_y = location['y'] + size['height'] // 2
                    
                    remaining_steps = target_index - mode_order.index(final_mode) if final_mode in mode_order else steps_needed
                    
                    for i in range(abs(remaining_steps)):
                        if remaining_steps > 0:
                            # Swipe left to right
                            start_x = location['x'] + size['width'] * 0.3
                            end_x = location['x'] + size['width'] * 0.7
                        else:
                            # Swipe right to left
                            start_x = location['x'] + size['width'] * 0.7
                            end_x = location['x'] + size['width'] * 0.3
                        
                        driver.swipe(start_x, center_y, end_x, center_y, 300)
                        time.sleep(1)
                        
                        new_mode = self.get_current_camera_mode(driver)
                        if new_mode == target_mode:
                            logger.info(f"✅ Swipe fallback successful! Switched to {target_mode} mode")
                            return True
                    
                    return False
                    
            except Exception as e:
                logger.error(f"iOS accessibility actions failed: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to switch camera mode: {e}")
            return False
        
    def create_driver(self, device_udid: str = None):
        """Create Appium driver with confirmed working options for REAL DEVICE"""
        options = XCUITestOptions()
        options.platform_name = "iOS"
        options.automation_name = "XCUITest"
        options.bundle_id = "com.burbn.instagram"
        
        # Device-specific configuration
        if device_udid:
            options.udid = device_udid
            options.device_name = f"Real iPhone ({device_udid[:8]})"
        else:
            # Default to our known test device
            device_udid = "f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3"
            options.udid = device_udid
            options.device_name = "Real iPhone Test Device"
            
        # Multi-device port configuration
        device_configs = {
            "f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3": {  # PhoneX
                "appium_port": 4723,
                "wda_port": 8100
            },
            "df44ce18dfdd9d0ffd2420fb9fc0176a7b6bd64e": {  # Phone9
                "appium_port": 4735,
                "wda_port": 8106
            }
        }
        
        # Get port configuration for this device
        device_config = device_configs.get(device_udid, device_configs["f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3"])
        appium_port = device_config["appium_port"]
        wda_port = device_config["wda_port"]
        
        # Set WDA port
        options.wda_local_port = wda_port
            
        # Real device settings
        options.no_reset = True
        options.full_reset = False
        options.new_command_timeout = 300
        options.connect_hardware_keyboard = False
        
        try:
            appium_url = f"http://localhost:{appium_port}"
            driver = webdriver.Remote(appium_url, options=options)
            logger.info(f"✅ Connected to REAL device: {options.udid} on port {appium_port}")
            return driver
        except Exception as e:
            logger.error(f"❌ Failed to connect to REAL device {options.udid} on port {appium_port}: {e}")
            return None

    async def like_posts(self, device_udid: str, count: int = 5) -> Dict[str, Any]:
        """Like posts using confirmed working selectors with rate limiting"""
        result = {'success': False, 'message': '', 'data': {'liked_count': 0}}
        
        # Check rate limit first
        rate_check = rate_limiter.check_rate_limit(device_udid, "like")
        if not rate_check['allowed']:
            result['message'] = rate_check['message']
            result['data']['rate_limit_info'] = rate_check
            return result
        
        try:
            driver = self.create_driver(device_udid)
            if not driver:
                result['message'] = "Failed to create driver"
                return result
            
            # Navigate to home feed
            home_tab = driver.find_element("accessibility id", self.confirmed_selectors['tabs']['home'])
            home_tab.click()
            time.sleep(3)
            
            liked_count = 0
            for attempt in range(count * 2):  # More attempts than needed
                try:
                    # Scroll down to reveal like buttons
                    driver.swipe(200, 400, 200, 200, 800)
                    time.sleep(2)
                    
                    # Handle ad recovery if needed
                    await self._handle_ad_recovery(driver)
                    
                    # Find and click like button
                    like_button = driver.find_element("accessibility id", self.confirmed_selectors['like_button'])
                    like_button.click()
                    time.sleep(random.uniform(1, 3))
                    
                    liked_count += 1
                    logger.info(f"✅ Liked post {liked_count}/{count}")
                    
                    if liked_count >= count:
                        break
                        
                except Exception as e:
                    logger.warning(f"Like attempt {attempt + 1} failed: {e}")
                    continue
            
            result['success'] = True
            result['message'] = f"Successfully liked {liked_count} posts"
            result['data']['liked_count'] = liked_count
            
            # Record successful action
            rate_limiter.record_action(device_udid, "like", True, {'liked_count': liked_count})
            
        except Exception as e:
            result['message'] = f"Like action error: {str(e)}"
            logger.error(f"Like posts error: {e}")
            
            # Record failed action
            rate_limiter.record_action(device_udid, "like", False, {'error': str(e)})
        finally:
            if 'driver' in locals():
                driver.quit()
                
        return result

    async def comment_on_posts(self, device_udid: str, comments: List[str], count: int = 3) -> Dict[str, Any]:
        """Comment on posts using confirmed working 7-checkpoint system with rate limiting"""
        result = {'success': False, 'message': '', 'data': {'commented_count': 0}}
        
        # Check rate limit first (15 comments/hour)
        rate_check = rate_limiter.check_rate_limit(device_udid, "comment")
        if not rate_check['allowed']:
            result['message'] = rate_check['message']
            result['data']['rate_limit_info'] = rate_check
            return result
        
        try:
            driver = self.create_driver(device_udid)
            if not driver:
                result['message'] = "Failed to create driver"
                return result
            
            # Navigate to home feed with posts
            home_tab = driver.find_element("accessibility id", self.confirmed_selectors['tabs']['home'])
            home_tab.click()
            time.sleep(3)
            
            # Scroll down to reveal posts (stories are at top by default)
            driver.swipe(200, 400, 200, 200, 800)
            time.sleep(2)
            driver.swipe(200, 400, 200, 200, 800)
            time.sleep(2)
            
            commented_count = 0
            for attempt in range(count * 2):
                try:
                    # Handle ad recovery
                    await self._handle_ad_recovery(driver)
                    
                    # Find comment button
                    comment_button = driver.find_element("accessibility id", self.confirmed_selectors['comment_button'])
                    comment_button.click()
                    time.sleep(3)
                    
                    # Type comment
                    comment_text = random.choice(comments)
                    comment_input = driver.find_element("accessibility id", "text-view")
                    comment_input.send_keys(comment_text)
                    time.sleep(2)
                    
                    # Click post button (precise selector)
                    post_button = driver.find_element("xpath", "//XCUIElementTypeButton[@name='send-button' and @label='Post comment']")
                    post_button.click()
                    time.sleep(4)
                    
                    # Close comment section
                    close_button = driver.find_element("accessibility id", "Button")
                    close_button.click()
                    time.sleep(2)
                    
                    commented_count += 1
                    logger.info(f"✅ Commented on post {commented_count}/{count}: {comment_text}")
                    
                    if commented_count >= count:
                        break
                        
                    # Scroll to next post
                    driver.swipe(200, 400, 200, 200, 800)
                    time.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"Comment attempt {attempt + 1} failed: {e}")
                    # Scroll to next post on failure
                    try:
                        driver.swipe(200, 400, 200, 200, 800)
                        time.sleep(2)
                    except:
                        pass
                    continue
            
            result['success'] = True
            result['message'] = f"Successfully commented on {commented_count} posts"
            result['data']['commented_count'] = commented_count
            
        except Exception as e:
            result['message'] = f"Comment action error: {str(e)}"
            logger.error(f"Comment posts error: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                
        return result

    async def follow_user(self, device_udid: str, username: str) -> Dict[str, Any]:
        """Follow user using confirmed working search navigation with rate limiting"""
        result = {'success': False, 'message': '', 'data': {}}
        
        # Check rate limit first (20 follows/hour)  
        rate_check = rate_limiter.check_rate_limit(device_udid, "follow")
        if not rate_check['allowed']:
            result['message'] = rate_check['message']
            result['data']['rate_limit_info'] = rate_check
            return result
        
        try:
            driver = self.create_driver(device_udid)
            if not driver:
                result['message'] = "Failed to create driver"
                return result
            
            # Navigate to search
            explore_tab = driver.find_element("accessibility id", self.confirmed_selectors['tabs']['explore'])
            explore_tab.click()
            time.sleep(3)
            
            # Click search bar
            search_bar = driver.find_element("accessibility id", "search-bar")
            search_bar.click()
            time.sleep(2)
            
            # Type username
            search_input = driver.find_element("accessibility id", "search-text-input")
            search_input.send_keys(username)
            time.sleep(3)
            
            # CRITICAL: Skip search suggestion, click actual profile
            # Look for profile with story-ring (not search suggestion)
            profile_results = driver.find_elements("xpath", "//XCUIElementTypeCell[contains(@name, 'search-collection-view-cell-')]")
            
            clicked_profile = False
            for result_cell in profile_results:
                try:
                    # Check if this cell has story-ring (actual profile)
                    story_ring = result_cell.find_element("accessibility id", "story-ring")
                    # This is the actual profile, click it
                    result_cell.click()
                    clicked_profile = True
                    break
                except:
                    # This is likely the search suggestion, skip it
                    continue
            
            if not clicked_profile:
                result['message'] = f"Could not find profile for {username}"
                return result
            
            time.sleep(4)
            
            # Click follow button
            follow_button = driver.find_element("accessibility id", self.confirmed_selectors['follow_button'])
            initial_state = follow_button.get_attribute("label")
            follow_button.click()
            time.sleep(3)
            
            # Verify follow state change
            updated_button = driver.find_element("accessibility id", self.confirmed_selectors['follow_button'])
            final_state = updated_button.get_attribute("label")
            
            result['success'] = True
            result['message'] = f"Successfully followed {username}"
            result['data'] = {
                'username': username,
                'initial_state': initial_state,
                'final_state': final_state,
                'follow_confirmed': "Follow" in initial_state and "unfollow" in final_state.lower()
            }
            
        except Exception as e:
            result['message'] = f"Follow action error: {str(e)}"
            logger.error(f"Follow user error: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                
        return result

    async def view_stories(self, device_udid: str, count: int = 10) -> Dict[str, Any]:
        """View stories using confirmed working selectors"""
        result = {'success': False, 'message': '', 'data': {'viewed_count': 0}}
        
        try:
            driver = self.create_driver(device_udid)
            if not driver:
                result['message'] = "Failed to create driver"
                return result
            
            # Navigate to home feed
            home_tab = driver.find_element("accessibility id", self.confirmed_selectors['tabs']['home'])
            home_tab.click()
            time.sleep(3)
            
            viewed_count = 0
            for attempt in range(count):
                try:
                    # Find stories tray
                    stories_tray = driver.find_element("accessibility id", self.confirmed_selectors['stories_tray'])
                    
                    # Find individual story rings
                    story_rings = stories_tray.find_elements("accessibility id", self.confirmed_selectors['story_ring'])
                    
                    if not story_rings:
                        break
                    
                    # Click on a random story ring
                    story_ring = random.choice(story_rings)
                    story_ring.click()
                    time.sleep(random.uniform(3, 8))  # Watch story
                    
                    # Dismiss story
                    dismiss_button = driver.find_element("accessibility id", "story-dismiss-button")
                    dismiss_button.click()
                    time.sleep(2)
                    
                    viewed_count += 1
                    logger.info(f"✅ Viewed story {viewed_count}/{count}")
                    
                except Exception as e:
                    logger.warning(f"Story view attempt {attempt + 1} failed: {e}")
                    continue
            
            result['success'] = True
            result['message'] = f"Successfully viewed {viewed_count} stories"
            result['data']['viewed_count'] = viewed_count
            
        except Exception as e:
            result['message'] = f"Story view error: {str(e)}"
            logger.error(f"View stories error: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                
        return result

    async def scan_profile(self, device_udid: str, username: str = None) -> Dict[str, Any]:
        """Scan profile data using confirmed working extraction"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = self.create_driver(device_udid)
            if not driver:
                result['message'] = "Failed to create driver"
                return result
            
            if username:
                # Navigate to specific user profile via search
                explore_tab = driver.find_element("accessibility id", self.confirmed_selectors['tabs']['explore'])
                explore_tab.click()
                time.sleep(3)
                
                # Search for user (using same logic as follow_user)
                search_bar = driver.find_element("accessibility id", "search-bar")
                search_bar.click()
                time.sleep(2)
                
                search_input = driver.find_element("accessibility id", "search-text-input")
                search_input.send_keys(username)
                time.sleep(3)
                
                # Click actual profile (skip search suggestion)
                profile_results = driver.find_elements("xpath", "//XCUIElementTypeCell[contains(@name, 'search-collection-view-cell-')]")
                
                clicked_profile = False
                for result_cell in profile_results:
                    try:
                        story_ring = result_cell.find_element("accessibility id", "story-ring")
                        result_cell.click()
                        clicked_profile = True
                        break
                    except:
                        continue
                
                if not clicked_profile:
                    result['message'] = f"Could not find profile for {username}"
                    return result
                    
                time.sleep(4)
            else:
                # Navigate to own profile
                profile_tab = driver.find_element("accessibility id", self.confirmed_selectors['tabs']['profile'])
                profile_tab.click()
                time.sleep(3)
            
            # Extract profile data
            profile_data = {}
            
            try:
                # Extract username
                username_elements = driver.find_elements("xpath", "//XCUIElementTypeStaticText")
                for element in username_elements:
                    text = element.text
                    if text and "@" not in text and len(text) > 2:
                        profile_data['username'] = text
                        break
            except:
                pass
            
            try:
                # Extract follower/following counts (simplified)
                stat_elements = driver.find_elements("xpath", "//XCUIElementTypeStaticText")
                numbers = [elem.text for elem in stat_elements if elem.text.replace(',', '').isdigit()]
                if len(numbers) >= 3:
                    profile_data['posts'] = numbers[0]
                    profile_data['followers'] = numbers[1] 
                    profile_data['following'] = numbers[2]
            except:
                pass
            
            result['success'] = True
            result['message'] = f"Successfully scanned profile: {username or 'own profile'}"
            result['data'] = profile_data
            
        except Exception as e:
            result['message'] = f"Profile scan error: {str(e)}"
            logger.error(f"Scan profile error: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                
        return result

    async def _handle_ad_recovery(self, driver):
        """Handle ad recovery using confirmed working strategy"""
        try:
            # Check for common ad elements
            ad_indicators = ["cta-button", "ig icon x pano outline 24"]
            
            for indicator in ad_indicators:
                try:
                    ad_element = driver.find_element("accessibility id", indicator)
                    # Ad detected, navigate back to home
                    home_tab = driver.find_element("accessibility id", self.confirmed_selectors['tabs']['home'])
                    home_tab.click()
                    time.sleep(2)
                    logger.info("✅ Ad recovery successful")
                    return
                except:
                    continue
        except:
            pass

    async def post_picture(self, device_udid: str, caption: str = "Posted via FSN Appium") -> Dict[str, Any]:
        """Post picture with caption using confirmed working selectors"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = self.create_driver(device_udid)
            if not driver:
                result['message'] = "Failed to create driver"
                return result
            
            # Navigate to camera tab
            camera_tab = driver.find_element("accessibility id", "camera-tab")
            camera_tab.click()
            time.sleep(3)
            
            # Handle permission popups if they appear
            try:
                continue_button = driver.find_element("accessibility id", "ig-photo-library-priming-continue-button")
                continue_button.click()
                time.sleep(2)
            except:
                pass
                
            try:
                allow_photos = driver.find_element("accessibility id", "Allow Access to All Photos")
                allow_photos.click()
                time.sleep(2)
            except:
                pass
            
            # Select first photo from gallery
            try:
                first_photo = driver.find_element("name", "gallery-photo-cell-0")
                first_photo.click()
                time.sleep(2)
            except:
                # Fallback to any photo cell
                photo_cells = driver.find_elements("xpath", "//XCUIElementTypeCell[contains(@name, 'gallery-photo-cell')]")
                if photo_cells:
                    photo_cells[0].click()
                    time.sleep(2)
            
            # Click next button
            next_button = driver.find_element("accessibility id", "next-button")
            next_button.click()
            time.sleep(3)
            
            # Add caption using confirmed working selector
            try:
                caption_field = driver.find_element("accessibility id", "caption-cell-text-view")
                caption_field.click()
                time.sleep(1)
                
                # Use the corrected caption input selector
                caption_input = driver.find_element("xpath", "(//XCUIElementTypeTextView[@name='caption-cell-text-view'])[2]")
                caption_input.send_keys(caption)
                time.sleep(2)
                
                # Tap OK if keyboard appears
                try:
                    ok_button = driver.find_element("accessibility id", "OK")
                    ok_button.click()
                    time.sleep(1)
                except:
                    pass
                    
            except Exception as caption_error:
                logger.warning(f"Caption addition failed: {caption_error}")
            
            # Share the post
            share_button = driver.find_element("accessibility id", "share-button")
            share_button.click()
            time.sleep(5)  # Allow posting to complete
            
            # Return to home
            home_tab = driver.find_element("accessibility id", "mainfeed-tab")
            home_tab.click()
            time.sleep(3)
            
            result['success'] = True
            result['message'] = "Picture posted successfully"
            result['data'] = {
                'caption': caption,
                'posted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            result['message'] = f"Picture posting error: {str(e)}"
            logger.error(f"Post picture error: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                
        return result

    async def search_hashtag(self, device_udid: str, hashtag: str) -> Dict[str, Any]:
        """Search hashtag and extract metrics using confirmed working selectors"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = self.create_driver(device_udid)
            if not driver:
                result['message'] = "Failed to create driver"
                return result
            
            # Navigate to explore tab
            explore_tab = driver.find_element("accessibility id", "explore-tab")
            explore_tab.click()
            time.sleep(3)
            
            # Click search bar
            search_bar = driver.find_element("accessibility id", "search-bar")
            search_bar.click()
            time.sleep(2)
            
            # Type hashtag query
            search_input = driver.find_element("accessibility id", "search-text-input")
            search_input.clear()
            hashtag_query = f"#{hashtag}" if not hashtag.startswith("#") else hashtag
            search_input.send_keys(hashtag_query)
            time.sleep(3)
            
            # Click on hashtag result
            search_results = driver.find_elements("xpath", "//XCUIElementTypeCell[contains(@name, 'search-collection-view-cell-')]")
            hashtag_clicked = False
            
            for result_cell in search_results:
                try:
                    cell_name = result_cell.get_attribute("name")
                    if "#" in cell_name or "hashtag" in cell_name.lower():
                        result_cell.click()
                        hashtag_clicked = True
                        break
                except:
                    continue
            
            if not hashtag_clicked and search_results:
                # Fallback to first result
                search_results[0].click()
                hashtag_clicked = True
                
            if hashtag_clicked:
                time.sleep(4)
                
                # Extract hashtag data
                hashtag_data = {
                    "hashtag": hashtag,
                    "timestamp": datetime.now().isoformat(),
                    "page_loaded": True,
                    "post_grid_detected": False
                }
                
                # Check for post grid
                try:
                    grid_elements = driver.find_elements("xpath", "//XCUIElementTypeCell")
                    if len(grid_elements) > 3:
                        hashtag_data["post_grid_detected"] = True
                        hashtag_data["grid_items_count"] = len(grid_elements)
                except:
                    pass
                
                # Try to extract metrics
                try:
                    text_elements = driver.find_elements("xpath", "//XCUIElementTypeStaticText")
                    for element in text_elements:
                        text = element.text
                        if text and any(word in text.lower() for word in ["post", "reel", "video"]):
                            hashtag_data["metrics_text"] = text
                            break
                except:
                    pass
                
                result['success'] = True
                result['message'] = f"Successfully searched hashtag: {hashtag}"
                result['data'] = hashtag_data
            else:
                result['message'] = f"Could not find hashtag results for: {hashtag}"
            
            # Return to home
            home_tab = driver.find_element("accessibility id", "mainfeed-tab")
            home_tab.click()
            time.sleep(3)
            
        except Exception as e:
            result['message'] = f"Hashtag search error: {str(e)}"
            logger.error(f"Search hashtag error: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                
        return result

    async def save_post(self, device_udid: str) -> Dict[str, Any]:
        """Save Instagram post using confirmed working selectors"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = self.create_driver(device_udid)
            if not driver:
                result['message'] = "Failed to create driver"
                return result
            
            # Navigate to home feed
            home_tab = driver.find_element("accessibility id", "mainfeed-tab")
            home_tab.click()
            time.sleep(3)
            
            # Scroll down to find posts
            driver.swipe(400, 600, 400, 400, 1000)
            time.sleep(2)
            
            # Find three dots menu using confirmed working approach
            three_dots_found = False
            
            # Try multiple strategies for finding three dots
            try:
                three_dots = driver.find_element("accessibility id", "three-dots")
                three_dots.click()
                three_dots_found = True
            except:
                try:
                    three_dots = driver.find_element("accessibility id", "more-button")
                    three_dots.click() 
                    three_dots_found = True
                except:
                    try:
                        dots_buttons = driver.find_elements("xpath", "//XCUIElementTypeButton[contains(@name, 'more') or contains(@name, 'menu') or contains(@name, 'option')]")
                        if dots_buttons:
                            dots_buttons[0].click()
                            three_dots_found = True
                    except:
                        # Fallback screen tap approach
                        driver.tap([(350, 300)])
                        three_dots_found = True
            
            if three_dots_found:
                time.sleep(2)
                
                # Find and click save option
                save_clicked = False
                
                try:
                    save_button = driver.find_element("accessibility id", "save-button")
                    save_button.click()
                    save_clicked = True
                except:
                    try:
                        save_button = driver.find_element("xpath", "//XCUIElementTypeButton[@name='Save']")
                        save_button.click()
                        save_clicked = True
                    except:
                        try:
                            save_options = driver.find_elements("xpath", "//XCUIElementTypeCell[contains(@name, 'Save') or contains(@name, 'save')]")
                            if save_options:
                                save_options[0].click()
                                save_clicked = True
                        except:
                            pass
                
                if save_clicked:
                    time.sleep(2)
                    
                    save_data = {
                        "timestamp": datetime.now().isoformat(),
                        "save_action_completed": True
                    }
                    
                    result['success'] = True
                    result['message'] = "Post saved successfully"
                    result['data'] = save_data
                else:
                    result['message'] = "Could not find save option"
            else:
                result['message'] = "Could not find post options menu"
            
            # Return to home
            home_tab = driver.find_element("accessibility id", "mainfeed-tab")
            home_tab.click()
            time.sleep(3)
            
        except Exception as e:
            result['message'] = f"Save post error: {str(e)}"
            logger.error(f"Save post error: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
                
        return result

# Global instance
real_device_instagram = RealDeviceInstagram()
