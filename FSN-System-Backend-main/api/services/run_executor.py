"""
Run Execution Service
Executes posting and warmup runs on devices
"""
import asyncio
import uuid
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import random

from database.connection import get_db
from models.template import PostingTemplate, WarmupTemplate, Run, RunLog
from models.device import Device
from models.account import Account
from services.appium_service import appium_service
from services.device_automation import device_automation
from services.integrated_photo_service import integrated_photo_service
from services.device_app_launcher import device_app_launcher

logger = structlog.get_logger()

class RunExecutor:
    """Executes posting and warmup runs on devices"""
    
    def __init__(self):
        self.active_runs = {}  # run_id -> run_info
        self.running = False
    
    async def start(self):
        """Start the run executor"""
        self.running = True
        logger.info("🚀 Starting run executor")
    
    async def stop(self):
        """Stop the run executor"""
        self.running = False
        # Stop all active runs
        for run_id in list(self.active_runs.keys()):
            await self.stop_run(run_id)
        logger.info("🛑 Run executor stopped")
    
    async def start_posting_run(
        self, 
        license_id: str, 
        device_id: int, 
        template_id: int, 
        account_id: Optional[int] = None
    ) -> str:
        """Start a posting run"""
        try:
            # Generate run ID
            run_id = str(uuid.uuid4())
            
            # Create run record
            async for db in get_db():
                run = Run(
                    run_id=run_id,
                    license_id=license_id,
                    device_id=device_id,
                    account_id=account_id,
                    type="posting",
                    template_id=template_id,
                    status="queued"
                )
                db.add(run)
                await db.commit()
                
                # Get template and device
                template_result = await db.execute(
                    select(PostingTemplate).where(PostingTemplate.id == template_id)
                )
                template = template_result.scalar_one_or_none()
                
                device_result = await db.execute(
                    select(Device).where(Device.id == device_id)
                )
                device = device_result.scalar_one_or_none()
                
                # Get account if account_id is provided
                account = None
                if account_id:
                    from migrations.setup_postgresql_tables import Account
                    account_result = await db.execute(
                        select(Account).where(Account.id == account_id)
                    )
                    account = account_result.scalar_one_or_none()
                
                if not template or not device:
                    raise Exception("Template or device not found")
                
                # Start execution
                asyncio.create_task(self._execute_posting_run(run_id, template, device, account_id, account))
                
                logger.info("✅ Started posting run", run_id=run_id, template_id=template_id, device_id=device_id)
                return run_id
                
        except Exception as e:
            logger.error("❌ Failed to start posting run", error=str(e))
            raise
    
    async def start_warmup_run(
        self, 
        license_id: str, 
        device_id: int, 
        warmup_id: int, 
        account_id: Optional[int] = None
    ) -> str:
        """Start a warmup run"""
        try:
            # Generate run ID
            run_id = str(uuid.uuid4())
            
            # Create run record
            async for db in get_db():
                run = Run(
                    run_id=run_id,
                    license_id=license_id,
                    device_id=device_id,
                    account_id=account_id,
                    type="warmup",
                    warmup_id=warmup_id,
                    status="queued"
                )
                db.add(run)
                await db.commit()
                
                # Get template and device
                template_result = await db.execute(
                    select(WarmupTemplate).where(WarmupTemplate.id == warmup_id)
                )
                template = template_result.scalar_one_or_none()
                
                device_result = await db.execute(
                    select(Device).where(Device.id == device_id)
                )
                device = device_result.scalar_one_or_none()
                
                # Get account if account_id is provided
                account = None
                if account_id:
                    from migrations.setup_postgresql_tables import Account
                    account_result = await db.execute(
                        select(Account).where(Account.id == account_id)
                    )
                    account = account_result.scalar_one_or_none()
                
                if not template or not device:
                    raise Exception("Template or device not found")
                
                # Start execution
                asyncio.create_task(self._execute_warmup_run(run_id, template, device, account_id, account))
                
                logger.info("✅ Started warmup run", run_id=run_id, warmup_id=warmup_id, device_id=device_id)
                return run_id
                
        except Exception as e:
            logger.error("❌ Failed to start warmup run", error=str(e))
            raise
    
    async def stop_run(self, run_id: str) -> bool:
        """Stop a running run"""
        try:
            if run_id in self.active_runs:
                # Mark as stopped
                async for db in get_db():
                    await db.execute(
                        update(Run)
                        .where(Run.run_id == run_id)
                        .values(
                            status="stopped",
                            finished_at=datetime.utcnow()
                        )
                    )
                    await db.commit()
                
                # Remove from active runs
                del self.active_runs[run_id]
                
                logger.info("✅ Stopped run", run_id=run_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("❌ Failed to stop run", error=str(e), run_id=run_id)
            return False
    
    async def get_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run status"""
        try:
            async for db in get_db():
                result = await db.execute(
                    select(Run).where(Run.run_id == run_id)
                )
                run = result.scalar_one_or_none()
                
                if run:
                    return {
                        "run_id": run.run_id,
                        "status": run.status,
                        "progress_pct": run.progress_pct,
                        "current_step": run.current_step,
                        "last_action": run.last_action,
                        "error_text": run.error_text,
                        "started_at": run.started_at,
                        "finished_at": run.finished_at
                    }
            
            return None
            
        except Exception as e:
            logger.error("❌ Failed to get run status", error=str(e), run_id=run_id)
            return None
    
    async def _execute_posting_run(
        self, 
        run_id: str, 
        template: PostingTemplate, 
        device: Device, 
        account_id: Optional[int],
        account: Optional[Any] = None
    ):
        """Execute a posting run"""
        try:
            # Update status to running
            await self._update_run_status(run_id, "running", 0, "Starting posting run")
            
            # Create Appium session (will be used by device_app_launcher)
            try:
                driver = await asyncio.wait_for(
                    self._create_appium_session(device), 
                    timeout=120  # 2 minute timeout for session creation
                )
                if not driver:
                    await self._update_run_status(run_id, "error", 0, "Failed to create Appium session")
                    return
            except asyncio.TimeoutError:
                await self._update_run_status(run_id, "error", 0, "Appium session creation timed out")
                return
            
            # Store session in appium service for device_app_launcher to use
            from services.appium_service import appium_service
            appium_service.active_sessions[device.udid] = driver
            
            self.active_runs[run_id] = {
                "driver": driver,
                "template": template,
                "device": device,
                "start_time": datetime.utcnow()
            }
            
            # Execute posting actions
            await self._execute_posting_actions(run_id, template, device, account_id, account)
            
            # Mark as completed
            await self._update_run_status(run_id, "success", 100, "Posting run completed")
            
        except Exception as e:
            logger.error("❌ Posting run failed", error=str(e), run_id=run_id)
            await self._update_run_status(run_id, "error", 0, f"Posting run failed: {str(e)}")
        finally:
            # Cleanup
            if run_id in self.active_runs:
                driver = self.active_runs[run_id].get("driver")
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                del self.active_runs[run_id]
    
    async def _execute_warmup_run(
        self, 
        run_id: str, 
        template: WarmupTemplate, 
        device: Device, 
        account_id: Optional[int],
        account: Optional[Any] = None
    ):
        """Execute a warmup run"""
        try:
            # Update status to running
            await self._update_run_status(run_id, "running", 0, "Starting warmup run")
            
            # Create Appium session
            driver = await self._create_appium_session(device)
            if not driver:
                await self._update_run_status(run_id, "error", 0, "Failed to create Appium session")
                return
            
            self.active_runs[run_id] = {
                "driver": driver,
                "template": template,
                "device": device,
                "start_time": datetime.utcnow()
            }
            
            # Execute warmup actions
            await self._execute_warmup_actions(run_id, template, driver)
            
            # Mark as completed
            await self._update_run_status(run_id, "success", 100, "Warmup run completed")
            
        except Exception as e:
            logger.error("❌ Warmup run failed", error=str(e), run_id=run_id)
            await self._update_run_status(run_id, "error", 0, f"Warmup run failed: {str(e)}")
        finally:
            # Cleanup
            if run_id in self.active_runs:
                driver = self.active_runs[run_id].get("driver")
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                del self.active_runs[run_id]
    
    async def _create_appium_session(self, device: Device):
        """Create Appium session for device"""
        try:
            # Build Appium URL
            appium_url = f"{device.public_url}{device.appium_base_path}"
            
            # Create WebDriver session
            from appium import webdriver as appium_webdriver
            from appium.options.ios import XCUITestOptions
            
            options = XCUITestOptions()
            options.platform_name = "iOS"
            options.device_name = device.name
            options.udid = device.udid
            options.bundle_id = "com.barp.Trident"  # Threads app bundle ID
            options.auto_accept_alerts = True
            options.auto_dismiss_alerts = True
            
            driver = appium_webdriver.Remote(appium_url, options=options)
            
            logger.info("✅ Created Appium session", device_id=device.id, appium_url=appium_url)
            return driver
            
        except Exception as e:
            logger.error("❌ Failed to create Appium session", error=str(e), device_id=device.id)
            return None
    
    async def _execute_posting_actions(self, run_id: str, template: PostingTemplate, device: Device, account_id: Optional[int], account: Optional[Any] = None):
        """Execute posting actions based on template - 1 post per session"""
        try:
            total_actions = (
                template.photos_per_day + 
                template.text_posts_per_day + 
                template.follows_per_day + 
                template.likes_per_day
            )
            
            if total_actions == 0:
                await self._update_run_status(run_id, "success", 100, "No actions to perform")
                return
            
            completed_actions = 0
            
            # Determine device type and platform
            device_type = "jailbroken" if device.jailbroken else "non_jailbroken"
            platform = "threads"  # Assuming threads for now, could be made configurable
            
            # Get container ID for JB devices from account settings
            container_id = None
            if device_type == "jailbroken":
                if account and hasattr(account, 'container_number') and account.container_number:
                    container_id = f"container_{account.container_number}"
                    logger.info(f"🔧 Using container ID from account: {container_id} (container_number: {account.container_number})")
                else:
                    container_id = f"container_{account_id}" if account_id else "default"
                    logger.warning(f"⚠️ No container_number in account, using fallback: {container_id}")
            
            # Execute photos posts - 1 session per post
            for i in range(template.photos_per_day):
                await self._log_run_action(run_id, "info", f"Starting photo post session {i+1}/{template.photos_per_day}")
                
                # Launch app for this session
                launch_result = await device_app_launcher.launch_app_for_session(
                    device.udid, 
                    platform, 
                    device_type, 
                    container_id
                )
                
                if not launch_result['success']:
                    await self._log_run_action(run_id, "error", f"Failed to launch app for photo post {i+1}: {launch_result['message']}")
                    continue
                
                # Execute the photo post
                await self._log_run_action(run_id, "info", f"Creating photo post {i+1}/{template.photos_per_day}")
                await self._post_photo_with_template(device_app_launcher, template, run_id)
                
                # Close app after post
                await device_app_launcher.close_app(device.udid, platform)
                
                completed_actions += 1
                progress = int((completed_actions / total_actions) * 100)
                await self._update_run_status(run_id, "running", progress, f"Completed photo post session {i+1}/{template.photos_per_day}")
                
                # Wait between sessions
                await self._random_delay(30, 60)  # 30-60 seconds between sessions
            
            # Execute text posts - 1 session per post
            for i in range(template.text_posts_per_day):
                await self._log_run_action(run_id, "info", f"Starting text post session {i+1}/{template.text_posts_per_day}")
                
                # Launch app for this session
                launch_result = await device_app_launcher.launch_app_for_session(
                    device.udid, 
                    platform, 
                    device_type, 
                    container_id
                )
                
                if not launch_result['success']:
                    await self._log_run_action(run_id, "error", f"Failed to launch app for text post {i+1}: {launch_result['message']}")
                    continue
                
                # Execute the text post
                await self._log_run_action(run_id, "info", f"Creating text post {i+1}/{template.text_posts_per_day}")
                await self._post_text(device_app_launcher)
                
                # Close app after post
                await device_app_launcher.close_app(device.udid, platform)
                
                completed_actions += 1
                progress = int((completed_actions / total_actions) * 100)
                await self._update_run_status(run_id, "running", progress, f"Completed text post session {i+1}/{template.text_posts_per_day}")
                
                # Wait between sessions
                await self._random_delay(30, 60)  # 30-60 seconds between sessions
            
            # Execute follows
            for i in range(template.follows_per_day):
                await self._log_run_action(run_id, "info", f"Following user {i+1}/{template.follows_per_day}")
                await self._follow_user(driver)
                completed_actions += 1
                progress = int((completed_actions / total_actions) * 100)
                await self._update_run_status(run_id, "running", progress, f"Followed user {i+1}/{template.follows_per_day}")
                await self._random_delay(1, 3)
            
            # Execute likes
            for i in range(template.likes_per_day):
                await self._log_run_action(run_id, "info", f"Liking post {i+1}/{template.likes_per_day}")
                await self._like_post(driver)
                completed_actions += 1
                progress = int((completed_actions / total_actions) * 100)
                await self._update_run_status(run_id, "running", progress, f"Liked post {i+1}/{template.likes_per_day}")
                await self._random_delay(1, 3)
            
            # Execute scrolling
            if template.scrolling_minutes > 0:
                await self._log_run_action(run_id, "info", f"Scrolling for {template.scrolling_minutes} minutes")
                await self._scroll_feed(driver, template.scrolling_minutes)
                await self._update_run_status(run_id, "running", 95, f"Scrolled for {template.scrolling_minutes} minutes")
            
        except Exception as e:
            logger.error("❌ Posting actions failed", error=str(e), run_id=run_id)
            raise
    
    async def _execute_warmup_actions(self, run_id: str, template: WarmupTemplate, driver):
        """Execute warmup actions based on template"""
        try:
            days = template.days_json
            if not days or len(days) == 0:
                await self._update_run_status(run_id, "success", 100, "No warmup days configured")
                return
            
            total_days = len(days)
            
            for day_index, day in enumerate(days):
                await self._log_run_action(run_id, "info", f"Executing warmup day {day_index + 1}/{total_days}")
                
                # Execute day actions
                await self._execute_warmup_day(run_id, day, driver)
                
                progress = int(((day_index + 1) / total_days) * 100)
                await self._update_run_status(run_id, "running", progress, f"Completed warmup day {day_index + 1}/{total_days}")
                
                # Delay between days
                if day_index < total_days - 1:
                    await self._random_delay(60, 120)  # 1-2 minutes between days
            
        except Exception as e:
            logger.error("❌ Warmup actions failed", error=str(e), run_id=run_id)
            raise
    
    async def _execute_warmup_day(self, run_id: str, day: Dict[str, Any], driver):
        """Execute a single warmup day"""
        try:
            # Scroll
            if day.get("scroll", 0) > 0:
                await self._log_run_action(run_id, "info", f"Scrolling for {day['scroll']} minutes")
                await self._scroll_feed(driver, day["scroll"])
            
            # Likes
            for i in range(day.get("likes", 0)):
                await self._log_run_action(run_id, "info", f"Liking post {i+1}/{day['likes']}")
                await self._like_post(driver)
                await self._random_delay(1, 3)
            
            # Follows
            for i in range(day.get("follows", 0)):
                await self._log_run_action(run_id, "info", f"Following user {i+1}/{day['follows']}")
                await self._follow_user(driver)
                await self._random_delay(1, 3)
            
            # Comments
            for i in range(day.get("comments", 0)):
                await self._log_run_action(run_id, "info", f"Commenting on post {i+1}/{day['comments']}")
                await self._comment_post(driver)
                await self._random_delay(2, 5)
            
            # Stories
            for i in range(day.get("stories", 0)):
                await self._log_run_action(run_id, "info", f"Viewing story {i+1}/{day['stories']}")
                await self._view_story(driver)
                await self._random_delay(1, 3)
            
            # Posts
            for i in range(day.get("posts", 0)):
                await self._log_run_action(run_id, "info", f"Creating post {i+1}/{day['posts']}")
                await self._post_text(driver)
                await self._random_delay(2, 5)
            
        except Exception as e:
            logger.error("❌ Warmup day execution failed", error=str(e), run_id=run_id)
            raise
    
    # Action implementations using real automation
    async def _post_photo_with_template(self, driver, template: PostingTemplate, run_id: str):
        """Post a photo using template settings (photos folder + captions file)"""
        try:
            # Get device UDID from driver or session
            device_udid = getattr(driver, 'desired_capabilities', {}).get('udid', 'unknown_device')
            
            await self._log_run_action(run_id, "info", f"🚀 Starting integrated photo posting workflow")
            
            # Use integrated photo service with template settings
            photo_result = await integrated_photo_service.process_photo_post(
                photos_folder=template.photos_folder_url,
                captions_file=template.captions_file_url,
                device_udid=device_udid
            )
            
            if not photo_result['success']:
                await self._log_run_action(run_id, "error", f"❌ Photo processing failed: {photo_result['message']}")
                return
            
            photo_url = photo_result['photo_url']
            caption = photo_result['caption']
            
            await self._log_run_action(run_id, "info", f"📸 Photo processed and served at: {photo_url}")
            await self._log_run_action(run_id, "info", f"📝 Using caption: {caption[:100]}...")
            
            # Now instruct iPhone to download and post the photo
            await self._post_photo_from_url(driver, photo_url, caption, run_id)
            
        except Exception as e:
            await self._log_run_action(run_id, "error", f"❌ Template photo posting failed: {str(e)}")
            logger.error("Template photo posting failed", error=str(e), run_id=run_id)

    async def _post_photo_from_url(self, driver, photo_url: str, caption: str, run_id: str):
        """Post photo by downloading from URL to iPhone"""
        try:
            await self._log_run_action(run_id, "info", f"📱 Instructing iPhone to download photo from: {photo_url}")
            
            # Step 1: Open Safari on iPhone and download photo
            await self._download_photo_to_iphone_photos(driver, photo_url, run_id)
            
            # Step 2: Open Instagram and post the downloaded photo
            await self._post_photo_from_gallery(driver, caption, run_id)
            
        except Exception as e:
            await self._log_run_action(run_id, "error", f"❌ Photo posting from URL failed: {str(e)}")
            logger.error("Photo posting from URL failed", error=str(e))

    async def _download_photo_to_iphone_photos(self, driver, photo_url: str, run_id: str):
        """Download photo from URL to iPhone Photos app using Safari"""
        try:
            await self._log_run_action(run_id, "info", "🌐 Opening Safari to download photo")
            
            # Open Safari
            safari_bundle = "com.apple.mobilesafari"
            driver.activate_app(safari_bundle)
            await asyncio.sleep(2)
            
            # Navigate to photo URL
            driver.get(photo_url)
            await asyncio.sleep(3)
            
            # Long press on image to save it
            try:
                # Find the image element
                image_element = driver.find_element("xpath", "//img")
                
                # Long press to open context menu
                from appium.webdriver.common.touch_action import TouchAction
                action = TouchAction(driver)
                action.long_press(image_element).perform()
                await asyncio.sleep(2)
                
                # Tap "Save to Photos"
                save_button = driver.find_element("accessibility id", "Save to Photos")
                save_button.click()
                await asyncio.sleep(2)
                
                await self._log_run_action(run_id, "info", "✅ Photo saved to iPhone Photos")
                
            except Exception as e:
                await self._log_run_action(run_id, "warning", f"⚠️ Could not save via context menu, trying alternative method")
                # Alternative: Take screenshot or use other method
                pass
                
        except Exception as e:
            await self._log_run_action(run_id, "error", f"❌ Failed to download photo to iPhone: {str(e)}")
            raise

    async def _post_photo_from_gallery(self, driver, caption: str, run_id: str):
        """Post the most recent photo from iPhone gallery"""
        try:
            await self._log_run_action(run_id, "info", "📸 Opening Instagram to post photo")
            
            # Open Instagram
            instagram_bundle = "com.burbn.instagram"
            driver.activate_app(instagram_bundle)
            await asyncio.sleep(3)
            
            # Navigate to camera tab
            camera_tab = driver.find_element("accessibility id", "camera-tab")
            camera_tab.click()
            await asyncio.sleep(3)
            
            # Handle permission popups if they appear
            try:
                continue_button = driver.find_element("accessibility id", "ig-photo-library-priming-continue-button")
                continue_button.click()
                await asyncio.sleep(2)
            except:
                pass
                
            try:
                allow_photos = driver.find_element("accessibility id", "Allow Access to All Photos")
                allow_photos.click()
                await asyncio.sleep(2)
            except:
                pass
            
            # Select the most recent photo (should be the one we just downloaded)
            try:
                first_photo = driver.find_element("name", "gallery-photo-cell-0")
                first_photo.click()
                await asyncio.sleep(2)
            except:
                # Fallback to any photo cell
                photo_cells = driver.find_elements("xpath", "//XCUIElementTypeCell[contains(@name, 'gallery-photo-cell')]")
                if photo_cells:
                    photo_cells[0].click()
                    await asyncio.sleep(2)
            
            # Click next button
            next_button = driver.find_element("accessibility id", "next-button")
            next_button.click()
            await asyncio.sleep(3)
            
            # Add caption
            if caption:
                try:
                    caption_field = driver.find_element("accessibility id", "caption-text-view")
                    caption_field.click()
                    caption_field.send_keys(caption)
                    await asyncio.sleep(1)
                except:
                    # Try alternative caption selector
                    try:
                        caption_field = driver.find_element("xpath", "//XCUIElementTypeTextView")
                        caption_field.click()
                        caption_field.send_keys(caption)
                        await asyncio.sleep(1)
                    except:
                        await self._log_run_action(run_id, "warning", "⚠️ Could not add caption")
            
            # Share/Post the photo
            try:
                share_button = driver.find_element("accessibility id", "share-button")
                share_button.click()
                await asyncio.sleep(3)
                
                await self._log_run_action(run_id, "info", "✅ Photo posted successfully!")
                
            except:
                # Try alternative share button
                try:
                    share_button = driver.find_element("accessibility id", "Share")
                    share_button.click()
                    await asyncio.sleep(3)
                    
                    await self._log_run_action(run_id, "info", "✅ Photo posted successfully!")
                except:
                    await self._log_run_action(run_id, "error", "❌ Could not find share button")
                    raise Exception("Could not find share button")
                    
        except Exception as e:
            await self._log_run_action(run_id, "error", f"❌ Failed to post photo from gallery: {str(e)}")
            raise

    async def _post_photo(self, driver, photo_path: str = None, caption: str = ""):
        """Post a photo (legacy method)"""
        if photo_path:
            await device_automation.post_photo(driver, photo_path, caption)
        else:
            # Use default photo or skip
            await self._random_delay(2, 4)
    
    async def _post_text(self, driver, text: str = None):
        """Post text content"""
        if text:
            await device_automation.post_text(driver, text)
        else:
            # Use default text or skip
            await self._random_delay(1, 3)
    
    async def _follow_user(self, driver, username: str = None):
        """Follow a user"""
        if username:
            await device_automation.follow_user(driver, username)
        else:
            # Find random user to follow or skip
            await self._random_delay(1, 2)
    
    async def _like_post(self, driver):
        """Like a post"""
        await device_automation.like_post(driver)
    
    async def _comment_post(self, driver, comment: str = None):
        """Comment on a post"""
        if comment:
            await device_automation.comment_post(driver, comment)
        else:
            # Use default comment or skip
            await self._random_delay(2, 4)
    
    async def _view_story(self, driver):
        """View a story"""
        await device_automation.view_story(driver)
    
    async def _scroll_feed(self, driver, minutes: int):
        """Scroll the feed for specified minutes"""
        await device_automation.scroll_feed(driver, minutes)
    
    async def _random_delay(self, min_seconds: float, max_seconds: float):
        """Random delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def _update_run_status(self, run_id: str, status: str, progress: int, current_step: str):
        """Update run status in database"""
        try:
            async for db in get_db():
                await db.execute(
                    update(Run)
                    .where(Run.run_id == run_id)
                    .values(
                        status=status,
                        progress_pct=progress,
                        current_step=current_step,
                        last_action=current_step,
                        finished_at=datetime.utcnow() if status in ["success", "error", "stopped"] else None
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error("❌ Failed to update run status", error=str(e), run_id=run_id)
    
    async def _log_run_action(self, run_id: str, level: str, message: str, payload: Dict[str, Any] = None):
        """Log run action"""
        try:
            async for db in get_db():
                log = RunLog(
                    run_id=run_id,
                    level=level,
                    message=message,
                    payload_json=payload
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            logger.error("❌ Failed to log run action", error=str(e), run_id=run_id)

# Create global instance
run_executor = RunExecutor()
