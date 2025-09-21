"""
FSN Appium Farm - Client-Side License Enforcement
================================================

Handles license verification, hardware binding, and enforcement for the main API.
Integrates with the centralized license server for validation.
"""

import asyncio
import hashlib
import json
import platform
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import base64
import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

class LicenseStatus(BaseModel):
    """License status model matching server response"""
    status: str  # VALID, EXPIRED, REVOKED, INVALID
    client_id: str
    max_devices: int
    devices_used: int
    expiry: datetime
    features: List[str]
    days_remaining: int
    grace_period: bool = False
    message: str

class LicenseManager:
    """Manages license verification and enforcement"""
    
    def __init__(self, license_server_url: str, client_id: str, license_key: str):
        self.license_server_url = license_server_url
        self.client_id = client_id
        self.license_key = license_key
        self.hardware_hash = self._generate_hardware_hash()
        self.last_check: Optional[datetime] = None
        self.license_status: Optional[LicenseStatus] = None
        self.grace_period_start: Optional[datetime] = None
        
        # Embed public key (in production, this would be compiled in)
        self.public_key_b64 = None  # Will be fetched from server
        
        logger.info("🔐 License Manager initialized", 
                   client_id=client_id, hardware_hash=self.hardware_hash[:16])
    
    def _generate_hardware_hash(self) -> str:
        """Generate hardware fingerprint for binding (deployment-aware)"""
        identifiers = []
        
        try:
            # Mac address (works on all platforms)
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0, 2*6, 2)][::-1])
            identifiers.append(f"mac:{mac}")
            
            # System info
            identifiers.append(f"platform:{platform.platform()}")
            identifiers.append(f"processor:{platform.processor()}")
            identifiers.append(f"machine:{platform.machine()}")
            
            # Platform-specific hardware identifiers
            if platform.system() == "Darwin":
                # macOS - get serial number
                try:
                    result = subprocess.run(
                        ["system_profiler", "SPHardwareDataType"], 
                        capture_output=True, text=True, timeout=10
                    )
                    for line in result.stdout.split('\n'):
                        if 'Serial Number' in line:
                            serial = line.split(':')[-1].strip()
                            identifiers.append(f"serial:{serial}")
                            break
                except:
                    pass
                    
            elif platform.system() == "Linux":
                # Linux VPS - get machine-id and DMI info
                try:
                    # Machine ID (unique per installation)
                    with open('/etc/machine-id', 'r') as f:
                        machine_id = f.read().strip()
                        identifiers.append(f"machine_id:{machine_id}")
                except:
                    pass
                
                try:
                    # DMI System UUID (if available)
                    result = subprocess.run(
                        ["dmidecode", "-s", "system-uuid"], 
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        uuid_val = result.stdout.strip()
                        identifiers.append(f"dmi_uuid:{uuid_val}")
                except:
                    pass
                
                try:
                    # CPU info
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if 'Serial' in line:
                                serial = line.split(':')[-1].strip()
                                identifiers.append(f"cpu_serial:{serial}")
                                break
                except:
                    pass
                    
            elif platform.system() == "Windows":
                # Windows - get system UUID
                try:
                    result = subprocess.run(
                        ["wmic", "csproduct", "get", "UUID"], 
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        uuid_val = lines[1].strip()
                        identifiers.append(f"win_uuid:{uuid_val}")
                except:
                    pass
            
            # Add hostname for server identification
            identifiers.append(f"hostname:{platform.node()}")
            
            # Docker container detection
            if os.path.exists('/.dockerenv'):
                identifiers.append("container:docker")
            
            # Create hash
            combined = "|".join(sorted(identifiers))
            hw_hash = hashlib.sha256(combined.encode()).hexdigest()
            
            logger.info("🔍 Hardware fingerprint generated", 
                       platform=platform.system(),
                       identifiers_count=len(identifiers),
                       hash_preview=hw_hash[:16])
            
            return hw_hash
            
        except Exception as e:
            logger.error("Failed to generate hardware hash", error=str(e))
            # Fallback to deterministic UUID based on hostname + MAC
            fallback_data = f"{platform.node()}:{uuid.getnode()}"
            return hashlib.sha256(fallback_data.encode()).hexdigest()
    
    def _add_client_watermark(self, data: Dict) -> Dict:
        """Add client watermark to logs/jobs for traceability"""
        watermark = {
            "client_id": self.client_id,
            "hw_hash": self.hardware_hash[:8],  # Partial hash for identification
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if isinstance(data, dict):
            data["_fsn_license"] = watermark
        
        return data
    
    async def _make_license_request(self, endpoint: str, payload: Dict) -> Optional[Dict]:
        """Make request to license server with retry logic"""
        url = f"{self.license_server_url}{endpoint}"
        
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload)
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.warning("License server error", 
                                     status=response.status_code, 
                                     response=response.text,
                                     attempt=attempt + 1)
                        
            except Exception as e:
                logger.warning("License server connection failed", 
                             error=str(e), attempt=attempt + 1)
                
                if attempt < 2:  # Retry with exponential backoff
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def verify_license(self, force_check: bool = False) -> LicenseStatus:
        """Verify license with server (cached for 24h unless forced)"""
        
        # Check cache (24h validity)
        if (not force_check and self.license_status and self.last_check and 
            (datetime.utcnow() - self.last_check).total_seconds() < 86400):
            logger.debug("Using cached license status", status=self.license_status.status)
            return self.license_status
        
        logger.info("🔍 Verifying license with server...")
        
        # Make verification request
        payload = {
            "license_key": self.license_key,
            "hardware_hash": self.hardware_hash,
            "client_id": self.client_id
        }
        
        response = await self._make_license_request("/license/verify", payload)
        
        if response:
            self.license_status = LicenseStatus(**response)
            self.last_check = datetime.utcnow()
            
            logger.info("✅ License verification complete", 
                       status=self.license_status.status,
                       days_remaining=self.license_status.days_remaining,
                       message=self.license_status.message)
        else:
            # Server unavailable - use grace period logic
            if self.license_status:
                logger.warning("⚠️ License server unavailable, using cached status")
                return self.license_status
            else:
                # No cached status and server unavailable - assume invalid
                logger.error("❌ License server unavailable and no cached status")
                self.license_status = LicenseStatus(
                    status="INVALID",
                    client_id=self.client_id,
                    max_devices=0,
                    devices_used=0,
                    expiry=datetime.utcnow(),
                    features=[],
                    days_remaining=0,
                    message="License server unavailable"
                )
        
        return self.license_status
    
    async def activate_license(self) -> LicenseStatus:
        """Activate license on first use"""
        logger.info("🔓 Activating license...")
        
        # Get device info for binding
        device_info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "activated_at": datetime.utcnow().isoformat()
        }
        
        payload = {
            "license_key": self.license_key,
            "hardware_hash": self.hardware_hash,
            "client_id": self.client_id,
            "device_info": device_info
        }
        
        response = await self._make_license_request("/license/activate", payload)
        
        if response:
            self.license_status = LicenseStatus(**response)
            self.last_check = datetime.utcnow()
            
            logger.info("✅ License activated successfully", 
                       client_id=self.client_id,
                       max_devices=self.license_status.max_devices,
                       features=self.license_status.features)
        else:
            logger.error("❌ License activation failed")
            raise RuntimeError("Failed to activate license")
        
        return self.license_status
    
    def is_license_valid(self) -> bool:
        """Check if license allows operation"""
        if not self.license_status:
            return False
        
        if self.license_status.status == "VALID":
            return True
        
        if self.license_status.status == "EXPIRED" and self.license_status.grace_period:
            # Check if within 7-day grace period
            if not self.grace_period_start:
                self.grace_period_start = datetime.utcnow()
            
            grace_days = (datetime.utcnow() - self.grace_period_start).days
            if grace_days <= 7:
                logger.warning(f"⚠️ Operating in grace period ({grace_days}/7 days)")
                return True
        
        return False
    
    def get_license_info(self) -> Dict:
        """Get license information for UI display"""
        if not self.license_status:
            return {
                "status": "UNKNOWN",
                "message": "License not verified",
                "client_id": self.client_id,
                "features": []
            }
        
        info = {
            "status": self.license_status.status,
            "message": self.license_status.message,
            "client_id": self.license_status.client_id,
            "features": self.license_status.features,
            "max_devices": self.license_status.max_devices,
            "devices_used": self.license_status.devices_used,
            "expiry": self.license_status.expiry.isoformat(),
            "days_remaining": self.license_status.days_remaining,
            "grace_period": self.license_status.grace_period
        }
        
        # Add watermark
        return self._add_client_watermark(info)
    
    def enforce_license_check(self):
        """Enforce license validity - raises exception if invalid"""
        if not self.is_license_valid():
            if self.license_status:
                message = f"License {self.license_status.status.lower()}: {self.license_status.message}"
            else:
                message = "No valid license found"
            
            logger.error("🚫 License enforcement failed", message=message)
            raise RuntimeError(f"FSN Appium Farm: {message}")
    
    async def start_background_verification(self):
        """Start background task for periodic license verification"""
        logger.info("🔄 Starting background license verification (24h intervals)")
        
        while True:
            try:
                await asyncio.sleep(86400)  # 24 hours
                await self.verify_license(force_check=True)
                
                # Check if license became invalid
                if not self.is_license_valid():
                    logger.error("🚫 License became invalid during background check")
                    # In production, this could trigger graceful shutdown
                    
            except Exception as e:
                logger.error("Background license verification failed", error=str(e))
                await asyncio.sleep(3600)  # Retry in 1 hour on error


# Global license manager instance
_license_manager: Optional[LicenseManager] = None

def init_license_manager(license_server_url: str, client_id: str, license_key: str) -> LicenseManager:
    """Initialize global license manager"""
    global _license_manager
    _license_manager = LicenseManager(license_server_url, client_id, license_key)
    return _license_manager

def get_license_manager() -> LicenseManager:
    """Get global license manager instance"""
    if not _license_manager:
        raise RuntimeError("License manager not initialized")
    return _license_manager

# Decorators for license enforcement
def require_license(func):
    """Decorator to enforce license check on API endpoints"""
    async def wrapper(*args, **kwargs):
        license_manager = get_license_manager()
        license_manager.enforce_license_check()
        return await func(*args, **kwargs)
    
    return wrapper

def require_feature(feature: str):
    """Decorator to enforce feature-specific licensing"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            license_manager = get_license_manager()
            license_manager.enforce_license_check()
            
            if feature not in license_manager.license_status.features:
                raise RuntimeError(f"Feature '{feature}' not licensed")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
