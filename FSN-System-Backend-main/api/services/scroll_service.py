#!/usr/bin/env python3
"""
Scroll Service - Phase 5 Implementation
======================================

📱 SCROLLING SYSTEM SERVICE - Backend Integration

Comprehensive scrolling service for Instagram and Threads platforms.

Features:
- Platform-agnostic scrolling interface
- Smart scrolling with human-like patterns
- Content discovery and interaction
- Scroll metrics collection
- Integration with job execution system

Author: FSN Appium Team
Started: January 15, 2025
Status: Phase 5 Scrolling System Backend Integration
"""

import asyncio
import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy

from models.device import Device
from models.job import Job, JobType, JobStatus

logger = logging.getLogger(__name__)

class ScrollType(Enum):
    """Types of scrolling available"""
    HOME_FEED = "home_feed"
    REELS = "reels"
    THREADS_FEED = "threads_feed"

class ScrollService:
    """Comprehensive scrolling service for all platforms"""
    
    def __init__(self):
        self.active_scrolls = {}
        self.scroll_metrics = {}
        
    async def execute_scroll_job(self, job: Job, device: Device) -> Dict[str, Any]:
        """
        Execute a scrolling job on the specified device
        
        Args:
            job: Job object containing scroll parameters
            device: Device object to execute on
            
        Returns:
            Dict containing scroll results and metrics
        """
        try:
            logger.info(f"🎯 Starting scroll job {job.id} on device {device.name}")
            
            # Initialize scroll session
            session_id = f"scroll_{job.id}_{int(time.time())}"
            self.active_scrolls[session_id] = {
                "job_id": job.id,
                "device_id": device.id,
                "start_time": datetime.now(),
                "status": "running"
            }
            
            # Create driver
            driver = await self._create_driver(device)
            
            try:
                # Execute scrolling based on platform and type
                if device.platform == "instagram":
                    result = await self._execute_instagram_scroll(driver, job, session_id)
                elif device.platform == "threads":
                    result = await self._execute_threads_scroll(driver, job, session_id)
                else:
                    raise ValueError(f"Unsupported platform: {device.platform}")
                
                # Update job status
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                
                # Store metrics
                self.scroll_metrics[session_id] = result
                
                logger.info(f"✅ Scroll job {job.id} completed successfully")
                return result
                
            finally:
                # Cleanup
                if driver:
                    driver.quit()
                if session_id in self.active_scrolls:
                    del self.active_scrolls[session_id]
                    
        except Exception as e:
            logger.error(f"❌ Scroll job {job.id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            raise
    
    async def _create_driver(self, device: Device) -> webdriver.Remote:
        """Create Appium driver for the device"""
        try:
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = "iPhone"
            options.udid = device.udid
            options.bundle_id = self._get_bundle_id(device.platform)
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.wda_local_port = device.wda_port
            options.auto_accept_alerts = True
            options.connect_hardware_keyboard = False
            
            driver = webdriver.Remote(f"http://localhost:{device.appium_port}", options=options)
            logger.info(f"✅ Driver created for device {device.name}")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create driver for device {device.name}: {e}")
            raise
    
    def _get_bundle_id(self, platform: str) -> str:
        """Get bundle ID for platform"""
        bundle_ids = {
            "instagram": "com.burbn.instagram",
            "threads": "com.burbn.threads"
        }
        return bundle_ids.get(platform, "com.burbn.instagram")
    
    async def _execute_instagram_scroll(self, driver: webdriver.Remote, job: Job, session_id: str) -> Dict[str, Any]:
        """Execute Instagram scrolling"""
        try:
            logger.info("📱 Executing Instagram scrolling")
            
            # Navigate to target page
            if job.scroll_type == ScrollType.HOME_FEED.value:
                home_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "mainfeed-tab")
                home_tab.click()
                await asyncio.sleep(2)
            elif job.scroll_type == ScrollType.REELS.value:
                reels_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "reels-tab")
                reels_tab.click()
                await asyncio.sleep(3)
            
            # Get scroll parameters
            screen_size = driver.get_window_size()
            scroll_x = int(screen_size['width'] * 0.5)
            scroll_start_y = int(screen_size['height'] * 0.8)  # Start from 80% down
            scroll_end_y = int(screen_size['height'] * 0.1)    # End at 10% down
            
            # Execute scrolling
            scroll_count = 0
            content_found = 0
            interactions = 0
            
            for i in range(job.scroll_count or 5):
                # Human-like scroll - 60%+ of screen height with random variation
                # Faster scrolling for reels, slower for home feed
                if job.scroll_type == "reels":
                    scroll_duration = random.randint(400, 800)  # 0.4-0.8 seconds (faster for reels)
                else:
                    scroll_duration = random.randint(800, 1500)  # 0.8-1.5 seconds (normal for home feed)
                
                base_percentage = 0.6  # Start from 60%
                random_variation = random.uniform(0.0, 0.4)  # Add 0-40% more
                scroll_percentage = base_percentage + random_variation  # 60-100% of screen height
                scroll_distance = int(screen_size['height'] * scroll_percentage)
                
                # Human mistake behavior - sometimes scroll up instead of down
                if random.random() < 0.10:  # 10% chance of "mistake"
                    logger.info("🤦 Human mistake: scrolling up instead of down")
                    # Scroll up (wrong direction)
                    mistake_distance = random.randint(100, 300)
                    driver.swipe(
                        scroll_x, scroll_start_y,
                        scroll_x, scroll_start_y + mistake_distance,
                        random.randint(300, 600)
                    )
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    # Realize mistake and scroll down (correct direction)
                    logger.info("🔄 Correcting mistake: scrolling down")
                    driver.swipe(
                        scroll_x, scroll_start_y,
                        scroll_x, scroll_start_y - scroll_distance,
                        scroll_duration
                    )
                else:
                    # Normal scroll down
                    driver.swipe(
                        scroll_x, scroll_start_y,
                        scroll_x, scroll_start_y - scroll_distance,
                        scroll_duration
                    )
                
                # Human-like pause for content to load and "reading" time
                content_load_pause = random.uniform(1.5, 3.0)
                await asyncio.sleep(content_load_pause)
                
                # Count content
                like_buttons = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "like-button")
                content_found += len(like_buttons)
                
                # Random interaction
                if like_buttons and random.random() < 0.3:
                    try:
                        like_buttons[0].click()
                        interactions += 1
                        await asyncio.sleep(1)
                    except:
                        pass
                
                # Human-like "reading" pause - 3-10 seconds randomly
                reading_pause = random.uniform(3.0, 10.0)
                await asyncio.sleep(reading_pause)
                
                scroll_count += 1
            
            result = {
                "session_id": session_id,
                "platform": "instagram",
                "scroll_type": job.scroll_type,
                "scroll_count": scroll_count,
                "content_found": content_found,
                "interactions": interactions,
                "duration_seconds": (datetime.now() - self.active_scrolls[session_id]["start_time"]).total_seconds(),
                "success": True
            }
            
            logger.info(f"✅ Instagram scrolling completed: {scroll_count} scrolls, {content_found} content found")
            return result
            
        except Exception as e:
            logger.error(f"❌ Instagram scrolling failed: {e}")
            raise
    
    async def _execute_threads_scroll(self, driver: webdriver.Remote, job: Job, session_id: str) -> Dict[str, Any]:
        """Execute Threads scrolling"""
        try:
            logger.info("🧵 Executing Threads scrolling")
            
            # Navigate to home feed
            feed_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "feed-tab-main")
            feed_tab.click()
            await asyncio.sleep(2)
            
            # Get scroll parameters
            screen_size = driver.get_window_size()
            scroll_x = int(screen_size['width'] * 0.5)
            scroll_start_y = int(screen_size['height'] * 0.8)  # Start from 80% down
            scroll_end_y = int(screen_size['height'] * 0.1)    # End at 10% down
            
            # Execute scrolling
            scroll_count = 0
            threads_found = 0
            interactions = 0
            
            for i in range(job.scroll_count or 5):
                # Human-like scroll
                scroll_duration = random.randint(800, 1500)
                scroll_distance = random.randint(200, 400)
                
                # Human mistake behavior - sometimes scroll up instead of down
                if random.random() < 0.10:  # 10% chance of "mistake"
                    logger.info("🤦 Human mistake: scrolling up instead of down")
                    # Scroll up (wrong direction)
                    mistake_distance = random.randint(100, 300)
                    driver.swipe(
                        scroll_x, scroll_start_y,
                        scroll_x, scroll_start_y + mistake_distance,
                        random.randint(300, 600)
                    )
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    # Realize mistake and scroll down (correct direction)
                    logger.info("🔄 Correcting mistake: scrolling down")
                    driver.swipe(
                        scroll_x, scroll_start_y,
                        scroll_x, scroll_start_y - scroll_distance,
                        scroll_duration
                    )
                else:
                    # Normal scroll down
                    driver.swipe(
                        scroll_x, scroll_start_y,
                        scroll_x, scroll_start_y - scroll_distance,
                        scroll_duration
                    )
                
                # Human-like pause for content to load and "reading" time
                content_load_pause = random.uniform(1.5, 3.0)
                await asyncio.sleep(content_load_pause)
                
                # Count threads
                like_buttons = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "like-button")
                reply_buttons = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "reply-button")
                threads_found += len(like_buttons) + len(reply_buttons)
                
                # Random interaction
                if like_buttons and random.random() < 0.3:
                    try:
                        like_buttons[0].click()
                        interactions += 1
                        await asyncio.sleep(1)
                    except:
                        pass
                
                # Human-like "reading" pause - 3-10 seconds randomly
                reading_pause = random.uniform(3.0, 10.0)
                await asyncio.sleep(reading_pause)
                
                scroll_count += 1
            
            result = {
                "session_id": session_id,
                "platform": "threads",
                "scroll_type": job.scroll_type,
                "scroll_count": scroll_count,
                "threads_found": threads_found,
                "interactions": interactions,
                "duration_seconds": (datetime.now() - self.active_scrolls[session_id]["start_time"]).total_seconds(),
                "success": True
            }
            
            logger.info(f"✅ Threads scrolling completed: {scroll_count} scrolls, {threads_found} threads found")
            return result
            
        except Exception as e:
            logger.error(f"❌ Threads scrolling failed: {e}")
            raise
    
    def get_scroll_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get scroll metrics for a session"""
        return self.scroll_metrics.get(session_id)
    
    def get_active_scrolls(self) -> Dict[str, Any]:
        """Get all active scroll sessions"""
        return self.active_scrolls
    
    def cleanup_session(self, session_id: str):
        """Cleanup a scroll session"""
        if session_id in self.active_scrolls:
            del self.active_scrolls[session_id]
        if session_id in self.scroll_metrics:
            del self.scroll_metrics[session_id]

# Global scroll service instance
scroll_service = ScrollService()
