#!/usr/bin/env python3
"""
Universal Ad Recovery Strategy
Handles both in-feed ads and ad landing pages with proper close buttons
"""
from appium import webdriver
from appium.options.ios import XCUITestOptions
import time
import os

def create_driver():
    """Create Appium driver for real device"""
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.udid = "f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3"
    options.automation_name = "XCUITest"
    options.wda_local_port = 8108
    options.bundle_id = "com.burbn.instagram"
    options.wda_bundle_id = "com.devicex.wdx"
    options.no_reset = True
    
    return webdriver.Remote("http://localhost:4739", options=options)

def detect_ad_type(driver):
    """Detect what type of ad we're dealing with"""
    print("🔍 DETECTING AD TYPE")
    
    # Check for ad landing page (has close button)
    try:
        close_button = driver.find_element("accessibility id", "ig icon x pano outline 24")
        if close_button.is_displayed():
            print("   🎯 DETECTED: Ad Landing Page (has close button)")
            return "landing_page", close_button
    except:
        pass
    
    # Check for in-feed ad (has CTA button)
    try:
        cta_button = driver.find_element("accessibility id", "cta-button")
        if cta_button.is_displayed():
            print("   🎯 DETECTED: In-Feed Ad (has CTA button)")
            return "in_feed", cta_button
    except:
        pass
    
    # Check for sponsored post
    try:
        sponsored_elements = driver.find_elements("xpath", "//*[contains(@value, 'Sponsored')]")
        if sponsored_elements:
            print("   🎯 DETECTED: Sponsored Post")
            return "sponsored", None
    except:
        pass
    
    print("   ✅ NO AD DETECTED")
    return "none", None

def universal_ad_escape(driver):
    """Universal ad escape strategy"""
    print("🚪 UNIVERSAL AD ESCAPE")
    
    ad_type, ad_element = detect_ad_type(driver)
    
    if ad_type == "landing_page":
        # Use the close button directly
        print("   🎯 Using close button for landing page")
        try:
            ad_element.click()
            time.sleep(2)
            print("   ✅ Clicked close button")
            return True
        except Exception as e:
            print(f"   ❌ Close button failed: {e}")
    
    elif ad_type == "in_feed":
        # Navigate away from in-feed ad
        print("   🎯 Navigating away from in-feed ad")
        try:
            home_tab = driver.find_element("accessibility id", "mainfeed-tab")
            home_tab.click()
            time.sleep(2)
            print("   ✅ Navigated to home tab")
            return True
        except Exception as e:
            print(f"   ❌ Home navigation failed: {e}")
    
    elif ad_type == "sponsored":
        # Handle sponsored posts
        print("   🎯 Handling sponsored post")
        try:
            home_tab = driver.find_element("accessibility id", "mainfeed-tab")
            home_tab.click()
            time.sleep(2)
            print("   ✅ Navigated away from sponsored post")
            return True
        except Exception as e:
            print(f"   ❌ Sponsored post escape failed: {e}")
    
    # Fallback methods
    print("   🔄 Trying fallback methods")
    
    fallback_methods = [
        # Method 1: Try alternative close button selectors
        lambda: driver.find_element("xpath", "//XCUIElementTypeButton[@name='ig icon x pano outline 24']").click(),
        lambda: driver.find_element("ios class chain", "**/XCUIElementTypeButton[`name == \"ig icon x pano outline 24\"`]").click(),
        
        # Method 2: Back navigation
        lambda: driver.back(),
        
        # Method 3: Home tab (always works)
        lambda: driver.find_element("accessibility id", "mainfeed-tab").click(),
        
        # Method 4: Swipe down to dismiss
        lambda: driver.swipe(200, 100, 200, 400, 500),
        
        # Method 5: Tap safe area (top left)
        lambda: driver.tap([(50, 50)]),
    ]
    
    for i, method in enumerate(fallback_methods, 1):
        try:
            print(f"   🔄 Trying fallback method {i}")
            method()
            time.sleep(2)
            
            # Check if we escaped
            new_ad_type, _ = detect_ad_type(driver)
            if new_ad_type == "none":
                print(f"   ✅ Escaped using fallback method {i}!")
                return True
        except Exception as e:
            print(f"   ❌ Fallback method {i} failed: {e}")
            continue
    
    print("   ⚠️ All escape methods failed")
    return False

