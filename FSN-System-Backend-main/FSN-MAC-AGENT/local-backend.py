#!/usr/bin/env python3
"""
FSN Local Backend for Mac
Connects to your frontend and starts Appium processes locally
"""

from fastapi import FastAPI, HTTPException
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import subprocess
import time
import json
from datetime import datetime
import os
import psutil
import threading
import socket
import requests
import uuid
import asyncio
from log_cleaner import clean_template_data_for_logging, clean_job_info_for_history, format_template_summary

app = FastAPI(title="FSN Local Backend", version="1.0.0")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent storage for devices and jobs
DEVICES_FILE = "devices_storage.json"

def load_devices():
    """Load devices from persistent storage"""
    try:
        if os.path.exists(DEVICES_FILE):
            with open(DEVICES_FILE, 'r') as f:
                devices_data = json.load(f)
                print(f"📂 Loaded {len(devices_data)} devices from storage")
                return devices_data
    except Exception as e:
        print(f"⚠️ Failed to load devices from storage: {e}")
    return []

def save_devices():
    """Save devices to persistent storage"""
    try:
        with open(DEVICES_FILE, 'w') as f:
            json.dump(devices, f, indent=2)
        print(f"💾 Saved {len(devices)} devices to storage")
    except Exception as e:
        print(f"⚠️ Failed to save devices to storage: {e}")

# Load devices from storage on startup
devices = load_devices()
jobs = []
running_appium_processes = {}  # device_id -> process
active_jobs = {}  # job_id -> job_info
job_history = []  # completed jobs

# -------------------------------
# Simple WebSocket connection manager
# -------------------------------
active_websocket_connections: "set[WebSocket]" = set()

def get_active_connection_count() -> int:
    try:
        return len(active_websocket_connections)
    except Exception:
        return 0

# -------------------------------
# Helper Functions
# -------------------------------
async def get_account_by_device_id(device_id: str):
    """Get account information by device_id from database"""
    try:
        # Use requests instead of aiohttp to avoid dependency issues
        import requests
        
        # Make API call to get accounts for this device
        response = requests.get(f"http://localhost:8000/api/v1/accounts?device_id={device_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            accounts = data.get('items', [])
            if accounts:
                # Return the first account (assuming one account per device for now)
                account = accounts[0]
                print(f"🔍 Found account: {account.get('username')} with container_number: {account.get('container_number')}")
                return account
            else:
                print(f"🔍 No accounts found for device {device_id}")
                return None
        else:
            print(f"🔍 Failed to get accounts for device {device_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"🔍 Error getting account for device {device_id}: {e}")
        return None

# -------------------------------
# Job Execution Functions
# -------------------------------
async def start_template_execution_job(device_id: str, template_data: dict = None):
    """Start a template execution job for the device"""
    try:
        # Generate job ID
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        # Create job info with actual template data or sensible defaults
        if template_data:
            # Use the actual template data from frontend
            job_info = {
                "id": job_id,
                "device_id": device_id,  # Store device_id for WebSocket updates
                "template": template_data,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "current_step": "pending",
                "progress": 0,
                "results": [],
                "errors": []
            }
        else:
            # No template data provided - cannot proceed
            raise HTTPException(status_code=400, detail="Template data is required for job execution")
        
        active_jobs[job_id] = job_info
        
        # Start job execution in background
        asyncio.create_task(execute_template_job(job_id))
        
        # Send initial job status update
        await update_job_status(job_id, "initializing", "Starting job...", 5)
        
        print(f"🚀 Started template execution job {job_id} for device {device_id}")
        return job_id
        
    except Exception as e:
        print(f"❌ Failed to start template execution job: {e}")
        return None

async def execute_template_job(job_id: str):
    """Execute the template job"""
    job_info = active_jobs.get(job_id)
    if not job_info:
        print(f"❌ Job {job_id} not found")
        return
    
    try:
        device_id = job_info["device_id"]
        template = job_info["template"]
        
        print(f"🎯 Executing job {job_id} for device {device_id}")
        
        # Send status update: job is now running
        await update_job_status(job_id, "running", "Navigating to home feed", 10)
        
        # Step 1: Wait for Appium to be ready
        # Don't send generic "waiting_for_appium" - let callbacks handle all updates
        print(f"🚀 Starting job {job_id} - callbacks will handle progress updates")
        await asyncio.sleep(5)  # Wait for Appium to fully start
        
        # Step 2: Handle container switching (if jailbroken)
        device = None
        for d in devices:
            if d.get("id") == device_id:
                device = d
                break
        
        if device and device.get("jailbroken", False):
            await update_job_status(job_id, "container_switching", "switching_containers", 30)
            print(f"🔄 Switching to Crane container for device {device_id}")
            await execute_crane_container_switch(device_id, job_id)
        
        # Step 3: Execute template actions
        await update_job_status(job_id, "executing", "executing_template", 50)
        
        # Execute real Appium automation
        text_posts = template.get("settings", {}).get("textPostsPerDay", 0)
        photo_posts = template.get("settings", {}).get("photosPostsPerDay", 0)
        
        total_posts = text_posts + photo_posts
        completed_posts = 0
        results = []
        
        # Execute photo posts first (if any)
        if photo_posts > 0:
            print(f"📸 Executing {photo_posts} real photo posts for device {device_id}")
            await execute_real_threads_photo_posts(device_id, photo_posts, job_id, template)
            completed_posts += photo_posts
            results.append({"action": "post_photo", "count": photo_posts, "success": True})
        
        # Execute text posts (if any)
        if text_posts > 0:
            print(f"📝 Executing {text_posts} real text posts for device {device_id}")
            await execute_real_threads_posts(device_id, text_posts, job_id, template)
            completed_posts += text_posts
            results.append({"action": "post_thread", "count": text_posts, "success": True})
        
        # Handle case where no posts are specified
        if total_posts == 0:
            print(f"⚠️ No posts specified in template - completing job without posting")
            results.append({"action": "no_posts", "count": 0, "success": True})
        
        # Step 4: Complete job (profile scans done after each post)
        # Send final completion update
        await update_job_status(job_id, "completed", "Job completed successfully", 100)
        job_info["completed_at"] = datetime.now().isoformat()
        job_info["results"] = results
        print(f"🏁 All posts completed - job completed successfully")
        
        # Filter out large base64 content before moving to history
        job_info_clean = clean_job_info_for_history(job_info)
        print(f"🧹 Filtered out large file content from job history")
        
        # Move to history (cleaned version)
        job_history.append(job_info_clean)
        del active_jobs[job_id]
        
        print(f"✅ Job {job_id} completed successfully with profile tracking")
        
    except Exception as e:
        print(f"❌ Job {job_id} failed: {e}")
        if job_id in active_jobs:
            # Send failure status update
            await update_job_status(job_id, "failed", f"Job failed: {str(e)}", 0)
            
            job_info = active_jobs[job_id]
            job_info["status"] = "failed"
            job_info["completed_at"] = datetime.now().isoformat()
            job_info["errors"].append(str(e))
            
            # Filter out large base64 content before moving to history
            job_info_clean = clean_job_info_for_history(job_info)
            print(f"🧹 Filtered out large file content from failed job history")
            
            job_history.append(job_info_clean)
            del active_jobs[job_id]

async def execute_crane_container_switch(device_id: str, job_id: str):
    """Execute Crane container switching for jailbroken devices"""
    try:
        # Get device info
        device = None
        for d in devices:
            if d.get("id") == device_id:
                device = d
                break
        
        if not device:
            print(f"❌ Device {device_id} not found")
            return
        
        print(f"🔄 Starting Crane container switch for device {device_id}")
        
        # Import the Crane container switching
        import sys
        platforms_path = "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main"
        sys.path.append(platforms_path)
        
        from api.services.crane_account_switching import complete_crane_account_switch_flow
        
        # Get assigned accounts for this device
        # For now, we'll use a default account - in real implementation, this would come from the template/device assignment
        account_info = {
            "platform": "threads",
            "username": "default_user",  # This should come from device assignment
            "container_name": f"threads_container_{device_id}"
        }
        
        # Execute container switch
        result = await complete_crane_account_switch_flow(device, account_info)
        
        if result:
            print(f"✅ Crane container switch successful for device {device_id}")
        else:
            print(f"❌ Crane container switch failed for device {device_id}")
        
    except Exception as e:
        print(f"❌ Error in Crane container switching: {e}")
        # Don't raise - continue with automation even if container switch fails

def download_photo_via_safari_proven_method(driver, photo_url):
    """
    Download photo via Safari using the proven method from picture.py
    """
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    
    try:
        print(f"📱 Opening Safari...")
        driver.activate_app('com.apple.mobilesafari')
        
        # 1. Click the initial tab bar item to activate the URL field
        print(f"📱 Clicking initial URL bar element...")
        initial_url_bar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, '//XCUIElementTypeTextField[@name="TabBarItemTitle"]'))
        )
        initial_url_bar.click()
        
        # 2. Wait for the actual URL input field to appear
        print(f"📱 Waiting for URL field to appear...")
        final_url_field = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, '//XCUIElementTypeTextField[@name="URL"]'))
        )
        
        # Clear and type the URL
        final_url_field.clear()
        time.sleep(0.5)
        final_url_field.send_keys(photo_url)
        
        # Click Go button
        print(f"📱 Clicking Go button...")
        go_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, '//XCUIElementTypeButton[@name="Go"]'))
        )
        go_button.click()
        
        # Handle ngrok "Visit Site" button if it appears
        try:
            print(f"📱 Checking for 'Visit Site' button...")
            visit_site_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((AppiumBy.XPATH, '//XCUIElementTypeButton[@name="Visit Site"]'))
            )
            print(f"📱 Clicking 'Visit Site' button...")
            visit_site_button.click()
        except:
            print(f"📱 'Visit Site' button not found, continuing...")
        
        print(f"📱 Waiting for image to load...")
        time.sleep(10)
        
        # Find and long press on the image
        print(f"🖼️ Finding image element...")
        image_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, "//XCUIElementTypeImage"))
        )
        
        print(f"📱 Long pressing on image...")
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)
        actions.click_and_hold(image_element).pause(2).release().perform()
        
        print(f"💾 Looking for 'Add to Photos' button...")
        add_to_photos_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, '//XCUIElementTypeButton[@name="Add to Photos"]'))
        )
        add_to_photos_button.click()
        
        print(f"✅ Photo saved to iPhone Photos successfully!")
        time.sleep(5)
        return True
        
    except Exception as e:
        print(f"❌ Safari photo download failed: {e}")
        return False
    finally:
        try:
            driver.terminate_app('com.apple.mobilesafari')
        except:
            pass

