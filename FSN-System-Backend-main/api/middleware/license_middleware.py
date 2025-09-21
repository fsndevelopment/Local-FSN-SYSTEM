"""
License Validation Middleware

Validates license keys for all API operations to ensure proper access control
"""

import structlog
from fastapi import HTTPException, Depends, Header
from typing import Optional
import httpx
import os

logger = structlog.get_logger()

# License management server URL
LICENSE_SERVER_URL = os.getenv("LICENSE_SERVER_URL", "https://fsn-system-license.onrender.com")

async def validate_license(license_key: str, device_id: str) -> dict:
    """
    Validate license with the license management server
    
    Args:
        license_key: The license key to validate
        device_id: The device ID making the request
        
    Returns:
        dict: License information if valid
        
    Raises:
        HTTPException: If license is invalid or expired
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LICENSE_SERVER_URL}/api/v1/license/validate",
                json={
                    "license_key": license_key,
                    "device_id": device_id
                },
                timeout=5.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired license"
                )
            
            data = response.json()
            
            if not data.get("valid", False):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired license"
                )
            
            return data
            
    except httpx.RequestError as e:
        logger.error("Failed to validate license", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="License validation service unavailable"
        )

def get_license_key(
    x_license_key: Optional[str] = Header(None, alias="X-License-Key")
) -> str:
    """
    Extract license key from request headers
    
    Args:
        x_license_key: License key from X-License-Key header
        
    Returns:
        str: License key
        
    Raises:
        HTTPException: If license key is missing
    """
    if not x_license_key:
        raise HTTPException(
            status_code=400,
            detail="License key required. Please provide X-License-Key header."
        )
    
    return x_license_key

def get_device_id(
    x_device_id: Optional[str] = Header(None, alias="X-Device-ID")
) -> str:
    """
    Extract device ID from request headers
    
    Args:
        x_device_id: Device ID from X-Device-ID header
        
    Returns:
        str: Device ID
        
    Raises:
        HTTPException: If device ID is missing
    """
    if not x_device_id:
        raise HTTPException(
            status_code=400,
            detail="Device ID required. Please provide X-Device-ID header."
        )
    
    return x_device_id

async def require_valid_license(
    license_key: str = Depends(get_license_key),
    device_id: str = Depends(get_device_id)
) -> dict:
    """
    Dependency that requires a valid license for API access
    
    Args:
        license_key: License key from headers
        device_id: Device ID from headers
        
    Returns:
        dict: Validated license information including original license_key and device_id
        
    Raises:
        HTTPException: If license is invalid or expired
    """
    # Validate the license with the license server
    license_data = await validate_license(license_key, device_id)
    
    # Return the license data with the original license_key and device_id
    return {
        "license_key": license_key,
        "device_id": device_id,
        "valid": True,
        "license_data": license_data
    }
