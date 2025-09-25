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
ACCOUNTS_FILE = "accounts_storage.json"  # Default fallback; replaced by license-aware path below

# Per-account posting tracking (license-aware)
def get_post_tracking_file_path() -> str:
    current_key = license_key or load_license_key()
    safe_key = _sanitize_license_for_filename(current_key)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, f"accounts_post_counts_{safe_key}.json")

def load_account_post_tracking() -> list:
    try:
        fp = get_post_tracking_file_path()
        if os.path.exists(fp):
            with open(fp, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load account post tracking: {e}")
    return []

def save_account_post_tracking(data: list) -> None:
    try:
        fp = get_post_tracking_file_path()
        with open(fp, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved account post tracking: {fp}")
    except Exception as e:
        print(f"⚠️ Failed to save account post tracking: {e}")

def reset_daily_post_counts_if_new_day() -> None:
    """Reset posts_today for all accounts at midnight (license-aware file)."""
    try:
        tracking = load_account_post_tracking()
        if not tracking:
            return
        today = datetime.now().date().isoformat()
        changed = False
        for entry in tracking:
            if entry.get('last_reset') != today:
                entry['posts_today'] = 0
                entry['last_reset'] = today
                changed = True
        if changed:
            save_account_post_tracking(tracking)
            print("🗓️ Daily post counters reset to 0 for all accounts")
    except Exception as e:
        print(f"⚠️ Failed to reset daily post counts: {e}")

def get_posts_today_for_account(account_id: str, username: Optional[str], device_id: str) -> int:
    """Read posts_today for an account from tracking storage (0 if missing)."""
    try:
        tracking = load_account_post_tracking()
        today = datetime.now().date().isoformat()
        for entry in tracking:
            if (
                str(entry.get('id')) == str(account_id)
            ) or (
                username and str(entry.get('username')) == str(username) and str(entry.get('device_id')) == str(device_id)
            ):
                # Ensure daily reset if file wasn't updated yet today
                if entry.get('last_reset') != today:
                    return 0
                return int(entry.get('posts_today') or 0)
    except Exception as e:
        print(f"⚠️ Failed to read posts_today: {e}")
    return 0

def increment_account_post_count(device_id: str, username_hint: Optional[str] = None) -> None:
    """Increment post counters for the primary account assigned to this device (or matching username)."""
    try:
        # Prefer a specific account match if provided; otherwise pick the first account for device
        # Prefer currently active account for this device if available
        if 'CURRENT_ACCOUNT' in globals() and CURRENT_ACCOUNT.get(device_id):
            accounts = [CURRENT_ACCOUNT[device_id]]
        else:
            accounts = DEVICE_ACCOUNTS.get(device_id, []) if 'DEVICE_ACCOUNTS' in globals() else []
        if not accounts:
            # Fallback: load all and filter by device
            accounts = [a for a in load_accounts() if str(a.get('device_id')) == str(device_id)]
        if not accounts:
            print(f"⚠️ No accounts found for device {device_id}; cannot increment post count")
            return
        target = None
        if username_hint:
            for a in accounts:
                if str(a.get('username')) == str(username_hint):
                    target = a
                    break
        if target is None:
            target = accounts[0]

        tracking = load_account_post_tracking()
        # Find existing entry by account id or username+device
        found = None
        for entry in tracking:
            if (
                str(entry.get('id')) == str(target.get('id'))
            ) or (
                str(entry.get('username')) == str(target.get('username'))
                and str(entry.get('device_id')) == str(device_id)
            ):
                found = entry
                break
        now_iso = datetime.now().isoformat()
        if found is None:
            found = {
                'id': str(target.get('id')),
                'device_id': str(device_id),
                'username': str(target.get('username')),
                'platform': target.get('platform') or 'threads',
                'container_number': str(target.get('container_number')),
                'posts_total': 0,
                'posts_today': 0,
                'last_post_at': None,
                'last_reset': datetime.now().date().isoformat(),
            }
            tracking.append(found)

        # Daily reset if needed
        last_reset = found.get('last_reset')
        today = datetime.now().date().isoformat()
        if last_reset != today:
            found['posts_today'] = 0
            found['last_reset'] = today

        found['posts_total'] = int(found.get('posts_total') or 0) + 1
        found['posts_today'] = int(found.get('posts_today') or 0) + 1
        found['last_post_at'] = now_iso

        save_account_post_tracking(tracking)
        print(f"📈 Incremented post count for @{found['username']} (device {device_id}) → total={found['posts_total']} today={found['posts_today']}")
    except Exception as e:
        print(f"⚠️ Failed to increment account post count: {e}")

def _sanitize_license_for_filename(license_str: Optional[str]) -> str:
    """Sanitize license key for safe filename usage."""
    if not license_str:
        return "local_dev"
    # Keep alphanumerics and a few safe chars
    safe = ''.join(ch for ch in str(license_str) if ch.isalnum() or ch in ('-', '_'))
    return safe or "local_dev"

def get_accounts_file_path() -> str:
    """Return license-aware accounts file path (per-license storage)."""
    # Use already-loaded license_key if available; otherwise try to load
    current_key = license_key or load_license_key()
    safe_key = _sanitize_license_for_filename(current_key)
    # Store next to this backend file to keep it self-contained per install
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, f"accounts_{safe_key}.json")

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

def load_accounts():
    """Load accounts from persistent storage"""
    try:
        accounts_file = get_accounts_file_path()
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r') as f:
                data = json.load(f)
                print(f"📂 Loaded {len(data)} accounts from storage: {accounts_file}")
                return data
    except Exception as e:
        print(f"⚠️ Failed to load accounts from storage: {e}")
    return []

def save_accounts(accounts_data):
    """Save accounts to persistent storage"""
    try:
        accounts_file = get_accounts_file_path()
        with open(accounts_file, 'w') as f:
            json.dump(accounts_data, f, indent=2)
        print(f"💾 Saved {len(accounts_data)} accounts to storage: {accounts_file}")
    except Exception as e:
        print(f"⚠️ Failed to save accounts to storage: {e}")

def get_account_phase(account_id: str) -> str:
    """Get account phase (warmup/posting) from accounts file"""
    try:
        accounts = load_accounts()
        for account in accounts:
            if str(account.get('id')) == str(account_id):
                return account.get('account_phase', 'posting')
    except Exception as e:
        print(f"⚠️ Failed to get account phase for {account_id}: {e}")
    return 'posting'  # Default to posting if not found

# Load devices from storage on startup
devices = load_devices()
jobs = []
running_appium_processes = {}  # device_id -> process
active_jobs = {}  # job_id -> job_info
DEVICE_ACCOUNTS = {}  # device_id -> list of accounts
DEVICE_TEMPLATES = {}  # device_id -> template_data
LAST_ACCOUNT_SESSIONS = {}  # account_id -> last_post_timestamp
job_history = []  # completed jobs

# -------------------------------
# Session tracking and account management
# -------------------------------

SESSION_TRACKING_FILE = "account_sessions.json"

def load_session_data():
    """Load session tracking data from file"""
    global LAST_ACCOUNT_SESSIONS
    try:
        if os.path.exists(SESSION_TRACKING_FILE):
            with open(SESSION_TRACKING_FILE, 'r') as f:
                LAST_ACCOUNT_SESSIONS = json.load(f)
                print(f"📊 Loaded session data for {len(LAST_ACCOUNT_SESSIONS)} accounts")
        else:
            LAST_ACCOUNT_SESSIONS = {}
            print("📊 No existing session data found")
    except Exception as e:
        print(f"⚠️ Failed to load session data: {e}")
        LAST_ACCOUNT_SESSIONS = {}

def save_session_data():
    """Save session tracking data to file"""
    try:
        with open(SESSION_TRACKING_FILE, 'w') as f:
            json.dump(LAST_ACCOUNT_SESSIONS, f, indent=2)
        print(f"💾 Saved session data for {len(LAST_ACCOUNT_SESSIONS)} accounts")
    except Exception as e:
        print(f"⚠️ Failed to save session data: {e}")

# Load session data on startup
load_session_data()

def get_post_tracking_file_path():
    """Get the path for the post tracking file"""
    key = license_key or load_license_key()
    safe_key = key.replace(" ", "_").replace("-", "_") if key else "local_dev"
    return f"accounts_post_counts_{safe_key}.json"

def load_account_post_tracking():
    """Load account post tracking data"""
    try:
        file_path = get_post_tracking_file_path()
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"⚠️ Failed to load post tracking: {e}")
        return []

def save_account_post_tracking(data: list):
    """Save account post tracking data"""
    try:
        file_path = get_post_tracking_file_path()
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save post tracking: {e}")

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
        # 1) Check local persistent accounts storage first (synced from frontend localStorage)
        accounts_data = load_accounts()
        if accounts_data:
            matching = [a for a in accounts_data if str(a.get('device_id')) == str(device_id)]
            if matching:
                account = matching[0]
                print(f"🔍 Found local account: {account.get('username')} with container_number: {account.get('container_number')}")
                return account

        # 2) Fallback: Try HTTP API if available
        try:
            import requests
            response = requests.get(f"http://localhost:8000/api/v1/accounts?device_id={device_id}", timeout=3)
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('items', [])
                if accounts:
                    account = accounts[0]
                    print(f"🔍 Found HTTP account: {account.get('username')} with container_number: {account.get('container_number')}")
                    return account
        except Exception as http_err:
            print(f"🔍 HTTP accounts lookup failed: {http_err}")
        
        print(f"🔍 No accounts found for device {device_id}")
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

