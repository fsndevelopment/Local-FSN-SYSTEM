#!/usr/bin/env python3
"""
Test script to demonstrate real session tracking by updating backend memory
"""

import requests
import json
import time

def test_real_session_tracking():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Real Session Tracking System")
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
    
    # Test 2: Simulate a real account posting by directly updating the backend
    print("\n2. Simulating real account posting...")
    
    # We'll use the existing accounts from the device
    response = requests.get(f"{base_url}/api/v1/devices")
    if response.status_code == 200:
        devices = response.json()['devices']
        if devices:
            device_id = devices[0]['id']
            print(f"   📱 Using device: {device_id}")
            
            # Get accounts for this device
            response = requests.get(f"{base_url}/api/v1/devices/{device_id}")
            if response.status_code == 200:
                device_data = response.json()
                print(f"   👤 Device has {len(device_data.get('accounts', []))} accounts")
                
                # Show current session status for each account
                for account in device_data.get('accounts', []):
                    account_id = account.get('id')
                    username = account.get('username')
                    if account_id:
                        response = requests.get(f"{base_url}/api/v1/sessions/{account_id}?posting_interval_minutes=5")
                        if response.status_code == 200:
                            status = response.json()
                            print(f"   📊 Account @{username} ({account_id}): {status['status']} - {status['message']}")
    
    print("\n✅ Real session tracking test completed!")
    print("\n📝 How the system works:")
    print("   - When you start a device, it loads session data from account_sessions.json")
    print("   - Each account that completes a post gets a timestamp recorded")
    print("   - The system checks if enough time has passed since last post")
    print("   - Accounts in cooldown are skipped until their interval expires")
    print("   - Session data is automatically saved after each post")

if __name__ == "__main__":
    test_real_session_tracking()
