"""
Crane Container Service
Manages Crane containers for jailbroken device account switching
"""

import asyncio
import logging
import subprocess
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiofiles

logger = logging.getLogger(__name__)

class CraneContainerService:
    """
    Service for managing Crane containers on jailbroken devices
    Handles container creation, switching, deletion, and state management
    """
    
    def __init__(self):
        self.crane_binary = "/usr/bin/crane"  # Default Crane binary path
        self.container_config_path = "/var/mobile/Library/Preferences/crane_containers.json"
        self.containers_dir = "/var/mobile/Containers/Data/Application"
        
    async def is_crane_available(self, device_udid: str) -> bool:
        """Check if Crane is available on the device"""
        try:
            # Use SSH to check if Crane is installed
            result = await self._ssh_execute(device_udid, f"which {self.crane_binary}")
            return result.get("success", False) and result.get("output", "").strip() != ""
        except Exception as e:
            logger.error(f"Error checking Crane availability: {e}")
            return False
    
    async def get_installed_containers(self, device_udid: str) -> List[Dict[str, Any]]:
        """Get list of all installed Crane containers"""
        try:
            result = await self._ssh_execute(device_udid, f"{self.crane_binary} list")
            if not result.get("success", False):
                return []
            
            containers = []
            output_lines = result.get("output", "").strip().split('\n')
            
            for line in output_lines[1:]:  # Skip header
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        container_id = parts[0]
                        container_name = parts[1]
                        status = parts[2]
                        
                        containers.append({
                            "id": container_id,
                            "name": container_name,
                            "status": status,
                            "platform": self._detect_platform_from_name(container_name)
                        })
            
            return containers
            
        except Exception as e:
            logger.error(f"Error getting installed containers: {e}")
            return []
    
    async def create_container(self, device_udid: str, container_name: str, platform: str, bundle_id: str) -> Dict[str, Any]:
        """Create a new Crane container for an account"""
        try:
            # Generate unique container name
            full_container_name = f"{platform}_{container_name}_{self._generate_container_id()}"
            
            # Create container using Crane
            cmd = f"{self.crane_binary} create {full_container_name} {bundle_id}"
            result = await self._ssh_execute(device_udid, cmd)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create container: {result.get('error', 'Unknown error')}",
                    "data": {}
                }
            
            # Store container metadata
            container_info = {
                "id": full_container_name,
                "name": container_name,
                "platform": platform,
                "bundle_id": bundle_id,
                "created_at": self._get_current_timestamp(),
                "status": "created"
            }
            
            await self._save_container_metadata(device_udid, full_container_name, container_info)
            
            logger.info(f"Created Crane container {full_container_name} for {platform} account {container_name}")
            
            return {
                "success": True,
                "message": f"Container {full_container_name} created successfully",
                "data": {
                    "container": container_info
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating container: {e}")
            return {
                "success": False,
                "message": f"Container creation failed: {str(e)}",
                "data": {}
            }
    
    async def switch_to_container(self, device_udid: str, container_id: str, platform: str) -> Dict[str, Any]:
        """Switch to a specific Crane container"""
        try:
            # Get container metadata
            container_info = await self._get_container_metadata(device_udid, container_id)
            if not container_info:
                return {
                    "success": False,
                    "message": f"Container {container_id} not found",
                    "data": {}
                }
            
            # Switch to container
            cmd = f"{self.crane_binary} switch {container_id}"
            result = await self._ssh_execute(device_udid, cmd)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to switch to container: {result.get('error', 'Unknown error')}",
                    "data": {}
                }
            
            # Update container status
            container_info["status"] = "active"
            container_info["last_switched"] = self._get_current_timestamp()
            await self._save_container_metadata(device_udid, container_id, container_info)
            
            # Launch the app in the container
            bundle_id = container_info.get("bundle_id")
            if bundle_id:
                launch_result = await self._launch_app_in_container(device_udid, bundle_id)
                if not launch_result.get("success", False):
                    logger.warning(f"Container switched but app launch failed: {launch_result.get('message')}")
            
            logger.info(f"Switched to Crane container {container_id} for {platform}")
            
            return {
                "success": True,
                "message": f"Successfully switched to container {container_id}",
                "data": {
                    "container": container_info,
                    "launch_result": launch_result
                }
            }
            
        except Exception as e:
            logger.error(f"Error switching to container: {e}")
            return {
                "success": False,
                "message": f"Container switch failed: {str(e)}",
                "data": {}
            }
    
    async def delete_container(self, device_udid: str, container_id: str) -> Dict[str, Any]:
        """Delete a Crane container"""
        try:
            # Delete container using Crane
            cmd = f"{self.crane_binary} delete {container_id}"
            result = await self._ssh_execute(device_udid, cmd)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to delete container: {result.get('error', 'Unknown error')}",
                    "data": {}
                }
            
            # Remove container metadata
            await self._delete_container_metadata(device_udid, container_id)
            
            logger.info(f"Deleted Crane container {container_id}")
            
            return {
                "success": True,
                "message": f"Container {container_id} deleted successfully",
                "data": {}
            }
            
        except Exception as e:
            logger.error(f"Error deleting container: {e}")
            return {
                "success": False,
                "message": f"Container deletion failed: {str(e)}",
                "data": {}
            }
    
    async def get_container_status(self, device_udid: str, container_id: str) -> Dict[str, Any]:
        """Get status of a specific container"""
        try:
            # Get container metadata
            container_info = await self._get_container_metadata(device_udid, container_id)
            if not container_info:
                return {
                    "success": False,
                    "message": f"Container {container_id} not found",
                    "data": {}
                }
            
            # Check if container is currently active
            cmd = f"{self.crane_binary} current"
            result = await self._ssh_execute(device_udid, cmd)
            
            is_active = False
            if result.get("success", False):
                current_container = result.get("output", "").strip()
                is_active = current_container == container_id
            
            container_info["is_active"] = is_active
            
            return {
                "success": True,
                "message": "Container status retrieved successfully",
                "data": {
                    "container": container_info
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return {
                "success": False,
                "message": f"Failed to get container status: {str(e)}",
                "data": {}
            }
    
    async def list_containers_for_platform(self, device_udid: str, platform: str) -> List[Dict[str, Any]]:
        """Get containers for a specific platform (Instagram/Threads)"""
        try:
            all_containers = await self.get_installed_containers(device_udid)
            platform_containers = [
                container for container in all_containers 
                if container.get("platform") == platform.lower()
            ]
            
            return platform_containers
            
        except Exception as e:
            logger.error(f"Error listing containers for platform {platform}: {e}")
            return []
    
    # Helper methods
    
    async def _ssh_execute(self, device_udid: str, command: str) -> Dict[str, Any]:
        """Execute command on device via SSH"""
        try:
            # Use SSH to execute command on device
            # This is a placeholder - implement with actual SSH client
            ssh_cmd = f"ssh root@{device_udid} '{command}'"
            
            process = await asyncio.create_subprocess_shell(
                ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else ""
            }
            
        except Exception as e:
            logger.error(f"SSH execution failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _launch_app_in_container(self, device_udid: str, bundle_id: str) -> Dict[str, Any]:
        """Launch app in the current container"""
        try:
            cmd = f"launchctl start {bundle_id}"
            result = await self._ssh_execute(device_udid, cmd)
            
            return {
                "success": result.get("success", False),
                "message": "App launched in container" if result.get("success") else f"App launch failed: {result.get('error')}",
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Error launching app in container: {e}")
            return {
                "success": False,
                "message": f"App launch failed: {str(e)}",
                "data": {}
            }
    
    def _detect_platform_from_name(self, container_name: str) -> str:
        """Detect platform from container name"""
        if "instagram" in container_name.lower():
            return "instagram"
        elif "threads" in container_name.lower():
            return "threads"
        else:
            return "unknown"
    
    def _generate_container_id(self) -> str:
        """Generate unique container ID"""
        import time
        import random
        return f"{int(time.time())}_{random.randint(1000, 9999)}"
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    async def _save_container_metadata(self, device_udid: str, container_id: str, metadata: Dict[str, Any]) -> None:
        """Save container metadata to device"""
        try:
            # Load existing metadata
            existing_data = await self._load_container_metadata(device_udid)
            existing_data[container_id] = metadata
            
            # Save updated metadata
            cmd = f"echo '{json.dumps(existing_data)}' > {self.container_config_path}"
            await self._ssh_execute(device_udid, cmd)
            
        except Exception as e:
            logger.error(f"Error saving container metadata: {e}")
    
    async def _get_container_metadata(self, device_udid: str, container_id: str) -> Optional[Dict[str, Any]]:
        """Get container metadata from device"""
        try:
            data = await self._load_container_metadata(device_udid)
            return data.get(container_id)
        except Exception as e:
            logger.error(f"Error getting container metadata: {e}")
            return None
    
    async def _load_container_metadata(self, device_udid: str) -> Dict[str, Any]:
        """Load all container metadata from device"""
        try:
            cmd = f"cat {self.container_config_path}"
            result = await self._ssh_execute(device_udid, cmd)
            
            if result.get("success", False) and result.get("output"):
                return json.loads(result.get("output"))
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error loading container metadata: {e}")
            return {}
    
    async def _delete_container_metadata(self, device_udid: str, container_id: str) -> None:
        """Delete container metadata from device"""
        try:
            # Load existing metadata
            existing_data = await self._load_container_metadata(device_udid)
            
            # Remove container from metadata
            if container_id in existing_data:
                del existing_data[container_id]
                
                # Save updated metadata
                cmd = f"echo '{json.dumps(existing_data)}' > {self.container_config_path}"
                await self._ssh_execute(device_udid, cmd)
                
        except Exception as e:
            logger.error(f"Error deleting container metadata: {e}")

# Global instance
crane_container_service = CraneContainerService()