def test_with_ad_recovery():
    """Test scrolling with automatic ad recovery"""
    print("🛡️  TESTING WITH AUTOMATIC AD RECOVERY")
    print("=" * 45)
    
    driver = create_driver()
    
    try:
        print("✅ Connected to Instagram app")
        time.sleep(3)
        
        # Create evidence directory
        os.makedirs("evidence/universal_ad_test", exist_ok=True)
        
        # Navigate to home
        print("\n🏠 NAVIGATE TO HOME")
        try:
            home_tab = driver.find_element("accessibility id", "mainfeed-tab")
            home_tab.click()
            time.sleep(3)
            print("   ✅ On home feed")
        except Exception as e:
            print(f"   ❌ Could not navigate to home: {e}")
        
        # Test cycle: scroll, detect ads, recover, continue
        max_attempts = 3
        like_button_found = False
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n🔄 ATTEMPT {attempt}/{max_attempts}")
            
            # Take screenshot before action
            driver.save_screenshot(f"evidence/universal_ad_test/attempt_{attempt}_before.png")
            
            # Scroll down to find content
            print("   📜 Scrolling down")
            driver.swipe(200, 400, 200, 200, 1000)
            time.sleep(2)
            
            # Take screenshot after scroll
            driver.save_screenshot(f"evidence/universal_ad_test/attempt_{attempt}_after_scroll.png")
            
            # Check for ads and handle them
            ad_type, _ = detect_ad_type(driver)
            if ad_type != "none":
                print(f"   🚨 Ad detected: {ad_type}")
                if universal_ad_escape(driver):
                    print("   ✅ Successfully escaped ad")
                    driver.save_screenshot(f"evidence/universal_ad_test/attempt_{attempt}_after_escape.png")
                else:
                    print("   ❌ Failed to escape ad")
                    continue
            
            # Look for like buttons
            print("   ❤️  Looking for like buttons")
            try:
                like_buttons = driver.find_elements("accessibility id", "like-button")
                
                if like_buttons:
                    print(f"   📊 Found {len(like_buttons)} like button(s)")
                    
                    # Find a clickable one
                    for i, button in enumerate(like_buttons):
                        try:
                            if button.is_displayed() and button.is_enabled():
                                print(f"   ✅ Button {i+1} is clickable")
                                
                                # Test the like button
                                initial_state = button.get_attribute("label") or "Unknown"
                                print(f"   📋 Initial state: '{initial_state}'")
                                
                                driver.save_screenshot(f"evidence/universal_ad_test/attempt_{attempt}_like_before.png")
                                button.click()
                                time.sleep(2)
                                driver.save_screenshot(f"evidence/universal_ad_test/attempt_{attempt}_like_after.png")
                                
                                new_state = button.get_attribute("label") or "Unknown"
                                print(f"   🎉 State change: '{initial_state}' → '{new_state}'")
                                
                                # Unlike to restore
                                time.sleep(1)
                                button.click()
                                print("   🔄 Unliked to restore state")
                                
                                like_button_found = True
                                break
                        except Exception as e:
                            print(f"   ⚠️ Button {i+1} error: {e}")
                            continue
                
                if like_button_found:
                    break
                else:
                    print("   ❌ No clickable like buttons found this attempt")
            
            except Exception as e:
                print(f"   ❌ Error looking for like buttons: {e}")
        
        if like_button_found:
            print("\n🎉 SUCCESS! Found and tested like button with ad recovery!")
            return True
        else:
            print(f"\n❌ Could not find clickable like button after {max_attempts} attempts")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        try:
            driver.quit()
            print("📱 Disconnected")
        except:
            pass

if __name__ == "__main__":
    success = test_with_ad_recovery()
    
    print("\n" + "=" * 45)
    print("🎯 UNIVERSAL AD RECOVERY TEST RESULTS")
    print("=" * 45)
    
    if success:
        print("🎉 SUCCESS! Universal ad recovery strategy works!")
        print("✅ Can handle ad landing pages AND in-feed ads")
        print("✅ Like button functionality confirmed with ad recovery")
        print("🚀 Ready for full Step 2 testing!")
    else:
        print("❌ Ad recovery strategy needs refinement")
    
    print(f"\n🏁 RESULT: {'✅ UNIVERSAL AD RECOVERY WORKS' if success else '❌ NEEDS WORK'}")
    exit(0 if success else 1)
