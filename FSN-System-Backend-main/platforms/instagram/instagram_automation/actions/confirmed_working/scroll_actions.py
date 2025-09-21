#!/usr/bin/env python3
"""
Instagram Scrolling Actions - Phase 5 Implementation
====================================================

📱 INSTAGRAM SCROLLING SYSTEM - Smart Content Discovery

Following proven Instagram patterns with comprehensive scrolling functionality.

Features:
- Home feed scrolling with content detection
- Reels page scrolling with engagement tracking
- Smart scrolling logic with human-like patterns
- Scroll depth tracking and performance metrics
- Content interaction during scroll

Author: FSN Appium Team
Started: January 15, 2025
Status: Phase 5 Scrolling System Implementation
"""

import sys
import os
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add platforms to path
sys.path.append('/Users/janvorlicek/Desktop/FSN-APPIUM-main/backend-appium-integration')

from platforms.shared.utils.checkpoint_system import CheckpointSystem
from platforms.shared.utils.appium_driver import AppiumDriverManager
from platforms.config import Platform
from appium.webdriver.common.appiumby import AppiumBy

class InstagramScrollActions(CheckpointSystem):
    """Instagram scrolling implementation using proven patterns"""
    
    def __init__(self, scroll_type: str = "home_feed"):
        super().__init__("instagram", f"scroll_{scroll_type}")
        self.driver = None
        self.scroll_type = scroll_type
        self.scroll_count = 0
        self.content_found = []
        self.scroll_metrics = {
            "total_scrolls": 0,
            "content_discovered": 0,
            "interactions_performed": 0,
            "scroll_depth": 0,
            "start_time": None,
            "end_time": None
        }
        
    def setup_driver(self):
        """Initialize driver and launch Instagram app"""
        try:
            self.logger.info("📱 Setting up driver and launching Instagram...")
            
            from platforms.config import DEVICE_CONFIG
            from appium.options.ios import XCUITestOptions
            from appium import webdriver
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = DEVICE_CONFIG["udid"]
            options.bundle_id = "com.burbn.instagram"
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.wda_local_port = DEVICE_CONFIG["wda_port"]
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            
            self.driver = webdriver.Remote(f"http://localhost:{DEVICE_CONFIG['appium_port']}", options=options)
            self.wait = AppiumDriverManager.get_wait_driver(self.driver)
            
            self.logger.info("✅ Driver setup complete - Instagram ready")
            return True
        except Exception as e:
            self.logger.error(f"❌ Driver setup failed: {e}")
            return False
    
    def checkpoint_1_navigate_to_target_page(self, driver) -> bool:
        """Checkpoint 1: Navigate to target page (home feed or reels)"""
        try:
            self.logger.info(f"🎯 CHECKPOINT 1: Navigate to {self.scroll_type}")
            
            # Wait for app to fully load
            self.logger.info("⏳ Waiting for Instagram to fully load...")
            time.sleep(5)
            
            # Check current page source for debugging
            page_source = driver.page_source
            self.logger.info(f"📱 Current page source length: {len(page_source)}")
            
            if self.scroll_type == "home_feed":
                # Try to find home feed tab with multiple selectors
                home_tab = None
                selectors = ["mainfeed-tab", "Home", "home-tab", "feed-tab"]
                
                for selector in selectors:
                    try:
                        self.logger.info(f"🔍 Trying selector: {selector}")
                        home_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, selector)
                        self.logger.info(f"✅ Found home tab with selector: {selector}")
                        break
                    except Exception as e:
                        self.logger.info(f"❌ Selector {selector} failed: {e}")
                        continue
                
                if home_tab:
                    home_tab.click()
                    time.sleep(3)
                    self.logger.info("✅ Navigated to home feed")
                else:
                    self.logger.error("❌ Could not find home feed tab with any selector")
                    return False
                
            elif self.scroll_type == "reels":
                # Try to find reels tab with multiple selectors
                reels_tab = None
                selectors = ["reels-tab", "Reels", "reel-tab"]
                
                for selector in selectors:
                    try:
                        self.logger.info(f"🔍 Trying selector: {selector}")
                        reels_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, selector)
                        self.logger.info(f"✅ Found reels tab with selector: {selector}")
                        break
                    except Exception as e:
                        self.logger.info(f"❌ Selector {selector} failed: {e}")
                        continue
                
                if reels_tab:
                    reels_tab.click()
                    time.sleep(3)
                    self.logger.info("✅ Navigated to reels page")
                else:
                    self.logger.error("❌ Could not find reels tab with any selector")
                    return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Navigation to {self.scroll_type} failed: {e}")
            return False
    
    def checkpoint_2_identify_scroll_area(self, driver) -> bool:
        """Checkpoint 2: Identify the scrollable area"""
        try:
            self.logger.info("🎯 CHECKPOINT 2: Identify scrollable area")
            
            # Get screen dimensions for scroll calculations
            screen_size = driver.get_window_size()
            self.screen_width = screen_size['width']
            self.screen_height = screen_size['height']
            
            # Calculate scroll parameters - 70-80% of screen height
            self.scroll_start_y = int(self.screen_height * 0.8)  # Start from 80% down
            self.scroll_end_y = int(self.screen_height * 0.1)    # End at 10% down
            self.scroll_x = int(self.screen_width * 0.5)         # Center horizontally
            
            self.logger.info(f"📱 Screen: {self.screen_width}x{self.screen_height}")
            self.logger.info(f"📜 Scroll: Y {self.scroll_start_y} → {self.scroll_end_y}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Scroll area identification failed: {e}")
            return False
    
    def checkpoint_3_initial_content_scan(self, driver) -> bool:
        """Checkpoint 3: Scan for initial content before scrolling"""
        try:
            self.logger.info("🎯 CHECKPOINT 3: Initial content scan")
            
            # Look for content elements
            content_selectors = [
                "like-button",
                "comment-button", 
                "share-button",
                "save-button",
                "post-image",
                "reel-video"
            ]
            
            initial_content = {}
            for selector in content_selectors:
                try:
                    elements = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, selector)
                    if elements:
                        initial_content[selector] = len(elements)
                        self.logger.info(f"   Found {len(elements)} {selector}(s)")
                except:
                    pass
            
            self.initial_content_count = sum(initial_content.values())
            self.logger.info(f"📊 Initial content elements: {self.initial_content_count}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initial content scan failed: {e}")
            return False
    
    def checkpoint_4_execute_smart_scrolling(self, driver) -> bool:
        """Checkpoint 4: Execute smart scrolling with human-like patterns"""
        try:
            self.logger.info("🎯 CHECKPOINT 4: Execute smart scrolling")
            
            self.scroll_metrics["start_time"] = datetime.now()
            max_scrolls = 5  # Limit for testing
            
            for scroll_num in range(max_scrolls):
                self.logger.info(f"📜 Scroll {scroll_num + 1}/{max_scrolls}")
                
                # Human-like scroll variation - 60%+ of screen height with random variation
                # Faster scrolling for reels, slower for home feed
                if self.scroll_type == "reels":
                    scroll_duration = random.randint(400, 800)  # 0.4-0.8 seconds (faster for reels)
                else:
                    scroll_duration = random.randint(800, 1500)  # 0.8-1.5 seconds (normal for home feed)
                
                base_percentage = 0.6  # Start from 60%
                random_variation = random.uniform(0.0, 0.4)  # Add 0-40% more
                scroll_percentage = base_percentage + random_variation  # 60-100% of screen height
                scroll_distance = int(self.screen_height * scroll_percentage)
                
                # Calculate scroll coordinates
                start_y = self.scroll_start_y
                end_y = start_y - scroll_distance
                
                # Human mistake behavior - sometimes scroll up instead of down
                if random.random() < 0.10:  # 10% chance of "mistake"
                    self.logger.info("🤦 Human mistake: scrolling up instead of down")
                    # Scroll up (wrong direction)
                    mistake_distance = random.randint(100, 300)
                    driver.swipe(
                        self.scroll_x, start_y, 
                        self.scroll_x, start_y + mistake_distance, 
                        random.randint(300, 600)
                    )
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # Realize mistake and scroll down (correct direction)
                    self.logger.info("🔄 Correcting mistake: scrolling down")
                    driver.swipe(
                        self.scroll_x, start_y, 
                        self.scroll_x, end_y, 
                        scroll_duration
                    )
                else:
                    # Normal scroll down
                    driver.swipe(
                        self.scroll_x, start_y, 
                        self.scroll_x, end_y, 
                        scroll_duration
                    )
                
                # Human-like pause for content to load and "reading" time
                content_load_pause = random.uniform(1.5, 3.0)
                self.logger.info(f"⏳ Content load pause: {content_load_pause:.1f}s")
                time.sleep(content_load_pause)
                
                # Check for new content
                self._scan_for_content(driver, scroll_num + 1)
                
                # Human-like "reading" pause - 3-10 seconds randomly
                reading_pause = random.uniform(3.0, 10.0)
                self.logger.info(f"👀 Human reading pause: {reading_pause:.1f}s")
                time.sleep(reading_pause)
                
                # Additional random behavior - sometimes scroll back up slightly
                if random.random() < 0.2:  # 20% chance
                    back_scroll = random.randint(50, 150)
                    self.logger.info(f"↩️ Random back scroll: {back_scroll}px")
                    driver.swipe(
                        self.scroll_x, self.scroll_start_y - 100,
                        self.scroll_x, self.scroll_start_y - 100 + back_scroll,
                        random.randint(500, 800)
                    )
                    time.sleep(random.uniform(1.0, 2.0))
                
                self.scroll_count += 1
                self.scroll_metrics["total_scrolls"] = self.scroll_count
                
                # Check if we've reached bottom (optional)
                if self._detect_end_of_feed(driver):
                    self.logger.info("🔚 End of feed detected")
                    break
            
            self.scroll_metrics["end_time"] = datetime.now()
            self.logger.info(f"✅ Scrolling completed: {self.scroll_count} scrolls")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Smart scrolling failed: {e}")
            return False
    
    def _scan_for_content(self, driver, scroll_num: int):
        """Helper: Scan for content during scrolling"""
        try:
            content_selectors = ["like-button", "comment-button", "post-image"]
            new_content = 0
            
            for selector in content_selectors:
                try:
                    elements = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, selector)
                    if elements:
                        new_content += len(elements)
                except:
                    pass
            
            if new_content > 0:
                self.content_found.append({
                    "scroll_num": scroll_num,
                    "content_count": new_content,
                    "timestamp": datetime.now().isoformat()
                })
                self.scroll_metrics["content_discovered"] += new_content
                self.logger.info(f"   📱 Scroll {scroll_num}: Found {new_content} content elements")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Content scan error: {e}")
    
    def _detect_end_of_feed(self, driver) -> bool:
        """Helper: Detect if we've reached the end of the feed"""
        try:
            # Look for "You're all caught up" or similar indicators
            end_indicators = [
                "You're all caught up",
                "No more posts",
                "End of feed"
            ]
            
            page_source = driver.page_source
            for indicator in end_indicators:
                if indicator.lower() in page_source.lower():
                    return True
                    
            return False
        except:
            return False
    
    def checkpoint_5_content_interaction(self, driver) -> bool:
        """Checkpoint 5: Interact with discovered content"""
        try:
            self.logger.info("🎯 CHECKPOINT 5: Content interaction")
            
            interactions_performed = 0
            
            # Find like buttons and interact with some
            try:
                like_buttons = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "like-button")
                if like_buttons:
                    # Interact with first few like buttons
                    for i, button in enumerate(like_buttons[:3]):  # Limit to 3 interactions
                        try:
                            if button.is_enabled() and button.is_displayed():
                                button.click()
                                interactions_performed += 1
                                time.sleep(1)  # Brief pause between interactions
                        except:
                            pass
            except:
                pass
            
            self.scroll_metrics["interactions_performed"] = interactions_performed
            self.logger.info(f"✅ Performed {interactions_performed} content interactions")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Content interaction failed: {e}")
            return False
    
    def checkpoint_6_collect_scroll_metrics(self, driver) -> bool:
        """Checkpoint 6: Collect comprehensive scroll metrics"""
        try:
            self.logger.info("🎯 CHECKPOINT 6: Collect scroll metrics")
            
            # Calculate scroll depth
            self.scroll_metrics["scroll_depth"] = self.scroll_count * 300  # Approximate pixels
            
            # Calculate duration
            if self.scroll_metrics["start_time"] and self.scroll_metrics["end_time"]:
                duration = (self.scroll_metrics["end_time"] - self.scroll_metrics["start_time"]).total_seconds()
                self.scroll_metrics["duration_seconds"] = duration
                self.scroll_metrics["scrolls_per_minute"] = (self.scroll_count / duration) * 60 if duration > 0 else 0
            
            # Final metrics summary
            self.logger.info("📊 SCROLL METRICS SUMMARY:")
            self.logger.info(f"   Total scrolls: {self.scroll_metrics['total_scrolls']}")
            self.logger.info(f"   Content discovered: {self.scroll_metrics['content_discovered']}")
            self.logger.info(f"   Interactions performed: {self.scroll_metrics['interactions_performed']}")
            self.logger.info(f"   Scroll depth: {self.scroll_metrics['scroll_depth']} pixels")
            if 'duration_seconds' in self.scroll_metrics:
                self.logger.info(f"   Duration: {self.scroll_metrics['duration_seconds']:.1f} seconds")
                self.logger.info(f"   Scroll rate: {self.scroll_metrics['scrolls_per_minute']:.1f} scrolls/min")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Metrics collection failed: {e}")
            return False
    
    def checkpoint_7_return_to_safe_state(self, driver) -> bool:
        """Checkpoint 7: Return to safe state"""
        try:
            self.logger.info("🎯 CHECKPOINT 7: Return to safe state")
            
            # Ensure we're on home feed
            home_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "mainfeed-tab")
            home_tab.click()
            time.sleep(2)
            
            self.logger.info("✅ Returned to safe state (home feed)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Safe state return failed: {e}")
            return False
    
    def define_checkpoints(self):
        """Define the checkpoint sequence for scrolling test"""
        return [
            (self.checkpoint_1_navigate_to_target_page, "navigate_to_target_page"),
            (self.checkpoint_2_identify_scroll_area, "identify_scroll_area"),
            (self.checkpoint_3_initial_content_scan, "initial_content_scan"),
            (self.checkpoint_4_execute_smart_scrolling, "execute_smart_scrolling"),
            (self.checkpoint_5_content_interaction, "content_interaction"),
            (self.checkpoint_6_collect_scroll_metrics, "collect_scroll_metrics"),
            (self.checkpoint_7_return_to_safe_state, "return_to_safe_state")
        ]
    
    def run_scroll_test(self):
        """Execute the complete Instagram scrolling test"""
        self.logger.info(f"📱 STARTING INSTAGRAM {self.scroll_type.upper()} SCROLLING TEST")
        self.logger.info("🚀 PHASE 5 SCROLLING SYSTEM IMPLEMENTATION!")
        
        try:
            # Setup
            if not self.setup_driver():
                return False
            
            # Execute checkpoints
            checkpoints = self.define_checkpoints()
            success = self.run_checkpoint_sequence(self.driver, checkpoints)
            
            if success:
                self.logger.info(f"🎉 INSTAGRAM {self.scroll_type.upper()} SCROLLING: SUCCESS!")
                self.logger.info("📱 SCROLLING SYSTEM WORKING!")
                
                # Final summary
                self.logger.info(f"📊 Final scroll metrics: {self.scroll_metrics}")
                    
            else:
                self.logger.error(f"❌ INSTAGRAM {self.scroll_type.upper()} SCROLLING: NEEDS INVESTIGATION")
                
            return success
            
        except Exception as e:
            self.logger.error(f"💥 SCROLL TEST EXECUTION ERROR: {e}")
            return False
            
        finally:
            AppiumDriverManager.safe_quit_driver(self.driver)

def main():
    """Run Instagram scrolling tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Scrolling Test')
    parser.add_argument('--type', choices=['home_feed', 'reels'], default='home_feed',
                       help='Type of scrolling to test')
    
    args = parser.parse_args()
    
    test = InstagramScrollActions(args.type)
    success = test.run_scroll_test()
    
    if success:
        print(f"\n🎉 INSTAGRAM {args.type.upper()} SCROLLING TEST PASSED!")
        print("📱 SCROLLING SYSTEM IMPLEMENTED SUCCESSFULLY!")
        exit(0)
    else:
        print(f"\n❌ INSTAGRAM {args.type.upper()} SCROLLING TEST NEEDS INVESTIGATION")
        print("📋 Check logs for details")
        exit(1)

if __name__ == "__main__":
    main()
