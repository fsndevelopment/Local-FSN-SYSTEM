"""
FSM State Definitions for Instagram/Threads Automation
Defines all possible states and transitions for action execution
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class ActionState(Enum):
    """
    Universal states for all Instagram/Threads actions
    Every action follows this state machine pattern
    """
    # Core execution states
    INIT = "init"                    # Initialize context and validate inputs
    OPEN_APP = "open_app"           # Launch Instagram/Threads app
    ENSURE_HOME = "ensure_home"     # Navigate to home screen (recovery point)
    NAVIGATE = "navigate"           # Navigate to target (profile, post, etc.)
    FIND_TARGET = "find_target"     # Locate UI element for action
    ACT = "act"                     # Perform action (like, follow, etc.)
    READ = "read"                   # Read data (for scan_profile, get_stats)
    VERIFY = "verify"               # Confirm action succeeded
    LOG = "log"                     # Record results and telemetry
    DONE = "done"                   # Complete successfully
    
    # Action-specific states
    SCROLL = "scroll"               # Scroll through feed/content
    LIKE = "like"                   # Like a post
    SELECT_STORY = "select_story"   # Select a story to view
    VIEW = "view"                   # View content (story, post, etc.)
    EXIT_STORY = "exit_story"       # Exit story view
    
    # Error handling states
    ERROR = "error"                 # Handle failures
    RECOVER = "recover"             # Attempt recovery
    RETRY = "retry"                 # Retry after recovery
    FAIL = "fail"                   # Terminal failure state


class StateTransition:
    """Defines valid transitions between states"""
    
    # Valid state transitions map
    TRANSITIONS: Dict[ActionState, List[ActionState]] = {
        ActionState.INIT: [
            ActionState.OPEN_APP,
            ActionState.ERROR
        ],
        ActionState.OPEN_APP: [
            ActionState.ENSURE_HOME,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.ENSURE_HOME: [
            ActionState.NAVIGATE,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.NAVIGATE: [
            ActionState.FIND_TARGET,
            ActionState.SCROLL,       # For scroll actions
            ActionState.SELECT_STORY, # For story viewing
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.FIND_TARGET: [
            ActionState.ACT,          # For actions like like, follow
            ActionState.READ,         # For data collection like scan_profile
            ActionState.LIKE,         # For like actions
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.ACT: [
            ActionState.VERIFY,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.READ: [
            ActionState.VERIFY,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.VERIFY: [
            ActionState.LOG,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.SCROLL: [
            ActionState.VERIFY,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.LIKE: [
            ActionState.VERIFY,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.SELECT_STORY: [
            ActionState.VIEW,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.VIEW: [
            ActionState.EXIT_STORY,
            ActionState.VERIFY,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.EXIT_STORY: [
            ActionState.VERIFY,
            ActionState.ERROR,
            ActionState.RECOVER
        ],
        ActionState.LOG: [
            ActionState.DONE,
            ActionState.ERROR
        ],
        ActionState.ERROR: [
            ActionState.RECOVER,
            ActionState.FAIL
        ],
        ActionState.RECOVER: [
            ActionState.ENSURE_HOME,  # Most common recovery path
            ActionState.OPEN_APP,     # App restart recovery
            ActionState.RETRY,        # Retry from last state
            ActionState.FAIL          # Recovery failed
        ],
        ActionState.RETRY: [
            ActionState.NAVIGATE,     # Retry from navigation
            ActionState.FIND_TARGET,  # Retry from target finding
            ActionState.ACT,          # Retry action
            ActionState.READ,         # Retry data reading
            ActionState.ERROR         # Retry failed
        ],
        ActionState.DONE: [],         # Terminal success state
        ActionState.FAIL: []          # Terminal failure state
    }
    
    @classmethod
    def is_valid_transition(cls, from_state: ActionState, to_state: ActionState) -> bool:
        """Check if transition from one state to another is valid"""
        return to_state in cls.TRANSITIONS.get(from_state, [])
    
    @classmethod
    def get_valid_transitions(cls, from_state: ActionState) -> List[ActionState]:
        """Get all valid transitions from a given state"""
        return cls.TRANSITIONS.get(from_state, [])
    
    @classmethod
    def is_terminal_state(cls, state: ActionState) -> bool:
        """Check if state is terminal (no outgoing transitions)"""
        return len(cls.TRANSITIONS.get(state, [])) == 0


class StateMetadata:
    """Metadata and timing information for state execution"""
    
    def __init__(self, state: ActionState):
        self.state = state
        self.entered_at: Optional[datetime] = None
        self.exited_at: Optional[datetime] = None
        self.duration_ms: Optional[int] = None
        self.retry_count: int = 0
        self.error_message: Optional[str] = None
        self.success: bool = False
        
    def enter(self) -> None:
        """Mark state as entered"""
        self.entered_at = datetime.utcnow()
        
    def exit(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark state as exited"""
        self.exited_at = datetime.utcnow()
        self.success = success
        self.error_message = error_message
        
        if self.entered_at and self.exited_at:
            delta = self.exited_at - self.entered_at
            self.duration_ms = int(delta.total_seconds() * 1000)
    
    def increment_retry(self) -> None:
        """Increment retry counter"""
        self.retry_count += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            "state": self.state.value,
            "entered_at": self.entered_at.isoformat() if self.entered_at else None,
            "exited_at": self.exited_at.isoformat() if self.exited_at else None,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "success": self.success,
            "error_message": self.error_message
        }


class ExecutionPath:
    """Tracks the complete execution path through states"""
    
    def __init__(self):
        self.states: List[StateMetadata] = []
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.total_duration_ms: Optional[int] = None
        
    def start(self) -> None:
        """Mark execution start"""
        self.started_at = datetime.utcnow()
        
    def complete(self) -> None:
        """Mark execution complete"""
        self.completed_at = datetime.utcnow()
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.total_duration_ms = int(delta.total_seconds() * 1000)
    
    def add_state(self, state: ActionState) -> StateMetadata:
        """Add a new state to the execution path"""
        metadata = StateMetadata(state)
        self.states.append(metadata)
        return metadata
    
    def get_current_state(self) -> Optional[StateMetadata]:
        """Get the current (last) state"""
        return self.states[-1] if self.states else None
    
    def get_state_path(self) -> List[str]:
        """Get list of state names in execution order"""
        return [state.state.value for state in self.states]
    
    def get_total_retries(self) -> int:
        """Get total retry count across all states"""
        return sum(state.retry_count for state in self.states)
    
    def was_successful(self) -> bool:
        """Check if execution completed successfully"""
        if not self.states:
            return False
        final_state = self.states[-1]
        return final_state.state == ActionState.DONE and final_state.success
    
    def get_failure_point(self) -> Optional[StateMetadata]:
        """Get the state where execution failed"""
        for state in reversed(self.states):
            if not state.success and state.error_message:
                return state
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_ms": self.total_duration_ms,
            "state_path": self.get_state_path(),
            "total_retries": self.get_total_retries(),
            "successful": self.was_successful(),
            "failure_point": self.get_failure_point().to_dict() if self.get_failure_point() else None,
            "states": [state.to_dict() for state in self.states]
        }
