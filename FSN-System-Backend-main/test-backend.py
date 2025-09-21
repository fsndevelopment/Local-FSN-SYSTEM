#!/usr/bin/env python3
"""
Test script to check if the backend is working
"""
import requests
import json

def test_backend():
    backend_url = "https://fsn-system-backend.onrender.com"
    
    print("🔍 Testing backend endpoints...")
    
    # Test 1: Check if backend is up
    try:
        response = requests.get(f"{backend_url}/", timeout=10)
        print(f"✅ Backend is up: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend is down: {e}")
        return
    
    # Test 2: Check if agents endpoint exists
    try:
        response = requests.get(f"{backend_url}/api/agents", timeout=10)
        print(f"✅ Agents endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Agents endpoint error: {e}")
    
    # Test 3: Test pair-token endpoint
    try:
        data = {"license_id": "651A6308E6BD453C8E8C10EEF4F334A2"}
        response = requests.post(f"{backend_url}/api/agents/pair-token", 
                               json=data, timeout=10)
        print(f"✅ Pair-token endpoint: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Token: {result.get('pair_token', 'N/A')[:20]}...")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Pair-token endpoint error: {e}")

if __name__ == "__main__":
    test_backend()
