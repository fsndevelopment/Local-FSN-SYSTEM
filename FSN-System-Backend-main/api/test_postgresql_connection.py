#!/usr/bin/env python3
"""
Test PostgreSQL connection for FSN Backend
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Database URL - same as in config.py
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

async def test_postgresql_connection():
    """Test PostgreSQL connection and table access"""
    
    print("🔄 Testing PostgreSQL connection...")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Test basic connection
            result = await conn.execute(text("SELECT 1"))
            print("✅ Basic connection test successful!")
            
            # Check if models table exists
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'models'
            """))
            tables = result.fetchall()
            
            if tables:
                print("✅ Models table exists!")
                
                # Check models count
                result = await conn.execute(text("SELECT COUNT(*) FROM models"))
                count = result.scalar()
                print(f"📊 Models in database: {count}")
                
                # Check models with license key
                result = await conn.execute(text("""
                    SELECT id, name, license_key, created_at 
                    FROM models 
                    WHERE license_key = '651A6308E6BD453C8E8C10EEF4F334A2'
                """))
                models = result.fetchall()
                print(f"📊 Models for your license: {len(models)}")
                for model in models:
                    print(f"  - ID: {model[0]}, Name: {model[1]}, License: {model[2]}, Created: {model[3]}")
                
            else:
                print("❌ Models table does not exist!")
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        raise
    finally:
        await engine.dispose()
    
    print("🎉 PostgreSQL test completed!")

if __name__ == "__main__":
    asyncio.run(test_postgresql_connection())
