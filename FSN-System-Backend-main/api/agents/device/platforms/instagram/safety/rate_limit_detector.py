"""
Instagram Rate Limit Detection and Handling
Critical safety feature to detect "action blocked" warnings and implement backoff strategies
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Types of Instagram rate limits"""
    LIKE_LIMIT = "like_limit"
    FOLLOW_LIMIT = "follow_limit"
    COMMENT_LIMIT = "comment_limit"
    STORY_LIMIT = "story_limit"
    GENERAL_LIMIT = "general_limit"
    TEMPORARY_BLOCK = "temporary_block"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class RateLimitSeverity(Enum):
    """Severity levels for rate limiting"""
    WARNING = "warning"           # Soft warning, continue with caution
    MODERATE = "moderate"         # Reduce activity significantly
    SEVERE = "severe"            # Stop activity, wait for cooldown
    CRITICAL = "critical"        # Account at risk, immediate stop


@dataclass
class RateLimitEvent:
    """Rate limit detection event"""
    timestamp: datetime
    limit_type: RateLimitType
    severity: RateLimitSeverity
    message: str
    screenshot_path: Optional[str] = None
    suggested_cooldown_minutes: int = 30
    detection_confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class InstagramRateLimitDetector:
    """
    Detects Instagram rate limiting and action blocks
    Implements progressive backoff strategies
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.rate_limit_history: List[RateLimitEvent] = []
        self.action_counts = {
            "likes": {"count": 0, "last_reset": datetime.now()},
            "follows": {"count": 0, "last_reset": datetime.now()},
            "comments": {"count": 0, "last_reset": datetime.now()},
            "stories": {"count": 0, "last_reset": datetime.now()}
        }
        
        # Conservative rate limits (per hour)
        self.hourly_limits = {
            "likes": 40,        # Very conservative
            "follows": 20,      # Instagram is strict on follows
            "comments": 15,     # Comments are heavily monitored
            "stories": 60       # Stories are generally safer
        }
        
        # Rate limit detection selectors
        self.rate_limit_selectors = {
            "action_blocked_popup": [
                "Action Blocked",
                "Try Again Later", 
                "We restrict certain activity",
                "Tell us if you think we made a mistake"
            ],
            "suspicious_activity": [
                "Suspicious Activity Detected",
                "Please verify your identity",
                "Help us confirm it's you"
            ],
            "follow_limit": [
                "You're following too fast",
                "Slow down",
                "You can't follow more people right now"
            ],
            "like_limit": [
                "You're liking too fast",
                "Take a break",
                "You can't like posts right now"
            ]
        }
    
    async def check_for_rate_limits(self) -> Optional[RateLimitEvent]:
        """
        Check current screen for any rate limiting indicators
        Returns RateLimitEvent if detected, None otherwise
        """
        try:
            # Get current page source
            page_source = await self._get_page_source()
            if not page_source:
                return None
            
            # Check for various rate limit indicators
            for limit_type_name, keywords in self.rate_limit_selectors.items():
                for keyword in keywords:
                    if keyword.lower() in page_source.lower():
                        logger.warning(f"Rate limit detected: {keyword}")
                        
                        # Determine limit type and severity
                        limit_type, severity = self._classify_rate_limit(limit_type_name, keyword)
                        
                        # Create rate limit event
                        event = RateLimitEvent(
                            timestamp=datetime.now(),
                            limit_type=limit_type,
                            severity=severity,
                            message=f"Instagram rate limit detected: {keyword}",
                            detection_confidence=0.9,
                            suggested_cooldown_minutes=self._calculate_cooldown(severity),
                            metadata={
                                "detection_method": "text_analysis",
                                "keyword": keyword,
                                "limit_category": limit_type_name
                            }
                        )
                        
                        # Take screenshot for evidence
                        event.screenshot_path = await self._capture_evidence_screenshot()
                        
                        # Record event
                        self.rate_limit_history.append(event)
                        
                        return event
            
            # Check for visual indicators (buttons, popups)
            rate_limit_elements = await self._check_visual_indicators()
            if rate_limit_elements:
                return rate_limit_elements
                
            return None
            
        except Exception as e:
            logger.error(f"Error checking for rate limits: {e}")
            return None
    
    async def _get_page_source(self) -> Optional[str]:
        """Get current page source safely"""
        try:
            if hasattr(self.driver, 'page_source'):
                return self.driver.page_source
            else:
                # For async drivers
                return await self.driver.get_page_source()
        except Exception as e:
            logger.error(f"Failed to get page source: {e}")
            return None
    
    async def _check_visual_indicators(self) -> Optional[RateLimitEvent]:
        """Check for visual rate limit indicators (buttons, popups)"""
        try:
            # Common rate limit popup buttons
            popup_selectors = [
                ("accessibility_id", "OK"),
                ("accessibility_id", "Try Again Later"),
                ("accessibility_id", "Tell us if you think we made a mistake"),
                ("xpath", "//XCUIElementTypeButton[contains(@name, 'OK')]"),
                ("xpath", "//XCUIElementTypeStaticText[contains(@name, 'Action Blocked')]")
            ]
            
            for selector_type, selector_value in popup_selectors:
                try:
                    if await self._is_element_present(selector_type, selector_value):
                        logger.warning(f"Rate limit popup detected: {selector_value}")
                        
                        event = RateLimitEvent(
                            timestamp=datetime.now(),
                            limit_type=RateLimitType.GENERAL_LIMIT,
                            severity=RateLimitSeverity.MODERATE,
                            message=f"Rate limit popup detected: {selector_value}",
                            detection_confidence=0.95,
                            suggested_cooldown_minutes=60,
                            metadata={
                                "detection_method": "visual_element",
                                "selector_type": selector_type,
                                "selector_value": selector_value
                            }
                        )
                        
                        event.screenshot_path = await self._capture_evidence_screenshot()
                        self.rate_limit_history.append(event)
                        
                        return event
                        
                except Exception:
                    continue  # Try next selector
                    
            return None
            
        except Exception as e:
            logger.error(f"Error checking visual indicators: {e}")
            return None
    
    async def _is_element_present(self, selector_type: str, selector_value: str) -> bool:
        """Check if element is present without throwing exception"""
        try:
            if hasattr(self.driver, 'find_element'):
                # Sync driver
                element = self.driver.find_element(selector_type, selector_value)
                return element is not None
            else:
                # Async driver
                element = await self.driver.find_element(selector_type, selector_value, timeout=2)
                return element is not None
        except:
            return False
    
    def _classify_rate_limit(self, limit_type_name: str, keyword: str) -> tuple[RateLimitType, RateLimitSeverity]:
        """Classify the type and severity of rate limit"""
        
        # Map detection categories to limit types
        type_mapping = {
            "action_blocked_popup": RateLimitType.GENERAL_LIMIT,
            "suspicious_activity": RateLimitType.SUSPICIOUS_ACTIVITY,
            "follow_limit": RateLimitType.FOLLOW_LIMIT,
            "like_limit": RateLimitType.LIKE_LIMIT
        }
        
        limit_type = type_mapping.get(limit_type_name, RateLimitType.GENERAL_LIMIT)
        
        # Determine severity based on keywords
        if any(severe_word in keyword.lower() for severe_word in 
               ["blocked", "restricted", "suspended", "verify your identity"]):
            severity = RateLimitSeverity.SEVERE
        elif any(moderate_word in keyword.lower() for moderate_word in 
                 ["slow down", "take a break", "too fast"]):
            severity = RateLimitSeverity.MODERATE
        elif any(warning_word in keyword.lower() for warning_word in 
                 ["try again later", "confirm"]):
            severity = RateLimitSeverity.WARNING
        else:
            severity = RateLimitSeverity.MODERATE
            
        return limit_type, severity
    
    def _calculate_cooldown(self, severity: RateLimitSeverity) -> int:
        """Calculate recommended cooldown period in minutes"""
        cooldown_mapping = {
            RateLimitSeverity.WARNING: 15,
            RateLimitSeverity.MODERATE: 60,
            RateLimitSeverity.SEVERE: 180,    # 3 hours
            RateLimitSeverity.CRITICAL: 1440  # 24 hours
        }
        
        return cooldown_mapping.get(severity, 60)
    
    async def _capture_evidence_screenshot(self) -> Optional[str]:
        """Capture screenshot for rate limit evidence"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"evidence/rate_limits/rate_limit_{timestamp}.png"
            
            if hasattr(self.driver, 'save_screenshot'):
                self.driver.save_screenshot(screenshot_path)
            else:
                await self.driver.save_screenshot(screenshot_path)
                
            logger.info(f"Rate limit evidence captured: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
    
    def track_action(self, action_type: str) -> bool:
        """
        Track an action and check if we're approaching limits
        Returns True if action is safe, False if we should stop
        """
        if action_type not in self.action_counts:
            logger.warning(f"Unknown action type: {action_type}")
            return True
        
        # Reset hourly counters if needed
        self._reset_hourly_counters()
        
        # Increment counter
        self.action_counts[action_type]["count"] += 1
        current_count = self.action_counts[action_type]["count"]
        limit = self.hourly_limits[action_type]
        
        logger.info(f"Action tracking: {action_type} = {current_count}/{limit}")
        
        # Check if we're approaching the limit
        if current_count >= limit:
            logger.warning(f"Rate limit reached for {action_type}: {current_count}/{limit}")
            return False
        elif current_count >= limit * 0.8:  # 80% of limit
            logger.warning(f"Approaching rate limit for {action_type}: {current_count}/{limit}")
        
        return True
    
    def _reset_hourly_counters(self):
        """Reset action counters every hour"""
        now = datetime.now()
        
        for action_type in self.action_counts:
            last_reset = self.action_counts[action_type]["last_reset"]
            if now - last_reset >= timedelta(hours=1):
                logger.info(f"Resetting hourly counter for {action_type}")
                self.action_counts[action_type]["count"] = 0
                self.action_counts[action_type]["last_reset"] = now
    
    def get_current_limits_status(self) -> Dict[str, Any]:
        """Get current status of all rate limits"""
        self._reset_hourly_counters()
        
        status = {}
        for action_type, data in self.action_counts.items():
            limit = self.hourly_limits[action_type]
            current = data["count"]
            
            status[action_type] = {
                "current": current,
                "limit": limit,
                "percentage": (current / limit) * 100,
                "remaining": limit - current,
                "last_reset": data["last_reset"].isoformat()
            }
        
        return status
    
    def get_rate_limit_history(self, hours: int = 24) -> List[RateLimitEvent]:
        """Get rate limit events from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [event for event in self.rate_limit_history if event.timestamp >= cutoff_time]
    
    async def handle_rate_limit(self, event: RateLimitEvent) -> Dict[str, Any]:
        """
        Handle detected rate limit with appropriate response
        Returns action plan for the calling code
        """
        logger.warning(f"Handling rate limit: {event.limit_type.value} - {event.severity.value}")
        
        action_plan = {
            "should_stop": False,
            "cooldown_minutes": event.suggested_cooldown_minutes,
            "retry_strategy": "exponential_backoff",
            "actions_to_take": []
        }
        
        # Determine response based on severity
        if event.severity == RateLimitSeverity.CRITICAL:
            action_plan.update({
                "should_stop": True,
                "cooldown_minutes": 1440,  # 24 hours
                "actions_to_take": ["screenshot", "alert_admin", "stop_all_automation"]
            })
        
        elif event.severity == RateLimitSeverity.SEVERE:
            action_plan.update({
                "should_stop": True,
                "cooldown_minutes": 180,  # 3 hours
                "actions_to_take": ["screenshot", "dismiss_popup", "wait_and_retry"]
            })
        
        elif event.severity == RateLimitSeverity.MODERATE:
            action_plan.update({
                "should_stop": True,
                "cooldown_minutes": 60,
                "actions_to_take": ["screenshot", "dismiss_popup", "reduce_activity"]
            })
        
        else:  # WARNING
            action_plan.update({
                "should_stop": False,
                "cooldown_minutes": 15,
                "actions_to_take": ["slow_down", "continue_with_caution"]
            })
        
        # Try to dismiss any popup
        if "dismiss_popup" in action_plan["actions_to_take"]:
            await self._dismiss_rate_limit_popup()
        
        logger.info(f"Rate limit action plan: {action_plan}")
        return action_plan
    
    async def _dismiss_rate_limit_popup(self) -> bool:
        """Try to dismiss rate limit popup"""
        try:
            # Common dismiss buttons
            dismiss_selectors = [
                ("accessibility_id", "OK"),
                ("accessibility_id", "Dismiss"),
                ("accessibility_id", "Got it"),
                ("xpath", "//XCUIElementTypeButton[contains(@name, 'OK')]")
            ]
            
            for selector_type, selector_value in dismiss_selectors:
                try:
                    if await self._is_element_present(selector_type, selector_value):
                        if hasattr(self.driver, 'find_element'):
                            element = self.driver.find_element(selector_type, selector_value)
                            element.click()
                        else:
                            element = await self.driver.find_element(selector_type, selector_value)
                            await self.driver.click_element(element)
                        
                        logger.info(f"Dismissed rate limit popup using {selector_value}")
                        await asyncio.sleep(2)  # Wait for popup to disappear
                        return True
                        
                except Exception:
                    continue
            
            logger.warning("Could not find rate limit popup to dismiss")
            return False
            
        except Exception as e:
            logger.error(f"Error dismissing rate limit popup: {e}")
            return False


class RateLimitMiddleware:
    """
    Middleware to wrap Instagram actions with rate limit protection
    """
    
    def __init__(self, detector: InstagramRateLimitDetector):
        self.detector = detector
    
    async def execute_with_protection(self, action_type: str, action_func, *args, **kwargs):
        """
        Execute an action with rate limit protection
        
        Args:
            action_type: Type of action (likes, follows, comments, stories)
            action_func: The function to execute
            *args, **kwargs: Arguments for the action function
        """
        
        # Pre-action checks
        logger.info(f"Executing {action_type} with rate limit protection")
        
        # Check if we're already at rate limits
        if not self.detector.track_action(action_type):
            logger.warning(f"Rate limit reached for {action_type}, skipping action")
            return {
                "success": False,
                "reason": "rate_limit_reached",
                "current_limits": self.detector.get_current_limits_status()
            }
        
        # Check for existing rate limit indicators
        existing_limit = await self.detector.check_for_rate_limits()
        if existing_limit and existing_limit.severity in [RateLimitSeverity.SEVERE, RateLimitSeverity.CRITICAL]:
            logger.warning(f"Existing rate limit detected, skipping {action_type}")
            action_plan = await self.detector.handle_rate_limit(existing_limit)
            return {
                "success": False,
                "reason": "existing_rate_limit",
                "rate_limit_event": existing_limit,
                "action_plan": action_plan
            }
        
        try:
            # Execute the action
            result = await action_func(*args, **kwargs)
            
            # Post-action rate limit check
            post_action_limit = await self.detector.check_for_rate_limits()
            if post_action_limit:
                logger.warning(f"Rate limit triggered by {action_type}")
                action_plan = await self.detector.handle_rate_limit(post_action_limit)
                
                # Update result with rate limit info
                if isinstance(result, dict):
                    result.update({
                        "rate_limit_triggered": True,
                        "rate_limit_event": post_action_limit,
                        "action_plan": action_plan
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing {action_type}: {e}")
            
            # Check if error was due to rate limiting
            error_limit = await self.detector.check_for_rate_limits()
            if error_limit:
                action_plan = await self.detector.handle_rate_limit(error_limit)
                return {
                    "success": False,
                    "reason": "rate_limit_error",
                    "error": str(e),
                    "rate_limit_event": error_limit,
                    "action_plan": action_plan
                }
            
            raise e
