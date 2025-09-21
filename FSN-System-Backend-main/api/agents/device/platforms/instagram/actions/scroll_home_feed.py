"""
Instagram SCROLL_HOME_FEED Action - Human-like scrolling with engagement simulation
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional, List

from ....fsm import ActionState, ActionContext
from ....actions.base_action import BaseAction, BaseActionStateHandler
from ..selectors.registry import InstagramSelectorRegistry

logger = logging.getLogger(__name__)


class NavigateToFeedStateHandler(BaseActionStateHandler):
    """Navigate to Instagram home feed"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Navigating to home feed")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Find and tap home tab
            home_tab_result = await selector_registry.find_home_tab(timeout=5)
            if not home_tab_result:
                raise RuntimeError("Home tab not found")
            
            context.add_log("Found home tab, tapping...")
            await context.driver.click_element(home_tab_result.element)
            
            # Wait for feed to load
            await asyncio.sleep(2)
            
            # Verify we're on home feed by looking for main-feed container
            feed_result = await selector_registry.find_home_feed_container(timeout=5)
            if not feed_result:
                raise RuntimeError("Could not verify home feed loaded")
            
            context.add_log("Successfully navigated to home feed")
            return ActionState.SCROLL
            
        except Exception as e:
            context.add_log(f"Navigation failed: {e}")
            raise


class ScrollFeedStateHandler(BaseActionStateHandler):
    """Perform human-like scrolling through home feed"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        scroll_duration = context.payload.parameters.get('scroll_duration', 60)  # seconds
        engagement_rate = context.payload.parameters.get('engagement_rate', 0.1)  # 10% chance to like
        
        context.add_log(f"Starting home feed scroll for {scroll_duration} seconds with {engagement_rate*100}% engagement rate")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            start_time = time.time()
            posts_viewed = 0
            posts_liked = 0
            
            # Store scroll statistics
            context.store_data("scroll_stats", {
                "posts_viewed": 0,
                "posts_liked": 0,
                "scroll_actions": 0,
                "start_time": start_time
            })
            
            while (time.time() - start_time) < scroll_duration:
                # Human-like scroll timing (1-4 seconds between scrolls)
                scroll_delay = random.uniform(1.0, 4.0)
                await asyncio.sleep(scroll_delay)
                
                # Perform scroll action
                success = await self._perform_human_scroll(context)
                if not success:
                    context.add_log("Scroll action failed, continuing...")
                    continue
                
                # Update scroll stats
                stats = context.get_data("scroll_stats")
                stats["scroll_actions"] += 1
                
                # Occasionally pause to "read" posts (simulate human behavior)
                if random.random() < 0.3:  # 30% chance to pause
                    pause_duration = random.uniform(2.0, 8.0)
                    context.add_log(f"Pausing to read content for {pause_duration:.1f} seconds")
                    await asyncio.sleep(pause_duration)
                
                # Check for posts to potentially like
                if random.random() < engagement_rate:
                    liked = await self._try_like_post(context, selector_registry)
                    if liked:
                        posts_liked += 1
                        stats["posts_liked"] = posts_liked
                        context.add_log(f"Liked a post! Total likes: {posts_liked}")
                
                posts_viewed += 1
                stats["posts_viewed"] = posts_viewed
                
                # Log progress every 10 posts
                if posts_viewed % 10 == 0:
                    elapsed = time.time() - start_time
                    context.add_log(f"Progress: {posts_viewed} posts viewed, {posts_liked} liked in {elapsed:.1f}s")
            
            # Final statistics
            elapsed = time.time() - start_time
            context.add_log(f"Scroll completed: {posts_viewed} posts viewed, {posts_liked} liked in {elapsed:.1f}s")
            
            # Store final results
            context.result_data = {
                "posts_viewed": posts_viewed,
                "posts_liked": posts_liked,
                "scroll_duration": elapsed,
                "engagement_rate_actual": posts_liked / max(posts_viewed, 1),
                "scroll_actions": stats["scroll_actions"]
            }
            
            return ActionState.VERIFY
            
        except Exception as e:
            context.add_log(f"Scrolling failed: {e}")
            raise
    
    async def _perform_human_scroll(self, context: ActionContext) -> bool:
        """Perform a human-like scroll action"""
        try:
            # Get screen dimensions for scroll calculation
            screen_size = await context.driver.get_window_size()
            screen_height = screen_size['height']
            screen_width = screen_size['width']
            
            # Calculate scroll points (avoid edges and tab bar)
            start_y = screen_height * random.uniform(0.7, 0.8)  # Start from lower area
            end_y = screen_height * random.uniform(0.2, 0.4)    # End in upper area
            x = screen_width * 0.5  # Center horizontally
            
            # Variable scroll speed (human-like)
            scroll_duration = random.randint(800, 1500)  # milliseconds
            
            # Perform swipe
            await context.driver.swipe(x, start_y, x, end_y, scroll_duration)
            
            return True
            
        except Exception as e:
            logger.warning(f"Scroll action failed: {e}")
            return False
    
    async def _try_like_post(self, context: ActionContext, selector_registry) -> bool:
        """Attempt to like a post in the current view"""
        try:
            # Look for like button
            like_result = await selector_registry.find_like_button_home_feed(timeout=2)
            if not like_result:
                return False
            
            # Human-like delay before liking
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Tap like button
            await context.driver.click_element(like_result.element)
            
            # Brief delay to verify like registered
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            return True
            
        except Exception as e:
            logger.debug(f"Like attempt failed: {e}")
            return False


class VerifyScrollStateHandler(BaseActionStateHandler):
    """Verify scroll results and statistics"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Verifying scroll results")
        
        result_data = context.result_data
        if not result_data:
            raise RuntimeError("No scroll results to verify")
        
        posts_viewed = result_data.get("posts_viewed", 0)
        posts_liked = result_data.get("posts_liked", 0)
        scroll_duration = result_data.get("scroll_duration", 0)
        
        # Basic validation
        if posts_viewed == 0:
            raise RuntimeError("No posts were viewed during scroll")
        
        if scroll_duration < 5:
            raise RuntimeError("Scroll duration too short")
        
        # Calculate engagement metrics
        engagement_rate = posts_liked / posts_viewed if posts_viewed > 0 else 0
        posts_per_minute = (posts_viewed / scroll_duration) * 60 if scroll_duration > 0 else 0
        
        context.add_log(f"Scroll verification successful:")
        context.add_log(f"  - Posts viewed: {posts_viewed}")
        context.add_log(f"  - Posts liked: {posts_liked}")
        context.add_log(f"  - Engagement rate: {engagement_rate:.2%}")
        context.add_log(f"  - Posts per minute: {posts_per_minute:.1f}")
        context.add_log(f"  - Duration: {scroll_duration:.1f}s")
        
        # Add metrics to result
        result_data.update({
            "engagement_rate_calculated": engagement_rate,
            "posts_per_minute": posts_per_minute,
            "verification_passed": True
        })
        
        return ActionState.LOG


