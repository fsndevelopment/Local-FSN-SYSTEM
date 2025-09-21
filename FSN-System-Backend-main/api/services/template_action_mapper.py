"""
Template Action Mapper
Maps template configurations to Appium actions
"""

import logging
from typing import List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Available action types"""
    POST_THREAD = "post_thread"
    LIKE_POST = "like_post"
    COMMENT_POST = "comment_post"
    FOLLOW_USER = "follow_user"
    UNFOLLOW_USER = "unfollow_user"
    SCAN_PROFILE = "scan_profile"
    SEARCH_PROFILE = "search_profile"
    VIEW_THREAD = "view_thread"
    REPLY_TO_THREAD = "reply_to_thread"
    REPOST = "repost"
    QUOTE_POST = "quote_post"
    EDIT_PROFILE = "edit_profile"

class AppiumAction:
    """Represents an Appium action to be executed"""
    
    def __init__(self, action_type: ActionType, platform: str, count: int = 1, parameters: Dict[str, Any] = None):
        self.type = action_type
        self.platform = platform
        self.count = count
        self.parameters = parameters or {}

class TemplateActionMapper:
    """Maps template configurations to Appium actions"""
    
    def __init__(self):
        self.script_paths = {
            ActionType.POST_THREAD: "platforms/threads/working_tests/06_post_thread_functionality_test.py",
            ActionType.LIKE_POST: "platforms/threads/working_tests/01_like_post_functionality_test.py",
            ActionType.COMMENT_POST: "platforms/threads/working_tests/02_comment_post_functionality_test.py",
            ActionType.SCAN_PROFILE: "platforms/threads/working_tests/04_scan_profile_functionality_test.py",
            ActionType.SEARCH_PROFILE: "platforms/threads/working_tests/03_search_profile_functionality_test.py",
            ActionType.VIEW_THREAD: "platforms/threads/working_tests/05_view_thread_functionality_test.py",
            ActionType.REPLY_TO_THREAD: "platforms/threads/working_tests/07_reply_to_thread_functionality_test.py",
            ActionType.REPOST: "platforms/threads/working_tests/08_repost_functionality_test.py",
            ActionType.QUOTE_POST: "platforms/threads/working_tests/09_quote_post_functionality_test.py",
            ActionType.EDIT_PROFILE: "platforms/threads/working_tests/12_edit_profile_functionality_test.py",
        }
    
    def map_template_to_actions(self, template: Dict[str, Any]) -> List[AppiumAction]:
        """
        Map template configuration to list of Appium actions
        
        Args:
            template: Template configuration dictionary
            
        Returns:
            List of AppiumAction objects
        """
        actions = []
        platform = template.get("platform", "threads").lower()
        settings = template.get("settings", {})
        
        logger.info(f"Mapping template to actions", 
                   template_id=template.get("id"),
                   platform=platform,
                   settings=settings)
        
        # Map text posts per day to POST_THREAD actions
        text_posts_per_day = settings.get("textPostsPerDay", 0)
        if text_posts_per_day > 0:
            actions.append(AppiumAction(
                action_type=ActionType.POST_THREAD,
                platform=platform,
                count=text_posts_per_day,
                parameters={
                    "text_posts_file": settings.get("textPostsFile", "threads_posts.txt"),
                    "captions_file": settings.get("captionsFile", "")
                }
            ))
        
        # Map photo posts per day to POST_THREAD actions with images
        photo_posts_per_day = settings.get("photosPostsPerDay", 0)
        if photo_posts_per_day > 0:
            actions.append(AppiumAction(
                action_type=ActionType.POST_THREAD,
                platform=platform,
                count=photo_posts_per_day,
                parameters={
                    "photos_folder": settings.get("photosFolder", "threads_photos"),
                    "include_images": True
                }
            ))
        
        # Map likes per day to LIKE_POST actions
        likes_per_day = settings.get("likesPerDay", 0)
        if likes_per_day > 0:
            actions.append(AppiumAction(
                action_type=ActionType.LIKE_POST,
                platform=platform,
                count=likes_per_day
            ))
        
        # Map follows per day to FOLLOW_USER actions
        follows_per_day = settings.get("followsPerDay", 0)
        if follows_per_day > 0:
            actions.append(AppiumAction(
                action_type=ActionType.FOLLOW_USER,
                platform=platform,
                count=follows_per_day
            ))
        
        # Map scrolling time to VIEW_THREAD actions
        scrolling_time_minutes = settings.get("scrollingTimeMinutes", 0)
        if scrolling_time_minutes > 0:
            # Convert minutes to approximate number of scroll actions
            scroll_count = max(1, scrolling_time_minutes * 2)  # ~2 scrolls per minute
            actions.append(AppiumAction(
                action_type=ActionType.VIEW_THREAD,
                platform=platform,
                count=scroll_count,
                parameters={
                    "scrolling_duration_minutes": scrolling_time_minutes
                }
            ))
        
        logger.info(f"Generated {len(actions)} actions from template", 
                   template_id=template.get("id"),
                   action_count=len(actions))
        
        return actions
    
    def get_script_path(self, action: AppiumAction) -> str:
        """Get the script path for an action"""
        return self.script_paths.get(action.type)

# Global instance
template_action_mapper = TemplateActionMapper()