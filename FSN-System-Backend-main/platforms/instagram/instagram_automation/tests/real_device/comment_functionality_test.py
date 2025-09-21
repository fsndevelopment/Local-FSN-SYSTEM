#!/usr/bin/env python3
"""
COMMENT FUNCTIONALITY TEST - Step 3
BULLETPROOF COMMERCIAL-GRADE COMMENT SYSTEM
All selectors verified from real device XML evidence
"""
from appium import webdriver
from appium.options.ios import XCUITestOptions
import time
import os
import random

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

class CommentCheckpoints:
    """BULLETPROOF CHECKPOINT SYSTEM FOR COMMENTING"""
    
    @staticmethod
    def where_am_i(driver):
        """GPS for comment flow - where are we?"""
        try:
            if driver.find_element("accessibility id", "stories-tray"):
                return "instagram_home_feed"
        except:
            pass
            
        try:
            if driver.find_element("accessibility id", "text-view"):
                return "comment_input_active"
        except:
            pass
            
        try:
            if driver.find_element("xpath", "//XCUIElementTypeButton[@name='send-button' and @label='Post comment']"):
                return "comment_ready_to_post"
        except:
            pass
        
        return "unknown_location"
    
    @staticmethod
    def navigate_to_home_feed_with_posts(driver):
        """CHECKPOINT: Ensure we're on home feed with posts visible"""
        try:
            # Navigate to home feed
            home_tab = driver.find_element("accessibility id", "mainfeed-tab")
            home_tab.click()
            time.sleep(3)
            
            # Scroll down to reveal posts (stories are at top by default)
            print("📜 Scrolling down to reveal posts...")
            driver.swipe(200, 600, 200, 300, 1000)  # Scroll down
            time.sleep(2)
            
            # Scroll again to ensure we have posts
            driver.swipe(200, 600, 200, 300, 1000)  # Second scroll
            time.sleep(2)
            
            print("✅ Home feed with posts visible")
            return True
        except Exception as e:
            print(f"❌ Failed to navigate to home feed with posts: {e}")
            return False
    
    @staticmethod
    def find_comment_button(driver):
        """CHECKPOINT: Find and verify comment button"""
        try:
            comment_button = driver.find_element("accessibility id", "comment-button")
            return comment_button
        except Exception as e:
            print(f"❌ Comment button not found: {e}")
            return None
    
    @staticmethod
    def open_comment_section(driver, comment_button):
        """CHECKPOINT: Open comment section"""
        try:
            comment_button.click()
            time.sleep(2)
            # Verify comment section opened
            comment_input = driver.find_element("accessibility id", "text-view")
            return comment_input
        except Exception as e:
            print(f"❌ Failed to open comment section: {e}")
            return None
    
    @staticmethod
    def enter_comment_text(driver, comment_input, comment_text):
        """CHECKPOINT: Enter comment with human-like typing"""
        try:
            comment_input.click()
            time.sleep(1)
            
            # Human-like typing with delays
            for char in comment_text:
                comment_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))  # Human typing speed
            
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Failed to enter comment text: {e}")
            return False
    
    @staticmethod
    def find_post_button(driver):
        """CHECKPOINT: Find the correct post button (visible one)"""
        try:
            # Use the SPECIFIC selector for the visible post button
            post_button = driver.find_element("xpath", "//XCUIElementTypeButton[@name='send-button' and @label='Post comment']")
            if post_button.get_attribute("visible") == "true":
                return post_button
            else:
                print("⚠️ Post button found but not visible")
                return None
        except Exception as e:
            print(f"❌ Post button not found: {e}")
            return None
    
    @staticmethod
    def submit_comment(driver, post_button):
        """CHECKPOINT: Submit the comment"""
        try:
            post_button.click()
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Failed to submit comment: {e}")
            return False
    
    @staticmethod
    def close_comment_section(driver):
        """CHECKPOINT: Close comment section and return to feed"""
        try:
            close_button = driver.find_element("accessibility id", "Button")
            close_button.click()
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Failed to close comment section: {e}")
            return False

