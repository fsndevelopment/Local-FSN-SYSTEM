#!/usr/bin/env python3
"""
Instagram Account Switching Test
Desktop test following the same checkpoint structure as previous tests
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the backend API to the path
sys.path.append('/Users/janvorlicek/Desktop/FSN-APPIUM-main/backend-appium-integration/api')

from services.instagram_account_switching import instagram_account_switching

class AccountSwitchingTest:
    def __init__(self):
        self.test_name = "instagram_account_switching"
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
            
        self.results.append(checkpoint)
        print(f"✅ Checkpoint saved: {filename_prefix}")
        return checkpoint
        
    async def test_launch_instagram(self, device_udid: str):
        """Test 1: Launch Instagram homepage"""
        print(f"\n🚀 Test 1: Launch Instagram on {device_udid}")
        
        try:
            result = await instagram_account_switching.launch_instagram_homepage(device_udid)
            
            if result['success']:
                print("✅ Instagram launched successfully")
                checkpoint = self.save_checkpoint("launch_instagram_homepage", True, result)
                return True
            else:
                print(f"❌ Instagram launch failed: {result['message']}")
                checkpoint = self.save_checkpoint("launch_instagram_homepage", False, result)
                return False
                
        except Exception as e:
            print(f"❌ Exception during Instagram launch: {e}")
            checkpoint = self.save_checkpoint("launch_instagram_homepage", False, {"error": str(e)})
            return False
    
    async def test_navigate_to_profile(self, device_udid: str):
        """Test 2: Navigate to profile tab"""
        print(f"\n👤 Test 2: Navigate to profile tab on {device_udid}")
        
        try:
            result = await instagram_account_switching.navigate_to_profile_tab(device_udid)
            
            if result['success']:
                print("✅ Successfully navigated to profile tab")
                checkpoint = self.save_checkpoint("navigate_to_profile_tab", True, result)
                return True
            else:
                print(f"❌ Profile navigation failed: {result['message']}")
                checkpoint = self.save_checkpoint("navigate_to_profile_tab", False, result)
                return False
                
        except Exception as e:
            print(f"❌ Exception during profile navigation: {e}")
            checkpoint = self.save_checkpoint("navigate_to_profile_tab", False, {"error": str(e)})
            return False
    
    async def test_open_account_switcher(self, device_udid: str):
        """Test 3: Open account switcher dropdown"""
        print(f"\n🔄 Test 3: Open account switcher on {device_udid}")
        
        try:
            result = await instagram_account_switching.open_account_switcher(device_udid)
            
            if result['success']:
                print("✅ Account switcher opened successfully")
                checkpoint = self.save_checkpoint("open_account_switcher", True, result)
                return True
            else:
                print(f"❌ Account switcher failed: {result['message']}")
                checkpoint = self.save_checkpoint("open_account_switcher", False, result)
                return False
                
        except Exception as e:
            print(f"❌ Exception during account switcher: {e}")
            checkpoint = self.save_checkpoint("open_account_switcher", False, {"error": str(e)})
            return False
    
    async def test_get_available_accounts(self, device_udid: str):
        """Test 4: Get available accounts"""
        print(f"\n📋 Test 4: Get available accounts on {device_udid}")
        
        try:
            result = await instagram_account_switching.get_available_accounts(device_udid)
            
            if result['success']:
                accounts = result['data']['accounts']
                print(f"✅ Found {len(accounts)} available accounts:")
                for i, account in enumerate(accounts, 1):
                    print(f"   {i}. {account['username']}")
                
                checkpoint = self.save_checkpoint("get_available_accounts", True, result)
                return result  # Return the full result object, not just accounts
            else:
                print(f"❌ Get accounts failed: {result['message']}")
                checkpoint = self.save_checkpoint("get_available_accounts", False, result)
                return result  # Return the full result object even on failure
                
        except Exception as e:
            print(f"❌ Exception during get accounts: {e}")
            checkpoint = self.save_checkpoint("get_available_accounts", False, {"error": str(e)})
            return []
    
    async def test_switch_to_account(self, device_udid: str, target_username: str):
        """Test 5: Switch to specific account"""
        print(f"\n🔄 Test 5: Switch to account '{target_username}' on {device_udid}")
        
        try:
            result = await instagram_account_switching.switch_to_account(device_udid, target_username)
            
            if result['success']:
                print(f"✅ Successfully switched to account: {target_username}")
                checkpoint = self.save_checkpoint(f"switch_to_account_{target_username}", True, result)
                return True
            else:
                print(f"❌ Account switch failed: {result['message']}")
                checkpoint = self.save_checkpoint(f"switch_to_account_{target_username}", False, result)
                return False
                
        except Exception as e:
            print(f"❌ Exception during account switch: {e}")
            checkpoint = self.save_checkpoint(f"switch_to_account_{target_username}", False, {"error": str(e)})
            return False
    
    async def test_close_account_switcher(self, device_udid: str):
        """Test closing account switcher"""
        print(f"🔒 Close account switcher on {device_udid}")
        
        try:
            result = await instagram_account_switching.close_account_switcher(device_udid)
            
            if result['success']:
                print(f"✅ Account switcher closed successfully")
                checkpoint = self.save_checkpoint("close_account_switcher", True, result)
                return True
            else:
                print(f"❌ Close switcher failed: {result['message']}")
                checkpoint = self.save_checkpoint("close_account_switcher", False, result)
                return False
                
        except Exception as e:
            print(f"❌ Exception during close switcher: {e}")
            checkpoint = self.save_checkpoint("close_account_switcher", False, {"error": str(e)})
            return False
    
    async def test_complete_flow(self, device_udid: str, target_username: str):
        """Test 6: Complete account switching flow"""
        print(f"\n🎯 Test 6: Complete flow to switch to '{target_username}' on {device_udid}")
        
        try:
            result = await instagram_account_switching.complete_account_switch_flow(device_udid, target_username)
            
            if result['success']:
                print(f"✅ Complete flow successful for account: {target_username}")
                checkpoint = self.save_checkpoint(f"complete_flow_{target_username}", True, result)
                return True
            else:
                print(f"❌ Complete flow failed: {result['message']}")
                checkpoint = self.save_checkpoint(f"complete_flow_{target_username}", False, result)
                return False
                
        except Exception as e:
            print(f"❌ Exception during complete flow: {e}")
            checkpoint = self.save_checkpoint(f"complete_flow_{target_username}", False, {"error": str(e)})
            return False
    
    def generate_test_report(self):
        """Generate test report"""
        report_file = self.test_dir / "test_report.json"
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        
        report = {
            "test_name": self.test_name,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": failed_tests,
                "success_rate": f"{(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            "results": self.results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📊 Test Report Generated:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {report['summary']['success_rate']}")
        print(f"   Report saved: {report_file}")
        
        return report

async def main():
    """Main test execution"""
    print("🧪 Instagram Account Switching Test")
    print("=" * 50)
    
    # Test configuration
    test_device_udid = "df44ce18dfdd9d0ffd2420fb9fc0176a7b6bd64e"  # Phone9 (connected)
    test_accounts = [
        "linaaarogers11439",
        "alexanderrfitzgerald2676740", 
        "carlarrivera4921647"
    ]
    
    # Configure device in Appium service
    print(f"🔧 Configuring device: {test_device_udid}")
    device_caps = {
        'udid': test_device_udid,
        'platform': 'iOS',
        'name': 'Phone9',
        'os_version': '16.7.11',
        'appium_port': 4735,
        'wda_port': 8100
    }
    
    # Add device to capabilities and update server URL
    from services.appium_service import appium_service
    appium_service.device_capabilities[test_device_udid] = device_caps
    appium_service.server_url = 'http://localhost:4735'
    print(f"✅ Device configured. Available devices: {list(appium_service.device_capabilities.keys())}")
    
    # Initialize test
    test = AccountSwitchingTest()
    test.create_test_directory()
    
    print(f"🎯 Testing with device: {test_device_udid}")
    print(f"🎯 Target accounts: {', '.join(test_accounts)}")
    
    # Run individual tests
    print(f"\n{'='*20} INDIVIDUAL TESTS {'='*20}")
    
    # Test 1: Launch Instagram
    await test.test_launch_instagram(test_device_udid)
    await asyncio.sleep(2)
    
    # Test 2: Navigate to profile
    await test.test_navigate_to_profile(test_device_udid)
    await asyncio.sleep(2)
    
    # Test 3: Open switcher
    await test.test_open_account_switcher(test_device_udid)
    await asyncio.sleep(2)
    
    # Test 4: Get available accounts
    accounts_result = await test.test_get_available_accounts(test_device_udid)
    await asyncio.sleep(2)
    
    # Determine which accounts to test switching to
    switchable_accounts = []
    if accounts_result and accounts_result.get('success') and accounts_result.get('data', {}).get('accounts'):
        available_accounts = accounts_result['data']['accounts']
        print(f"✅ Found {len(available_accounts)} accounts:")
        for i, acc in enumerate(available_accounts):
            username = acc.get('username', acc) if isinstance(acc, dict) else acc
            print(f"   {i+1}. {username}")
        
        # Skip the first account (currently active) and test switching to others
        if len(available_accounts) > 1:
            current_account = available_accounts[0]
            current_username = current_account.get('username', current_account) if isinstance(current_account, dict) else current_account
            switchable_accounts = available_accounts[1:]  # Skip the first (current) account
            # Extract usernames for display
            switchable_usernames = [acc.get('username', acc) if isinstance(acc, dict) else acc for acc in switchable_accounts]
            print(f"🔄 Current account: {current_username}")
            print(f"🔄 Will test switching to: {switchable_usernames}")
        else:
            switchable_accounts = []
            print("⚠️ Only one account available, no switching possible")
    else:
        # Fallback to test accounts, but skip the first one
        switchable_accounts = test_accounts[1:] if len(test_accounts) > 1 else []
        print(f"⚠️ Using fallback accounts, will test switching to: {switchable_accounts}")
    
    # If no switchable accounts found, skip the switching tests
    if not switchable_accounts:
        print("⚠️ No accounts available for switching, skipping individual switch tests")
        switchable_accounts = []
    
    # Test 5: Switch to each switchable account (switcher should already be open)
    for account in switchable_accounts:
        # Extract username from account object
        username = account.get('username', account) if isinstance(account, dict) else account
        await test.test_switch_to_account(test_device_udid, username)
        await asyncio.sleep(2)
        
        # After switching, we're automatically on the new account's profile page
        # Navigate back to profile tab for next account switch test (in case we're not there)
        await test.test_navigate_to_profile(test_device_udid)
        await asyncio.sleep(2)
        
        # Open switcher again for next account
        await test.test_open_account_switcher(test_device_udid)
        await asyncio.sleep(2)
    
    # Run complete flow tests
    print(f"\n{'='*20} COMPLETE FLOW TESTS {'='*20}")
    
    # Use the same switchable accounts for complete flow tests
    for account in switchable_accounts:
        # Extract username from account object
        username = account.get('username', account) if isinstance(account, dict) else account
        await test.test_complete_flow(test_device_udid, username)
        await asyncio.sleep(3)
    
    # Generate report
    print(f"\n{'='*20} TEST COMPLETE {'='*20}")
    test.generate_test_report()
    
    print(f"\n✅ All tests completed! Check evidence folder: {test.test_dir}")

if __name__ == "__main__":
    asyncio.run(main())
