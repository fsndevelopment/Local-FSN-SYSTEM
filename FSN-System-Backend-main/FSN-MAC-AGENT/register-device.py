#!/usr/bin/env python3
"""
Register iPhone with Local Backend
This registers your iPhone with the local backend running on your Mac
"""

import requests
import time
import uuid
from datetime import datetime

# Local backend URL (running on your Mac)
LOCAL_BACKEND = "http://localhost:8000"

def register_iphone():
    """Register iPhone with local backend"""
    print("📱 Registering iPhone with Local FSN Backend...")
    print("")
    
    # Generate device info
    device_id = f"mac-iphone-{int(time.time())}"
    udid = f"ios-{uuid.uuid4().hex[:8]}"
    
    device_data = {
        "udid": udid,
        "platform": "iOS",
        "name": "iPhone (Mac Local)",
        "status": "active",
        "appium_port": 4720,
        "wda_port": 8100,
        "mjpeg_port": 9100,
        "last_seen": datetime.now().isoformat()
    }
    
    try:
        print(f"📡 Connecting to local backend at {LOCAL_BACKEND}...")
        response = requests.post(f"{LOCAL_BACKEND}/api/devices", json=device_data)
        
        if response.status_code == 200:
            device = response.json()
            print("✅ SUCCESS! iPhone registered with local backend")
            print(f"   Device ID: {device['id']}")
            print(f"   UDID: {device['udid']}")
            print(f"   Appium Port: {device['appium_port']}")
            print("")
            print("🎉 Your iPhone is now connected to the local FSN system!")
            print("")
            print("📊 Next Steps:")
            print("   1. Go to fsndevelopment.com")
            print("   2. Your iPhone should appear in the device list")
            print("   3. Start automation jobs from the frontend")
            print("   4. Appium will start automatically on your Mac")
            print("")
            print("🔄 Keeping connection alive...")
            print("   Press Ctrl+C to disconnect")
            
            # Keep connection alive
            while True:
                time.sleep(30)
                try:
                    heartbeat_response = requests.post(
                        f"{LOCAL_BACKEND}/api/devices/{device['id']}/heartbeat"
                    )
                    if heartbeat_response.status_code == 200:
                        print("💓 Heartbeat sent - Device is online")
                    else:
                        print("⚠️  Heartbeat failed - Device may be offline")
                except:
                    print("⚠️  Cannot connect to local backend")
                    
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            print("")
            print("🔧 Make sure the local backend is running:")
            print("   python3 local-backend.py")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local backend!")
        print("")
        print("🔧 Start the local backend first:")
        print("   python3 local-backend.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    register_iphone()