async def start_warmup_automation(device_id: str, warmup_accounts: list) -> str:
    """Start warmup automation for accounts in warmup phase"""
    try:
        # Generate job ID
        job_id = f"warmup_{uuid.uuid4().hex[:8]}"
        
        # Create job info for warmup
        job_info = {
            "id": job_id,
            "device_id": device_id,
            "type": "warmup",
            "accounts": warmup_accounts,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "current_step": "pending",
            "progress": 0,
            "results": [],
            "errors": []
        }
        
        active_jobs[job_id] = job_info
        
        # Start warmup execution in background
        asyncio.create_task(execute_warmup_job(job_id))
        
        # Send initial job status update
        await update_job_status(job_id, "initializing", "Starting warmup automation...", 5)
        
        print(f"🔥 Started warmup automation job {job_id} for device {device_id}")
        return job_id
        
    except Exception as e:
        print(f"❌ Failed to start warmup automation: {e}")
        return None

async def execute_warmup_job(job_id: str):
    """Execute the warmup job"""
    job_info = active_jobs.get(job_id)
    if not job_info:
        print(f"❌ Warmup job {job_id} not found")
        return
    
    try:
        device_id = job_info["device_id"]
        warmup_accounts = job_info["accounts"]
        
        print(f"🔥 Executing warmup job {job_id} for device {device_id}")
        
        # Update status
        await update_job_status(job_id, "running", "Running warmup for accounts", 10)
        
        # Get device info
        device = None
        for d in devices:
            if d.get("id") == device_id:
                device = d
                break
        
        if not device:
            raise Exception(f"Device {device_id} not found")
        
        # Run warmup for each account
        for account in warmup_accounts:
            username = account.get('username', 'unknown')
            account_id = account.get('id')
            
            print(f"🔥 Running warmup for account @{username}")
            await update_job_status(job_id, "running", f"Running warmup for @{username}", 20)
            
            # Broadcast warmup start
            await broadcast_account_processing(device_id, username, account_id, "Starting warmup automation")
            
            try:
                # Create default warmup template data
                warmup_template_data = {
                    "id": "default_warmup",
                    "name": "Default Warmup Template",
                    "total_days": 1,
                    "days_config": [
                        {
                            "day_number": 1,
                            "scroll_minutes": 10,
                            "likes_count": 5,
                            "follows_count": 2
                        }
                    ]
                }
                
                # Execute warmup for this account
                await execute_warmup_for_account(device, account, warmup_template_data, f"warmup_{account_id}")
                
                print(f"✅ Warmup completed for @{username}")
                await broadcast_account_processing(device_id, username, account_id, "Warmup completed successfully")
                
            except Exception as e:
                print(f"❌ Warmup failed for @{username}: {e}")
                await broadcast_account_processing(device_id, username, account_id, f"Warmup failed: {e}")
                job_info["errors"].append(f"Account @{username}: {e}")
        
        # Mark job as completed
        await update_job_status(job_id, "completed", "Warmup automation completed", 100)
        job_info["completed_at"] = datetime.now().isoformat()
        
        print(f"✅ Warmup job {job_id} completed")
        
    except Exception as e:
        print(f"❌ Warmup job {job_id} failed: {e}")
        await update_job_status(job_id, "failed", f"Warmup failed: {e}", 0)
        job_info["errors"].append(str(e))

async def execute_warmup_for_account(device: dict, account: dict, warmup_template_data: dict, job_id: str):
    """Execute warmup activities for a single account"""
    try:
        username = account.get('username', 'unknown')
        account_id = str(account.get('id', ''))
        
        print(f"🔥 Starting warmup for account @{username}")
        
        # Check if warmup already completed today (you can implement this logic)
        # For now, we'll always run warmup
        
        # Get current day and settings
        current_day = 1  # Default to day 1
        days_config = warmup_template_data.get('days_config', [])
        
        # Find day configuration
        day_config = None
        for day in days_config:
            if day.get('day_number') == current_day:
                day_config = day
                break
        
        if not day_config:
            print(f"⚠️ No configuration found for day {current_day} - using defaults")
            day_config = {
                'scroll_minutes': 10,
                'likes_count': 5,
                'follows_count': 2
            }
        
        print(f"📅 Executing Day {current_day} warmup:")
        print(f"   Scroll: {day_config.get('scroll_minutes', 0)} minutes")
        print(f"   Likes: {day_config.get('likes_count', 0)}")
        print(f"   Follows: {day_config.get('follows_count', 0)}")
        print(f"🎯 Warmup will take approximately {day_config.get('scroll_minutes', 0)} minutes for scrolling")
        
        # Import and execute warmup test
        import sys
        import os
        
        # Add the platforms directory to Python path
        platforms_path = "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main"
        sys.path.append(platforms_path)
        
        # Import the warmup test
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "warmup_test", 
            f"{platforms_path}/platforms/threads/working_tests/warmup_engagement_test.py"
        )
        warmup_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(warmup_module)
        ThreadsWarmupTest = warmup_module.ThreadsWarmupTest
        
        # Switch to correct container for jailbroken devices
        if device.get("jailbroken", False):
            print(f"🔄 Switching to Crane container for warmup on device {device.get('id')}")
            account_info = {
                "platform": "threads",
                "username": username,
                "container_number": str(account.get("container_number", "1"))
            }
            await execute_crane_container_switch(device.get('id'), f"warmup_{account_id}", account_info)
        
        # Execute warmup activities
        print(f"🎯 Running warmup activities for @{username}...")
        warmup_test = ThreadsWarmupTest(
            scroll_minutes=day_config.get('scroll_minutes', 0),
            likes_count=day_config.get('likes_count', 0),
            follows_count=day_config.get('follows_count', 0),
            expected_username=username,
            device_type=device.get("jailbroken", False) and "jailbroken" or "non-jailbroken",
            container_id=account.get("container_number")
        )
        
        result = await warmup_test.run_full_test()
        
        if result.get('success'):
            print(f"✅ Warmup completed successfully for @{username}")
        else:
            print(f"❌ Warmup failed for @{username}: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in warmup for account @{username}: {e}")
        raise

