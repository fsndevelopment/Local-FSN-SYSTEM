#!/usr/bin/env python3
"""
Simple SCAN_PROFILE Test - Standalone test without FSM dependencies
"""
from appium import webdriver
from appium.options.ios import XCUITestOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dataclasses import dataclass
import time
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProfileData:
    """Structured profile data"""
    username: str
    display_name: str = None
    bio: str = None
    followers_count: str = None
    following_count: str = None
    posts_count: str = None
    is_verified: bool = False
    is_private: bool = False
    profile_picture_present: bool = False
    scan_timestamp: str = ""
    success: bool = True
    error_message: str = None

def create_driver():
    """Create Appium driver"""
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.udid = "f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3"
    options.automation_name = "XCUITest"
    options.wda_local_port = 8108
    options.bundle_id = "com.burbn.instagram"
    options.wda_bundle_id = "com.devicex.wdx"
    options.no_reset = True
    
    return webdriver.Remote("http://localhost:4739", options=options)

def scan_own_profile(driver) -> ProfileData:
    """Scan own profile using profile tab"""
    logger.info("Scanning own profile via profile tab")
    
    profile_data = ProfileData(
        username="own_profile",
        scan_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    try:
        # Go to home first
        home_tab = driver.find_element(By.ACCESSIBILITY_ID, "mainfeed-tab")
        home_tab.click()
        time.sleep(1)
        
        # Click profile tab
        profile_tab = driver.find_element(By.ACCESSIBILITY_ID, "profile-tab")
        profile_tab.click()
        time.sleep(3)
        logger.info("Navigated to own profile")
        
        # Extract profile data
        return extract_profile_data(driver, profile_data)
        
    except Exception as e:
        profile_data.success = False
        profile_data.error_message = f"Navigation failed: {e}"
        return profile_data

def scan_target_profile(driver, username: str) -> ProfileData:
    """Scan target profile by searching"""
    logger.info(f"Scanning target profile: {username}")
    
    profile_data = ProfileData(
        username=username,
        scan_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    try:
        # Navigate to search
        search_tab = driver.find_element(By.ACCESSIBILITY_ID, "explore-tab")
        search_tab.click()
        time.sleep(2)
        
        # Check if we need to click search tab again
        try:
            driver.find_element(By.ACCESSIBILITY_ID, "search-text-input")
            logger.info("Search input found")
        except:
            logger.info("Clicking search tab again")
            search_tab.click()
            time.sleep(2)
        
        # Search for username
        search_field = driver.find_element(By.ACCESSIBILITY_ID, "search-text-input")
        search_field.click()
        search_field.clear()
        search_field.send_keys(username)
        time.sleep(3)
        
        # Click on search result
        try:
            search_result = driver.find_element(By.ACCESSIBILITY_ID, f"{username}, verified account")
            search_result.click()
            logger.info(f"Clicked verified account: {username}")
        except:
            search_results = driver.find_elements(By.XPATH, "//XCUIElementTypeCell[contains(@name, 'search-collection-view-cell-')]")
            if search_results:
                search_results[0].click()
                logger.info("Clicked first search result")
            else:
                raise Exception("No search results found")
        
        time.sleep(4)
        
        # Extract profile data
        return extract_profile_data(driver, profile_data)
        
    except Exception as e:
        profile_data.success = False
        profile_data.error_message = f"Navigation failed: {e}"
        return profile_data

def extract_profile_data(driver, profile_data: ProfileData) -> ProfileData:
    """Extract profile data from current profile page"""
    logger.info("Extracting profile data")
    
    try:
        # Extract username/display name
        try:
            # For own profile, look for specific username pattern
            if profile_data.username == "own_profile":
                try:
                    # Try specific selector for own profile username
                    username_element = driver.find_element(By.XPATH, "//XCUIElementTypeOther[@name='Jacqub Sf']")
                    profile_data.display_name = username_element.get_attribute("name")
                    logger.info(f"Own profile display name: {profile_data.display_name}")
                except:
                    # Fallback: look for Other elements with reasonable names
                    username_elements = driver.find_elements(By.XPATH, "//XCUIElementTypeOther[@name]")
                    for element in username_elements:
                        name = element.get_attribute("name")
                        if name and len(name) > 2 and name.lower() not in ['followers', 'following', 'posts', 'edit profile', 'message', 'follow', 'back', 'tagged', 'tab-bar-container']:
                            if not name.isdigit() and 'button' not in name.lower() and 'scroll' not in name.lower():
                                profile_data.display_name = name
                                logger.info(f"Display name: {name}")
                                break
            else:
                # For other profiles, use generic approach
                username_elements = driver.find_elements(By.XPATH, "//XCUIElementTypeOther[@name]")
                for element in username_elements:
                    name = element.get_attribute("name")
                    if name and len(name) > 2 and name.lower() not in ['followers', 'following', 'posts', 'edit profile', 'message', 'follow', 'back', 'tagged', 'tab-bar-container']:
                        if not name.isdigit() and 'button' not in name.lower() and 'scroll' not in name.lower():
                            profile_data.display_name = name
                            logger.info(f"Display name: {name}")
                            break
        except Exception as e:
            logger.warning(f"Could not extract display name: {e}")
        
        # Extract followers count - get actual count text
        try:
            followers_element = driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-followers")
            # Try to get the actual count text from child elements
            followers_texts = followers_element.find_elements(By.XPATH, ".//XCUIElementTypeStaticText")
            for text_element in followers_texts:
                text = text_element.get_attribute("name") or text_element.text
                if text and ('follower' in text.lower() or text.replace(',', '').replace('.', '').replace('K', '').replace('M', '').replace('B', '').isdigit()):
                    profile_data.followers_count = text
                    logger.info(f"Followers: {text}")
                    break
            
            # Fallback: get any text from the element
            if not profile_data.followers_count:
                profile_data.followers_count = followers_element.get_attribute("name") or followers_element.text or "followers_element_found"
        except Exception as e:
            logger.warning(f"Could not extract followers: {e}")
        
        # Extract following count
        try:
            following_element = driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-following-button")
            following_texts = following_element.find_elements(By.XPATH, ".//XCUIElementTypeStaticText")
            for text_element in following_texts:
                text = text_element.get_attribute("name") or text_element.text
                if text and ('following' in text.lower() or text.replace(',', '').replace('.', '').replace('K', '').replace('M', '').replace('B', '').isdigit()):
                    profile_data.following_count = text
                    logger.info(f"Following: {text}")
                    break
            
            if not profile_data.following_count:
                profile_data.following_count = following_element.get_attribute("name") or following_element.text or "following_element_found"
        except Exception as e:
            logger.warning(f"Could not extract following: {e}")
        
        # Extract posts count
        try:
            posts_element = driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-media-button")
            posts_texts = posts_element.find_elements(By.XPATH, ".//XCUIElementTypeStaticText")
            for text_element in posts_texts:
                text = text_element.get_attribute("name") or text_element.text
                if text and ('post' in text.lower() or text.replace(',', '').replace('.', '').replace('K', '').replace('M', '').replace('B', '').isdigit()):
                    profile_data.posts_count = text
                    logger.info(f"Posts: {text}")
                    break
            
            if not profile_data.posts_count:
                profile_data.posts_count = posts_element.get_attribute("name") or posts_element.text or "posts_element_found"
        except Exception as e:
            logger.warning(f"Could not extract posts: {e}")
        
        # Extract bio - look for StaticText elements (skip counts and common UI)
        try:
            # For own profile, try specific bio selector first
            if profile_data.username == "own_profile":
                try:
                    bio_element = driver.find_element(By.ACCESSIBILITY_ID, "Sss")
                    profile_data.bio = bio_element.get_attribute("name") or bio_element.text
                    logger.info(f"Own profile bio: {profile_data.bio}")
                except:
                    logger.info("Specific bio selector 'Sss' not found, trying generic approach")
            
            # If specific selector didn't work or it's not own profile, use generic approach
            if not profile_data.bio:
                bio_elements = driver.find_elements(By.XPATH, "//XCUIElementTypeStaticText")
                for element in bio_elements:
                    text = element.get_attribute("name") or element.text
                    if text and len(text) >= 1:  # Even single characters can be bio
                        # Skip common UI elements and extracted counts
                        skip_texts = ['followers', 'following', 'posts', 'edit profile', 'message', 'follow', 'back', 'tagged']
                        skip_texts.extend([profile_data.followers_count, profile_data.following_count, profile_data.posts_count, profile_data.display_name])
                        
                        # Skip usernames that start with @ or contain underscores (likely usernames, not bios)
                        if text.startswith('@') or '_' in text:
                            continue
                        
                        if text.lower() not in [s.lower() if s else '' for s in skip_texts]:
                            if not any(skip in text.lower() for skip in skip_texts if skip):
                                profile_data.bio = text
                                logger.info(f"Bio: {text[:30]}...")
                                break
        except Exception as e:
            logger.warning(f"Could not extract bio: {e}")
        
        # Check if account is private (requires scrolling)
        try:
            profile_data.is_private = check_private_status(driver)
        except Exception as e:
            logger.warning(f"Could not check private status: {e}")
        
        # Check verification status (only for target profiles, not own profile)
        try:
            if profile_data.username != "own_profile":
                profile_data.is_verified = check_verification_status(driver)
            else:
                # Can't check verification on own profile - Instagram doesn't allow it
                logger.info("Skipping verification check for own profile")
                profile_data.is_verified = False
        except Exception as e:
            logger.warning(f"Could not check verification: {e}")
        
        # Check profile picture
        try:
            profile_pics = driver.find_elements(By.XPATH, "//XCUIElementTypeButton[contains(@name, 'Profile picture')]")
            profile_data.profile_picture_present = len(profile_pics) > 0
            logger.info(f"Profile picture: {profile_data.profile_picture_present}")
        except:
            logger.warning("Could not check profile picture")
        
        return profile_data
        
    except Exception as e:
        profile_data.success = False
        profile_data.error_message = f"Data extraction failed: {e}"
        return profile_data

def check_private_status(driver) -> bool:
    """Check if account is private by scrolling down and looking for private text"""
    logger.info("Checking if account is private")
    
    try:
        # First check if "This account is private" text is already visible
        try:
            private_element = driver.find_element(By.ACCESSIBILITY_ID, "This account is private")
            logger.info("Account is private (text already visible)")
            return True
        except:
            pass
        
        # If not visible, scroll down to reveal private status
        try:
            # Get screen dimensions for scrolling
            screen_size = driver.get_window_size()
            screen_height = screen_size['height']
            screen_width = screen_size['width']
            
            # Scroll down from middle of screen
            start_y = screen_height * 0.6
            end_y = screen_height * 0.3
            x = screen_width * 0.5
            
            # Perform scroll
            driver.swipe(x, start_y, x, end_y, 1000)
            time.sleep(1)
            logger.info("Scrolled down to check for private status")
            
            # Now check for private text
            try:
                private_element = driver.find_element(By.ACCESSIBILITY_ID, "This account is private")
                logger.info("Account is private (found after scrolling)")
                
                # Scroll back up to restore original position
                driver.swipe(x, end_y, x, start_y, 1000)
                time.sleep(1)
                
                return True
            except:
                logger.info("Account is public (no private text found)")
                
                # Scroll back up anyway
                driver.swipe(x, end_y, x, start_y, 1000)
                time.sleep(1)
                
                return False
                
        except Exception as e:
            logger.warning(f"Could not scroll to check private status: {e}")
            return False
            
    except Exception as e:
        logger.warning(f"Private status check failed: {e}")
        return False

def check_verification_status(driver) -> bool:
    """Check verification by clicking username and looking for Verified text"""
    logger.info("Checking verification status")
    
    try:
        # Use the specific selector for the username button (avoiding back button)
        # Try to find the username button using the specific pattern you provided
        username_button = None
        
        try:
            # For Instagram profile specifically
            username_button = driver.find_element(By.XPATH, "(//XCUIElementTypeButton[@name='instagram'])[1]")
            logger.info("Found Instagram username button")
        except:
            try:
                # Generic approach - look for buttons with specific names, avoiding problematic elements
                buttons = driver.find_elements(By.XPATH, "//XCUIElementTypeButton[@name]")
                for button in buttons:
                    name = button.get_attribute("name")
                    if name and len(name) > 2:
                        # Skip back button, common UI elements, and problematic elements
                        skip_elements = [
                            'profile-back-button', 'back-button', 'followers', 'following', 
                            'posts', 'edit profile', 'message', 'follow', 'tagged', 'Tagged',
                            'Vertical scroll bar', 'scroll bar'
                        ]
                        if name not in skip_elements:
                            # Skip tab-bar elements and other UI
                            if 'tab' not in name.lower() and 'button' not in name.lower() and 'scroll' not in name.lower():
                                username_button = button
                                logger.info(f"Found potential username button: {name}")
                                break
            except Exception as e:
                logger.warning(f"Could not find username button: {e}")
        
        if not username_button:
            logger.warning("No username button found for verification check")
            return False
        
        # Double-check we're not clicking the back button
        button_name = username_button.get_attribute("name")
        if button_name == "profile-back-button":
            logger.warning("Avoiding back button click")
            return False
        
        # Click username button to open about page
        username_button.click()
        time.sleep(3)  # Give more time for about page to load
        logger.info(f"Clicked username button: {button_name}")
        
        # Look for "Verified" text on about page
        try:
            verified_element = driver.find_element(By.ACCESSIBILITY_ID, "Verified")
            logger.info("Account is verified!")
            
            # Close about page using the correct Back button
            try:
                # Use the specific Back button selector you provided
                back_button = driver.find_element(By.ACCESSIBILITY_ID, "Back")
                back_button.click()
                logger.info("Closed about page with Back button")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not close about page with Back button: {e}")
                # Fallback: try tapping outside
                try:
                    driver.tap([(50, 300)], 500)
                    logger.info("Closed about page with tap fallback")
                    time.sleep(2)
                except:
                    logger.warning("Could not close about page with tap either")
            
            return True
            
        except:
            logger.info("Account is not verified (no Verified text found)")
            
            # Close about page using the correct Back button
            try:
                back_button = driver.find_element(By.ACCESSIBILITY_ID, "Back")
                back_button.click()
                logger.info("Closed about page with Back button")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not close about page with Back button: {e}")
                # Fallback: try tapping outside
                try:
                    driver.tap([(50, 300)], 500)
                    logger.info("Closed about page with tap fallback")
                    time.sleep(2)
                except:
                    logger.warning("Could not close about page with tap either")
            
            return False
            
    except Exception as e:
        logger.warning(f"Verification check failed: {e}")
        
        # Try to recover by going back to home if we got lost
        try:
            home_tab = driver.find_element(By.ACCESSIBILITY_ID, "mainfeed-tab")
            home_tab.click()
            time.sleep(1)
            logger.info("Recovered by going to home")
        except:
            pass
            
        return False

def test_scan_profile():
    """Test profile scanning"""
    print("🧪 SIMPLE SCAN_PROFILE TEST")
    print("=" * 50)
    
    driver = create_driver()
    
    try:
        print("📱 Connected to Instagram")
        time.sleep(2)
        
        # TEST 1: Scan own profile
        print(f"\n{'='*30}")
        print("🧪 TEST 1: SCAN OWN PROFILE")
        print(f"{'='*30}")
        
        own_profile = scan_own_profile(driver)
        
        print(f"✅ Own Profile Results:")
        print(f"   📊 Success: {own_profile.success}")
        print(f"   👤 Username: {own_profile.username}")
        print(f"   📝 Bio: {own_profile.bio}")
        print(f"   👥 Followers: {own_profile.followers_count}")
        print(f"   👤 Following: {own_profile.following_count}")
        print(f"   📷 Posts: {own_profile.posts_count}")
        print(f"   ✅ Verified: {own_profile.is_verified}")
        print(f"   🖼️  Profile Pic: {own_profile.profile_picture_present}")
        
        if not own_profile.success:
            print(f"   ❌ Error: {own_profile.error_message}")
        
        # TEST 2: Scan Instagram profile
        print(f"\n{'='*30}")
        print("🧪 TEST 2: SCAN INSTAGRAM PROFILE")
        print(f"{'='*30}")
        
        instagram_profile = scan_target_profile(driver, "instagram")
        
        print(f"✅ Instagram Profile Results:")
        print(f"   📊 Success: {instagram_profile.success}")
        print(f"   👤 Username: {instagram_profile.username}")
        print(f"   📝 Bio: {instagram_profile.bio}")
        print(f"   👥 Followers: {instagram_profile.followers_count}")
        print(f"   👤 Following: {instagram_profile.following_count}")
        print(f"   📷 Posts: {instagram_profile.posts_count}")
        print(f"   ✅ Verified: {instagram_profile.is_verified}")
        print(f"   🖼️  Profile Pic: {instagram_profile.profile_picture_present}")
        
        if not instagram_profile.success:
            print(f"   ❌ Error: {instagram_profile.error_message}")
        
        # Clean up
        try:
            home_tab = driver.find_element(By.ACCESSIBILITY_ID, "mainfeed-tab")
            home_tab.click()
            time.sleep(1)
            print("🧹 Returned to home screen")
        except:
            pass
        
        # Calculate success
        tests_passed = sum([own_profile.success, instagram_profile.success])
        success_rate = (tests_passed / 2) * 100
        
        print(f"\n{'='*50}")
        print(f"🎯 SCAN_PROFILE TEST RESULTS")
        print(f"{'='*50}")
        print(f"📊 Success Rate: {success_rate:.1f}% ({tests_passed}/2)")
        
        return success_rate >= 50  # At least one test should pass
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        try:
            driver.quit()
            print("📱 Disconnected from iPhone")
        except:
            pass

if __name__ == "__main__":
    success = test_scan_profile()
    print(f"\n🏁 RESULT: {'SUCCESS' if success else 'NEEDS WORK'}")
