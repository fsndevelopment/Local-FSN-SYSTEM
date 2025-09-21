#!/usr/bin/env python3
"""
Setup PostgreSQL tables for FSN Backend
This script creates the necessary tables in the PostgreSQL database.
"""

import asyncio
from sqlalchemy import create_engine, text, Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# Database URL - same as license system
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

Base = declarative_base()

class Model(Base):
    """Model/Influencer profile that accounts belong to"""
    
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    profile_photo = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    age_range = Column(String(20), nullable=True)
    location = Column(String(100), nullable=True)
    interests = Column(JSON, nullable=True)
    posting_schedule = Column(JSON, nullable=True)
    engagement_strategy = Column(JSON, nullable=True)
    content_preferences = Column(JSON, nullable=True)
    license_key = Column(String(100), nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Account(Base):
    """Social media account for automation"""
    
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    auth_type = Column(String(20), nullable=False, default="non-2fa")
    platform = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="inactive")
    warmup_phase = Column(String(20), nullable=True)
    
    # Model association
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    
    # Device association
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    container_number = Column(Integer, nullable=True)
    
    # License key for data isolation
    license_key = Column(String(100), nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Device(Base):
    """Device model for iPhone management"""
    
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    udid = Column(String(100), unique=True, nullable=False)
    ios_version = Column(String(20), nullable=True)
    model = Column(String(50), nullable=True)
    appium_port = Column(Integer, nullable=False, default=4723)
    wda_port = Column(Integer, nullable=False, default=8100)
    mjpeg_port = Column(Integer, nullable=False, default=9100)
    wda_bundle_id = Column(String(100), nullable=True)
    jailbroken = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="offline")
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    proxy_pool_id = Column(Integer, nullable=True)  # Removed FK to avoid dependency issues
    settings = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

async def setup_postgresql_tables():
    """Create all necessary tables in PostgreSQL"""
    
    print("🔄 Setting up PostgreSQL tables for FSN Backend...")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            # Check if tables already exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('models', 'accounts', 'devices')
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            
            if existing_tables:
                print(f"📋 Found existing tables: {existing_tables}")
                print("⚠️  Tables already exist. Skipping creation.")
            else:
                print("📋 No existing tables found. Creating tables...")
                await conn.run_sync(Base.metadata.create_all)
                print("✅ All tables created successfully!")
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection test successful!")
            
    except Exception as e:
        print(f"❌ Error setting up PostgreSQL tables: {e}")
        raise
    finally:
        await engine.dispose()
    
    print("🎉 PostgreSQL setup completed successfully!")

if __name__ == "__main__":
    asyncio.run(setup_postgresql_tables())
