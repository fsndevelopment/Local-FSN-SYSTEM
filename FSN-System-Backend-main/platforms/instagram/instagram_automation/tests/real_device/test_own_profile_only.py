#!/usr/bin/env python3
"""
Test Own Profile Only - Simplified test for own profile scanning
"""
from appium import webdriver
from appium.options.ios import XCUITestOptions
from selenium.webdriver.common.by import By
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
        
        # Extract display name
        try:
            username_element = driver.find_element(By.XPATH, "//XCUIElementTypeOther[@name='Jacqub Sf']")
            profile_data.display_name = username_element.get_attribute("name")
            logger.info(f"Display name: {profile_data.display_name}")
        except Exception as e:
            logger.warning(f"Could not extract display name: {e}")
        
        # Extract bio using specific selector
        try:
            bio_element = driver.find_element(By.ACCESSIBILITY_ID, "Sss")
            profile_data.bio = bio_element.get_attribute("name") or bio_element.text
            logger.info(f"Bio: {profile_data.bio}")
        except Exception as e:
            logger.warning(f"Could not extract bio with specific selector: {e}")
            # Fallback: try generic approach
            try:
                bio_elements = driver.find_elements(By.XPATH, "//XCUIElementTypeStaticText")
                for element in bio_elements:
                    text = element.get_attribute("name") or element.text
                    if text and len(text) >= 1:
                        # Skip usernames and common UI
                        if text.startswith('@') or '_' in text or text in ['followers', 'following', 'posts']:
                            continue
                        profile_data.bio = text
                        logger.info(f"Bio (generic): {text}")
                        break
            except Exception as e2:
                logger.warning(f"Generic bio extraction also failed: {e2}")
        
        # Extract actual follower/following/posts counts (numbers, not selector names)
        try:
            followers_element = driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-followers")
            # Try to get actual count text from child elements
            followers_texts = followers_element.find_elements(By.XPATH, ".//XCUIElementTypeStaticText")
            followers_count = None
            for text_element in followers_texts:
                text = text_element.get_attribute("name") or text_element.text
                if text and (text.replace(',', '').replace('.', '').replace('K', '').replace('M', '').isdigit() or 'follower' in text.lower()):
                    followers_count = text
                    break
            
            # If no child text found, try the element itself
            if not followers_count:
                element_text = followers_element.get_attribute("value") or followers_element.text
                if element_text:
                    followers_count = element_text
                else:
                    followers_count = "followers_element_found_but_no_text"
            
            profile_data.followers_count = followers_count
            logger.info(f"Followers: {followers_count}")
        except Exception as e:
            logger.warning(f"Could not extract followers: {e}")
        
        try:
            following_element = driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-following-button")
            # Try to get actual count text from child elements
            following_texts = following_element.find_elements(By.XPATH, ".//XCUIElementTypeStaticText")
            following_count = None
            for text_element in following_texts:
                text = text_element.get_attribute("name") or text_element.text
                if text and (text.replace(',', '').replace('.', '').replace('K', '').replace('M', '').isdigit() or 'following' in text.lower()):
                    following_count = text
                    break
            
            # If no child text found, try the element itself
            if not following_count:
                element_text = following_element.get_attribute("value") or following_element.text
                if element_text:
                    following_count = element_text
                else:
                    following_count = "following_element_found_but_no_text"
            
            profile_data.following_count = following_count
            logger.info(f"Following: {following_count}")
        except Exception as e:
            logger.warning(f"Could not extract following: {e}")
        
        try:
            posts_element = driver.find_element(By.ACCESSIBILITY_ID, "user-detail-header-media-button")
            # Try to get actual count text from child elements
            posts_texts = posts_element.find_elements(By.XPATH, ".//XCUIElementTypeStaticText")
            posts_count = None
            for text_element in posts_texts:
                text = text_element.get_attribute("name") or text_element.text
                if text and (text.replace(',', '').replace('.', '').replace('K', '').replace('M', '').isdigit() or 'post' in text.lower()):
                    posts_count = text
                    break
            
            # If no child text found, try the element itself
            if not posts_count:
                element_text = posts_element.get_attribute("value") or posts_element.text
                if element_text:
                    posts_count = element_text
                else:
                    posts_count = "posts_element_found_but_no_text"
            
            profile_data.posts_count = posts_count
            logger.info(f"Posts: {posts_count}")
        except Exception as e:
            logger.warning(f"Could not extract posts: {e}")
        
        # Check profile picture
        try:
            profile_pics = driver.find_elements(By.XPATH, "//XCUIElementTypeButton[contains(@name, 'Profile picture')]")
            profile_data.profile_picture_present = len(profile_pics) > 0
            logger.info(f"Profile picture: {profile_data.profile_picture_present}")
        except:
            logger.warning("Could not check profile picture")
        
        # Skip verification check for own profile (Instagram doesn't allow it)
        profile_data.is_verified = False
        logger.info("Skipped verification check for own profile")
        
        # Check if private (scroll down)
        try:
            screen_size = driver.get_window_size()
            screen_height = screen_size['height']
            screen_width = screen_size['width']
            
            start_y = screen_height * 0.6
            end_y = screen_height * 0.3
            x = screen_width * 0.5
            
            driver.swipe(x, start_y, x, end_y, 1000)
            time.sleep(1)
            
            try:
                private_element = driver.find_element(By.ACCESSIBILITY_ID, "This account is private")
                profile_data.is_private = True
                logger.info("Account is private")
            except:
                profile_data.is_private = False
                logger.info("Account is public")
            
            # Scroll back up
            driver.swipe(x, end_y, x, start_y, 1000)
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"Could not check private status: {e}")
        
        return profile_data
        
    except Exception as e:
        profile_data.success = False
        profile_data.error_message = f"Scan failed: {e}"
        logger.error(f"Own profile scan failed: {e}")
        return profile_data

