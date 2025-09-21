"""
Watchdog Systems for Instagram/Threads Automation
Lightweight async monitoring tasks for error detection and recovery
"""

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import time

from ..fsm.context import ActionContext

logger = logging.getLogger(__name__)


@dataclass
class WatchdogConfig:
    """Configuration for watchdog systems"""
    
    # UI Freeze Detection
    ui_freeze_enabled: bool = True
    ui_freeze_samples: int = 3
    ui_freeze_interval_ms: int = 3000
    ui_freeze_p_hash_delta_max: int = 2
    
    # Session Drop Detection
    session_enabled: bool = True
    session_ping_interval_s: int = 8
    session_fail_threshold: int = 2
    
    # Network Stall Detection
    network_stall_enabled: bool = True
    network_stall_inactivity_s: int = 15
    network_stall_check_interval_s: int = 3
    
    # Deadman Timer
    deadman_enabled: bool = True
    deadman_max_duration_s: int = 120


@dataclass
class WatchdogTelemetry:
    """Telemetry data for watchdog systems"""
    
    # Counters
    ui_freeze_trips: int = 0
    session_restarts: int = 0
    network_stalls: int = 0
    deadman_trips: int = 0
    
    # Timing data
    state_durations: Dict[str, List[float]] = field(default_factory=dict)
    guard_wait_times: Dict[str, List[float]] = field(default_factory=dict)
    retries_per_action: List[int] = field(default_factory=list)
    
    # Status gauges
    driver_session_up: Dict[str, bool] = field(default_factory=dict)
    proxy_in_use: Dict[str, str] = field(default_factory=dict)
    
    def increment_counter(self, counter: str) -> None:
        """Increment a telemetry counter"""
        if hasattr(self, counter):
            current = getattr(self, counter)
            setattr(self, counter, current + 1)
    
    def record_duration(self, category: str, key: str, duration_ms: float) -> None:
        """Record duration measurement"""
        if category not in self.state_durations:
            self.state_durations[category] = []
        self.state_durations[category].append(duration_ms)
    
    def set_gauge(self, gauge: str, key: str, value: Any) -> None:
        """Set gauge value"""
        if hasattr(self, gauge):
            gauge_dict = getattr(self, gauge)
            gauge_dict[key] = value


