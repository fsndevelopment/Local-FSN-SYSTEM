"""
Instagram VIEW_STORY Action - Story navigation with realistic timing
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


class NavigateToStoriesStateHandler(BaseActionStateHandler):
    """Navigate to home feed and find stories"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Navigating to stories area")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Ensure we're on home feed first
            home_tab_result = await selector_registry.find_home_tab(timeout=5)
            if home_tab_result:
                context.add_log("Tapping home tab to ensure we're on home feed")
                await context.driver.click_element(home_tab_result.element)
                await asyncio.sleep(2)
            
            # Look for stories tray
            stories_tray_result = await selector_registry.find_stories_tray(timeout=5)
            if not stories_tray_result:
                raise RuntimeError("Stories tray not found")
            
            context.add_log("Found stories tray")
            return ActionState.SELECT_STORY
            
        except Exception as e:
            context.add_log(f"Navigation to stories failed: {e}")
            raise


class SelectStoryStateHandler(BaseActionStateHandler):
    """Select a story to view"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        username = context.payload.parameters.get('username')  # Specific user or None for random
        
        context.add_log(f"Selecting story to view (username: {username or 'random'})")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            if username:
                # TODO: Implement specific username story selection
                context.add_log(f"Specific username story selection not yet implemented, using random")
            
            # Find any available story ring
            story_ring_result = await selector_registry.find_story_ring(timeout=5)
            if not story_ring_result:
                raise RuntimeError("No story rings found")
            
            context.add_log("Found story ring, tapping to open...")
            
            # Human-like delay before tapping
            delay = random.uniform(1.0, 3.0)
            await asyncio.sleep(delay)
            
            # Tap story ring to open
            await context.driver.click_element(story_ring_result.element)
            
            # Wait for story to load
            await asyncio.sleep(3)
            
            context.add_log("Story opened successfully")
            
            # Store story selection details
            context.store_data("story_info", {
                "selector_used": story_ring_result.strategy_used.type,
                "selection_delay": delay,
                "opened_at": time.time()
            })
            
            return ActionState.VIEW
            
        except Exception as e:
            context.add_log(f"Story selection failed: {e}")
            raise


class ViewStoryStateHandler(BaseActionStateHandler):
    """View story with realistic timing and navigation"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        view_all = context.payload.parameters.get('view_all', True)
        
        context.add_log(f"Viewing story (view_all: {view_all})")
        
        try:
            stories_viewed = 0
            start_time = time.time()
            
            if view_all:
                # View multiple story segments with realistic timing
                stories_viewed = await self._view_all_story_segments(context)
            else:
                # View just one story segment
                stories_viewed = await self._view_single_story_segment(context)
            
            duration = time.time() - start_time
            
            context.add_log(f"Story viewing completed: {stories_viewed} segments in {duration:.1f}s")
            
            # Store viewing results
            context.result_data = {
                "stories_viewed": stories_viewed,
                "viewing_duration": duration,
                "view_mode": "all" if view_all else "single"
            }
            
            return ActionState.EXIT_STORY
            
        except Exception as e:
            context.add_log(f"Story viewing failed: {e}")
            raise
    
    async def _view_all_story_segments(self, context: ActionContext) -> int:
        """View all available story segments"""
        segments_viewed = 0
        max_segments = 10  # Safety limit
        
        for i in range(max_segments):
            # Realistic viewing time per segment (3-8 seconds)
            view_time = random.uniform(3.0, 8.0)
            context.add_log(f"Viewing story segment {i+1} for {view_time:.1f}s")
            
            await asyncio.sleep(view_time)
            segments_viewed += 1
            
            # Try to advance to next segment (tap right side of screen)
            try:
                screen_size = await context.driver.get_window_size()
                screen_width = screen_size['width']
                screen_height = screen_size['height']
                
                # Tap right side to advance (avoid accidental interactions)
                tap_x = screen_width * 0.8
                tap_y = screen_height * 0.5
                
                await context.driver.tap(tap_x, tap_y)
                await asyncio.sleep(1)  # Wait for transition
                
            except Exception as e:
                context.add_log(f"Could not advance story segment: {e}")
                break  # Assume we reached the end
        
        return segments_viewed
    
    async def _view_single_story_segment(self, context: ActionContext) -> int:
        """View just one story segment"""
        view_time = random.uniform(4.0, 10.0)
        context.add_log(f"Viewing single story segment for {view_time:.1f}s")
        
        await asyncio.sleep(view_time)
        return 1