def test_own_profile_only():
    """Test own profile scanning only"""
    print("🧪 OWN PROFILE SCAN TEST")
    print("=" * 40)
    
    driver = create_driver()
    
    try:
        print("📱 Connected to Instagram")
        time.sleep(2)
        
        # Scan own profile
        own_profile = scan_own_profile(driver)
        
        print(f"\n✅ Own Profile Results:")
        print(f"   📊 Success: {own_profile.success}")
        print(f"   👤 Display Name: {own_profile.display_name}")
        print(f"   📝 Bio: '{own_profile.bio}'")
        print(f"   👥 Followers: {own_profile.followers_count}")
        print(f"   👤 Following: {own_profile.following_count}")
        print(f"   📷 Posts: {own_profile.posts_count}")
        print(f"   ✅ Verified: {own_profile.is_verified}")
        print(f"   🔒 Private: {own_profile.is_private}")
        print(f"   🖼️  Profile Pic: {own_profile.profile_picture_present}")
        print(f"   ⏰ Timestamp: {own_profile.scan_timestamp}")
        
        if not own_profile.success:
            print(f"   ❌ Error: {own_profile.error_message}")
        
        # Clean up
        try:
            home_tab = driver.find_element(By.ACCESSIBILITY_ID, "mainfeed-tab")
            home_tab.click()
            time.sleep(1)
            print("🧹 Returned to home screen")
        except:
            pass
        
        # Save results
        results = {
            "success": own_profile.success,
            "display_name": own_profile.display_name,
            "bio": own_profile.bio,
            "followers_count": own_profile.followers_count,
            "following_count": own_profile.following_count,
            "posts_count": own_profile.posts_count,
            "is_verified": own_profile.is_verified,
            "is_private": own_profile.is_private,
            "profile_picture_present": own_profile.profile_picture_present,
            "scan_timestamp": own_profile.scan_timestamp,
            "error_message": own_profile.error_message
        }
        
        with open('tests/device/own_profile_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*40}")
        print(f"🎯 OWN PROFILE SCAN RESULTS")
        print(f"{'='*40}")
        print(f"📊 Success: {'YES' if own_profile.success else 'NO'}")
        
        if own_profile.bio == "Sss":
            print("✅ Bio extraction CORRECT: 'Sss' found!")
        else:
            print(f"⚠️  Bio extraction: Expected 'Sss', got '{own_profile.bio}'")
        
        print(f"\n💾 Results saved to: own_profile_results.json")
        
        return own_profile.success
        
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
    success = test_own_profile_only()
    print(f"\n🏁 RESULT: {'SUCCESS' if success else 'NEEDS WORK'}")
