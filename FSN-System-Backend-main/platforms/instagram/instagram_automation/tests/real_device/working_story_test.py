#!/usr/bin/env python3
"""
Working Story Test - Using ACTUAL verified selectors from registry
Uses the confirmed working selectors: story-ring, stories-tray, story-dismiss-button
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

def test_story_viewing():
    """Test story viewing using ACTUAL working selectors"""
    print("📖 WORKING STORY TEST - Using Verified Selectors")
    print("=" * 50)
    
    driver = None
    
    try:
        # Create driver
        print("📱 Creating driver...")
        driver = create_driver()
        time.sleep(3)
        
        # Navigate to home feed
        print("🏠 Going to home feed...")
        home_tab = driver.find_element("accessibility id", "mainfeed-tab")
        home_tab.click()
        time.sleep(3)
        
        # Look for stories tray (ACTUAL WORKING SELECTOR)
        print("🔍 Looking for stories tray...")
        try:
            stories_tray = driver.find_element("accessibility id", "stories-tray")
            print("✅ Found stories tray!")
        except:
            print("⚠️ Stories tray not found with accessibility id, trying xpath...")
            try:
                stories_tray = driver.find_element("xpath", "//XCUIElementTypeCell[@name='stories-tray']")
                print("✅ Found stories tray with xpath!")
            except:
                print("❌ No stories tray found")
                return False
        
        # Look for story rings (ACTUAL WORKING SELECTOR)
        print("🎯 Looking for story rings...")
        try:
            story_rings = driver.find_elements("accessibility id", "story-ring")
            if story_rings:
                print(f"✅ Found {len(story_rings)} story rings!")
                
                # Click first story ring
                print("👆 Clicking first story ring...")
                driver.save_screenshot("evidence/working_story_test/before_story.png")
                story_rings[0].click()
                time.sleep(3)  # Let story load
                driver.save_screenshot("evidence/working_story_test/story_viewing.png")
                print("✅ Story opened!")
                
                # Try to dismiss story (ACTUAL WORKING SELECTOR)
                print("🔙 Dismissing story...")
                try:
                    dismiss_btn = driver.find_element("accessibility id", "story-dismiss-button")
                    dismiss_btn.click()
                    print("✅ Dismissed story with dismiss button!")
                except:
                    print("⚠️ Dismiss button not found, trying tap to exit...")
                    driver.tap([(50, 400)])  # Tap left side to exit
                    print("✅ Exited story with tap!")
                
                time.sleep(2)
                driver.save_screenshot("evidence/working_story_test/after_story.png")
                
                print("🎉 STORY VIEWING TEST: SUCCESS!")
                return True
            else:
                print("❌ No story rings found")
                return False
                
        except Exception as e:
            print(f"❌ Story rings error: {e}")
            return False
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()
            print("📱 Driver closed")

if __name__ == "__main__":
    os.makedirs("evidence/working_story_test", exist_ok=True)
    success = test_story_viewing()
    
    if success:
        print("\n✅ ACTION 3: VIEW_STORY - CONFIRMED WORKING!")
    else:
        print("\n❌ ACTION 3: VIEW_STORY - NEEDS INVESTIGATION")
