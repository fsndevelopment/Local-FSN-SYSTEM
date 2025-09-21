"""
Tracking and analytics API routes - Placeholder
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/tracking")
async def get_tracking():
    return {"message": "Tracking endpoint - coming soon"}