class ExitStoryStateHandler(BaseActionStateHandler):
    """Exit story properly without accidental interactions"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Exiting story view")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Look for story dismiss button
            dismiss_result = await selector_registry.find_story_dismiss_button(timeout=5)
            if dismiss_result:
                context.add_log("Found story dismiss button, tapping...")
                await context.driver.click_element(dismiss_result.element)
            else:
                # Fallback: tap outside story area (left edge)
                context.add_log("Dismiss button not found, using fallback exit method")
                screen_size = await context.driver.get_window_size()
                screen_height = screen_size['height']
                
                tap_x = 20  # Far left edge
                tap_y = screen_height * 0.5
                
                await context.driver.tap(tap_x, tap_y)
            
            # Wait for story to close
            await asyncio.sleep(2)
            
            # Verify we're back on home feed
            home_feed_result = await selector_registry.find_home_feed_container(timeout=3)
            if home_feed_result:
                context.add_log("Successfully exited story and returned to home feed")
            else:
                context.add_log("Warning: Could not verify return to home feed")
            
            return ActionState.VERIFY
            
        except Exception as e:
            context.add_log(f"Story exit failed: {e}")
            raise


class VerifyStoryViewStateHandler(BaseActionStateHandler):
    """Verify story viewing results"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Verifying story viewing results")
        
        result_data = context.result_data
        if not result_data:
            raise RuntimeError("No story viewing results to verify")
        
        stories_viewed = result_data.get("stories_viewed", 0)
        viewing_duration = result_data.get("viewing_duration", 0)
        
        # Basic validation
        if stories_viewed == 0:
            raise RuntimeError("No stories were viewed")
        
        if viewing_duration < 1:
            raise RuntimeError("Viewing duration too short")
        
        # Calculate metrics
        avg_time_per_story = viewing_duration / stories_viewed if stories_viewed > 0 else 0
        
        context.add_log(f"Story viewing verification successful:")
        context.add_log(f"  - Stories viewed: {stories_viewed}")
        context.add_log(f"  - Total duration: {viewing_duration:.1f}s")
        context.add_log(f"  - Average time per story: {avg_time_per_story:.1f}s")
        
        # Add verification details
        result_data.update({
            "avg_time_per_story": avg_time_per_story,
            "verification_passed": True
        })
        
        return ActionState.LOG


class IGViewStoryAction(BaseAction):
    """
    Instagram VIEW_STORY action - Story navigation with realistic timing
    """
    
    def __init__(self, context: ActionContext):
        super().__init__(context)
    
    def _register_action_handlers(self) -> None:
        """Register VIEW_STORY specific state handlers"""
        handlers = {
            ActionState.NAVIGATE: NavigateToStoriesStateHandler(ActionState.NAVIGATE, self),
            ActionState.SELECT_STORY: SelectStoryStateHandler(ActionState.SELECT_STORY, self),
            ActionState.VIEW: ViewStoryStateHandler(ActionState.VIEW, self),
            ActionState.EXIT_STORY: ExitStoryStateHandler(ActionState.EXIT_STORY, self),
            ActionState.VERIFY: VerifyStoryViewStateHandler(ActionState.VERIFY, self)
        }
        
        self.state_machine.register_handlers(handlers)
    
    async def validate_target(self, target_value: str) -> bool:
        """Validate story parameters"""
        # For story action, target is not used but parameters are
        return True
    
    async def execute(self) -> bool:
        """Execute VIEW_STORY with real selector integration"""
        username = self.context.payload.parameters.get('username')
        view_all = self.context.payload.parameters.get('view_all', True)
        
        logger.info(f"Starting VIEW_STORY execution (username: {username or 'random'}, view_all: {view_all})")
        
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
            logger.info("VIEW_STORY completed successfully")
            result_data = self.context.result_data
            
            # Log viewing statistics
            stories_viewed = result_data.get('stories_viewed', 0)
            duration = result_data.get('viewing_duration', 0)
            logger.info(f"Story viewing stats: {stories_viewed} segments in {duration:.1f}s")
            
            # Log selector telemetry
            selector_registry = self.context.get_data("selector_registry")
            if selector_registry:
                telemetry = selector_registry.get_selector_telemetry()
                logger.info(f"Selector telemetry: {telemetry}")
        else:
            logger.error(f"VIEW_STORY failed: {self.context.error_message}")
        
        return success
    
    def get_expected_duration_ms(self) -> int:
        """Get expected duration for this action"""
        view_all = self.context.payload.parameters.get('view_all', True)
        return 60000 if view_all else 15000  # 60s for all, 15s for single
    
    def get_action_metadata(self) -> Dict[str, Any]:
        """Get action-specific metadata"""
        return {
            "action_type": "VIEW_STORY",
            "supports_parameters": ["username", "view_all"],
            "expected_results": ["stories_viewed", "viewing_duration", "avg_time_per_story"],
            "human_behavior": True,
            "rate_limit_sensitive": False
        }
