#!/usr/bin/env python3
"""
Test script using the EXACT template data from your frontend
Based on the debug log you showed: postingIntervalMinutes: 16
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
DEVICE_ID = "device-1758399156"

def test_with_your_exact_template():
    """Test using the exact template data from your frontend debug log"""
    
    print("🧪 Testing with YOUR EXACT Template Data")
    print("=" * 60)
    print("Using the template data from your debug log:")
    print("   Template: 'erterte'")
    print("   Posting Interval: 16 minutes")
    print("   Text Posts: 3 per day")
    print("   Platform: threads")
    
    # Stop any running device first
    print("\n1️⃣ Stopping any running device...")
    try:
        response = requests.post(f"{BASE_URL}/devices/{DEVICE_ID}/stop")
        print(f"   Stop response: {response.status_code}")
        time.sleep(2)
    except Exception as e:
        print(f"   ⚠️ Stop request failed: {e}")
    
    # Use the EXACT template data from your debug log
    template_data = {
        "settings": {
            "postingIntervalMinutes": 16,  # From your debug log
            "textPostsPerDay": 3,          # From your debug log
            "photosPerDay": 0,
            "textPostsFile": "Captionss.xlsx",  # From your debug log
            "textPostsFileContent": "",  # Empty for testing
            "photosFolder": "",
            "captionsFile": "",
            "captionsFileContent": "",
            "followsPerDay": 0,
            "likesPerDay": 0,
            "scrollingTimeMinutes": 0
        }
    }
    
    request_payload = {
        "device_id": DEVICE_ID,
        "job_type": "automation",
        "template_data": template_data
    }
    
    print(f"\n2️⃣ Sending YOUR template data to backend:")
    print(f"   Template: 'erterte'")
    print(f"   Posting Interval: 16 minutes")
    print(f"   Text Posts: 3 per day")
    print(f"   Text File: Captionss.xlsx")
    print(f"\n   Full payload:")
    print(json.dumps(request_payload, indent=2))
    
    try:
        response = requests.post(f"{BASE_URL}/devices/{DEVICE_ID}/start", json=request_payload)
        print(f"\n📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Template execution started successfully")
            print(f"   📊 Response: {result}")
            print(f"\n🔍 Check backend logs for:")
            print(f"   - 'Posting interval: 16 minutes'")
            print(f"   - '🔍 DEBUG - postingIntervalMinutes in settings: 16'")
            print(f"   - '🔍 DEBUG - Final posting_interval_minutes value: 16'")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Test completed! Check the backend logs to verify:")
    print("   - 'Posting interval: 16 minutes' appears in the logs")
    print("   - The correct interval value (16) is being used")
    print("   - No 'postingIntervalMinutes' is showing as 0 or None")
    print("\n💡 If the backend still shows a different interval, the issue is in the backend processing!")

if __name__ == "__main__":
    test_with_your_exact_template()
