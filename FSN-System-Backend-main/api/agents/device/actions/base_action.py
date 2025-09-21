"""
Base Action Class for FSM-based Instagram/Threads Actions
Provides common functionality and state handlers for all automation actions
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from ..fsm import (
    BaseStateMachineAction, ActionState, StateHandler, 
    ActionContext, Platform
)

logger = logging.getLogger(__name__)


class BaseActionStateHandler(StateHandler):
    """Base state handler with common functionality"""
    
    def __init__(self, state: ActionState, action: 'BaseAction'):
        super().__init__(state)
        self.action = action
    
    async def execute(self, context: ActionContext) -> ActionState:
        """Execute state with error handling"""
        try:
            return await self._execute_state(context)
        except Exception as e:
            logger.error(f"Error in {self.state.value}: {e}")
            context.metrics.increment_counter("errors_encountered")
            return ActionState.ERROR
    
    @abstractmethod
    async def _execute_state(self, context: ActionContext) -> ActionState:
        """Implement specific state logic"""
        pass


class InitStateHandler(BaseActionStateHandler):
    """Initialize action context and validate inputs"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log(f"Initializing {context.payload.action_type}")
        
        # Validate required data
        if not context.device or not context.account:
            raise ValueError("Device and account are required")
        
        if not context.payload.target:
            raise ValueError("Action target is required")
        
        # Set up execution ID
        context.add_log(f"Execution ID: {context.execution_id}")
        context.add_log(f"Device: {context.device.name} ({context.device.udid})")
        context.add_log(f"Account: {context.account.username}")
        context.add_log(f"Platform: {context.platform.value}")
        context.add_log(f"Target: {context.payload.target.type} = {context.payload.target.value}")
        
        return ActionState.OPEN_APP


class OpenAppStateHandler(BaseActionStateHandler):
    """Launch Instagram or Threads app"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        app_name = "Instagram" if context.platform == Platform.INSTAGRAM else "Threads"
        context.add_log(f"Opening {app_name} app")
        
        if not context.driver:
            raise RuntimeError("Driver not initialized")
        
        # Use driver to open app
        success = await context.driver.open_app(context.platform)
        if not success:
            raise RuntimeError(f"Failed to open {app_name} app")
        
        context.add_log(f"{app_name} app opened successfully")
        return ActionState.ENSURE_HOME


class EnsureHomeStateHandler(BaseActionStateHandler):
    """Navigate to home screen (recovery point)"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Ensuring home screen")
        
        # Use recovery helper to get to home
        from ..recovery.helpers import ensure_home
        success = await ensure_home(context.driver, context.platform)
        
        if not success:
            raise RuntimeError("Failed to reach home screen")
        
        context.add_log("Successfully reached home screen")
        return ActionState.NAVIGATE


class ErrorStateHandler(BaseActionStateHandler):
    """Handle errors and determine recovery strategy"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Handling error state")
        context.metrics.increment_counter("errors_encountered")
        
        # Get the last error
        error_msg = context.error_message or "Unknown error"
        error_code = context.error_code or "E_UNKNOWN"
        
        context.add_log(f"Error: {error_code} - {error_msg}")
        
        # Determine recovery strategy based on error type
        if error_code.startswith("E_TIMEOUT"):
            return ActionState.RECOVER
        elif error_code.startswith("E_NAV"):
            return ActionState.RECOVER  
        elif error_code.startswith("E_SESSION"):
            return ActionState.RECOVER
        elif error_code.startswith("E_CRITICAL"):
            return ActionState.FAIL
        else:
            return ActionState.RECOVER


class RecoverStateHandler(BaseActionStateHandler):
    """Attempt recovery from errors"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Attempting recovery")
        context.metrics.increment_counter("recoveries_attempted")
        
        error_code = context.error_code or "E_UNKNOWN"
        
        # Recovery strategy based on error type
        if error_code.startswith("E_TIMEOUT_ANCHOR"):
            # Element not found - try recovery then retry
            from ..recovery.helpers import close_modals, hide_keyboard
            await close_modals(context.driver)
            await hide_keyboard(context.driver)
            return ActionState.RETRY
            
        elif error_code.startswith("E_NAV_LOOP"):
            # Navigation loop - reset to home
            return ActionState.ENSURE_HOME
            
        elif error_code.startswith("E_SESSION_DROP"):
            # Session dropped - restart app
            return ActionState.OPEN_APP
            
        else:
            # Generic recovery - try to get home
            return ActionState.ENSURE_HOME


