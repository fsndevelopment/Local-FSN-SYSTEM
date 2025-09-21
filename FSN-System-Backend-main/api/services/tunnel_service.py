"""
Tunnel Service for creating secure tunnels
"""
import subprocess
import json
import asyncio
import structlog
from typing import Optional, Dict, Any
import os

logger = structlog.get_logger()

class TunnelService:
    """Service for creating secure tunnels using cloudflared or ngrok"""
    
    def __init__(self):
        self.ngrok_auth_token = os.getenv("NGROK_AUTHTOKEN")
        self.use_ngrok = bool(self.ngrok_auth_token)
    
    async def create_tunnel(self, local_port: int) -> Dict[str, Any]:
        """
        Create a tunnel for the given local port
        
        Args:
            local_port: Local port to tunnel
            
        Returns:
            Dict containing tunnel information
        """
        try:
            if self.use_ngrok:
                return await self._create_ngrok_tunnel(local_port)
            else:
                return await self._create_cloudflared_tunnel(local_port)
                
        except Exception as e:
            logger.error("❌ Failed to create tunnel", error=str(e), port=local_port)
            raise Exception(f"Failed to create tunnel: {str(e)}")
    
    async def _create_ngrok_tunnel(self, local_port: int) -> Dict[str, Any]:
        """Create ngrok tunnel"""
        try:
            # Set ngrok auth token
            env = os.environ.copy()
            env["NGROK_AUTHTOKEN"] = self.ngrok_auth_token
            
            # Start ngrok tunnel
            process = await asyncio.create_subprocess_exec(
                "ngrok", "tcp", str(local_port),
                "--log=stdout",
                "--log-level=info",
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait a moment for tunnel to establish
            await asyncio.sleep(3)
            
            # Get tunnel info from ngrok API
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:4040/api/tunnels") as response:
                    if response.status == 200:
                        data = await response.json()
                        tunnels = data.get("tunnels", [])
                        
                        for tunnel in tunnels:
                            if tunnel.get("proto") == "tcp" and str(local_port) in tunnel.get("config", {}).get("addr", ""):
                                public_url = tunnel.get("public_url", "").replace("tcp://", "https://")
                                
                                logger.info("✅ Created ngrok tunnel", port=local_port, url=public_url)
                                
                                return {
                                    "public_url": public_url,
                                    "local_port": local_port,
                                    "tunnel_type": "ngrok",
                                    "process": process
                                }
            
            raise Exception("No tunnel found in ngrok API")
            
        except Exception as e:
            logger.error("❌ Failed to create ngrok tunnel", error=str(e), port=local_port)
            raise
    
    async def _create_cloudflared_tunnel(self, local_port: int) -> Dict[str, Any]:
        """Create cloudflared tunnel"""
        try:
            # Start cloudflared tunnel
            process = await asyncio.create_subprocess_exec(
                "cloudflared", "tunnel", "--url", f"http://localhost:{local_port}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for tunnel to establish and capture output
            await asyncio.sleep(5)
            
            # Read stderr to get the tunnel URL
            stderr_output = await process.stderr.read()
            stderr_text = stderr_output.decode()
            
            # Parse cloudflared output to find tunnel URL
            public_url = None
            for line in stderr_text.split('\n'):
                if "https://" in line and "trycloudflare.com" in line:
                    # Extract URL from line like "2024-01-01T12:00:00Z INF | https://abc123.trycloudflare.com"
                    parts = line.split("https://")
                    if len(parts) > 1:
                        url_part = parts[1].split()[0]
                        public_url = f"https://{url_part}"
                        break
            
            if not public_url:
                raise Exception("Could not extract tunnel URL from cloudflared output")
            
            logger.info("✅ Created cloudflared tunnel", port=local_port, url=public_url)
            
            return {
                "public_url": public_url,
                "local_port": local_port,
                "tunnel_type": "cloudflared",
                "process": process
            }
            
        except Exception as e:
            logger.error("❌ Failed to create cloudflared tunnel", error=str(e), port=local_port)
            raise
    
    async def stop_tunnel(self, tunnel_info: Dict[str, Any]) -> bool:
        """
        Stop a tunnel
        
        Args:
            tunnel_info: Tunnel information from create_tunnel
            
        Returns:
            bool: True if stopped successfully
        """
        try:
            process = tunnel_info.get("process")
            if process and process.returncode is None:
                process.terminate()
                await asyncio.sleep(2)
                
                if process.returncode is None:
                    process.kill()
                
                logger.info("✅ Stopped tunnel", tunnel_type=tunnel_info.get("tunnel_type"))
                return True
            
            return False
            
        except Exception as e:
            logger.error("❌ Failed to stop tunnel", error=str(e))
            return False
    
    def is_tunnel_healthy(self, public_url: str) -> bool:
        """
        Check if tunnel is healthy
        
        Args:
            public_url: Public URL to check
            
        Returns:
            bool: True if tunnel is healthy
        """
        try:
            import aiohttp
            import asyncio
            
            async def check_health():
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(f"{public_url}/status", timeout=5) as response:
                            return response.status == 200
                    except:
                        return False
            
            # Run health check
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(check_health())
            
        except Exception as e:
            logger.error("❌ Tunnel health check failed", error=str(e), url=public_url)
            return False

# Create global instance
tunnel_service = TunnelService()