class Watchdog(ABC):
    """Base class for all watchdog implementations"""
    
    def __init__(self, name: str, config: WatchdogConfig, telemetry: WatchdogTelemetry):
        self.name = name
        self.config = config
        self.telemetry = telemetry
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.context: Optional[ActionContext] = None
    
    @abstractmethod
    async def tick(self, ctx: ActionContext) -> None:
        """Perform watchdog check - implemented by subclasses"""
        pass
    
    async def start(self, ctx: ActionContext) -> None:
        """Start the watchdog monitoring"""
        if self.is_running:
            return
        
        self.context = ctx
        self.is_running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.debug(f"Started watchdog: {self.name}")
    
    async def stop(self) -> None:
        """Stop the watchdog monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.debug(f"Stopped watchdog: {self.name}")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        try:
            while self.is_running and self.context:
                await self.tick(self.context)
                await asyncio.sleep(self.get_check_interval())
        except asyncio.CancelledError:
            logger.debug(f"Watchdog {self.name} monitoring cancelled")
        except Exception as e:
            logger.error(f"Watchdog {self.name} error: {e}")
            if self.context:
                self.context.set_error(f"Watchdog {self.name} failed: {e}", f"E_WATCHDOG_{self.name.upper()}")
    
    @abstractmethod
    def get_check_interval(self) -> float:
        """Get the check interval in seconds"""
        pass
    
    def raise_watchdog_error(self, ctx: ActionContext, error_code: str, details: str) -> None:
        """Raise a watchdog detection error"""
        logger.warning(f"Watchdog {self.name} detected issue: {error_code} - {details}")
        ctx.set_error(f"Watchdog detection: {details}", error_code)
        ctx.add_log(f"Watchdog {self.name} triggered: {error_code}")


class InputFreezeDetector(Watchdog):
    """
    Detects UI freeze by comparing perceptual hashes of screenshots
    Uses downscaled grayscale images for efficient comparison
    """
    
    def __init__(self, config: WatchdogConfig, telemetry: WatchdogTelemetry):
        super().__init__("InputFreeze", config, telemetry)
        self.screenshot_hashes: List[str] = []
        self.last_screenshot_time = 0
    
    async def tick(self, ctx: ActionContext) -> None:
        """Check for UI freeze by comparing screenshot hashes"""
        if not self.config.ui_freeze_enabled:
            return
        
        current_time = time.time() * 1000  # milliseconds
        
        # Only check at specified intervals
        if current_time - self.last_screenshot_time < self.config.ui_freeze_interval_ms:
            return
        
        try:
            # Take screenshot and compute perceptual hash
            screenshot_path = f"/tmp/watchdog_{ctx.execution_id}_{int(current_time)}.png"
            if ctx.driver and await ctx.driver.take_screenshot(screenshot_path):
                p_hash = await self._compute_perceptual_hash(screenshot_path)
                
                if p_hash:
                    self.screenshot_hashes.append(p_hash)
                    self.last_screenshot_time = current_time
                    
                    # Keep only the required number of samples
                    if len(self.screenshot_hashes) > self.config.ui_freeze_samples:
                        self.screenshot_hashes.pop(0)
                    
                    # Check for freeze if we have enough samples
                    if len(self.screenshot_hashes) >= self.config.ui_freeze_samples:
                        if self._detect_ui_freeze():
                            self.telemetry.increment_counter("ui_freeze_trips")
                            self.raise_watchdog_error(
                                ctx, 
                                "E_UI_FREEZE",
                                f"UI frozen for {self.config.ui_freeze_samples} consecutive samples"
                            )
                            # Clear samples after detection
                            self.screenshot_hashes.clear()
                
                # Clean up screenshot file
                try:
                    import os
                    os.remove(screenshot_path)
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"InputFreezeDetector error: {e}")
    
    async def _compute_perceptual_hash(self, image_path: str) -> Optional[str]:
        """Compute perceptual hash of screenshot"""
        try:
            # TODO: Implement actual perceptual hash computation
            # This would typically use PIL/Pillow to:
            # 1. Load image
            # 2. Convert to grayscale
            # 3. Resize to small size (e.g., 32x32)
            # 4. Compute hash (average hash or perceptual hash)
            
            # Placeholder implementation using file hash
            with open(image_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()[:16]  # Shortened for demo
                
        except Exception as e:
            logger.debug(f"Failed to compute perceptual hash: {e}")
            return None
    
    def _detect_ui_freeze(self) -> bool:
        """Detect if UI is frozen based on hash similarity"""
        if len(self.screenshot_hashes) < self.config.ui_freeze_samples:
            return False
        
        # Compare all hashes for similarity
        # TODO: Implement actual perceptual hash distance calculation
        # For now, using exact string comparison as placeholder
        
        first_hash = self.screenshot_hashes[0]
        identical_count = sum(1 for h in self.screenshot_hashes if h == first_hash)
        
        # If all samples are identical or very similar, UI is likely frozen
        return identical_count >= self.config.ui_freeze_samples
    
    def get_check_interval(self) -> float:
        """Get check interval in seconds"""
        return self.config.ui_freeze_interval_ms / 1000.0


class SessionDropDetector(Watchdog):
    """
    Monitors WDA session health by pinging /status endpoint
    Attempts automatic reconnection on failures
    """
    
    def __init__(self, config: WatchdogConfig, telemetry: WatchdogTelemetry):
        super().__init__("SessionDrop", config, telemetry)
        self.consecutive_failures = 0
        self.last_ping_time = 0
    
    async def tick(self, ctx: ActionContext) -> None:
        """Check WDA session health"""
        if not self.config.session_enabled:
            return
        
        current_time = time.time()
        
        # Only ping at specified intervals
        if current_time - self.last_ping_time < self.config.session_ping_interval_s:
            return
        
        self.last_ping_time = current_time
        
        try:
            if ctx.driver:
                # Ping WDA session
                session_healthy = await self._ping_wda_session(ctx.driver)
                
                if session_healthy:
                    self.consecutive_failures = 0
                    self.telemetry.set_gauge("driver_session_up", ctx.device.udid, True)
                else:
                    self.consecutive_failures += 1
                    self.telemetry.set_gauge("driver_session_up", ctx.device.udid, False)
                    
                    if self.consecutive_failures >= self.config.session_fail_threshold:
                        self.telemetry.increment_counter("session_restarts")
                        self.raise_watchdog_error(
                            ctx,
                            "E_SESSION_DROP",
                            f"WDA session failed {self.consecutive_failures} consecutive pings"
                        )
                        self.consecutive_failures = 0  # Reset after detection
                        
        except Exception as e:
            logger.debug(f"SessionDropDetector error: {e}")
            self.consecutive_failures += 1
    
    async def _ping_wda_session(self, driver) -> bool:
        """Ping WDA session to check health"""
        try:
            # TODO: Implement actual WDA session ping
            # This would typically make a request to /status endpoint
            # For now, assume session is healthy if driver is connected
            return driver.is_connected
            
        except Exception as e:
            logger.debug(f"WDA ping failed: {e}")
            return False
    
    def get_check_interval(self) -> float:
        """Get check interval in seconds"""
        return self.config.session_ping_interval_s


class NetworkStallDetector(Watchdog):
    """
    Detects network stalls by monitoring XML source changes
    Tracks node count changes to detect feed loading issues
    """
    
    def __init__(self, config: WatchdogConfig, telemetry: WatchdogTelemetry):
        super().__init__("NetworkStall", config, telemetry)
        self.last_xml_node_count = 0
        self.last_change_time = time.time()
        self.monitoring_network_operation = False
    
    async def tick(self, ctx: ActionContext) -> None:
        """Check for network stalls during network operations"""
        if not self.config.network_stall_enabled or not self.monitoring_network_operation:
            return
        
        try:
            if ctx.driver:
                # Get current page source and count nodes
                page_source = await ctx.driver.get_page_source()
                current_node_count = self._count_xml_nodes(page_source)
                
                current_time = time.time()
                
                if current_node_count != self.last_xml_node_count:
                    # Content changed, reset timer
                    self.last_xml_node_count = current_node_count
                    self.last_change_time = current_time
                else:
                    # No change, check if stalled
                    stall_duration = current_time - self.last_change_time
                    
                    if stall_duration > self.config.network_stall_inactivity_s:
                        self.telemetry.increment_counter("network_stalls")
                        self.raise_watchdog_error(
                            ctx,
                            "E_NETWORK_STALL",
                            f"Network stall detected: no content changes for {stall_duration:.1f}s"
                        )
                        # Reset monitoring after detection
                        self.stop_monitoring_network()
                        
        except Exception as e:
            logger.debug(f"NetworkStallDetector error: {e}")
    
    def start_monitoring_network(self) -> None:
        """Start monitoring for network operations"""
        self.monitoring_network_operation = True
        self.last_change_time = time.time()
        logger.debug("Started monitoring network operations")
    
    def stop_monitoring_network(self) -> None:
        """Stop monitoring network operations"""
        self.monitoring_network_operation = False
        logger.debug("Stopped monitoring network operations")
    
    def _count_xml_nodes(self, xml_source: str) -> int:
        """Count XML nodes in page source"""
        try:
            # Simple node counting by counting opening tags
            return xml_source.count('<') if xml_source else 0
        except:
            return 0
    
    def get_check_interval(self) -> float:
        """Get check interval in seconds"""
        return self.config.network_stall_check_interval_s


class DeadmanTimer(Watchdog):
    """
    Deadman timer to prevent infinite loops
    Already implemented in StateMachine, this provides telemetry integration
    """
    
    def __init__(self, config: WatchdogConfig, telemetry: WatchdogTelemetry):
        super().__init__("Deadman", config, telemetry)
        self.action_start_time: Optional[float] = None
    
    async def tick(self, ctx: ActionContext) -> None:
        """Check for deadman timeout"""
        if not self.config.deadman_enabled:
            return
        
        current_time = time.time()
        
        if self.action_start_time is None:
            self.action_start_time = current_time
            return
        
        duration = current_time - self.action_start_time
        
        if duration > self.config.deadman_max_duration_s:
            self.telemetry.increment_counter("deadman_trips")
            self.raise_watchdog_error(
                ctx,
                "E_DEADMAN",
                f"Action exceeded maximum duration: {duration:.1f}s > {self.config.deadman_max_duration_s}s"
            )
    
    def reset_timer(self) -> None:
        """Reset the deadman timer"""
        self.action_start_time = time.time()
    
    def get_check_interval(self) -> float:
        """Get check interval in seconds"""
        return 5.0  # Check every 5 seconds


class WatchdogSystem:
    """
    Manages all watchdog instances for an action execution
    Coordinates startup, monitoring, and shutdown
    """
    
    def __init__(self, config: WatchdogConfig = None):
        self.config = config or WatchdogConfig()
        self.telemetry = WatchdogTelemetry()
        
        # Initialize all watchdogs
        self.watchdogs: List[Watchdog] = [
            InputFreezeDetector(self.config, self.telemetry),
            SessionDropDetector(self.config, self.telemetry),
            NetworkStallDetector(self.config, self.telemetry),
            DeadmanTimer(self.config, self.telemetry)
        ]
        
        self.is_running = False
    
    async def start_all(self, ctx: ActionContext) -> None:
        """Start all enabled watchdogs"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting watchdog system")
        
        for watchdog in self.watchdogs:
            try:
                await watchdog.start(ctx)
            except Exception as e:
                logger.error(f"Failed to start watchdog {watchdog.name}: {e}")
    
    async def stop_all(self) -> None:
        """Stop all watchdogs"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping watchdog system")
        
        for watchdog in self.watchdogs:
            try:
                await watchdog.stop()
            except Exception as e:
                logger.error(f"Failed to stop watchdog {watchdog.name}: {e}")
    
    def get_network_stall_detector(self) -> Optional[NetworkStallDetector]:
        """Get network stall detector for manual control"""
        for watchdog in self.watchdogs:
            if isinstance(watchdog, NetworkStallDetector):
                return watchdog
        return None
    
    def get_deadman_timer(self) -> Optional[DeadmanTimer]:
        """Get deadman timer for manual control"""
        for watchdog in self.watchdogs:
            if isinstance(watchdog, DeadmanTimer):
                return watchdog
        return None
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get comprehensive telemetry summary"""
        return {
            "counters": {
                "ui_freeze_trips": self.telemetry.ui_freeze_trips,
                "session_restarts": self.telemetry.session_restarts,
                "network_stalls": self.telemetry.network_stalls,
                "deadman_trips": self.telemetry.deadman_trips
            },
            "histograms": {
                "state_durations": self.telemetry.state_durations,
                "guard_wait_times": self.telemetry.guard_wait_times,
                "retries_per_action": self.telemetry.retries_per_action
            },
            "gauges": {
                "driver_session_up": self.telemetry.driver_session_up,
                "proxy_in_use": self.telemetry.proxy_in_use
            },
            "config": {
                "ui_freeze_enabled": self.config.ui_freeze_enabled,
                "session_enabled": self.config.session_enabled,
                "network_stall_enabled": self.config.network_stall_enabled,
                "deadman_enabled": self.config.deadman_enabled
            }
        }
