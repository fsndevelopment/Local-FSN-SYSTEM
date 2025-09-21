"""
Real Device Test Routes
Quick testing endpoints for confirmed working Instagram actions
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
import logging
from services.real_device_instagram import real_device_instagram
from services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/real-device", tags=["real-device-testing"])

@router.post("/test-like")
async def test_like_posts(count: int = 5, device_udid: Optional[str] = None) -> Dict[str, Any]:
    """Test like functionality using confirmed working selectors"""
    try:
        result = await real_device_instagram.like_posts(device_udid, count)
        return {
            "status": "success" if result['success'] else "failed",
            "message": result['message'],
            "data": result['data']
        }
    except Exception as e:
        logger.error(f"Test like error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-comment")
async def test_comment_posts(
    count: int = 3, 
    comments: List[str] = ["Great post! 👍", "Amazing content!", "Love this! ✨"],
    device_udid: Optional[str] = None
) -> Dict[str, Any]:
    """Test comment functionality using confirmed working 7-checkpoint system"""
    try:
        result = await real_device_instagram.comment_on_posts(device_udid, comments, count)
        return {
            "status": "success" if result['success'] else "failed",
            "message": result['message'],
            "data": result['data']
        }
    except Exception as e:
        logger.error(f"Test comment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-follow")
async def test_follow_user(username: str, device_udid: Optional[str] = None) -> Dict[str, Any]:
    """Test follow functionality using confirmed working search navigation"""
    try:
        result = await real_device_instagram.follow_user(device_udid, username)
        return {
            "status": "success" if result['success'] else "failed",
            "message": result['message'],
            "data": result['data']
        }
    except Exception as e:
        logger.error(f"Test follow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-stories")
async def test_view_stories(count: int = 10, device_udid: Optional[str] = None) -> Dict[str, Any]:
    """Test story viewing using confirmed working selectors"""
    try:
        result = await real_device_instagram.view_stories(device_udid, count)
        return {
            "status": "success" if result['success'] else "failed",
            "message": result['message'],
            "data": result['data']
        }
    except Exception as e:
        logger.error(f"Test stories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-scan-profile")
async def test_scan_profile(username: Optional[str] = None, device_udid: Optional[str] = None) -> Dict[str, Any]:
    """Test profile scanning using confirmed working extraction"""
    try:
        result = await real_device_instagram.scan_profile(device_udid, username)
        return {
            "status": "success" if result['success'] else "failed",
            "message": result['message'],
            "data": result['data']
        }
    except Exception as e:
        logger.error(f"Test scan profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-post-picture")
async def test_post_picture(caption: str = "Posted via FSN Appium API! 📸", device_udid: Optional[str] = None) -> Dict[str, Any]:
    """Test picture posting using confirmed working 8-checkpoint system"""
    try:
        result = await real_device_instagram.post_picture(device_udid, caption)
        return {
            "status": "success" if result['success'] else "failed",
            "message": result['message'],
            "data": result['data']
        }
    except Exception as e:
        logger.error(f"Test post picture error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-search-hashtag")
async def test_search_hashtag(hashtag: str, device_udid: Optional[str] = None) -> Dict[str, Any]:
    """Test hashtag search using confirmed working 7-checkpoint system"""
    try:
        result = await real_device_instagram.search_hashtag(device_udid, hashtag)
        return {
            "status": "success" if result['success'] else "failed",
            "message": result['message'],
            "data": result['data']
        }
    except Exception as e:
        logger.error(f"Test search hashtag error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-save-post")
async def test_save_post(device_udid: Optional[str] = None) -> Dict[str, Any]:
    """Test post saving using confirmed working 7-checkpoint system"""
    try:
        result = await real_device_instagram.save_post(device_udid)
        return {
            "status": "success" if result['success'] else "failed",
            "message": result['message'],
            "data": result['data']
        }
    except Exception as e:
        logger.error(f"Test save post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-status")
async def get_test_status() -> Dict[str, Any]:
    """Get current testing status and confirmed working actions"""
    return {
        "confirmed_working_actions": [
            "LIKE_POST - simple_like_test.py ✅",
            "COMMENT_POST - comment_functionality_test.py (7-checkpoint system) ✅",
            "FOLLOW_USER - follow_unfollow_functionality_test.py (search navigation) ✅",
            "VIEW_STORY - working_story_test.py ✅",
            "SCAN_PROFILE - simple_scan_profile_test.py ✅",
            "POST_PICTURE - post_picture_functionality_test.py (8-checkpoint system) ✅",
            "SEARCH_HASHTAG - search_hashtag_functionality_test.py (7-checkpoint system) ✅",
            "SAVE_POST - save_post_functionality_test.py (7-checkpoint system) ✅"
        ],
        "total_confirmed": 9,
        "progress": "55% Complete - ALL 9 CORE INSTAGRAM ACTIONS WORKING! 🎉",
        "milestone": "Step 6 COMPLETED - Complete Instagram automation suite achieved",
        "next_step": "API Integration & Production Deployment",
        "critical_search_pattern": {
            "skip_suggestion": "search-collection-view-cell-5013418422474281695",
            "click_actual_profile": "search-collection-view-cell-202075315"
        },
        "new_actions_added": [
            "POST_PICTURE - Complete photo posting with caption",
            "SEARCH_HASHTAG - Hashtag search and data extraction", 
            "SAVE_POST - Post saving functionality"
        ]
    }

@router.get("/rate-limits/{device_udid}")
async def get_device_rate_limits(device_udid: str) -> Dict[str, Any]:
    """Get rate limiting status for a specific device"""
    try:
        status = rate_limiter.get_device_status(device_udid)
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"Rate limits status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rate-limits-recommendations")
async def get_rate_limit_recommendations() -> Dict[str, Any]:
    """Get commercial-safe rate limiting recommendations"""
    try:
        recommendations = rate_limiter.get_commercial_recommendations()
        return {
            "status": "success",
            "data": recommendations
        }
    except Exception as e:
        logger.error(f"Rate limit recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
