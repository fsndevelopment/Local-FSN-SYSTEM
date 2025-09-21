"""
Instagram Actions Package
FSM-based Instagram automation actions
"""

from .scan_profile import IGScanProfileAction
from .like import IGLikeAction
from .follow_account import IGFollowAccountAction
from .unfollow_account import IGUnfollowAccountAction

__all__ = [
    "IGScanProfileAction",
    "IGLikeAction",
    "IGFollowAccountAction",
    "IGUnfollowAccountAction"
]
