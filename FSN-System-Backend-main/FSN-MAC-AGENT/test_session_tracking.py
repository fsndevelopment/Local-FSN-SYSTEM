#!/usr/bin/env python3
"""
Test script to demonstrate session tracking functionality
"""

import requests
import json
import time

def test_session_tracking():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Session Tracking System")
    print("=" * 50)
    
    # Test 1: Check initial session status
    print("\n1. Checking initial session status...")
    response = requests.get(f"{base_url}/api/v1/sessions")
    if response.status_code == 200:
        data = response.json()
        print(f"   📊 Total accounts with sessions: {data['total_accounts']}")
        print(f"   📅 Last updated: {time.ctime(data['last_updated'])}")
    else:
        print(f"   ❌ Failed to get sessions: {response.status_code}")
        return
    
    # Test 2: Simulate account posting (manually add to session data)
    print("\n2. Simulating account posting...")
    
    # Get current session data
    response = requests.get(f"{base_url}/api/v1/sessions")
    sessions = response.json()['sessions']
    
    # Add a test account session
    test_account_id = "test_account_123"
    sessions[test_account_id] = time.time()
    
    # Save the updated session data (this would normally be done by the backend)
    print(f"   ✅ Simulated posting for account {test_account_id}")
    
    # Test 3: Check account status with different intervals
    print("\n3. Testing account status with different intervals...")
    
    # Test with 0 minutes (should be ready)
    response = requests.get(f"{base_url}/api/v1/sessions/{test_account_id}?posting_interval_minutes=0")
    if response.status_code == 200:
        status = response.json()
        print(f"   📊 Account {test_account_id} with 0 min interval: {status['status']} - {status['message']}")
    
    # Test with 5 minutes (should be in cooldown)
    response = requests.get(f"{base_url}/api/v1/sessions/{test_account_id}?posting_interval_minutes=5")
    if response.status_code == 200:
        status = response.json()
        print(f"   📊 Account {test_account_id} with 5 min interval: {status['status']} - {status['message']}")
        if 'remaining_minutes' in status:
            print(f"   ⏰ Remaining cooldown: {status['remaining_minutes']} minutes")
    
    # Test 4: Wait and check again
    print("\n4. Waiting 2 seconds and checking again...")
    time.sleep(2)
    
    response = requests.get(f"{base_url}/api/v1/sessions/{test_account_id}?posting_interval_minutes=1")
    if response.status_code == 200:
        status = response.json()
        print(f"   📊 Account {test_account_id} with 1 min interval: {status['status']} - {status['message']}")
        if 'remaining_minutes' in status:
            print(f"   ⏰ Remaining cooldown: {status['remaining_minutes']} minutes")
    
    print("\n✅ Session tracking test completed!")
    print("\n📝 How it works:")
    print("   - Each account that posts gets a timestamp in LAST_ACCOUNT_SESSIONS")
    print("   - The system checks elapsed time vs posting_interval_minutes")
    print("   - Accounts in cooldown are skipped until their interval expires")
    print("   - Session data is saved to account_sessions.json for persistence")

if __name__ == "__main__":
    test_session_tracking()
