#!/usr/bin/env python3
"""
Threads 2FA Login Functionality Test
====================================

Test script for Threads 2FA login functionality using the 8-checkpoint system.
Tests the complete 2FA authentication flow with real device.

Test Credentials:
- Username: nikita64712025c
- Password: datNe4zRS5qy
- 2FA Code: 7A6QISVJHZ77DSFW26BP547NUDKDEQSB

Author: FSN Appium Team
Last Updated: January 15, 2025
Status: Production-ready
"""

import sys
import os
import time
import logging
from appium import webdriver
from appium.options.ios import XCUITestOptions

# Add the backend-appium-integration directory to the path
sys.path.append('/Users/jacqubsf/Downloads/FSN-APPIUM-main/backend-appium-integration')

from platforms.threads.actions.login_action import create_threads_login_action
from platforms.threads.actions.twofa_login_action import create_threads_2fa_login_action

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_2fa_login():
    """Test Threads 2FA login functionality"""
    
    # Test credentials
    test_username = "nikita64712025c"
    test_password = "datNe4zRS5qy"
    test_2fa_code = "7A6QISVJHZ77DSFW26BP547NUDKDEQSB"
    
    # Device configuration
    device_config = {
        "udid": "ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf",
        "wda_port": 8109,
        "wda_bundle_id": "com.device11.wd11"
    }
    
    # Appium server configuration
    appium_server_url = "http://localhost:4741"
    
    # iOS capabilities
    options = XCUITestOptions()
    options.udid = device_config["udid"]
    options.platform_name = "iOS"
    options.platform_version = "17.0"  # Adjust based on your device
    options.device_name = "iPhone"
    options.automation_name = "XCUITest"
    options.no_reset = True
    options.full_reset = False
    
    driver = None
    
    try:
        logger.info("🚀 Starting Threads 2FA Login Test")
        logger.info(f"📱 Device: {device_config['udid']}")
        logger.info(f"👤 Username: {test_username}")
        logger.info(f"🔐 2FA Code: {test_2fa_code[:3]}***{test_2fa_code[-3:]}")
        
        # Initialize WebDriver
        logger.info("🔧 Initializing WebDriver...")
        driver = webdriver.Remote(appium_server_url, options=options)
        logger.info("✅ WebDriver initialized successfully")
        
        # Test 1: Regular login first (to trigger 2FA requirement)
        logger.info("\n" + "="*60)
        logger.info("🧵 TEST 1: Regular Login (to trigger 2FA)")
        logger.info("="*60)
        
        login_action = create_threads_login_action(driver, device_config)
        login_result = login_action.execute(
            username=test_username,
            password=test_password,
            account_type="2fa"
        )
        
        logger.info(f"📊 Login Result: {login_result['success']}")
        if not login_result['success']:
            logger.info("ℹ️ Regular login failed as expected - 2FA required")
        else:
            logger.info("⚠️ Regular login succeeded - 2FA may not be required")
        
        # Wait a moment before 2FA test
        time.sleep(3)
        
        # Test 2: 2FA Login
        logger.info("\n" + "="*60)
        logger.info("🧵 TEST 2: 2FA Login")
        logger.info("="*60)
        
        twofa_action = create_threads_2fa_login_action(driver, device_config)
        twofa_result = twofa_action.execute(
            username=test_username,
            password=test_password,
            twofa_code=test_2fa_code
        )
        
        # Display results
        logger.info("\n" + "="*60)
        logger.info("📊 2FA LOGIN TEST RESULTS")
        logger.info("="*60)
        logger.info(f"✅ Success: {twofa_result['success']}")
        logger.info(f"🎯 Action ID: {twofa_result.get('action_id', 'N/A')}")
        logger.info(f"📁 Log Directory: {twofa_result.get('log_directory', 'N/A')}")
        
        if twofa_result['success']:
            logger.info("🎉 2FA Login test PASSED!")
            logger.info("✅ Account successfully logged in with 2FA")
        else:
            logger.error("❌ 2FA Login test FAILED!")
            if 'error' in twofa_result:
                logger.error(f"🚨 Error: {twofa_result['error']}")
        
        # Display session summary
        if 'session_summary' in twofa_result:
            summary = twofa_result['session_summary']
            logger.info("\n📈 SESSION SUMMARY:")
            logger.info(f"   Total Actions: {summary.get('total_actions', 0)}")
            logger.info(f"   Successful Actions: {summary.get('successful_actions', 0)}")
            logger.info(f"   Failed Actions: {summary.get('failed_actions', 0)}")
            logger.info(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        return twofa_result['success']
        
    except Exception as e:
        logger.error(f"🚨 Test execution failed: {str(e)}")
        return False
        
    finally:
        # Cleanup
        if driver:
            try:
                logger.info("🧹 Cleaning up WebDriver...")
                driver.quit()
                logger.info("✅ WebDriver cleanup completed")
            except Exception as e:
                logger.error(f"⚠️ Error during cleanup: {str(e)}")

def main():
    """Main test function"""
    print("🧵 Threads 2FA Login Functionality Test")
    print("=======================================")
    print("Testing 2FA authentication flow with real device")
    print("Using provided test credentials")
    print()
    
    # Check if Appium server is running
    try:
        import requests
        response = requests.get("http://localhost:4741/status", timeout=5)
        if response.status_code == 200:
            print("✅ Appium server is running")
        else:
            print("❌ Appium server is not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Appium server: {str(e)}")
        print("Please start Appium server first:")
        print("appium --port 4741")
        return False
    
    # Run the test
    success = test_2fa_login()
    
    print("\n" + "="*60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ 2FA login functionality is working correctly")
    else:
        print("❌ TESTS FAILED!")
        print("🔧 Check the logs for detailed error information")
    print("="*60)
    
    return success

if __name__ == "__main__":
    main()