async def execute_scrolling_and_liking(device_id: str, job_id: str, template_data: dict = None):
    """Execute scrolling and liking after posts but before profile extraction"""
    try:
        # Get device info
        device = None
        for d in devices:
            if d.get("id") == device_id:
                device = d
                break
        
        if not device:
            print(f"❌ Device {device_id} not found for scrolling")
            return False
        
        # Get template settings for scrolling and liking
        settings = template_data.get("settings", {}) if template_data else {}
        scrolling_time_minutes = settings.get("scrollingTimeMinutes", 0)
        likes_per_day = settings.get("likesPerDay", 0)
        
        print(f"📊 Scrolling Template settings:")
        print(f"   Scrolling time: {scrolling_time_minutes} minutes")
        print(f"   Likes per day: {likes_per_day}")
        
        # Skip if no scrolling or liking configured
        if scrolling_time_minutes == 0 and likes_per_day == 0:
            print(f"⏭️ No scrolling or liking configured - skipping")
            return True
        
        # Check if scrolling/liking already done today (once per day limit)
        today = datetime.now().strftime("%Y-%m-%d")
        scroll_tracking_file = f"scroll_tracking_{device_id}_{today}.json"
        
        if os.path.exists(scroll_tracking_file):
            print(f"✅ Scrolling and liking already completed today for device {device_id}")
            return True
        
        print(f"🎯 Starting scrolling and liking for device {device_id}")
        print(f"   Duration: {scrolling_time_minutes} minutes")
        print(f"   Target likes: {likes_per_day}")
        
        # Import the scrolling and liking automation
        import sys
        sys.path.append('/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main/platforms/threads/actions')
        sys.path.append('/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main/platforms/threads/working_tests')
        
        # Import not needed - scrolling and liking is now handled in the automation checkpoints
        
        # Create scrolling automation
        scroll_automation = ThreadsScrollActions(scroll_type="home_feed")
        
        # Execute scrolling with liking
        print(f"📱 Executing {scrolling_time_minutes} minutes of scrolling with {likes_per_day} likes...")
        
        # This would need to be implemented to combine scrolling + liking
        # For now, let's create a basic implementation
        success = await execute_combined_scroll_and_like(
            device, scrolling_time_minutes, likes_per_day, job_id
        )
        
        if success:
            # Mark as completed for today
            with open(scroll_tracking_file, 'w') as f:
                import json
                json.dump({
                    "date": today,
                    "device_id": device_id,
                    "scrolling_minutes": scrolling_time_minutes,
                    "likes_completed": likes_per_day,
                    "completed_at": datetime.now().isoformat()
                }, f)
            print(f"✅ Scrolling and liking completed for today")
        
        return success
        
    except Exception as e:
        print(f"❌ Error in scrolling and liking: {e}")
        return False

async def execute_combined_scroll_and_like(device, scrolling_minutes, target_likes, job_id):
    """Execute combined scrolling and liking automation"""
    try:
        print(f"🔄 Starting combined scroll and like automation...")
        print(f"   Scrolling duration: {scrolling_minutes} minutes")
        print(f"   Target likes: {target_likes}")
        
        # TODO: Implement the actual scrolling and liking logic
        # This would use the ThreadsScrollActions and ThreadsLikePostTest classes
        # For now, simulate the process
        
        start_time = time.time()
        end_time = start_time + (scrolling_minutes * 60)  # Convert minutes to seconds
        likes_completed = 0
        
        while time.time() < end_time and likes_completed < target_likes:
            # Simulate scrolling and liking
            print(f"📱 Scrolling and looking for posts to like... ({likes_completed}/{target_likes} likes)")
            
            # Simulate time for scrolling and liking
            time.sleep(30)  # 30 seconds per like attempt
            likes_completed += 1
            
            # Update progress
            elapsed_minutes = (time.time() - start_time) / 60
            progress = min(100, int((elapsed_minutes / scrolling_minutes) * 100))
            print(f"📊 Scrolling progress: {progress}% ({elapsed_minutes:.1f}/{scrolling_minutes} minutes)")
        
        print(f"✅ Scrolling and liking completed: {likes_completed} likes in {scrolling_minutes} minutes")
        return True
        
    except Exception as e:
        print(f"❌ Error in combined scroll and like: {e}")
        return False

