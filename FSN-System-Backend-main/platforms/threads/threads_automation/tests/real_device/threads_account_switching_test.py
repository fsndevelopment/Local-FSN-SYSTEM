#!/usr/bin/env python3
"""
Threads Account Switching Test
Desktop test following the same checkpoint structure as Instagram test
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the backend API to the path
sys.path.append('/Users/janvorlicek/Desktop/FSN-APPIUM-main/backend-appium-integration/api')

from services.threads_account_switching import threads_account_switching

class AccountSwitchingTest:
    def __init__(self):
        self.test_name = "threads_account_switching"
        self.evidence_dir = Path("/Users/janvorlicek/Desktop/FSN-APPIUM-main/evidence")
        self.test_dir = None
        self.results = []
        
    def create_test_directory(self):
        """Create test directory with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_dir = self.evidence_dir / f"{self.test_name}_{timestamp}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created test directory: {self.test_dir}")
        
    def save_checkpoint(self, action_name: str, success: bool, data: dict = None):
        """Save checkpoint following the established pattern"""
        timestamp = datetime.now().strftime("%H%M%S")
        status = "SUCCESS" if success else "FAILED"
        filename_prefix = f"{action_name}_{status}_{timestamp}"
        
        checkpoint = {
            "action": action_name,
            "status": status,
            "timestamp": timestamp,
            "success": success,
            "data": data or {}
        }
        
        # Save JSON checkpoint
        checkpoint_file = self.test_dir / f"{filename_prefix}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
            
        return checkpoint

    async def test_launch_threads(self, device_udid: str):
        """Test launching Threads app"""
        print(f"\n🚀 Test 1: Launch Threads on {device_udid}")
        try:
            result = await threads_account_switching.launch_threads_homepage(device_udid)
            success = result.get('success', False)
            message = result.get('message', 'Unknown error')
            
            if success:
                print(f"✅ Threads launched successfully")
            else:
                print(f"❌ Threads launch failed: {message}")
                
            self.save_checkpoint("launch_threads_app", success, result)
            return success, message
            
        except Exception as e:
            error_msg = f"Threads launch error: {str(e)}"
            print(f"❌ Threads launch failed: {error_msg}")
            self.save_checkpoint("launch_threads_app", False, {"error": str(e)})
            return False, error_msg

    async def test_navigate_to_profile(self, device_udid: str):
        """Test navigating to profile tab"""
        print(f"\n👤 Test 2: Navigate to profile tab on {device_udid}")
        try:
            result = await threads_account_switching.navigate_to_profile_tab(device_udid)
            success = result.get('success', False)
            message = result.get('message', 'Unknown error')
            
            if success:
                print(f"✅ Profile navigation successful")
            else:
                print(f"❌ Profile navigation failed: {message}")
                
            self.save_checkpoint("navigate_to_profile_tab", success, result)
            return success, message
            
        except Exception as e:
            error_msg = f"Profile navigation error: {str(e)}"
            print(f"❌ Profile navigation failed: {error_msg}")
            self.save_checkpoint("navigate_to_profile_tab", False, {"error": str(e)})
            return False, error_msg

    async def test_open_account_switcher(self, device_udid: str):
        """Test opening account switcher"""
        print(f"\n🔄 Test 3: Open account switcher on {device_udid}")
        try:
            result = await threads_account_switching.open_account_switcher(device_udid)
            success = result.get('success', False)
            message = result.get('message', 'Unknown error')
            current_username = result.get('data', {}).get('current_username')
            
            if success:
                print(f"✅ Account switcher opened successfully")
                if current_username:
                    print(f"   Current username: {current_username}")
            else:
                print(f"❌ Account switcher failed: {message}")
                
            self.save_checkpoint("open_account_switcher", success, result)
            return success, message, current_username
            
        except Exception as e:
            error_msg = f"Account switcher error: {str(e)}"
            print(f"❌ Account switcher failed: {error_msg}")
            self.save_checkpoint("open_account_switcher", False, {"error": str(e)})
            return False, error_msg, None

    async def test_get_available_accounts(self, device_udid: str, current_username: str = None):
        """Test getting available accounts"""
        print(f"\n📋 Test 4: Get available accounts on {device_udid}")
        try:
            result = await threads_account_switching.get_available_accounts(device_udid, current_username)
            success = result.get('success', False)
            message = result.get('message', 'Unknown error')
            accounts = result.get('data', {}).get('accounts', [])
            
            if success:
                print(f"✅ Found {len(accounts)} available accounts:")
                for account in accounts:
                    username = account.get('username', account) if isinstance(account, dict) else account
                    print(f"   - {username}")
            else:
                print(f"❌ Get accounts failed: {message}")
                
            self.save_checkpoint("get_available_accounts", success, result)
            return success, message, accounts
            
        except Exception as e:
            error_msg = f"Get accounts error: {str(e)}"
            print(f"❌ Get accounts failed: {error_msg}")
            self.save_checkpoint("get_available_accounts", False, {"error": str(e)})
            return False, error_msg, []

    async def test_switch_to_account(self, device_udid: str, target_username: str):
        """Test switching to a specific account"""
        print(f"\n🔄 Test 5: Switch to account '{target_username}' on {device_udid}")
        try:
            result = await threads_account_switching.switch_to_account(device_udid, target_username)
            success = result.get('success', False)
            message = result.get('message', 'Unknown error')
            
            if success:
                print(f"✅ Account switch successful")
            else:
                print(f"❌ Account switch failed: {message}")
                
            self.save_checkpoint(f"switch_to_account_{target_username}", success, result)
            return success, message
            
        except Exception as e:
            error_msg = f"Account switch error: {str(e)}"
            print(f"❌ Account switch failed: {error_msg}")
            self.save_checkpoint(f"switch_to_account_{target_username}", False, {"error": str(e)})
            return False, error_msg

    async def test_complete_flow(self, device_udid: str, target_username: str):
        """Test complete account switching flow"""
        print(f"\n🎯 Test 6: Complete flow to switch to '{target_username}' on {device_udid}")
        try:
            result = await threads_account_switching.complete_account_switch_flow(device_udid, target_username)
            success = result.get('success', False)
            message = result.get('message', 'Unknown error')
            
            if success:
                print(f"✅ Complete flow successful")
            else:
                print(f"❌ Complete flow failed: {message}")
                
            self.save_checkpoint(f"complete_flow_{target_username}", success, result)
            return success, message
            
        except Exception as e:
            error_msg = f"Complete flow error: {str(e)}"
            print(f"❌ Complete flow failed: {error_msg}")
            self.save_checkpoint(f"complete_flow_{target_username}", False, {"error": str(e)})
            return False, error_msg

    def generate_test_report(self):
        """Generate test report"""
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results if result.get('success', False))
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_name": self.test_name,
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round(success_rate, 2),
            "results": self.results
        }
        
        # Save report
        report_file = self.test_dir / "test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📊 Test Report Generated:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Report saved: {report_file}")
        
        return report

