"""
Core FSM State Machine Engine
Generic finite state machine that any Instagram/Threads action can use
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from .states import ActionState, StateTransition, ExecutionPath
from .context import ActionContext
from ..recovery.watchdogs import WatchdogSystem, WatchdogConfig


logger = logging.getLogger(__name__)


class StateHandler:
    """Base class for state handlers"""
    
    def __init__(self, state: ActionState):
        self.state = state
    
    async def execute(self, context: ActionContext) -> ActionState:
        """Execute the state logic and return next state"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    async def can_enter(self, context: ActionContext) -> bool:
        """Check if state can be entered (validation)"""
        return True
    
    async def on_exit(self, context: ActionContext, next_state: ActionState) -> None:
        """Called when exiting this state"""
        pass


class StateMachine:
    """
    Generic FSM engine for Instagram/Threads automation
    Manages state transitions, error handling, and recovery
    """
    
    def __init__(self, context: ActionContext, watchdog_config: WatchdogConfig = None):
        self.context = context
        self.current_state = ActionState.INIT
        self.execution_path = ExecutionPath()
        self.state_handlers: Dict[ActionState, StateHandler] = {}
        
        # Execution control
        self.max_execution_time_seconds = 300  # 5 minutes max
        self.max_total_retries = 10
        self.is_running = False
        self.should_stop = False
        
        # Integrated watchdog system
        self.watchdog_system = WatchdogSystem(watchdog_config)
        self.last_state_change = datetime.utcnow()
    
    def register_handler(self, state: ActionState, handler: StateHandler) -> None:
        """Register a handler for a specific state"""
        self.state_handlers[state] = handler
        logger.debug(f"Registered handler for state {state.value}")
    
    def register_handlers(self, handlers: Dict[ActionState, StateHandler]) -> None:
        """Register multiple handlers at once"""
        for state, handler in handlers.items():
            self.register_handler(state, handler)
    
    async def execute(self) -> bool:
        """
        Execute the state machine until completion or failure
        Returns True if successful, False if failed
        """
        if self.is_running:
            raise RuntimeError("State machine is already running")
        
        self.is_running = True
        self.should_stop = False
        self.execution_path.start()
        self.context.metrics.start()
        
        logger.info(f"Starting FSM execution for {self.context.payload.action_type}")
        
        try:
            # Start watchdog system
            await self.watchdog_system.start_all(self.context)
            
            # Main execution loop
            while not self.should_stop and not StateTransition.is_terminal_state(self.current_state):
                # Check execution timeout
                if self._is_execution_timeout():
                    await self._handle_timeout()
                    break
                
                # Execute current state
                await self._execute_current_state()
                
                # Check if we should stop
                if self.should_stop:
                    break
            
            # Finalize execution
            self.execution_path.complete()
            self.context.metrics.end()
            
            success = self.execution_path.was_successful()
            logger.info(f"FSM execution completed. Success: {success}")
            
            return success
            
        except Exception as e:
            logger.error(f"FSM execution failed with exception: {e}")
            await self._handle_critical_error(str(e))
            return False
        
        finally:
            # Stop watchdog system
            await self.watchdog_system.stop_all()
            self.is_running = False
    
    async def stop(self) -> None:
        """Stop the state machine execution"""
        logger.info("Stopping FSM execution")
        self.should_stop = True
    
    async def _execute_current_state(self) -> None:
        """Execute the current state and handle transition"""
        state_metadata = self.execution_path.add_state(self.current_state)
        state_metadata.enter()
        
        logger.debug(f"Executing state: {self.current_state.value}")
        
        try:
            # Get handler for current state
            handler = self.state_handlers.get(self.current_state)
            if not handler:
                raise RuntimeError(f"No handler registered for state {self.current_state.value}")
            
            # Check if we can enter this state
            if not await handler.can_enter(self.context):
                raise RuntimeError(f"Cannot enter state {self.current_state.value}")
            
            # Execute the state
            next_state = await handler.execute(self.context)
            
            # Validate transition
            if not StateTransition.is_valid_transition(self.current_state, next_state):
                raise RuntimeError(f"Invalid transition from {self.current_state.value} to {next_state.value}")
            
            # Handle state exit
            await handler.on_exit(self.context, next_state)
            
            # Mark state as successful
            state_metadata.exit(success=True)
            
            # Transition to next state
            await self._transition_to_state(next_state)
            
        except Exception as e:
            logger.error(f"Error in state {self.current_state.value}: {e}")
            
            # Mark state as failed
            state_metadata.exit(success=False, error_message=str(e))
            
            # Handle error
            await self._handle_state_error(str(e))
    
    async def _transition_to_state(self, next_state: ActionState) -> None:
        """Transition to the next state"""
        logger.debug(f"Transitioning from {self.current_state.value} to {next_state.value}")
        
        self.current_state = next_state
        self.last_state_change = datetime.utcnow()
        
        # Add context log
        self.context.add_log(f"Transitioned to state: {next_state.value}")
    
    async def _handle_state_error(self, error_message: str) -> None:
        """Handle error in state execution"""
        self.context.set_error(error_message, f"E_STATE_{self.current_state.value.upper()}")
        
        # Check if we can recover
        if self._can_attempt_recovery():
            await self._transition_to_state(ActionState.ERROR)
        else:
            await self._transition_to_state(ActionState.FAIL)
    
    async def _handle_timeout(self) -> None:
        """Handle execution timeout"""
        error_msg = f"Execution timeout after {self.max_execution_time_seconds} seconds"
        logger.error(error_msg)
        self.context.set_error(error_msg, "E_EXECUTION_TIMEOUT")
        await self._transition_to_state(ActionState.FAIL)
    
    async def _handle_deadman_timeout(self) -> None:
        """Handle deadman timer timeout (stuck in one state)"""
        error_msg = f"Deadman timeout: stuck in state {self.current_state.value} for {self.deadman_timer_seconds} seconds"
        logger.error(error_msg)
        self.context.set_error(error_msg, "E_DEADMAN_TIMEOUT")
        await self._transition_to_state(ActionState.FAIL)
    
    async def _handle_critical_error(self, error_message: str) -> None:
        """Handle critical system error"""
        logger.critical(f"Critical FSM error: {error_message}")
        self.context.set_error(error_message, "E_CRITICAL_FSM_ERROR")
        self.execution_path.complete()
        self.context.metrics.end()
    
    def _is_execution_timeout(self) -> bool:
        """Check if execution has timed out"""
        if not self.execution_path.started_at:
            return False
        
        elapsed = (datetime.utcnow() - self.execution_path.started_at).total_seconds()
        return elapsed > self.max_execution_time_seconds
    
    def _is_deadman_timeout(self) -> bool:
        """Check if deadman timer has expired"""
        elapsed = (datetime.utcnow() - self.last_state_change).total_seconds()
        return elapsed > self.deadman_timer_seconds
    
    def _can_attempt_recovery(self) -> bool:
        """Check if recovery can be attempted"""
        total_retries = self.execution_path.get_total_retries()
        return total_retries < self.max_total_retries
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get complete execution summary for logging"""
        return {
            "context": self.context.to_dict(),
            "execution_path": self.execution_path.to_dict(),
            "final_state": self.current_state.value,
            "is_running": self.is_running,
            "should_stop": self.should_stop,
            "watchdog_telemetry": self.watchdog_system.get_telemetry_summary()
        }


class BaseStateMachineAction:
    """
    Base class for all FSM-based actions
    Provides common functionality and state handlers
    """
    
    def __init__(self, context: ActionContext):
        self.context = context
        self.state_machine = StateMachine(context)
        self._register_common_handlers()
    
    def _register_common_handlers(self) -> None:
        """Register common state handlers used by all actions"""
        # These will be overridden by specific actions as needed
        pass
    
    async def execute(self) -> bool:
        """Execute the action using the state machine"""
        return await self.state_machine.execute()
    
    async def stop(self) -> None:
        """Stop the action execution"""
        await self.state_machine.stop()
    
    def get_result(self) -> Dict[str, Any]:
        """Get the execution result"""
        return self.state_machine.get_execution_summary()
