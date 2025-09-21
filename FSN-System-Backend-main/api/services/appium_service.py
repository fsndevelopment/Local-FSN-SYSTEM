"""
Appium Service - Core automation engine for device management and control
"""
import asyncio
import subprocess
import json
import logging
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class AppiumService:
    """Main service for managing Appium sessions and device automation"""
    
    def __init__(self):
        self.server_url = "http://localhost:4723"
        self.active_sessions: Dict[str, webdriver.Remote] = {}
        self.device_capabilities: Dict[str, Dict] = {}
        self.remote_agents: Dict[str, Dict] = {}  # Store remote agent URLs
        
    async def start_appium_server(self) -> bool:
        """Start Appium server if not running"""
        try:
            # Check if Appium server is already running
            result = subprocess.run(
                ["curl", "-s", f"{self.server_url}/status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("Appium server is already running")
                return True
                
        except subprocess.TimeoutExpired:
            pass
            
        try:
            # Start Appium server in background
            logger.info("Starting Appium server...")
            process = subprocess.Popen(
                ["appium", "server", "--port", "4723", "--allow-insecure", "adb_shell", "--relaxed-security"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            for _ in range(30):  # Wait up to 30 seconds
                try:
                    result = subprocess.run(
                        ["curl", "-s", f"{self.server_url}/status"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        logger.info("Appium server started successfully")
                        return True
                except:
                    pass
                await asyncio.sleep(1)
                
            logger.error("Failed to start Appium server")
            return False
            
        except Exception as e:
            logger.error(f"Error starting Appium server: {e}")
            return False
    
    async def discover_devices(self) -> List[Dict[str, Any]]:
        """Discover connected devices (iOS and Android)"""
        devices = []
        
        try:
            # Discover Android devices
            logger.info("🔍 Discovering Android devices...")
            android_devices = await self._discover_android_devices()
            devices.extend(android_devices)
            logger.info(f"📱 Found {len(android_devices)} Android devices")
            
            # Discover iOS devices (if on macOS)
            logger.info("🔍 Discovering iOS devices...")
            ios_devices = await self._discover_ios_devices()
            devices.extend(ios_devices)
            logger.info(f"📱 Found {len(ios_devices)} iOS devices")
            
            # Update device capabilities cache
            for device in devices:
                self.device_capabilities[device['udid']] = device
            
            logger.info(f"✅ Total devices discovered: {len(devices)}")
            
        except Exception as e:
            logger.error(f"❌ Error during device discovery: {e}")
            # Return empty list instead of crashing
            return []
            
        return devices
    
    async def _discover_android_devices(self) -> List[Dict[str, Any]]:
        """Discover connected Android devices using ADB"""
        devices = []
        
        try:
            # Run adb devices command
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning("ADB not found or failed to run")
                return devices
                
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip() and 'device' in line:
                    parts = line.split()
                    udid = parts[0]
                    
                    # Get device info
                    device_info = await self._get_android_device_info(udid)
                    if device_info:
                        devices.append({
                            'udid': udid,
                            'platform': 'Android',
                            'name': device_info.get('model', f'Android-{udid[:8]}'),
                            'os_version': device_info.get('version', 'Unknown'),
                            'status': 'online',
                            'last_seen': datetime.now().isoformat(),
                            'capabilities': device_info
                        })
                        
        except subprocess.TimeoutExpired:
            logger.warning("ADB command timed out")
        except Exception as e:
            logger.error(f"Error discovering Android devices: {e}")
            
        return devices
    
    async def _discover_ios_devices(self) -> List[Dict[str, Any]]:
        """Discover connected iOS devices using libimobiledevice (for jailbroken devices)"""
        devices = []
        
        try:
            # Use idevice_id to list connected iOS devices
            result = subprocess.run(
                ["idevice_id", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                udids = result.stdout.strip().split('\n')
                
                for udid in udids:
                    if udid.strip():
                        # Get device info using ideviceinfo
                        device_info = await self._get_ios_device_info(udid.strip())
                        if device_info:
                            devices.append({
                                'udid': udid.strip(),
                                'platform': 'iOS',
                                'name': device_info.get('DeviceName', f'iOS-{udid[:8]}'),
                                'os_version': device_info.get('ProductVersion', 'Unknown'),
                                'status': 'online',
                                'last_seen': datetime.now().isoformat(),
                                'capabilities': device_info,
                                'jailbroken': await self._check_jailbreak_status(udid.strip())
                            })
                            
        except subprocess.TimeoutExpired:
            logger.warning("iOS device discovery timed out")
        except FileNotFoundError:
            logger.info("libimobiledevice tools not found - install with: brew install libimobiledevice")
        except Exception as e:
            logger.error(f"Error discovering iOS devices: {e}")
            
        return devices
    
    async def _get_ios_device_info(self, udid: str) -> Optional[Dict[str, str]]:
        """Get detailed info about an iOS device"""
        try:
            # Get device properties using ideviceinfo
            result = subprocess.run(
                ["ideviceinfo", "-u", udid],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
                
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    try:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                    except:
                        continue
                        
            return info
            
        except Exception as e:
            logger.error(f"Error getting iOS device info for {udid}: {e}")
            return None
    
    async def _check_jailbreak_status(self, udid: str) -> bool:
        """Check if iOS device is jailbroken"""
        try:
            # Try to access /Applications directory (jailbreak indicator)
            result = subprocess.run(
                ["idevicefs", "ls", "-u", udid, "/Applications"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # If we can list /Applications, device is likely jailbroken
            return result.returncode == 0
            
        except Exception:
            # If idevicefs not available, assume jailbroken if we got this far
            return True
    
    async def _get_android_device_info(self, udid: str) -> Optional[Dict[str, str]]:
        """Get detailed info about an Android device"""
        try:
            # Get device properties
            result = subprocess.run(
                ["adb", "-s", udid, "shell", "getprop"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
                
            props = {}
            for line in result.stdout.split('\n'):
                if ':' in line and '[' in line:
                    try:
                        key = line.split('[')[1].split(']')[0]
                        value = line.split('[')[2].split(']')[0] if line.count('[') > 1 else ''
                        props[key] = value
                    except:
                        continue
                        
            return {
                'model': props.get('ro.product.model', 'Unknown'),
                'brand': props.get('ro.product.brand', 'Unknown'),
                'version': props.get('ro.build.version.release', 'Unknown'),
                'sdk': props.get('ro.build.version.sdk', 'Unknown'),
                'manufacturer': props.get('ro.product.manufacturer', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error getting device info for {udid}: {e}")
            return None
    
    async def create_session(self, device_udid: str, app_package: str = None) -> Optional[str]:
        """Create an Appium session for a device"""
        if device_udid in self.active_sessions:
            logger.info(f"Session already exists for device {device_udid}")
            return device_udid
            
        device_info = self.device_capabilities.get(device_udid)
        if not device_info:
            logger.warning(f"Device {device_udid} not found in capabilities, trying to discover...")
            # Try to discover devices
            await self.discover_devices()
            device_info = self.device_capabilities.get(device_udid)
            
            if not device_info:
                logger.error(f"Device {device_udid} still not found after discovery")
                return None
            
        try:
            if device_info['platform'] == 'Android':
                options = UiAutomator2Options()
                options.device_name = device_info['name']
                options.udid = device_udid
                options.platform_name = "Android"
                options.platform_version = device_info['os_version']
                options.automation_name = "UiAutomator2"
                options.no_reset = True
                options.full_reset = False
                
                if app_package:
                    options.app_package = app_package
                    options.app_activity = self._get_main_activity(app_package)
                
            else:  # iOS
                options = XCUITestOptions()
                options.device_name = device_info['name']
                options.udid = device_udid
                options.platform_name = "iOS"
                options.platform_version = device_info['os_version']
                options.automation_name = "XCUITest"
                
                if app_package:
                    options.bundle_id = app_package
            
            # Create WebDriver session
            driver = webdriver.Remote(
                command_executor=self.server_url,
                options=options
            )
            
            self.active_sessions[device_udid] = driver
            logger.info(f"Created Appium session for device {device_udid}")
            return device_udid
            
        except Exception as e:
            logger.error(f"Failed to create session for device {device_udid}: {e}")
            return None
    
    async def close_session(self, device_udid: str) -> bool:
        """Close Appium session for a device"""
        if device_udid not in self.active_sessions:
            return True
            
        try:
            driver = self.active_sessions[device_udid]
            driver.quit()
            del self.active_sessions[device_udid]
            logger.info(f"Closed session for device {device_udid}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing session for device {device_udid}: {e}")
            return False
    
    def _get_main_activity(self, package_name: str) -> str:
        """Get main activity for common apps"""
        activities = {
            'com.instagram.android': 'com.instagram.mainactivity.MainActivity',
            'com.zhiliaoapp.musically': 'com.ss.android.ugc.aweme.splash.SplashActivity',  # TikTok
            'com.twitter.android': 'com.twitter.android.StartActivity',
            'com.facebook.katana': 'com.facebook.katana.LoginActivity'
        }
        return activities.get(package_name, '.MainActivity')
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session device UDIDs"""
        return list(self.active_sessions.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Appium service"""
        return {
            'server_running': await self._is_server_running(),
            'active_sessions': len(self.active_sessions),
            'discovered_devices': len(self.device_capabilities),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _is_server_running(self) -> bool:
        """Check if Appium server is running"""
        try:
            result = subprocess.run(
                ["curl", "-s", f"{self.server_url}/status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    async def register_remote_agent(self, agent_id: str, appium_url: str) -> bool:
        """Register a remote agent's Appium URL"""
        try:
            self.remote_agents[agent_id] = {
                "appium_url": appium_url,
                "last_seen": datetime.utcnow()
            }
            logger.info(f"Registered remote agent: {agent_id} -> {appium_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to register remote agent: {e}")
            return False

    async def get_agent_for_device(self, device_udid: str) -> Optional[str]:
        """Get the agent ID for a specific device"""
        # This would typically query the database to find which agent has this device
        # For now, return the first available agent
        if self.remote_agents:
            return list(self.remote_agents.keys())[0]
        return None

    async def create_remote_session(self, device_udid: str, agent_id: str) -> Optional[str]:
        """Create a session on a remote agent"""
        try:
            if agent_id not in self.remote_agents:
                logger.error(f"Agent {agent_id} not found")
                return None

            agent_url = self.remote_agents[agent_id]["appium_url"]
            logger.info(f"Creating remote session for {device_udid} on agent {agent_id} at {agent_url}")
            
            # Get device capabilities
            device_info = self.device_capabilities.get(device_udid)
            if not device_info:
                logger.warning(f"Device {device_udid} not found in capabilities, trying to discover...")
                # Try to discover devices from this agent
                await self.discover_remote_devices(agent_id)
                device_info = self.device_capabilities.get(device_udid)
                
                if not device_info:
                    logger.error(f"Device {device_udid} still not found after discovery")
                    return None
            
            # Ensure jailbroken status is included in device info
            if 'jailbroken' not in device_info:
                logger.warning(f"Device {device_udid} missing jailbroken status, checking...")
                device_info['jailbroken'] = await self._check_jailbreak_status(device_udid)
                logger.info(f"🔍 Device {device_udid} jailbroken status: {device_info['jailbroken']}")
            
            logger.info(f"🔍 Device info for {device_udid}: {device_info}")

            # Prepare capabilities for real Appium session
            if device_info['platform'] == 'Android':
                options = UiAutomator2Options()
                options.device_name = device_info['name']
                options.udid = device_udid
                options.platform_name = "Android"
                options.platform_version = device_info['os_version']
                options.automation_name = "UiAutomator2"
                options.no_reset = True
                options.full_reset = False
            else:  # iOS
                options = XCUITestOptions()
                options.device_name = device_info['name']
                options.udid = device_udid
                options.platform_name = "iOS"
                options.platform_version = device_info['os_version']
                options.automation_name = "XCUITest"
                options.no_reset = True
                options.new_command_timeout = 300
                
                # Add jailbroken capability if device is jailbroken
                if device_info.get('jailbroken', False):
                    options.set_capability("jailbroken", True)
                    logger.info(f"🔧 Added jailbroken capability for device {device_udid}")
                else:
                    options.set_capability("jailbroken", False)
                    logger.info(f"📱 Added non-jailbroken capability for device {device_udid}")

            logger.info(f"Creating real Appium session with capabilities: {options.to_capabilities()}")
            
            # Create WebDriver session on remote agent
            driver = webdriver.Remote(
                command_executor=agent_url,
                options=options
            )

            # Store the session ID (not the driver object)
            session_id = driver.session_id
            self.active_sessions[device_udid] = session_id
            logger.info(f"✅ Created REAL remote session for device {device_udid} on agent {agent_id}")
            logger.info(f"📱 Session ID: {session_id}")
            logger.info(f"🔌 Appium URL: {agent_url}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create remote session for device {device_udid}: {e}")
            return None

    async def discover_remote_devices(self, agent_id: str) -> List[Dict[str, Any]]:
        """Discover devices from a remote agent"""
        try:
            if agent_id not in self.remote_agents:
                logger.error(f"Agent {agent_id} not found")
                return []

            agent_url = self.remote_agents[agent_id]["appium_url"]
            base_url = agent_url.replace('/appium', '')
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/devices", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    devices = data.get('devices', [])
                    
                    # Update device capabilities cache
                    for device in devices:
                        self.device_capabilities[device['udid']] = device
                    
                    logger.info(f"Discovered {len(devices)} devices from agent {agent_id}")
                    return devices
                else:
                    logger.error(f"Failed to discover devices from agent {agent_id}: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error discovering devices from agent {agent_id}: {e}")
            return []

    async def health_check_remote_agent(self, agent_id: str) -> bool:
        """Check health of remote agent"""
        try:
            if agent_id not in self.remote_agents:
                return False

            agent_url = self.remote_agents[agent_id]["appium_url"]
            base_url = agent_url.replace('/appium', '')
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/health", timeout=5)
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Health check failed for agent {agent_id}: {e}")
            return False


# Global instance
appium_service = AppiumService()
