"""
Instagram FOLLOW_ACCOUNT Action - Strategic following with safety limits and human behavior
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional

from ....fsm import ActionState, ActionContext
from ....actions.base_action import BaseAction, BaseActionStateHandler
from ..selectors.registry import InstagramSelectorRegistry
from ..safety.rate_limit_detector import InstagramRateLimitDetector

logger = logging.getLogger(__name__)


class NavigateToProfileStateHandler(BaseActionStateHandler):
    """Navigate to the target profile to follow"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        target_username = context.payload.target.value.lstrip('@')
        context.add_log(f"Navigating to profile: {target_username}")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Navigate to search
            search_result = await selector_registry.find_search_tab(timeout=5)
            if not search_result:
                raise RuntimeError("Could not find search tab")
            
            context.add_log("Clicking search tab")
            await context.driver.click_element(search_result.element)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            # Find search input
            search_input_result = await selector_registry.find_search_input(timeout=5)
            if not search_input_result:
                raise RuntimeError("Could not find search input")
            
            context.add_log(f"Searching for username: {target_username}")
            await context.driver.click_element(search_input_result.element)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Type username
            await context.driver.send_keys(search_input_result.element, target_username)
            await asyncio.sleep(random.uniform(1.5, 3.0))  # Wait for search results
            
            # Find and click the profile in search results
            # This will depend on the search results selector
            context.add_log("Looking for profile in search results")
            
            # For now, we'll assume the first result is correct
            # TODO: Implement more sophisticated result selection
            search_results = await selector_registry.find_search_results(timeout=5)
            if search_results and len(search_results) > 0:
                context.add_log("Clicking on first search result")
                await context.driver.click_element(search_results[0].element)
                await asyncio.sleep(random.uniform(2.0, 3.0))
            else:
                raise RuntimeError(f"No search results found for {target_username}")
            
            return ActionState.FIND_TARGET
            
        except Exception as e:
            context.add_log(f"Navigation failed: {e}")
            raise


class FindFollowButtonStateHandler(BaseActionStateHandler):
    """Find the follow button on the profile"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Looking for follow button")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Look for follow button
            follow_result = await selector_registry.find_follow_button(timeout=8)
            if not follow_result:
                # Check if already following
                following_result = await selector_registry.find_following_button(timeout=3)
                if following_result:
                    context.add_log("Already following this account")
                    context.result_data = {
                        "action_taken": "already_following",
                        "reason": "account_already_followed"
                    }
                    return ActionState.VERIFY
                else:
                    raise RuntimeError("Could not find follow button or following indicator")
            
            # Store follow button for action
            context.store_data("follow_button", follow_result)
            context.add_log(f"Found follow button using strategy: {follow_result.strategy_used.type}")
            
            return ActionState.ACT
            
        except Exception as e:
            context.add_log(f"Failed to find follow button: {e}")
            raise


class FollowActionStateHandler(BaseActionStateHandler):
    """Perform the follow action with human timing and safety checks"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        follow_probability = context.payload.parameters.get('follow_probability', 0.8)
        
        context.add_log(f"Starting follow action with {follow_probability*100}% probability")
        
        # Initialize rate limit detector
        rate_limit_detector = InstagramRateLimitDetector(context.driver)
        
        # Check current rate limit status
        if not rate_limit_detector.track_action("follows"):
            context.add_log("Rate limit reached for follows, skipping action")
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
            # Random decision based on probability (human unpredictability)
            if random.random() > follow_probability:
                context.add_log("Randomly decided not to follow this account (human behavior)")
                context.result_data = {
                    "action_taken": "skipped",
                    "reason": "random_human_decision",
                    "follow_probability": follow_probability
                }
                return ActionState.VERIFY
            
            # Get follow button
            follow_result = context.get_data("follow_button")
            if not follow_result:
                raise RuntimeError("Follow button not available")
            
            # Human-like delay before action
            delay = random.uniform(1.0, 3.0)
            context.add_log(f"Human delay before follow: {delay:.2f}s")
            await asyncio.sleep(delay)
            
            # Perform the follow action
            context.add_log("Tapping follow button...")
            await context.driver.click_element(follow_result.element)
            
            # Wait for follow to register
            verification_delay = random.uniform(0.8, 1.5)
            await asyncio.sleep(verification_delay)
            
            context.add_log("Follow action completed")
            
            # Post-action rate limit check
            post_action_rate_limit = await rate_limit_detector.check_for_rate_limits()
            if post_action_rate_limit:
                context.add_log(f"Rate limit triggered by follow action: {post_action_rate_limit.message}")
                action_plan = await rate_limit_detector.handle_rate_limit(post_action_rate_limit)
                
                # Store action details with rate limit info
                context.result_data = {
                    "action_taken": "followed_but_rate_limited",
                    "selector_used": follow_result.strategy_used.type,
                    "execution_time_ms": follow_result.execution_time_ms,
                    "human_delay": delay,
                    "verification_delay": verification_delay,
                    "rate_limit_triggered": True,
                    "rate_limit_event": post_action_rate_limit,
                    "action_plan": action_plan
                }
            else:
                # Store action details
                context.result_data = {
                    "action_taken": "followed",
                    "selector_used": follow_result.strategy_used.type,
                    "execution_time_ms": follow_result.execution_time_ms,
                    "human_delay": delay,
                    "verification_delay": verification_delay,
                    "rate_limit_safe": True
                }
            
            return ActionState.VERIFY
            
        except Exception as e:
            context.add_log(f"Follow action failed: {e}")
            context.result_data = {
                "action_taken": "failed",
                "error": str(e)
            }
            raise


