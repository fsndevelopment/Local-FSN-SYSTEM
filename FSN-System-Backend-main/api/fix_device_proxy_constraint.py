#!/usr/bin/env python3
"""
Fix Device model proxy_pool_id foreign key constraint
This script removes the problematic foreign key constraint that references non-existent proxy_pools table.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Database URL - using existing license database
DATABASE_URL = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"

async def fix_device_proxy_constraint():
    """Remove the problematic foreign key constraint from devices table"""
    
    print("🔧 Fixing Device model proxy_pool_id constraint...")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Check if devices table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'devices'
                );
            """))
            devices_exists = result.scalar()
            
            if devices_exists:
                print("📋 Devices table exists, checking constraints...")
                
                # Check current constraints on devices table
                result = await conn.execute(text("""
                    SELECT constraint_name, constraint_type, column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = 'devices' 
                    AND tc.constraint_type = 'FOREIGN KEY'
                """))
                
                constraints = result.fetchall()
                print(f"📊 Found {len(constraints)} foreign key constraints:")
                for constraint in constraints:
                    print(f"  - {constraint[0]}: {constraint[2]} -> {constraint[1]}")
                
                # Check if proxy_pool_id column exists
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'devices' AND column_name = 'proxy_pool_id'
                """))
                
                proxy_column = result.fetchone()
                if proxy_column:
                    print(f"📋 proxy_pool_id column exists: {proxy_column[1]} (nullable: {proxy_column[2]})")
                    
                    # Drop the foreign key constraint if it exists
                    try:
                        await conn.execute(text("""
                            ALTER TABLE devices 
                            DROP CONSTRAINT IF EXISTS devices_proxy_pool_id_fkey
                        """))
                        print("✅ Dropped foreign key constraint for proxy_pool_id")
                    except Exception as e:
                        print(f"⚠️ Could not drop constraint (may not exist): {e}")
                    
                    # Make sure the column is nullable
                    try:
                        await conn.execute(text("""
                            ALTER TABLE devices 
                            ALTER COLUMN proxy_pool_id DROP NOT NULL
                        """))
                        print("✅ Made proxy_pool_id column nullable")
                    except Exception as e:
                        print(f"⚠️ Could not modify column (may already be nullable): {e}")
                        
                else:
                    print("📋 proxy_pool_id column does not exist - this is fine")
                    
            else:
                print("📋 Devices table does not exist yet - will be created properly")
                
        print("✅ Device proxy constraint fix completed!")
        
    except Exception as e:
        print(f"❌ Error fixing device proxy constraint: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_device_proxy_constraint())
