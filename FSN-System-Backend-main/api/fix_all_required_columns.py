#!/usr/bin/env python3
"""
Fix all required columns to be nullable to match the model definition
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

async def fix_all_required_columns():
    """Fix all required columns to be nullable"""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # Check current column definitions
            logger.info("Checking current column definitions...")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'accounts' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            
            logger.info("Current columns:")
            for col in columns:
                logger.info(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # Columns that should be nullable according to the model
            columns_to_fix = [
                ('auth_type', 'non-2fa'),
                ('status', 'active'),
            ]
            
            for column_name, default_value in columns_to_fix:
                logger.info(f"Fixing column: {column_name}")
                
                # Update existing NULL values first (if any)
                logger.info(f"Setting default values for existing NULL {column_name} records...")
                await conn.execute(text(f"""
                    UPDATE accounts 
                    SET {column_name} = '{default_value}' 
                    WHERE {column_name} IS NULL;
                """))
                
                # Make the column nullable
                logger.info(f"Making {column_name} column nullable...")
                await conn.execute(text(f"""
                    ALTER TABLE accounts 
                    ALTER COLUMN {column_name} DROP NOT NULL;
                """))
                
                logger.info(f"✅ {column_name} column fixed successfully!")
            
            # Verify the fix
            logger.info("Verifying the fix...")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'accounts' 
                AND column_name IN ('auth_type', 'status')
                AND table_schema = 'public'
                ORDER BY column_name;
            """))
            fixed_columns = result.fetchall()
            
            logger.info("Fixed columns:")
            for col in fixed_columns:
                logger.info(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # Test account creation
            logger.info("Testing account creation...")
            try:
                await conn.execute(text("""
                    INSERT INTO accounts (
                        username, platform, password, license_key, 
                        created_at, updated_at
                    ) VALUES (
                        'test_full_fix', 'instagram', 'testpass123', 
                        '651A6308E6BD453C8E8C10EEF4F334A2',
                        NOW(), NOW()
                    );
                """))
                logger.info("✅ Instagram account creation works!")
                
                # Test Threads account creation
                await conn.execute(text("""
                    INSERT INTO accounts (
                        username, platform, password, license_key, 
                        created_at, updated_at
                    ) VALUES (
                        'test_threads_full_fix', 'threads', 'testpass123', 
                        '651A6308E6BD453C8E8C10EEF4F334A2',
                        NOW(), NOW()
                    );
                """))
                logger.info("✅ Threads account creation works!")
                
                # Clean up test accounts
                await conn.execute(text("""
                    DELETE FROM accounts 
                    WHERE username LIKE 'test_%_full_fix';
                """))
                logger.info("Test accounts cleaned up")
                
            except Exception as e:
                logger.error(f"❌ Account creation still fails: {e}")
            
    except Exception as e:
        logger.error(f"❌ Failed to fix columns: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_all_required_columns())

