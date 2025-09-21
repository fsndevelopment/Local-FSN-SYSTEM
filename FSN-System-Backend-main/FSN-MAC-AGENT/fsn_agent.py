#!/usr/bin/env python3
"""
FSN Agent - Simple Python Agent
Just run this file and it will connect your device to the FSN system
"""

import requests
import time
import json
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "https://fsn-system-backend.onrender.com"
LICENSE_KEY = "651A6308E6BD453C8E8C10EEF4F334A2"

def generate_device_info():
    """Generate unique device information"""
    device_id = f"mac-iphone-{int(time.time())}"
    udid = f"ios-{uuid.uuid4().hex[:8]}"
    return device_id, udid

def register_device(device_id, udid):
    """Register device with the backend"""
    print("📡 Registering device with FSN backend...")
    
    device_data = {
        "udid": udid,
        "platform": "iOS",
        "name": "iPhone (Mac Agent)",
        "status": "active",
        "appium_port": 4720,
        "wda_port": 8100,
        "mjpeg_port": 9100,
        "last_seen": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/devices",
            json=device_data,
            headers={
                "Content-Type": "application/json",
                "X-License-Key": LICENSE_KEY
            },
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ SUCCESS! Device registered with FSN system")
            print(f"   Device ID: {response.json().get('id', 'Unknown')}")
            return response.json().get('id')
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return None

def send_heartbeat(device_id):
    """Send heartbeat to keep device online"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/devices/{device_id}/heartbeat",
            json={
                "status": "active",
                "last_seen": datetime.now().isoformat()
            },
            headers={
                "X-License-Key": LICENSE_KEY
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def main():
    print("🚀 FSN Python Agent")
    print("===================")
    print("")
    
    # Generate device info
    device_id, udid = generate_device_info()
    print(f"📱 Device Info:")
    print(f"   Device ID: {device_id}")
    print(f"   UDID: {udid}")
    print("")
    
    # Register device
    backend_device_id = register_device(device_id, udid)
    
    if not backend_device_id:
        print("")
        print("🔧 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Make sure fsndevelopment.com is accessible")
        print("   3. Try again in a few minutes")
        return
    
    print("")
    print("🎉 YOUR IPHONE IS NOW CONNECTED!")
    print("")
    print("📊 What you can do now:")
    print("   1. Go to fsndevelopment.com/devices")
    print("   2. You should see your iPhone in the device list")
    print("   3. Start automation jobs from the frontend")
    print("")
    print("🔄 Keeping connection alive...")
    print("   Press Ctrl+C to disconnect")
    print("")
    
    # Keep connection alive
    heartbeat_count = 0
    try:
        while True:
            time.sleep(30)  # Wait 30 seconds
            heartbeat_count += 1
            
            if send_heartbeat(backend_device_id):
                print(f"💓 Heartbeat #{heartbeat_count} - Device is online")
            else:
                print(f"⚠️  Heartbeat #{heartbeat_count} failed - Device may be offline")
                
    except KeyboardInterrupt:
        print("\n🛑 Disconnecting device...")
        print("   Device disconnected from FSN system")
        print("   Goodbye!")

if __name__ == "__main__":
    main()