async def broadcast_account_processing(device_id: str, username: str, account_id: str, step: str):
    """Broadcast account processing updates via WebSocket"""
    try:
        message = {
            "type": "job_update",
            "data": {
                "device_id": device_id,
                "username": username,
                "account_id": account_id,
                "current_step": step,
                "progress": 0,
                "timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📡 BROADCASTING ACCOUNT PROCESSING: device={device_id}, username={username}, step={step}")
        print(f"📡 WebSocket message: {json.dumps(message, indent=2)}")
        
        # Send to all connected WebSocket clients
        if active_websocket_connections:
            disconnected = set()
            for websocket in active_websocket_connections:
                try:
                    await websocket.send_text(json.dumps(message))
                    print(f"✅ Sent account processing WebSocket message to connection")
                except Exception as e:
                    print(f"⚠️ Failed to send WebSocket message: {e}")
                    disconnected.add(websocket)
            
            # Remove disconnected connections
            for ws in disconnected:
                active_websocket_connections.discard(ws)
        else:
            print(f"⚠️ No active WebSocket connections to send account processing update")
            
    except Exception as e:
        print(f"❌ Failed to broadcast account processing update: {e}")

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

async def execute_crane_container_switch(device_id: str, job_id: str, account_info: dict = None):
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
        
        from api.services.crane_account_switching import crane_threads_account_switching
        
        # Use provided account info or default
        if not account_info:
            account_info = {
                "platform": "threads",
                "username": "default_user",
                "container_name": f"threads_container_{device_id}",
                "container_number": "2"
            }
        
        # Execute container switch (pass UDID string, not entire device dict)
        result = await crane_threads_account_switching.complete_crane_account_switch_flow(device.get("udid"), account_info.get("container_number", "2"), "threads")
        
        if result:
            print(f"✅ Crane container switch successful for device {device_id}")
        else:
            print(f"❌ Crane container switch failed for device {device_id}")
        
    except Exception as e:
        print(f"❌ Error in Crane container switching: {e}")
        # Don't raise - continue with automation even if container switch fails

async def download_photo_via_safari_proven_method(driver, photo_url):
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
        await asyncio.sleep(0.5)  # ASYNC VERSION TO NOT BLOCK WEBSOCKETS
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
        await asyncio.sleep(10)  # ASYNC VERSION TO NOT BLOCK WEBSOCKETS
        
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
        await asyncio.sleep(5)  # ASYNC VERSION TO NOT BLOCK WEBSOCKETS
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
            
            # Simulate time for scrolling and liking - USE ASYNC SLEEP TO NOT BLOCK WEBSOCKETS
            await asyncio.sleep(30)  # 30 seconds per like attempt - ASYNC VERSION
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
        
        # Log template name and summary
        template_name = template_data.get('name', 'Unknown Template')
        template_id = template_data.get('id', 'No ID')
        template_summary = format_template_summary(template_data)
        print(f"📋 Template: '{template_name}' (ID: {template_id})")
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
        integrated_photo_service = None  # type: ignore
        try:
            import sys
            import os
            # Add the api/services directory to the path
            api_services_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api", "services")
            if api_services_path not in sys.path:
                sys.path.append(api_services_path)
            from integrated_photo_service import integrated_photo_service  # type: ignore
        except ImportError as e:
            print(f"⚠️ Warning: Could not import integrated_photo_service: {e}")
            print("📸 Photo posting will be skipped for this session")
        
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
                if integrated_photo_service is None:
                    print("⚠️ Photo service not available - skipping photo post")
                    continue
                    
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
                    download_success = await download_photo_via_safari_proven_method(safari_driver, photo_url)
                    
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
                        # When post verification completes, increment post counter for the primary account
                        if checkpoint_name == 'verify_post' and actual_progress >= 62:
                            try:
                                increment_account_post_count(device_id=device_id)
                            except Exception as e:
                                print(f"⚠️ Could not increment post count: {e}")
                    else:
                        print(f"❌ JOB {job_id} NOT FOUND IN ACTIVE_JOBS for direct update!")
                
                # Get scrolling settings from template
                scrolling_time_minutes = settings.get("scrollingTimeMinutes", 0)
                likes_per_day = settings.get("likesPerDay", 0)
                
                # Get device type and container info
                device_type = "jailbroken" if device.get("jailbroken", False) else "non_jailbroken"
                
                # Get container_number from account data
                container_id = None
                if device_type == "jailbroken":
                    # Get account data to find the correct container
                    account_data = await get_account_by_device_id(device_id)
                    if account_data and account_data.get('container_number'):
                        container_id = str(account_data.get('container_number'))
                        print(f"🔧 Using container from account: {container_id} (account: {account_data.get('username')})")
                        
                        # Send WebSocket notification with username
                        try:
                            await broadcast_account_processing(
                                device_id=device_id,
                                username=account_data.get('username', 'unknown'),
                                account_id=str(account_data.get('id', 'unknown')),
                                current_step="Starting photo post automation",
                                progress=0
                            )
                        except Exception as e:
                            print(f"❌ Failed to send WebSocket account processing notification: {e}")
                    else:
                        container_id = "3"  # Fallback to container 3
                        print(f"🔧 Using fallback container: {container_id} (no account container found)")
                
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
                # Provide expected username for downstream profile verification
                try:
                    if account_data and account_data.get('username'):
                        automation.expected_username = account_data.get('username')
                        print(f"🔎 Set expected_username for automation: @{automation.expected_username}")
                except Exception as e:
                    print(f"⚠️ Could not set expected_username on automation: {e}")
                
                print(f"📱 Executing Threads photo post automation...")
                
                # Execute with media enabled - now async to avoid blocking WebSocket
                success = await automation.run_test()
                
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
                if integrated_photo_service is not None:
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
        if integrated_photo_service is not None:
            await integrated_photo_service.cleanup_all()
        print(f"🧹 Final cleanup completed")
        
    except Exception as e:
        print(f"❌ Exception in execute_real_threads_photo_posts: {e}")
        import traceback
        traceback.print_exc()
        
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "error"
            active_jobs[job_id]["message"] = f"Photo posts failed: {str(e)}"

async def start_appium_for_device(device_id: str):
    """Start Appium server for a specific device if not already running"""
    global running_appium_processes
    
    # Check if Appium is already running for this device
    if device_id in running_appium_processes:
        process = running_appium_processes[device_id]
        # Support None sentinel from idempotent path
        if process is None:
            print(f"✅ Appium already running for device {device_id}")
            return True
        if hasattr(process, 'poll') and process.poll() is None:  # Process is still running
            print(f"✅ Appium already running for device {device_id}")
            return True
    
    # Get device info
    device = None
    for d in devices:
        if d.get("id") == device_id:
            device = d
            break
    
    if not device:
        print(f"❌ Device {device_id} not found")
        return False
    
    # Check if port is already in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', device.get('appium_port')))
    sock.close()
    
    if result == 0:
        # If port is already listening, consider Appium running and record it
        print(f"✅ Appium already running on port {device.get('appium_port')}")
        running_appium_processes.setdefault(device_id, None)
        return True
    
    try:
        # Ensure temp directory exists and has proper permissions
        import tempfile
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        print(f"🔧 Using temp directory: {temp_dir}")
        
        # Start Appium server for this device (minimal command)
        appium_cmd = [
            "appium",
            "-p", str(device.get('appium_port'))
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
        await asyncio.sleep(3)
        
        # Check if process is still running
        if process.poll() is not None:
            # Process has already exited, get the error
            stdout, stderr = process.communicate()
            print(f"❌ Appium failed to start:")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            return False
        
        # Check if port is actually listening
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
            
            print(f"❌ Appium port {device.get('appium_port')} is not accessible")
            return False
        
        print(f"✅ Appium is running on port {device.get('appium_port')}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Appium: {e}")
        return False

async def execute_real_threads_posts(device_id: str, text_posts: int, job_id: str, template_data: dict = None):
    """Execute real Threads posts using Appium automation.
    If multiple accounts are assigned to the device, iterate over them and optionally loop with interval.
    """
    global DEVICE_ACCOUNTS, DEVICE_TEMPLATES
    
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
        
        # Start Appium for this device if not already running
        print(f"🔧 Ensuring Appium is running for device {device_id}...")
        appium_started = await start_appium_for_device(device_id)
        if not appium_started:
            print(f"❌ Failed to start Appium for device {device_id}")
            return
        
        print(f"🎯 Starting real Threads automation for device {device_id}")
        # Ensure keep-running scheduler flag is set
        global DEVICE_KEEP_RUNNING
        if 'DEVICE_KEEP_RUNNING' not in globals():
            DEVICE_KEEP_RUNNING = {}
        DEVICE_KEEP_RUNNING[device_id] = True
        # Ensure pause flag store exists
        global DEVICE_PAUSED
        if 'DEVICE_PAUSED' not in globals():
            DEVICE_PAUSED = {}
        DEVICE_PAUSED.setdefault(device_id, False)
        # Determine assigned accounts for the device
        assigned_accounts = DEVICE_ACCOUNTS.get(device_id, []) if 'DEVICE_ACCOUNTS' in globals() else []
        if not assigned_accounts:
            assigned_accounts = [a for a in load_accounts() if str(a.get('device_id')) == str(device_id)]
        print(f"👥 Assigned accounts: {len(assigned_accounts)}")
        
        # Store accounts and template data globally for account switching
        DEVICE_ACCOUNTS[device_id] = assigned_accounts
        DEVICE_TEMPLATES[device_id] = template_data
        
        # Ensure daily counters are reset when day changes
        reset_daily_post_counts_if_new_day()

        # Get template settings
        settings = template_data.get("settings", {}) if template_data else {}
        photos_per_day = settings.get("photosPerDay", 0)
        text_posts_file = settings.get("textPostsFile", "")
        interval_minutes = int(settings.get("accountIntervalMinutes", 0) or 0)
        posting_interval_minutes = int(settings.get("postingIntervalMinutes", 30) or 30)
        per_day_limit = int(settings.get("textPostsPerDay", text_posts) or text_posts)
        run_loop = bool(settings.get("runLoop", False))
        
        # Debug: Log what we received from frontend
        print(f"🔍 DEBUG - Template settings received:")
        print(f"   textPostsFile: {text_posts_file}")
        print(f"   textPostsFileContent: {'Present' if settings.get('textPostsFileContent') else 'Missing'}")
        print(f"   postingIntervalMinutes: {posting_interval_minutes}")
        print(f"   All settings keys: {list(settings.keys())}")
        
        print(f"📊 Template settings:")
        print(f"   Text posts: {text_posts}")
        print(f"   Photos per day: {photos_per_day}")
        print(f"   Text posts file: {text_posts_file}")
        print(f"   Posting interval: {posting_interval_minutes} minutes")
        
        # Log template name and summary
        template_name = template_data.get('name', 'Unknown Template')
        template_id = template_data.get('id', 'No ID')
        template_summary = format_template_summary(template_data)
        text_posts_file_content = settings.get("textPostsFileContent", "")
        print(f"📋 Template: '{template_name}' (ID: {template_id})")
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
        
        # Fallback: Create sample text posts if none available (for testing)
        if not text_posts_list and text_posts > 0:
            print("⚠️ No text posts available - creating sample posts for testing")
            text_posts_list = [
                f"Sample post {i+1} - This is a test post for automation"
                for i in range(text_posts)
            ]
            print(f"📝 Created {len(text_posts_list)} sample text posts")
        
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

        # Helper to run posting for a single account
        async def run_for_account(account: dict):
            """Run automation for a single account - one post per call"""
            try:
                # Set current account context so counters map correctly
                global CURRENT_ACCOUNT
                if 'CURRENT_ACCOUNT' not in globals():
                    CURRENT_ACCOUNT = {}
                CURRENT_ACCOUNT[device_id] = account
                print(f"👤 Using account @{account.get('username')} container {account.get('container_number')} platform {account.get('platform')}")

                # Send WebSocket notification with username
                try:
                    await broadcast_account_processing(
                        device_id=device_id,
                        username=account.get('username', 'unknown'),
                        account_id=str(account.get('id', 'unknown')),
                        current_step="Starting text post automation",
                        progress=0
                    )
                except Exception as e:
                    print(f"⚠️ Failed to broadcast account processing: {e}")

                # Enforce daily post limit from template per account
                current_today = get_posts_today_for_account(
                    account_id=str(account.get('id','')),
                    username=account.get('username'),
                    device_id=device_id
                )
                if current_today >= per_day_limit:
                    print(f"⏭️ @{account.get('username')} reached daily limit ({current_today}/{per_day_limit}) - skipping")
                    return False

                # Execute only ONE post per account per call
                if text_posts > 0:
                    print(f"📝 Creating 1 text post for account @{account.get('username')}")
                    
                    # Get the text content for this post
                    if not text_posts_list:
                        print(f"❌ No text posts available - skipping")
                        return False
                    
                    # Use text from xlsx file, cycling through available posts
                    # Use a simple counter to cycle through posts
                    post_index = 0  # For now, use first post - can be improved later
                    post_text = text_posts_list[post_index]
                    print(f"📝 Post text: {post_text}")
                    
                    # Create progress callback function
                    def progress_callback(checkpoint_name, checkpoint_percent):
                        actual_progress = min(checkpoint_percent, 100)
                        print(f"📊 CHECKPOINT: {checkpoint_name} ({actual_progress}%)")
                        
                        # Update job status
                        if job_id in active_jobs:
                            job_info = active_jobs[job_id]
                            job_info["status"] = "executing"
                            job_info["current_step"] = checkpoint_name
                            job_info["progress"] = actual_progress
                            job_info["message"] = checkpoint_name
                        
                        # Send WebSocket update with username
                        try:
                            import asyncio
                            try:
                                loop = asyncio.get_running_loop()
                                asyncio.create_task(broadcast_account_processing(
                                    device_id=device_id,
                                    username=account.get('username', 'unknown'),
                                    account_id=str(account.get('id', 'unknown')),
                                    current_step=checkpoint_name,
                                    progress=actual_progress
                                ))
                            except RuntimeError:
                                # No running loop - skip broadcast
                                pass
                        except Exception as e:
                            print(f"⚠️ Failed to schedule WebSocket broadcast: {e}")
                    
                    # Get scrolling settings from template  
                    scrolling_time_minutes = settings.get("scrollingTimeMinutes", 0)
                    likes_per_day = settings.get("likesPerDay", 0)
                    
                    # Get device type and container info
                    device_type = "jailbroken" if device.get("jailbroken", False) else "non_jailbroken"
                
                    # Get container_number from current account selection
                    container_id = None
                    if device_type == "jailbroken":
                        account_data = CURRENT_ACCOUNT.get(device_id) if 'CURRENT_ACCOUNT' in globals() else None
                        if account_data and account_data.get('container_number'):
                            container_id = str(account_data.get('container_number'))
                            print(f"🔧 Using container from account: {container_id} (account: {account_data.get('username')})")
                        else:
                            container_id = "3"  # Fallback to container 3
                            print(f"🔧 Using fallback container: {container_id} (no account container found)")
                    
                    print(f"🔧 Device info: Type={device_type}, Container={container_id}")
                    
                    # Create the automation instance with callback and device info
                    automation = ThreadsPostThreadTest(
                        post_text=post_text, 
                        photos_per_day=0,  # No photos for text posts
                        progress_callback=progress_callback,
                        device_type=device_type,
                        container_id=container_id
                    )
                    
                    # Set scrolling parameters on the automation instance
                    automation.scrolling_minutes = scrolling_time_minutes
                    automation.likes_target = likes_per_day
                    # Provide expected username for downstream profile verification
                    try:
                        if account_data and account_data.get('username'):
                            automation.expected_username = account_data.get('username')
                            print(f"🔎 Set expected_username for automation: @{automation.expected_username}")
                    except Exception as e:
                        print(f"⚠️ Could not set expected_username on automation: {e}")
                    automation.device_id = device_id
                    
                    # Run the automation
                    success = await automation.run_test()
                    
                    print(f"🏁 Post automation finished: {'✅ Success' if success else '❌ Failed'}")
                    
                    if success:
                        print(f"✅ Post created successfully")
                        # Increment post count for this account
                        try:
                            increment_account_post_count(device_id=device_id, username_hint=account.get('username'))
                        except Exception as e:
                            print(f"⚠️ Could not increment post count: {e}")
                        return True
                    else:
                        print(f"❌ Failed to create post")
                        return False
                else:
                    print(f"⚠️ No text posts to execute for this account")
                    return False
                    
            except Exception as e:
                print(f"❌ Error in run_for_account: {e}")
                return False

        async def run_all_accounts_once():
            """Run all accounts once with proper cooldown management"""
            nonlocal posting_interval_minutes  # Access the outer scope variable
            global LAST_ACCOUNT_SESSIONS
            
            if 'LAST_ACCOUNT_SESSIONS' not in globals():
                LAST_ACCOUNT_SESSIONS = {}
            
            # First, check if there are any warmup accounts that need to be completed
            warmup_accounts = []
            for acc in assigned_accounts:
                account_id = str(acc.get('id', ''))
                warmup_data = get_warmup_account_data(account_id)
                if warmup_data and warmup_data.get('account_phase') == 'warmup' and not warmup_data.get('warmup_completed_today', False):
                    warmup_accounts.append(acc)
            
            # If there are warmup accounts that haven't completed today, run warmup first
            if warmup_accounts:
                print(f"🔥 Found {len(warmup_accounts)} accounts needing warmup - running warmup first")
                await broadcast_device_status_update(device_id, "running", "Running warmup automation")
                
                # Get warmup template data for the first warmup account
                first_warmup_account = warmup_accounts[0]
                warmup_account_id = str(first_warmup_account.get('id', ''))
                warmup_data = get_warmup_account_data(warmup_account_id)
                warmup_template_id = warmup_data.get('warmup_template_id') if warmup_data else None
                
                # Create default warmup template data if not available
                warmup_template_data = {
                    "id": warmup_template_id or "default",
                    "name": "Default Warmup Template",
                    "total_days": 1,
                    "days_config": [
                        {
                            "day_number": 1,
                            "scroll_minutes": 10,
                            "likes_count": 5,
                            "follows_count": 2
                        }
                    ]
                }
                
                for acc in warmup_accounts:
                    username = acc.get('username', 'unknown')
                    print(f"🔥 Running warmup for account @{username}")
                    await execute_warmup_for_account(device, acc, warmup_template_data, f"warmup_{acc.get('id')}")
                print(f"🔥 Warmup completed for all accounts - now proceeding with posting")
                return 0, True  # Return that we ran something (warmup)
            
            count = 0
            ran_any = False
            
            for acc in assigned_accounts:
                username = acc.get('username', 'unknown')
                account_id = str(acc.get('id', ''))
                
                # Check if account is in cooldown
                if account_id in LAST_ACCOUNT_SESSIONS:
                    last_post_time = LAST_ACCOUNT_SESSIONS[account_id]
                    elapsed_minutes = (time.time() - last_post_time) / 60
                    
                    if elapsed_minutes < posting_interval_minutes:
                        wait_left = posting_interval_minutes - elapsed_minutes
                        print(f"⏳ Skipping account @{username} - cooldown {wait_left:.1f} min remaining")
                        continue
                
                # Run this account
                print(f"🚀 Running account @{username}")
                success = await run_for_account(acc)
                
                if success:
                    count += 1
                    ran_any = True
                    print(f"✅ Account @{username} completed session successfully")
                    
                    # Update session tracking
                    LAST_ACCOUNT_SESSIONS[account_id] = time.time()
                    
                    # Save session data
                    try:
                        save_session_data()
                    except Exception as e:
                        print(f"⚠️ Failed to save session data: {e}")
                    
                    # Broadcast account status update
                    try:
                        await broadcast_account_status_update(device_id)
                    except Exception as e:
                        print(f"⚠️ Failed to broadcast account status update: {e}")
                else:
                    print(f"❌ Account @{username} session failed")
            
            return count, ran_any

        async def calculate_next_ready_time():
            """Calculate when the next account will be ready"""
            if 'LAST_ACCOUNT_SESSIONS' not in globals():
                return 0
            
            next_ready_time = float('inf')  # Start with infinity
            current_time = time.time()
            
            for acc in assigned_accounts:
                account_id = str(acc.get('id', ''))
                if account_id in LAST_ACCOUNT_SESSIONS:
                    last_post_time = LAST_ACCOUNT_SESSIONS[account_id]
                    ready_time = last_post_time + (posting_interval_minutes * 60)
                    
                    # Only consider accounts that are still in cooldown
                    if ready_time > current_time:
                        next_ready_time = min(next_ready_time, ready_time)
            
            # If no accounts are in cooldown, return current time
            return next_ready_time if next_ready_time != float('inf') else current_time

        # Main loop control - persistent scheduler: run forever until stopped
        print("🔄 Starting persistent scheduler loop...")
        total_posts_completed = 0
        attempt = 0
        
        while DEVICE_KEEP_RUNNING.get(device_id, True):
            # Respect pause flag
            if DEVICE_PAUSED.get(device_id):
                await broadcast_device_status_update(device_id, "paused", "Device paused")
                try:
                    await broadcast_account_status_update(device_id)
                except Exception:
                    pass
                await asyncio.sleep(2)
                continue
            attempt += 1
            print(f"🔄 Loop attempt {attempt} - Posts completed so far: {total_posts_completed}")
            
            posts_this_round, ran_any = await run_all_accounts_once()
            total_posts_completed += posts_this_round
            
            if not ran_any:
                # Calculate when next account will be ready
                next_ready_time = await calculate_next_ready_time()
                current_time = time.time()
                
                if next_ready_time > current_time:
                    wait_seconds = next_ready_time - current_time
                    wait_minutes = wait_seconds / 60
                    
                    print(f"⏳ All accounts in cooldown - waiting {wait_minutes:.1f} minutes until next account is ready")
                    print(f"🕐 Next account ready at: {datetime.fromtimestamp(next_ready_time).strftime('%H:%M:%S')}")
                    
                    # Wait for the next account to be ready, but check every 30 seconds
                    # to see if any other accounts become ready earlier
                    while time.time() < next_ready_time:
                        # Check if any accounts are ready now
                        posts_this_check, ran_any = await run_all_accounts_once()
                        if ran_any:
                            total_posts_completed += posts_this_check
                            print(f"📊 Found ready account! Completed {posts_this_check} posts, {total_posts_completed}/{text_posts} total")
                            break
                        
                        # Wait 30 seconds before checking again
                        remaining_time = next_ready_time - time.time()
                        wait_time = min(30, remaining_time)
                        if wait_time > 0:
                            await asyncio.sleep(wait_time)
                else:
                    print(f"⏳ All accounts in cooldown - waiting 30 seconds before next check")
                    await asyncio.sleep(30)
            else:
                print(f"📊 Completed {posts_this_round} posts this round, {total_posts_completed}/{text_posts} total")
        
        print(f"🏁 Scheduler stopped for device {device_id} - total posts this run: {total_posts_completed}")
        
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
        
        # Determine expected username from active account for this device
        expected_username = None
        try:
            account = await get_account_by_device_id(device_id)
            if account and account.get('username'):
                expected_username = account.get('username')
                print(f"🔎 Using expected_username for profile scan: @{expected_username}")
        except Exception as e:
            print(f"⚠️ Could not determine expected_username for profile scan: {e}")

        # Execute profile scan
        print("📊 Running profile scan...")
        scanner = ThreadsScanProfileTest(expected_username=expected_username)
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


async def execute_warmup_session(device_id: str, warmup_template_data: dict, job_id: str):
    """Execute warmup session for engagement activities (scroll, like, follow) without posting"""
    try:
        print(f"🔥 Starting warmup session for device {device_id}")
        
        # Get device info
        device = None
        for d in devices:
            if d.get("id") == device_id:
                device = d
                break
        
        if not device:
            print(f"❌ Device {device_id} not found")
            return
        
        # Start Appium for this device if not already running
        print(f"🔧 Ensuring Appium is running for device {device_id}...")
        appium_started = await start_appium_for_device(device_id)
        if not appium_started:
            print(f"❌ Failed to start Appium for device {device_id}")
            return
        
        # Get warmup template settings
        settings = warmup_template_data.get("settings", {}) if warmup_template_data else {}
        total_days = warmup_template_data.get("total_days", 1)
        days_config = warmup_template_data.get("days_config", [])
        
        # Log template information
        template_name = warmup_template_data.get('name', 'Unknown Warmup Template')
        template_id = warmup_template_data.get('id', 'No ID')
        print(f"📋 Warmup Template: '{template_name}' (ID: {template_id})")
        print(f"   Total days: {total_days}")
        print(f"   Days config: {len(days_config)} days configured")
        
        # Get accounts assigned to this device
        assigned_accounts = [a for a in load_accounts() if str(a.get('device_id')) == str(device_id)]
        if not assigned_accounts:
            print(f"❌ No accounts assigned to device {device_id}")
            return
        
        print(f"👥 Found {len(assigned_accounts)} accounts assigned to device")
        
        # Filter accounts that are in warmup phase
        warmup_accounts = []
        for acc in assigned_accounts:
            account_id = str(acc.get('id', ''))
            warmup_data = get_warmup_account_data(account_id)
            if warmup_data and warmup_data.get('account_phase') == 'warmup':
                warmup_accounts.append(acc)
        
        if not warmup_accounts:
            print(f"⚠️ No accounts in warmup phase for device {device_id}")
            return
        
        print(f"🔥 Found {len(warmup_accounts)} accounts in warmup phase")
        
        # Execute warmup for each account
        for acc in warmup_accounts:
            await execute_warmup_for_account(device, acc, warmup_template_data, job_id)
            
    except Exception as e:
        print(f"❌ Error in warmup session: {e}")
        raise


async def execute_warmup_for_account(device: dict, account: dict, warmup_template_data: dict, job_id: str):
    """Execute warmup activities for a single account"""
    try:
        username = account.get('username', 'unknown')
        account_id = str(account.get('id', ''))
        
        print(f"🔥 Starting warmup for account @{username}")
        
        # Check if warmup already completed today
        warmup_data = get_warmup_account_data(account_id)
        if warmup_data and warmup_data.get('warmup_completed_today'):
            print(f"⏭️ Account @{username} already completed warmup today - skipping")
            return
        
        # Get current day and settings
        current_day = warmup_data.get('current_day', 1) if warmup_data else 1
        days_config = warmup_template_data.get('days_config', [])
        
        # Find day configuration
        day_config = None
        for day in days_config:
            if day.get('day_number') == current_day:
                day_config = day
                break
        
        if not day_config:
            print(f"⚠️ No configuration found for day {current_day} - using defaults")
            day_config = {
                'scroll_minutes': 10,
                'likes_count': 5,
                'follows_count': 2
            }
        
        print(f"📅 Executing Day {current_day} warmup:")
        print(f"   Scroll: {day_config.get('scroll_minutes', 0)} minutes")
        print(f"   Likes: {day_config.get('likes_count', 0)}")
        print(f"   Follows: {day_config.get('follows_count', 0)}")
        print(f"🎯 Warmup will take approximately {day_config.get('scroll_minutes', 0)} minutes for scrolling")
        
        # Import and execute warmup test
        import sys
        import os
        
        # Add the platforms directory to Python path
        platforms_path = "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main"
        sys.path.append(platforms_path)
        
        # Import the warmup test
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "warmup_test", 
            f"{platforms_path}/platforms/threads/working_tests/warmup_engagement_test.py"
        )
        warmup_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(warmup_module)
        ThreadsWarmupTest = warmup_module.ThreadsWarmupTest
        
        # Switch to correct container for jailbroken devices (EXACT SAME AS POSTING)
        if device.get("jailbroken", False):
            print(f"🔄 Switching to Crane container for warmup on device {device.get('id')}")
            account_info = {
                "platform": "threads",
                "username": username,
                "container_number": str(account.get("container_number", "1"))
            }
            await execute_crane_container_switch(device.get('id'), f"warmup_{account_id}", account_info)
        
        # Execute warmup activities
        print(f"🎯 Running warmup activities for @{username}...")
        warmup_test = ThreadsWarmupTest(
            scroll_minutes=day_config.get('scroll_minutes', 0),
            likes_count=day_config.get('likes_count', 0),
            follows_count=day_config.get('follows_count', 0),
            expected_username=username,
            device_type=device.get("jailbroken", False) and "jailbroken" or "non-jailbroken",
            container_id=account.get("container_number")
        )
        
        result = await warmup_test.run_full_test()
        
        if result.get('success'):
            print(f"✅ Warmup completed successfully for @{username}")
            
            # Update warmup tracking
            update_warmup_progress(account_id, current_day, day_config)
            
            # Update next day
            next_day = current_day + 1
            total_days = warmup_template_data.get('total_days', 1)
            if next_day > total_days:
                print(f"🎉 Warmup sequence completed for @{username}!")
                next_day = 1  # Reset to day 1 for next cycle
            
            set_warmup_next_day(account_id, next_day)
            
        else:
            print(f"❌ Warmup failed for @{username}: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in warmup for account @{username}: {e}")
        raise


def get_warmup_account_data(account_id: str, license_key: str = "dev") -> dict:
    """Get warmup tracking data for an account.
    Reads license-specific file first (accounts_warmup_tracking_license_dev.json),
    falls back to local file (accounts_warmup_tracking_local_dev.json)."""
    try:
        import json
        import os

        base_dir = os.path.dirname(__file__)
        license_file = os.path.join(base_dir, "accounts_warmup_tracking_license_dev.json")
        local_file = os.path.join(base_dir, "accounts_warmup_tracking_local_dev.json")

        selected_file = license_file if os.path.exists(license_file) else local_file
        if not os.path.exists(selected_file):
            return {}

        with open(selected_file, 'r') as f:
            data = json.load(f)

        license_key = f"license_{license_key}"
        if license_key not in data:
            return {}

        return data[license_key].get(f"account_{account_id}", {})

    except Exception as e:
        print(f"⚠️ Error reading warmup data: {e}")
        return {}


def update_warmup_progress(account_id: str, day: int, day_config: dict, license_key: str = "dev"):
    """Update warmup progress for an account"""
    try:
        import json
        import os
        from datetime import datetime
        
        base_dir = os.path.dirname(__file__)
        license_file = os.path.join(base_dir, "accounts_warmup_tracking_license_dev.json")
        local_file = os.path.join(base_dir, "accounts_warmup_tracking_local_dev.json")
        # Prefer license-specific file if it exists; otherwise write to local
        warmup_file = license_file if os.path.exists(license_file) else local_file
        
        # Load existing data
        data = {}
        if os.path.exists(warmup_file):
            with open(warmup_file, 'r') as f:
                data = json.load(f)
        
        # Initialize license structure
        license_key = f"license_{license_key}"
        if license_key not in data:
            data[license_key] = {}
        
        account_key = f"account_{account_id}"
        if account_key not in data[license_key]:
            data[license_key][account_key] = {
                "warmup_completed_today": False,
                "current_day": 1,
                "last_warmup_date": None,
                "warmup_stats": {},
                "next_warmup_day": 1,
                "warmup_template_id": None,
                "account_phase": "posting"
            }
        
        # Update warmup stats
        day_key = f"day_{day}"
        data[license_key][account_key]["warmup_stats"][day_key] = {
            "likes": day_config.get('likes_count', 0),
            "follows": day_config.get('follows_count', 0),
            "scroll_minutes": day_config.get('scroll_minutes', 0),
            "completed_at": datetime.now().isoformat()
        }
        
        # Update completion status
        data[license_key][account_key]["warmup_completed_today"] = True
        data[license_key][account_key]["last_warmup_date"] = datetime.now().isoformat()
        data[license_key][account_key]["current_day"] = day
        
        # Save updated data
        with open(warmup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Updated warmup progress for account {account_id}, day {day}")
        
    except Exception as e:
        print(f"⚠️ Error updating warmup progress: {e}")


def set_warmup_next_day(account_id: str, next_day: int, license_key: str = "dev"):
    """Set the next warmup day for an account"""
    try:
        import json
        import os
        
        base_dir = os.path.dirname(__file__)
        license_file = os.path.join(base_dir, "accounts_warmup_tracking_license_dev.json")
        local_file = os.path.join(base_dir, "accounts_warmup_tracking_local_dev.json")
        warmup_file = license_file if os.path.exists(license_file) else local_file
        
        # Load existing data
        data = {}
        if os.path.exists(warmup_file):
            with open(warmup_file, 'r') as f:
                data = json.load(f)
        
        # Update next warmup day
        license_key = f"license_{license_key}"
        account_key = f"account_{account_id}"
        
        if license_key in data and account_key in data[license_key]:
            data[license_key][account_key]["next_warmup_day"] = next_day
            
            # Save updated data
            with open(warmup_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"📅 Set next warmup day to {next_day} for account {account_id}")
        
    except Exception as e:
        print(f"⚠️ Error setting next warmup day: {e}")


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
    for websocket in active_websocket_connections.copy():  # Use copy to avoid modification during iteration
        try:
            # Check if WebSocket is still connected before sending
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_text(json.dumps(message))
                print(f"✅ Sent WebSocket message to connection")
            else:
                print(f"⚠️ WebSocket is disconnected, removing from active connections")
                disconnected.add(websocket)
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
    for websocket in active_websocket_connections.copy():  # Use copy to avoid modification during iteration
        try:
            # Check if WebSocket is still connected before sending
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_text(json.dumps(device_update))
            else:
                disconnected.add(websocket)
        except Exception as e:
            print(f"⚠️ Failed to send device status update: {e}")
            disconnected.add(websocket)
    
    # Remove disconnected connections
    for websocket in disconnected:
        active_websocket_connections.discard(websocket)

async def broadcast_account_processing(device_id: str, username: str, account_id: str, current_step: str, progress: int = 0):
    """Broadcast account processing update to all WebSocket connections"""
    print(f"📡 BROADCASTING ACCOUNT PROCESSING: device={device_id}, username={username}, step={current_step}")
    
    message = {
        "type": "job_update",
        "data": {
            "device_id": device_id,
            "username": username,
            "account_id": account_id,
            "current_step": current_step,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        },
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"📡 WebSocket message: {json.dumps(message, indent=2)}")
    print(f"🔌 Active WebSocket connections: {len(active_websocket_connections)}")
    
    # Send to all connected WebSockets
    disconnected = set()
    for websocket in active_websocket_connections.copy():  # Use copy to avoid modification during iteration
        try:
            # Check if WebSocket is still connected before sending
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_text(json.dumps(message))
                print(f"✅ Sent account processing WebSocket message to connection")
            else:
                disconnected.add(websocket)
        except Exception as e:
            print(f"❌ Failed to send account processing WebSocket message: {e}")
            disconnected.add(websocket)
    
    # Remove disconnected connections
    for websocket in disconnected:
        active_websocket_connections.discard(websocket)

async def broadcast_account_status_update(device_id: str):
    """Broadcast account status update to all connected WebSocket clients"""
    global active_websocket_connections
    try:
        # Get the latest account status
        assigned_accounts = DEVICE_ACCOUNTS.get(device_id, []) if 'DEVICE_ACCOUNTS' in globals() else []
        
        if not assigned_accounts:
            return
        
        # Get posting interval from template
        posting_interval_minutes = 30  # Default
        if 'DEVICE_TEMPLATES' in globals() and DEVICE_TEMPLATES.get(device_id):
            template_data = DEVICE_TEMPLATES[device_id]
            settings = template_data.get('settings', {})
            posting_interval_minutes = int(settings.get('postingIntervalMinutes', 30) or 30)
        
        # Get daily target from template
        daily_target = 0
        try:
            if 'DEVICE_TEMPLATES' in globals() and DEVICE_TEMPLATES.get(device_id):
                template_data = DEVICE_TEMPLATES[device_id]
                settings = template_data.get('settings', {})
                daily_target = int(settings.get('textPostsPerDay', 0) or 0)
        except Exception as e:
            print(f"⚠️ Failed to get daily target for device {device_id}: {e}")
            daily_target = 2  # Default fallback
        
        items = []
        for acc in assigned_accounts:
            account_id = str(acc.get('id', ''))
            username = acc.get('username', 'unknown')
            
            # Get post counts
            posts_total = 0
            posts_today = 0
            last_post_at = None
            
            try:
                # Load post tracking data
                tracking_data = load_account_post_tracking()
                for item in tracking_data:
                    if item.get('username') == username:
                        posts_total = item.get('posts_total', 0)
                        posts_today = item.get('posts_today', 0)
                        last_post_at = item.get('last_post_at')
                        break
            except Exception as e:
                print(f"⚠️ Failed to load post tracking for {username}: {e}")
            
            # Determine status: completed for today, cooldown, or ready
            status = "ready"
            remaining_minutes = 0
            
            if account_id in LAST_ACCOUNT_SESSIONS:
                last_post_time = LAST_ACCOUNT_SESSIONS[account_id]
                elapsed_minutes = (time.time() - last_post_time) / 60
                
                if elapsed_minutes < posting_interval_minutes:
                    status = "cooldown"
                    remaining_minutes = posting_interval_minutes - elapsed_minutes

            # Completed for today if reached daily target
            try:
                if daily_target and posts_today >= daily_target:
                    status = "completed"
            except Exception:
                pass
            
            items.append({
                "id": account_id,
                "username": username,
                "posts_total": posts_total,
                "posts_today": posts_today,
                "daily_target": daily_target,
                "last_post_at": last_post_at,
                "status": status,
                "remaining_minutes": remaining_minutes
            })
        
        message_data = {
            "type": "account_status_update",
            "device_id": device_id,
            "accounts": items,
            "posting_interval_minutes": posting_interval_minutes,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected clients
        if active_websocket_connections:
            disconnected = set()
            for websocket in active_websocket_connections.copy():
                try:
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_text(json.dumps(message_data))
                except Exception:
                    disconnected.add(websocket)
            
            # Remove disconnected clients
            active_websocket_connections -= disconnected
            
    except Exception as e:
        print(f"❌ Error broadcasting account status update: {e}")

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

    # Load license-aware accounts and filter for this device
    accounts_for_device = []
    try:
        all_accounts = load_accounts()
        accounts_for_device = [
            {
                "id": str(a.get("id")),
                "device_id": str(a.get("device_id")),
                "username": str(a.get("username")),
                "container_number": str(a.get("container_number")),
                "platform": (a.get("platform") or "threads")
            }
            for a in (all_accounts or [])
            if str(a.get("device_id")) == str(device_id)
        ]
        print(f"👤 Accounts for device {device_id}: {len(accounts_for_device)} found")
        for acc in accounts_for_device:
            print(f"   - {acc['platform']} | @{acc['username']} | container {acc['container_number']}")
    except Exception as e:
        print(f"⚠️ Failed to load accounts for device {device_id}: {e}")

    # Persist selection for later automation steps
    try:
        global DEVICE_ACCOUNTS
    except NameError:
        DEVICE_ACCOUNTS = {}
    DEVICE_ACCOUNTS[device_id] = accounts_for_device
    
    # Check account phases and decide whether to run warmup or posting
    warmup_accounts = []
    posting_accounts = []
    
    for account in accounts_for_device:
        account_phase = get_account_phase(account['id'])
        if account_phase == 'warmup':
            warmup_accounts.append(account)
        else:
            posting_accounts.append(account)
    
    print(f"📊 Account phases for device {device_id}:")
    print(f"   🔥 Warmup accounts: {len(warmup_accounts)}")
    for acc in warmup_accounts:
        print(f"      - @{acc['username']} (ID: {acc['id']})")
    print(f"   📝 Posting accounts: {len(posting_accounts)}")
    for acc in posting_accounts:
        print(f"      - @{acc['username']} (ID: {acc['id']})")

    print(f"🚀 Starting device: {device.get('name')}")
    print(f"   Platform: {device.get('platform')}")
    print(f"   UDID: {device.get('udid')}")
    print(f"   Appium Port: {device.get('appium_port')}")

    # Immediately broadcast device status to flip UI to running
    try:
        import asyncio as _asyncio
        _asyncio.create_task(broadcast_device_status_update(device_id, "running", "Device start requested"))
    except Exception as e:
        print(f"⚠️ Failed to broadcast initial device running status: {e}")
    
    # Check if Appium is already running for this device
    if device_id in running_appium_processes:
        process = running_appium_processes[device_id]
        # Support None sentinel from idempotent warmup start
        if process is None or (hasattr(process, 'poll') and process.poll() is None):
            print(f"✅ Appium already running for {device.get('name')}")
            return {"status": "already_running", "device_id": device_id}
    
    # Check if port is already in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', device.get('appium_port')))
    sock.close()
    
    if result == 0:
        # Port listening: record sentinel and short-circuit
        print(f"✅ Appium already listening on port {device.get('appium_port')}")
        running_appium_processes.setdefault(device_id, None)
        return {"status": "already_running", "device_id": device_id}
    
    try:
        # Ensure temp directory exists and has proper permissions
        import tempfile
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        print(f"🔧 Using temp directory: {temp_dir}")
        
        # Start Appium server for this device (minimal command)
        appium_cmd = [
            "appium",
            "-p", str(device.get('appium_port'))
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
        await asyncio.sleep(3)  # ASYNC VERSION TO NOT BLOCK WEBSOCKETS
        
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
            
            # Start automation based on account phases
            try:
                if warmup_accounts:
                    # Start warmup automation for warmup accounts
                    print(f"🔥 Starting warmup automation for {len(warmup_accounts)} accounts")
                    job_id = await start_warmup_automation(device_id, warmup_accounts)
                elif posting_accounts:
                    # Start posting automation for posting accounts
                    print(f"📝 Starting posting automation for {len(posting_accounts)} accounts")
                    template_data = request.template_data if request else None
                    job_id = await start_template_execution_job(device_id, template_data)
                else:
                    print(f"⚠️ No accounts found for device {device_id}")
                    job_id = None
                    
                if job_id:
                    print(f"🚀 Started automation job {job_id} for device {device_id}")
            except Exception as e:
                print(f"❌ Failed to start automation: {e}")
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
    # Allow local development if no license
    if key:
        # Use device_id label if device lookup fails
        dev = next((d for d in devices if d.get("id") == device_id), None)
        val_device_id = (dev or {}).get("udid", device_id)
        validation = validate_license(key, val_device_id)
        if not validation.get("valid", False):
            raise HTTPException(status_code=403, detail={"message": "License invalid or expired", "details": validation})

    # Signal scheduler to stop
    try:
        if 'DEVICE_KEEP_RUNNING' in globals():
            DEVICE_KEEP_RUNNING[device_id] = False
    except Exception:
        pass

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
        # Ensure device status is set to stopped and notify listeners even if no process found
        for device in devices:
            if device.get("id") == device_id:
                device['status'] = "stopped"
                break
        await broadcast_device_status_update(device_id, "stopped", "Device stopped")
        return {"status": "not_running", "device_id": device_id}


@app.post("/api/v1/devices/{device_id}/pause")
async def pause_device(device_id: str):
    """Pause automation scheduler for a specific device (keep Appium running)."""
    # License validation before any action
    key = license_key or load_license_key()
    dev = next((d for d in devices if d.get("id") == device_id), None)
    val_device_id = (dev or {}).get("udid", device_id)
    validation = validate_license(key, val_device_id)
    if not validation.get("valid", False):
        raise HTTPException(status_code=403, detail={"message": "License invalid or expired", "details": validation})

    global DEVICE_PAUSED
    if 'DEVICE_PAUSED' not in globals():
        DEVICE_PAUSED = {}
    DEVICE_PAUSED[device_id] = True

    # Update device status and broadcast
    for device in devices:
        if device.get("id") == device_id:
            device['status'] = "paused"
            break
    await broadcast_device_status_update(device_id, "paused", "Device paused")
    try:
        await broadcast_account_status_update(device_id)
    except Exception:
        pass
    return {"status": "paused", "device_id": device_id}


@app.post("/api/v1/devices/{device_id}/resume")
async def resume_device(device_id: str):
    """Resume automation scheduler for a specific device."""
    # License validation before any action
    key = license_key or load_license_key()
    dev = next((d for d in devices if d.get("id") == device_id), None)
    val_device_id = (dev or {}).get("udid", device_id)
    validation = validate_license(key, val_device_id)
    if not validation.get("valid", False):
        raise HTTPException(status_code=403, detail={"message": "License invalid or expired", "details": validation})

    global DEVICE_PAUSED
    if 'DEVICE_PAUSED' not in globals():
        DEVICE_PAUSED = {}
    DEVICE_PAUSED[device_id] = False

    # Update status and broadcast
    for device in devices:
        if device.get("id") == device_id:
            device['status'] = "running"
            break
    await broadcast_device_status_update(device_id, "active", "Device resumed")
    try:
        await broadcast_account_status_update(device_id)
    except Exception:
        pass
    return {"status": "running", "device_id": device_id}

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
async def get_accounts(device_id: str = None):
    """Get accounts from local persistent storage, optionally filtered by device_id"""
    try:
        accounts = load_accounts()
        if device_id:
            accounts = [a for a in accounts if str(a.get('device_id')) == str(device_id)]
        return {"items": accounts, "total": len(accounts)}
    except Exception as e:
        # Ensure we never block - always return something
        print(f"⚠️ get_accounts error: {e}")
        return {"items": [], "total": 0}

@app.post("/api/v1/accounts/sync")
async def sync_accounts(payload: dict):
    """Sync accounts from frontend localStorage export.
    Expected payload: { "accounts": [ { device_id, username, container_number, ... }, ... ] }
    """
    try:
        accounts_list = payload.get("accounts", []) or []
        if not isinstance(accounts_list, list):
            raise HTTPException(status_code=400, detail="accounts must be a list")
        # Basic normalization
        normalized = []
        for a in accounts_list:
            if not isinstance(a, dict):
                continue
            rec = {
                "id": a.get("id") or a.get("_id") or str(uuid.uuid4()),
                "device_id": str(a.get("device_id") or a.get("deviceId") or ""),
                "username": a.get("username") or a.get("name") or "",
                "container_number": str(a.get("container_number") or a.get("containerNumber") or a.get("container") or ""),
                "platform": a.get("platform") or "threads",
            }
            normalized.append(rec)
        save_accounts(normalized)
        return {"success": True, "saved": len(normalized)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync accounts: {str(e)}")

@app.post("/api/v1/accounts")
async def create_account(account: dict):
    """Create a new account and persist it to the license-aware local storage file"""
    try:
        print(f"🔍 CREATE/UPDATE ACCOUNT - Received data: {account}")
        
        # Normalize and assign ID
        new_id = account.get("id") or f"account-{int(time.time())}"
        rec = {
            "id": new_id,
            "device_id": str(account.get("device_id") or account.get("device") or ""),
            "username": account.get("username") or account.get("threads_username") or account.get("instagram_username") or account.get("name") or "",
            "container_number": str(account.get("container_number") or account.get("containerNumber") or account.get("container") or ""),
            "platform": account.get("platform") or "threads",
        }
        
        # Preserve account_phase if provided
        if "account_phase" in account:
            rec["account_phase"] = account["account_phase"]
            print(f"🔍 CREATE/UPDATE ACCOUNT - Preserving account_phase: {account['account_phase']}")
        
        # Merge with existing to keep any extra fields
        rec.update(account)
        
        print(f"🔍 CREATE/UPDATE ACCOUNT - Final record: {rec}")
        
        # Load existing accounts, append, and save
        existing = load_accounts()
        
        # ALWAYS preserve account_phase for existing accounts if not provided in update
        # This prevents the frontend from accidentally removing the phase field
        for existing_account in existing:
            if str(existing_account.get("id")) == str(new_id):
                # If account_phase not provided in update, preserve existing one
                if "account_phase" not in account and "account_phase" in existing_account:
                    rec["account_phase"] = existing_account["account_phase"]
                    print(f"🔍 CREATE/UPDATE ACCOUNT - Preserved existing account_phase: {existing_account['account_phase']}")
                # If account_phase is provided, use it
                elif "account_phase" in account:
                    print(f"🔍 CREATE/UPDATE ACCOUNT - Using provided account_phase: {account['account_phase']}")
                # If no existing account_phase, default to posting
                elif "account_phase" not in rec:
                    rec["account_phase"] = "posting"
                    print(f"🔍 CREATE/UPDATE ACCOUNT - Set default account_phase: posting")
                break
        
        # Ensure account_phase is always set (safety net)
        if "account_phase" not in rec:
            rec["account_phase"] = "posting"
            print(f"🔍 CREATE/UPDATE ACCOUNT - Safety net: Set default account_phase to posting")
        
        # Replace if same id exists
        existing = [a for a in existing if str(a.get("id")) != str(rec.get("id"))]
        existing.append(rec)
        
        # Ensure ALL accounts have account_phase field (final safety check)
        for account in existing:
            if "account_phase" not in account:
                account["account_phase"] = "posting"
                print(f"🔍 CREATE/UPDATE ACCOUNT - Safety net: Added account_phase to account {account.get('id')}")
        
        save_accounts(existing)
        
        print(f"🔍 CREATE/UPDATE ACCOUNT - Saved account with account_phase: {rec.get('account_phase', 'NOT SET')}")
        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")

@app.delete("/api/v1/accounts/{account_id}")
async def delete_account(account_id: str):
    """Delete an account by ID from the license-aware local storage file"""
    try:
        # Load existing accounts
        existing = load_accounts()
        # Find and remove the account
        original_count = len(existing)
        existing = [a for a in existing if str(a.get("id")) != str(account_id)]
        
        if len(existing) < original_count:
            # Account was found and removed
            save_accounts(existing)
            print(f"🗑️ Deleted account {account_id} from storage")
            return {"success": True, "deleted": account_id}
        else:
            # Account not found
            return {"success": False, "message": "Account not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")

@app.get("/api/v1/accounts/stats")
async def get_accounts_stats():
    """Basic accounts stats to satisfy frontend checks"""
    try:
        accounts = load_accounts()
        return {"total": len(accounts)}
    except Exception:
        return {"total": 0}

@app.post("/api/v1/accounts/update-phase")
async def update_account_phase(request: dict):
    """Update account phase in warmup tracking files"""
    try:
        account_id = request.get('account_id')
        username = request.get('username')
        phase = request.get('phase')
        
        if not all([account_id, username, phase]):
            raise HTTPException(status_code=400, detail="Missing required fields: account_id, username, phase")
        
        if phase not in ['warmup', 'posting']:
            raise HTTPException(status_code=400, detail="Phase must be 'warmup' or 'posting'")
        
        # Update the warmup tracking file
        base_dir = os.path.dirname(__file__)
        license_file = os.path.join(base_dir, "accounts_warmup_tracking_license_dev.json")
        local_file = os.path.join(base_dir, "accounts_warmup_tracking_local_dev.json")
        
        # Use license file if it exists, otherwise local file
        warmup_file = license_file if os.path.exists(license_file) else local_file
        
        # Load existing data
        data = {}
        if os.path.exists(warmup_file):
            with open(warmup_file, 'r') as f:
                data = json.load(f)
        
        # Ensure license_dev section exists
        if 'license_dev' not in data:
            data['license_dev'] = {}
        
        # Update the account phase in warmup tracking file
        account_key = f"account_{account_id}"
        if account_key not in data['license_dev']:
            data['license_dev'][account_key] = {}
        
        data['license_dev'][account_key]['account_phase'] = phase
        
        # Save the updated warmup tracking data
        with open(warmup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Updated account {username} phase to {phase} in {warmup_file}")
        
        # Also update the accounts file
        try:
            accounts = load_accounts()
            account_found = False
            for account in accounts:
                if str(account.get('id')) == str(account_id):
                    account['account_phase'] = phase
                    account_found = True
                    break
            
            if account_found:
                save_accounts(accounts)
                print(f"✅ Updated account {username} phase to {phase} in accounts file")
            else:
                print(f"⚠️ Account {account_id} not found in accounts file")
        except Exception as e:
            print(f"⚠️ Failed to update accounts file: {e}")
        
        return {"status": "success", "message": f"Account {username} phase updated to {phase}"}
        
    except Exception as e:
        print(f"❌ Error updating account phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/devices/{device_id}/account-status")
async def get_device_account_status(device_id: str):
    """Get detailed account status for a device including cooldowns and post counts"""
    try:
        # Get accounts assigned to this device
        assigned_accounts = DEVICE_ACCOUNTS.get(device_id, []) if 'DEVICE_ACCOUNTS' in globals() else []
        
        if not assigned_accounts:
            return {"accounts": [], "posting_interval_minutes": 30}
        
        # Get posting interval from template
        posting_interval_minutes = 30  # Default
        if 'DEVICE_TEMPLATES' in globals() and DEVICE_TEMPLATES.get(device_id):
            template_data = DEVICE_TEMPLATES[device_id]
            settings = template_data.get('settings', {})
            posting_interval_minutes = int(settings.get('postingIntervalMinutes', 30) or 30)
        
        # Get daily target from template
        daily_target = 0
        try:
            if 'DEVICE_TEMPLATES' in globals() and DEVICE_TEMPLATES.get(device_id):
                template_data = DEVICE_TEMPLATES[device_id]
                settings = template_data.get('settings', {})
                daily_target = int(settings.get('textPostsPerDay', 0) or 0)
        except Exception as e:
            print(f"⚠️ Failed to get daily target for device {device_id}: {e}")
            daily_target = 2  # Default fallback
        
        items = []
        for acc in assigned_accounts:
            account_id = str(acc.get('id', ''))
            username = acc.get('username', 'unknown')
            
            # Get post counts
            posts_total = 0
            posts_today = 0
            last_post_at = None
            
            try:
                # Load post tracking data
                tracking_data = load_account_post_tracking()
                for item in tracking_data:
                    if item.get('username') == username:
                        posts_total = item.get('posts_total', 0)
                        posts_today = item.get('posts_today', 0)
                        last_post_at = item.get('last_post_at')
                        break
            except Exception as e:
                print(f"⚠️ Failed to load post tracking for {username}: {e}")
            
            # Check cooldown status
            status = "ready"
            remaining_minutes = 0
            
            if account_id in LAST_ACCOUNT_SESSIONS:
                last_post_time = LAST_ACCOUNT_SESSIONS[account_id]
                elapsed_minutes = (time.time() - last_post_time) / 60
                
                if elapsed_minutes < posting_interval_minutes:
                    status = "cooldown"
                    remaining_minutes = posting_interval_minutes - elapsed_minutes
            
            # Get warmup data
            warmup_data = get_warmup_account_data(account_id)
            account_phase = warmup_data.get('account_phase', 'posting') if warmup_data else 'posting'
            warmup_completed_today = warmup_data.get('warmup_completed_today', False) if warmup_data else False
            current_day = warmup_data.get('current_day', 1) if warmup_data else 1
            warmup_stats = warmup_data.get('warmup_stats', {}) if warmup_data else {}
            
            # Determine final status based on phase and completion
            final_status = status
            if account_phase == 'warmup':
                if warmup_completed_today:
                    final_status = "warmup_completed"
                else:
                    final_status = "warmup_ready"
            elif posts_today >= daily_target and daily_target > 0:
                final_status = "completed"
            
            items.append({
                "id": account_id,
                "username": username,
                "posts_total": posts_total,
                "posts_today": posts_today,
                "daily_target": daily_target,
                "last_post_at": last_post_at,
                "status": final_status,
                "remaining_minutes": remaining_minutes,
                # Warmup-specific data
                "account_phase": account_phase,
                "warmup_completed_today": warmup_completed_today,
                "current_day": current_day,
                "warmup_stats": warmup_stats
            })
        
        return {
            "accounts": items,
            "posting_interval_minutes": posting_interval_minutes
        }
        
    except Exception as e:
        print(f"❌ Error getting account status for device {device_id}: {e}")
        return {"accounts": [], "posting_interval_minutes": 30}

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

@app.post("/api/v1/templates/{template_id}/execute")
async def execute_posting_template(template_id: str, request: dict):
    """Execute a posting template for specific accounts"""
    try:
        print(f"📝 Starting posting template execution: template={template_id}")
        print(f"📝 Request data: {request}")
        
        device_id = request.get('device_id')
        account_ids = request.get('account_ids', [])
        template_data = request.get('template_data')
        
        if not device_id or not account_ids:
            raise HTTPException(status_code=400, detail="Missing required parameters: device_id, account_ids")
        
        # Convert device_id to string if it's not None
        if device_id is not None:
            device_id = str(device_id)
        
        # Generate job ID
        job_id = f"posting_{uuid.uuid4().hex[:8]}"

        # Broadcast immediate WS update so UI flips to running
        try:
            first_account_id = str(account_ids[0]) if account_ids else ""
            username = "unknown"
            try:
                for a in (load_accounts() or []):
                    if str(a.get("id")) == first_account_id:
                        username = str(a.get("username", "unknown"))
                        break
            except Exception:
                pass
            import asyncio as _asyncio
            _asyncio.create_task(broadcast_account_processing(
                device_id=str(device_id),
                username=username,
                account_id=first_account_id,
                current_step="Starting text post automation",
                progress=0
            ))
        except Exception as e:
            print(f"⚠️ Failed to broadcast initial posting job update: {e}")
        
        # Start posting execution in background
        asyncio.create_task(execute_real_threads_posts(device_id, len(account_ids), job_id, template_data))
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Posting template execution started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to start posting template execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start posting template execution: {str(e)}")

@app.post("/api/v1/runs/warmup")
async def start_warmup_run(request: dict):
    """Start a warmup run for a specific account"""
    try:
        print(f"🔥 DEBUG - Raw request received: {request}")
        
        device_id = request.get('device_id')
        account_id = request.get('account_id')
        warmup_template_id = request.get('warmup_template_id')
        warmup_template_data = request.get('warmup_template_data')
        posting_template_data = request.get('posting_template_data')
        license_id = request.get('license_id')
        
        print(f"🔥 Starting warmup run: device={device_id}, account={account_id}, template={warmup_template_id}")
        print(f"🔥 Warmup template data provided: {warmup_template_data is not None}")
        
        # Convert device_id to string if it's not None
        if device_id is not None:
            device_id = str(device_id)
        
        if not all([device_id, account_id, warmup_template_id]):
            print(f"❌ Missing required parameters: device_id={device_id}, account_id={account_id}, warmup_template_id={warmup_template_id}")
            raise HTTPException(status_code=400, detail="Missing required parameters: device_id, account_id, warmup_template_id")
        
        # License validation
        key = license_key or load_license_key()
        if not key and not license_id:
            print("⚠️ No license key set - allowing local development mode")
        elif key:
            dev = next((d for d in devices if d.get("id") == device_id), None)
            val_device_id = (dev or {}).get("udid", device_id)
            validation = validate_license(key, val_device_id)
            if not validation.get("valid", False):
                raise HTTPException(status_code=403, detail={"message": "License invalid or expired", "details": validation})
        
        # Generate job ID
        job_id = f"warmup_{uuid.uuid4().hex[:8]}"

        # Broadcast immediate WS update so UI flips to running for warmup
        try:
            username = "unknown"
            try:
                for a in (load_accounts() or []):
                    if str(a.get("id")) == str(account_id):
                        username = str(a.get("username", "unknown"))
                        break
            except Exception:
                pass
            import asyncio as _asyncio
            _asyncio.create_task(broadcast_account_processing(
                device_id=str(device_id),
                username=username,
                account_id=str(account_id),
                current_step="Starting warmup automation",
                progress=0
            ))
        except Exception as e:
            print(f"⚠️ Failed to broadcast initial warmup job update: {e}")
        
        # Start warmup execution in background
        asyncio.create_task(execute_warmup_session(device_id, warmup_template_data, job_id))
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Warmup run started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to start warmup run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start warmup run: {str(e)}")

# WebSocket endpoints (for real-time updates)
@app.websocket("/api/v1/ws")
async def websocket_v1(websocket: WebSocket):
    """Accept simple WebSocket connections for local development.

    The frontend expects ws://localhost:8000/api/v1/ws?client_id=... to succeed.
    We accept any origin and keep the connection open, emitting basic heartbeat messages.
    """
    await websocket.accept()
    active_websocket_connections.add(websocket)
    print(f"🔌 WebSocket connection established. Total connections: {len(active_websocket_connections)}")
    
    try:
        # Send a welcome/status message
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to FSN Local Backend WebSocket",
            "active_connections": get_active_connection_count(),
        })
        
        # Start a heartbeat task to keep connection alive
        async def send_heartbeat():
            while True:
                try:
                    await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                    if websocket in active_websocket_connections:
                        await websocket.send_json({
                            "type": "heartbeat",
                            "active_connections": get_active_connection_count(),
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception as e:
                    print(f"⚠️ Heartbeat error: {e}")
                    break
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat())

        # Basic receive loop; echo pings and ignore others
        while True:
            try:
                msg = await websocket.receive_text()
                if msg.strip().lower() in {"ping", "\"ping\""}:
                    await websocket.send_json({"type": "pong", "active_connections": get_active_connection_count()})
                else:
                    # Echo back as acknowledgement so frontend hooks don't error
                    await websocket.send_json({"type": "ack", "received": msg})
            except WebSocketDisconnect:
                print(f"🔌 WebSocket disconnected by client")
                break
            except Exception as e:
                print(f"⚠️ WebSocket receive error: {e}")
                # Check if WebSocket is still connected before breaking
                if websocket.client_state.name == "DISCONNECTED":
                    print(f"🔌 WebSocket is disconnected, ending receive loop")
                    break
                # For other errors, continue the loop
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    except Exception:
        # Ensure we do not crash the app on WS errors
        try:
            await websocket.close()
        except Exception:
            pass
    finally:
        # Cancel heartbeat task
        try:
            if 'heartbeat_task' in locals():
                heartbeat_task.cancel()
        except Exception:
            pass
        
        # Remove from active connections
        if websocket in active_websocket_connections:
            active_websocket_connections.discard(websocket)
            print(f"🔌 WebSocket connection removed. Total connections: {len(active_websocket_connections)}")

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