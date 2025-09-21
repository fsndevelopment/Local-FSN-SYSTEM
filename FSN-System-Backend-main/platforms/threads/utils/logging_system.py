#!/usr/bin/env python3
"""
Threads Logging System
=====================

Comprehensive logging system for Threads automation actions.
Integrates with the existing checkpoint system and provides detailed
logging for debugging, monitoring, and evidence collection.

Key Features:
- Action-level logging with timestamps
- Screenshot and XML capture for each action
- Error tracking and recovery logging
- Performance metrics collection
- Integration with checkpoint system

Author: FSN Appium Team
Last Updated: January 15, 2025
Status: Production-ready
"""

import time
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webdriver import WebDriver

class ThreadsLoggingSystem:
    """Comprehensive logging system for Threads automation"""
    
    def __init__(self, platform: str = "threads", device_id: str = "unknown"):
        self.platform = platform
        self.device_id = device_id
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create logging directory
        self.log_dir = f"/Users/jacqubsf/Downloads/FSN-APPIUM-main/logs/{platform}_{device_id}_{self.session_id}"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Action tracking
        self.actions_log = []
        self.current_action = None
        
    def _setup_logger(self) -> logging.Logger:
        """Setup comprehensive logging configuration"""
        logger = logging.getLogger(f"{self.platform}_{self.device_id}")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            f"{self.log_dir}/threads_automation.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler for real-time monitoring
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def start_action(self, action_name: str, action_type: str, **kwargs) -> str:
        """Start logging for a new action"""
        action_id = f"{action_name}_{int(time.time())}"
        
        self.current_action = {
            "action_id": action_id,
            "action_name": action_name,
            "action_type": action_type,
            "start_time": datetime.now().isoformat(),
            "device_id": self.device_id,
            "platform": self.platform,
            "parameters": kwargs,
            "checkpoints": [],
            "screenshots": [],
            "xml_dumps": [],
            "errors": [],
            "performance": {}
        }
        
        self.logger.info(f"🎯 STARTING ACTION: {action_name} ({action_type})")
        self.logger.info(f"📱 Device: {self.device_id}")
        self.logger.info(f"⏰ Start Time: {self.current_action['start_time']}")
        
        if kwargs:
            self.logger.info(f"🔧 Parameters: {json.dumps(kwargs, indent=2)}")
        
        return action_id
    
    def log_checkpoint(self, checkpoint_name: str, success: bool, 
                      driver: Optional[WebDriver] = None, 
                      error_message: str = None) -> None:
        """Log a checkpoint with evidence collection"""
        if not self.current_action:
            self.logger.warning("⚠️ No active action - cannot log checkpoint")
            return
        
        checkpoint = {
            "name": checkpoint_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "error_message": error_message
        }
        
        # Collect evidence if driver provided
        if driver:
            try:
                # Screenshot
                screenshot_path = f"{self.log_dir}/checkpoint_{checkpoint_name}_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                checkpoint["screenshot"] = screenshot_path
                
                # XML dump
                xml_path = f"{self.log_dir}/checkpoint_{checkpoint_name}_{int(time.time())}.xml"
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                checkpoint["xml_dump"] = xml_path
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not collect evidence for {checkpoint_name}: {e}")
        
        self.current_action["checkpoints"].append(checkpoint)
        
        status = "✅" if success else "❌"
        self.logger.info(f"{status} CHECKPOINT: {checkpoint_name}")
        
        if error_message:
            self.logger.error(f"💥 Error: {error_message}")
    
    def log_error(self, error_type: str, error_message: str, 
                 driver: Optional[WebDriver] = None) -> None:
        """Log an error with evidence collection"""
        if not self.current_action:
            self.logger.warning("⚠️ No active action - cannot log error")
            return
        
        error = {
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Collect evidence if driver provided
        if driver:
            try:
                # Screenshot
                screenshot_path = f"{self.log_dir}/error_{error_type}_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                error["screenshot"] = screenshot_path
                
                # XML dump
                xml_path = f"{self.log_dir}/error_{error_type}_{int(time.time())}.xml"
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                error["xml_dump"] = xml_path
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not collect error evidence: {e}")
        
        self.current_action["errors"].append(error)
        self.logger.error(f"💥 ERROR ({error_type}): {error_message}")
    
    def log_performance(self, metric_name: str, value: float, unit: str = "seconds") -> None:
        """Log performance metrics"""
        if not self.current_action:
            self.logger.warning("⚠️ No active action - cannot log performance")
            return
        
        self.current_action["performance"][metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"📊 PERFORMANCE: {metric_name} = {value} {unit}")
    
    def end_action(self, success: bool, driver: Optional[WebDriver] = None) -> Dict[str, Any]:
        """End the current action and save logs"""
        if not self.current_action:
            self.logger.warning("⚠️ No active action to end")
            return {}
        
        # Calculate duration
        start_time = datetime.fromisoformat(self.current_action["start_time"])
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Update action with end details
        self.current_action.update({
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "success": success,
            "checkpoints_passed": len([cp for cp in self.current_action["checkpoints"] if cp["success"]]),
            "total_checkpoints": len(self.current_action["checkpoints"]),
            "error_count": len(self.current_action["errors"])
        })
        
        # Final evidence collection
        if driver:
            try:
                # Final screenshot
                final_screenshot = f"{self.log_dir}/final_state_{int(time.time())}.png"
                driver.save_screenshot(final_screenshot)
                self.current_action["final_screenshot"] = final_screenshot
                
                # Final XML dump
                final_xml = f"{self.log_dir}/final_state_{int(time.time())}.xml"
                with open(final_xml, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                self.current_action["final_xml"] = final_xml
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not collect final evidence: {e}")
        
        # Save action log
        action_file = f"{self.log_dir}/action_{self.current_action['action_id']}.json"
        with open(action_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_action, f, indent=2, ensure_ascii=False)
        
        # Add to actions log
        self.actions_log.append(self.current_action)
        
        # Log summary
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.logger.info(f"🏁 ACTION COMPLETED: {self.current_action['action_name']} - {status}")
        self.logger.info(f"⏱️ Duration: {duration:.2f} seconds")
        self.logger.info(f"📊 Checkpoints: {self.current_action['checkpoints_passed']}/{self.current_action['total_checkpoints']}")
        self.logger.info(f"💥 Errors: {self.current_action['error_count']}")
        self.logger.info(f"📁 Log Directory: {self.log_dir}")
        
        # Clear current action
        result = self.current_action.copy()
        self.current_action = None
        
        return result
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the current logging session"""
        total_actions = len(self.actions_log)
        successful_actions = len([action for action in self.actions_log if action.get("success", False)])
        
        total_duration = sum(action.get("duration_seconds", 0) for action in self.actions_log)
        
        return {
            "session_id": self.session_id,
            "platform": self.platform,
            "device_id": self.device_id,
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "failed_actions": total_actions - successful_actions,
            "success_rate": (successful_actions / total_actions * 100) if total_actions > 0 else 0,
            "total_duration_seconds": total_duration,
            "log_directory": self.log_dir,
            "actions": self.actions_log
        }
    
    def save_session_summary(self) -> str:
        """Save session summary to file"""
        summary = self.get_session_summary()
        summary_file = f"{self.log_dir}/session_summary.json"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📊 Session summary saved: {summary_file}")
        return summary_file


# Global logging system instance
_threads_logger = None

def get_threads_logger(device_id: str = "unknown") -> ThreadsLoggingSystem:
    """Get or create global Threads logging system instance"""
    global _threads_logger
    if _threads_logger is None:
        _threads_logger = ThreadsLoggingSystem(device_id=device_id)
    return _threads_logger


if __name__ == "__main__":
    print("🧵 Threads Logging System")
    print("========================")
    print("Comprehensive logging for Threads automation")
    print("Evidence collection and performance tracking")
    print("Integration with checkpoint system")