class VerifyFollowStateHandler(BaseActionStateHandler):
    """Verify follow action was successful"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Verifying follow action")
        
        result_data = context.result_data
        if not result_data:
            context.add_log("No result data available for verification")
            return ActionState.LOG
        
        action_taken = result_data.get("action_taken")
        
        if action_taken in ["followed", "followed_but_rate_limited"]:
            context.add_log("Follow action verification successful")
            
            # Optional: Check if button changed to "Following"
            try:
                selector_registry = context.get_data("selector_registry")
                if selector_registry:
                    following_result = await selector_registry.find_following_button(timeout=3)
                    if following_result:
                        context.add_log("Verified: Follow button changed to Following")
                        result_data["verification"] = "button_changed_to_following"
                    else:
                        context.add_log("Could not verify button state change")
                        result_data["verification"] = "button_state_unclear"
            except Exception as e:
                context.add_log(f"Verification check failed: {e}")
                result_data["verification"] = f"verification_error: {e}"
                
        elif action_taken == "already_following":
            context.add_log("Account was already being followed")
            
        elif action_taken == "skipped":
            reason = result_data.get("reason", "unknown")
            context.add_log(f"Follow action was skipped: {reason}")
            
        elif action_taken == "blocked":
            context.add_log("Follow action was blocked by rate limiting")
            
        else:
            context.add_log(f"Follow action failed: {action_taken}")
        
        return ActionState.LOG


class IGFollowAccountAction(BaseAction):
    """
    Instagram FOLLOW_ACCOUNT action
    Strategically follows accounts with safety limits and human behavior
    """
    
    def __init__(self, context: ActionContext):
        super().__init__(context)
    
    def _register_action_handlers(self) -> None:
        """Register FOLLOW_ACCOUNT specific state handlers"""
        handlers = {
            ActionState.NAVIGATE: NavigateToProfileStateHandler(ActionState.NAVIGATE, self),
            ActionState.FIND_TARGET: FindFollowButtonStateHandler(ActionState.FIND_TARGET, self),
            ActionState.ACT: FollowActionStateHandler(ActionState.ACT, self),
            ActionState.VERIFY: VerifyFollowStateHandler(ActionState.VERIFY, self)
        }
        
        self.state_machine.register_handlers(handlers)
    
    async def validate_target(self, target_value: str) -> bool:
        """Validate Instagram username target"""
        if not target_value:
            return False
        
        # Remove @ if present
        username = target_value.lstrip('@')
        
        # Basic Instagram username validation
        if not username:
            return False
        
        if len(username) > 30:  # Instagram username limit
            return False
        
        # Check for valid characters (alphanumeric, dots, underscores)
        if not all(c.isalnum() or c in '._' for c in username):
            return False
        
        # Can't start or end with dots
        if username.startswith('.') or username.endswith('.'):
            return False
        
        # Can't have consecutive dots
        if '..' in username:
            return False
        
        return True
    
    async def execute(self) -> bool:
        """Execute FOLLOW_ACCOUNT with rate limit protection"""
        target_username = self.context.payload.target.value.lstrip('@')
        logger.info(f"Starting FOLLOW_ACCOUNT execution for {target_username}")
        
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
            logger.info(f"FOLLOW_ACCOUNT completed successfully for {target_username}")
            follow_data = self.context.result_data
            
            # Log action details
            action_taken = follow_data.get('action_taken', 'unknown')
            logger.info(f"Follow result: {action_taken}")
            
            # Log rate limit status if available
            if 'rate_limit_triggered' in follow_data:
                logger.warning(f"Rate limit triggered during follow action")
        else:
            logger.error(f"FOLLOW_ACCOUNT failed for {target_username}: {self.context.error_message}")
        
        return success
    
    def get_expected_duration_ms(self) -> int:
        """Get expected duration for this action"""
        return 15000  # 15 seconds expected for follow action
    
    def get_action_metadata(self) -> Dict[str, Any]:
        """Get action-specific metadata"""
        return {
            "action_type": "FOLLOW_ACCOUNT",
            "platform": "instagram",
            "safety_features": ["rate_limiting", "human_behavior", "random_decisions"],
            "max_hourly_rate": 20,
            "requires_navigation": True,
            "risk_level": "medium"
        }
