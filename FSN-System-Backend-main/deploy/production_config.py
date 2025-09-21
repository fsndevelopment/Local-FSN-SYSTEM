#!/usr/bin/env python3
"""
Production Configuration for FSN APPIUM Instagram Automation

Complete production-ready configuration with all 9 confirmed working Instagram actions:
1. SCAN_PROFILE ✅
2. SCROLL_HOME_FEED ✅  
3. LIKE_POST ✅
4. VIEW_STORY ✅
5. COMMENT_POST ✅
6. FOLLOW/UNFOLLOW ✅
7. POST_PICTURE ✅
8. SEARCH_HASHTAG ✅
9. SAVE_POST ✅

Rate Limits: Commercial-safe (15 comments/hour, 20 follows/hour, etc.)
"""

import os
from typing import Dict, Any

class ProductionConfig:
    """Production configuration for FSN APPIUM"""
    
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = 8000
    WORKERS = 4
    RELOAD = False  # Disable in production
    
    # Appium Configuration
    APPIUM_HOST = "localhost"
    APPIUM_PORT = 4739
    WDA_LOCAL_PORT = 8108
    
    # Device Configuration
    DEVICE_UDID = os.getenv("DEVICE_UDID", "f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3")
    XCODE_ORG_ID = os.getenv("XCODE_ORG_ID", "QH986HH926")
    XCODE_SIGNING_ID = os.getenv("XCODE_SIGNING_ID", "iPhone Developer")
    
    # Instagram App Configuration
    INSTAGRAM_BUNDLE_ID = "com.burbn.instagram"
    AUTO_ACCEPT_ALERTS = True
    NEW_COMMAND_TIMEOUT = 300
    CONNECT_HARDWARE_KEYBOARD = False
    
    # Rate Limiting Configuration (Commercial Safe)
    RATE_LIMITS = {
        "comment": 15,      # Comments per hour
        "follow": 20,       # Follows per hour
        "unfollow": 20,     # Unfollows per hour
        "like": 40,         # Likes per hour
        "story_view": 50,   # Story views per hour
        "search": 30,       # Searches per hour
        "post_picture": 5,  # Posts per hour
        "save_post": 25,    # Saves per hour
        "scan_profile": 30, # Profile scans per hour
        "general": 60       # General actions per hour
    }
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///fsn_appium_farm.db")
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    API_KEY_HEADER = "X-API-Key"
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Instagram Actions Configuration
    CONFIRMED_ACTIONS = {
        "scan_profile": {
            "enabled": True,
            "selectors": {
                "profile_tab": "profile-tab",
                "followers": "//XCUIElementTypeStaticText",
                "following": "//XCUIElementTypeStaticText", 
                "posts": "//XCUIElementTypeStaticText"
            },
            "rate_limit": "scan_profile"
        },
        "scroll_home_feed": {
            "enabled": True,
            "selectors": {
                "home_tab": "mainfeed-tab",
                "stories_tray": "stories-tray"
            },
            "rate_limit": "general"
        },
        "like_post": {
            "enabled": True,
            "selectors": {
                "like_button": "like-button",
                "home_tab": "mainfeed-tab"
            },
            "rate_limit": "like"
        },
        "view_story": {
            "enabled": True,
            "selectors": {
                "stories_tray": "stories-tray",
                "story_ring": "story-ring",
                "story_dismiss": "story-dismiss-button"
            },
            "rate_limit": "story_view"
        },
        "comment_post": {
            "enabled": True,
            "selectors": {
                "comment_button": "comment-button",
                "text_input": "text-view",
                "post_button": "//XCUIElementTypeButton[@name='send-button' and @label='Post comment']",
                "close_button": "Button"
            },
            "rate_limit": "comment"
        },
        "follow_unfollow": {
            "enabled": True,
            "selectors": {
                "explore_tab": "explore-tab",
                "search_input": "search-text-input",
                "follow_button": "user-detail-header-follow-button",
                "unfollow_cell": "//XCUIElementTypeCell[@name='Unfollow']"
            },
            "rate_limit": "follow",
            "search_patterns": {
                "skip_suggestion": "search-collection-view-cell-5013418422474281695",
                "click_profile": "search-collection-view-cell-202075315"
            }
        },
        "post_picture": {
            "enabled": True,
            "selectors": {
                "camera_tab": "camera-tab",
                "gallery_photo": "gallery-photo-cell-0",
                "next_button": "next-button",
                "caption_field": "caption-cell-text-view",
                "caption_input": "(//XCUIElementTypeTextView[@name='caption-cell-text-view'])[2]",
                "share_button": "share-button",
                "ok_button": "OK"
            },
            "permissions": {
                "continue_button": "ig-photo-library-priming-continue-button",
                "allow_photos": "Allow Access to All Photos"
            },
            "rate_limit": "post_picture"
        },
        "search_hashtag": {
            "enabled": True,
            "selectors": {
                "explore_tab": "explore-tab",
                "search_bar": "search-bar",
                "search_input": "search-text-input",
                "search_results": "//XCUIElementTypeCell[contains(@name, 'search-collection-view-cell-')]"
            },
            "rate_limit": "search"
        },
        "save_post": {
            "enabled": True,
            "selectors": {
                "three_dots": ["three-dots", "more-button"],
                "save_button": "save-button",
                "save_text": "//XCUIElementTypeButton[@name='Save']",
                "save_cell": "//XCUIElementTypeCell[contains(@name, 'Save')]"
            },
            "rate_limit": "save_post"
        }
    }
    
    # Human Behavior Configuration
    HUMAN_BEHAVIOR = {
        "scroll_delays": {
            "min": 1.0,
            "max": 4.0
        },
        "action_delays": {
            "min": 0.5,
            "max": 2.0
        },
        "pause_delays": {
            "min": 2.0,
            "max": 8.0
        },
        "typing_delays": {
            "min": 0.1,
            "max": 0.3
        }
    }
    
    # Monitoring Configuration
    MONITORING = {
        "health_check_interval": 300,  # 5 minutes
        "device_check_interval": 60,   # 1 minute
        "rate_limit_check_interval": 30, # 30 seconds
        "instagram_warning_detection": True
    }
    
    @classmethod
    def get_uvicorn_config(cls) -> Dict[str, Any]:
        """Get configuration for Uvicorn server"""
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "workers": cls.WORKERS,
            "reload": cls.RELOAD,
            "log_level": cls.LOG_LEVEL.lower(),
            "access_log": True
        }
    
    @classmethod
    def get_appium_options(cls) -> Dict[str, Any]:
        """Get Appium driver options"""
        return {
            "platform_name": "iOS",
            "device_name": "iPhone",
            "bundle_id": cls.INSTAGRAM_BUNDLE_ID,
            "udid": cls.DEVICE_UDID,
            "wda_local_port": cls.WDA_LOCAL_PORT,
            "xcode_org_id": cls.XCODE_ORG_ID,
            "xcode_signing_id": cls.XCODE_SIGNING_ID,
            "auto_accept_alerts": cls.AUTO_ACCEPT_ALERTS,
            "new_command_timeout": cls.NEW_COMMAND_TIMEOUT,
            "connect_hardware_keyboard": cls.CONNECT_HARDWARE_KEYBOARD
        }
    
    @classmethod
    def validate_environment(cls) -> Dict[str, Any]:
        """Validate production environment"""
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check required environment variables
        required_env = ["DEVICE_UDID"]
        for var in required_env:
            if not os.getenv(var):
                validation["warnings"].append(f"Environment variable {var} not set, using default")
        
        # Check device connectivity (simplified)
        try:
            import subprocess
            result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True)
            if cls.DEVICE_UDID not in result.stdout:
                validation["errors"].append(f"Device {cls.DEVICE_UDID} not connected")
        except:
            validation["warnings"].append("Could not check device connectivity")
        
        # Check Appium server
        try:
            import requests
            response = requests.get(f"http://{cls.APPIUM_HOST}:{cls.APPIUM_PORT}/status", timeout=5)
            if response.status_code != 200:
                validation["errors"].append("Appium server not responding")
        except:
            validation["warnings"].append("Could not check Appium server")
        
        if validation["errors"]:
            validation["valid"] = False
        
        return validation

# Create global production config instance
production_config = ProductionConfig()
