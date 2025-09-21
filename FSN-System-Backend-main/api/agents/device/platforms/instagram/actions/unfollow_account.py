"""
Instagram UNFOLLOW_ACCOUNT Action - Strategic unfollowing with safety and human behavior
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
    """Navigate to the target profile to unfollow"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        target_username = context.payload.target.value.lstrip('@')
        use_following_list = context.payload.parameters.get('use_following_list', False)
        
        context.add_log(f"Navigating to profile: {target_username}")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            if use_following_list:
                # Navigate via following list (more efficient for mass unfollowing)
                context.add_log("Using following list navigation method")
                await self._navigate_via_following_list(context, selector_registry, target_username)
            else:
                # Navigate via search (more reliable for specific accounts)
                context.add_log("Using search navigation method")
                await self._navigate_via_search(context, selector_registry, target_username)
            
            return ActionState.FIND_TARGET
            
        except Exception as e:
            context.add_log(f"Navigation failed: {e}")
            raise
    
    async def _navigate_via_search(self, context: ActionContext, selector_registry, target_username: str):
        """Navigate to profile via search"""
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
        context.add_log("Looking for profile in search results")
        search_results = await selector_registry.find_search_results(timeout=5)
        if search_results and len(search_results) > 0:
            context.add_log("Clicking on first search result")
            await context.driver.click_element(search_results[0].element)
            await asyncio.sleep(random.uniform(2.0, 3.0))
        else:
            raise RuntimeError(f"No search results found for {target_username}")
    
    async def _navigate_via_following_list(self, context: ActionContext, selector_registry, target_username: str):
        """Navigate to profile via following list (for mass unfollowing)"""
        # This would require implementing following list navigation
        # For now, fall back to search method
        context.add_log("Following list navigation not yet implemented, using search")
        await self._navigate_via_search(context, selector_registry, target_username)


class FindUnfollowButtonStateHandler(BaseActionStateHandler):
    """Find the unfollow (Following) button on the profile"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Looking for Following button to unfollow")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Look for Following button (indicates we're following this account)
            following_result = await selector_registry.find_following_button(timeout=8)
            if not following_result:
                # Check if we're not following this account
                follow_result = await selector_registry.find_follow_button(timeout=3)
                if follow_result:
                    context.add_log("Not following this account - nothing to unfollow")
                    context.result_data = {
                        "action_taken": "not_following",
                        "reason": "account_not_followed"
                    }
                    return ActionState.VERIFY
                else:
                    raise RuntimeError("Could not find Following button or Follow button")
            
            # Store following button for action
            context.store_data("following_button", following_result)
            context.add_log(f"Found Following button using strategy: {following_result.strategy_used.type}")
            
            return ActionState.ACT
            
        except Exception as e:
            context.add_log(f"Failed to find Following button: {e}")
            raise


class UnfollowActionStateHandler(BaseActionStateHandler):
    """Perform the unfollow action with human timing and safety checks"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        unfollow_probability = context.payload.parameters.get('unfollow_probability', 0.8)
        
        context.add_log(f"Starting unfollow action with {unfollow_probability*100}% probability")
        
        # Initialize rate limit detector
        rate_limit_detector = InstagramRateLimitDetector(context.driver)
        
        # Check current rate limit status
        if not rate_limit_detector.track_action("follows"):  # Unfollows count towards follow limits
            context.add_log("Rate limit reached for follows/unfollows, skipping action")
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
            if random.random() > unfollow_probability:
                context.add_log("Randomly decided not to unfollow this account (human behavior)")
                context.result_data = {
                    "action_taken": "skipped",
                    "reason": "random_human_decision",
                    "unfollow_probability": unfollow_probability
                }
                return ActionState.VERIFY
            
            # Get following button
            following_result = context.get_data("following_button")
            if not following_result:
                raise RuntimeError("Following button not available")
            
            # Human-like delay before action
            delay = random.uniform(1.5, 4.0)  # Slightly longer than follow delay
            context.add_log(f"Human delay before unfollow: {delay:.2f}s")
            await asyncio.sleep(delay)
            
            # Perform the unfollow action (click Following button)
            context.add_log("Tapping Following button...")
            await context.driver.click_element(following_result.element)
            
            # Wait for unfollow confirmation popup
            popup_delay = random.uniform(0.5, 1.0)
            await asyncio.sleep(popup_delay)
            
            # Handle unfollow confirmation popup
            context.add_log("Looking for unfollow confirmation popup...")
            confirmation_handled = await self._handle_unfollow_confirmation(context)
            
            if not confirmation_handled:
                context.add_log("Warning: Unfollow confirmation popup not found - action may not have completed")
            
            # Wait for unfollow to register
            verification_delay = random.uniform(0.8, 1.5)
            await asyncio.sleep(verification_delay)
            
            context.add_log("Unfollow action completed")
            
            # Post-action rate limit check
            post_action_rate_limit = await rate_limit_detector.check_for_rate_limits()
            if post_action_rate_limit:
                context.add_log(f"Rate limit triggered by unfollow action: {post_action_rate_limit.message}")
                action_plan = await rate_limit_detector.handle_rate_limit(post_action_rate_limit)
                
                # Store action details with rate limit info
                context.result_data = {
                    "action_taken": "unfollowed_but_rate_limited",
                    "selector_used": following_result.strategy_used.type,
                    "execution_time_ms": following_result.execution_time_ms,
                    "human_delay": delay,
                    "popup_handled": confirmation_handled,
                    "rate_limit_triggered": True,
                    "rate_limit_event": post_action_rate_limit,
                    "action_plan": action_plan
                }
            else:
                # Store action details
                context.result_data = {
                    "action_taken": "unfollowed",
                    "selector_used": following_result.strategy_used.type,
                    "execution_time_ms": following_result.execution_time_ms,
                    "human_delay": delay,
                    "popup_handled": confirmation_handled,
                    "rate_limit_safe": True
                }
            
            return ActionState.VERIFY
            
        except Exception as e:
            context.add_log(f"Unfollow action failed: {e}")
            context.result_data = {
                "action_taken": "failed",
                "error": str(e)
            }
            raise
    
    async def _handle_unfollow_confirmation(self, context: ActionContext) -> bool:
        """Handle the unfollow confirmation popup"""
        try:
            selector_registry = context.get_data("selector_registry")
            if not selector_registry:
                return False
            
            # Look for common unfollow confirmation text/buttons
            unfollow_confirmations = [
                "Unfollow",
                "Stop following",
                "Yes, unfollow"
            ]
            
            for confirmation_text in unfollow_confirmations:
                try:
                    # Try to find confirmation button
                    confirmation_button = await context.driver.find_element(
                        "xpath", 
                        f"//XCUIElementTypeButton[contains(@name, '{confirmation_text}')]",
                        timeout=3
                    )
                    
                    if confirmation_button:
                        context.add_log(f"Found confirmation button: {confirmation_text}")
                        await context.driver.click_element(confirmation_button)
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                        return True
                        
                except Exception:
                    continue
            
            context.add_log("No unfollow confirmation popup found")
            return False
            
        except Exception as e:
            context.add_log(f"Error handling unfollow confirmation: {e}")
            return False


