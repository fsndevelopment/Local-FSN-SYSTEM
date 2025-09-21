#!/usr/bin/env python3
"""
Find Ad and Test Recovery - Aggressive Version
Keeps scrolling until we find an ad, then tests our recovery strategy
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

def scroll_and_look_for_ad(driver):
    """Keep scrolling until we find an ad"""
    print("🔍 HUNTING FOR ADS")
    
    for scroll_attempt in range(10):  # Try up to 10 scrolls
        print(f"\n📱 SCROLL ATTEMPT {scroll_attempt + 1}")
        
        # Check for ads before scrolling
        cta_buttons = driver.find_elements("accessibility id", "cta-button")
        sponsored_text = driver.find_elements("accessibility id", "Sponsored")
        
        if cta_buttons or sponsored_text:
            print("🎯 AD FOUND!")
            return True
            
        # Scroll down to find more content
        print("⬇️ Scrolling down to find ads...")
        driver.swipe(300, 600, 300, 300, 800)  # Slower swipe
        time.sleep(2)  # Wait for content to load
        
    print("❌ No ads found after 10 scrolls")
    return False

def test_ad_click_and_recovery(driver):
    """Intentionally click on an ad and test recovery"""
    print("\n🎯 TESTING AD CLICK AND RECOVERY")
    
    # Look for CTA button (Download, Sign up, etc.)
    cta_buttons = driver.find_elements("accessibility id", "cta-button")
    
    if cta_buttons:
        print(f"📱 Found {len(cta_buttons)} CTA buttons")
        print("🖱️ Clicking on first CTA button to test recovery...")
        
        # Take screenshot before clicking
        driver.save_screenshot("evidence/before_ad_click.png")
        
        # Click the ad
        cta_buttons[0].click()
        time.sleep(3)  # Wait for ad to load
        
        # Take screenshot after clicking
        driver.save_screenshot("evidence/after_ad_click.png")
        
        # Test recovery strategy
        return test_ad_recovery(driver)
    else:
        print("❌ No CTA buttons found to test")
        return False

def test_ad_recovery(driver):
    """Test our ad recovery strategies"""
    print("\n🛡️ TESTING AD RECOVERY STRATEGIES")
    
    # Strategy 1: Look for close button (X)
    try:
        close_buttons = driver.find_elements("accessibility id", "ig icon x pano outline 24")
        if close_buttons:
            print("✅ STRATEGY 1: Found close button (X)")
            close_buttons[0].click()
            time.sleep(2)
            driver.save_screenshot("evidence/after_close_button.png")
            print("🎉 Successfully closed ad with X button!")
            return True
    except Exception as e:
        print(f"❌ Strategy 1 failed: {e}")
    
    # Strategy 2: Back button
    try:
        back_buttons = driver.find_elements("accessibility id", "Back")
        if back_buttons:
            print("✅ STRATEGY 2: Found back button")
            back_buttons[0].click()
            time.sleep(2)
            print("🎉 Successfully used back button!")
            return True
    except Exception as e:
        print(f"❌ Strategy 2 failed: {e}")
    
    # Strategy 3: Home tab
    try:
        home_tabs = driver.find_elements("accessibility id", "Home")
        if home_tabs:
            print("✅ STRATEGY 3: Found home tab")
            home_tabs[0].click()
            time.sleep(2)
            print("🎉 Successfully returned via home tab!")
            return True
    except Exception as e:
        print(f"❌ Strategy 3 failed: {e}")
    
    print("❌ ALL RECOVERY STRATEGIES FAILED")
    return False

def find_ad_and_test_recovery():
    """Main test function"""
    print("🚀 FIND AD AND TEST RECOVERY")
    print("=" * 50)
    
    os.makedirs("evidence", exist_ok=True)
    driver = create_driver()
    
    try:
        # Start from home
        print("🏠 Ensuring we're on home feed...")
        home_tabs = driver.find_elements("accessibility id", "Home")
        if home_tabs:
            home_tabs[0].click()
            time.sleep(2)
        
        # Hunt for ads
        if scroll_and_look_for_ad(driver):
            # Test clicking ad and recovery
            if test_ad_click_and_recovery(driver):
                print("\n🎉 AD RECOVERY TEST SUCCESSFUL!")
            else:
                print("\n❌ AD RECOVERY TEST FAILED!")
        else:
            print("\n❌ Could not find any ads to test recovery")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        driver.save_screenshot("evidence/test_error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    find_ad_and_test_recovery()
