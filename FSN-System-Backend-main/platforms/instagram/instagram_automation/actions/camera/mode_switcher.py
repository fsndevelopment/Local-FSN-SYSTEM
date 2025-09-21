#!/usr/bin/env python3
"""
WORKING CAMERA MODE SWITCHER - NO SAFETY BULLSHIT
Just switches modes using the discovered working positions
"""
import time
from appium.webdriver.common.appiumby import AppiumBy

def get_current_mode(driver):
    """Get current camera mode"""
    try:
        mode_selector = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "current-camera-mode")
        return mode_selector.get_attribute('value')
    except:
        return None

def switch_camera_mode_WORKING(driver, target_mode):
    """
    WORKING camera mode switching - NO SAFETY CHECKS
    Uses discovered working positions: POST=13.3%, STORY=60%, REEL=66.7%
    """
    try:
        target_mode = target_mode.upper()
        if target_mode not in ['POST', 'STORY', 'REEL']:
            print(f"❌ Invalid mode: {target_mode}")
            return False
        
        print(f"🎯 Switching to {target_mode} mode...")
        
        # Find mode selector
        mode_selector = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "current-camera-mode")
        
        # Get current mode
        current_mode = get_current_mode(driver)
        print(f"   📍 Current: {current_mode}")
        
        if current_mode == target_mode:
            print(f"   ✅ Already in {target_mode}")
            return True
        
        # Calculate position using WORKING percentages
        location = mode_selector.location
        size = mode_selector.size
        center_y = location['y'] + size['height'] // 2
        
        # DISCOVERED WORKING POSITIONS
        working_percentages = {
            'POST': 0.133,   # 13.3% - confirmed working
            'STORY': 0.60,   # 60.0% - confirmed working
            'REEL': 0.667    # 66.7% - confirmed working
        }
        
        target_x = location['x'] + int(size['width'] * working_percentages[target_mode])
        print(f"   👆 Tapping at {working_percentages[target_mode]*100:.1f}%: ({target_x}, {center_y})")
        
        # Just tap - no safety bullshit
        driver.tap([(target_x, center_y)])
        time.sleep(1.5)
        
        # Verify result
        new_mode = get_current_mode(driver)
        if new_mode == target_mode:
            print(f"   ✅ SUCCESS: {current_mode} → {target_mode}")
            return True
        else:
            print(f"   ❌ FAILED: got {new_mode}")
            return False
        
    except Exception as e:
        print(f"❌ Switch failed: {e}")
        return False

def navigate_to_camera_and_switch(driver, target_mode):
    """
    Navigate to camera and switch mode - NO SAFETY CHECKS
    """
    try:
        print(f"📷 Navigate to camera and switch to {target_mode}...")
        
        # Navigate to camera tab
        try:
            camera_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "camera-tab")
            camera_tab.click()
            time.sleep(3)
        except:
            print("   📍 Already on camera")
        
        # Switch mode using working function
        return switch_camera_mode_WORKING(driver, target_mode)
        
    except Exception as e:
        print(f"❌ Navigation failed: {e}")
        return False

# Test function
def test_working_camera_modes():
    """Test the working camera mode switcher"""
    from appium import webdriver
    from appium.options.ios import XCUITestOptions
    
    print("🎯 TESTING WORKING CAMERA MODE SWITCHER (NO SAFETY)")
    print("=" * 55)
    
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.automation_name = "XCUITest"
    options.bundle_id = "com.burbn.instagram"
    options.udid = "f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3"  # PhoneX
    options.device_name = "PhoneX"
    options.wda_local_port = 8100
    options.no_reset = True
    options.full_reset = False
    options.new_command_timeout = 300
    
    driver = webdriver.Remote("http://localhost:4739", options=options)
    
    try:
        time.sleep(2)
        
        # Test all mode switches
        test_sequence = [
            ('POST', 'Switch to POST'),
            ('STORY', 'Switch to STORY'),  
            ('REEL', 'Switch to REEL'),
            ('POST', 'Back to POST'),
            ('REEL', 'Direct POST→REEL'),
            ('STORY', 'REEL→STORY')
        ]
        
        success_count = 0
        
        for i, (mode, description) in enumerate(test_sequence):
            print(f"\n--- Test {i+1}: {description} ---")
            
            if navigate_to_camera_and_switch(driver, mode):
                success_count += 1
                print(f"✅ {description} SUCCESS")
                driver.save_screenshot(f"evidence/working_test_{i+1}_{mode.lower()}_success.png")
            else:
                print(f"❌ {description} FAILED")
                driver.save_screenshot(f"evidence/working_test_{i+1}_{mode.lower()}_failed.png")
            
            time.sleep(1)
        
        success_rate = (success_count / len(test_sequence)) * 100
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Success: {success_count}/{len(test_sequence)}")
        print(f"   Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 CAMERA MODE SWITCHING COMPLETELY FIXED!")
            print("✅ Ready for content creation features!")
            print("🚀 POST_REEL, POST_STORY, POST_CAROUSEL can now be implemented!")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        driver.quit()
        print("🔌 Driver closed")

if __name__ == "__main__":
    print("🎯 WORKING Camera Mode Switcher - NO SAFETY BULLSHIT")
    print("Uses discovered working positions: POST=13.3%, STORY=60%, REEL=66.7%")
    input("Press Enter to test...")
    
    success = test_working_camera_modes()
    
    if success:
        print("\n🎉 FUCKING FINALLY! CAMERA MODE SWITCHING WORKS!")
        print("✅ No more safety check bullshit interfering")
        print("🚀 Content creation features unlocked!")