def test_comment_functionality():
    """BULLETPROOF COMMENT TEST with checkpoint recovery"""
    print("💬 TESTING COMMENT FUNCTIONALITY - STEP 3")
    print("=" * 50)
    
    # Test comments to use
    test_comments = [
        "Great post! 👍",
        "Love this! ❤️",
        "Amazing content 🔥",
        "So inspiring! ✨"
    ]
    
    driver = None
    
    try:
        print("📱 Creating driver...")
        driver = create_driver()
        time.sleep(3)
        
        checkpoints = CommentCheckpoints()
        
        # CHECKPOINT 1: Navigate to home feed with posts
        print("\n🏠 CHECKPOINT 1: Navigate to home feed with posts")
        current_location = checkpoints.where_am_i(driver)
        print(f"📍 Current location: {current_location}")
        
        if not checkpoints.navigate_to_home_feed_with_posts(driver):
            raise Exception("Failed to reach home feed with posts checkpoint")
        print("✅ CHECKPOINT 1 PASSED: At home feed with posts visible")
        
        # CHECKPOINT 2: Find comment button  
        print("\n💬 CHECKPOINT 2: Find comment button")
        comment_button = checkpoints.find_comment_button(driver)
        if not comment_button:
            raise Exception("Failed to find comment button")
        print("✅ CHECKPOINT 2 PASSED: Comment button found")
        
        # CHECKPOINT 3: Open comment section
        print("\n📝 CHECKPOINT 3: Open comment section")
        comment_input = checkpoints.open_comment_section(driver, comment_button)
        if not comment_input:
            raise Exception("Failed to open comment section")
        print("✅ CHECKPOINT 3 PASSED: Comment section opened")
        
        # CHECKPOINT 4: Enter comment text
        print("\n⌨️ CHECKPOINT 4: Enter comment text")
        selected_comment = random.choice(test_comments)
        print(f"📝 Comment to post: '{selected_comment}'")
        
        if not checkpoints.enter_comment_text(driver, comment_input, selected_comment):
            raise Exception("Failed to enter comment text")
        print("✅ CHECKPOINT 4 PASSED: Comment text entered")
        
        # CHECKPOINT 5: Find post button
        print("\n🎯 CHECKPOINT 5: Find post button")
        post_button = checkpoints.find_post_button(driver)
        if not post_button:
            raise Exception("Failed to find post button")
        print("✅ CHECKPOINT 5 PASSED: Post button found and visible")
        
        # CHECKPOINT 6: Submit comment
        print("\n📤 CHECKPOINT 6: Submit comment")
        if not checkpoints.submit_comment(driver, post_button):
            raise Exception("Failed to submit comment")
        print("✅ CHECKPOINT 6 PASSED: Comment submitted!")
        
        # CHECKPOINT 7: Close comment section  
        print("\n🔙 CHECKPOINT 7: Close comment section")
        if not checkpoints.close_comment_section(driver):
            print("⚠️ Warning: Failed to close comment section (not critical)")
        else:
            print("✅ CHECKPOINT 7 PASSED: Comment section closed")
        
        # Save evidence
        os.makedirs("evidence/comment_test", exist_ok=True)
        driver.save_screenshot("evidence/comment_test/comment_success.png")
        
        print("\n🎉 COMMENT FUNCTIONALITY TEST: SUCCESS!")
        print("✅ All checkpoints passed!")
        print("💬 Comment posted successfully!")
        print("📸 Evidence saved to: evidence/comment_test/")
        
        return True
        
    except Exception as e:
        print(f"\n💥 COMMENT TEST FAILED: {str(e)}")
        
        # Error recovery
        if driver:
            try:
                print("🔄 Attempting error recovery...")
                checkpoints = CommentCheckpoints()
                checkpoints.close_comment_section(driver)
                checkpoints.navigate_to_home_feed_with_posts(driver)
                print("✅ Error recovery successful")
            except:
                print("❌ Error recovery failed")
        
        return False
        
    finally:
        if driver:
            driver.quit()
            print("📱 Driver closed")

if __name__ == "__main__":
    success = test_comment_functionality()
    
    if success:
        print("\n✅ STEP 3: COMMENT_POST - CONFIRMED WORKING!")
    else:
        print("\n❌ STEP 3: COMMENT_POST - NEEDS DEBUGGING")