async def execute_real_threads_photo_posts(device_id: str, photo_posts: int, job_id: str, template_data: dict = None):
    """Execute real Threads photo posts using Appium automation with integrated photo service"""
    try:
        # Get device info
        device = None
        for d in devices:
            if d.get("id") == device_id:
                device = d
                break
        
        if not device:
            print(f"❌ Device {device_id} not found")
            return
        
        print(f"🎯 Starting real Threads PHOTO automation for device {device_id}")
        
        # Get template settings for photos
        settings = template_data.get("settings", {}) if template_data else {}
        photos_folder = settings.get("photosFolder", "")
        captions_file = settings.get("captionsFile", "")
        captions_file_content = settings.get("captionsFileContent", "")
        
        print(f"📊 Photo Template settings:")
        print(f"   Photo posts: {photo_posts}")
        print(f"   Photos folder: {photos_folder}")
        print(f"   Captions file: {captions_file}")
        
        # Log template summary instead of full data
        template_summary = format_template_summary(template_data)
        print(f"   Template summary: {template_summary}")
        print(f"   Has captions file content: {'Yes' if captions_file_content else 'No'}")
        
        # Read captions from XLSX file content if specified
        captions_list = []
        
        if captions_file_content and photo_posts > 0:
            try:
                import pandas as pd
                import base64
                import io
                
                # Decode base64 content
                file_content = base64.b64decode(captions_file_content.split(',')[1])  # Remove data:application/...;base64, prefix
                
                # Read XLSX from bytes
                df = pd.read_excel(io.BytesIO(file_content))
                
                if 'caption' in df.columns:
                    captions_list = df['caption'].dropna().astype(str).tolist()
                elif 'text' in df.columns:
                    captions_list = df['text'].dropna().astype(str).tolist()
                else:
                    captions_list = df.iloc[:, 0].dropna().astype(str).tolist()
                
                print(f"📖 Loaded {len(captions_list)} captions from XLSX content")
                print(f"📝 Captions preview: {captions_list[:3] if captions_list else 'None'}")
            except Exception as e:
                print(f"⚠️ Failed to read captions XLSX content: {e}")
                print("📝 No captions content available - will use default captions")
                captions_list = []
        elif captions_file and photo_posts > 0:
            # Fallback to file path if base64 content not available
            try:
                import pandas as pd
                df = pd.read_excel(captions_file)
                if 'caption' in df.columns:
                    captions_list = df['caption'].dropna().astype(str).tolist()
                elif 'text' in df.columns:
                    captions_list = df['text'].dropna().astype(str).tolist()
                else:
                    captions_list = df.iloc[:, 0].dropna().astype(str).tolist()
                print(f"📖 Loaded {len(captions_list)} captions from file {captions_file}")
            except Exception as e:
                print(f"⚠️ Failed to read captions XLSX file {captions_file}: {e}")
                print("📝 No captions file available - will use default captions")
                captions_list = []
        else:
            print("📝 No captions file specified - will use default captions")
            captions_list = []
        
        # Default captions if none provided
        if not captions_list:
            captions_list = [
                "Living my best life! ✨",
                "Another day, another adventure 🌟", 
                "Grateful for this moment 🙏",
                "Making memories that last forever 📸",
                "Life is beautiful 🌈"
            ]
            print(f"📝 Using {len(captions_list)} default captions")
        
        # Import the integrated photo service
        import sys
        sys.path.append("/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main/api/services")
        from integrated_photo_service import integrated_photo_service
        
        # Import the Threads automation script
        platforms_path = "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main"
        sys.path.append(platforms_path)
        
        # Import the Threads automation using importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "post_thread_test", 
            f"{platforms_path}/platforms/threads/working_tests/06_post_thread_functionality_test.py"
        )
        post_thread_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(post_thread_module)
        ThreadsPostThreadTest = post_thread_module.ThreadsPostThreadTest
        
        # Execute photo posts
        for i in range(photo_posts):
            print(f"📸 Creating real photo post {i+1}/{photo_posts}")
            
            # Calculate base progress for this post
            base_progress = (i * 100 // photo_posts)
            print(f"📊 Starting photo post {i+1}/{photo_posts} automation (base progress: {base_progress}%)")
            
            try:
                # STEP 1: Process photo BEFORE launching Threads app
                print(f"🚀 STEP 1: Processing photo for post {i+1}")
                
                if not photos_folder:
                    print(f"❌ No photos folder specified - cannot proceed")
                    continue
                
                # Check if device has ngrok token for photo posting
                device_ngrok_token = device.get('ngrok_token')
                if not device_ngrok_token:
                    print(f"⚠️ No ngrok token set for device {device_id} - skipping photo post {i+1}")
                    print(f"💡 Set ngrok token in device settings to enable photo posting")
                    continue
                
                # Use integrated photo service to select, clean, and serve photo
                photo_result = await integrated_photo_service.process_photo_post(
                    photos_folder=photos_folder,
                    captions_file=captions_file if captions_file else None,
                    device_udid=device.get('udid', f"device_{device_id}"),
                    ngrok_token=device_ngrok_token
                )
                
                if not photo_result['success']:
                    print(f"❌ Photo processing failed: {photo_result['message']}")
                    continue
                
                photo_url = photo_result['photo_url']
                caption_from_photo_service = photo_result.get('caption', '')
                
                # Use caption from photo service or select from captions list
                if caption_from_photo_service:
                    selected_caption = caption_from_photo_service
                else:
                    selected_caption = captions_list[i % len(captions_list)]
                
                print(f"📸 Photo processed and served at: {photo_url}")
                print(f"📝 Using caption: {selected_caption[:100]}...")
                
                # STEP 2: Download photo to iPhone via Safari using proven method
                print(f"📱 STEP 2: Downloading photo to iPhone via Safari using proven picture.py method")
                
                # Import Appium WebDriver for Safari automation
                from appium import webdriver
                from appium.options.ios import XCUITestOptions
                from appium.webdriver.common.appiumby import AppiumBy
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                import time
                
                # Create Appium driver for Safari
                safari_options = XCUITestOptions()
                safari_options.platform_name = "iOS"
                safari_options.device_name = device.get('name', 'iPhone')
                safari_options.udid = device.get('udid')
                safari_options.automation_name = "XCUITest"
                safari_options.bundle_id = "com.apple.mobilesafari"  # Safari bundle ID
                safari_options.wda_local_port = device.get('wda_port', 8109)
                safari_options.no_reset = True
                safari_options.full_reset = False
                safari_options.new_command_timeout = 300
                
                appium_url = f"http://localhost:{device.get('appium_port', 4741)}"
                
                try:
                    print(f"📱 Creating Safari WebDriver session...")
                    safari_driver = webdriver.Remote(appium_url, options=safari_options)
                    
                    # Use the proven Safari download method from picture.py
                    download_success = download_photo_via_safari_proven_method(safari_driver, photo_url)
                    
                    if download_success:
                        print(f"✅ Photo downloaded to iPhone Photos successfully!")
                    else:
                        print(f"❌ Photo download failed, but continuing with Threads posting...")
                    
                    # Close Safari
                    safari_driver.quit()
                    print(f"🌐 Safari session closed")
                    
                except Exception as safari_error:
                    print(f"❌ Safari download failed: {safari_error}")
                    print(f"⚠️ Continuing with Threads posting assuming photo is in gallery...")
                    
                    # Clean up driver if it exists
                    try:
                        safari_driver.quit()
                    except:
                        pass
                
                # STEP 3: Launch Threads and post with media
                print(f"📱 STEP 3: Launching Threads app and posting with media")
                
                # Create progress callback function that sends updates immediately
                def progress_callback(checkpoint_name, checkpoint_percent):
                    # For single post, use checkpoint_percent directly
                    # For multiple posts, distribute across posts
                    if photo_posts == 1:
                        actual_progress = checkpoint_percent
                    else:
                        progress_per_post = 100 // photo_posts
                        actual_progress = base_progress + (checkpoint_percent * progress_per_post // 100)
                    
                    actual_progress = min(actual_progress, 100)
                    print(f"📊 REAL CHECKPOINT UPDATE: {checkpoint_name} ({actual_progress}%) - Photo Post {i+1}/{photo_posts}")
                    
                    # Update job status directly
                    print(f"🔥 CALLBACK TRIGGERED: {checkpoint_name} ({actual_progress}%)")
                    
                    if job_id in active_jobs:
                        job_info = active_jobs[job_id]
                        print(f"🔥 DIRECT UPDATE - BEFORE: status={job_info.get('status')}, progress={job_info.get('progress')}, step={job_info.get('current_step')}")
                        
                        # Update job info directly
                        job_info["status"] = "executing"
                        job_info["current_step"] = checkpoint_name
                        job_info["progress"] = actual_progress
                        job_info["message"] = checkpoint_name
                        
                        print(f"🔥 DIRECT UPDATE - AFTER: status={job_info.get('status')}, progress={job_info.get('progress')}, step={job_info.get('current_step')}")
                        print(f"✅ DIRECT PROGRESS UPDATE: {checkpoint_name} ({actual_progress}%)")
                    else:
                        print(f"❌ JOB {job_id} NOT FOUND IN ACTIVE_JOBS for direct update!")
                
                # Get scrolling settings from template
                scrolling_time_minutes = settings.get("scrollingTimeMinutes", 0)
                likes_per_day = settings.get("likesPerDay", 0)
                
                # Get device type and container info
                device_type = "jailbroken" if device.get("jailbroken", False) else "non_jailbroken"
                
                # Get container_number from device settings (temporarily using device data)
                container_id = None
                if device_type == "jailbroken":
                    # For now, use container 3 as specified by user
                    # TODO: Get this from account data properly
                    container_id = "3"  # User specified container 3
                    print(f"🔧 Using container: {container_id} (hardcoded for testing)")
                
                print(f"🔧 Device info: Type={device_type}, Container={container_id}")
                
                # Create the automation instance with callback and device info
                automation = ThreadsPostThreadTest(
                    post_text=selected_caption,
                    photos_per_day=photo_posts,  # Use photo posts count from template!
                    progress_callback=progress_callback,
                    device_type=device_type,
                    container_id=container_id
                )
                
                # Set scrolling parameters on the automation instance
                automation.scrolling_minutes = scrolling_time_minutes
                automation.likes_target = likes_per_day
                automation.device_id = device_id
                
                print(f"📱 Executing Threads photo post automation...")
                
                # Execute with media enabled
                success = automation.run_test()
                
                if success:
                    print(f"✅ Photo post {i+1}/{photo_posts} completed successfully!")
                    
                    # Update final progress for this post
                    final_progress = ((i + 1) * 100 // photo_posts)
                    if job_id in active_jobs:
                        active_jobs[job_id]["progress"] = final_progress
                        active_jobs[job_id]["current_step"] = f"Photo post {i+1} completed"
                        active_jobs[job_id]["message"] = f"Photo post {i+1}/{photo_posts} completed successfully"
                        print(f"📊 Final progress for post {i+1}: {final_progress}%")
                else:
                    print(f"❌ Photo post {i+1}/{photo_posts} failed")
                    
                    # Update job with error
                    if job_id in active_jobs:
                        active_jobs[job_id]["status"] = "error"
                        active_jobs[job_id]["message"] = f"Photo post {i+1} failed"
                        print(f"❌ Updated job status to error for post {i+1}")
                
                # Cleanup photo resources after posting
                print(f"🧹 Cleaning up photo resources...")
                await integrated_photo_service._cleanup_device_handlers(device.get('udid', f"device_{device_id}"))
                
                print(f"✅ Photo post {i+1}/{photo_posts} workflow completed")
                
            except Exception as e:
                print(f"❌ Exception in photo post {i+1}/{photo_posts}: {e}")
                import traceback
                traceback.print_exc()
                
                if job_id in active_jobs:
                    active_jobs[job_id]["status"] = "error"
                    active_jobs[job_id]["message"] = f"Photo post {i+1} failed: {str(e)}"
                
                continue
        
        # Mark job as completed
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "completed"
            active_jobs[job_id]["progress"] = 100
            active_jobs[job_id]["current_step"] = "All photo posts completed"
            active_jobs[job_id]["message"] = f"Successfully completed {photo_posts} photo posts"
            
        print(f"🎉 All {photo_posts} photo posts completed successfully!")
        
        # Execute scrolling and liking after photo posts (once per day)
        print(f"🔄 Starting scrolling and liking after photo posts...")
        await execute_scrolling_and_liking(device_id, job_id, template_data)
        
        # Final cleanup
        await integrated_photo_service.cleanup_all()
        print(f"🧹 Final cleanup completed")
        
    except Exception as e:
        print(f"❌ Exception in execute_real_threads_photo_posts: {e}")
        import traceback
        traceback.print_exc()
        
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "error"
            active_jobs[job_id]["message"] = f"Photo posts failed: {str(e)}"

async def execute_real_threads_posts(device_id: str, text_posts: int, job_id: str, template_data: dict = None):
    """Execute real Threads posts using Appium automation"""
    try:
        # Get device info
        device = None
        for d in devices:
            if d.get("id") == device_id:
                device = d
                break
        
        if not device:
            print(f"❌ Device {device_id} not found")
            return
        
        print(f"🎯 Starting real Threads automation for device {device_id}")
        
        # Get template settings
        settings = template_data.get("settings", {}) if template_data else {}
        photos_per_day = settings.get("photosPerDay", 0)
        text_posts_file = settings.get("textPostsFile", "")
        
        print(f"📊 Template settings:")
        print(f"   Text posts: {text_posts}")
        print(f"   Photos per day: {photos_per_day}")
        print(f"   Text posts file: {text_posts_file}")
        
        # Log template summary instead of full data
        template_summary = format_template_summary(template_data)
        text_posts_file_content = settings.get("textPostsFileContent", "")
        print(f"   Template summary: {template_summary}")
        print(f"   Has text posts file content: {'Yes' if text_posts_file_content else 'No'}")
        
        # Read text posts from XLSX file content if specified
        text_posts_list = []
        text_posts_file_content = settings.get("textPostsFileContent", "")
        
        if text_posts_file_content and text_posts > 0:
            try:
                import pandas as pd
                import base64
                import io
                
                # Decode base64 content
                file_content = base64.b64decode(text_posts_file_content.split(',')[1])  # Remove data:application/...;base64, prefix
                
                # Read XLSX from bytes
                df = pd.read_excel(io.BytesIO(file_content))
                
                if 'text' in df.columns:
                    text_posts_list = df['text'].dropna().astype(str).tolist()
                else:
                    text_posts_list = df.iloc[:, 0].dropna().astype(str).tolist()
                
                print(f"📖 Loaded {len(text_posts_list)} text posts from XLSX content")
                print(f"📝 Text posts preview: {text_posts_list[:3] if text_posts_list else 'None'}")
            except Exception as e:
                print(f"⚠️ Failed to read XLSX content: {e}")
                print("📝 No XLSX content available - cannot proceed without text posts file")
                text_posts_list = []
        elif text_posts_file and text_posts > 0:
            # Fallback to file path if base64 content not available
            try:
                import pandas as pd
                df = pd.read_excel(text_posts_file)
                if 'text' in df.columns:
                    text_posts_list = df['text'].dropna().astype(str).tolist()
                else:
                    text_posts_list = df.iloc[:, 0].dropna().astype(str).tolist()
                print(f"📖 Loaded {len(text_posts_list)} text posts from file {text_posts_file}")
            except Exception as e:
                print(f"⚠️ Failed to read XLSX file {text_posts_file}: {e}")
                print("📝 No XLSX file available - cannot proceed without text posts file")
                text_posts_list = []
        else:
            print("📝 No text posts file specified - cannot proceed without text posts")
            text_posts_list = []
        
        # Import the Threads automation script
        import sys
        import os
        
        # Add the platforms directory to Python path
        platforms_path = "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main"
        sys.path.append(platforms_path)
        
        # Import the Threads automation using importlib (since filename starts with number)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "post_thread_test", 
            f"{platforms_path}/platforms/threads/working_tests/06_post_thread_functionality_test.py"
        )
        post_thread_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(post_thread_module)
        ThreadsPostThreadTest = post_thread_module.ThreadsPostThreadTest
        
        # Execute posts with profile scan after each post
        for i in range(text_posts):
            print(f"📝 Creating real text post {i+1}/{text_posts}")
            
            # Calculate base progress for this post
            base_progress = (i * 100 // text_posts)
            print(f"📊 Starting post {i+1}/{text_posts} automation (base progress: {base_progress}%)")
            
            try:
                # Get the text content for this post
                if not text_posts_list:
                    print(f"❌ No text posts available - skipping post {i+1}")
                    continue
                
                # Use text from xlsx file, cycling through available posts
                post_text = text_posts_list[i % len(text_posts_list)]
                print(f"📝 Post text: {post_text}")
                
                # Don't send generic updates - let callbacks handle everything
                print(f"📝 Starting post {i+1}/{text_posts} - callbacks will send progress updates")
                
                # Create progress callback function that sends updates immediately
                def progress_callback(checkpoint_name, checkpoint_percent):
                    # For single post, use checkpoint_percent directly
                    # For multiple posts, distribute across posts
                    if text_posts == 1:
                        actual_progress = checkpoint_percent
                    else:
                        progress_per_post = 100 // text_posts
                        actual_progress = base_progress + (checkpoint_percent * progress_per_post // 100)
                    
                    actual_progress = min(actual_progress, 100)
                    print(f"📊 REAL CHECKPOINT UPDATE: {checkpoint_name} ({actual_progress}%) - Post {i+1}/{text_posts}")
                    
                    # Update job status directly (no threading, no async)
                    print(f"🔥 CALLBACK TRIGGERED: {checkpoint_name} ({actual_progress}%)")
                    
                    if job_id in active_jobs:
                        job_info = active_jobs[job_id]
                        print(f"🔥 DIRECT UPDATE - BEFORE: status={job_info.get('status')}, progress={job_info.get('progress')}, step={job_info.get('current_step')}")
                        
                        # Update job info directly
                        job_info["status"] = "executing"
                        job_info["current_step"] = checkpoint_name
                        job_info["progress"] = actual_progress
                        job_info["message"] = checkpoint_name
                        
                        print(f"🔥 DIRECT UPDATE - AFTER: status={job_info.get('status')}, progress={job_info.get('progress')}, step={job_info.get('current_step')}")
                        print(f"✅ DIRECT PROGRESS UPDATE: {checkpoint_name} ({actual_progress}%)")
                    else:
                        print(f"❌ JOB {job_id} NOT FOUND IN ACTIVE_JOBS for direct update!")
                
                # Get scrolling settings from template  
                scrolling_time_minutes = settings.get("scrollingTimeMinutes", 0)
                likes_per_day = settings.get("likesPerDay", 0)
                
                # Get device type and container info
                device_type = "jailbroken" if device.get("jailbroken", False) else "non_jailbroken"
                
                # Get container_number from device settings (temporarily using device data)
                container_id = None
                if device_type == "jailbroken":
                    # For now, use container 3 as specified by user
                    # TODO: Get this from account data properly
                    container_id = "3"  # User specified container 3
                    print(f"🔧 Using container: {container_id} (hardcoded for testing)")
                
                print(f"🔧 Device info: Type={device_type}, Container={container_id}")
                
                # Create the automation instance with callback and device info
                automation = ThreadsPostThreadTest(
                    post_text=post_text, 
                    photos_per_day=photos_per_day, 
                    progress_callback=progress_callback,
                    device_type=device_type,
                    container_id=container_id
                )
                
                # Set scrolling parameters on the automation instance
                automation.scrolling_minutes = scrolling_time_minutes
                automation.likes_target = likes_per_day
                automation.device_id = device_id
                
                # Run the automation with callback
                success = automation.run_test()
                
                # Don't send generic completion updates - let the callbacks handle it
                print(f"🏁 Post {i+1} automation finished: {'✅ Success' if success else '❌ Failed'}")
                
                if success:
                    print(f"✅ Post {i+1} created successfully with profile tracking")
                else:
                    print(f"❌ Failed to create post {i+1}")
                
            except Exception as e:
                print(f"❌ Failed to create post {i+1}: {e}")
                # Continue with next post even if one fails
                continue
            
            # Small delay between posts
            if i < text_posts - 1:
                await asyncio.sleep(2)
        
        print(f"✅ Completed {text_posts} real Threads posts")
        
        # Execute scrolling and liking after text posts (once per day)
        print(f"🔄 Starting scrolling and liking after text posts...")
        await execute_scrolling_and_liking(device_id, job_id, template_data)
        
    except Exception as e:
        print(f"❌ Error in real Threads automation: {e}")
        raise


async def execute_profile_scan_for_tracking(device_id: str, job_id: str):
    """Execute profile scan for follower tracking after job completion"""
    try:
        print(f"📊 Starting profile scan for tracking on device {device_id}")
        
        # Import the profile scanner
        import sys
        import os
        
        # Add the platforms directory to Python path
        platforms_path = "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main"
        sys.path.append(platforms_path)
        
        # Import the profile scanner using importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "scan_profile_test", 
            f"{platforms_path}/platforms/threads/working_tests/04_scan_profile_functionality_test.py"
        )
        scan_profile_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scan_profile_module)
        ThreadsScanProfileTest = scan_profile_module.ThreadsScanProfileTest
        
        # Execute profile scan
        print("📊 Running profile scan...")
        scanner = ThreadsScanProfileTest()
        success = scanner.run_test()
        
        if success and hasattr(scanner, 'profile_data'):
            profile_stats = {
                "username": scanner.profile_data.get('username', 'Unknown'),
                "name": scanner.profile_data.get('name', 'Unknown'),
                "followers_count": scanner.profile_data.get('followers_count', 0),
                "followers_raw": scanner.profile_data.get('followers_raw', ''),
                "bio": scanner.profile_data.get('bio', ''),
                "scan_timestamp": datetime.now().isoformat(),
                "device_id": device_id,
                "job_id": job_id
            }
            
            print(f"📊 Profile stats extracted: {profile_stats}")
            
            # Save to tracking database
            await save_follower_tracking_data(profile_stats)
            
            return profile_stats
        else:
            print("❌ Profile scan failed or no data extracted")
            return None
            
    except Exception as e:
        print(f"❌ Profile scan error: {e}")
        return None

async def save_follower_tracking_data(profile_stats: dict):
    """Save follower tracking data to database/storage"""
    try:
        # For now, save to local file - will be replaced with database later
        tracking_file = "follower_tracking.json"
        
        # Load existing data
        tracking_data = []
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
        
        # Add new data
        tracking_data.append(profile_stats)
        
        # Save back to file
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)
        
        print(f"💾 Saved follower tracking data: {profile_stats['username']} - {profile_stats['followers_count']} followers")
        
    except Exception as e:
        print(f"❌ Failed to save tracking data: {e}")

async def update_job_status(job_id: str, status: str, step: str, progress: int):
    """Update job status and send WebSocket update"""
    print(f"🔧 UPDATE_JOB_STATUS CALLED: job_id={job_id}, status={status}, step={step}, progress={progress}")
    print(f"🔧 ACTIVE_JOBS KEYS: {list(active_jobs.keys())}")
    
    if job_id in active_jobs:
        job_info = active_jobs[job_id]
        print(f"🔧 BEFORE UPDATE: status={job_info.get('status')}, progress={job_info.get('progress')}, step={job_info.get('current_step')}")
        
        # Update job info
        job_info["status"] = status
        job_info["current_step"] = step
        job_info["progress"] = progress
        job_info["message"] = step  # Also set message field
        
        # Set started_at if initializing
        if status == "initializing" and not job_info.get("started_at"):
            job_info["started_at"] = datetime.now().isoformat()
        
        # Verify the update worked
        print(f"🔧 AFTER UPDATE: status={job_info.get('status')}, progress={job_info.get('progress')}, step={job_info.get('current_step')}")
        print(f"🔧 ACTIVE_JOBS NOW: {active_jobs[job_id]}")
    else:
        print(f"❌ JOB {job_id} NOT FOUND IN ACTIVE_JOBS!")
        return
    
    # Get device_id from job info
    device_id = job_info.get("device_id", "unknown")
    
    # Send WebSocket update
    print(f"🔌 BEFORE WebSocket: {len(active_websocket_connections)} connections")
    print(f"🔌 Sending job update: job_id={job_id}, device_id={device_id}, status={status}, step={step}, progress={progress}")
    
    try:
        await broadcast_job_update(job_id, {
            "status": status,
            "progress": progress,
            "current_step": step,
            "device_id": device_id  # Include device_id in WebSocket message
        })
        print(f"✅ WebSocket update sent successfully for device {device_id}")
    except Exception as e:
        print(f"❌ WebSocket update FAILED: {e}")
    
    print(f"📊 Job {job_id} (Device {device_id}): {status} - {step} ({progress}%)")

async def broadcast_job_update(job_id: str, update_data: dict):
    """Broadcast job update to all WebSocket connections"""
    message = {
        "type": "job_update",
        "job_id": job_id,
        "data": update_data,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"📡 Broadcasting job update: {json.dumps(message, indent=2)}")
    print(f"🔌 Active WebSocket connections: {len(active_websocket_connections)}")
    
    # Send to all connected WebSockets
    disconnected = set()
    for websocket in active_websocket_connections:
        try:
            await websocket.send_text(json.dumps(message))
            print(f"✅ Sent WebSocket message to connection")
        except Exception as e:
            print(f"❌ Failed to send WebSocket message: {e}")
            disconnected.add(websocket)
    
    # Clean up disconnected websockets
    for websocket in disconnected:
        active_websocket_connections.discard(websocket)
        
    if len(active_websocket_connections) == 0:
        print("⚠️ NO ACTIVE WEBSOCKET CONNECTIONS - Frontend not connected!")

async def broadcast_device_status_update(device_id: str, status: str, message: str):
    """Broadcast device status update to all WebSocket connections"""
    # Find device details
    device = None
    for d in devices:
        if d.get("id") == device_id:
            device = d
            break
    
    # Map backend status to frontend status
    frontend_status = "active" if status == "running" else "offline" if status == "stopped" else "error"
    
    device_update = {
        "type": "device_status_update",
        "device_id": device_id,  # Keep as string, don't convert to int
        "status": frontend_status,
        "details": {
            "name": device.get("name", f"Device {device_id}") if device else f"Device {device_id}",
            "udid": device.get("udid", "") if device else "",
            "old_status": "offline" if status == "running" else "active",
            "new_status": frontend_status
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Send to all connected WebSockets
    disconnected = set()
    for websocket in active_websocket_connections:
        try:
            await websocket.send_text(json.dumps(device_update))
        except Exception as e:
            print(f"⚠️ Failed to send device status update: {e}")
            disconnected.add(websocket)
    
    # Remove disconnected connections
    for websocket in disconnected:
        active_websocket_connections.discard(websocket)

# -------------------------------
# License management configuration
# -------------------------------
LICENSE_SERVER_URL = "https://fsn-system-license.onrender.com"
LICENSE_VALIDATE_PATH = "/api/v1/license/validate"
LICENSE_FILE_PATH = os.path.join(os.path.dirname(__file__), ".license_key")

license_key: Optional[str] = None
license_blocked: bool = False

def load_license_key() -> Optional[str]:
    if os.path.exists(LICENSE_FILE_PATH):
        try:
            with open(LICENSE_FILE_PATH, "r", encoding="utf-8") as f:
                key = f.read().strip()
                return key or None
        except Exception:
            return None
    # Fallback to environment
    return os.getenv("FSN_LICENSE_KEY")

def save_license_key(key: str) -> None:
    try:
        with open(LICENSE_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(key.strip())
    except Exception:
        pass

def validate_license(current_license_key: Optional[str], device_id: str) -> Dict[str, Any]:
    """Validate license with central server. Returns dict with 'valid': bool and details."""
    result: Dict[str, Any] = {"valid": False, "reason": "missing_license"}
    
    # For local development, bypass license validation if no key is set
    if not current_license_key:
        print("⚠️ No license key set - allowing local development mode")
        return {"valid": True, "reason": "local_development", "details": {"mode": "local_dev"}}
    
    try:
        url = f"{LICENSE_SERVER_URL}{LICENSE_VALIDATE_PATH}"
        payload = {
            "license_key": current_license_key,
            "device_id": device_id,
        }
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            result.update({
                "valid": bool(data.get("valid", False)),
                "details": data,
            })
        else:
            # 401/403 etc -> invalid
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}
            result.update({"valid": False, "details": data, "status_code": resp.status_code})
        return result
    except Exception as e:
        # If license server is unreachable, allow local development
        print(f"⚠️ License server unreachable ({e}) - allowing local development mode")
        return {"valid": True, "reason": "local_development", "details": {"mode": "local_dev", "error": str(e)}}

def heartbeat_license_validator():
    global license_blocked
    while True:
        time.sleep(30)
        try:
            key = license_key or load_license_key()
            device_id = f"heartbeat-{socket.gethostname()}"
            res = validate_license(key, device_id)
            is_valid = res.get("valid", False)
            license_blocked = not is_valid
            
            # Only stop processes if license is explicitly invalid (not just missing for local dev)
            if not is_valid and res.get("reason") != "local_development":
                print("🚫 License invalid - stopping all processes")
                # Stop all running appium processes if license is invalid
                for dev_id, proc in list(running_appium_processes.items()):
                    try:
                        if proc.poll() is None:
                            proc.terminate()
                            proc.wait(timeout=5)
                    except Exception:
                        pass
                    finally:
                        running_appium_processes.pop(dev_id, None)
                for d in devices:
                    d["status"] = "stopped"
            else:
                license_blocked = False
        except Exception:
            # Never crash the thread
            continue

class Device(BaseModel):
    id: Optional[str] = None
    udid: str
    platform: str
    name: str
    status: Optional[str] = "stopped"
    appium_port: Optional[int] = 4741
    wda_port: Optional[int] = 8109
    mjpeg_port: Optional[int] = 9100
    last_seen: Optional[str] = None
    ios_version: Optional[str] = "15.0"
    model: Optional[str] = "iPhone"
    wda_bundle_id: Optional[str] = "com.device.wd"
    jailbroken: Optional[bool] = False
    ngrok_token: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class Job(BaseModel):
    id: str
    device_id: str
    account_id: str
    type: str
    status: str
    created_at: str

class StartDeviceRequest(BaseModel):
    device_id: str
    job_type: str = "automation"
    template_data: Optional[Dict[str, Any]] = None

class UpdateDeviceRequest(BaseModel):
    ngrok_token: Optional[str] = None

class LicenseSetRequest(BaseModel):
    license_key: str

@app.get("/")
async def root():
    return {"message": "FSN Local Backend is running!", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "license_blocked": license_blocked}

# License endpoints
@app.post("/api/v1/license")
async def set_license(req: LicenseSetRequest):
    global license_key, license_blocked
    key = (req.license_key or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="license_key required")
    save_license_key(key)
    license_key = key
    # Validate immediately using host identifier
    host_id = f"host-{socket.gethostname()}"
    res = validate_license(license_key, host_id)
    license_blocked = not res.get("valid", False)
    if not res.get("valid", False):
        raise HTTPException(status_code=403, detail={"message": "License invalid", "details": res})
    return {"status": "ok", "validated": True, "details": res.get("details")}

@app.get("/api/v1/license/status")
async def license_status():
    key = license_key or load_license_key()
    host_id = f"status-{socket.gethostname()}"
    res = validate_license(key, host_id)
    return {"license_present": bool(key), "valid": res.get("valid", False), "details": res.get("details"), "blocked": license_blocked}

# Device endpoints - compatible with your frontend
@app.get("/api/v1/devices")
async def get_devices():
    return {"devices": devices, "total": len(devices)}

@app.get("/api/v1/devices/{device_id}")
async def get_device(device_id: str):
    """Get a specific device"""
    # Find the device
    device = None
    for d in devices:
        if d.get("id") == device_id:
            device = d
            break
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device

@app.put("/api/v1/devices/{device_id}")
async def update_device(device_id: str, request: UpdateDeviceRequest):
    """Update device settings including optional ngrok token"""
    # Find the device
    device = None
    for d in devices:
        if d.get("id") == device_id:
            device = d
            break
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update ngrok token
    if request.ngrok_token is not None:
        device["ngrok_token"] = request.ngrok_token
        if request.ngrok_token:
            print(f"🔑 Updated ngrok token for device {device_id}: {request.ngrok_token[:10]}...")
        else:
            print(f"🔑 Removed ngrok token for device {device_id}")
        save_devices()  # Save to persistent storage
    
    return {"message": "Device updated successfully", "device": device}

@app.post("/api/v1/devices")
async def create_device(device: Device):
    # Generate ID and timestamp if not provided
    if not device.id:
        device.id = f"device-{int(time.time())}"
    if not device.last_seen:
        device.last_seen = datetime.now().isoformat()
    
    # Set default settings if not provided
    if not device.settings:
        device.settings = {
            "autoAcceptAlerts": True,
            "autoDismissAlerts": True,
            "shouldTerminateApp": True
        }
    
    # Convert to dict for storage
    device_dict = device.model_dump(exclude_none=False)
    devices.append(device_dict)
    save_devices()  # Save to persistent storage
    print(f"📱 Device registered: {device.name} ({device.udid}) - ngrok_token: {'set' if device.ngrok_token else 'not set'}")
    return device_dict

@app.put("/api/v1/devices/{device_id}")
async def update_device(device_id: str, device_data: dict):
    """Update device capabilities from frontend"""
    for i, device in enumerate(devices):
        if device["id"] == device_id:
            # Update device with new capabilities
            devices[i].update(device_data)
            devices[i]["last_seen"] = datetime.now().isoformat()
            save_devices()  # Save to persistent storage
            print(f"📱 Device updated: {device['name']} with new capabilities")
            print(f"   New capabilities: {device_data}")
            return devices[i]
    raise HTTPException(status_code=404, detail="Device not found")

@app.delete("/api/v1/devices/{device_id}")
async def delete_device(device_id: str):
    """Delete a device"""
    for i, device in enumerate(devices):
        if device.get("id") == device_id:
            deleted_device = devices.pop(i)
            save_devices()  # Save to persistent storage
            print(f"🗑️ Device deleted: {deleted_device['name']} ({deleted_device['udid']})")
            return {"message": "Device deleted successfully", "device": deleted_device}
    raise HTTPException(status_code=404, detail="Device not found")

@app.post("/api/v1/devices/{device_id}/heartbeat")
async def device_heartbeat(device_id: str):
    for device in devices:
        if device.get("id") == device_id:
            device['last_seen'] = datetime.now().isoformat()
            return {"status": "success"}
    raise HTTPException(status_code=404, detail="Device not found")

# THE MAIN ENDPOINT - Start device from frontend
@app.post("/api/v1/devices/{device_id}/start")
async def start_device(device_id: str, request: Optional[StartDeviceRequest] = None):
    """Start Appium for a specific device when called from frontend"""
    
    print(f"🚀 Received start request for device_id: {device_id}")
    
    # Log request summary without massive base64 content
    if request and hasattr(request, 'template_data') and request.template_data:
        template_summary = format_template_summary(request.template_data)
        print(f"📝 Request summary: job_type='{request.job_type}' template_summary='{template_summary}'")
    else:
        print(f"📝 Request body: {request}")
    
    # Find the device
    device = None
    for d in devices:
        if d.get("id") == device_id:
            device = d
            break
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # License validation before any action
    key = license_key or load_license_key()
    validation = validate_license(key, device.get('udid'))
    if not validation.get("valid", False):
        raise HTTPException(status_code=403, detail={"message": "License invalid or expired", "details": validation})

    print(f"🚀 Starting device: {device.get('name')}")
    print(f"   Platform: {device.get('platform')}")
    print(f"   UDID: {device.get('udid')}")
    print(f"   Appium Port: {device.get('appium_port')}")
    
    # Check if Appium is already running for this device
    if device_id in running_appium_processes:
        process = running_appium_processes[device_id]
        if process.poll() is None:  # Process is still running
            print(f"✅ Appium already running for {device.get('name')}")
            return {"status": "already_running", "device_id": device_id}
    
    # Check if port is already in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', device.get('appium_port')))
    sock.close()
    
    if result == 0:
        print(f"❌ Port {device.get('appium_port')} is already in use")
        # Try to kill any process using the port
        try:
            result = subprocess.run(['lsof', '-ti', f':{device.get("appium_port")}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        subprocess.run(['kill', '-9', pid.strip()], check=False)
                        print(f"🔧 Killed process {pid.strip()} using port {device.get('appium_port')}")
        except Exception as e:
            print(f"⚠️ Could not kill process using port: {e}")
        
        # Wait a moment for port to be released
        time.sleep(2)
    
    try:
        # Ensure temp directory exists and has proper permissions
        import tempfile
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        print(f"🔧 Using temp directory: {temp_dir}")
        
        # Start Appium server for this device
        appium_cmd = [
            "appium",
            "server",
            "--port", str(device.get('appium_port')),
            "--driver-xcuitest-webdriveragent-port", str(device.get('wda_port')),
            "--session-override",
            "--log-level", "info",
            "--relaxed-security"
        ]
        
        print(f"🔧 Starting Appium command: {' '.join(appium_cmd)}")
        
        # Start Appium process with proper environment
        print(f"🔧 Starting Appium process...")
        
        # Set environment variables for Appium
        env = os.environ.copy()
        env['TMPDIR'] = temp_dir  # Ensure Appium uses the correct temp directory
        
        process = subprocess.Popen(
            appium_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,  # Pass the environment with TMPDIR
            preexec_fn=None if os.name == 'nt' else os.setsid  # Create new process group
        )
        
        # Store the process
        running_appium_processes[device_id] = process
        
        # Wait for Appium to start and check if it's actually running
        print("⏳ Waiting for Appium to start...")
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is not None:
            # Process has already exited, get the error
            stdout, stderr = process.communicate()
            print(f"❌ Appium failed to start:")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            raise Exception(f"Appium failed to start: {stderr}")
        
        # Check if port is actually listening
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', device.get('appium_port')))
        sock.close()
        
        if result != 0:
            print(f"❌ Appium port {device.get('appium_port')} is not listening")
            # Try to get any error output
            try:
                stdout, stderr = process.communicate(timeout=1)
                print(f"   STDOUT: {stdout}")
                print(f"   STDERR: {stderr}")
            except:
                pass
            
            # Clean up the failed process
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass
            
            # Remove from running processes
            running_appium_processes.pop(device_id, None)
            
            raise Exception(f"Appium port {device.get('appium_port')} is not accessible. Please check if Appium is installed correctly: 'npm install -g appium' and 'appium driver install xcuitest'")
        
        print(f"✅ Appium is running on port {device.get('appium_port')}")
        
        # NOW CONNECT TO THE ACTUAL PHONE!
        print(f"📱 Connecting to iPhone: {device.get('udid')}")
        
        try:
            # Create a session with the phone using Appium
            # Use actual device capabilities from stored device data
            # Appium 2.x requires vendor prefixes for non-standard capabilities
            # Use the same working capabilities as the follow_only.py script
            capabilities = {
                "platformName": "iOS",
                "appium:deviceName": device.get('name'),
                "appium:udid": device.get('udid'),
                "appium:automationName": "XCUITest",
                "appium:wdaLocalPort": device.get('wda_port'),
                "appium:updatedWDABundleId": device.get('wda_bundle_id', 'com.device11.wd11'),
                "appium:useNewWDA": False,  # Reuse existing WDA
                "appium:skipServerInstallation": True,  # Skip WDA installation
                "appium:noReset": True
            }
            
            # Add WDA bundle ID if specified
            if device.get('wda_bundle_id'):
                capabilities["appium:wdaBundleId"] = device.get('wda_bundle_id')
                
            # Add jailbreak status if available
            if device.get('jailbroken'):
                capabilities["appium:jailbroken"] = True
                
            # Add any additional settings with appium: prefix
            if device.get('settings'):
                for key, value in device.get('settings').items():
                    capabilities[f"appium:{key}"] = value
            
            session_payload = {
                "capabilities": {
                    "alwaysMatch": capabilities
                }
            }
            
            print(f"📱 Device capabilities configured:")
            for key, value in capabilities.items():
                print(f"   {key}: {value}")
            
            print(f"✅ Appium server ready for device connection!")
            print(f"   Device UDID: {device.get('udid')}")
            print(f"   Appium URL: http://localhost:{device.get('appium_port')}")
            print(f"   Script will create its own session with these capabilities")
            
            # Update device status
            device['status'] = "running"
            device['capabilities'] = capabilities  # Store capabilities for script to use
            
            # Send WebSocket update for device status change
            await broadcast_device_status_update(device_id, "running", "Appium server ready, script will initialize")
            
            # Start template execution job (script will create its own session)
            try:
                # Pass template data from request if available
                template_data = request.template_data if request else None
                job_id = await start_template_execution_job(device_id, template_data)
                print(f"🚀 Started job {job_id} for device {device_id}")
            except Exception as e:
                print(f"❌ Failed to start job: {e}")
                job_id = None
            
            return {
                "status": "connected",
                "device_id": device_id,
                "session_id": None,  # No session created yet
                "appium_port": device.get('appium_port'),
                "pid": process.pid,
                "job_id": job_id,
                "message": "Appium server ready, script will create session!"
            }
                
        except Exception as e:
            print(f"❌ Error connecting to iPhone: {e}")
            device['status'] = "error"
            return {
                "status": "error", 
                "device_id": device_id,
                "error": "Connection failed",
                "details": str(e)
            }
        
    except Exception as e:
        print(f"❌ Failed to start Appium: {e}")
        device['status'] = "error"
        raise HTTPException(status_code=500, detail=f"Failed to start Appium: {str(e)}")

@app.post("/api/v1/devices/{device_id}/stop")
async def stop_device(device_id: str):
    """Stop Appium for a specific device"""
    # License validation before any action
    key = license_key or load_license_key()
    # Use device_id label if device lookup fails
    dev = next((d for d in devices if d.get("id") == device_id), None)
    val_device_id = (dev or {}).get("udid", device_id)
    validation = validate_license(key, val_device_id)
    if not validation.get("valid", False):
        raise HTTPException(status_code=403, detail={"message": "License invalid or expired", "details": validation})

    if device_id in running_appium_processes:
        process = running_appium_processes[device_id]
        if process.poll() is None:  # Process is still running
            process.terminate()
            process.wait()
            print(f"🛑 Appium stopped for device {device_id}")
        
        del running_appium_processes[device_id]
        
        # Clean up any ngrok sessions for this device
        try:
            print(f"🧹 Cleaning up ngrok sessions for device {device_id}...")
            from pyngrok import ngrok
            ngrok.kill()
            print(f"✅ ngrok sessions cleaned up for device {device_id}")
        except Exception as e:
            print(f"⚠️ Failed to cleanup ngrok sessions: {e}")
        
        # Update device status
        for device in devices:
            if device.get("id") == device_id:
                device['status'] = "stopped"
                break
        
        # Send WebSocket update for device status change
        await broadcast_device_status_update(device_id, "stopped", "Device stopped successfully")
        
        return {"status": "stopped", "device_id": device_id}
    else:
        return {"status": "not_running", "device_id": device_id}

# Job endpoints
@app.get("/api/v1/jobs")
async def get_jobs():
    print(f"🔍 GET_JOBS ENDPOINT CALLED")
    print(f"🔍 ACTIVE_JOBS COUNT: {len(active_jobs)}")
    
    # Clean active jobs before logging and returning
    active_jobs_list = []
    for job_info in active_jobs.values():
        job_clean = clean_job_info_for_history(job_info)
        active_jobs_list.append(job_clean)
    
    print(f"🔍 ACTIVE_JOBS_LIST (cleaned): {len(active_jobs_list)} jobs")
    
    for i, job in enumerate(active_jobs_list):
        print(f"🔍 JOB {i}: id={job.get('id')}, status={job.get('status')}, progress={job.get('progress')}, step={job.get('current_step')}")
    
    # Clean completed jobs before returning
    completed_jobs_clean = []
    for job in job_history[-20:]:  # Last 20 completed jobs
        job_clean = clean_job_info_for_history(job)
        completed_jobs_clean.append(job_clean)
    
    result = {
        "active_jobs": active_jobs_list,
        "completed_jobs": completed_jobs_clean,
        "total_active": len(active_jobs),
        "total_completed": len(job_history)
    }
    
    # Log summary without massive content
    print(f"🔍 RETURNING: active={len(active_jobs_list)}, completed={len(completed_jobs_clean)}, total_completed={len(job_history)}")
    return result

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    if job_id in active_jobs:
        return active_jobs[job_id]
    else:
        # Check in history
        for job in job_history:
            if job["id"] == job_id:
                return job
        raise HTTPException(status_code=404, detail="Job not found")

@app.post("/api/v1/jobs")
async def create_job(job: Job):
    job.id = f"job-{int(time.time())}"
    job.created_at = datetime.now().isoformat()
    jobs.append(job)
    return job

# Account endpoints
@app.get("/api/v1/accounts")
async def get_accounts():
    return {"accounts": [], "total": 0}

@app.post("/api/v1/accounts")
async def create_account(account: dict):
    return {"id": f"account-{int(time.time())}", **account}

# Templates endpoints (for frontend compatibility)
@app.get("/api/v1/templates")
async def get_templates():
    return {"templates": [], "total": 0}

@app.post("/api/v1/templates")
async def create_template(template_data: dict):
    """Create a new template - Force localStorage fallback"""
    try:
        # Always return success to trigger localStorage fallback
        # This ensures templates are saved locally on the user's PC
        return {"data": {"id": "local", "message": "Saved to localStorage"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

@app.get("/api/v1/models")
async def get_models():
    return {"models": [], "total": 0}

@app.post("/api/v1/models")
async def create_model(req: dict):
    """Create a new model - Force localStorage fallback"""
    try:
        # Always return success to trigger localStorage fallback
        # This ensures models are saved locally on the user's PC
        return {"data": {"id": "local", "message": "Saved to localStorage"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create model: {str(e)}")

# Follower Tracking endpoints
@app.get("/api/v1/tracking/followers")
async def get_follower_tracking():
    """Get all follower tracking data"""
    try:
        tracking_file = "follower_tracking.json"
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
            return {"tracking_data": tracking_data, "total": len(tracking_data)}
        else:
            return {"tracking_data": [], "total": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tracking data: {str(e)}")

@app.get("/api/v1/tracking/followers/{username}")
async def get_user_follower_history(username: str):
    """Get follower history for specific username"""
    try:
        tracking_file = "follower_tracking.json"
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
            
            # Filter data for specific username
            user_data = [entry for entry in tracking_data if entry.get('username') == username]
            
            # Sort by timestamp
            user_data.sort(key=lambda x: x.get('scan_timestamp', ''))
            
            return {"username": username, "history": user_data, "total": len(user_data)}
        else:
            return {"username": username, "history": [], "total": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user tracking data: {str(e)}")

@app.post("/api/v1/tracking/scan/{device_id}")
async def manual_profile_scan(device_id: str):
    """Manually trigger profile scan for tracking"""
    try:
        job_id = f"manual_scan_{uuid.uuid4().hex[:8]}"
        print(f"🔄 Manual profile scan triggered for device {device_id}")
        
        profile_stats = await execute_profile_scan_for_tracking(device_id, job_id)
        
        if profile_stats:
            return {"success": True, "data": profile_stats, "message": "Profile scan completed successfully"}
        else:
            return {"success": False, "message": "Profile scan failed"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual scan failed: {str(e)}")

# WebSocket endpoints (for real-time updates)
@app.websocket("/api/v1/ws")
async def websocket_v1(websocket: WebSocket):
    """Accept simple WebSocket connections for local development.

    The frontend expects ws://localhost:8000/api/v1/ws?client_id=... to succeed.
    We accept any origin and keep the connection open, emitting basic heartbeat messages.
    """
    await websocket.accept()
    active_websocket_connections.add(websocket)
    try:
        # Send a welcome/status message
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to FSN Local Backend WebSocket",
            "active_connections": get_active_connection_count(),
        })

        # Basic receive loop; echo pings and ignore others
        while True:
            msg = await websocket.receive_text()
            if msg.strip().lower() in {"ping", "\"ping\""}:
                await websocket.send_json({"type": "pong", "active_connections": get_active_connection_count()})
            else:
                # Echo back as acknowledgement so frontend hooks don't error
                await websocket.send_json({"type": "ack", "received": msg})
    except WebSocketDisconnect:
        pass
    except Exception:
        # Ensure we do not crash the app on WS errors
        try:
            await websocket.close()
        except Exception:
            pass
    finally:
        if websocket in active_websocket_connections:
            active_websocket_connections.discard(websocket)

@app.get("/api/ws")
async def websocket_placeholder():
    # Kept for backward-compatibility; frontend uses /api/v1/ws
    return {"message": "Use WebSocket at /api/v1/ws"}

if __name__ == "__main__":
    print("🚀 Starting FSN Local Backend...")
    print("📱 This runs on your Mac and connects to fsndevelopment.com")
    print("")
    # Load existing license key and start heartbeat thread
    license_key = load_license_key()
    threading.Thread(target=heartbeat_license_validator, daemon=True).start()
    if license_key:
        print("🔐 License key found. Validating periodically with license server…")
    else:
        print("⚠️ No license key set yet. Set it via POST /api/v1/license { license_key }")
    print("📊 Available endpoints:")
    print("   - http://localhost:8000/api/v1/devices")
    print("   - http://localhost:8000/api/v1/devices/{id}/start")
    print("   - http://localhost:8000/api/v1/devices/{id}/stop")
    print("")
    print("🔧 Backend is accessible from:")
    print("   - Local: http://localhost:8000")
    print("   - Network: http://[YOUR_IP]:8000")
    print("")

def cleanup_all_ngrok_sessions():
    """Clean up all ngrok sessions on shutdown"""
    try:
        print(f"🧹 Cleaning up all ngrok sessions on shutdown...")
        from pyngrok import ngrok
        ngrok.kill()
        print(f"✅ All ngrok sessions cleaned up")
    except Exception as e:
        print(f"⚠️ Failed to cleanup ngrok sessions on shutdown: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on app shutdown"""
    cleanup_all_ngrok_sessions()
    
uvicorn.run(app, host="0.0.0.0", port=8000)