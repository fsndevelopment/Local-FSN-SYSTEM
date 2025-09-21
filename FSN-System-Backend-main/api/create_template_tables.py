"""
Create Templates and Warmup Templates Database Tables
"""

import asyncio
from sqlalchemy import text
from database.connection import engine
from models.template import Template, WarmupTemplate
import structlog

logger = structlog.get_logger()

async def create_template_tables():
    """Create the templates and warmup_templates tables"""
    
    async with engine.begin() as conn:
        logger.info("🔧 Creating templates and warmup_templates tables...")
        
        # Create templates table
        logger.info("📋 Creating templates table...")
        await conn.run_sync(Template.metadata.create_all)
        logger.info("✅ Templates table created")
        
        # Create warmup_templates table
        logger.info("📋 Creating warmup_templates table...")
        await conn.run_sync(WarmupTemplate.metadata.create_all)
        logger.info("✅ Warmup templates table created")
        
        # Verify tables were created
        logger.info("🔍 Verifying tables were created...")
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN ('templates', 'warmup_templates')
            ORDER BY table_name;
        """))
        
        tables = result.fetchall()
        logger.info(f"📊 Created tables: {[table[0] for table in tables]}")
        
        # Check templates table schema
        logger.info("🔍 Checking templates table schema...")
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'templates' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """))
        
        templates_schema = result.fetchall()
        logger.info(f"📋 Templates table schema: {templates_schema}")
        
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
        logger.info(f"📋 Warmup templates table schema: {warmup_schema}")
        
        logger.info("🎉 Template tables created successfully!")

if __name__ == "__main__":
    async def main():
        try:
            await create_template_tables()
            print("🎉 Template tables created successfully!")
        except Exception as e:
            print(f"❌ Failed to create template tables: {e}")
            raise
    
    asyncio.run(main())
