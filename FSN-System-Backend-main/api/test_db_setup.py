#!/usr/bin/env python3
"""
Test script to verify database setup and create tables if needed
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect
from database.connection import Base
from models import device, account, job, content

DATABASE_URL = "sqlite+aiosqlite:///./fsn_appium_farm.db"

async def test_database_setup():
    """Test and setup database"""
    
    print("🔄 Testing database setup...")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Check if tables exist
            inspector = inspect(engine.sync_engine)
            existing_tables = inspector.get_table_names()
            print(f"📋 Existing tables: {existing_tables}")
            
            # Create all tables
            print("🔧 Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
            
            # Check tables again
            inspector = inspect(engine.sync_engine)
            new_tables = inspector.get_table_names()
            print(f"📋 Tables after creation: {new_tables}")
            
            # Test inserting a model
            print("🧪 Testing model insertion...")
            from models.account import Model
            from datetime import datetime
            
            test_model = Model(
                name="Test Model",
                profile_photo="test.jpg",
                license_key="test-license-123"
            )
            
            # Create session
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as session:
                session.add(test_model)
                await session.commit()
                await session.refresh(test_model)
                print(f"✅ Created test model with ID: {test_model.id}")
                
                # Test retrieving models
                from sqlalchemy import select
                result = await session.execute(select(Model))
                models = result.scalars().all()
                print(f"📊 Retrieved {len(models)} models from database")
                
                for model in models:
                    print(f"   - Model: {model.name} (ID: {model.id}, License: {model.license_key})")
            
            print("🎉 Database setup test completed successfully!")
            
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_database_setup())
