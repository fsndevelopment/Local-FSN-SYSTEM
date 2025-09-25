#!/usr/bin/env python3
"""
Test script to verify template execution and posting interval handling
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
DEVICE_ID = "device-1758399156"

def test_template_execution():
    """Test template execution with different posting intervals"""
    
    print("🧪 Testing Template Execution and Posting Interval Handling")
    print("=" * 60)
    
    # Test 1: Stop any running device first
    print("\n1️⃣ Stopping any running device...")
    try:
        response = requests.post(f"{BASE_URL}/devices/{DEVICE_ID}/stop")
        print(f"   Stop response: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Device stopped successfully")
        time.sleep(2)
    except Exception as e:
        print(f"   ⚠️ Stop request failed: {e}")
    
    # Test 2: Start device with 30-minute posting interval
    print("\n2️⃣ Testing with 30-minute posting interval...")
    template_data_30 = {
        "settings": {
            "postingIntervalMinutes": 30,
            "textPostsPerDay": 2,
            "photosPerDay": 0
        }
    }
    
    request_payload_30 = {
        "device_id": DEVICE_ID,
        "job_type": "automation",
        "template_data": template_data_30
    }
    
    print(f"   📤 Sending 30-minute interval data:")
    print(f"   {json.dumps(request_payload_30, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/devices/{DEVICE_ID}/start", json=request_payload_30)
        print(f"   📥 Response status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 30-minute interval test started successfully")
            print("   🔍 Check backend logs for 'Posting interval: 30 minutes'")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    time.sleep(3)
    
    # Test 3: Stop and test with 45-minute posting interval
    print("\n3️⃣ Stopping and testing with 45-minute posting interval...")
    try:
        response = requests.post(f"{BASE_URL}/devices/{DEVICE_ID}/stop")
        print(f"   Stop response: {response.status_code}")
        time.sleep(2)
    except Exception as e:
        print(f"   ⚠️ Stop request failed: {e}")
    
    template_data_45 = {
        "settings": {
            "postingIntervalMinutes": 45,
            "textPostsPerDay": 2,
            "photosPerDay": 0
        }
    }
    
    request_payload_45 = {
        "device_id": DEVICE_ID,
        "job_type": "automation",
        "template_data": template_data_45
    }
    
    print(f"   📤 Sending 45-minute interval data:")
    print(f"   {json.dumps(request_payload_45, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/devices/{DEVICE_ID}/start", json=request_payload_45)
        print(f"   📥 Response status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 45-minute interval test started successfully")
            print("   🔍 Check backend logs for 'Posting interval: 45 minutes'")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Test completed! Check the backend logs to verify:")
    print("   - 'Posting interval: X minutes' appears in the logs")
    print("   - The correct interval value is being used")
    print("   - No 'postingIntervalMinutes' is showing as 0 or None")

if __name__ == "__main__":
    test_template_execution()
