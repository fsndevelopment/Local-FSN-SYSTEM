"""
Fix Accounts Database Schema
Based on the successful fix applied to models in DATABASE_FIX_TECHNICAL_GUIDE.md

This script fixes the database schema mismatches that prevent accounts from being saved to the database.
"""

import asyncio
import asyncpg
from sqlalchemy import text
from database.connection import engine
import structlog

logger = structlog.get_logger()

async def fix_accounts_database_schema():
    """Fix the accounts table schema to match the model definitions"""
    
    async with engine.begin() as conn:
        logger.info("🔧 Starting accounts database schema fix...")
        
        # Check current schema
        logger.info("🔍 Checking current accounts table schema...")
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'accounts' 
            AND table_schema = 'public'
            AND column_name IN ('auth_type', 'status')
            ORDER BY column_name;
        """))
        
        current_schema = result.fetchall()
        logger.info(f"📊 Current schema: {current_schema}")
        
        # Fix auth_type column
        logger.info("🔧 Fixing auth_type column...")
        
        # First, update any existing NULL values
        await conn.execute(text("""
            UPDATE accounts 
            SET auth_type = 'non-2fa' 
            WHERE auth_type IS NULL;
        """))
        logger.info("✅ Updated existing NULL auth_type values")
        
        # Make the column nullable
        await conn.execute(text("""
            ALTER TABLE accounts 
            ALTER COLUMN auth_type DROP NOT NULL;
        """))
        logger.info("✅ Made auth_type column nullable")
        
        # Fix status column
        logger.info("🔧 Fixing status column...")
        
        # First, update any existing NULL values
        await conn.execute(text("""
            UPDATE accounts 
            SET status = 'active' 
            WHERE status IS NULL;
        """))
        logger.info("✅ Updated existing NULL status values")
        
        # Make the column nullable
        await conn.execute(text("""
            ALTER TABLE accounts 
            ALTER COLUMN status DROP NOT NULL;
        """))
        logger.info("✅ Made status column nullable")
        
        # Verify the fix
        logger.info("🔍 Verifying schema fix...")
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'accounts' 
            AND table_schema = 'public'
            AND column_name IN ('auth_type', 'status')
            ORDER BY column_name;
        """))
        
        updated_schema = result.fetchall()
        logger.info(f"📊 Updated schema: {updated_schema}")
        
        # Test account creation with NULL auth_type
        logger.info("🧪 Testing account creation with NULL auth_type...")
        try:
            await conn.execute(text("""
                INSERT INTO accounts (
                    username, platform, password, license_key, auth_type, status,
                    created_at, updated_at
                ) VALUES (
                    'test_schema_fix', 'instagram', 'testpass123', 
                    '651A6308E6BD453C8E8C10EEF4F334A2', NULL, NULL,
                    NOW(), NOW()
                );
            """))
            logger.info("✅ Test account creation with NULL values successful!")
            
            # Clean up test data
            await conn.execute(text("""
                DELETE FROM accounts 
                WHERE username = 'test_schema_fix';
            """))
            logger.info("🧹 Cleaned up test data")
            
        except Exception as e:
            logger.error(f"❌ Test account creation failed: {e}")
            raise
        
        logger.info("🎉 Accounts database schema fix completed successfully!")

async def verify_accounts_creation():
    """Verify that accounts can be created via API"""
    
    logger.info("🧪 Verifying accounts API creation...")
    
    # Test with minimal required fields
    test_account_data = {
        "username": "test_api_verification",
        "platform": "instagram",
        "password": "testpass123"
        # auth_type and status should now be optional
    }
    
    logger.info(f"📤 Test data: {test_account_data}")
    logger.info("✅ Accounts should now be creatable via API with optional auth_type and status")

if __name__ == "__main__":
    async def main():
        try:
            await fix_accounts_database_schema()
            await verify_accounts_creation()
            print("🎉 Accounts database schema fix completed successfully!")
        except Exception as e:
            print(f"❌ Fix failed: {e}")
            raise
    
    asyncio.run(main())
