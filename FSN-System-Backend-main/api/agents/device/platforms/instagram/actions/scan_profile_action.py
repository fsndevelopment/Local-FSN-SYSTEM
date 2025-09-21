#!/usr/bin/env python3
"""
Instagram SCAN_PROFILE Action - Extract comprehensive profile data
"""
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProfileData:
    """Structured profile data"""
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers_count: Optional[str] = None
    following_count: Optional[str] = None
    posts_count: Optional[str] = None
    is_verified: bool = False
    is_private: bool = False
    profile_picture_present: bool = False
    scan_timestamp: str = ""
    success: bool = True
    error_message: Optional[str] = None

class IGScanProfileAction:
    """Instagram Profile Scanning Action with comprehensive data extraction"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
    def execute(self, target_username: str = None, use_own_profile: bool = False) -> ProfileData:
        """
        Execute profile scanning action
        
        Args:
            target_username: Username to scan (if None and use_own_profile=True, scans own profile)
            use_own_profile: If True, navigates to own profile tab instead of searching
            
        Returns:
            ProfileData: Comprehensive profile information
        """
        logger.info(f"Starting profile scan - target: {target_username}, own_profile: {use_own_profile}")
        
        try:
            # Step 1: Navigate to profile
            if use_own_profile:
                profile_data = self._scan_own_profile()
            else:
                if not target_username:
                    return ProfileData(
                        username="", 
                        success=False, 
                        error_message="Username required when not scanning own profile"
                    )
                profile_data = self._scan_target_profile(target_username)
            
            logger.info(f"Profile scan completed successfully: {profile_data.username}")
            return profile_data
            
        except Exception as e:
            error_msg = f"Profile scan failed: {str(e)}"
            logger.error(error_msg)
            return ProfileData(
                username=target_username or "unknown",
                success=False,
                error_message=error_msg
            )
    
    def _scan_own_profile(self) -> ProfileData:
        """Scan own profile using profile tab"""
        logger.info("Scanning own profile via profile tab")
        
        # Navigate to own profile
        try:
            # Go to home first
            home_tab = self.driver.find_element(By.ACCESSIBILITY_ID, "mainfeed-tab")
            home_tab.click()
            time.sleep(1)
            
            # Click profile tab
            profile_tab = self.driver.find_element(By.ACCESSIBILITY_ID, "profile-tab")
            profile_tab.click()
            time.sleep(3)
            logger.info("Navigated to own profile")
            
        except Exception as e:
            raise Exception(f"Failed to navigate to own profile: {e}")
        
        # Extract profile data
        return self._extract_profile_data()
    
    def _scan_target_profile(self, username: str) -> ProfileData:
        """Scan target profile by searching for username"""
        logger.info(f"Scanning target profile: {username}")
        
        try:
            # Navigate to search
            search_tab = self.driver.find_element(By.ACCESSIBILITY_ID, "explore-tab")
            search_tab.click()
            time.sleep(2)
            
            # Check if we need to click search tab again (Instagram state memory)
            try:
                self.driver.find_element(By.ACCESSIBILITY_ID, "search-text-input")
                logger.info("Search input found - on search page")
            except:
                logger.info("Search input not found - clicking search tab again")
                search_tab.click()
                time.sleep(2)
            
            # Search for username
            search_field = self.driver.find_element(By.ACCESSIBILITY_ID, "search-text-input")
            search_field.click()
            search_field.clear()
            search_field.send_keys(username)
            time.sleep(3)
            logger.info(f"Searched for username: {username}")
            
            # Click on search result (first result)
            try:
                # Try to find specific username result
                search_result = self.driver.find_element(By.ACCESSIBILITY_ID, f"{username}, verified account")
                search_result.click()
                logger.info(f"Clicked on verified account: {username}")
            except:
                try:
                    # Try generic search result pattern
                    search_results = self.driver.find_elements(By.XPATH, "//XCUIElementTypeCell[contains(@name, 'search-collection-view-cell-')]")
                    if search_results:
                        search_results[0].click()
                        logger.info("Clicked on first search result")
                    else:
                        raise Exception("No search results found")
                except Exception as e:
                    raise Exception(f"Failed to click search result: {e}")
            
            time.sleep(4)  # Wait for profile to load
            
        except Exception as e:
            raise Exception(f"Failed to navigate to target profile: {e}")
        
        # Extract profile data
        return self._extract_profile_data(username)
    
    def _extract_profile_data(self, expected_username: str = None) -> ProfileData:
        """Extract comprehensive profile data from current profile page"""
        logger.info("Extracting profile data from current page")
        
        profile_data = ProfileData(
            username=expected_username or "unknown",
            scan_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        try:
            # Extract followers count
            try:
                followers_element = self.driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-followers")
                profile_data.followers_count = followers_element.get_attribute("name") or followers_element.text
                logger.info(f"Extracted followers: {profile_data.followers_count}")
            except Exception as e:
                logger.warning(f"Could not extract followers count: {e}")
            
            # Extract following count
            try:
                following_element = self.driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-following-button")
                profile_data.following_count = following_element.get_attribute("name") or following_element.text
                logger.info(f"Extracted following: {profile_data.following_count}")
            except Exception as e:
                logger.warning(f"Could not extract following count: {e}")
            
            # Extract posts count
            try:
                posts_element = self.driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-media-button")
                profile_data.posts_count = posts_element.get_attribute("name") or posts_element.text
                logger.info(f"Extracted posts: {profile_data.posts_count}")
            except Exception as e:
                logger.warning(f"Could not extract posts count: {e}")
            
            # Extract bio (using generic approach since bio text varies)
            try:
                # Try to find bio text elements - look for StaticText elements in bio area
                bio_elements = self.driver.find_elements(By.XPATH, "//XCUIElementTypeStaticText")
                
                # Filter bio elements (typically appear after username and before stats)
                potential_bio = []
                for element in bio_elements:
                    text = element.get_attribute("name") or element.text
                    if text and len(text) > 3 and text not in [profile_data.followers_count, profile_data.following_count, profile_data.posts_count]:
                        # Skip common UI elements
                        if text.lower() not in ['followers', 'following', 'posts', 'edit profile', 'message', 'follow']:
                            potential_bio.append(text)
                
                if potential_bio:
                    # Take the first substantial text as bio
                    profile_data.bio = potential_bio[0]
                    logger.info(f"Extracted bio: {profile_data.bio[:50]}...")
                    
            except Exception as e:
                logger.warning(f"Could not extract bio: {e}")
            
            # Check verification status (requires clicking on username)
            try:
                profile_data.is_verified = self._check_verification_status()
            except Exception as e:
                logger.warning(f"Could not check verification status: {e}")
            
            # Check if profile picture is present
            try:
                profile_pic = self.driver.find_element(By.ACCESSIBILITY_ID, "instagram. Profile picture")
                profile_data.profile_picture_present = True
                logger.info("Profile picture detected")
            except:
                # Try generic profile picture selector
                try:
                    profile_pics = self.driver.find_elements(By.XPATH, "//XCUIElementTypeButton[contains(@name, 'Profile picture')]")
                    profile_data.profile_picture_present = len(profile_pics) > 0
                except:
                    logger.warning("Could not detect profile picture")
            
            logger.info("Profile data extraction completed")
            return profile_data
            
        except Exception as e:
            profile_data.success = False
            profile_data.error_message = f"Data extraction failed: {e}"
            logger.error(f"Profile data extraction failed: {e}")
            return profile_data
    
    def _check_verification_status(self) -> bool:
        """Check if account is verified by clicking on username and checking about page"""
        logger.info("Checking verification status")
        
        try:
            # Find and click on username to open about page
            username_buttons = self.driver.find_elements(By.XPATH, "//XCUIElementTypeButton[contains(@name, 'instagram')]")
            if not username_buttons:
                logger.warning("No username button found for verification check")
                return False
            
            # Click the first username button
            username_buttons[0].click()
            time.sleep(2)
            logger.info("Clicked username to open about page")
            
            # Look for "Verified" text on about page
            try:
                verified_element = self.driver.find_element(By.ACCESSIBILITY_ID, "Verified")
                logger.info("Verified badge found - account is verified")
                
                # Close the about page (click back or outside)
                try:
                    # Try to find and click back button or close
                    back_buttons = self.driver.find_elements(By.ACCESSIBILITY_ID, "back-button")
                    if back_buttons:
                        back_buttons[0].click()
                    else:
                        # Tap outside to close
                        self.driver.tap([(100, 300)], 500)
                    time.sleep(1)
                    logger.info("Closed about page")
                except:
                    logger.warning("Could not close about page")
                
                return True
                
            except:
                logger.info("No verified badge found - account is not verified")
                
                # Close the about page
                try:
                    back_buttons = self.driver.find_elements(By.ACCESSIBILITY_ID, "back-button")
                    if back_buttons:
                        back_buttons[0].click()
                    else:
                        self.driver.tap([(100, 300)], 500)
                    time.sleep(1)
                except:
                    pass
                
                return False
                
        except Exception as e:
            logger.warning(f"Verification check failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up and return to home screen"""
        try:
            home_tab = self.driver.find_element(By.ACCESSIBILITY_ID, "mainfeed-tab")
            home_tab.click()
            time.sleep(1)
            logger.info("Returned to home screen")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
