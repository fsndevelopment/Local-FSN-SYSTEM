#!/usr/bin/env python3
"""
Fix auth_type column to be nullable to match the model definition
"""

import asyncio
import asyncpg
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger()

# Database URL
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

async def fix_auth_type_column():
    """Fix auth_type column to be nullable"""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # Check current auth_type column definition
            logger.info("Checking current auth_type column definition...")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'accounts' 
                AND column_name = 'auth_type'
                AND table_schema = 'public';
            """))
            column_info = result.fetchone()
            
            if column_info:
                logger.info(f"Current auth_type column: {column_info[0]}, type: {column_info[1]}, nullable: {column_info[2]}, default: {column_info[3]}")
                
                if column_info[2] == 'NO':
                    logger.info("auth_type column is NOT NULL, fixing to be nullable...")
                    
                    # Update existing NULL values first (if any)
                    logger.info("Setting default values for existing NULL auth_type records...")
                    await conn.execute(text("""
                        UPDATE accounts 
                        SET auth_type = 'non-2fa' 
                        WHERE auth_type IS NULL;
                    """))
                    
                    # Make the column nullable
                    logger.info("Making auth_type column nullable...")
                    await conn.execute(text("""
                        ALTER TABLE accounts 
                        ALTER COLUMN auth_type DROP NOT NULL;
                    """))
                    
                    logger.info("✅ auth_type column fixed successfully!")
                else:
                    logger.info("✅ auth_type column is already nullable")
            else:
                logger.error("❌ auth_type column not found!")
            
            # Verify the fix
            logger.info("Verifying the fix...")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'accounts' 
                AND column_name = 'auth_type'
                AND table_schema = 'public';
            """))
            column_info = result.fetchone()
            
            if column_info:
                logger.info(f"Updated auth_type column: {column_info[0]}, type: {column_info[1]}, nullable: {column_info[2]}, default: {column_info[3]}")
                
                # Test account creation
                logger.info("Testing account creation with NULL auth_type...")
                try:
                    await conn.execute(text("""
                        INSERT INTO accounts (
                            username, platform, password, license_key, auth_type,
                            created_at, updated_at
                        ) VALUES (
                            'test_auth_type_fix', 'instagram', 'testpass123', 
                            '651A6308E6BD453C8E8C10EEF4F334A2', NULL,
                            NOW(), NOW()
                        );
                    """))
                    logger.info("✅ Account creation with NULL auth_type works!")
                    
                    # Clean up test account
                    await conn.execute(text("""
                        DELETE FROM accounts 
                        WHERE username = 'test_auth_type_fix';
                    """))
                    logger.info("Test account cleaned up")
                    
                except Exception as e:
                    logger.error(f"❌ Account creation still fails: {e}")
            
    except Exception as e:
        logger.error(f"❌ Failed to fix auth_type column: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_auth_type_column())

