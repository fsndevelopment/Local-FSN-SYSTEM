"""
Integrated Photo Posting Service
Combines photo cleaning, ngrok serving, and iPhone posting
"""
import os
import random
import asyncio
import structlog
import shutil
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

# Import your existing components
import sys
sys.path.append('/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main/USEFUL SCRIPTS')
sys.path.append('/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main/CLEANER')

from ngrok_handler import NgrokHandler
from cleaner import clean_metadata_and_modify_image

logger = structlog.get_logger()

class IntegratedPhotoService:
    """Complete photo posting service with cleaning and ngrok serving"""
    
    def __init__(self):
        self.active_handlers = {}  # Track active ngrok handlers
        self.temp_dirs = {}  # Track temporary directories
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.heic']
        
    async def process_photo_post(self, 
                               photos_folder: str, 
                               captions_file: Optional[str] = None,
                               device_udid: str = None,
                               ngrok_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete photo posting workflow:
        1. Select random photo from folder
        2. Clean photo (remove metadata, slight modifications)
        3. Create ngrok tunnel to serve photo
        4. Return photo URL and caption for iPhone to use
        """
        result = {'success': False, 'message': '', 'photo_url': '', 'caption': ''}
        
        try:
            logger.info("🚀 Starting integrated photo posting workflow", 
                       photos_folder=photos_folder, device_udid=device_udid)
            
            # Step 1: Select random photo from folder
            photo_path = await self._select_random_photo(photos_folder)
            if not photo_path:
                result['message'] = f"No photos found in folder: {photos_folder}"
                return result
            
            logger.info("📸 Selected photo", photo_path=photo_path)
            
            # Step 2: Clean the photo
            cleaned_photo_path = await self._clean_photo(photo_path, device_udid)
            if not cleaned_photo_path:
                result['message'] = "Failed to clean photo"
                return result
            
            logger.info("🧹 Photo cleaned", cleaned_path=cleaned_photo_path)
            
            # Step 3: Create ngrok tunnel to serve the photo
            if not ngrok_token:
                result['message'] = "No ngrok token provided - photo posting requires ngrok token for this device"
                return result
                
            photo_url = await self._serve_photo_via_ngrok(cleaned_photo_path, device_udid, ngrok_token)
            if not photo_url:
                result['message'] = "Failed to create photo serving tunnel"
                return result
            
            logger.info("🌐 Photo served via ngrok", url=photo_url)
            
            # Step 4: Get random caption if captions file provided
            caption = await self._get_random_caption(captions_file)
            
            result = {
                'success': True,
                'message': 'Photo processed and ready for posting',
                'photo_url': photo_url,
                'caption': caption,
                'original_photo': photo_path,
                'cleaned_photo': cleaned_photo_path
            }
            
            logger.info("✅ Photo posting workflow completed", photo_url=photo_url)
            return result
            
        except Exception as e:
            logger.error("❌ Photo posting workflow failed", error=str(e))
            result['message'] = f"Workflow failed: {str(e)}"
            return result
    
    async def _select_random_photo(self, photos_folder: str) -> Optional[str]:
        """Select a random photo from the specified folder"""
        try:
            # Handle relative paths - look in common locations
            search_paths = []
            
            if os.path.isabs(photos_folder):
                # Absolute path - use as is
                search_paths.append(photos_folder)
            else:
                # Relative path - search in common locations
                base_paths = [
                    "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main",
                    "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main",
                    "/Users/jacqubsf/Desktop",
                    "/Users/jacqubsf/Downloads",
                    os.getcwd(),  # Current working directory
                ]
                
                for base_path in base_paths:
                    full_path = os.path.join(base_path, photos_folder)
                    search_paths.append(full_path)
            
            # Try each path until we find one that exists
            actual_photos_folder = None
            for path in search_paths:
                if os.path.exists(path):
                    actual_photos_folder = path
                    logger.info("📁 Found photos folder", original=photos_folder, actual=actual_photos_folder)
                    break
            
            if not actual_photos_folder:
                logger.error("Photos folder not found in any search location", 
                           folder=photos_folder, 
                           searched_paths=search_paths)
                return None
            
            # Get all image files from the found folder
            photo_files = []
            for ext in self.supported_formats:
                pattern = f"*{ext}"
                photo_files.extend(Path(actual_photos_folder).glob(pattern))
                # Also check uppercase extensions
                pattern_upper = f"*{ext.upper()}"
                photo_files.extend(Path(actual_photos_folder).glob(pattern_upper))
            
            if not photo_files:
                logger.error("No photos found in folder", folder=actual_photos_folder)
                return None
            
            # Select random photo
            selected_photo = random.choice(photo_files)
            logger.info("📷 Random photo selected", 
                       photo=str(selected_photo), 
                       total_photos=len(photo_files))
            
            return str(selected_photo)
            
        except Exception as e:
            logger.error("Failed to select random photo", error=str(e))
            return None
    
    async def _clean_photo(self, photo_path: str, device_udid: str) -> Optional[str]:
        """Clean photo using your cleaner script"""
        try:
            # Create temporary directory for this device
            if device_udid not in self.temp_dirs:
                temp_dir = tempfile.mkdtemp(prefix=f"fsn_photos_{device_udid}_")
                self.temp_dirs[device_udid] = temp_dir
                logger.info("Created temp directory", temp_dir=temp_dir, device=device_udid)
            
            temp_dir = self.temp_dirs[device_udid]
            
            # Generate unique filename for cleaned photo
            original_name = Path(photo_path).stem
            cleaned_filename = f"{original_name}_cleaned_{random.randint(1000, 9999)}.jpg"
            cleaned_path = os.path.join(temp_dir, cleaned_filename)
            
            # Use your cleaner function to clean the photo
            logger.info("🧹 Cleaning photo", original=photo_path, cleaned=cleaned_path)
            clean_metadata_and_modify_image(photo_path, cleaned_path)
            
            if os.path.exists(cleaned_path):
                logger.info("✅ Photo cleaned successfully", cleaned_path=cleaned_path)
                return cleaned_path
            else:
                logger.error("Cleaned photo was not created", cleaned_path=cleaned_path)
                return None
                
        except Exception as e:
            logger.error("Failed to clean photo", error=str(e))
            return None
    
    async def _serve_photo_via_ngrok(self, photo_path: str, device_udid: str, ngrok_token: str) -> Optional[str]:
        """Serve photo via ngrok using your NgrokHandler"""
        try:
            # Get the directory containing the photo
            photo_dir = os.path.dirname(photo_path)
            photo_filename = os.path.basename(photo_path)
            
            # Create unique ngrok handler for this device
            handler_key = f"{device_udid}_{random.randint(1000, 9999)}"
            
            # Stop any existing handler for this device
            await self._cleanup_device_handlers(device_udid)
            
            # Create new ngrok handler
            logger.info("🌐 Creating ngrok tunnel", directory=photo_dir, device=device_udid)
            
            # Create a temporary ngrok tokens file for this device
            import tempfile
            import json
            
            # Create temporary tokens file with device-specific token
            temp_tokens_file = os.path.join(photo_dir, "ngrok_tokens.json")
            tokens_data = {"default": ngrok_token}
            
            with open(temp_tokens_file, 'w') as f:
                json.dump(tokens_data, f)
            
            logger.info("🔑 Created temporary ngrok tokens file", tokens_file=temp_tokens_file)
            
            # Use your NgrokHandler class with device-specific token
            # Change to photo directory so ngrok handler can find the tokens file
            original_cwd = os.getcwd()
            logger.info("🔧 Changing working directory", 
                       from_dir=original_cwd, 
                       to_dir=photo_dir,
                       tokens_file_exists=os.path.exists(temp_tokens_file))
            os.chdir(photo_dir)
            
            try:
                # Verify tokens file exists in current directory
                current_tokens_path = os.path.join(os.getcwd(), "ngrok_tokens.json")
                logger.info("🔍 Checking tokens file", 
                           current_dir=os.getcwd(),
                           tokens_path=current_tokens_path,
                           file_exists=os.path.exists(current_tokens_path))
                
                handler = NgrokHandler(directory=photo_dir, token_name="default")
                handler.start_server_and_tunnel()
            finally:
                # Always restore original working directory
                os.chdir(original_cwd)
            
            public_url = handler.get_public_url()
            if not public_url:
                logger.error("Failed to get ngrok public URL")
                return None
            
            # Store handler for cleanup later
            self.active_handlers[handler_key] = {
                'handler': handler,
                'device_udid': device_udid,
                'photo_path': photo_path
            }
            
            # Construct full photo URL
            photo_url = f"{public_url}/{photo_filename}"
            
            logger.info("✅ Photo served via ngrok", 
                       public_url=public_url, 
                       photo_url=photo_url,
                       device=device_udid)
            
            return photo_url
            
        except Exception as e:
            logger.error("Failed to serve photo via ngrok", error=str(e))
            return None
    
    async def _get_random_caption(self, captions_file: Optional[str]) -> str:
        """Get random caption from Excel file or return default"""
        if not captions_file or not os.path.exists(captions_file):
            default_captions = [
                "Living my best life! ✨",
                "Another day, another adventure 🌟",
                "Grateful for this moment 🙏",
                "Making memories that last forever 📸",
                "Life is beautiful 🌈",
                "Chasing dreams and catching sunsets 🌅",
                "Good vibes only 😊",
                "Creating my own sunshine ☀️"
            ]
            return random.choice(default_captions)
        
        try:
            # Try to read Excel file for captions
            import pandas as pd
            
            # Read the Excel file
            df = pd.read_excel(captions_file)
            
            # Assume captions are in the first column
            if not df.empty:
                captions = df.iloc[:, 0].dropna().tolist()
                if captions:
                    selected_caption = random.choice(captions)
                    logger.info("📝 Selected caption from file", 
                               caption=selected_caption[:50] + "..." if len(selected_caption) > 50 else selected_caption)
                    return str(selected_caption)
            
            logger.warning("No captions found in Excel file, using default")
            return "Posted via FSN Bot 🤖"
            
        except Exception as e:
            logger.error("Failed to read captions file", error=str(e))
            return "Posted via FSN Bot 🤖"
    
    async def download_photo_to_iphone(self, photo_url: str, device_udid: str) -> Dict[str, Any]:
        """
        Instruct iPhone to download photo from ngrok URL
        This would be called by your Appium script
        """
        result = {'success': False, 'message': ''}
        
        try:
            logger.info("📱 Instructing iPhone to download photo", 
                       url=photo_url, device=device_udid)
            
            # This would be implemented in your Appium script
            # For now, return success assuming the download works
            result = {
                'success': True,
                'message': 'Photo download instruction sent to iPhone',
                'photo_url': photo_url,
                'device_udid': device_udid
            }
            
            return result
            
        except Exception as e:
            logger.error("Failed to download photo to iPhone", error=str(e))
            result['message'] = f"Download failed: {str(e)}"
            return result
    
    async def _cleanup_device_handlers(self, device_udid: str):
        """Cleanup ngrok handlers for a specific device"""
        try:
            handlers_to_remove = []
            
            for handler_key, handler_info in self.active_handlers.items():
                if handler_info['device_udid'] == device_udid:
                    try:
                        handler_info['handler'].stop_server_and_tunnel()
                        logger.info("🧹 Cleaned up ngrok handler", 
                                   handler_key=handler_key, device=device_udid)
                    except Exception as e:
                        logger.warning("Failed to cleanup handler", 
                                     handler_key=handler_key, error=str(e))
                    handlers_to_remove.append(handler_key)
            
            # Remove cleaned up handlers
            for handler_key in handlers_to_remove:
                del self.active_handlers[handler_key]
                
        except Exception as e:
            logger.error("Failed to cleanup device handlers", error=str(e))
    
    async def cleanup_all(self):
        """Cleanup all active handlers and temporary directories"""
        try:
            # Stop all ngrok handlers
            for handler_key, handler_info in self.active_handlers.items():
                try:
                    handler_info['handler'].stop_server_and_tunnel()
                    logger.info("🧹 Stopped ngrok handler", handler_key=handler_key)
                except Exception as e:
                    logger.warning("Failed to stop handler", handler_key=handler_key, error=str(e))
            
            self.active_handlers.clear()
            
            # Clean up temporary directories
            for device_udid, temp_dir in self.temp_dirs.items():
                try:
                    shutil.rmtree(temp_dir)
                    logger.info("🧹 Cleaned up temp directory", temp_dir=temp_dir, device=device_udid)
                except Exception as e:
                    logger.warning("Failed to cleanup temp dir", temp_dir=temp_dir, error=str(e))
            
            self.temp_dirs.clear()
            logger.info("✅ All cleanup completed")
            
        except Exception as e:
            logger.error("Failed to cleanup all resources", error=str(e))
    
    def get_active_handlers_info(self) -> Dict[str, Any]:
        """Get information about active handlers"""
        return {
            'active_handlers_count': len(self.active_handlers),
            'active_devices': list(set(h['device_udid'] for h in self.active_handlers.values())),
            'temp_directories': list(self.temp_dirs.keys())
        }

# Global instance
integrated_photo_service = IntegratedPhotoService()