class VerifyUnfollowStateHandler(BaseActionStateHandler):
    """Verify unfollow action was successful"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Verifying unfollow action")
        
        result_data = context.result_data
        if not result_data:
            context.add_log("No result data available for verification")
            return ActionState.LOG
        
        action_taken = result_data.get("action_taken")
        
        if action_taken in ["unfollowed", "unfollowed_but_rate_limited"]:
            context.add_log("Unfollow action verification successful")
            
            # Optional: Check if button changed back to "Follow"
            try:
                selector_registry = context.get_data("selector_registry")
                if selector_registry:
                    follow_result = await selector_registry.find_follow_button(timeout=3)
                    if follow_result:
                        context.add_log("Verified: Following button changed to Follow")
                        result_data["verification"] = "button_changed_to_follow"
                    else:
                        context.add_log("Could not verify button state change")
                        result_data["verification"] = "button_state_unclear"
            except Exception as e:
                context.add_log(f"Verification check failed: {e}")
                result_data["verification"] = f"verification_error: {e}"
                
        elif action_taken == "not_following":
            context.add_log("Account was not being followed")
            
        elif action_taken == "skipped":
            reason = result_data.get("reason", "unknown")
            context.add_log(f"Unfollow action was skipped: {reason}")
            
        elif action_taken == "blocked":
            context.add_log("Unfollow action was blocked by rate limiting")
            
        else:
            context.add_log(f"Unfollow action failed: {action_taken}")
        
        return ActionState.LOG


class IGUnfollowAccountAction(BaseAction):
    """
    Instagram UNFOLLOW_ACCOUNT action
    Strategically unfollows accounts with safety limits and human behavior
    """
    
    def __init__(self, context: ActionContext):
        super().__init__(context)
    
    def _register_action_handlers(self) -> None:
        """Register UNFOLLOW_ACCOUNT specific state handlers"""
        handlers = {
            ActionState.NAVIGATE: NavigateToProfileStateHandler(ActionState.NAVIGATE, self),
            ActionState.FIND_TARGET: FindUnfollowButtonStateHandler(ActionState.FIND_TARGET, self),
            ActionState.ACT: UnfollowActionStateHandler(ActionState.ACT, self),
            ActionState.VERIFY: VerifyUnfollowStateHandler(ActionState.VERIFY, self)
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
        """Execute UNFOLLOW_ACCOUNT with rate limit protection"""
        target_username = self.context.payload.target.value.lstrip('@')
        logger.info(f"Starting UNFOLLOW_ACCOUNT execution for {target_username}")
        
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
            logger.info(f"UNFOLLOW_ACCOUNT completed successfully for {target_username}")
            unfollow_data = self.context.result_data
            
            # Log action details
            action_taken = unfollow_data.get('action_taken', 'unknown')
            logger.info(f"Unfollow result: {action_taken}")
            
            # Log rate limit status if available
            if 'rate_limit_triggered' in unfollow_data:
                logger.warning(f"Rate limit triggered during unfollow action")
        else:
            logger.error(f"UNFOLLOW_ACCOUNT failed for {target_username}: {self.context.error_message}")
        
        return success
    
    def get_expected_duration_ms(self) -> int:
        """Get expected duration for this action"""
        return 18000  # 18 seconds expected for unfollow action (slightly longer due to confirmation)
    
    def get_action_metadata(self) -> Dict[str, Any]:
        """Get action-specific metadata"""
        return {
            "action_type": "UNFOLLOW_ACCOUNT",
            "platform": "instagram",
            "safety_features": ["rate_limiting", "human_behavior", "random_decisions", "confirmation_handling"],
            "max_hourly_rate": 20,  # Same limit as follows
            "requires_navigation": True,
            "risk_level": "medium-high"  # Unfollowing can be more suspicious
        }
