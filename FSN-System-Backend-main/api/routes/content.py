"""
Content management API routes - Placeholder
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/content")
async def get_content():
    return {"message": "Content endpoint - coming soon"}
