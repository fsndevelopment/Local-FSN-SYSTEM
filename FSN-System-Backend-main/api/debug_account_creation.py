#!/usr/bin/env python3
"""
Debug account creation issue - test Instagram vs Threads account creation
"""

import asyncio
import asyncpg
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
import structlog
from datetime import datetime

logger = structlog.get_logger()

# Database URL
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

async def debug_account_creation():
    """Debug account creation for Instagram vs Threads"""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # Check existing accounts
            logger.info("Checking existing accounts...")
            result = await conn.execute(text("""
                SELECT id, username, platform, license_key, created_at 
                FROM accounts 
                ORDER BY created_at DESC 
                LIMIT 10;
            """))
            accounts = result.fetchall()
            
            logger.info(f"Found {len(accounts)} existing accounts:")
            for account in accounts:
                logger.info(f"  ID: {account[0]}, Username: {account[1]}, Platform: {account[2]}, License: {account[3][:10]}...")
            
            # Check account schema
            logger.info("Checking accounts table schema...")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'accounts' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            
            logger.info("Accounts table columns:")
            for col in columns:
                logger.info(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # Test account creation directly
            logger.info("Testing direct account creation...")
            
            # Test 1: Instagram account
            logger.info("Test 1: Creating Instagram account...")
            try:
                await conn.execute(text("""
                    INSERT INTO accounts (
                        username, platform, password, license_key, 
                        created_at, updated_at
                    ) VALUES (
                        'test_instagram_debug', 'instagram', 'testpass123', 
                        '651A6308E6BD453C8E8C10EEF4F334A2',
                        NOW(), NOW()
                    );
                """))
                logger.info("✅ Instagram account created successfully")
            except Exception as e:
                logger.error(f"❌ Instagram account creation failed: {e}")
            
            # Test 2: Threads account
            logger.info("Test 2: Creating Threads account...")
            try:
                await conn.execute(text("""
                    INSERT INTO accounts (
                        username, platform, password, license_key, 
                        created_at, updated_at
                    ) VALUES (
                        'test_threads_debug', 'threads', 'testpass123', 
                        '651A6308E6BD453C8E8C10EEF4F334A2',
                        NOW(), NOW()
                    );
                """))
                logger.info("✅ Threads account created successfully")
            except Exception as e:
                logger.error(f"❌ Threads account creation failed: {e}")
            
            # Check if accounts were created
            result = await conn.execute(text("""
                SELECT id, username, platform, created_at 
                FROM accounts 
                WHERE username LIKE 'test_%_debug'
                ORDER BY created_at DESC;
            """))
            test_accounts = result.fetchall()
            
            logger.info(f"Test accounts created: {len(test_accounts)}")
            for account in test_accounts:
                logger.info(f"  ID: {account[0]}, Username: {account[1]}, Platform: {account[2]}")
            
            # Clean up test accounts
            logger.info("Cleaning up test accounts...")
            await conn.execute(text("""
                DELETE FROM accounts 
                WHERE username LIKE 'test_%_debug';
            """))
            logger.info("Test accounts cleaned up")
            
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(debug_account_creation())

