"""
Instagram Automation Service - Handle Instagram-specific actions
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .appium_service import appium_service

logger = logging.getLogger(__name__)

class InstagramService:
    """Service for Instagram automation actions"""
    
    def __init__(self):
        self.app_package = "com.instagram.android"
        self.login_timeout = 30
        self.action_timeout = 15
        
    async def login(self, device_udid: str, username: str, password: str) -> Dict[str, Any]:
        """Login to Instagram on a device"""
        result = {
            'success': False,
            'message': '',
            'data': {}
        }
        
        try:
            # Ensure we have a session
            session_id = await appium_service.create_session(device_udid, self.app_package)
            if not session_id:
                result['message'] = "Failed to create device session"
                return result
                
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.login_timeout)
            
            # Launch Instagram app
            driver.activate_app(self.app_package)
            await asyncio.sleep(2)
            
            # Check if already logged in
            if await self._is_logged_in(driver):
                result['success'] = True
                result['message'] = "Already logged in"
                return result
            
            # Look for login screen elements
            try:
                # Try to find username field
                username_field = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//android.widget.EditText[@content-desc='Username']"))
                )
                
                # Clear and enter username
                username_field.clear()
                username_field.send_keys(username)
                await asyncio.sleep(1)
                
                # Find password field
                password_field = driver.find_element(By.XPATH, "//android.widget.EditText[@content-desc='Password']")
                password_field.clear()
                password_field.send_keys(password)
                await asyncio.sleep(1)
                
                # Find and click login button
                login_button = driver.find_element(By.XPATH, "//android.widget.Button[@content-desc='Log in']")
                login_button.click()
                
                # Wait for login to complete
                await asyncio.sleep(5)
                
                # Check if login was successful
                if await self._is_logged_in(driver):
                    result['success'] = True
                    result['message'] = "Login successful"
                    logger.info(f"Successfully logged into Instagram on device {device_udid}")
                else:
                    result['message'] = "Login failed - check credentials"
                    
            except TimeoutException:
                result['message'] = "Login screen not found - app may need manual setup"
            except NoSuchElementException as e:
                result['message'] = f"Login element not found: {str(e)}"
                
        except Exception as e:
            result['message'] = f"Login error: {str(e)}"
            logger.error(f"Instagram login error on device {device_udid}: {e}")
            
        return result
    
    async def like_post(self, device_udid: str, post_url: str = None) -> Dict[str, Any]:
        """Like a post on Instagram"""
        result = {
            'success': False,
            'message': '',
            'data': {}
        }
        
        try:
            if device_udid not in appium_service.active_sessions:
                result['message'] = "No active session for device"
                return result
                
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.action_timeout)
            
            # Ensure Instagram app is active
            driver.activate_app(self.app_package)
            await asyncio.sleep(2)
            
            # Navigate to home feed if no specific post URL
            if not post_url:
                home_tab = driver.find_element(By.XPATH, "//android.widget.FrameLayout[@content-desc='Home']")
                home_tab.click()
                await asyncio.sleep(2)
            
            # Look for like button (heart icon)
            try:
                # Try to find an unliked post (empty heart)
                like_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//android.widget.ImageView[@content-desc='Like']"))
                )
                
                like_button.click()
                await asyncio.sleep(1)
                
                result['success'] = True
                result['message'] = "Post liked successfully"
                logger.info(f"Liked post on device {device_udid}")
                
            except TimeoutException:
                result['message'] = "No likeable posts found"
            except NoSuchElementException:
                result['message'] = "Like button not found"
                
        except Exception as e:
            result['message'] = f"Like action error: {str(e)}"
            logger.error(f"Instagram like error on device {device_udid}: {e}")
            
        return result
    
    async def follow_user(self, device_udid: str, username: str = None) -> Dict[str, Any]:
        """Follow a user on Instagram"""
        result = {
            'success': False,
            'message': '',
            'data': {}
        }
        
        try:
            if device_udid not in appium_service.active_sessions:
                result['message'] = "No active session for device"
                return result
                
            driver = appium_service.active_sessions[device_udid]
            wait = WebDriverWait(driver, self.action_timeout)
            
            # Ensure Instagram app is active
            driver.activate_app(self.app_package)
            await asyncio.sleep(2)
            
            if username:
                # Navigate to specific user profile
                # This would require search functionality
                result['message'] = "Specific user following not implemented yet"
            else:
                # Follow suggested users or from current feed
                try:
                    # Look for follow button in suggested users or posts
                    follow_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//android.widget.Button[@text='Follow']"))
                    )
                    
                    follow_button.click()
                    await asyncio.sleep(1)
                    
                    result['success'] = True
                    result['message'] = "User followed successfully"
                    logger.info(f"Followed user on device {device_udid}")
                    
                except TimeoutException:
                    result['message'] = "No follow buttons found"
                except NoSuchElementException:
                    result['message'] = "Follow button not found"
                    
        except Exception as e:
            result['message'] = f"Follow action error: {str(e)}"
            logger.error(f"Instagram follow error on device {device_udid}: {e}")
            
        return result
    
    async def view_stories(self, device_udid: str, count: int = 3) -> Dict[str, Any]:
        """View Instagram stories"""
        result = {
            'success': False,
            'message': '',
            'data': {'viewed_count': 0}
        }
        
        try:
            if device_udid not in appium_service.active_sessions:
                result['message'] = "No active session for device"
                return result
                
            driver = appium_service.active_sessions[device_udid]
            
            # Ensure Instagram app is active
            driver.activate_app(self.app_package)
            await asyncio.sleep(2)
            
            # Navigate to home to see stories
            home_tab = driver.find_element(By.XPATH, "//android.widget.FrameLayout[@content-desc='Home']")
            home_tab.click()
            await asyncio.sleep(2)
            
            viewed = 0
            for i in range(count):
                try:
                    # Look for story circles at the top
                    story_circle = driver.find_element(By.XPATH, "//androidx.recyclerview.widget.RecyclerView//android.widget.ImageView")
                    story_circle.click()
                    await asyncio.sleep(3)  # Let story play
                    
                    # Tap to next story or exit
                    driver.tap([(500, 300)])  # Tap center to advance
                    await asyncio.sleep(2)
                    
                    viewed += 1
                    
                except NoSuchElementException:
                    break
                    
            result['success'] = True
            result['message'] = f"Viewed {viewed} stories"
            result['data']['viewed_count'] = viewed
            
        except Exception as e:
            result['message'] = f"Story viewing error: {str(e)}"
            logger.error(f"Instagram story error on device {device_udid}: {e}")
            
        return result
    
    async def _is_logged_in(self, driver) -> bool:
        """Check if user is logged into Instagram"""
        try:
            # Look for elements that indicate we're logged in
            # This could be the home tab, profile icon, etc.
            home_indicator = driver.find_element(By.XPATH, "//android.widget.FrameLayout[@content-desc='Home']")
            return home_indicator is not None
        except NoSuchElementException:
            return False
        except Exception:
            return False
    
    async def get_account_info(self, device_udid: str) -> Dict[str, Any]:
        """Get current account information"""
        result = {
            'success': False,
            'message': '',
            'data': {}
        }
        
        try:
            if device_udid not in appium_service.active_sessions:
                result['message'] = "No active session for device"
                return result
                
            driver = appium_service.active_sessions[device_udid]
            
            # First, try to launch Instagram app
            try:
                driver.activate_app("com.burbn.instagram")
                await asyncio.sleep(3)
                result['success'] = True
                result['message'] = "Instagram app launched successfully"
                result['data'] = {
                    'app_launched': True,
                    'ready_for_automation': True
                }
                logger.info(f"Instagram app launched on device {device_udid}")
                
            except Exception as app_error:
                # If Instagram isn't installed, try to check what apps are available
                try:
                    # Get current app info
                    current_bundle = driver.current_app
                    result['message'] = f"Instagram not found. Current app: {current_bundle}"
                    result['data'] = {
                        'current_app': current_bundle,
                        'instagram_installed': False
                    }
                except Exception as bundle_error:
                    result['message'] = f"Could not launch Instagram: {str(app_error)}"
                    result['data'] = {
                        'error': str(app_error),
                        'suggestion': "Install Instagram app on the device"
                    }
                
        except Exception as e:
            result['message'] = f"Profile info error: {str(e)}"
            logger.error(f"Instagram profile info error on device {device_udid}: {e}")
            
        return result


# Global instance
instagram_service = InstagramService()
