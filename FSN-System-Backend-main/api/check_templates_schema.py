"""
Check Templates and Warmup Templates Database Schema
"""

import asyncio
from sqlalchemy import text
from database.connection import engine
import structlog

logger = structlog.get_logger()

async def check_templates_schema():
    """Check the schema of templates and warmup_templates tables"""
    
    async with engine.begin() as conn:
        logger.info("🔍 Checking templates table schema...")
        
        # Check templates table schema
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'templates' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """))
        
        templates_schema = result.fetchall()
        logger.info(f"📊 Templates table schema: {templates_schema}")
        
        # Check warmup_templates table schema
        logger.info("🔍 Checking warmup_templates table schema...")
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'warmup_templates' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """))
        
        warmup_schema = result.fetchall()
        logger.info(f"📊 Warmup templates table schema: {warmup_schema}")
        
        # Check for NOT NULL columns that might cause issues
        logger.info("🔍 Checking for potentially problematic NOT NULL columns...")
        
        for table_name, schema in [("templates", templates_schema), ("warmup_templates", warmup_schema)]:
            logger.info(f"📋 {table_name.upper()} - NOT NULL columns:")
            for column in schema:
                if column[2] == 'NO':  # is_nullable = 'NO'
                    logger.info(f"  ❌ {column[0]}: {column[1]} NOT NULL (default: {column[3]})")

if __name__ == "__main__":
    async def main():
        try:
            await check_templates_schema()
        except Exception as e:
            print(f"❌ Schema check failed: {e}")
            raise
    
    asyncio.run(main())
