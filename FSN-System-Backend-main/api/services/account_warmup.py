"""
Account Warmup System
Gradually increases activity on new accounts to avoid Instagram detection
"""
import asyncio
import random
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.connection import get_db, AsyncSessionLocal
from models.account import Account
from models.job import Job, JobType, JobStatus, JobPriority
from .instagram_automation import instagram_automation

logger = logging.getLogger(__name__)

class WarmupPhase(Enum):
    """Account warmup phases"""
    FRESH = "fresh"
    WARMING = "warming" 
    ACTIVE = "active"
    ESTABLISHED = "established"

class WarmupSchedule:
    """Defines warmup activities for each phase"""
    
    PHASES = {
        WarmupPhase.FRESH: {
            'duration_days': 3,
            'daily_activities': {
                'login_sessions': {'min': 2, 'max': 4},
                'profile_views': {'min': 5, 'max': 15},
                'story_views': {'min': 3, 'max': 8},
                'search_queries': {'min': 2, 'max': 5},
                'explore_browsing': {'min': 5, 'max': 10}  # minutes
            },
            'restrictions': {
                'no_follows': True,
                'no_likes': True,
                'no_comments': True,
                'no_dms': True,
                'no_posting': True
            }
        },
        WarmupPhase.WARMING: {
            'duration_days': 7,
            'daily_activities': {
                'login_sessions': {'min': 3, 'max': 6},
                'profile_views': {'min': 10, 'max': 25},
                'story_views': {'min': 5, 'max': 15},
                'search_queries': {'min': 3, 'max': 8},
                'explore_browsing': {'min': 8, 'max': 15},
                'likes': {'min': 5, 'max': 20},
                'follows': {'min': 2, 'max': 8}
            },
            'restrictions': {
                'no_comments': True,
                'no_dms': True,
                'no_posting': True,
                'limited_follows': True,
                'limited_likes': True
            }
        },
        WarmupPhase.ACTIVE: {
            'duration_days': 14,
            'daily_activities': {
                'login_sessions': {'min': 4, 'max': 8},
                'profile_views': {'min': 15, 'max': 40},
                'story_views': {'min': 10, 'max': 25},
                'search_queries': {'min': 5, 'max': 12},
                'explore_browsing': {'min': 10, 'max': 20},
                'likes': {'min': 15, 'max': 50},
                'follows': {'min': 5, 'max': 20},
                'comments': {'min': 2, 'max': 8},
                'profile_updates': {'min': 0, 'max': 2}
            },
            'restrictions': {
                'no_dms': True,
                'limited_posting': True,
                'moderate_activity': True
            }
        },
        WarmupPhase.ESTABLISHED: {
            'duration_days': None,  # Ongoing
            'daily_activities': {
                'login_sessions': {'min': 5, 'max': 12},
                'profile_views': {'min': 20, 'max': 60},
                'story_views': {'min': 15, 'max': 40},
                'search_queries': {'min': 8, 'max': 20},
                'explore_browsing': {'min': 15, 'max': 30},
                'likes': {'min': 25, 'max': 100},
                'follows': {'min': 10, 'max': 40},
                'comments': {'min': 5, 'max': 20},
                'dms': {'min': 2, 'max': 10},
                'posts': {'min': 0, 'max': 3}
            },
            'restrictions': {
                'full_activity': True
            }
        }
    }

