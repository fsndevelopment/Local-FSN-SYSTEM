"""
Migration: Add license_key column to accounts table
"""

import asyncio
import asyncpg
from sqlalchemy import text
from database.connection import get_db

async def migrate_accounts_add_license_key():
    """Add license_key column to accounts table if it doesn't exist"""
    
    # SQL to add the license_key column
    add_column_sql = """
    ALTER TABLE accounts 
    ADD COLUMN IF NOT EXISTS license_key VARCHAR(100);
    """
    
    # SQL to create index on license_key
    add_index_sql = """
    CREATE INDEX IF NOT EXISTS ix_accounts_license_key 
    ON accounts (license_key);
    """
    
    try:
        # Get database connection
        async for db in get_db():
            # Add the column
            await db.execute(text(add_column_sql))
            print("✅ Added license_key column to accounts table")
            
            # Add the index
            await db.execute(text(add_index_sql))
            print("✅ Added index on license_key column")
            
            # Commit the changes
            await db.commit()
            print("✅ Migration completed successfully")
            break
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_accounts_add_license_key())
