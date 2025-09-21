#!/usr/bin/env python3
"""
Initialize PostgreSQL database for FSN Backend
This script ensures the backend tables are created in the license database.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from models.account import Base, Model, Account
from models.device import Device

# Database URL - using existing license database
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

async def init_database():
    """Initialize the PostgreSQL database with backend tables"""
    
    print("🔄 Initializing FSN Backend PostgreSQL database...")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            print("📋 Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All tables created successfully!")
            
            # Test the connection
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection test successful!")
            
            # Check if models table exists and is accessible
            try:
                models_result = await conn.execute(text("SELECT COUNT(*) FROM models"))
                models_count = models_result.scalar()
                print(f"📊 Models table accessible - current count: {models_count}")
            except Exception as e:
                print(f"⚠️ Models table check failed: {e}")
                
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    finally:
        await engine.dispose()
    
    print("🎉 Database initialization completed successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())
