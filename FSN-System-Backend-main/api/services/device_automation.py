"""
Device Automation Service
Real Instagram and Threads automation actions
"""
import asyncio
import random
import structlog
from typing import Dict, Any, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

logger = structlog.get_logger()

class DeviceAutomation:
    """Real device automation for Instagram and Threads"""
    
    def __init__(self):
        self.timeout = 10
        self.short_timeout = 5
    
    async def post_photo(self, driver, photo_path: str, caption: str = "") -> bool:
        """Post a photo to Instagram/Threads"""
        try:
            logger.info("📸 Starting photo post", photo_path=photo_path)
            
            # Open composer
            await self._open_composer(driver)
            
            # Select photo
            await self._select_photo(driver, photo_path)
            
            # Add caption
            if caption:
                await self._add_caption(driver, caption)
            
            # Post
            await self._publish_post(driver)
            
            logger.info("✅ Photo posted successfully")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to post photo", error=str(e))
            return False
    
    async def post_text(self, driver, text: str) -> bool:
        """Post text content to Threads"""
        try:
            logger.info("📝 Starting text post", text_length=len(text))
            
            # Open composer
            await self._open_composer(driver)
            
            # Type text
            await self._type_text(driver, text)
            
            # Post
            await self._publish_post(driver)
            
            logger.info("✅ Text post published successfully")
            return True
            
        except Exception as e:
            logger.error("❌ Failed to post text", error=str(e))
            return False
    
    async def follow_user(self, driver, username: str) -> bool:
        """Follow a user"""
        try:
            logger.info("👥 Following user", username=username)
            
            # Search for user
            await self._search_user(driver, username)
            
            # Click follow button
            await self._click_follow_button(driver)
            
            logger.info("✅ User followed successfully", username=username)
            return True
            
        except Exception as e:
            logger.error("❌ Failed to follow user", error=str(e), username=username)
            return False
    
    async def like_post(self, driver) -> bool:
        """Like a post in the feed"""
        try:
            logger.info("❤️ Liking post")
            
            # Find like button
            like_button = await self._find_like_button(driver)
            
            if like_button:
                like_button.click()
                await self._random_delay(1, 2)
                logger.info("✅ Post liked successfully")
                return True
            else:
                logger.warn("⚠️ Like button not found")
                return False
                
        except Exception as e:
            logger.error("❌ Failed to like post", error=str(e))
            return False
    
    async def comment_post(self, driver, comment: str) -> bool:
        """Comment on a post"""
        try:
            logger.info("💬 Commenting on post", comment=comment)
            
            # Find comment button
            comment_button = await self._find_comment_button(driver)
            
            if comment_button:
                comment_button.click()
                await self._random_delay(1, 2)
                
                # Type comment
                await self._type_comment(driver, comment)
                
                # Submit comment
                await self._submit_comment(driver)
                
                logger.info("✅ Comment posted successfully")
                return True
            else:
                logger.warn("⚠️ Comment button not found")
                return False
                
        except Exception as e:
            logger.error("❌ Failed to comment on post", error=str(e))
            return False
    
    async def view_story(self, driver) -> bool:
        """View a story"""
        try:
            logger.info("📖 Viewing story")
            
            # Find story
            story = await self._find_story(driver)
            
            if story:
                story.click()
                await self._random_delay(3, 5)  # View story for a few seconds
                
                # Close story
                await self._close_story(driver)
                
                logger.info("✅ Story viewed successfully")
                return True
            else:
                logger.warn("⚠️ No story found")
                return False
                
        except Exception as e:
            logger.error("❌ Failed to view story", error=str(e))
            return False
    
    async def scroll_feed(self, driver, minutes: int) -> bool:
        """Scroll the feed for specified minutes"""
        try:
            logger.info("📜 Scrolling feed", minutes=minutes)
            
            end_time = time.time() + (minutes * 60)
            scroll_count = 0
            
            while time.time() < end_time:
                # Scroll down
                driver.execute_script("window.scrollBy(0, 500);")
                await self._random_delay(2, 4)
                
                scroll_count += 1
                
                # Random pause
                if scroll_count % 5 == 0:
                    await self._random_delay(5, 10)
            
            logger.info("✅ Feed scrolling completed", scroll_count=scroll_count)
            return True
            
        except Exception as e:
            logger.error("❌ Failed to scroll feed", error=str(e))
            return False
    
    # Helper methods for Instagram
    async def _open_instagram_composer(self, driver):
        """Open Instagram composer"""
        try:
            # Look for plus button or create button
            selectors = [
                "//button[contains(@aria-label, 'New post')]",
                "//button[contains(@aria-label, 'Create')]",
                "//button[contains(@aria-label, 'Add')]",
                "//div[contains(@class, 'create')]//button",
                "//button[contains(@class, 'create')]"
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    await self._random_delay(1, 2)
                    return
                except TimeoutException:
                    continue
            
            raise Exception("Could not find Instagram composer button")
            
        except Exception as e:
            logger.error("❌ Failed to open Instagram composer", error=str(e))
            raise
    
    # Helper methods for Threads
    async def _open_threads_composer(self, driver):
        """Open Threads composer"""
        try:
            # Look for compose button
            selectors = [
                "//button[contains(@aria-label, 'Compose')]",
                "//button[contains(@aria-label, 'New thread')]",
                "//div[contains(@class, 'compose')]//button",
                "//button[contains(@class, 'compose')]",
                "//button[contains(text(), 'Compose')]"
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    await self._random_delay(1, 2)
                    return
                except TimeoutException:
                    continue
            
            raise Exception("Could not find Threads composer button")
            
        except Exception as e:
            logger.error("❌ Failed to open Threads composer", error=str(e))
            raise
    
    async def _open_composer(self, driver):
        """Open composer (detect platform)"""
        try:
            # Try to detect platform by URL or elements
            current_url = driver.current_url.lower()
            
            if "instagram" in current_url:
                await self._open_instagram_composer(driver)
            elif "threads" in current_url or "barp" in current_url:
                await self._open_threads_composer(driver)
            else:
                # Try both
                try:
                    await self._open_instagram_composer(driver)
                except:
                    await self._open_threads_composer(driver)
                    
        except Exception as e:
            logger.error("❌ Failed to open composer", error=str(e))
            raise
    
    async def _select_photo(self, driver, photo_path: str):
        """Select photo for upload"""
        try:
            # Look for file input or photo selection
            selectors = [
                "//input[@type='file']",
                "//input[contains(@accept, 'image')]",
                "//button[contains(@aria-label, 'Select')]",
                "//button[contains(@aria-label, 'Choose')]"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, self.short_timeout).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    
                    if element.tag_name == "input":
                        element.send_keys(photo_path)
                    else:
                        element.click()
                        # Handle file picker if needed
                        await self._handle_file_picker(driver, photo_path)
                    
                    await self._random_delay(2, 4)
                    return
                except TimeoutException:
                    continue
            
            raise Exception("Could not find photo selection element")
            
        except Exception as e:
            logger.error("❌ Failed to select photo", error=str(e))
            raise
    
    async def _add_caption(self, driver, caption: str):
        """Add caption to post"""
        try:
            # Look for caption/description input
            selectors = [
                "//textarea[contains(@placeholder, 'Write a caption')]",
                "//textarea[contains(@placeholder, 'Write a description')]",
                "//textarea[contains(@placeholder, 'What')]",
                "//div[contains(@contenteditable, 'true')]",
                "//textarea"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    element.click()
                    await self._random_delay(0.5, 1)
                    
                    element.clear()
                    element.send_keys(caption)
                    
                    await self._random_delay(1, 2)
                    return
                except TimeoutException:
                    continue
            
            logger.warn("⚠️ Could not find caption input")
            
        except Exception as e:
            logger.error("❌ Failed to add caption", error=str(e))
            raise
    
    async def _type_text(self, driver, text: str):
        """Type text in composer"""
        try:
            # Look for text input
            selectors = [
                "//textarea[contains(@placeholder, 'Start a thread')]",
                "//textarea[contains(@placeholder, 'What')]",
                "//div[contains(@contenteditable, 'true')]",
                "//textarea"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    element.click()
                    await self._random_delay(0.5, 1)
                    
                    element.clear()
                    element.send_keys(text)
                    
                    await self._random_delay(1, 2)
                    return
                except TimeoutException:
                    continue
            
            raise Exception("Could not find text input")
            
        except Exception as e:
            logger.error("❌ Failed to type text", error=str(e))
            raise
    
    async def _publish_post(self, driver):
        """Publish the post"""
        try:
            # Look for publish/share button
            selectors = [
                "//button[contains(@aria-label, 'Share')]",
                "//button[contains(@aria-label, 'Post')]",
                "//button[contains(text(), 'Share')]",
                "//button[contains(text(), 'Post')]",
                "//button[contains(@class, 'share')]",
                "//button[contains(@class, 'post')]"
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    await self._random_delay(3, 5)  # Wait for upload
                    return
                except TimeoutException:
                    continue
            
            raise Exception("Could not find publish button")
            
        except Exception as e:
            logger.error("❌ Failed to publish post", error=str(e))
            raise
    
    async def _search_user(self, driver, username: str):
        """Search for a user"""
        try:
            # Look for search input
            selectors = [
                "//input[contains(@placeholder, 'Search')]",
                "//input[contains(@aria-label, 'Search')]",
                "//input[@type='search']"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    element.click()
                    element.clear()
                    element.send_keys(username)
                    element.send_keys(Keys.RETURN)
                    
                    await self._random_delay(2, 4)
                    return
                except TimeoutException:
                    continue
            
            raise Exception("Could not find search input")
            
        except Exception as e:
            logger.error("❌ Failed to search user", error=str(e))
            raise
    
    async def _click_follow_button(self, driver):
        """Click follow button"""
        try:
            # Look for follow button
            selectors = [
                "//button[contains(text(), 'Follow')]",
                "//button[contains(@aria-label, 'Follow')]",
                "//button[contains(@class, 'follow')]"
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    await self._random_delay(1, 2)
                    return
                except TimeoutException:
                    continue
            
            raise Exception("Could not find follow button")
            
        except Exception as e:
            logger.error("❌ Failed to click follow button", error=str(e))
            raise
    
    async def _find_like_button(self, driver):
        """Find like button in feed"""
        try:
            selectors = [
                "//button[contains(@aria-label, 'Like')]",
                "//button[contains(@class, 'like')]",
                "//button[contains(@class, 'heart')]"
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    return button
                except TimeoutException:
                    continue
            
            return None
            
        except Exception as e:
            logger.error("❌ Failed to find like button", error=str(e))
            return None
    
    async def _find_comment_button(self, driver):
        """Find comment button in feed"""
        try:
            selectors = [
                "//button[contains(@aria-label, 'Comment')]",
                "//button[contains(@class, 'comment')]",
                "//button[contains(@class, 'reply')]"
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    return button
                except TimeoutException:
                    continue
            
            return None
            
        except Exception as e:
            logger.error("❌ Failed to find comment button", error=str(e))
            return None
    
    async def _type_comment(self, driver, comment: str):
        """Type comment text"""
        try:
            # Look for comment input
            selectors = [
                "//textarea[contains(@placeholder, 'Add a comment')]",
                "//textarea[contains(@placeholder, 'Write a comment')]",
                "//div[contains(@contenteditable, 'true')]",
                "//textarea"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    element.click()
                    element.clear()
                    element.send_keys(comment)
                    
                    await self._random_delay(1, 2)
                    return
                except TimeoutException:
                    continue
            
            raise Exception("Could not find comment input")
            
        except Exception as e:
            logger.error("❌ Failed to type comment", error=str(e))
            raise
    
    async def _submit_comment(self, driver):
        """Submit comment"""
        try:
            # Look for submit button
            selectors = [
                "//button[contains(text(), 'Post')]",
                "//button[contains(@aria-label, 'Post')]",
                "//button[contains(@class, 'submit')]"
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    await self._random_delay(1, 2)
                    return
                except TimeoutException:
                    continue
            
            # Try Enter key
            element = driver.switch_to.active_element
            element.send_keys(Keys.RETURN)
            await self._random_delay(1, 2)
            
        except Exception as e:
            logger.error("❌ Failed to submit comment", error=str(e))
            raise
    
    async def _find_story(self, driver):
        """Find a story to view"""
        try:
            selectors = [
                "//div[contains(@class, 'story')]",
                "//button[contains(@aria-label, 'Story')]",
                "//div[contains(@class, 'circle')]"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, self.short_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    return element
                except TimeoutException:
                    continue
            
            return None
            
        except Exception as e:
            logger.error("❌ Failed to find story", error=str(e))
            return None
    
    async def _close_story(self, driver):
        """Close story view"""
        try:
            # Try various close methods
            try:
                # Try clicking outside story
                ActionChains(driver).move_by_offset(100, 100).click().perform()
                await self._random_delay(1, 2)
                return
            except:
                pass
            
            try:
                # Try escape key
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                await self._random_delay(1, 2)
                return
            except:
                pass
            
            try:
                # Try back button
                driver.back()
                await self._random_delay(1, 2)
                return
            except:
                pass
                
        except Exception as e:
            logger.error("❌ Failed to close story", error=str(e))
    
    async def _handle_file_picker(self, driver, file_path: str):
        """Handle file picker dialog"""
        try:
            # This would need platform-specific implementation
            # For now, just wait
            await self._random_delay(2, 4)
            
        except Exception as e:
            logger.error("❌ Failed to handle file picker", error=str(e))
    
    async def _random_delay(self, min_seconds: float, max_seconds: float):
        """Random delay between actions"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

# Create global instance
device_automation = DeviceAutomation()
