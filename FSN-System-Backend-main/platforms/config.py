#!/usr/bin/env python3
"""
FSN Appium Platform Configuration
================================

Central configuration for all supported platforms.
Each platform has its own automation capabilities and configurations.

Platforms:
- Instagram: 100% Complete (14/14 actions)
- Threads: Phase 2 Development (Clean sheet)

Author: FSN Appium Team
Last Updated: January 15, 2025
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class Platform(Enum):
    """Supported automation platforms"""
    INSTAGRAM = "instagram"
    THREADS = "threads"

@dataclass
class PlatformConfig:
    """Configuration for a specific platform"""
    name: str
    bundle_id: str
    display_name: str
    status: str
    completion_percentage: int
    working_actions: List[str]
    test_directory: str
    actions_directory: str

# Platform Configurations
PLATFORM_CONFIGS = {
    Platform.INSTAGRAM: PlatformConfig(
        name="instagram",
        bundle_id="com.burbn.instagram", 
        display_name="Instagram",
        status="100% Complete - Production Ready",
        completion_percentage=100,
        working_actions=[
            "LIKE_POST",
            "COMMENT_POST", 
            "FOLLOW_UNFOLLOW",
            "SCAN_PROFILE",
            "POST_PICTURE",
            "SEARCH_HASHTAG",
            "SAVE_POST",
            "VIEW_STORY",
            "UNIVERSAL_AD_RECOVERY",
            "CAMERA_MODE_SWITCHING",
            "POST_REEL",
            "POST_STORY", 
            "POST_CAROUSEL",
            "EDIT_PROFILE"
        ],
        test_directory="platforms/instagram/instagram_automation/tests",
        actions_directory="platforms/instagram/instagram_automation/actions"
    ),
    
    Platform.THREADS: PlatformConfig(
        name="threads",
        bundle_id="com.instagram.barcelona",
        display_name="Threads", 
        status="Phase 2 Development - Clean Sheet",
        completion_percentage=0,
        working_actions=[],
        test_directory="platforms/threads/tests",
        actions_directory="platforms/threads/actions"
    )
}

# Device Configuration
DEVICE_CONFIG = {
    "udid": "ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf",  # Your iPhone
    "appium_port": 4741,
    "wda_port": 8109,
    "ios_version": "17.2.1"
}

def get_platform_config(platform: Platform) -> PlatformConfig:
    """Get configuration for specified platform"""
    return PLATFORM_CONFIGS[platform]

def get_all_platforms() -> Dict[Platform, PlatformConfig]:
    """Get all platform configurations"""
    return PLATFORM_CONFIGS

def get_completed_platforms() -> List[Platform]:
    """Get list of completed platforms"""
    return [p for p, config in PLATFORM_CONFIGS.items() if config.completion_percentage == 100]

def get_active_development_platforms() -> List[Platform]:
    """Get platforms currently in development"""
    return [p for p, config in PLATFORM_CONFIGS.items() if 0 < config.completion_percentage < 100]

def get_upcoming_platforms() -> List[Platform]:
    """Get platforms not yet started"""
    return [p for p, config in PLATFORM_CONFIGS.items() if config.completion_percentage == 0]

# Rate Limiting (Instagram-proven, applicable to Threads)
RATE_LIMITS = {
    "likes_per_hour": 40,
    "comments_per_hour": 15, 
    "follows_per_hour": 20,
    "posts_per_day": 10,
    "stories_per_day": 20
}

# Human Behavior Simulation
HUMAN_BEHAVIOR = {
    "action_delay": (1, 5),      # Seconds between actions
    "typing_speed": (0.1, 0.3),  # Seconds per character
    "scroll_duration": (1, 4),   # Seconds for scrolling
    "story_view_time": (3, 8),   # Seconds viewing stories
}

if __name__ == "__main__":
    print("🚀 FSN Appium Platform Configuration")
    print("=====================================")
    
    for platform, config in PLATFORM_CONFIGS.items():
        print(f"\n📱 {config.display_name}")
        print(f"   Status: {config.status}")
        print(f"   Completion: {config.completion_percentage}%")
        print(f"   Actions: {len(config.working_actions)}")
        print(f"   Bundle ID: {config.bundle_id}")
