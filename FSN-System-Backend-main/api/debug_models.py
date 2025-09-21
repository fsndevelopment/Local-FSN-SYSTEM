#!/usr/bin/env python3
"""
Debug script to check models in database
"""

import asyncio
import sys
import os

# Add the api directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from models.account import Model

# Database URL - using existing license database
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

async def debug_models():
    """Check all models in the database"""
    
    print("🔍 Debugging models in PostgreSQL database...")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        async with engine.connect() as conn:
            # Check all models
            result = await conn.execute(text("SELECT id, name, license_key, created_at FROM models ORDER BY created_at DESC"))
            models = result.fetchall()
            
            print(f"📊 Total models in database: {len(models)}")
            print("=" * 60)
            
            for model in models:
                print(f"ID: {model[0]}")
                print(f"Name: {model[1]}")
                print(f"License Key: {model[2]}")
                print(f"Created: {model[3]}")
                print("-" * 40)
                
            # Check specific license key
            license_key = "651A6308E6BD453C8E8C10EEF4F334A2"
            result = await conn.execute(text("SELECT COUNT(*) FROM models WHERE license_key = :license_key"), {"license_key": license_key})
            count = result.scalar()
            print(f"📋 Models for license '{license_key}': {count}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_models())