class IGScrollHomeFeedAction(BaseAction):
    """
    Instagram SCROLL_HOME_FEED action - Human-like feed scrolling with engagement
    """
    
    def __init__(self, context: ActionContext):
        super().__init__(context)
    
    def _register_action_handlers(self) -> None:
        """Register SCROLL_HOME_FEED specific state handlers"""
        handlers = {
            ActionState.NAVIGATE: NavigateToFeedStateHandler(ActionState.NAVIGATE, self),
            ActionState.SCROLL: ScrollFeedStateHandler(ActionState.SCROLL, self),
            ActionState.VERIFY: VerifyScrollStateHandler(ActionState.VERIFY, self)
        }
        
        self.state_machine.register_handlers(handlers)
    
    async def validate_target(self, target_value: str) -> bool:
        """Validate scroll parameters"""
        # For scroll action, target is not used but parameters are
        return True
    
    async def execute(self) -> bool:
        """Execute SCROLL_HOME_FEED with real selector integration"""
        scroll_duration = self.context.payload.parameters.get('scroll_duration', 60)
        engagement_rate = self.context.payload.parameters.get('engagement_rate', 0.1)
        
        logger.info(f"Starting SCROLL_HOME_FEED execution for {scroll_duration}s with {engagement_rate} engagement")
        
        # Store references for state handlers
        self.context.store_data("watchdog_system", self.state_machine.watchdog_system)
        
        # Initialize Instagram selector registry
        if self.context.driver:
            selector_registry = InstagramSelectorRegistry(self.context.driver)
            self.context.store_data("selector_registry", selector_registry)
        else:
            raise RuntimeError("Driver not available for selector registry")
        
        # Execute the FSM
        success = await super().execute()
        
        if success:
            logger.info(f"SCROLL_HOME_FEED completed successfully")
            result_data = self.context.result_data
            
            # Log final statistics
            posts_viewed = result_data.get('posts_viewed', 0)
            posts_liked = result_data.get('posts_liked', 0)
            duration = result_data.get('scroll_duration', 0)
            logger.info(f"Final stats: {posts_viewed} posts viewed, {posts_liked} liked in {duration:.1f}s")
            
            # Log selector telemetry
            selector_registry = self.context.get_data("selector_registry")
            if selector_registry:
                telemetry = selector_registry.get_selector_telemetry()
                logger.info(f"Selector telemetry: {telemetry}")
        else:
            logger.error(f"SCROLL_HOME_FEED failed: {self.context.error_message}")
        
        return success
    
    def get_expected_duration_ms(self) -> int:
        """Get expected duration for this action"""
        scroll_duration = self.context.payload.parameters.get('scroll_duration', 60)
        return (scroll_duration + 10) * 1000  # Add 10s buffer
    
    def get_action_metadata(self) -> Dict[str, Any]:
        """Get action-specific metadata"""
        return {
            "action_type": "SCROLL_HOME_FEED",
            "supports_parameters": ["scroll_duration", "engagement_rate"],
            "expected_results": ["posts_viewed", "posts_liked", "engagement_rate", "scroll_duration"],
            "human_behavior": True,
            "rate_limit_sensitive": True
        }
