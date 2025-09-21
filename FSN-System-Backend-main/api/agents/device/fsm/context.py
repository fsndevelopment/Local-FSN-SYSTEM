"""
FSM Execution Context
Shared state and data that flows between FSM states during action execution
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from models.device import Device
from models.account import Account
from models.job import Job


class Platform(Enum):
    """Supported platforms"""
    INSTAGRAM = "instagram"
    THREADS = "threads"


class DriverType(Enum):
    """Available driver types"""
    JB = "jb"           # Jailbroken device with Frida/daemon
    NONJB = "nonjb"     # Standard device with WDA only


@dataclass
class ActionTarget:
    """Target for the action (username, post URL, etc.)"""
    type: str                           # "username", "post_url", "hashtag", etc.
    value: str                          # "@example", "https://...", "#hashtag"
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional target data


@dataclass
class ActionPayload:
    """Action-specific parameters and configuration"""
    action_type: str                    # "IG_SCAN_PROFILE", "IG_LIKE", etc.
    target: ActionTarget
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Behavior configuration
    human_like_timing: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30


@dataclass
class DeviceCapabilities:
    """Device capabilities detected at runtime"""
    ui_automation: bool = True          # WDA available
    frida: bool = False                 # Frida daemon available
    fast_scrape: bool = False           # Fast data extraction
    tweak_integration: bool = False     # Custom tweaks installed
    
    frida_version: Optional[str] = None
    tweak_version: Optional[str] = None
    performance_score: Optional[int] = None
    
    def supports(self, capability: str) -> bool:
        """Check if device supports a capability"""
        return getattr(self, capability, False)
    
    def is_jailbroken(self) -> bool:
        """Check if device is jailbroken"""
        return self.frida or self.tweak_integration


@dataclass
class ExecutionMetrics:
    """Performance and execution metrics"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Action-specific metrics
    elements_found: int = 0
    ui_interactions: int = 0
    network_requests: int = 0
    screenshots_taken: int = 0
    
    # Error tracking
    errors_encountered: int = 0
    recoveries_attempted: int = 0
    fallbacks_used: int = 0
    
    def start(self) -> None:
        """Mark execution start"""
        self.start_time = datetime.utcnow()
    
    def end(self) -> None:
        """Mark execution end and calculate duration"""
        self.end_time = datetime.utcnow()
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_ms = int(delta.total_seconds() * 1000)
    
    def increment_counter(self, counter: str) -> None:
        """Increment a metric counter"""
        if hasattr(self, counter):
            current = getattr(self, counter)
            setattr(self, counter, current + 1)


class ActionContext:
    """
    Complete execution context for FSM actions
    Contains all data needed for action execution and state transitions
    """
    
    def __init__(
        self,
        job: Job,
        device: Device,
        account: Account,
        payload: ActionPayload,
        platform: Platform,
        driver_type: DriverType
    ):
        # Core execution data
        self.job = job
        self.device = device
        self.account = account
        self.payload = payload
        self.platform = platform
        self.driver_type = driver_type
        
        # Device capabilities (populated at runtime)
        self.capabilities: Optional[DeviceCapabilities] = None
        
        # Driver instances (populated by driver factory)
        self.driver: Optional[Any] = None  # BaseDriver instance
        self.wda_session: Optional[Any] = None
        self.frida_daemon: Optional[Any] = None
        
        # Execution state
        self.execution_id = f"{job.id}_{datetime.utcnow().timestamp()}"
        self.metrics = ExecutionMetrics()
        
        # Data storage for state transitions
        self.shared_data: Dict[str, Any] = {}
        self.screenshots: List[str] = []  # Screenshot file paths
        self.logs: List[str] = []         # Action logs
        
        # Results storage
        self.result_data: Dict[str, Any] = {}
        self.success: bool = False
        self.error_message: Optional[str] = None
        self.error_code: Optional[str] = None
    
    def set_capabilities(self, capabilities: DeviceCapabilities) -> None:
        """Set device capabilities"""
        self.capabilities = capabilities
    
    def set_driver(self, driver: Any) -> None:
        """Set the driver instance"""
        self.driver = driver
    
    def set_sessions(self, wda_session: Any = None, frida_daemon: Any = None) -> None:
        """Set session instances"""
        self.wda_session = wda_session
        self.frida_daemon = frida_daemon
    
    def store_data(self, key: str, value: Any) -> None:
        """Store data for use in later states"""
        self.shared_data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Retrieve stored data"""
        return self.shared_data.get(key, default)
    
    def add_screenshot(self, file_path: str) -> None:
        """Add screenshot path"""
        self.screenshots.append(file_path)
        self.metrics.increment_counter("screenshots_taken")
    
    def add_log(self, message: str) -> None:
        """Add log message"""
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
    
    def set_result(self, data: Dict[str, Any], success: bool = True) -> None:
        """Set final result data"""
        self.result_data = data
        self.success = success
    
    def set_error(self, error_message: str, error_code: str) -> None:
        """Set error information"""
        self.error_message = error_message
        self.error_code = error_code
        self.success = False
        self.metrics.increment_counter("errors_encountered")
    
    def get_platform_prefix(self) -> str:
        """Get platform prefix for job types (IG_, TH_)"""
        return "IG_" if self.platform == Platform.INSTAGRAM else "TH_"
    
    def is_jailbroken_device(self) -> bool:
        """Check if device is jailbroken"""
        return (self.capabilities and self.capabilities.is_jailbroken()) or False
    
    def supports_fast_scrape(self) -> bool:
        """Check if device supports fast scraping"""
        return (self.capabilities and self.capabilities.fast_scrape) or False
    
    def get_timeout(self) -> int:
        """Get timeout for operations"""
        return self.payload.parameters.get("timeout_seconds", self.payload.timeout_seconds)
    
    def get_max_retries(self) -> int:
        """Get maximum retry count"""
        return self.payload.parameters.get("max_retries", self.payload.max_retries)
    
    def should_use_human_timing(self) -> bool:
        """Check if human-like timing should be used"""
        return self.payload.human_like_timing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging"""
        return {
            "execution_id": self.execution_id,
            "job_id": self.job.id,
            "device_udid": self.device.udid,
            "account_username": self.account.username,
            "platform": self.platform.value,
            "driver_type": self.driver_type.value,
            "action_type": self.payload.action_type,
            "target": {
                "type": self.payload.target.type,
                "value": self.payload.target.value
            },
            "capabilities": {
                "jailbroken": self.is_jailbroken_device(),
                "fast_scrape": self.supports_fast_scrape()
            } if self.capabilities else None,
            "metrics": {
                "duration_ms": self.metrics.duration_ms,
                "elements_found": self.metrics.elements_found,
                "ui_interactions": self.metrics.ui_interactions,
                "screenshots_taken": self.metrics.screenshots_taken,
                "errors_encountered": self.metrics.errors_encountered,
                "recoveries_attempted": self.metrics.recoveries_attempted
            },
            "result": {
                "success": self.success,
                "error_message": self.error_message,
                "error_code": self.error_code,
                "data": self.result_data
            },
            "logs_count": len(self.logs),
            "screenshots_count": len(self.screenshots)
        }
