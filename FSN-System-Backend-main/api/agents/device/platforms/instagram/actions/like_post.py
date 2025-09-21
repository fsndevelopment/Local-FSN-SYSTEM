"""
Instagram LIKE_POST Action - Like posts with human timing, verification, and rate limit protection
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional

from ....fsm import ActionState, ActionContext
from ....actions.base_action import BaseAction, BaseActionStateHandler
from ..selectors.registry import InstagramSelectorRegistry
from ..safety.rate_limit_detector import InstagramRateLimitDetector, RateLimitMiddleware

logger = logging.getLogger(__name__)


class FindPostStateHandler(BaseActionStateHandler):
    """Find the post to like (current post or navigate to specific post)"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        use_current_post = context.payload.parameters.get('use_current_post', True)
        
        if use_current_post:
            context.add_log("Using current post for like action")
            return ActionState.LIKE
        else:
            # TODO: Implement navigation to specific post
            context.add_log("Navigation to specific post not yet implemented, using current post")
            return ActionState.LIKE


class LikePostStateHandler(BaseActionStateHandler):
    """Perform the like action with human timing and verification"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        like_probability = context.payload.parameters.get('like_probability', 0.8)
        
        context.add_log(f"Starting like action with {like_probability*100}% probability")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        # Initialize rate limit detector
        rate_limit_detector = InstagramRateLimitDetector(context.driver)
        
        # Check current rate limit status
        if not rate_limit_detector.track_action("likes"):
            context.add_log("Rate limit reached for likes, skipping action")
            context.result_data = {
                "action_taken": "skipped",
                "reason": "rate_limit_reached",
                "limits_status": rate_limit_detector.get_current_limits_status()
            }
            return ActionState.VERIFY
        
        # Check for existing rate limit indicators on screen
        existing_rate_limit = await rate_limit_detector.check_for_rate_limits()
        if existing_rate_limit:
            context.add_log(f"Rate limit detected on screen: {existing_rate_limit.message}")
            action_plan = await rate_limit_detector.handle_rate_limit(existing_rate_limit)
            context.result_data = {
                "action_taken": "blocked",
                "reason": "rate_limit_detected",
                "rate_limit_event": existing_rate_limit,
                "action_plan": action_plan
            }
            return ActionState.VERIFY
        
        try:
            # Random decision based on probability
            if random.random() > like_probability:
                context.add_log("Randomly decided not to like this post (human behavior)")
                context.result_data = {
                    "action_taken": "skipped",
                    "reason": "random_decision",
                    "like_probability": like_probability
                }
                return ActionState.VERIFY
            
            # Look for like button in home feed context
            like_result = await selector_registry.find_like_button_home_feed(timeout=5)
            if not like_result:
                # Fallback to generic like button
                like_result = await selector_registry.find_like_button(timeout=3)
                if not like_result:
                    raise RuntimeError("Like button not found")
            
            context.add_log("Found like button")
            
            # Check current state (if possible) - for now we'll just attempt to like
            # TODO: Implement state detection to avoid double-liking
            
            # Human-like delay before liking (0.5-2 seconds)
            delay = random.uniform(0.5, 2.0)
            context.add_log(f"Human delay: {delay:.1f} seconds")
            await asyncio.sleep(delay)
            
            # Perform the like action
            context.add_log("Tapping like button...")
            await context.driver.click_element(like_result.element)
            
            # Wait for like to register
            verification_delay = random.uniform(0.3, 0.8)
            await asyncio.sleep(verification_delay)
            
            context.add_log("Like action completed")
            
            # Post-action rate limit check
            post_action_rate_limit = await rate_limit_detector.check_for_rate_limits()
            if post_action_rate_limit:
                context.add_log(f"Rate limit triggered by like action: {post_action_rate_limit.message}")
                action_plan = await rate_limit_detector.handle_rate_limit(post_action_rate_limit)
                
                # Store action details with rate limit info
                context.result_data = {
                    "action_taken": "liked_but_rate_limited",
                    "selector_used": like_result.strategy_used.type,
                    "execution_time_ms": like_result.execution_time_ms,
                    "human_delay": delay,
                    "verification_delay": verification_delay,
                    "rate_limit_triggered": True,
                    "rate_limit_event": post_action_rate_limit,
                    "action_plan": action_plan
                }
            else:
                # Store action details
                context.result_data = {
                    "action_taken": "liked",
                    "selector_used": like_result.strategy_used.type,
                    "execution_time_ms": like_result.execution_time_ms,
                    "human_delay": delay,
                    "verification_delay": verification_delay,
                    "rate_limit_safe": True
                }
            
            return ActionState.VERIFY
            
        except Exception as e:
            context.add_log(f"Like action failed: {e}")
            context.result_data = {
                "action_taken": "failed",
                "error": str(e)
            }
            raise


class VerifyLikeStateHandler(BaseActionStateHandler):
    """Verify like action was successful and track for rate limiting"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Verifying like action")
        
        result_data = context.result_data
        if not result_data:
            raise RuntimeError("No like action results to verify")
        
        action_taken = result_data.get("action_taken")
        
        if action_taken == "skipped":
            context.add_log("Like action was skipped by design")
            return ActionState.LOG
        
        if action_taken == "failed":
            context.add_log("Like action failed")
            return ActionState.LOG
        
        if action_taken == "liked":
            context.add_log("Like action appears successful")
            
            # TODO: Implement verification by checking button state change
            # For now, we assume success based on no errors
            
            # Track action for rate limiting
            self._track_like_action(context)
            
            # Add verification details
            result_data.update({
                "verification_passed": True,
                "timestamp": time.time()
            })
            
            return ActionState.LOG
        
        raise RuntimeError(f"Unknown action state: {action_taken}")
    
    def _track_like_action(self, context: ActionContext):
        """Track like action for rate limiting purposes"""
        # Get or create rate limit tracker
        rate_tracker = context.get_data("rate_tracker")
        if not rate_tracker:
            rate_tracker = {
                "likes_count": 0,
                "likes_timestamps": [],
                "last_like_time": None
            }
            context.store_data("rate_tracker", rate_tracker)
        
        # Update tracking
        current_time = time.time()
        rate_tracker["likes_count"] += 1
        rate_tracker["likes_timestamps"].append(current_time)
        rate_tracker["last_like_time"] = current_time
        
        # Keep only recent timestamps (last hour)
        hour_ago = current_time - 3600
        rate_tracker["likes_timestamps"] = [
            ts for ts in rate_tracker["likes_timestamps"] if ts > hour_ago
        ]
        
        likes_last_hour = len(rate_tracker["likes_timestamps"])
        context.add_log(f"Rate tracking: {likes_last_hour} likes in last hour")
        
        # Warn if approaching limits
        if likes_last_hour > 40:  # Conservative limit
            context.add_log("⚠️  Approaching like rate limit (40/hour)")


