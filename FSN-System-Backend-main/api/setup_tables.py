#!/usr/bin/env python3
"""
Setup backend tables in PostgreSQL license database
This script creates the backend tables (models, accounts, devices) in the existing license database.
"""

import asyncio
import sys
import os

# Add the api directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from models.account import Base, Model, Account
from models.device import Device

# Database URL - using existing license database
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

async def setup_backend_tables():
    """Create backend tables in the PostgreSQL license database"""
    
    print("🔄 Setting up FSN Backend tables in PostgreSQL license database...")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        # Create all backend tables
        async with engine.begin() as conn:
            print("📋 Creating backend tables...")
            
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('models', 'accounts', 'devices')
            """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"📊 Existing tables: {existing_tables}")
            
            # Always recreate tables to ensure proper schema
            print("🔨 Creating/updating backend tables...")
            
            # Drop existing tables if they exist (to recreate with proper schema)
            if 'devices' in existing_tables:
                print("🗑️ Dropping existing devices table to recreate with proper schema...")
                await conn.execute(text("DROP TABLE IF EXISTS devices CASCADE"))
            
            if 'accounts' in existing_tables:
                print("🗑️ Dropping existing accounts table to recreate with proper schema...")
                await conn.execute(text("DROP TABLE IF EXISTS accounts CASCADE"))
                
            if 'models' in existing_tables:
                print("🗑️ Dropping existing models table to recreate with proper schema...")
                await conn.execute(text("DROP TABLE IF EXISTS models CASCADE"))
            
            # Create all tables with proper schema
            await conn.run_sync(Base.metadata.create_all, bind=engine.sync_engine)
            print("✅ Backend tables created/updated successfully")
            
            # Test connection
            result = await conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("✅ Database connection test successful!")
            else:
                print("❌ Database connection test failed.")
                
    except Exception as e:
        print(f"❌ Error setting up backend tables: {e}")
        raise
    finally:
        await engine.dispose()
        
    print("🎉 Backend tables setup completed!")

if __name__ == "__main__":
    asyncio.run(setup_backend_tables())
