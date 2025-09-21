#!/usr/bin/env python3
"""
Simple iPhone Connection Test
Bypasses all the complex setup and directly tests iPhone connection
"""

import requests
import json
import time
import subprocess
import os

def kill_port(port):
    """Kill any process using the specified port"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    subprocess.run(['kill', '-9', pid.strip()], check=False)
                    print(f"🔧 Killed process {pid.strip()} using port {port}")
    except Exception as e:
        print(f"⚠️ Could not kill process using port {port}: {e}")

def start_appium(port):
    """Start Appium server"""
    print(f"🚀 Starting Appium on port {port}...")
    
    # Kill any existing process on the port
    kill_port(port)
    time.sleep(2)
    
    # Start Appium
    cmd = [
        "appium", "server",
        "--port", str(port),
        "--driver-xcuitest-webdriveragent-port", "8109",
        "--session-override",
        "--log-level", "info"
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for Appium to start
    print("⏳ Waiting for Appium to start...")
    time.sleep(5)
    
    # Check if it's running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"❌ Appium failed to start:")
        print(f"   STDOUT: {stdout}")
        print(f"   STDERR: {stderr}")
        return None
    
    # Check if port is listening
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        print(f"✅ Appium is running on port {port}")
        return process
    else:
        print(f"❌ Appium port {port} is not listening")
        process.terminate()
        return None

def test_iphone_connection():
    """Test iPhone connection with minimal setup"""
    print("🧪 Testing iPhone Connection")
    print("=" * 50)
    
    # Device info - using your iPhone UDID
    device_info = {
        "udid": "ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf",  # Your iPhone UDID
        "name": "iPhone7",
        "ios_version": "15.0",  # iPhone 7 typically runs iOS 15 or earlier
        "appium_port": 4741
    }
    
    print(f"📱 Device: {device_info['name']}")
    print(f"📱 UDID: {device_info['udid']}")
    print(f"📱 iOS: {device_info['ios_version']}")
    
    # Start Appium
    appium_process = start_appium(device_info['appium_port'])
    if not appium_process:
        return False
    
    try:
        # Test basic Appium status
        print("\n🔍 Testing Appium status...")
        response = requests.get(f"http://localhost:{device_info['appium_port']}/status", timeout=10)
        if response.status_code == 200:
            print("✅ Appium is responding")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ Appium status check failed: {response.status_code}")
            return False
        
        # Test session creation with minimal capabilities
        print("\n🔍 Testing session creation...")
        
        # Use the same capabilities as the working script
        capabilities = {
            "platformName": "iOS",
            "appium:deviceName": device_info['name'],
            "appium:udid": device_info['udid'],
            "appium:automationName": "XCUITest",
            "appium:wdaLocalPort": 8109,
            "appium:updatedWDABundleId": "com.device11.wd11",  # Use the same bundle ID as working script
            "appium:useNewWDA": False,  # Reuse existing WDA
            "appium:skipServerInstallation": True,  # Skip WDA installation
            "appium:noReset": True
        }
        
        session_payload = {
            "capabilities": {
                "alwaysMatch": capabilities
            }
        }
        
        print("📱 Capabilities:")
        for key, value in capabilities.items():
            print(f"   {key}: {value}")
        
        print("\n⏳ Creating session (this may take 2-3 minutes for first run)...")
        
        # Create session with longer timeout
        response = requests.post(
            f"http://localhost:{device_info['appium_port']}/session",
            json=session_payload,
            timeout=180  # 3 minutes timeout
        )
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get('value', {}).get('sessionId')
            print(f"✅ Successfully connected to iPhone!")
            print(f"   Session ID: {session_id}")
            
            # Test basic interaction
            print("\n🔍 Testing basic interaction...")
            try:
                # Get window size
                size_response = requests.get(
                    f"http://localhost:{device_info['appium_port']}/session/{session_id}/window/size",
                    timeout=10
                )
                if size_response.status_code == 200:
                    size_data = size_response.json()
                    print(f"✅ Screen size: {size_data.get('value', {})}")
                else:
                    print(f"⚠️ Could not get screen size: {size_response.status_code}")
                
                # Close session
                requests.delete(f"http://localhost:{device_info['appium_port']}/session/{session_id}", timeout=10)
                print("✅ Session closed")
                
            except Exception as e:
                print(f"⚠️ Error during interaction test: {e}")
            
            return True
            
        else:
            print(f"❌ Failed to create session:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - WebDriverAgent build is taking too long")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up
        if appium_process:
            print("\n🧹 Cleaning up...")
            appium_process.terminate()
            try:
                appium_process.wait(timeout=5)
            except:
                appium_process.kill()
            print("✅ Appium stopped")

def main():
    print("🚀 iPhone Connection Test")
    print("This will test direct connection to your iPhone")
    print("=" * 60)
    
    # Check if device is connected
    print("📱 Checking device connection...")
    try:
        result = subprocess.run("xcrun devicectl list devices", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            if "29B26C51-9847-5284-AC5E-8A1241DB9A52" in result.stdout:
                print("✅ iPhone 11 is connected")
            else:
                print("❌ iPhone 11 not found in connected devices")
                print("Available devices:")
                print(result.stdout)
                return
        else:
            print("❌ Could not check device connection")
            return
    except Exception as e:
        print(f"❌ Error checking devices: {e}")
        return
    
    # Run the test
    success = test_iphone_connection()
    
    if success:
        print("\n🎉 SUCCESS! iPhone connection test passed!")
        print("Your iPhone can be automated with Appium.")
    else:
        print("\n💥 FAILED! iPhone connection test failed.")
        print("Check the error messages above for details.")
        print("\nCommon issues:")
        print("1. Make sure your iPhone is trusted and unlocked")
        print("2. Check that Xcode is properly installed")
        print("3. Verify your Apple Developer account is set up")
        print("4. Try running this test again")

if __name__ == "__main__":
    main()
