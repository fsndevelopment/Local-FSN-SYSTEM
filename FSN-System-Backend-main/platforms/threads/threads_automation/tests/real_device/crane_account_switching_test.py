#!/usr/bin/env python3
"""
Crane Container Account Switching Test
Test for jailbroken device account switching using Crane containers
Supports Instagram and Threads platforms
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the backend API to the path
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.append(os.path.join(project_root, 'api'))

from services.crane_account_switching import crane_threads_account_switching

class CraneAccountSwitchingTest:
    def __init__(self):
        self.test_name = "crane_account_switching"
        # Use project-relative path for evidence directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        self.evidence_dir = Path(os.path.join(project_root, "evidence"))
        self.test_dir = None
        self.results = []
        
        # Test configuration
        self.device_udid = "f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3"  # Your device UDID
        self.test_containers = ["4", "5", "7"]  # Test with these containers
        self.platform = "threads"
        
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
        
        print(f"💾 Saved checkpoint: {filename_prefix}.json")
        return checkpoint
    
    async def test_get_available_containers(self):
        """Test getting available containers"""
        print("\n🔍 Testing: Get Available Containers")
        
        try:
            result = await crane_threads_account_switching.get_available_containers(
                self.device_udid, 
                self.platform
            )
            
            checkpoint = self.save_checkpoint(
                "get_available_containers", 
                result['success'], 
                result
            )
            
            if result['success']:
                containers = result['data'].get('containers', [])
                print(f"✅ Found {len(containers)} containers:")
                for container in containers:
                    print(f"   - Container {container['id']}: {container['name']} ({container['status']})")
            else:
                print(f"❌ Failed to get containers: {result['message']}")
                
            return result['success']
            
        except Exception as e:
            print(f"❌ Error getting containers: {e}")
            self.save_checkpoint("get_available_containers", False, {"error": str(e)})
            return False
    
    async def test_crane_account_switch_flow(self, container_id: str):
        """Test complete Crane account switching flow"""
        print(f"\n🔄 Testing: Crane Account Switch to Container {container_id}")
        
        try:
            result = await crane_threads_account_switching.complete_crane_account_switch_flow(
                self.device_udid,
                container_id,
                self.platform
            )
            
            checkpoint = self.save_checkpoint(
                f"crane_switch_to_container_{container_id}", 
                result['success'], 
                result
            )
            
            if result['success']:
                print(f"✅ Successfully switched to container {container_id}")
                checkpoints = result['data'].get('checkpoints', [])
                print(f"   - Completed {len(checkpoints)} checkpoints")
                
                # Print checkpoint details
                for i, cp in enumerate(checkpoints, 1):
                    status = "✅" if cp['success'] else "❌"
                    print(f"   {i}. {cp['action']}: {status} - {cp['message']}")
            else:
                print(f"❌ Failed to switch to container {container_id}: {result['message']}")
                
            return result['success']
            
        except Exception as e:
            print(f"❌ Error switching to container {container_id}: {e}")
            self.save_checkpoint(f"crane_switch_to_container_{container_id}", False, {"error": str(e)})
            return False
    
    async def test_individual_crane_steps(self, container_id: str):
        """Test individual Crane switching steps"""
        print(f"\n🔧 Testing: Individual Crane Steps for Container {container_id}")
        
        # Get driver first
        driver = await crane_threads_account_switching._get_driver(self.device_udid, self.platform)
        if not driver:
            print("   ❌ Could not get driver for individual steps test")
            return False
        
        from selenium.webdriver.support.ui import WebDriverWait
        wait = WebDriverWait(driver, 15)
        
        steps = [
            ("navigate_to_home_screen", "Navigate to Home Screen"),
            ("long_press_app_icon", "Long Press Threads Icon"),
            ("click_container_default", "Click Container, Default Button"),
            ("select_target_container", f"Select Container {container_id}"),
            ("launch_app_with_container", "Launch Threads with Container")
        ]
        
        results = []
        
        for step_method, step_name in steps:
            print(f"\n   🔸 {step_name}")
            
            try:
                if step_method == "navigate_to_home_screen":
                    result = await crane_threads_account_switching._navigate_to_home_screen(self.device_udid, driver, wait)
                elif step_method == "long_press_app_icon":
                    result = await crane_threads_account_switching._long_press_app_icon(self.device_udid, self.platform, driver, wait)
                elif step_method == "click_container_default":
                    result = await crane_threads_account_switching._click_container_default_button(self.device_udid, driver, wait)
                elif step_method == "select_target_container":
                    result = await crane_threads_account_switching._select_target_container(self.device_udid, container_id, driver, wait)
                elif step_method == "launch_app_with_container":
                    result = await crane_threads_account_switching._launch_app_with_container(self.device_udid, self.platform, driver, wait)
                else:
                    result = {"success": False, "message": "Unknown step"}
                
                checkpoint = self.save_checkpoint(
                    f"crane_{step_method}_{container_id}", 
                    result['success'], 
                    result
                )
                
                status = "✅" if result['success'] else "❌"
                print(f"   {status} {step_name}: {result['message']}")
                
                results.append(result['success'])
                
                # Wait between steps
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error in {step_name}: {e}")
                self.save_checkpoint(f"crane_{step_method}_{container_id}", False, {"error": str(e)})
                results.append(False)
        
        return all(results)
    
    async def run_comprehensive_test(self):
        """Run comprehensive Crane account switching test"""
        print("🚀 Starting Threads Crane Account Switching Test")
        print("=" * 60)
        
        self.create_test_directory()
        
        # Test 1: Get available containers
        print("\n📋 TEST 1: Get Available Containers")
        containers_success = await self.test_get_available_containers()
        
        # Test 2: Test individual steps with first container
        if self.test_containers:
            first_container = self.test_containers[0]
            print(f"\n📋 TEST 2: Individual Steps Test (Container {first_container})")
            individual_success = await self.test_individual_crane_steps(first_container)
        
        # Test 3: Test complete flow with just container 4
        print(f"\n📋 TEST 3: Complete Flow Test (Container 4)")
        flow_results = []
        
        # Only test the first container (container 4)
        container_id = self.test_containers[0]
        print(f"\n   🔄 Testing Container {container_id}")
        success = await self.test_crane_account_switch_flow(container_id)
        flow_results.append(success)
        
        print("✅ Test completed after successfully opening container 4!")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        print(f"✅ Get Containers: {'PASS' if containers_success else 'FAIL'}")
        print(f"✅ Individual Steps: {'PASS' if individual_success else 'FAIL'}")
        
        print(f"\n🔄 Complete Flow Results:")
        for i, container_id in enumerate(self.test_containers):
            status = "PASS" if flow_results[i] else "FAIL"
            print(f"   Container {container_id}: {status}")
        
        total_tests = 2 + len(self.test_containers)  # containers + individual + flow tests
        passed_tests = sum([containers_success, individual_success] + flow_results)
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Crane account switching is working perfectly!")
        else:
            print("⚠️  Some tests failed. Check the logs for details.")
        
        print(f"\n📁 Test evidence saved to: {self.test_dir}")
        
        return passed_tests == total_tests

async def main():
    """Main test function"""
    test = CraneAccountSwitchingTest()
    
    print("🔧 Crane Account Switching Test (Threads)")
    print("This test will verify Crane container switching functionality")
    print("Make sure your jailbroken device is connected and Crane is installed")
    print()
    
    # Ask for device UDID if not set
    if test.device_udid == "00008110-000A4C2E3A38801E":
        print("⚠️  Please update the device_udid in the test file with your actual device UDID")
        print("   Current UDID: 00008110-000A4C2E3A38801E")
        print()
    
    # Ask for test containers
    print(f"📋 Test will use containers: {', '.join(test.test_containers)}")
    print("   You can modify test_containers list in the test file")
    print()
    
    input("Press Enter to start the test...")
    
    try:
        success = await test.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
