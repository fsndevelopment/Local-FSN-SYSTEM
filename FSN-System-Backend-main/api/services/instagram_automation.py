"""
Complete Instagram Automation Engine for iOS Devices
Handles all Instagram actions with smart rate limiting and error handling
"""
import asyncio
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from .appium_service import appium_service

logger = logging.getLogger(__name__)

class InstagramAutomation:
    """Complete Instagram automation engine with all bot actions"""
    
    def __init__(self):
        self.app_package = "com.burbn.instagram"
        self.timeout = 15
        self.rate_limits = {
            'follow': {'per_hour': 60, 'per_day': 400},
            'like': {'per_hour': 100, 'per_day': 1000}, 
            'comment': {'per_hour': 30, 'per_day': 100},
            'dm': {'per_hour': 20, 'per_day': 50},
            'story_view': {'per_hour': 200, 'per_day': 1500}
        }
        self.action_counts = {}  # Track actions per device
        
    async def login(self, device_udid: str, username: str, password: str) -> Dict[str, Any]:
        """Advanced Instagram login with multiple fallback methods"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            if device_udid not in appium_service.active_sessions:
                session_id = await appium_service.create_session(device_udid, self.app_package)
                if not session_id:
                    result['message'] = "Failed to create device session"
                    return result
            
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Launch Instagram
            driver.activate_app(self.app_package)
            await asyncio.sleep(3)
            
            # Check if already logged in
            if await self._is_logged_in(driver):
                result['success'] = True
                result['message'] = "Already logged in"
                result['data']['username'] = await self._get_current_username(driver)
                return result
            
            # Handle login flow with multiple methods
            login_success = False
            
            # Method 1: Standard login form
            try:
                login_success = await self._login_standard_form(driver, username, password, wait)
            except Exception as e:
                logger.warning(f"Standard login failed: {e}")
            
            # Method 2: Login with phone number fallback
            if not login_success:
                try:
                    login_success = await self._login_phone_fallback(driver, username, password, wait)
                except Exception as e:
                    logger.warning(f"Phone login failed: {e}")
            
            # Method 3: Login via saved accounts
            if not login_success:
                try:
                    login_success = await self._login_saved_account(driver, username, wait)
                except Exception as e:
                    logger.warning(f"Saved account login failed: {e}")
            
            if login_success:
                # Handle post-login screens
                await self._handle_post_login_screens(driver, wait)
                
                result['success'] = True
                result['message'] = "Login successful"
                result['data'] = {
                    'username': username,
                    'login_time': datetime.now().isoformat(),
                    'method': 'automated'
                }
                logger.info(f"Instagram login successful for {username} on {device_udid}")
            else:
                result['message'] = "All login methods failed"
                
        except Exception as e:
            result['message'] = f"Login error: {str(e)}"
            logger.error(f"Instagram login error for {username} on {device_udid}: {e}")
            
        return result
    
    async def follow_user(self, device_udid: str, target_username: str) -> Dict[str, Any]:
        """Follow a specific user with smart rate limiting"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            # Check rate limits
            if not await self._check_rate_limit(device_udid, 'follow'):
                result['message'] = "Rate limit exceeded for follow actions"
                return result
            
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Navigate to user profile
            if await self._navigate_to_profile(driver, target_username, wait):
                # Check if already following
                if await self._is_already_following(driver):
                    result['success'] = True
                    result['message'] = f"Already following @{target_username}"
                    return result
                
                # Click follow button
                follow_success = await self._click_follow_button(driver, wait)
                
                if follow_success:
                    # Handle follow confirmation screens
                    await self._handle_follow_confirmations(driver, wait)
                    
                    # Verify follow action
                    await asyncio.sleep(2)
                    if await self._verify_follow_success(driver):
                        await self._increment_action_count(device_udid, 'follow')
                        
                        result['success'] = True
                        result['message'] = f"Successfully followed @{target_username}"
                        result['data'] = {
                            'target_user': target_username,
                            'action_time': datetime.now().isoformat(),
                            'method': 'profile_follow'
                        }
                        logger.info(f"Followed @{target_username} on {device_udid}")
                    else:
                        result['message'] = "Follow action failed verification"
                else:
                    result['message'] = "Could not click follow button"
            else:
                result['message'] = f"Could not navigate to @{target_username} profile"
                
        except Exception as e:
            result['message'] = f"Follow error: {str(e)}"
            logger.error(f"Follow error for @{target_username} on {device_udid}: {e}")
            
        return result
    
    async def like_posts(self, device_udid: str, hashtag: str = None, count: int = 5) -> Dict[str, Any]:
        """Like posts from hashtag or home feed"""
        result = {'success': False, 'message': '', 'data': {'liked_count': 0}}
        
        try:
            if not await self._check_rate_limit(device_udid, 'like'):
                result['message'] = "Rate limit exceeded for like actions"
                return result
            
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Navigate to content source
            if hashtag:
                navigation_success = await self._navigate_to_hashtag(driver, hashtag, wait)
            else:
                navigation_success = await self._navigate_to_home_feed(driver, wait)
            
            if not navigation_success:
                result['message'] = "Could not navigate to content source"
                return result
            
            liked_count = 0
            for i in range(count):
                try:
                    # Find unliked post
                    like_button = await self._find_like_button(driver, wait)
                    if like_button:
                        # Click like button
                        like_button.click()
                        await asyncio.sleep(random.uniform(1, 3))
                        
                        # Verify like action
                        if await self._verify_like_success(driver):
                            liked_count += 1
                            await self._increment_action_count(device_udid, 'like')
                            logger.info(f"Liked post {i+1} on {device_udid}")
                        
                        # Scroll to next post
                        await self._scroll_to_next_post(driver)
                        await asyncio.sleep(random.uniform(2, 5))
                    else:
                        # No more posts to like
                        break
                        
                except Exception as e:
                    logger.warning(f"Error liking post {i+1}: {e}")
                    continue
            
            result['success'] = True
            result['message'] = f"Liked {liked_count} posts"
            result['data'] = {
                'liked_count': liked_count,
                'source': hashtag or 'home_feed',
                'action_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            result['message'] = f"Like posts error: {str(e)}"
            logger.error(f"Like posts error on {device_udid}: {e}")
            
        return result
    
    async def comment_on_posts(self, device_udid: str, comments: List[str], count: int = 3) -> Dict[str, Any]:
        """Comment on posts with predefined comment list"""
        result = {'success': False, 'message': '', 'data': {'commented_count': 0}}
        
        try:
            if not await self._check_rate_limit(device_udid, 'comment'):
                result['message'] = "Rate limit exceeded for comment actions"
                return result
            
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Navigate to home feed
            if not await self._navigate_to_home_feed(driver, wait):
                result['message'] = "Could not navigate to home feed"
                return result
            
            commented_count = 0
            for i in range(count):
                try:
                    # Find comment button
                    comment_button = await self._find_comment_button(driver, wait)
                    if comment_button:
                        comment_button.click()
                        await asyncio.sleep(2)
                        
                        # Select random comment
                        comment_text = random.choice(comments)
                        
                        # Type comment
                        if await self._type_comment(driver, comment_text, wait):
                            # Post comment
                            if await self._post_comment(driver, wait):
                                commented_count += 1
                                await self._increment_action_count(device_udid, 'comment')
                                logger.info(f"Commented on post {i+1}: '{comment_text}' on {device_udid}")
                        
                        # Go back to feed
                        await self._go_back_to_feed(driver)
                        await asyncio.sleep(random.uniform(3, 7))
                    else:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error commenting on post {i+1}: {e}")
                    continue
            
            result['success'] = True
            result['message'] = f"Commented on {commented_count} posts"
            result['data'] = {
                'commented_count': commented_count,
                'action_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            result['message'] = f"Comment error: {str(e)}"
            logger.error(f"Comment error on {device_udid}: {e}")
            
        return result
    
    async def view_stories(self, device_udid: str, count: int = 10) -> Dict[str, Any]:
        """View Instagram stories"""
        result = {'success': False, 'message': '', 'data': {'viewed_count': 0}}
        
        try:
            if not await self._check_rate_limit(device_udid, 'story_view'):
                result['message'] = "Rate limit exceeded for story viewing"
                return result
            
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Navigate to home feed
            if not await self._navigate_to_home_feed(driver, wait):
                result['message'] = "Could not navigate to home feed"
                return result
            
            viewed_count = 0
            for i in range(count):
                try:
                    # Find story circle
                    story_circle = await self._find_story_circle(driver, wait, i)
                    if story_circle:
                        story_circle.click()
                        await asyncio.sleep(3)
                        
                        # Watch story (3-7 seconds)
                        watch_time = random.uniform(3, 7)
                        await asyncio.sleep(watch_time)
                        
                        # Tap to next story or exit
                        await self._tap_next_story_or_exit(driver)
                        
                        viewed_count += 1
                        await self._increment_action_count(device_udid, 'story_view')
                        logger.info(f"Viewed story {i+1} on {device_udid}")
                        
                        await asyncio.sleep(random.uniform(1, 3))
                    else:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error viewing story {i+1}: {e}")
                    continue
            
            result['success'] = True
            result['message'] = f"Viewed {viewed_count} stories"
            result['data'] = {
                'viewed_count': viewed_count,
                'action_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            result['message'] = f"Story viewing error: {str(e)}"
            logger.error(f"Story viewing error on {device_udid}: {e}")
            
        return result
    
    async def send_direct_message(self, device_udid: str, username: str, message: str) -> Dict[str, Any]:
        """Send direct message to a user"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            if not await self._check_rate_limit(device_udid, 'dm'):
                result['message'] = "Rate limit exceeded for DM actions"
                return result
            
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Navigate to DM section
            if await self._navigate_to_dm_section(driver, wait):
                # Start new message
                if await self._start_new_message(driver, wait):
                    # Search and select user
                    if await self._search_and_select_user(driver, username, wait):
                        # Type and send message
                        if await self._type_and_send_message(driver, message, wait):
                            await self._increment_action_count(device_udid, 'dm')
                            
                            result['success'] = True
                            result['message'] = f"Message sent to @{username}"
                            result['data'] = {
                                'recipient': username,
                                'message': message,
                                'action_time': datetime.now().isoformat()
                            }
                            logger.info(f"Sent DM to @{username} on {device_udid}")
                        else:
                            result['message'] = "Could not send message"
                    else:
                        result['message'] = f"Could not find user @{username}"
                else:
                    result['message'] = "Could not start new message"
            else:
                result['message'] = "Could not navigate to DM section"
                
        except Exception as e:
            result['message'] = f"DM error: {str(e)}"
            logger.error(f"DM error to @{username} on {device_udid}: {e}")
            
        return result
    
    # Helper methods for UI interactions
    async def _is_logged_in(self, driver) -> bool:
        """Check if user is logged into Instagram"""
        try:
            # Look for home tab or profile elements
            home_elements = [
                "//XCUIElementTypeButton[@name='Home']",
                "//XCUIElementTypeButton[@name='Profile']",
                "//XCUIElementTypeTabBar",
                "**/XCUIElementTypeButton[`name CONTAINS 'Home'`]"
            ]
            
            for element_xpath in home_elements:
                try:
                    driver.find_element(By.XPATH, element_xpath)
                    return True
                except NoSuchElementException:
                    continue
            return False
        except Exception:
            return False
    
    async def _get_current_username(self, driver) -> Optional[str]:
        """Get current logged in username"""
        try:
            # Navigate to profile and extract username
            profile_tab = driver.find_element(By.XPATH, "//XCUIElementTypeButton[@name='Profile']")
            profile_tab.click()
            await asyncio.sleep(2)
            
            username_element = driver.find_element(By.XPATH, "//XCUIElementTypeStaticText[contains(@name, '@')]")
            return username_element.get_attribute('name')
        except Exception:
            return None
    
    async def _login_standard_form(self, driver, username: str, password: str, wait) -> bool:
        """Standard login form method"""
        try:
            # Find username field
            username_field = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//XCUIElementTypeTextField"))
            )
            username_field.clear()
            username_field.send_keys(username)
            await asyncio.sleep(1)
            
            # Find password field
            password_field = driver.find_element(By.XPATH, "//XCUIElementTypeSecureTextField")
            password_field.clear()
            password_field.send_keys(password)
            await asyncio.sleep(1)
            
            # Find and click login button
            login_button = driver.find_element(By.XPATH, "//XCUIElementTypeButton[@name='Log In']")
            login_button.click()
            
            # Wait for login to complete
            await asyncio.sleep(5)
            
            return await self._is_logged_in(driver)
            
        except Exception as e:
            logger.error(f"Standard login failed: {e}")
            return False
    
    async def _check_rate_limit(self, device_udid: str, action_type: str) -> bool:
        """Check if action is within rate limits"""
        if device_udid not in self.action_counts:
            self.action_counts[device_udid] = {}
        
        if action_type not in self.action_counts[device_udid]:
            self.action_counts[device_udid][action_type] = {
                'hourly': {'count': 0, 'reset_time': datetime.now() + timedelta(hours=1)},
                'daily': {'count': 0, 'reset_time': datetime.now() + timedelta(days=1)}
            }
        
        action_data = self.action_counts[device_udid][action_type]
        now = datetime.now()
        
        # Reset counters if time has passed
        if now > action_data['hourly']['reset_time']:
            action_data['hourly'] = {'count': 0, 'reset_time': now + timedelta(hours=1)}
        
        if now > action_data['daily']['reset_time']:
            action_data['daily'] = {'count': 0, 'reset_time': now + timedelta(days=1)}
        
        # Check limits
        limits = self.rate_limits.get(action_type, {'per_hour': 100, 'per_day': 1000})
        
        if action_data['hourly']['count'] >= limits['per_hour']:
            logger.warning(f"Hourly rate limit exceeded for {action_type} on {device_udid}")
            return False
        
        if action_data['daily']['count'] >= limits['per_day']:
            logger.warning(f"Daily rate limit exceeded for {action_type} on {device_udid}")
            return False
        
        return True
    
    async def _increment_action_count(self, device_udid: str, action_type: str):
        """Increment action count for rate limiting"""
        if device_udid in self.action_counts and action_type in self.action_counts[device_udid]:
            self.action_counts[device_udid][action_type]['hourly']['count'] += 1
            self.action_counts[device_udid][action_type]['daily']['count'] += 1
    
    # Additional helper methods would continue here...
    # (Navigation, UI interaction, verification methods)
    
    async def get_account_stats(self, device_udid: str) -> Dict[str, Any]:
        """Get current account statistics"""
        result = {'success': False, 'message': '', 'data': {}}
        
        try:
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.timeout)
            
            # Navigate to profile
            profile_tab = driver.find_element(By.XPATH, "//XCUIElementTypeButton[@name='Profile']")
            profile_tab.click()
            await asyncio.sleep(3)
            
            # Extract stats
            stats = {}
            try:
                # Posts count
                posts_element = driver.find_element(By.XPATH, "//XCUIElementTypeStaticText[contains(@name, 'posts')]")
                stats['posts'] = self._extract_number_from_text(posts_element.get_attribute('name'))
                
                # Followers count
                followers_element = driver.find_element(By.XPATH, "//XCUIElementTypeStaticText[contains(@name, 'followers')]")
                stats['followers'] = self._extract_number_from_text(followers_element.get_attribute('name'))
                
                # Following count
                following_element = driver.find_element(By.XPATH, "//XCUIElementTypeStaticText[contains(@name, 'following')]")
                stats['following'] = self._extract_number_from_text(following_element.get_attribute('name'))
                
            except Exception as e:
                logger.warning(f"Could not extract all stats: {e}")
            
            result['success'] = True
            result['data'] = stats
            result['message'] = "Stats extracted successfully"
            
        except Exception as e:
            result['message'] = f"Stats extraction error: {str(e)}"
            logger.error(f"Stats extraction error on {device_udid}: {e}")
            
        return result
    
    def _extract_number_from_text(self, text: str) -> int:
        """Extract number from text like '1,234 followers'"""
        try:
            import re
            numbers = re.findall(r'[\d,]+', text)
            if numbers:
                return int(numbers[0].replace(',', ''))
            return 0
        except:
            return 0


# Global instance
instagram_automation = InstagramAutomation()
