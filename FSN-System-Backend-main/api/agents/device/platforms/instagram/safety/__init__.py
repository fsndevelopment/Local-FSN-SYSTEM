"""
Instagram Safety Package
Rate limiting detection, human behavior simulation, and safety measures
"""

from .rate_limit_detector import (
    InstagramRateLimitDetector,
    RateLimitMiddleware,
    RateLimitEvent,
    RateLimitType,
    RateLimitSeverity
)

__all__ = [
    "InstagramRateLimitDetector",
    "RateLimitMiddleware", 
    "RateLimitEvent",
    "RateLimitType",
    "RateLimitSeverity"
]
