"""
Error Taxonomy and Recovery Policies
Defines error codes, classifications, and appropriate recovery strategies
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """High-level error categories"""
    TIMEOUT = "timeout"
    NAVIGATION = "navigation"
    SESSION = "session"
    PROXY = "proxy"
    CHECKPOINT = "checkpoint"
    ELEMENT = "element"
    NETWORK = "network"
    CRITICAL = "critical"


class ErrorCode(Enum):
    """Specific error codes with recovery policies"""
    
    # Timeout errors
    E_TIMEOUT_ANCHOR = "E_TIMEOUT_ANCHOR"                 # Element not found within timeout
    E_TIMEOUT_LOAD = "E_TIMEOUT_LOAD"                     # Page/screen load timeout
    E_TIMEOUT_NETWORK = "E_TIMEOUT_NETWORK"               # Network request timeout
    E_DEADMAN_TIMEOUT = "E_DEADMAN_TIMEOUT"               # FSM stuck in one state
    
    # Navigation errors
    E_NAV_LOOP = "E_NAV_LOOP"                             # Stuck in navigation loop
    E_NAV_LOST = "E_NAV_LOST"                             # Lost in app, can't find way home
    E_NAV_BLOCKED = "E_NAV_BLOCKED"                       # Navigation blocked by modal/popup
    E_NAV_UNEXPECTED = "E_NAV_UNEXPECTED"                 # Ended up on unexpected screen
    
    # Session errors
    E_SESSION_DROP = "E_SESSION_DROP"                     # WDA session disconnected
    E_SESSION_INVALID = "E_SESSION_INVALID"               # Session in invalid state
    E_APP_CRASH = "E_APP_CRASH"                           # Instagram/Threads crashed
    E_DEVICE_DISCONNECT = "E_DEVICE_DISCONNECT"           # Device disconnected
    
    # Proxy/Network errors
    E_PROXY_BLOCK = "E_PROXY_BLOCK"                       # Proxy blocked by Instagram
    E_NETWORK_UNREACHABLE = "E_NETWORK_UNREACHABLE"       # Network completely down
    E_RATE_LIMITED = "E_RATE_LIMITED"                     # Rate limited by Instagram
    
    # Instagram checkpoint/security errors
    E_CHECKPOINT = "E_CHECKPOINT"                         # Instagram security checkpoint
    E_LOGIN_REQUIRED = "E_LOGIN_REQUIRED"                 # Account logged out
    E_ACCOUNT_SUSPENDED = "E_ACCOUNT_SUSPENDED"           # Account banned/suspended
    E_ACTION_BLOCKED = "E_ACTION_BLOCKED"                 # Action temporarily blocked
    
    # Element/UI errors
    E_ELEMENT_NOT_FOUND = "E_ELEMENT_NOT_FOUND"           # Required UI element missing
    E_ELEMENT_NOT_CLICKABLE = "E_ELEMENT_NOT_CLICKABLE"   # Element exists but not clickable
    E_CLICK_NO_EFFECT = "E_CLICK_NO_EFFECT"               # Click didn't produce expected result
    E_UI_CHANGED = "E_UI_CHANGED"                         # Instagram UI updated, selectors invalid
    
    # Critical system errors
    E_CRITICAL_FSM_ERROR = "E_CRITICAL_FSM_ERROR"         # FSM engine failure
    E_DRIVER_ERROR = "E_DRIVER_ERROR"                     # Driver malfunction
    E_SYSTEM_ERROR = "E_SYSTEM_ERROR"                     # System-level error
    E_UNKNOWN = "E_UNKNOWN"                               # Unclassified error


class RecoveryAction(Enum):
    """Available recovery actions"""
    RETRY = "retry"                                       # Retry the same operation
    RETRY_WITH_RECOVERY = "retry_with_recovery"           # Close modals, then retry
    RESET_TO_HOME = "reset_to_home"                       # Navigate back to home screen
    RESTART_SESSION = "restart_session"                   # Restart WDA session
    RESTART_APP = "restart_app"                           # Restart Instagram/Threads
    SWITCH_PROXY = "switch_proxy"                         # Change proxy profile
    PAUSE_ACCOUNT = "pause_account"                       # Temporarily pause account
    ESCALATE = "escalate"                                 # Manual intervention required
    FAIL = "fail"                                         # Terminal failure, no recovery


@dataclass
class RecoveryPolicy:
    """Recovery policy for a specific error"""
    error_code: ErrorCode
    category: ErrorCategory
    primary_action: RecoveryAction
    fallback_actions: List[RecoveryAction]
    max_retries: int
    cooldown_seconds: int
    description: str
    
    def get_next_action(self, attempt_count: int) -> Optional[RecoveryAction]:
        """Get the next recovery action based on attempt count"""
        if attempt_count == 0:
            return self.primary_action
        elif attempt_count <= len(self.fallback_actions):
            return self.fallback_actions[attempt_count - 1]
        else:
            return RecoveryAction.FAIL


class ErrorTaxonomy:
    """Central registry of error codes and recovery policies"""
    
    # Recovery policies for each error code
    POLICIES: Dict[ErrorCode, RecoveryPolicy] = {
        
        # Timeout errors
        ErrorCode.E_TIMEOUT_ANCHOR: RecoveryPolicy(
            error_code=ErrorCode.E_TIMEOUT_ANCHOR,
            category=ErrorCategory.TIMEOUT,
            primary_action=RecoveryAction.RETRY_WITH_RECOVERY,
            fallback_actions=[RecoveryAction.RESET_TO_HOME, RecoveryAction.RESTART_APP],
            max_retries=3,
            cooldown_seconds=5,
            description="Element not found within timeout - try recovery then retry"
        ),
        
        ErrorCode.E_TIMEOUT_LOAD: RecoveryPolicy(
            error_code=ErrorCode.E_TIMEOUT_LOAD,
            category=ErrorCategory.TIMEOUT,
            primary_action=RecoveryAction.RETRY,
            fallback_actions=[RecoveryAction.RESTART_APP, RecoveryAction.RESTART_SESSION],
            max_retries=2,
            cooldown_seconds=10,
            description="Page load timeout - retry or restart"
        ),
        
        ErrorCode.E_DEADMAN_TIMEOUT: RecoveryPolicy(
            error_code=ErrorCode.E_DEADMAN_TIMEOUT,
            category=ErrorCategory.TIMEOUT,
            primary_action=RecoveryAction.FAIL,
            fallback_actions=[],
            max_retries=0,
            cooldown_seconds=0,
            description="FSM deadman timer expired - critical failure"
        ),
        
        # Navigation errors
        ErrorCode.E_NAV_LOOP: RecoveryPolicy(
            error_code=ErrorCode.E_NAV_LOOP,
            category=ErrorCategory.NAVIGATION,
            primary_action=RecoveryAction.RESET_TO_HOME,
            fallback_actions=[RecoveryAction.RESTART_APP],
            max_retries=2,
            cooldown_seconds=5,
            description="Navigation loop detected - reset to home"
        ),
        
        ErrorCode.E_NAV_LOST: RecoveryPolicy(
            error_code=ErrorCode.E_NAV_LOST,
            category=ErrorCategory.NAVIGATION,
            primary_action=RecoveryAction.RESET_TO_HOME,
            fallback_actions=[RecoveryAction.RESTART_APP],
            max_retries=2,
            cooldown_seconds=3,
            description="Lost in app navigation - return to home"
        ),
        
        ErrorCode.E_NAV_BLOCKED: RecoveryPolicy(
            error_code=ErrorCode.E_NAV_BLOCKED,
            category=ErrorCategory.NAVIGATION,
            primary_action=RecoveryAction.RETRY_WITH_RECOVERY,
            fallback_actions=[RecoveryAction.RESET_TO_HOME],
            max_retries=3,
            cooldown_seconds=2,
            description="Navigation blocked by modal - close and retry"
        ),
        
        # Session errors
        ErrorCode.E_SESSION_DROP: RecoveryPolicy(
            error_code=ErrorCode.E_SESSION_DROP,
            category=ErrorCategory.SESSION,
            primary_action=RecoveryAction.RESTART_SESSION,
            fallback_actions=[RecoveryAction.RESTART_APP],
            max_retries=2,
            cooldown_seconds=10,
            description="WDA session dropped - restart session"
        ),
        
        ErrorCode.E_APP_CRASH: RecoveryPolicy(
            error_code=ErrorCode.E_APP_CRASH,
            category=ErrorCategory.SESSION,
            primary_action=RecoveryAction.RESTART_APP,
            fallback_actions=[RecoveryAction.RESTART_SESSION],
            max_retries=2,
            cooldown_seconds=15,
            description="Instagram/Threads crashed - restart app"
        ),
        
        # Proxy/Network errors
        ErrorCode.E_PROXY_BLOCK: RecoveryPolicy(
            error_code=ErrorCode.E_PROXY_BLOCK,
            category=ErrorCategory.PROXY,
            primary_action=RecoveryAction.SWITCH_PROXY,
            fallback_actions=[RecoveryAction.PAUSE_ACCOUNT],
            max_retries=3,
            cooldown_seconds=30,
            description="Proxy blocked - switch proxy or pause account"
        ),
        
        ErrorCode.E_RATE_LIMITED: RecoveryPolicy(
            error_code=ErrorCode.E_RATE_LIMITED,
            category=ErrorCategory.NETWORK,
            primary_action=RecoveryAction.PAUSE_ACCOUNT,
            fallback_actions=[RecoveryAction.SWITCH_PROXY],
            max_retries=1,
            cooldown_seconds=300,  # 5 minutes
            description="Rate limited - pause account"
        ),
        
        # Instagram checkpoint/security errors
        ErrorCode.E_CHECKPOINT: RecoveryPolicy(
            error_code=ErrorCode.E_CHECKPOINT,
            category=ErrorCategory.CHECKPOINT,
            primary_action=RecoveryAction.PAUSE_ACCOUNT,
            fallback_actions=[RecoveryAction.ESCALATE],
            max_retries=0,
            cooldown_seconds=3600,  # 1 hour
            description="Instagram checkpoint - pause account for manual review"
        ),
        
        ErrorCode.E_ACCOUNT_SUSPENDED: RecoveryPolicy(
            error_code=ErrorCode.E_ACCOUNT_SUSPENDED,
            category=ErrorCategory.CHECKPOINT,
            primary_action=RecoveryAction.ESCALATE,
            fallback_actions=[],
            max_retries=0,
            cooldown_seconds=0,
            description="Account suspended - manual intervention required"
        ),
        
        ErrorCode.E_ACTION_BLOCKED: RecoveryPolicy(
            error_code=ErrorCode.E_ACTION_BLOCKED,
            category=ErrorCategory.CHECKPOINT,
            primary_action=RecoveryAction.PAUSE_ACCOUNT,
            fallback_actions=[RecoveryAction.SWITCH_PROXY],
            max_retries=1,
            cooldown_seconds=1800,  # 30 minutes
            description="Action blocked - pause account temporarily"
        ),
        
        # Element/UI errors
        ErrorCode.E_ELEMENT_NOT_FOUND: RecoveryPolicy(
            error_code=ErrorCode.E_ELEMENT_NOT_FOUND,
            category=ErrorCategory.ELEMENT,
            primary_action=RecoveryAction.RETRY_WITH_RECOVERY,
            fallback_actions=[RecoveryAction.RESET_TO_HOME, RecoveryAction.FAIL],
            max_retries=3,
            cooldown_seconds=3,
            description="UI element not found - try recovery or fail"
        ),
        
        ErrorCode.E_CLICK_NO_EFFECT: RecoveryPolicy(
            error_code=ErrorCode.E_CLICK_NO_EFFECT,
            category=ErrorCategory.ELEMENT,
            primary_action=RecoveryAction.RETRY,
            fallback_actions=[RecoveryAction.RETRY_WITH_RECOVERY, RecoveryAction.RESET_TO_HOME],
            max_retries=3,
            cooldown_seconds=2,
            description="Click had no effect - retry or recover"
        ),
        
        ErrorCode.E_UI_CHANGED: RecoveryPolicy(
            error_code=ErrorCode.E_UI_CHANGED,
            category=ErrorCategory.ELEMENT,
            primary_action=RecoveryAction.ESCALATE,
            fallback_actions=[],
            max_retries=0,
            cooldown_seconds=0,
            description="Instagram UI changed - selectors need updating"
        ),
        
        # Critical errors
        ErrorCode.E_CRITICAL_FSM_ERROR: RecoveryPolicy(
            error_code=ErrorCode.E_CRITICAL_FSM_ERROR,
            category=ErrorCategory.CRITICAL,
            primary_action=RecoveryAction.FAIL,
            fallback_actions=[],
            max_retries=0,
            cooldown_seconds=0,
            description="Critical FSM error - immediate failure"
        ),
        
        ErrorCode.E_UNKNOWN: RecoveryPolicy(
            error_code=ErrorCode.E_UNKNOWN,
            category=ErrorCategory.CRITICAL,
            primary_action=RecoveryAction.RETRY_WITH_RECOVERY,
            fallback_actions=[RecoveryAction.RESET_TO_HOME, RecoveryAction.FAIL],
            max_retries=2,
            cooldown_seconds=5,
            description="Unknown error - try basic recovery"
        )
    }
    
    @classmethod
    def get_policy(cls, error_code: ErrorCode) -> RecoveryPolicy:
        """Get recovery policy for an error code"""
        return cls.POLICIES.get(error_code, cls.POLICIES[ErrorCode.E_UNKNOWN])
    
    @classmethod
    def get_policy_by_string(cls, error_code_str: str) -> RecoveryPolicy:
        """Get recovery policy by error code string"""
        try:
            error_code = ErrorCode(error_code_str)
            return cls.get_policy(error_code)
        except ValueError:
            logger.warning(f"Unknown error code: {error_code_str}")
            return cls.POLICIES[ErrorCode.E_UNKNOWN]
    
    @classmethod
    def classify_error(cls, error_message: str) -> ErrorCode:
        """Classify an error message into an error code"""
        error_msg_lower = error_message.lower()
        
        # Timeout classification
        if "timeout" in error_msg_lower:
            if "element" in error_msg_lower or "anchor" in error_msg_lower:
                return ErrorCode.E_TIMEOUT_ANCHOR
            elif "load" in error_msg_lower:
                return ErrorCode.E_TIMEOUT_LOAD
            elif "network" in error_msg_lower:
                return ErrorCode.E_TIMEOUT_NETWORK
            else:
                return ErrorCode.E_TIMEOUT_ANCHOR
        
        # Navigation classification
        if "navigation" in error_msg_lower or "nav" in error_msg_lower:
            if "loop" in error_msg_lower:
                return ErrorCode.E_NAV_LOOP
            elif "lost" in error_msg_lower:
                return ErrorCode.E_NAV_LOST
            elif "blocked" in error_msg_lower or "modal" in error_msg_lower:
                return ErrorCode.E_NAV_BLOCKED
            else:
                return ErrorCode.E_NAV_UNEXPECTED
        
        # Session classification
        if "session" in error_msg_lower:
            if "drop" in error_msg_lower or "disconnect" in error_msg_lower:
                return ErrorCode.E_SESSION_DROP
            else:
                return ErrorCode.E_SESSION_INVALID
        
        if "crash" in error_msg_lower:
            return ErrorCode.E_APP_CRASH
        
        # Network/Proxy classification
        if "proxy" in error_msg_lower:
            return ErrorCode.E_PROXY_BLOCK
        
        if "rate limit" in error_msg_lower:
            return ErrorCode.E_RATE_LIMITED
        
        if "network" in error_msg_lower:
            return ErrorCode.E_NETWORK_UNREACHABLE
        
        # Instagram security classification
        if "checkpoint" in error_msg_lower:
            return ErrorCode.E_CHECKPOINT
        
        if "login" in error_msg_lower and "required" in error_msg_lower:
            return ErrorCode.E_LOGIN_REQUIRED
        
        if "suspend" in error_msg_lower or "ban" in error_msg_lower:
            return ErrorCode.E_ACCOUNT_SUSPENDED
        
        if "blocked" in error_msg_lower and "action" in error_msg_lower:
            return ErrorCode.E_ACTION_BLOCKED
        
        # Element classification
        if "element" in error_msg_lower:
            if "not found" in error_msg_lower:
                return ErrorCode.E_ELEMENT_NOT_FOUND
            elif "not clickable" in error_msg_lower:
                return ErrorCode.E_ELEMENT_NOT_CLICKABLE
            else:
                return ErrorCode.E_ELEMENT_NOT_FOUND
        
        if "click" in error_msg_lower and "no effect" in error_msg_lower:
            return ErrorCode.E_CLICK_NO_EFFECT
        
        # Critical classification
        if "critical" in error_msg_lower or "fsm" in error_msg_lower:
            return ErrorCode.E_CRITICAL_FSM_ERROR
        
        if "driver" in error_msg_lower:
            return ErrorCode.E_DRIVER_ERROR
        
        # Default to unknown
        return ErrorCode.E_UNKNOWN
    
    @classmethod
    def get_error_categories(cls) -> Dict[ErrorCategory, List[ErrorCode]]:
        """Get all error codes grouped by category"""
        categories: Dict[ErrorCategory, List[ErrorCode]] = {}
        
        for error_code, policy in cls.POLICIES.items():
            if policy.category not in categories:
                categories[policy.category] = []
            categories[policy.category].append(error_code)
        
        return categories
    
    @classmethod
    def get_recovery_stats(cls) -> Dict[str, int]:
        """Get statistics about recovery policies"""
        stats = {
            "total_policies": len(cls.POLICIES),
            "retryable_errors": 0,
            "terminal_errors": 0,
            "avg_max_retries": 0
        }
        
        total_retries = 0
        for policy in cls.POLICIES.values():
            if policy.max_retries > 0:
                stats["retryable_errors"] += 1
                total_retries += policy.max_retries
            else:
                stats["terminal_errors"] += 1
        
        if stats["retryable_errors"] > 0:
            stats["avg_max_retries"] = total_retries / stats["retryable_errors"]
        
        return stats
