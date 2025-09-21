"""
FSM (Finite State Machine) Package
Core automation engine for Instagram/Threads actions
"""

from .states import ActionState, StateTransition, StateMetadata, ExecutionPath
from .context import ActionContext, ActionPayload, ActionTarget, Platform, DriverType, DeviceCapabilities
from .state_machine import StateMachine, StateHandler, BaseStateMachineAction

__all__ = [
    # States
    "ActionState",
    "StateTransition", 
    "StateMetadata",
    "ExecutionPath",
    
    # Context
    "ActionContext",
    "ActionPayload",
    "ActionTarget",
    "Platform",
    "DriverType",
    "DeviceCapabilities",
    
    # State Machine
    "StateMachine",
    "StateHandler",
    "BaseStateMachineAction"
]
