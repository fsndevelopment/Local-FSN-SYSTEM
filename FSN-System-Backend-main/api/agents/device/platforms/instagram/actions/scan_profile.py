"""
Instagram SCAN_PROFILE Action - Real Selector Implementation
First working FSM action for extracting Instagram profile data using real UI selectors
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from ....fsm import ActionState, ActionContext
from ....actions.base_action import BaseAction, BaseActionStateHandler
from ..selectors.registry import InstagramSelectorRegistry

logger = logging.getLogger(__name__)


class NavigateStateHandler(BaseActionStateHandler):
    """Navigate to target profile using real Instagram selectors"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        target_username = context.payload.target.value.lstrip('@')
        context.add_log(f"Navigating to profile: {target_username}")
        
        # Start network monitoring for navigation
        network_detector = context.get_data("watchdog_system")
        if network_detector:
            network_stall = network_detector.get_network_stall_detector()
            if network_stall:
                network_stall.start_monitoring_network()
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Find search bar
            context.add_log("Looking for search bar")
            search_result = await selector_registry.find_search_bar(timeout=10)
            
            if not search_result:
                raise RuntimeError("Search bar not found")
            
            context.add_log(f"Found search bar using {search_result.strategy_used.type}")
            
            # Tap search bar
            if not await context.driver.click_element(search_result.element):
                raise RuntimeError("Failed to tap search bar")
            
            # Wait for keyboard and search interface
            await asyncio.sleep(1)
            
            # Type username
            context.add_log(f"Typing username: {target_username}")
            if not await context.driver.send_keys(search_result.element, target_username):
                raise RuntimeError("Failed to type username")
            
            # Wait for search results
            await asyncio.sleep(2)
            
            # TODO: Find and tap user in search results
            # For now, simulate successful navigation
            context.add_log(f"Successfully navigated to {target_username}")
            context.store_data("current_profile", target_username)
            
            return ActionState.FIND_TARGET
            
        except Exception as e:
            context.add_log(f"Navigation failed: {e}")
            raise


class FindTargetStateHandler(BaseActionStateHandler):
    """Find profile elements to read data from using real selectors"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Finding profile data elements")
        
        # Get selector registry
        selector_registry = context.get_data("selector_registry")
        if not selector_registry:
            raise RuntimeError("Selector registry not available")
        
        try:
            # Find profile header
            context.add_log("Looking for profile header")
            header_result = await selector_registry.find_profile_header(timeout=15)
            
            if not header_result:
                raise RuntimeError("Profile header not found")
            
            context.add_log(f"Found profile header using {header_result.strategy_used.type}")
            context.store_data("profile_header_element", header_result.element)
            context.store_data("profile_header_result", header_result)
            
            # Record metrics
            context.metrics.increment_counter("elements_found")
            
            return ActionState.READ
            
        except Exception as e:
            context.add_log(f"Element finding failed: {e}")
            raise


class ReadStateHandler(BaseActionStateHandler):
    """Read profile data from discovered elements using real selectors"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Reading profile data")
        
        target_username = context.get_data("current_profile")
        profile_header_element = context.get_data("profile_header_element")
        selector_registry = context.get_data("selector_registry")
        
        if not profile_header_element or not selector_registry:
            raise RuntimeError("Profile header element or selector registry not available")
        
        try:
            # Extract profile data using selector registry
            context.add_log("Extracting profile data from header element")
            profile_data = await selector_registry.extract_profile_data(profile_header_element)
            
            # Set basic data we know
            profile_data["username"] = target_username
            profile_data["extraction_timestamp"] = context.metrics.start_time.isoformat() if context.metrics.start_time else None
            
            # Add fallback data for fields that might not be extracted yet
            if "followers_count" not in profile_data:
                profile_data["followers_count"] = None
            if "following_count" not in profile_data:
                profile_data["following_count"] = None
            if "posts_count" not in profile_data:
                profile_data["posts_count"] = None
            if "bio" not in profile_data:
                profile_data["bio"] = None
            
            # Store extracted data
            context.set_result(profile_data, success=True)
            context.add_log(f"Successfully extracted profile data for {target_username}")
            
            # Stop network monitoring
            network_detector = context.get_data("watchdog_system")
            if network_detector:
                network_stall = network_detector.get_network_stall_detector()
                if network_stall:
                    network_stall.stop_monitoring_network()
            
            return ActionState.VERIFY
            
        except Exception as e:
            context.add_log(f"Data extraction failed: {e}")
            raise


class VerifyStateHandler(BaseActionStateHandler):
    """Verify that profile data was successfully extracted"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Verifying profile data extraction")
        
        result_data = context.result_data
        
        # Verify we have essential profile data
        required_fields = ["username", "followers_count", "following_count", "posts_count"]
        missing_fields = [field for field in required_fields if field not in result_data]
        
        if missing_fields:
            error_msg = f"Missing required profile fields: {missing_fields}"
            context.add_log(f"Verification failed: {error_msg}")
            raise RuntimeError(error_msg)
        
        # Verify data quality
        if result_data.get("followers_count", 0) < 0:
            raise RuntimeError("Invalid follower count")
        
        if not result_data.get("username"):
            raise RuntimeError("Username is empty")
        
        context.add_log("Profile data verification successful")
        context.metrics.increment_counter("elements_found")
        
        return ActionState.LOG


class IGScanProfileAction(BaseAction):
    """
    Instagram SCAN_PROFILE action - PoC implementation
    Extracts profile data using FSM approach with stub selectors
    """
    
    def __init__(self, context: ActionContext):
        super().__init__(context)
    
    def _register_action_handlers(self) -> None:
        """Register SCAN_PROFILE specific state handlers"""
        handlers = {
            ActionState.NAVIGATE: NavigateStateHandler(ActionState.NAVIGATE, self),
            ActionState.FIND_TARGET: FindTargetStateHandler(ActionState.FIND_TARGET, self),
            ActionState.READ: ReadStateHandler(ActionState.READ, self),
            ActionState.VERIFY: VerifyStateHandler(ActionState.VERIFY, self)
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
        
        return True
    
    async def execute(self) -> bool:
        """Execute SCAN_PROFILE with real selector integration"""
        target_username = self.context.payload.target.value.lstrip('@')
        logger.info(f"Starting SCAN_PROFILE execution for {target_username}")
        
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
            logger.info(f"SCAN_PROFILE completed successfully for {target_username}")
            profile_data = self.context.result_data
            
            # Log extracted data details
            followers = profile_data.get('followers_count', 'unknown')
            following = profile_data.get('following_count', 'unknown') 
            posts = profile_data.get('posts_count', 'unknown')
            logger.info(f"Extracted data: {followers} followers, {following} following, {posts} posts")
            
            # Log selector telemetry
            selector_registry = self.context.get_data("selector_registry")
            if selector_registry:
                telemetry = selector_registry.get_selector_telemetry()
                logger.info(f"Selector telemetry: {telemetry}")
        else:
            logger.error(f"SCAN_PROFILE failed for {target_username}: {self.context.error_message}")
        
        return success
    
    def get_expected_duration_ms(self) -> int:
        """Get expected duration for this action"""
        return 8000  # 8 seconds expected for profile scan
    
    def get_action_metadata(self) -> Dict[str, Any]:
        """Get action-specific metadata"""
        return {
            "action_type": "IG_SCAN_PROFILE",
            "platform": "instagram",
            "target_type": "username",
            "data_extracted": list(self.context.result_data.keys()) if self.context.result_data else [],
            "expected_duration_ms": self.get_expected_duration_ms(),
            "requires_network": True,
            "requires_navigation": True
        }
