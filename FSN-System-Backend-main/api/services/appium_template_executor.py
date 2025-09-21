"""
Appium Template Executor

Executes template-based automation using existing Appium scripts
"""

import asyncio
import subprocess
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.template_action_mapper import template_action_mapper, AppiumAction
from migrations.setup_postgresql_tables import Device, Account

logger = logging.getLogger(__name__)

class AppiumTemplateExecutor:
    """Executes template-based automation using existing Appium scripts"""
    
    def __init__(self):
        self.base_path = "/Users/jacqubsf/Downloads/Telegram Desktop/FSN-System-Backend-main/FSN-System-Backend-main"
        self.running_processes = {}
    
    async def execute_template(self, template: Dict[str, Any], device: Device, accounts: List[Account]) -> Dict[str, Any]:
        """
        Execute template using existing Appium scripts
        
        Args:
            template: Template configuration
            device: Device to execute on
            accounts: Accounts to use for execution
            
        Returns:
            Execution result dictionary
        """
        try:
            logger.info(f"Starting template execution", 
                       template_id=template.get('id'),
                       device_id=device.id,
                       accounts_count=len(accounts))
            
            # Debug: Log device information
            logger.info(f"🔍 Device Debug Info:")
            logger.info(f"   Device ID: {device.id}")
            logger.info(f"   Device Name: {device.name}")
            logger.info(f"   Device UDID: {device.udid}")
            logger.info(f"   Device Jailbroken: {device.jailbroken}")
            logger.info(f"   Device Jailbroken Type: {type(device.jailbroken)}")
            
            # Debug: Log account information
            for account in accounts:
                logger.info(f"🔍 Account Debug Info:")
                logger.info(f"   Account ID: {account.id}")
                logger.info(f"   Account Username: {account.username}")
                logger.info(f"   Account Container Number: {getattr(account, 'container_number', 'NOT SET')}")
                logger.info(f"   Account Container Number Type: {type(getattr(account, 'container_number', None))}")
            
            # Map template to actions
            actions = template_action_mapper.map_template_to_actions(template)
            logger.info(f"Generated {len(actions)} actions from template")
            
            # Execute actions for each account
            results = []
            for account in accounts:
                account_results = await self._execute_actions_for_account(actions, device, account)
                results.extend(account_results)
            
            logger.info(f"Template execution completed", 
                       template_id=template.get('id'),
                       total_actions=len(results))
            
            return {
                "success": True,
                "template_id": template.get('id'),
                "device_id": device.id,
                "accounts_processed": len(accounts),
                "actions_executed": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Template execution failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "template_id": template.get('id'),
                "device_id": device.id
            }
    
    async def _execute_actions_for_account(self, actions: List[AppiumAction], device: Device, account: Account) -> List[Dict[str, Any]]:
        """Execute all actions for a specific account"""
        results = []
        
        for action in actions:
            try:
                result = await self._execute_action(action, device, account)
                results.append(result)
            except Exception as e:
                logger.error(f"Action execution failed", 
                           action=action.type.value,
                           account_id=account.id,
                           error=str(e))
                results.append({
                    "action": action.type.value,
                    "account_id": account.id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _execute_action(self, action: AppiumAction, device: Device, account: Account) -> Dict[str, Any]:
        """Execute a single action using the appropriate Appium script"""
        script_path = template_action_mapper.get_script_path(action)
        
        if not script_path:
            raise Exception(f"No script found for action {action.type.value} on platform {action.platform}")
        
        full_script_path = os.path.join(self.base_path, script_path)
        
        if not os.path.exists(full_script_path):
            raise Exception(f"Script not found: {full_script_path}")
        
        # Prepare script parameters
        script_params = self._prepare_script_parameters(action, device, account)
        
        # Execute the script
        logger.info(f"Executing script", 
                   script=script_path,
                   action=action.type.value,
                   account_id=account.id,
                   device_id=device.id)
        
        try:
            result = await self._run_script(full_script_path, script_params)
            
            return {
                "action": action.type.value,
                "account_id": account.id,
                "device_id": device.id,
                "success": True,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Script execution failed", 
                       script=script_path,
                       error=str(e))
            raise
    
    def _prepare_script_parameters(self, action: AppiumAction, device: Device, account: Account) -> Dict[str, Any]:
        """Prepare parameters for the Appium script"""
        # Determine device type and container information
        device_type = "jailbroken" if getattr(device, 'jailbroken', False) else "non_jailbroken"
        container_id = None
        
        if device_type == "jailbroken":
            if hasattr(account, 'container_number') and account.container_number:
                container_id = f"container_{account.container_number}"
                logger.info(f"🔧 JB Device - Using container ID: {container_id} (container_number: {account.container_number})")
            else:
                container_id = f"container_{account.id}" if hasattr(account, 'id') else "default"
                logger.warning(f"⚠️ JB Device - No container_number in account, using fallback: {container_id}")
        
        params = {
            "device_udid": device.udid,
            "device_name": device.name,
            "wda_port": getattr(device, 'wda_port', 8109),
            "appium_port": getattr(device, 'appium_port', 4741),
            "platform": action.platform,
            "action_type": action.type.value,
            "action_count": action.count,
            "account_username": account.username,
            "account_email": account.email,
            "account_password": account.password,
            "account_platform": account.platform,
            "account_auth_type": account.auth_type,
            "account_two_factor_code": account.two_factor_code,
            # JB/NONJB device information
            "device_type": device_type,
            "device_jailbroken": getattr(device, 'jailbroken', False),
            "container_id": container_id,
        }
        
        # Add action-specific parameters
        params.update(action.parameters)
        
        return params
    
    async def _run_script(self, script_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Appium script with parameters"""
        # Create a temporary parameters file
        params_file = f"/tmp/appium_params_{datetime.utcnow().timestamp()}.json"
        
        try:
            with open(params_file, 'w') as f:
                json.dump(parameters, f, indent=2)
            
            # Run the script
            cmd = ["python3", script_path, "--params", params_file]
            
            logger.info(f"Running command", command=" ".join(cmd))
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.base_path
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Try to parse JSON output
                try:
                    result = json.loads(stdout.decode())
                except json.JSONDecodeError:
                    result = {"output": stdout.decode()}
                
                logger.info(f"Script completed successfully", 
                           script=script_path,
                           return_code=process.returncode)
                
                return result
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Script failed", 
                           script=script_path,
                           return_code=process.returncode,
                           error=error_msg)
                raise Exception(f"Script execution failed: {error_msg}")
                
        finally:
            # Clean up parameters file
            if os.path.exists(params_file):
                os.remove(params_file)
    
    async def stop_template_execution(self, template_id: str) -> bool:
        """Stop template execution"""
        try:
            # Find and stop running processes for this template
            processes_to_stop = []
            for process_id, process_info in self.running_processes.items():
                if process_info.get('template_id') == template_id:
                    processes_to_stop.append(process_id)
            
            for process_id in processes_to_stop:
                process = self.running_processes[process_id]['process']
                if process and process.returncode is None:
                    process.terminate()
                    await process.wait()
                del self.running_processes[process_id]
            
            logger.info(f"Stopped template execution", 
                       template_id=template_id,
                       processes_stopped=len(processes_to_stop))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop template execution", 
                        template_id=template_id,
                        error=str(e))
            return False

# Global instance
appium_template_executor = AppiumTemplateExecutor()
