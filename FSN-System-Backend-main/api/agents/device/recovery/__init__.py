"""
Recovery Package
Error handling, recovery helpers, and watchdog systems
"""

from .helpers import (
    ensure_home, close_modals, hide_keyboard, 
    return_home_map, detect_current_screen,
    RecoveryError
)
from .error_taxonomy import (
    ErrorCategory, ErrorCode, RecoveryAction, 
    RecoveryPolicy, ErrorTaxonomy
)
from .watchdogs import (
    Watchdog, WatchdogSystem, WatchdogConfig, WatchdogTelemetry,
    InputFreezeDetector, SessionDropDetector, NetworkStallDetector, DeadmanTimer
)

__all__ = [
    # Recovery helpers
    "ensure_home",
    "close_modals", 
    "hide_keyboard",
    "return_home_map",
    "detect_current_screen",
    "RecoveryError",
    
    # Error taxonomy
    "ErrorCategory",
    "ErrorCode",
    "RecoveryAction",
    "RecoveryPolicy", 
    "ErrorTaxonomy",
    
    # Watchdog system
    "Watchdog",
    "WatchdogSystem",
    "WatchdogConfig",
    "WatchdogTelemetry",
    "InputFreezeDetector",
    "SessionDropDetector", 
    "NetworkStallDetector",
    "DeadmanTimer"
]
