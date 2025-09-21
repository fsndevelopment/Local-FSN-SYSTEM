#!/usr/bin/env python3
"""
Database migration to fix datetime validation errors.
This script updates NULL updated_at fields to use created_at values.
"""

import asyncio
from sqlalchemy import create_engine, text, Column, String, Integer, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# Database URL - adjust for your environment
DATABASE_URL = "sqlite+aiosqlite:///./fsn_appium_farm.db"  # For SQLite
# DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"  # For PostgreSQL

Base = declarative_base()

async def fix_datetime_fields():
    """Fix NULL updated_at fields in models and accounts tables"""
    
    print("🔄 Starting datetime field migration...")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Check if tables exist
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('models', 'accounts')"))
            tables = result.fetchall()
            table_names = [row[0] for row in tables]
            
            print(f"📋 Found tables: {table_names}")
            
            # Fix models table
            if 'models' in table_names:
                print("🔧 Fixing models.updated_at fields...")
                await conn.execute(text("""
                    UPDATE models 
                    SET updated_at = created_at 
                    WHERE updated_at IS NULL
                """))
                
                # Check how many records were updated
                result = await conn.execute(text("SELECT COUNT(*) FROM models WHERE updated_at IS NOT NULL"))
                count = result.scalar()
                print(f"✅ Models table: {count} records now have valid updated_at")
            
            # Fix accounts table
            if 'accounts' in table_names:
                print("🔧 Fixing accounts.updated_at fields...")
                await conn.execute(text("""
                    UPDATE accounts 
                    SET updated_at = created_at 
                    WHERE updated_at IS NULL
                """))
                
                # Check how many records were updated
                result = await conn.execute(text("SELECT COUNT(*) FROM accounts WHERE updated_at IS NOT NULL"))
                count = result.scalar()
                print(f"✅ Accounts table: {count} records now have valid updated_at")
            
            print("🎉 Datetime field migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_datetime_fields())
