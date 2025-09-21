"""
Check All Database Tables
"""

import asyncio
from sqlalchemy import text
from database.connection import engine
import structlog

logger = structlog.get_logger()

async def check_all_tables():
    """Check all tables in the database"""
    
    async with engine.begin() as conn:
        logger.info("🔍 Checking all tables in database...")
        
        # Get all tables
        result = await conn.execute(text("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = result.fetchall()
        logger.info(f"📊 All tables in database: {tables}")
        
        # Check each table's schema
        for table_name, table_type in tables:
            logger.info(f"🔍 Checking {table_name} schema...")
            result = await conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))
            
            schema = result.fetchall()
            logger.info(f"📋 {table_name} schema: {schema}")

if __name__ == "__main__":
    async def main():
        try:
            await check_all_tables()
        except Exception as e:
            print(f"❌ Schema check failed: {e}")
            raise
    
    asyncio.run(main())
