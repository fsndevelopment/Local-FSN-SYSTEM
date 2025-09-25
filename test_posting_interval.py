#!/usr/bin/env python3

import requests
import json
import time

def test_posting_interval():
    """Test if postingIntervalMinutes is being received correctly by the backend"""
    
    # Test data
    test_data = {
        "device_id": "device-1758399156",
        "job_type": "automation",
        "template_data": {
            "settings": {
                "postingIntervalMinutes": 45,
                "textPostsPerDay": 2,
                "photosPerDay": 0
            }
        }
    }
    
    print("🧪 Testing postingIntervalMinutes reception...")
    print(f"📤 Sending data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Stop device first
        print("\n🛑 Stopping device...")
        stop_response = requests.post("http://localhost:8000/api/v1/devices/device-1758399156/stop")
        print(f"Stop response: {stop_response.json()}")
        
        time.sleep(2)
        
        # Start device with test data
        print("\n🚀 Starting device with test data...")
        start_response = requests.post(
            "http://localhost:8000/api/v1/devices/device-1758399156/start",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        
        print(f"Start response: {start_response.json()}")
        
        if start_response.status_code == 200:
            print("✅ Device started successfully!")
            print("🔍 Check the backend logs to see if postingIntervalMinutes was received correctly")
        else:
            print(f"❌ Failed to start device: {start_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_posting_interval()
