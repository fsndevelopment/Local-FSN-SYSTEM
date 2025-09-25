#!/usr/bin/env python3
"""
Test script to fetch and execute REAL templates from frontend storage
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:8000/api/v1"
DEVICE_ID = "device-1758399156"

def get_templates_from_storage():
    """Get templates from localStorage by checking the frontend storage"""
    print("🔍 Fetching templates from frontend storage...")
    
    # Try to get templates from the frontend API if it exists
    try:
        response = requests.get(f"{BASE_URL}/templates")
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Found {len(templates)} templates from API")
            return templates
    except Exception as e:
        print(f"⚠️ API templates not available: {e}")
    
    # Fallback: Check if we can access localStorage data
    # This would require the frontend to expose localStorage data via an API
    print("⚠️ No API access to templates, using fallback method")
    return []

def test_template_execution_with_real_data():
    """Test template execution using real template data"""
    
    print("🧪 Testing Template Execution with REAL Template Data")
    print("=" * 60)
    
    # Get real templates
    templates = get_templates_from_storage()
    
    if not templates:
        print("❌ No templates found! Please create a template in the frontend first.")
        print("   Go to Templates page -> Create Template -> Set posting interval -> Save")
        return
    
    print(f"\n📋 Found {len(templates)} templates:")
    for i, template in enumerate(templates):
        print(f"   {i+1}. {template.get('name', 'Unnamed')} - Platform: {template.get('platform', 'unknown')}")
        if 'postingIntervalMinutes' in template:
            print(f"      Posting Interval: {template['postingIntervalMinutes']} minutes")
        if 'textPostsPerDay' in template:
            print(f"      Text Posts: {template['textPostsPerDay']} per day")
    
    # Test with the first template that has posting interval
    test_template = None
    for template in templates:
        if template.get('postingIntervalMinutes', 0) > 0:
            test_template = template
            break
    
    if not test_template:
        print("❌ No template found with posting interval > 0")
        print("   Please create a template with a posting interval in the frontend")
        return
    
    print(f"\n🎯 Testing with template: '{test_template.get('name')}'")
    print(f"   Posting Interval: {test_template.get('postingIntervalMinutes')} minutes")
    print(f"   Text Posts: {test_template.get('textPostsPerDay')} per day")
    
    # Stop any running device first
    print("\n1️⃣ Stopping any running device...")
    try:
        response = requests.post(f"{BASE_URL}/devices/{DEVICE_ID}/stop")
        print(f"   Stop response: {response.status_code}")
        time.sleep(2)
    except Exception as e:
        print(f"   ⚠️ Stop request failed: {e}")
    
    # Prepare template data for backend
    template_data = {
        "settings": {
            "postingIntervalMinutes": test_template.get('postingIntervalMinutes', 30),
            "textPostsPerDay": test_template.get('textPostsPerDay', 2),
            "photosPerDay": test_template.get('photosPostsPerDay', 0),
            "textPostsFile": test_template.get('textPostsFile', ''),
            "textPostsFileContent": test_template.get('textPostsFileContent', ''),
            "photosFolder": test_template.get('photosFolder', ''),
            "captionsFile": test_template.get('captionsFile', ''),
            "captionsFileContent": test_template.get('captionsFileContent', ''),
            "followsPerDay": test_template.get('followsPerDay', 0),
            "likesPerDay": test_template.get('likesPerDay', 0),
            "scrollingTimeMinutes": test_template.get('scrollingTimeMinutes', 0)
        }
    }
    
    request_payload = {
        "device_id": DEVICE_ID,
        "job_type": "automation",
        "template_data": template_data
    }
    
    print(f"\n2️⃣ Sending REAL template data to backend:")
    print(f"   Template: {test_template.get('name')}")
    print(f"   Posting Interval: {test_template.get('postingIntervalMinutes')} minutes")
    print(f"   Full payload:")
    print(json.dumps(request_payload, indent=2))
    
    try:
        response = requests.post(f"{BASE_URL}/devices/{DEVICE_ID}/start", json=request_payload)
        print(f"\n📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Template execution started successfully")
            print(f"   📊 Response: {result}")
            print(f"\n🔍 Check backend logs for:")
            print(f"   - 'Posting interval: {test_template.get('postingIntervalMinutes')} minutes'")
            print(f"   - '🔍 DEBUG - postingIntervalMinutes in settings: {test_template.get('postingIntervalMinutes')}'")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Test completed! Check the backend logs to verify:")
    print(f"   - 'Posting interval: {test_template.get('postingIntervalMinutes')} minutes' appears")
    print(f"   - The correct interval value ({test_template.get('postingIntervalMinutes')}) is being used")
    print("   - No 'postingIntervalMinutes' is showing as 0 or None")

def create_mock_template_for_testing():
    """Create a mock template for testing if no real templates exist"""
    print("\n🔧 Creating mock template for testing...")
    
    mock_template = {
        "id": "test_template_123",
        "name": "Test Template from Python",
        "platform": "threads",
        "postingIntervalMinutes": 25,
        "textPostsPerDay": 2,
        "photosPostsPerDay": 0,
        "followsPerDay": 0,
        "likesPerDay": 0,
        "scrollingTimeMinutes": 0,
        "textPostsFile": "",
        "textPostsFileContent": "",
        "photosFolder": "",
        "captionsFile": "",
        "captionsFileContent": ""
    }
    
    print(f"   Created mock template: {mock_template['name']}")
    print(f"   Posting Interval: {mock_template['postingIntervalMinutes']} minutes")
    
    return mock_template

if __name__ == "__main__":
    # First try to get real templates
    templates = get_templates_from_storage()
    
    if not templates:
        print("⚠️ No real templates found, creating mock template for testing...")
        templates = [create_mock_template_for_testing()]
    
    test_template_execution_with_real_data()