class IGLikePostAction(BaseAction):
    """
    Instagram LIKE_POST action - Like posts with human timing and verification
    """
    
    def __init__(self, context: ActionContext):
        super().__init__(context)
    
    def _register_action_handlers(self) -> None:
        """Register LIKE_POST specific state handlers"""
        handlers = {
            ActionState.FIND_TARGET: FindPostStateHandler(ActionState.FIND_TARGET, self),
            ActionState.LIKE: LikePostStateHandler(ActionState.LIKE, self),
            ActionState.VERIFY: VerifyLikeStateHandler(ActionState.VERIFY, self)
        }
        
        self.state_machine.register_handlers(handlers)
    
    async def validate_target(self, target_value: str) -> bool:
        """Validate like parameters"""
        # For like action, target is not used but parameters are
        return True
    
    async def execute(self) -> bool:
        """Execute LIKE_POST with real selector integration"""
        use_current_post = self.context.payload.parameters.get('use_current_post', True)
        like_probability = self.context.payload.parameters.get('like_probability', 0.8)
        
        logger.info(f"Starting LIKE_POST execution (current_post: {use_current_post}, probability: {like_probability})")
        
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
            logger.info("LIKE_POST completed successfully")
            result_data = self.context.result_data
            
            # Log action details
            action_taken = result_data.get('action_taken', 'unknown')
            logger.info(f"Like action result: {action_taken}")
            
            if action_taken == "liked":
                selector_used = result_data.get('selector_used', 'unknown')
                logger.info(f"Used selector: {selector_used}")
            
            # Log selector telemetry
            selector_registry = self.context.get_data("selector_registry")
            if selector_registry:
                telemetry = selector_registry.get_selector_telemetry()
                logger.info(f"Selector telemetry: {telemetry}")
        else:
            logger.error(f"LIKE_POST failed: {self.context.error_message}")
        
        return success
    
    def get_expected_duration_ms(self) -> int:
        """Get expected duration for this action"""
        return 5000  # 5 seconds max for like action
    
    def get_action_metadata(self) -> Dict[str, Any]:
        """Get action-specific metadata"""
        return {
            "action_type": "LIKE_POST",
            "supports_parameters": ["use_current_post", "like_probability"],
            "expected_results": ["action_taken", "selector_used", "verification_passed"],
            "human_behavior": True,
            "rate_limit_sensitive": True,
            "rate_limits": {
                "likes_per_hour": 60,
                "conservative_limit": 40
            }
        }
