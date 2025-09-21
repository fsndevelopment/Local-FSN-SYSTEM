#!/usr/bin/env python3
"""
WebDriverAgent Setup Script for iOS Device
This script helps set up WebDriverAgent for your iPhone
"""

import subprocess
import os
import sys

def run_command(cmd, description):
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True
        else:
            print(f"❌ {description} failed:")
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def main():
    print("🚀 WebDriverAgent Setup for iOS Device")
    print("=" * 50)
    
    # Check if Xcode is installed
    if not os.path.exists("/Applications/Xcode.app"):
        print("❌ Xcode is not installed. Please install Xcode from the App Store.")
        return False
    
    print("✅ Xcode is installed")
    
    # Check if device is connected
    print("\n📱 Checking connected devices...")
    result = subprocess.run("xcrun devicectl list devices", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("Connected devices:")
        print(result.stdout)
    else:
        print("❌ Could not list devices. Make sure your iPhone is connected and trusted.")
        return False
    
    # Install WebDriverAgent
    print("\n🔧 Installing WebDriverAgent...")
    
    # Find WebDriverAgent path
    wda_path = None
    try:
        result = subprocess.run("find /opt/homebrew -name 'WebDriverAgent' -type d 2>/dev/null", 
                              shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            wda_path = result.stdout.strip().split('\n')[0]
            print(f"✅ Found WebDriverAgent at: {wda_path}")
        else:
            print("❌ WebDriverAgent not found. Installing...")
            if not run_command("appium driver install xcuitest", "Installing XCUITest driver"):
                return False
            
            # Try to find it again
            result = subprocess.run("find /opt/homebrew -name 'WebDriverAgent' -type d 2>/dev/null", 
                                  shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                wda_path = result.stdout.strip().split('\n')[0]
                print(f"✅ Found WebDriverAgent at: {wda_path}")
            else:
                print("❌ Still cannot find WebDriverAgent")
                return False
    except Exception as e:
        print(f"❌ Error finding WebDriverAgent: {e}")
        return False
    
    if not wda_path:
        print("❌ WebDriverAgent path not found")
        return False
    
    # Navigate to WebDriverAgent directory
    os.chdir(wda_path)
    print(f"📁 Working in: {wda_path}")
    
    # Install dependencies
    if not run_command("xcodebuild -project WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination 'platform=iOS,name=iPhone' clean build", 
                      "Building WebDriverAgent"):
        print("⚠️ Build failed. This is normal for the first run.")
        print("   You need to open the project in Xcode and configure signing.")
    
    print("\n🎯 Next Steps:")
    print("1. Open Xcode")
    print("2. Open the WebDriverAgent.xcodeproj file")
    print("3. Select your iPhone as the target device")
    print("4. Set your Apple Developer Team in the project settings")
    print("5. Build and run the WebDriverAgentRunner on your device")
    print("6. Once it's running on your device, try the automation again")
    
    print(f"\n📁 WebDriverAgent location: {wda_path}")
    print("🔧 Open this in Xcode: open WebDriverAgent.xcodeproj")
    
    return True

if __name__ == "__main__":
    main()
