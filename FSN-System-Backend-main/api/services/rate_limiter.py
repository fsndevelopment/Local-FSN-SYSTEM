#!/usr/bin/env python3
"""
Rate Limiting Service for Instagram Actions
Implements commercial-safe rate limits to prevent Instagram blocking

Rate Limits:
- Comments: 15 per hour (commercial safe)
- Follows: 20 per hour (commercial safe)
- Likes: 40 per hour (existing limit)
- General Actions: 60 per hour (safety buffer)
"""

import time
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ActionRecord:
    """Record of an action performed"""
    timestamp: float
    action_type: str
    device_udid: str
    success: bool
    details: Optional[Dict] = None

@dataclass
class RateLimit:
    """Rate limit configuration"""
    action_type: str
    max_per_hour: int
    current_count: int = 0
    window_start: float = 0
    last_reset: float = 0

class RateLimiter:
    """Commercial-safe rate limiter for Instagram actions"""
    
    def __init__(self, data_file: str = "rate_limits.json"):
        self.data_file = data_file
        self.action_records: Dict[str, List[ActionRecord]] = {}
        self.rate_limits: Dict[str, Dict[str, RateLimit]] = {}
        
        # Define commercial-safe rate limits
        self.default_limits = {
            "comment": 15,  # Comments per hour
            "follow": 20,   # Follows per hour 
            "unfollow": 20, # Unfollows per hour
            "like": 40,     # Likes per hour
            "story_view": 50, # Story views per hour
            "search": 30,   # Searches per hour
            "post_picture": 5, # Posts per hour
            "save_post": 25,   # Saves per hour
            "scan_profile": 30, # Profile scans per hour
            "general": 60   # General actions per hour
        }
        
        self.load_data()
    
    def load_data(self):
        """Load rate limiting data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    
                # Load action records
                for device_udid, records in data.get('action_records', {}).items():
                    self.action_records[device_udid] = [
                        ActionRecord(**record) for record in records
                    ]
                
                # Load rate limits
                for device_udid, limits in data.get('rate_limits', {}).items():
                    self.rate_limits[device_udid] = {
                        action_type: RateLimit(**limit_data)
                        for action_type, limit_data in limits.items()
                    }
        except Exception as e:
            logger.warning(f"Could not load rate limit data: {e}")
            self.action_records = {}
            self.rate_limits = {}
    
    def save_data(self):
        """Save rate limiting data to file"""
        try:
            data = {
                'action_records': {
                    device_udid: [asdict(record) for record in records]
                    for device_udid, records in self.action_records.items()
                },
                'rate_limits': {
                    device_udid: {
                        action_type: asdict(limit)
                        for action_type, limit in limits.items()
                    }
                    for device_udid, limits in self.rate_limits.items()
                }
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save rate limit data: {e}")
    
    def _ensure_device_limits(self, device_udid: str):
        """Ensure device has rate limit entries"""
        if device_udid not in self.rate_limits:
            self.rate_limits[device_udid] = {}
        
        if device_udid not in self.action_records:
            self.action_records[device_udid] = []
        
        # Initialize limits for this device
        current_time = time.time()
        for action_type, max_per_hour in self.default_limits.items():
            if action_type not in self.rate_limits[device_udid]:
                self.rate_limits[device_udid][action_type] = RateLimit(
                    action_type=action_type,
                    max_per_hour=max_per_hour,
                    window_start=current_time,
                    last_reset=current_time
                )
    
    def _clean_old_records(self, device_udid: str, hours_back: int = 2):
        """Clean records older than specified hours"""
        if device_udid not in self.action_records:
            return
        
        cutoff_time = time.time() - (hours_back * 3600)
        self.action_records[device_udid] = [
            record for record in self.action_records[device_udid]
            if record.timestamp >= cutoff_time
        ]
    
    def _reset_hourly_windows(self, device_udid: str):
        """Reset hourly windows if needed"""
        current_time = time.time()
        
        for action_type, limit in self.rate_limits[device_udid].items():
            # If more than an hour has passed, reset the window
            if current_time - limit.window_start >= 3600:
                limit.current_count = 0
                limit.window_start = current_time
                limit.last_reset = current_time
    
    def check_rate_limit(self, device_udid: str, action_type: str) -> Dict[str, any]:
        """
        Check if action is allowed under rate limits
        
        Returns:
            Dict with 'allowed' (bool), 'remaining' (int), 'reset_time' (float), 'message' (str)
        """
        self._ensure_device_limits(device_udid)
        self._clean_old_records(device_udid)
        self._reset_hourly_windows(device_udid)
        
        # Get limit for this action type (fallback to general)
        limit_key = action_type if action_type in self.default_limits else "general"
        limit = self.rate_limits[device_udid][limit_key]
        
        # Count recent actions of this type in current window
        current_time = time.time()
        window_start = limit.window_start
        
        recent_actions = [
            record for record in self.action_records[device_udid]
            if (record.action_type == action_type and 
                record.timestamp >= window_start and
                record.success)  # Only count successful actions
        ]
        
        current_count = len(recent_actions)
        remaining = max(0, limit.max_per_hour - current_count)
        allowed = current_count < limit.max_per_hour
        
        # Calculate reset time (when current window ends)
        reset_time = window_start + 3600
        
        result = {
            'allowed': allowed,
            'remaining': remaining,
            'current_count': current_count,
            'max_per_hour': limit.max_per_hour,
            'reset_time': reset_time,
            'reset_in_seconds': max(0, reset_time - current_time),
            'message': f"Rate limit: {current_count}/{limit.max_per_hour} {action_type} actions used this hour"
        }
        
        if not allowed:
            reset_minutes = int((reset_time - current_time) / 60)
            result['message'] = f"Rate limit exceeded for {action_type}. Try again in {reset_minutes} minutes."
        
        return result
    
    def record_action(self, device_udid: str, action_type: str, success: bool, details: Optional[Dict] = None):
        """Record an action for rate limiting"""
        self._ensure_device_limits(device_udid)
        
        record = ActionRecord(
            timestamp=time.time(),
            action_type=action_type,
            device_udid=device_udid,
            success=success,
            details=details or {}
        )
        
        self.action_records[device_udid].append(record)
        
        # Update current count if successful
        if success:
            limit_key = action_type if action_type in self.default_limits else "general"
            self.rate_limits[device_udid][limit_key].current_count += 1
        
        # Clean old records and save
        self._clean_old_records(device_udid)
        self.save_data()
        
        logger.info(f"Recorded {action_type} action for {device_udid}: {'success' if success else 'failed'}")
    
    def get_device_status(self, device_udid: str) -> Dict[str, any]:
        """Get complete rate limiting status for a device"""
        self._ensure_device_limits(device_udid)
        self._clean_old_records(device_udid)
        self._reset_hourly_windows(device_udid)
        
        status = {
            'device_udid': device_udid,
            'current_time': datetime.now().isoformat(),
            'limits': {},
            'recent_actions': []
        }
        
        # Get status for each action type
        for action_type in self.default_limits.keys():
            limit_status = self.check_rate_limit(device_udid, action_type)
            status['limits'][action_type] = limit_status
        
        # Get recent actions (last 2 hours)
        recent_cutoff = time.time() - (2 * 3600)
        recent_actions = [
            {
                'timestamp': datetime.fromtimestamp(record.timestamp).isoformat(),
                'action_type': record.action_type,
                'success': record.success,
                'details': record.details
            }
            for record in self.action_records[device_udid]
            if record.timestamp >= recent_cutoff
        ]
        
        status['recent_actions'] = sorted(recent_actions, key=lambda x: x['timestamp'], reverse=True)
        
        return status
    
    def get_commercial_recommendations(self) -> Dict[str, any]:
        """Get commercial-safe usage recommendations"""
        return {
            'recommended_limits': self.default_limits,
            'safety_guidelines': {
                'comments': 'Max 15/hour - Use varied, genuine comments',
                'follows': 'Max 20/hour - Target relevant accounts only', 
                'likes': 'Max 40/hour - Mix with organic scrolling',
                'posting': 'Max 5/hour - Space posts throughout day',
                'general': 'Max 60 total actions/hour across all types'
            },
            'best_practices': [
                'Spread actions throughout the day',
                'Vary timing between actions (30s-5min)',
                'Use human-like behavior patterns',
                'Monitor for Instagram warnings',
                'Respect platform terms of service'
            ]
        }

# Global rate limiter instance
rate_limiter = RateLimiter()
