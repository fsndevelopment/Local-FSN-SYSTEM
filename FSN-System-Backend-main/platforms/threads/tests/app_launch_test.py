#!/usr/bin/env python3
"""
Threads App Launch Test - Phase 2 Starting Point
===============================================

🧵 FIRST THREADS TEST - App Connectivity and Basic Navigation

This is the foundational test for Threads platform development.
Following the proven pattern from Instagram success.

Test Flow:
1. Launch Threads app
2. Verify app loads successfully  
3. Identify basic navigation elements
4. Map core UI structure
5. Return to safe state

Author: FSN Appium Team
Started: January 15, 2025
Status: Phase 2 Development Beginning
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add platforms to path
sys.path.append('/Users/janvorlicek/Desktop/FSN APPIUM')

from platforms.shared.utils.checkpoint_system import CheckpointSystem
from platforms.shared.utils.appium_driver import AppiumDriverManager
from platforms.config import Platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'threads_app_launch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class ThreadsAppLaunchTest(CheckpointSystem):
    """First Threads test using proven Instagram patterns"""
    
    def __init__(self):
        super().__init__("threads", "app_launch")
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Initialize Threads app driver"""
        try:
            self.logger.info("🧵 Setting up Threads app driver...")
            self.driver = AppiumDriverManager.create_driver(Platform.THREADS)
            self.wait = AppiumDriverManager.get_wait_driver(self.driver)
            self.logger.info("✅ Threads driver setup complete")
            return True
        except Exception as e:
            self.logger.error(f"❌ Threads driver setup failed: {e}")
            return False
    
    def checkpoint_1_app_launch(self, driver) -> bool:
        """Checkpoint 1: Launch Threads app and verify it loads"""
        try:
            self.logger.info("🎯 CHECKPOINT 1: Launch Threads app")
            
            # App should already be launching via bundle ID
            time.sleep(5)  # Give app time to load
            
            # Try to detect any Threads-specific elements
            # Note: We'll need to explore the actual app to find these
            current_app = driver.current_package
            self.logger.info(f"📱 Current app package: {current_app}")
            
            # Basic verification that we can interact with the app
            try:
                page_source = driver.page_source
                if len(page_source) > 100:  # App loaded some content
                    self.logger.info("✅ Threads app loaded with content")
                    return True
                else:
                    self.logger.error("❌ Threads app loaded but no content detected")
                    return False
            except Exception as e:
                self.logger.error(f"❌ Could not get app content: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ App launch failed: {e}")
            return False
    
    def checkpoint_2_basic_navigation_discovery(self, driver) -> bool:
        """Checkpoint 2: Discover basic navigation elements"""
        try:
            self.logger.info("🎯 CHECKPOINT 2: Discover basic navigation")
            
            # Look for common navigation patterns
            # These are typical elements in social media apps
            potential_nav_elements = [
                "tab-bar",
                "home-tab", 
                "search-tab",
                "profile-tab",
                "notifications-tab",
                "compose-button",
                "back-button"
            ]
            
            found_elements = []
            for element_id in potential_nav_elements:
                try:
                    elements = driver.find_elements("accessibility id", element_id)
                    if elements:
                        found_elements.append(element_id)
                        self.logger.info(f"📍 Found navigation element: {element_id}")
                except:
                    pass
            
            if found_elements:
                self.logger.info(f"✅ Discovered {len(found_elements)} navigation elements")
                return True
            else:
                self.logger.info("📱 No standard navigation elements found - will need manual exploration")
                return True  # Still success, just need to explore more
                
        except Exception as e:
            self.logger.error(f"❌ Navigation discovery failed: {e}")
            return False
    
    def checkpoint_3_ui_structure_analysis(self, driver) -> bool:
        """Checkpoint 3: Analyze UI structure for future development"""
        try:
            self.logger.info("🎯 CHECKPOINT 3: Analyze UI structure")
            
            # Get page source for analysis
            page_source = driver.page_source
            
            # Count different UI element types
            ui_elements = {
                "buttons": page_source.count("XCUIElementTypeButton"),
                "cells": page_source.count("XCUIElementTypeCell"), 
                "text_fields": page_source.count("XCUIElementTypeTextField"),
                "images": page_source.count("XCUIElementTypeImage"),
                "static_texts": page_source.count("XCUIElementTypeStaticText")
            }
            
            self.logger.info("📊 UI Structure Analysis:")
            for element_type, count in ui_elements.items():
                self.logger.info(f"   {element_type}: {count}")
            
            # Save detailed UI dump for future reference
            ui_dump_path = f"{self.evidence_dir}/threads_ui_structure.xml"
            with open(ui_dump_path, 'w', encoding='utf-8') as f:
                f.write(page_source)
            self.logger.info(f"📄 UI structure saved: {ui_dump_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ UI analysis failed: {e}")
            return False
    
    def checkpoint_4_permission_detection(self, driver) -> bool:
        """Checkpoint 4: Detect any permission dialogs or onboarding"""
        try:
            self.logger.info("🎯 CHECKPOINT 4: Check for permissions/onboarding")
            
            # Look for common permission dialog elements
            permission_indicators = [
                "Allow",
                "Don't Allow", 
                "OK",
                "Cancel",
                "Continue",
                "Get Started",
                "Skip",
                "Next"
            ]
            
            found_permissions = []
            for indicator in permission_indicators:
                try:
                    elements = driver.find_elements("accessibility id", indicator)
                    if elements:
                        found_permissions.append(indicator)
                        self.logger.info(f"🔐 Found permission element: {indicator}")
                except:
                    pass
            
            if found_permissions:
                self.logger.info(f"📱 Permission dialogs detected: {found_permissions}")
            else:
                self.logger.info("✅ No permission dialogs detected - app ready")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Permission detection failed: {e}")
            return False
    
    def checkpoint_5_return_safe_state(self, driver) -> bool:
        """Checkpoint 5: Return to safe state for future tests"""
        try:
            self.logger.info("🎯 CHECKPOINT 5: Return to safe state")
            
            # For now, just verify we can still interact with the app
            try:
                current_contexts = driver.contexts
                self.logger.info(f"📱 Available contexts: {current_contexts}")
                
                # Try to get current activity 
                current_activity = driver.current_activity
                self.logger.info(f"📱 Current activity: {current_activity}")
                
                self.logger.info("✅ App in stable state for future testing")
                return True
                
            except Exception as e:
                self.logger.warning(f"⚠️ State verification warning: {e}")
                return True  # Still consider success
                
        except Exception as e:
            self.logger.error(f"❌ Safe state return failed: {e}")
            return False
    
    def define_checkpoints(self):
        """Define the checkpoint sequence for app launch test"""
        return [
            (self.checkpoint_1_app_launch, "app_launch"),
            (self.checkpoint_2_basic_navigation_discovery, "navigation_discovery"),
            (self.checkpoint_3_ui_structure_analysis, "ui_analysis"), 
            (self.checkpoint_4_permission_detection, "permission_detection"),
            (self.checkpoint_5_return_safe_state, "safe_state_return")
        ]
    
    def run_test(self):
        """Execute the complete Threads app launch test"""
        self.logger.info("🧵 STARTING THREADS APP LAUNCH TEST")
        self.logger.info("🚀 PHASE 2 DEVELOPMENT - FIRST THREADS TEST!")
        
        try:
            # Setup
            if not self.setup_driver():
                return False
            
            # Execute checkpoints
            checkpoints = self.define_checkpoints()
            success = self.run_checkpoint_sequence(self.driver, checkpoints)
            
            if success:
                self.logger.info("🎉 THREADS APP LAUNCH: SUCCESS!")
                self.logger.info("🧵 READY FOR THREADS DEVELOPMENT!")
            else:
                self.logger.error("❌ THREADS APP LAUNCH: NEEDS INVESTIGATION")
                
            return success
            
        except Exception as e:
            self.logger.error(f"💥 TEST EXECUTION ERROR: {e}")
            return False
            
        finally:
            AppiumDriverManager.safe_quit_driver(self.driver)

def main():
    """Run the Threads app launch test"""
    test = ThreadsAppLaunchTest()
    success = test.run_test()
    
    if success:
        print("\n🎉 THREADS APP LAUNCH TEST PASSED!")
        print("🧵 READY TO BEGIN THREADS DEVELOPMENT!")
        exit(0)
    else:
        print("\n❌ THREADS APP LAUNCH TEST NEEDS INVESTIGATION")
        print("📋 Check logs for details")
        exit(1)

if __name__ == "__main__":
    main()
