"""
Database migration to create warmup templates tables
"""
import asyncio
import sys
import os
from sqlalchemy import text

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection import engine

async def create_warmup_templates_tables():
    """Create warmup templates and warmup day configs tables"""
    
    # Create tables
    async with engine.begin() as conn:
        # Create warmup_templates table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS warmup_templates (
                id SERIAL PRIMARY KEY,
                license_id VARCHAR(100) NOT NULL,
                platform VARCHAR(20) NOT NULL,
                name VARCHAR(100) NOT NULL,
                total_days INTEGER DEFAULT 1,
                days_config JSON NOT NULL,
                scroll_minutes_per_day INTEGER DEFAULT 0,
                likes_per_day INTEGER DEFAULT 0,
                follows_per_day INTEGER DEFAULT 0,
                posting_interval_minutes INTEGER DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
        """))
        
        print("✅ Created warmup_templates table")
        
        # Create warmup_day_configs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS warmup_day_configs (
                id SERIAL PRIMARY KEY,
                warmup_template_id INTEGER NOT NULL,
                day_number INTEGER NOT NULL,
                scroll_minutes INTEGER DEFAULT 0,
                likes_count INTEGER DEFAULT 0,
                follows_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warmup_template_id) REFERENCES warmup_templates (id) ON DELETE CASCADE
            );
        """))
        
        print("✅ Created warmup_day_configs table")
    
    # Create indexes in separate transaction (with error handling)
    try:
        async with engine.begin() as conn:
            # Create indexes for better performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_warmup_templates_license_id 
                ON warmup_templates (license_id);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_warmup_templates_platform 
                ON warmup_templates (platform);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_warmup_day_configs_template_id 
                ON warmup_day_configs (warmup_template_id);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_warmup_day_configs_day_number 
                ON warmup_day_configs (day_number);
            """))
            
            print("✅ Created indexes for warmup templates tables")
    except Exception as e:
        print(f"⚠️ Warning: Could not create indexes: {e}")
        print("✅ Tables created successfully (indexes can be created later)")

if __name__ == "__main__":
    asyncio.run(create_warmup_templates_tables())
