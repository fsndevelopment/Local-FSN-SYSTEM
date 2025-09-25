"""
Database migration to add posting_interval_minutes column to templates_posting table
"""
import asyncio
import sys
import os
from sqlalchemy import text

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection import engine

async def migrate_posting_interval_minutes():
    """Add posting_interval_minutes column to templates_posting table"""
    
    async with engine.begin() as conn:
        # Add posting_interval_minutes column to templates_posting table
        await conn.execute(text("""
            ALTER TABLE templates_posting 
            ADD COLUMN IF NOT EXISTS posting_interval_minutes INTEGER DEFAULT 30;
        """))
        
        print("✅ Added posting_interval_minutes column to templates_posting table")

if __name__ == "__main__":
    asyncio.run(migrate_posting_interval_minutes())
