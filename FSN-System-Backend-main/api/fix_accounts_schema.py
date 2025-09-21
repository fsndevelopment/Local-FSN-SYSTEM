#!/usr/bin/env python3
"""
Fix accounts table schema to include missing columns
"""

import asyncio
import asyncpg
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger()

# Database URL from environment or config
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

async def fix_accounts_schema():
    """Fix the accounts table schema by adding missing columns"""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # Check if accounts table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'accounts'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("Creating accounts table...")
                await conn.execute(text("""
                    CREATE TABLE accounts (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) NOT NULL,
                        email VARCHAR(255),
                        phone VARCHAR(20),
                        password VARCHAR(255),
                        auth_type VARCHAR(50) DEFAULT 'password',
                        two_factor_code VARCHAR(10),
                        platform VARCHAR(50) NOT NULL,
                        instagram_username VARCHAR(100),
                        threads_username VARCHAR(100),
                        model_id INTEGER,
                        device_id INTEGER,
                        notes TEXT,
                        container_number INTEGER,
                        license_key VARCHAR(100) NOT NULL,
                        status VARCHAR(50) DEFAULT 'active',
                        warmup_phase VARCHAR(50),
                        warmup_start_date TIMESTAMP,
                        bio TEXT,
                        profile_image_url VARCHAR(500),
                        followers_count INTEGER DEFAULT 0,
                        following_count INTEGER DEFAULT 0,
                        posts_count INTEGER DEFAULT 0,
                        last_activity TIMESTAMP,
                        settings JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
            else:
                logger.info("Accounts table exists, checking for missing columns...")
                
                # Check which columns exist
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'accounts' 
                    AND table_schema = 'public';
                """))
                existing_columns = {row[0] for row in result.fetchall()}
                logger.info(f"Existing columns: {existing_columns}")
                
                # Define required columns
                required_columns = {
                    'email': 'VARCHAR(255)',
                    'phone': 'VARCHAR(20)',
                    'password': 'VARCHAR(255)',
                    'auth_type': 'VARCHAR(50) DEFAULT \'password\'',
                    'two_factor_code': 'VARCHAR(10)',
                    'instagram_username': 'VARCHAR(100)',
                    'threads_username': 'VARCHAR(100)',
                    'model_id': 'INTEGER',
                    'device_id': 'INTEGER',
                    'notes': 'TEXT',
                    'container_number': 'INTEGER',
                    'license_key': 'VARCHAR(100) NOT NULL',
                    'status': 'VARCHAR(50) DEFAULT \'active\'',
                    'warmup_phase': 'VARCHAR(50)',
                    'warmup_start_date': 'TIMESTAMP',
                    'bio': 'TEXT',
                    'profile_image_url': 'VARCHAR(500)',
                    'followers_count': 'INTEGER DEFAULT 0',
                    'following_count': 'INTEGER DEFAULT 0',
                    'posts_count': 'INTEGER DEFAULT 0',
                    'last_activity': 'TIMESTAMP',
                    'settings': 'JSONB',
                    'created_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
                    'updated_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'
                }
                
                # Add missing columns
                for column_name, column_definition in required_columns.items():
                    if column_name not in existing_columns:
                        logger.info(f"Adding missing column: {column_name}")
                        try:
                            await conn.execute(text(f"ALTER TABLE accounts ADD COLUMN {column_name} {column_definition};"))
                            logger.info(f"✅ Added column {column_name}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to add column {column_name}: {e}")
                    else:
                        logger.info(f"✅ Column {column_name} already exists")
            
            # Create indexes
            logger.info("Creating indexes...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_accounts_license_key ON accounts(license_key);",
                "CREATE INDEX IF NOT EXISTS idx_accounts_model_id ON accounts(model_id);",
                "CREATE INDEX IF NOT EXISTS idx_accounts_device_id ON accounts(device_id);",
                "CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform);"
            ]
            
            for index_sql in indexes:
                try:
                    await conn.execute(text(index_sql))
                    logger.info(f"✅ Created index")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to create index: {e}")
            
            logger.info("✅ Accounts table schema fixed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Failed to fix accounts schema: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_accounts_schema())