async def main():
    print("🧪 Threads Account Switching Test")
    print("=" * 50)
    
    # Test configuration
    test_device_udid = "df44ce18dfdd9d0ffd2420fb9fc0176a7b6bd64e"
    test_platform = "threads"
    test_accounts = ["carlarrivera4921647", "ap5aihm4"]
    
    # Configure device in Appium service
    from services.appium_service import appium_service
    device_caps = {
        'udid': test_device_udid,
        'platform': 'iOS',
        'name': 'Phone9',
        'os_version': '16.7.11',
        'appium_port': 4735,
        'wda_port': 8100
    }
    appium_service.device_capabilities[test_device_udid] = device_caps
    appium_service.server_url = 'http://localhost:4735'
    
    print(f"🔧 Configuring device: {test_device_udid}")
    print(f"✅ Device configured. Available devices: {list(appium_service.device_capabilities.keys())}")
    
    # Create test instance
    test = AccountSwitchingTest()
    test.create_test_directory()
    
    print(f"🎯 Testing with device: {test_device_udid}")
    print(f"🎯 Target accounts: {', '.join(test_accounts)}")
    
    print(f"\n{'=' * 20} INDIVIDUAL TESTS {'=' * 20}")
    
    # Test 1: Launch Threads
    success, message = await test.test_launch_threads(test_device_udid)
    test.results.append({"test": "launch_threads", "success": success, "message": message})
    
    # Test 2: Navigate to profile
    success, message = await test.test_navigate_to_profile(test_device_udid)
    test.results.append({"test": "navigate_to_profile", "success": success, "message": message})
    
    # Test 3: Open account switcher
    success, message, current_username = await test.test_open_account_switcher(test_device_udid)
    test.results.append({"test": "open_account_switcher", "success": success, "message": message})
    
    # Test 4: Get available accounts (excluding current)
    success, message, accounts = await test.test_get_available_accounts(test_device_udid, current_username)
    test.results.append({"test": "get_available_accounts", "success": success, "message": message})
    
    # Use the available accounts (already filtered to exclude current)
    switchable_accounts = []
    if accounts:
        # Use all available accounts (current account already filtered out)
        switchable_accounts = accounts
    
    if not switchable_accounts:
        print(f"⚠️ No switchable accounts found, will test switching to: {test_accounts}")
        switchable_accounts = test_accounts
    
    # Test 5: Switch to each switchable account
    for account in switchable_accounts:
        username = account.get('username', account) if isinstance(account, dict) else account
        success, message = await test.test_switch_to_account(test_device_udid, username)
        test.results.append({"test": f"switch_to_account_{username}", "success": success, "message": message})
        
        # Navigate back to profile for next test
        await asyncio.sleep(2)
        await test.test_navigate_to_profile(test_device_udid)
        await asyncio.sleep(2)
        await test.test_open_account_switcher(test_device_udid)
        await asyncio.sleep(2)
    
    print(f"\n{'=' * 20} COMPLETE FLOW TESTS {'=' * 20}")
    
    # Test 6: Complete flow test
    target_account = switchable_accounts[0] if switchable_accounts else test_accounts[0]
    username = target_account.get('username', target_account) if isinstance(target_account, dict) else target_account
    success, message = await test.test_complete_flow(test_device_udid, username)
    test.results.append({"test": f"complete_flow_{username}", "success": success, "message": message})
    
    print(f"\n{'=' * 20} TEST COMPLETE {'=' * 20}")
    
    # Generate report
    test.generate_test_report()
    
    print(f"\n✅ All tests completed! Check evidence folder: {test.test_dir}")

if __name__ == "__main__":
    asyncio.run(main())