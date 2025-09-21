"""
Template to Job Conversion Service

Converts template actions into individual jobs for execution
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from models.job import Job, JobType, JobPriority, JobStatus
from models.account import Account
from models.device import Device

logger = logging.getLogger(__name__)

class TemplateJobConverter:
    """Converts template actions into executable jobs"""
    
    def __init__(self):
        self.job_type_mapping = {
            'threads': {
                'likes': JobType.THREADS_LIKE_POST,
                'follows': JobType.THREADS_FOLLOW_USER,
                'posts': JobType.THREADS_CREATE_POST,
                'comments': JobType.THREADS_COMMENT_POST,
                'reposts': JobType.THREADS_REPOST,
                'quotes': JobType.THREADS_QUOTE_POST,
                'scrolling': 'scrolling'  # Special case for scrolling
            },
            'instagram': {
                'likes': JobType.INSTAGRAM_LIKE_POST,
                'follows': JobType.INSTAGRAM_FOLLOW_USER,
                'posts': JobType.INSTAGRAM_POST_REEL,
                'stories': JobType.INSTAGRAM_POST_STORY,
                'comments': JobType.INSTAGRAM_COMMENT_POST,
                'reels': JobType.INSTAGRAM_POST_REEL,
                'scrolling': 'scrolling'  # Special case for scrolling
            }
        }
    
    def convert_template_to_jobs(
        self, 
        template_data: Dict[str, Any], 
        accounts: List[Account], 
        devices: List[Device],
        priority: str = "normal"
    ) -> List[Dict[str, Any]]:
        """
        Convert template data into a list of job creation data
        
        Args:
            template_data: Template configuration from frontend
            accounts: Available accounts for execution
            devices: Available devices for execution
            priority: Job priority level
            
        Returns:
            List of job creation dictionaries
        """
        jobs = []
        platform = template_data.get('platform', 'threads')
        
        if not accounts:
            logger.warning("No accounts available for template conversion")
            return jobs
            
        if not devices:
            logger.warning("No devices available for template conversion")
            return jobs
        
        # Distribute accounts across devices
        account_device_mapping = self._distribute_accounts_to_devices(accounts, devices)
        
        # Convert daily actions to jobs
        jobs.extend(self._create_daily_action_jobs(template_data, account_device_mapping, platform, priority))
        
        # Add scrolling jobs if specified
        if template_data.get('scrollingTimeMinutes', 0) > 0:
            jobs.extend(self._create_scrolling_jobs(template_data, account_device_mapping, platform, priority))
        
        logger.info(f"Converted template to {len(jobs)} jobs", 
                   platform=platform, 
                   accounts_count=len(accounts),
                   devices_count=len(devices))
        
        return jobs
    
    def _distribute_accounts_to_devices(
        self, 
        accounts: List[Account], 
        devices: List[Device]
    ) -> Dict[int, List[Account]]:
        """Distribute accounts across available devices"""
        device_accounts = {device.id: [] for device in devices}
        
        # Simple round-robin distribution
        for i, account in enumerate(accounts):
            device_id = devices[i % len(devices)].id
            device_accounts[device_id].append(account)
        
        return device_accounts
    
    def _create_daily_action_jobs(
        self, 
        template_data: Dict[str, Any], 
        account_device_mapping: Dict[int, List[Account]], 
        platform: str,
        priority: str
    ) -> List[Dict[str, Any]]:
        """Create jobs for daily actions (likes, follows, posts, etc.)"""
        jobs = []
        
        # Get job type mapping for platform
        platform_mapping = self.job_type_mapping.get(platform, {})
        
        # Process each device and its assigned accounts
        for device_id, device_accounts in account_device_mapping.items():
            if not device_accounts:
                continue
                
            # Create jobs for each account on this device
            for account in device_accounts:
                # Likes per day
                if template_data.get('likesPerDay', 0) > 0:
                    jobs.extend(self._create_action_jobs(
                        account, device_id, platform_mapping['likes'], 
                        template_data['likesPerDay'], 'likes', priority
                    ))
                
                # Follows per day
                if template_data.get('followsPerDay', 0) > 0:
                    jobs.extend(self._create_action_jobs(
                        account, device_id, platform_mapping['follows'], 
                        template_data['followsPerDay'], 'follows', priority
                    ))
                
                # Posts per day (photos)
                if template_data.get('photosPostsPerDay', 0) > 0:
                    jobs.extend(self._create_action_jobs(
                        account, device_id, platform_mapping['posts'], 
                        template_data['photosPostsPerDay'], 'posts', priority,
                        content_type='photos',
                        content_path=template_data.get('photosFolder', '')
                    ))
                
                # Text posts per day
                if template_data.get('textPostsPerDay', 0) > 0:
                    jobs.extend(self._create_action_jobs(
                        account, device_id, platform_mapping['posts'], 
                        template_data['textPostsPerDay'], 'text_posts', priority,
                        content_type='text',
                        content_path=template_data.get('textPostsFile', '')
                    ))
                
                # Stories per day (Instagram only)
                if platform == 'instagram' and template_data.get('storiesPerDay', 0) > 0:
                    jobs.extend(self._create_action_jobs(
                        account, device_id, platform_mapping['stories'], 
                        template_data['storiesPerDay'], 'stories', priority
                    ))
        
        return jobs
    
    def _create_scrolling_jobs(
        self, 
        template_data: Dict[str, Any], 
        account_device_mapping: Dict[int, List[Account]], 
        platform: str,
        priority: str
    ) -> List[Dict[str, Any]]:
        """Create scrolling jobs"""
        jobs = []
        scrolling_minutes = template_data.get('scrollingTimeMinutes', 0)
        
        if scrolling_minutes <= 0:
            return jobs
        
        # Create one scrolling job per device (not per account)
        for device_id, device_accounts in account_device_mapping.items():
            if not device_accounts:
                continue
                
            # Use the first account for scrolling
            account = device_accounts[0]
            
            jobs.append({
                'account_id': account.id,
                'device_id': device_id,
                'platform': platform,
                'type': 'scrolling',
                'priority': priority,
                'payload': {
                    'duration_minutes': scrolling_minutes,
                    'action_type': 'scrolling',
                    'template_id': template_data.get('id'),
                    'template_name': template_data.get('name')
                },
                'not_before': datetime.utcnow().isoformat(),
                'max_attempts': 3
            })
        
        return jobs
    
    def _create_action_jobs(
        self, 
        account: Account, 
        device_id: int, 
        job_type: JobType, 
        count: int, 
        action_name: str,
        priority: str,
        content_type: str = None,
        content_path: str = None
    ) -> List[Dict[str, Any]]:
        """Create individual action jobs"""
        jobs = []
        
        # Spread actions throughout the day (every 2-3 hours)
        time_interval = 24 * 60 // max(count, 1)  # minutes between actions
        
        for i in range(count):
            # Calculate when this action should run
            not_before = datetime.utcnow() + timedelta(minutes=i * time_interval)
            
            job_data = {
                'account_id': account.id,
                'device_id': device_id,
                'platform': account.platform,
                'type': job_type.value if hasattr(job_type, 'value') else str(job_type),
                'priority': priority,
                'payload': {
                    'action_type': action_name,
                    'content_type': content_type,
                    'content_path': content_path,
                    'template_id': getattr(account, 'template_id', None),
                    'template_name': getattr(account, 'template_name', None)
                },
                'not_before': not_before.isoformat(),
                'max_attempts': 3
            }
            
            jobs.append(job_data)
        
        return jobs

# Global instance
template_job_converter = TemplateJobConverter()
