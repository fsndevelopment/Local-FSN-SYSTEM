#!/usr/bin/env python3
"""
Direct Device Fix Script
Fixes the device connection issue by directly updating the database
"""

import asyncio
import sys
import os

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from database.connection import get_db
from models.device import Device

async def fix_device():
    """Fix the device by assigning it to a mock agent"""
    
    # Your device UDID
    device_udid = "ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf"
    
    print(f"🔧 Fixing device: {device_udid}")
    
    async for db in get_db():
        try:
            # Find the device
            result = await db.execute(select(Device).where(Device.udid == device_udid))
            device = result.scalar_one_or_none()
            
            if not device:
                print(f"❌ Device {device_udid} not found in database")
                return
            
            print(f"📱 Found device: {device.name} (ID: {device.id})")
            print(f"   Current status: {device.status}")
            print(f"   Current agent_id: {device.agent_id}")
            
            # Update the device
            await db.execute(
                update(Device)
                .where(Device.id == device.id)
                .values(
                    agent_id="mock_agent_fix",
                    platform="iOS",
                    status="offline",  # Start as offline, will be updated when connected
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            print(f"✅ Device {device_udid} fixed successfully!")
            print(f"   Assigned to mock agent: mock_agent_fix")
            print(f"   Platform set to: iOS")
            print(f"   Status set to: offline")
            
            # Verify the fix
            result = await db.execute(select(Device).where(Device.udid == device_udid))
            updated_device = result.scalar_one_or_none()
            
            print(f"\n📋 Updated device info:")
            print(f"   ID: {updated_device.id}")
            print(f"   Name: {updated_device.name}")
            print(f"   UDID: {updated_device.udid}")
            print(f"   Status: {updated_device.status}")
            print(f"   Agent ID: {updated_device.agent_id}")
            print(f"   Platform: {updated_device.platform}")
            
            break
            
        except Exception as e:
            print(f"❌ Error fixing device: {e}")
            await db.rollback()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(fix_device())
