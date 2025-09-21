"""
Photo Transfer Routes
API endpoints for transferring photos from Mac to iPhone
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import structlog

from ..services.photo_transfer_service import PhotoTransferService

logger = structlog.get_logger()
router = APIRouter(prefix="/api/photo-transfer", tags=["Photo Transfer"])

# Request models
class AirDropRequest(BaseModel):
    photo_path: str

class USBTransferRequest(BaseModel):
    photo_path: str
    device_udid: str

class LocalServerRequest(BaseModel):
    photo_path: str
    port: Optional[int] = 8080

class PhotoListRequest(BaseModel):
    device_udid: str

@router.post("/airdrop")
async def transfer_via_airdrop(request: AirDropRequest):
    """
    Transfer photo using AirDrop
    
    This will open the sharing menu and initiate AirDrop.
    User needs to manually select their iPhone from the AirDrop list.
    """
    try:
        service = PhotoTransferService()
        result = await service.transfer_photo_airdrop(request.photo_path)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return result
        
    except Exception as e:
        logger.error("❌ AirDrop transfer failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"AirDrop transfer failed: {str(e)}")

@router.post("/usb")
async def transfer_via_usb(request: USBTransferRequest):
    """
    Transfer photo via USB using libimobiledevice
    
    Requires:
    - iPhone connected via USB
    - Device trusted on Mac
    - libimobiledevice installed: brew install libimobiledevice
    """
    try:
        service = PhotoTransferService()
        result = await service.transfer_photo_usb(request.photo_path, request.device_udid)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return result
        
    except Exception as e:
        logger.error("❌ USB transfer failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"USB transfer failed: {str(e)}")

@router.post("/serve-local")
async def serve_photo_locally(request: LocalServerRequest):
    """
    Serve photo via local HTTP server
    
    Creates a local server that iPhone can access via WiFi.
    Returns the local URL that iPhone can use to download the photo.
    """
    try:
        service = PhotoTransferService()
        result = await service.serve_photo_locally(request.photo_path, request.port)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return result
        
    except Exception as e:
        logger.error("❌ Local server failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Local server failed: {str(e)}")

@router.get("/icloud-setup")
async def get_icloud_setup_instructions():
    """
    Get instructions for setting up iCloud Photos sync
    
    This is the most seamless solution - photos automatically sync
    between Mac and iPhone, so bot can access them directly.
    """
    try:
        service = PhotoTransferService()
        instructions = await service.setup_icloud_sync()
        return instructions
        
    except Exception as e:
        logger.error("❌ Failed to get iCloud instructions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get instructions: {str(e)}")

@router.post("/list-iphone-photos")
async def list_iphone_photos(request: PhotoListRequest):
    """
    List photos available on iPhone
    
    Returns identifiers that can be used with the posting functions.
    """
    try:
        service = PhotoTransferService()
        photos = await service.get_iphone_photos(request.device_udid)
        
        return {
            'success': True,
            'photos': photos,
            'count': len(photos)
        }
        
    except Exception as e:
        logger.error("❌ Failed to list iPhone photos", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list photos: {str(e)}")

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported photo formats"""
    try:
        service = PhotoTransferService()
        formats = service.get_supported_formats()
        
        return {
            'success': True,
            'formats': formats,
            'description': 'Supported photo formats for transfer'
        }
        
    except Exception as e:
        logger.error("❌ Failed to get supported formats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get formats: {str(e)}")

@router.get("/methods")
async def get_transfer_methods():
    """
    Get available photo transfer methods with pros/cons
    """
    methods = {
        'airdrop': {
            'name': 'AirDrop',
            'description': 'Native Mac/iPhone wireless transfer',
            'pros': [
                'Built into macOS/iOS',
                'No setup required',
                'Fast over WiFi',
                'User-friendly'
            ],
            'cons': [
                'Requires manual iPhone selection',
                'Both devices must be nearby',
                'Requires WiFi/Bluetooth'
            ],
            'requirements': [
                'Mac and iPhone on same WiFi network',
                'Bluetooth enabled on both devices',
                'AirDrop enabled in Control Center'
            ]
        },
        'usb': {
            'name': 'USB Transfer',
            'description': 'Direct transfer via USB cable',
            'pros': [
                'Direct connection',
                'No WiFi required',
                'Automated transfer'
            ],
            'cons': [
                'Requires libimobiledevice',
                'Complex setup',
                'iPhone must be trusted'
            ],
            'requirements': [
                'iPhone connected via USB',
                'Device trusted on Mac',
                'brew install libimobiledevice'
            ]
        },
        'local_server': {
            'name': 'Local HTTP Server',
            'description': 'Serve photos via local web server',
            'pros': [
                'Simple implementation',
                'Works over WiFi',
                'No special software needed'
            ],
            'cons': [
                'Requires manual download on iPhone',
                'Not fully automated',
                'Temporary server needed'
            ],
            'requirements': [
                'Both devices on same WiFi network',
                'iPhone Safari or photo app'
            ]
        },
        'icloud': {
            'name': 'iCloud Photos Sync',
            'description': 'Automatic sync via iCloud',
            'pros': [
                'Fully automated',
                'No manual transfer needed',
                'Always available',
                'Works with original quality'
            ],
            'cons': [
                'Requires iCloud storage',
                'Initial sync takes time',
                'Requires Apple ID'
            ],
            'requirements': [
                'iCloud Photos enabled on both devices',
                'Sufficient iCloud storage',
                'Internet connection for initial sync'
            ]
        }
    }
    
    return {
        'success': True,
        'methods': methods,
        'recommended': 'icloud',
        'fallback': 'airdrop'
    }
