"""
Integrated Photo Posting Routes
API endpoints for the complete photo posting workflow
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import structlog

from ..services.integrated_photo_service import integrated_photo_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/integrated-photo", tags=["Integrated Photo Posting"])

# Request models
class PhotoPostRequest(BaseModel):
    photos_folder: str
    captions_file: Optional[str] = None
    device_udid: str

class TestWorkflowRequest(BaseModel):
    photos_folder: str
    captions_file: Optional[str] = None

@router.post("/process-photo-post")
async def process_photo_post(request: PhotoPostRequest):
    """
    Complete photo posting workflow:
    1. Select random photo from folder
    2. Clean photo (remove metadata, slight modifications)  
    3. Create ngrok tunnel to serve photo
    4. Return photo URL and caption for iPhone
    """
    try:
        logger.info("🚀 Processing photo post request", 
                   folder=request.photos_folder, device=request.device_udid)
        
        result = await integrated_photo_service.process_photo_post(
            photos_folder=request.photos_folder,
            captions_file=request.captions_file,
            device_udid=request.device_udid
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except Exception as e:
        logger.error("❌ Photo post processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/test-workflow")
async def test_workflow(request: TestWorkflowRequest):
    """
    Test the photo processing workflow without device-specific operations
    Useful for testing photo selection, cleaning, and ngrok serving
    """
    try:
        logger.info("🧪 Testing photo workflow", folder=request.photos_folder)
        
        # Use a test device ID
        test_device_udid = "test_device_12345"
        
        result = await integrated_photo_service.process_photo_post(
            photos_folder=request.photos_folder,
            captions_file=request.captions_file,
            device_udid=test_device_udid
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        # Add test-specific information
        result['test_mode'] = True
        result['instructions'] = [
            f"1. Photo selected and cleaned: {result.get('original_photo', 'N/A')}",
            f"2. Photo served at: {result.get('photo_url', 'N/A')}",
            f"3. Caption generated: {result.get('caption', 'N/A')[:100]}...",
            "4. In production, iPhone would download from this URL and post to Instagram"
        ]
        
        return result
        
    except Exception as e:
        logger.error("❌ Workflow test failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.get("/active-handlers")
async def get_active_handlers():
    """Get information about active ngrok handlers and resources"""
    try:
        info = integrated_photo_service.get_active_handlers_info()
        return {
            'success': True,
            'handlers_info': info,
            'message': f"Found {info['active_handlers_count']} active handlers"
        }
        
    except Exception as e:
        logger.error("❌ Failed to get handlers info", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get info: {str(e)}")

@router.post("/cleanup")
async def cleanup_resources():
    """Cleanup all active handlers and temporary resources"""
    try:
        await integrated_photo_service.cleanup_all()
        
        return {
            'success': True,
            'message': 'All resources cleaned up successfully'
        }
        
    except Exception as e:
        logger.error("❌ Cleanup failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.get("/workflow-info")
async def get_workflow_info():
    """Get information about the integrated photo posting workflow"""
    return {
        'success': True,
        'workflow': {
            'name': 'Integrated Photo Posting',
            'description': 'Complete workflow from photo selection to Instagram posting',
            'steps': [
                {
                    'step': 1,
                    'name': 'Photo Selection',
                    'description': 'Randomly select photo from configured folder',
                    'component': 'IntegratedPhotoService._select_random_photo()'
                },
                {
                    'step': 2,
                    'name': 'Photo Cleaning', 
                    'description': 'Remove metadata and apply slight modifications',
                    'component': 'cleaner.clean_metadata_and_modify_image()'
                },
                {
                    'step': 3,
                    'name': 'ngrok Serving',
                    'description': 'Create tunnel to serve photo to iPhone',
                    'component': 'NgrokHandler.start_server_and_tunnel()'
                },
                {
                    'step': 4,
                    'name': 'Caption Generation',
                    'description': 'Select random caption from Excel file or use default',
                    'component': 'IntegratedPhotoService._get_random_caption()'
                },
                {
                    'step': 5,
                    'name': 'iPhone Download',
                    'description': 'iPhone downloads photo from ngrok URL via Safari',
                    'component': 'RunExecutor._download_photo_to_iphone_photos()'
                },
                {
                    'step': 6,
                    'name': 'Instagram Posting',
                    'description': 'Post downloaded photo to Instagram with caption',
                    'component': 'RunExecutor._post_photo_from_gallery()'
                }
            ],
            'template_integration': {
                'photos_per_day': 'Number of photos to post',
                'photos_folder': 'Folder containing source photos',
                'captions_file': 'Excel file with captions (optional)',
                'execution': 'Triggered by RunExecutor when template runs'
            }
        },
        'supported_formats': ['.jpg', '.jpeg', '.png', '.heic'],
        'requirements': [
            'ngrok tokens configured in ngrok_tokens.json',
            'Photos folder with supported image formats',
            'Optional: Excel file with captions',
            'iPhone connected via Appium with Safari and Instagram access'
        ]
    }
