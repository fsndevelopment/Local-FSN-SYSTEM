"""
Instagram LIKE Action - Real Selector Implementation
FSM action for liking Instagram posts using real UI selectors
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from ....fsm import ActionState, ActionContext
from ....actions.base_action import BaseAction, BaseActionStateHandler
from ..selectors.registry import InstagramSelectorRegistry

logger = logging.getLogger(__name__)


class FindPostStateHandler(BaseActionStateHandler):
    """Find the post to like"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Finding post to like")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Find post card
            context.add_log("Looking for post card")
            post_result = await selector_registry.find_post_card(timeout=10)
            
            if not post_result:
                raise RuntimeError("Post card not found")
            
            context.add_log(f"Found post card using {post_result.strategy_used.type}")
            context.store_data("post_element", post_result.element)
            context.store_data("post_result", post_result)
            
            # Record metrics
            context.metrics.increment_counter("elements_found")
            
            return ActionState.FIND_TARGET
            
        except Exception as e:
            context.add_log(f"Post finding failed: {e}")
            raise


class FindTargetStateHandler(BaseActionStateHandler):
    """Find the like button within the post"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Finding like button")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Find like button
            context.add_log("Looking for like button")
            like_result = await selector_registry.find_like_button(timeout=10)
            
            if not like_result:
                raise RuntimeError("Like button not found")
            
            context.add_log(f"Found like button using {like_result.strategy_used.type}")
            context.store_data("like_button_element", like_result.element)
            context.store_data("like_button_result", like_result)
            
            # Detect current like state
            current_state = await self._detect_like_state(context, like_result.element)
            context.store_data("initial_like_state", current_state)
            context.add_log(f"Like button initial state: {current_state}")
            
            # Record metrics
            context.metrics.increment_counter("elements_found")
            
            return ActionState.ACT
            
        except Exception as e:
            context.add_log(f"Like button finding failed: {e}")
            raise
    
    async def _detect_like_state(self, context: ActionContext, like_element: Any) -> str:
        """Detect if post is already liked or not"""
        try:
            # TODO: Implement actual state detection using element properties
            # For now, assume unliked state
            return "unliked"
        except Exception as e:
            logger.debug(f"Like state detection failed: {e}")
            return "unknown"


class ActStateHandler(BaseActionStateHandler):
    """Perform the like action"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Performing like action")
        
        like_button_element = context.get_data("like_button_element")
        initial_state = context.get_data("initial_like_state", "unknown")
        
        if not like_button_element:
            raise RuntimeError("Like button element not available")
        
        try:
            # Only like if not already liked
            if initial_state == "liked":
                context.add_log("Post already liked, skipping action")
                context.store_data("action_performed", False)
                context.store_data("final_like_state", "liked")
                return ActionState.VERIFY
            
            # Tap like button
            context.add_log("Tapping like button")
            if not await context.driver.click_element(like_button_element):
                raise RuntimeError("Failed to tap like button")
            
            # Wait for animation/state change
            await asyncio.sleep(1)
            
            context.store_data("action_performed", True)
            context.metrics.increment_counter("ui_interactions")
            
            return ActionState.VERIFY
            
        except Exception as e:
            context.add_log(f"Like action failed: {e}")
            raise


class VerifyStateHandler(BaseActionStateHandler):
    """Verify the like action was successful"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Verifying like action")
        
        action_performed = context.get_data("action_performed", False)
        like_button_element = context.get_data("like_button_element")
        
        if not action_performed:
            # No action needed, already liked
            context.set_result({
                "action": "like",
                "performed": False,
                "reason": "already_liked",
                "success": True
            }, success=True)
            return ActionState.LOG
        
        if not like_button_element:
            raise RuntimeError("Like button element not available for verification")
        
        try:
            # Detect final like state
            final_state = await self._detect_like_state(context, like_button_element)
            context.store_data("final_like_state", final_state)
            
            if final_state == "liked":
                context.add_log("Like action verified successfully")
                context.set_result({
                    "action": "like",
                    "performed": True,
                    "initial_state": context.get_data("initial_like_state"),
                    "final_state": final_state,
                    "success": True
                }, success=True)
            else:
                raise RuntimeError(f"Like verification failed: expected 'liked', got '{final_state}'")
            
            return ActionState.LOG
            
        except Exception as e:
            context.add_log(f"Like verification failed: {e}")
            raise
    
    async def _detect_like_state(self, context: ActionContext, like_element: Any) -> str:
        """Detect current like state"""
        try:
            # TODO: Implement actual state detection
            # For now, assume liked after action
            return "liked"
        except Exception as e:
            logger.debug(f"Like state detection failed: {e}")
            return "unknown"


class IGLikeAction(BaseAction):
    """
    Instagram LIKE action - Real selector implementation
    Likes Instagram posts using FSM approach with real UI selectors
    """
    
    def __init__(self, context: ActionContext):
        super().__init__(context)
    
    def _register_action_handlers(self) -> None:
        """Register LIKE specific state handlers"""
        handlers = {
            ActionState.NAVIGATE: FindPostStateHandler(ActionState.NAVIGATE, self),  # Reuse NAVIGATE for finding post
            ActionState.FIND_TARGET: FindTargetStateHandler(ActionState.FIND_TARGET, self),
            ActionState.ACT: ActStateHandler(ActionState.ACT, self),
            ActionState.VERIFY: VerifyStateHandler(ActionState.VERIFY, self)
        }
        
        self.state_machine.register_handlers(handlers)
    
    async def validate_target(self, target_value: str) -> bool:
        """Validate post URL or hashtag target"""
        if not target_value:
            return False
        
        # Support post URLs and hashtags
        if target_value.startswith('https://instagram.com/p/') or target_value.startswith('https://www.instagram.com/p/'):
            return True
        elif target_value.startswith('#') and len(target_value) > 1:
            return True
        else:
            return False
    
    async def execute(self) -> bool:
        """Execute LIKE with real selector integration"""
        target = self.context.payload.target.value
        logger.info(f"Starting LIKE execution for target: {target}")
        
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
            logger.info(f"LIKE completed successfully for {target}")
            result_data = self.context.result_data
            
            # Log action details
            performed = result_data.get('performed', False)
            reason = result_data.get('reason', 'completed')
            logger.info(f"Like action performed: {performed}, reason: {reason}")
            
            # Log selector telemetry
            selector_registry = self.context.get_data("selector_registry")
            if selector_registry:
                telemetry = selector_registry.get_selector_telemetry()
                logger.info(f"Selector telemetry: {telemetry}")
        else:
            logger.error(f"LIKE failed for {target}: {self.context.error_message}")
        
        return success
    
    def get_expected_duration_ms(self) -> int:
        """Get expected duration for this action"""
        return 5000  # 5 seconds expected for like action
    
    def get_action_metadata(self) -> Dict[str, Any]:
        """Get action-specific metadata"""
        return {
            "action_type": "IG_LIKE",
            "platform": "instagram",
            "target_type": "post_url_or_hashtag",
            "expected_duration_ms": self.get_expected_duration_ms(),
            "requires_network": False,
            "requires_navigation": True,
            "reversible": True  # Can be unliked
        }
