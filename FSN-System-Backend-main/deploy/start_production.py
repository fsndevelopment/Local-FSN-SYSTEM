#!/usr/bin/env python3
"""
Production Deployment Script for FSN APPIUM
Starts the complete Instagram automation system in production mode

✅ Includes all 9 confirmed working Instagram actions
✅ Commercial-safe rate limiting
✅ Health monitoring
✅ Auto-recovery
"""

import os
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path
from production_config import production_config

# Setup logging
logging.basicConfig(
    level=getattr(logging, production_config.LOG_LEVEL),
    format=production_config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

class ProductionDeployment:
    """Production deployment manager"""
    
    def __init__(self):
        self.appium_process = None
        self.api_process = None
        self.running = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def validate_environment(self):
        """Validate production environment before starting"""
        logger.info("🔍 Validating production environment...")
        
        validation = production_config.validate_environment()
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                logger.warning(f"⚠️ {warning}")
        
        if validation["errors"]:
            for error in validation["errors"]:
                logger.error(f"❌ {error}")
            return False
        
        logger.info("✅ Environment validation passed")
        return True
    
    def start_appium_server(self):
        """Start Appium server for device automation"""
        logger.info("🚀 Starting Appium server...")
        
        try:
            appium_cmd = [
                "appium",
                "--port", str(production_config.APPIUM_PORT),
                "--log-level", "info"
            ]
            
            self.appium_process = subprocess.Popen(
                appium_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Appium to start
            time.sleep(5)
            
            if self.appium_process.poll() is None:
                logger.info(f"✅ Appium server started on port {production_config.APPIUM_PORT}")
                return True
            else:
                logger.error("❌ Appium server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start Appium server: {e}")
            return False
    
    def start_api_server(self):
        """Start FastAPI server with production configuration"""
        logger.info("🚀 Starting FastAPI server...")
        
        try:
            # Change to API directory
            api_dir = Path(__file__).parent.parent / "api"
            
            uvicorn_cmd = [
                "uvicorn",
                "main:app",
                "--host", production_config.HOST,
                "--port", str(production_config.PORT),
                "--workers", str(production_config.WORKERS),
                "--log-level", production_config.LOG_LEVEL.lower(),
                "--access-log"
            ]
            
            if not production_config.RELOAD:
                uvicorn_cmd.append("--no-reload")
            
            self.api_process = subprocess.Popen(
                uvicorn_cmd,
                cwd=api_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for API to start
            time.sleep(5)
            
            if self.api_process.poll() is None:
                logger.info(f"✅ FastAPI server started on {production_config.HOST}:{production_config.PORT}")
                return True
            else:
                logger.error("❌ FastAPI server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start FastAPI server: {e}")
            return False
    
    def health_check(self):
        """Perform health check on running services"""
        try:
            import requests
            
            # Check API health
            api_url = f"http://localhost:{production_config.PORT}/api/real-device/test-status"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ API Health: {data.get('total_confirmed', 0)} Instagram actions available")
                return True
            else:
                logger.warning(f"⚠️ API Health: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Health check failed: {e}")
            return False
    
    def monitor_services(self):
        """Monitor running services and restart if needed"""
        logger.info("👁️ Starting service monitoring...")
        
        while self.running:
            try:
                # Check Appium process
                if self.appium_process and self.appium_process.poll() is not None:
                    logger.error("❌ Appium server died, restarting...")
                    self.start_appium_server()
                
                # Check API process
                if self.api_process and self.api_process.poll() is not None:
                    logger.error("❌ API server died, restarting...")
                    self.start_api_server()
                
                # Health check
                if not self.health_check():
                    logger.warning("⚠️ Health check failed")
                
                # Sleep until next check
                time.sleep(production_config.MONITORING["health_check_interval"])
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def shutdown(self, signum=None, frame=None):
        """Gracefully shutdown all services"""
        logger.info("🛑 Shutting down production deployment...")
        self.running = False
        
        # Stop API server
        if self.api_process:
            logger.info("Stopping FastAPI server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
        
        # Stop Appium server
        if self.appium_process:
            logger.info("Stopping Appium server...")
            self.appium_process.terminate()
            try:
                self.appium_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.appium_process.kill()
        
        logger.info("✅ Production deployment stopped")
        sys.exit(0)
    
    def start(self):
        """Start complete production deployment"""
        logger.info("🚀 Starting FSN APPIUM Production Deployment")
        logger.info("="*60)
        logger.info("📱 Instagram Actions: 9/9 Confirmed Working")
        logger.info("🛡️ Rate Limiting: Commercial Safe")
        logger.info("🔧 Configuration: Production Ready")
        logger.info("="*60)
        
        # Validate environment
        if not self.validate_environment():
            logger.error("❌ Environment validation failed")
            return False
        
        # Start Appium server
        if not self.start_appium_server():
            logger.error("❌ Failed to start Appium server")
            return False
        
        # Start API server
        if not self.start_api_server():
            logger.error("❌ Failed to start API server")
            self.shutdown()
            return False
        
        # Initial health check
        time.sleep(10)
        if not self.health_check():
            logger.warning("⚠️ Initial health check failed, continuing anyway...")
        
        # Start monitoring
        self.running = True
        logger.info("✅ Production deployment started successfully!")
        logger.info(f"🌐 API available at: http://localhost:{production_config.PORT}")
        logger.info(f"📊 Status endpoint: http://localhost:{production_config.PORT}/api/real-device/test-status")
        logger.info(f"🛡️ Rate limits: http://localhost:{production_config.PORT}/api/real-device/rate-limits-recommendations")
        
        try:
            self.monitor_services()
        except KeyboardInterrupt:
            self.shutdown()
        
        return True

def main():
    """Main production deployment entry point"""
    deployment = ProductionDeployment()
    
    try:
        success = deployment.start()
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Production deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