class AccountWarmupSystem:
    """Manages account warmup process"""
    
    def __init__(self):
        self.running = False
        self.warmup_task = None
        
    async def start(self):
        """Start the warmup system"""
        if self.running:
            return
            
        self.running = True
        self.warmup_task = asyncio.create_task(self._warmup_monitor())
        logger.info("🌡️ Account warmup system started")
    
    async def stop(self):
        """Stop the warmup system"""
        if not self.running:
            return
            
        self.running = False
        if self.warmup_task:
            self.warmup_task.cancel()
            try:
                await self.warmup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🌡️ Account warmup system stopped")
    
    async def _warmup_monitor(self):
        """Monitor accounts and schedule warmup activities"""
        while self.running:
            try:
                async with AsyncSessionLocal() as db:
                    # Get accounts that need warmup activities
                    accounts = await self._get_warmup_accounts(db)
                    
                    for account in accounts:
                        try:
                            await self._schedule_warmup_activities(db, account)
                        except Exception as e:
                            logger.error(f"Error scheduling warmup for account {account.id}: {e}")
                
                # Check every hour
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Warmup monitor error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _get_warmup_accounts(self, db: AsyncSession) -> List[Account]:
        """Get accounts that need warmup activities"""
        try:
            result = await db.execute(
                select(Account).where(
                                    Account.warmup_phase.in_([
                    WarmupPhase.FRESH.value,
                    WarmupPhase.WARMING.value, 
                    WarmupPhase.ACTIVE.value,
                    WarmupPhase.ESTABLISHED.value
                ])
                )
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting warmup accounts: {e}")
            return []
    
    async def _schedule_warmup_activities(self, db: AsyncSession, account: Account):
        """Schedule warmup activities for an account"""
        try:
            # Check if account needs phase progression
            await self._check_phase_progression(db, account)
            
            # Get current phase schedule
            current_phase = self._string_to_phase(account.warmup_phase)
            phase_config = WarmupSchedule.PHASES.get(current_phase)
            if not phase_config:
                return
            
            # Check if activities already scheduled for today
            today = datetime.now().date()
            if await self._has_todays_activities(db, account.id, today):
                return
            
            # Schedule activities based on phase
            activities = phase_config['daily_activities']
            await self._create_warmup_jobs(db, account, activities, today)
            
            logger.info(f"📅 Scheduled warmup activities for account {account.username} (Phase: {account.warmup_phase})")
            
        except Exception as e:
            logger.error(f"Error scheduling warmup activities for account {account.id}: {e}")
    
    async def _check_phase_progression(self, db: AsyncSession, account: Account):
        """Check if account should progress to next warmup phase"""
        try:
            if not account.warmup_started_at:
                # Start warmup
                await db.execute(
                    update(Account).where(Account.id == account.id).values(
                        warmup_started_at=datetime.utcnow(),
                        warmup_phase=WarmupPhase.FRESH.value,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                logger.info(f"🌱 Started warmup for account {account.username}")
                return
            
            # Calculate days in current phase
            days_in_phase = (datetime.utcnow() - account.warmup_started_at).days
            current_phase = self._string_to_phase(account.warmup_phase)
            phase_config = WarmupSchedule.PHASES.get(current_phase)
            
            if not phase_config or not phase_config.get('duration_days'):
                return
            
            # Check if ready for next phase
            if days_in_phase >= phase_config['duration_days']:
                next_phase = self._get_next_phase(current_phase)
                if next_phase:
                    await db.execute(
                        update(Account).where(Account.id == account.id).values(
                            warmup_phase=next_phase.value,
                            updated_at=datetime.utcnow()
                        )
                    )
                    await db.commit()
                    logger.info(f"📈 Account {account.username} progressed to phase: {next_phase.value}")
                    
        except Exception as e:
            logger.error(f"Error checking phase progression for account {account.id}: {e}")
    
    def _get_next_phase(self, current_phase: WarmupPhase) -> Optional[WarmupPhase]:
        """Get the next warmup phase"""
        phase_order = [
            WarmupPhase.FRESH,
            WarmupPhase.WARMING,
            WarmupPhase.ACTIVE,
            WarmupPhase.ESTABLISHED
        ]
        
        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    async def _has_todays_activities(self, db: AsyncSession, account_id: int, date) -> bool:
        """Check if warmup activities already scheduled for today"""
        try:
            start_of_day = datetime.combine(date, datetime.min.time())
            end_of_day = datetime.combine(date, datetime.max.time())
            
            result = await db.execute(
                select(Job).where(
                    Job.account_id == account_id,
                    Job.created_at >= start_of_day,
                    Job.created_at <= end_of_day,
                    Job.tags.like('%warmup%')
                ).limit(1)
            )
            
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking today's activities: {e}")
            return False
    
    async def _create_warmup_jobs(self, db: AsyncSession, account: Account, activities: Dict, date):
        """Create warmup jobs for the day"""
        try:
            jobs_to_create = []
            base_time = datetime.combine(date, datetime.min.time()) + timedelta(hours=8)  # Start at 8 AM
            
            # Create login sessions throughout the day
            login_count = random.randint(
                activities['login_sessions']['min'],
                activities['login_sessions']['max']
            )
            
            for i in range(login_count):
                # Spread logins throughout the day
                session_time = base_time + timedelta(
                    hours=random.randint(0, 14),  # 8 AM to 10 PM
                    minutes=random.randint(0, 59)
                )
                
                jobs_to_create.append(Job(
                    account_id=account.id,
                    type=JobType.INSTAGRAM_LOGIN,
                    priority=JobPriority.LOW,
                    not_before=session_time,
                    payload={'warmup': True},
                    status=JobStatus.PENDING
                ))
            
            # Create story viewing jobs
            if 'story_views' in activities:
                story_count = random.randint(
                    activities['story_views']['min'],
                    activities['story_views']['max']
                )
                
                for i in range(story_count):
                    view_time = base_time + timedelta(
                        hours=random.randint(0, 14),
                        minutes=random.randint(0, 59)
                    )
                    
                    jobs_to_create.append(Job(
                        account_id=account.id,
                        type=JobType.VIEW_STORY,
                        priority=JobPriority.LOW,
                        not_before=view_time,
                        payload={'count': random.randint(1, 3), 'warmup': True},
                        status=JobStatus.PENDING
                    ))
            
            # Create like jobs (if allowed in this phase)
            if 'likes' in activities:
                like_count = random.randint(
                    activities['likes']['min'],
                    activities['likes']['max']
                )
                
                # Split likes into multiple sessions
                like_sessions = random.randint(2, 4)
                likes_per_session = like_count // like_sessions
                
                for session in range(like_sessions):
                    like_time = base_time + timedelta(
                        hours=random.randint(0, 14),
                        minutes=random.randint(0, 59)
                    )
                    
                    jobs_to_create.append(Job(
                        account_id=account.id,
                        type=JobType.LIKE_POST.value,
                        priority=JobPriority.LOW,
                        not_before=like_time,
                        payload={'count': likes_per_session, 'warmup': True},
                        status=JobStatus.PENDING
                    ))
            
            # Create follow jobs (if allowed in this phase)
            if 'follows' in activities:
                follow_count = random.randint(
                    activities['follows']['min'],
                    activities['follows']['max']
                )
                
                for i in range(follow_count):
                    follow_time = base_time + timedelta(
                        hours=random.randint(0, 14),
                        minutes=random.randint(0, 59)
                    )
                    
                    # Use suggested users or hashtag followers
                    target_source = random.choice(['suggested', 'hashtag_followers'])
                    
                    jobs_to_create.append(Job(
                        account_id=account.id,
                        type=JobType.FOLLOW_USER,
                        priority=JobPriority.LOW,
                        not_before=follow_time,
                        payload={
                            'target_source': target_source,
                            'warmup': True
                        },
                        status=JobStatus.PENDING
                    ))
            
            # Create comment jobs (if allowed in this phase)
            if 'comments' in activities:
                comment_count = random.randint(
                    activities['comments']['min'],
                    activities['comments']['max']
                )
                
                warmup_comments = [
                    "Nice!", "Great post!", "Amazing!", "Love this!", "Beautiful!",
                    "Awesome!", "Cool!", "Perfect!", "Incredible!", "Fantastic!"
                ]
                
                for i in range(comment_count):
                    comment_time = base_time + timedelta(
                        hours=random.randint(0, 14),
                        minutes=random.randint(0, 59)
                    )
                    
                    jobs_to_create.append(Job(
                        account_id=account.id,
                        type=JobType.COMMENT_POST,
                        priority=JobPriority.LOW,
                        not_before=comment_time,
                        payload={
                            'comments': warmup_comments,
                            'count': 1,
                            'warmup': True
                        },
                        status=JobStatus.PENDING
                    ))
            
            # Add all jobs to database
            for job in jobs_to_create:
                db.add(job)
            
            await db.commit()
            logger.info(f"✅ Created {len(jobs_to_create)} warmup jobs for account {account.username}")
            
        except Exception as e:
            logger.error(f"Error creating warmup jobs: {e}")
            await db.rollback()
    
    async def get_warmup_status(self, account_id: int) -> Dict[str, Any]:
        """Get warmup status for an account"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(Account).where(Account.id == account_id))
                account = result.scalar_one_or_none()
                
                if not account:
                    return {'error': 'Account not found'}
                
                current_phase = self._string_to_phase(account.warmup_phase)
                phase_config = WarmupSchedule.PHASES.get(current_phase, {})
                
                # Calculate progress
                progress = 0
                if account.warmup_started_at:
                    days_in_phase = (datetime.utcnow() - account.warmup_started_at).days
                    phase_duration = phase_config.get('duration_days', 1)
                    if phase_duration:
                        progress = min(100, (days_in_phase / phase_duration) * 100)
                
                return {
                    'account_id': account.id,
                    'username': account.username,
                    'current_phase': account.warmup_phase,
                    'warmup_started': account.warmup_started_at.isoformat() if account.warmup_started_at else None,
                    'days_in_current_phase': days_in_phase if account.warmup_started_at else 0,
                    'phase_progress_percent': progress,
                    'phase_config': phase_config,
                    'next_phase': self._get_next_phase(current_phase).value if self._get_next_phase(current_phase) else None,
                    'restrictions': phase_config.get('restrictions', {}),
                    'daily_activities': phase_config.get('daily_activities', {})
                }
                
            except Exception as e:
                logger.error(f"Error getting warmup status: {e}")
                return {'error': str(e)}
    
    def _string_to_phase(self, phase_str: str) -> Optional[WarmupPhase]:
        """Convert string to WarmupPhase enum"""
        if not phase_str:
            return WarmupPhase.FRESH
        
        phase_map = {
            'fresh': WarmupPhase.FRESH,
            'warming': WarmupPhase.WARMING,
            'active': WarmupPhase.ACTIVE,
            'established': WarmupPhase.ESTABLISHED
        }
        return phase_map.get(phase_str.lower(), WarmupPhase.FRESH)


# Global instance
account_warmup_system = AccountWarmupSystem()
