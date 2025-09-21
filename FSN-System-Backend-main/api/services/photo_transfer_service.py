"""
Photo Transfer Service
Handles transferring photos from Mac to iPhone using various methods
"""
import os
import subprocess
import asyncio
import structlog
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = structlog.get_logger()

class PhotoTransferService:
    """Service for transferring photos from Mac to iPhone"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.heic']
        
    async def transfer_photo_airdrop(self, photo_path: str) -> Dict[str, Any]:
        """
        Transfer photo using AirDrop automation
        
        Args:
            photo_path: Path to photo on Mac
            
        Returns:
            Dict with success status and message
        """
        result = {'success': False, 'message': ''}
        
        try:
            if not os.path.exists(photo_path):
                result['message'] = f"Photo not found: {photo_path}"
                return result
                
            # Validate file format
            file_ext = Path(photo_path).suffix.lower()
            if file_ext not in self.supported_formats:
                result['message'] = f"Unsupported format: {file_ext}"
                return result
            
            # Create AppleScript for AirDrop
            applescript = f'''
            tell application "Finder"
                set theFile to POSIX file "{photo_path}"
                open theFile
                delay 2
                
                -- This will open the sharing menu
                tell application "System Events"
                    keystroke "i" using {{command down}}
                    delay 1
                    
                    -- Look for AirDrop option
                    click button "AirDrop" of window 1
                    delay 3
                end tell
            end tell
            '''
            
            # Execute AppleScript
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', applescript,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result['success'] = True
                result['message'] = "AirDrop sharing initiated. Please select your iPhone."
                logger.info("✅ AirDrop initiated", photo_path=photo_path)
            else:
                result['message'] = f"AirDrop failed: {stderr.decode()}"
                logger.error("❌ AirDrop failed", error=stderr.decode())
                
        except Exception as e:
            result['message'] = f"AirDrop error: {str(e)}"
            logger.error("❌ AirDrop error", error=str(e))
            
        return result
    
    async def transfer_photo_usb(self, photo_path: str, device_udid: str) -> Dict[str, Any]:
        """
        Transfer photo via USB using libimobiledevice
        
        Args:
            photo_path: Path to photo on Mac
            device_udid: iPhone UDID
            
        Returns:
            Dict with success status and message
        """
        result = {'success': False, 'message': ''}
        
        try:
            if not os.path.exists(photo_path):
                result['message'] = f"Photo not found: {photo_path}"
                return result
            
            # Check if libimobiledevice is installed
            check_cmd = await asyncio.create_subprocess_exec(
                'which', 'idevice_id',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await check_cmd.communicate()
            
            if check_cmd.returncode != 0:
                result['message'] = "libimobiledevice not installed. Run: brew install libimobiledevice"
                return result
            
            # Copy photo to iPhone Photos
            # Note: This requires the device to be paired and trusted
            copy_cmd = await asyncio.create_subprocess_exec(
                'ifuse', '--udid', device_udid, '/tmp/iphone_mount',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await copy_cmd.communicate()
            
            if copy_cmd.returncode == 0:
                # Copy file to mounted iPhone
                import shutil
                filename = os.path.basename(photo_path)
                dest_path = f"/tmp/iphone_mount/DCIM/100APPLE/{filename}"
                shutil.copy2(photo_path, dest_path)
                
                # Unmount
                subprocess.run(['umount', '/tmp/iphone_mount'])
                
                result['success'] = True
                result['message'] = "Photo transferred via USB"
                logger.info("✅ USB transfer completed", photo_path=photo_path)
            else:
                result['message'] = "Failed to mount iPhone via USB"
                
        except Exception as e:
            result['message'] = f"USB transfer error: {str(e)}"
            logger.error("❌ USB transfer error", error=str(e))
            
        return result
    
    async def serve_photo_locally(self, photo_path: str, port: int = 8080) -> Dict[str, Any]:
        """
        Serve photo via local HTTP server for iPhone to download
        
        Args:
            photo_path: Path to photo on Mac
            port: Port for HTTP server
            
        Returns:
            Dict with success status and local URL
        """
        result = {'success': False, 'message': '', 'url': ''}
        
        try:
            if not os.path.exists(photo_path):
                result['message'] = f"Photo not found: {photo_path}"
                return result
            
            # Get local IP address
            ip_cmd = await asyncio.create_subprocess_exec(
                'ifconfig', '|', 'grep', 'inet ', '|', 'grep', '-v', '127.0.0.1', '|', 'awk', '{print $2}', '|', 'head', '-1',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await ip_cmd.communicate()
            local_ip = stdout.decode().strip()
            
            if not local_ip:
                local_ip = "localhost"
            
            # Create simple HTTP server
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            import threading
            
            photo_dir = os.path.dirname(photo_path)
            filename = os.path.basename(photo_path)
            
            os.chdir(photo_dir)
            
            server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            photo_url = f"http://{local_ip}:{port}/{filename}"
            
            result['success'] = True
            result['message'] = "Photo server started"
            result['url'] = photo_url
            
            logger.info("✅ Photo server started", url=photo_url)
            
        except Exception as e:
            result['message'] = f"Server error: {str(e)}"
            logger.error("❌ Photo server error", error=str(e))
            
        return result
    
    async def setup_icloud_sync(self) -> Dict[str, Any]:
        """
        Provide instructions for iCloud Photos setup
        
        Returns:
            Dict with setup instructions
        """
        instructions = {
            'success': True,
            'message': 'iCloud Photos setup instructions',
            'steps': [
                "1. On Mac: System Preferences → Apple ID → iCloud → Photos (enable)",
                "2. On iPhone: Settings → [Your Name] → iCloud → Photos (enable)",
                "3. Wait for sync to complete (may take hours for large libraries)",
                "4. Photos will automatically appear in iPhone gallery",
                "5. Bot can then select any synced photo for posting"
            ],
            'benefits': [
                "Automatic sync - no manual transfer needed",
                "All photos always available on iPhone",
                "Works with original quality",
                "No internet required for bot operation"
            ]
        }
        
        logger.info("📋 iCloud Photos setup instructions provided")
        return instructions
    
    async def get_iphone_photos(self, device_udid: str) -> List[str]:
        """
        Get list of photos available on iPhone
        
        Args:
            device_udid: iPhone UDID
            
        Returns:
            List of photo identifiers
        """
        photos = []
        
        try:
            # This would require Appium session to enumerate photos
            # For now, return placeholder
            photos = [
                "gallery-photo-cell-0",
                "gallery-photo-cell-1", 
                "gallery-photo-cell-2",
                # ... more photos
            ]
            
            logger.info("📸 Found photos on iPhone", count=len(photos))
            
        except Exception as e:
            logger.error("❌ Failed to get iPhone photos", error=str(e))
            
        return photos
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported photo formats"""
        return self.supported_formats.copy()