class LogStateHandler(BaseActionStateHandler):
    """Log results and telemetry"""
    
    async def _execute_state(self, context: ActionContext) -> ActionState:
        context.add_log("Logging execution results")
        
        # Log final metrics
        context.add_log(f"Total duration: {context.metrics.duration_ms}ms")
        context.add_log(f"UI interactions: {context.metrics.ui_interactions}")
        context.add_log(f"Screenshots taken: {context.metrics.screenshots_taken}")
        context.add_log(f"Errors encountered: {context.metrics.errors_encountered}")
        context.add_log(f"Recoveries attempted: {context.metrics.recoveries_attempted}")
        
        # Success or failure
        if context.success:
            context.add_log("Action completed successfully")
        else:
            context.add_log(f"Action failed: {context.error_message}")
        
        return ActionState.DONE


class BaseAction(BaseStateMachineAction, ABC):
    """
    Base class for all Instagram/Threads actions
    Provides common FSM setup and state handlers
    """
    
    def __init__(self, context: ActionContext):
        super().__init__(context)
        self.platform = context.platform
        self.action_type = context.payload.action_type
        
        # Register common state handlers
        self._register_common_handlers()
        
        # Register action-specific handlers (implemented by subclasses)
        self._register_action_handlers()
    
    def _register_common_handlers(self) -> None:
        """Register common state handlers used by all actions"""
        handlers = {
            ActionState.INIT: InitStateHandler(ActionState.INIT, self),
            ActionState.OPEN_APP: OpenAppStateHandler(ActionState.OPEN_APP, self),
            ActionState.ENSURE_HOME: EnsureHomeStateHandler(ActionState.ENSURE_HOME, self),
            ActionState.ERROR: ErrorStateHandler(ActionState.ERROR, self),
            ActionState.RECOVER: RecoverStateHandler(ActionState.RECOVER, self),
            ActionState.LOG: LogStateHandler(ActionState.LOG, self)
        }
        
        self.state_machine.register_handlers(handlers)
    
    @abstractmethod
    def _register_action_handlers(self) -> None:
        """Register action-specific state handlers (implemented by subclasses)"""
        pass
    
    @abstractmethod
    async def validate_target(self, target_value: str) -> bool:
        """Validate the action target (implemented by subclasses)"""
        pass
    
    async def execute(self) -> bool:
        """Execute the action with pre/post processing"""
        logger.info(f"Starting {self.action_type} execution")
        
        try:
            # Pre-execution validation
            if not await self.validate_target(self.context.payload.target.value):
                self.context.set_error("Invalid target", "E_INVALID_TARGET")
                return False
            
            # Execute the FSM
            success = await super().execute()
            
            # Post-execution cleanup
            await self._cleanup()
            
            return success
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            self.context.set_error(str(e), "E_ACTION_EXECUTION")
            return False
    
    async def _cleanup(self) -> None:
        """Cleanup after action execution"""
        # Take final screenshot if action failed
        if not self.context.success and self.context.driver:
            try:
                screenshot_path = f"/tmp/{self.context.execution_id}_final.png"
                await self.context.driver.take_screenshot(screenshot_path)
                self.context.add_screenshot(screenshot_path)
            except Exception as e:
                logger.warning(f"Failed to take final screenshot: {e}")
    
    def get_action_result(self) -> Dict[str, Any]:
        """Get action-specific result data"""
        base_result = self.get_result()
        
        # Add action-specific data
        base_result.update({
            "action_type": self.action_type,
            "platform": self.platform.value,
            "target": {
                "type": self.context.payload.target.type,
                "value": self.context.payload.target.value
            },
            "result_data": self.context.result_data
        })
        
        return base_result
