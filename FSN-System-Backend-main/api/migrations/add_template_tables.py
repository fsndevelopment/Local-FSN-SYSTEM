"""
Database migration to add template and run tables
"""
import asyncio
from sqlalchemy import text
from database.connection import get_engine

async def migrate_template_tables():
    """Add template and run tables"""
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Create templates_posting table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS templates_posting (
                id SERIAL PRIMARY KEY,
                license_id VARCHAR(100) NOT NULL,
                platform VARCHAR(20) NOT NULL,
                name VARCHAR(100) NOT NULL,
                photos_per_day INTEGER DEFAULT 0,
                text_posts_per_day INTEGER DEFAULT 0,
                follows_per_day INTEGER DEFAULT 0,
                likes_per_day INTEGER DEFAULT 0,
                captions_file_url VARCHAR(500),
                photos_folder_url VARCHAR(500),
                scrolling_minutes INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        # Create templates_warmup table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS templates_warmup (
                id SERIAL PRIMARY KEY,
                license_id VARCHAR(100) NOT NULL,
                platform VARCHAR(20) NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                days_json JSON NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        # Create runs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id VARCHAR(36) PRIMARY KEY,
                license_id VARCHAR(100) NOT NULL,
                device_id INTEGER NOT NULL,
                account_id INTEGER,
                type VARCHAR(20) NOT NULL,
                template_id INTEGER,
                warmup_id INTEGER,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                finished_at TIMESTAMP WITH TIME ZONE,
                status VARCHAR(20) DEFAULT 'queued',
                progress_pct INTEGER DEFAULT 0,
                current_step VARCHAR(200),
                last_action VARCHAR(200),
                error_text TEXT
            );
        """))
        
        # Create run_logs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS run_logs (
                id SERIAL PRIMARY KEY,
                run_id VARCHAR(36) NOT NULL,
                ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                level VARCHAR(10) NOT NULL,
                message TEXT NOT NULL,
                payload_json JSON
            );
        """))
        
        # Create indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_templates_posting_license ON templates_posting(license_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_templates_warmup_license ON templates_warmup(license_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_runs_license ON runs(license_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_runs_device ON runs(device_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_run_logs_run_id ON run_logs(run_id);
        """))
        
        print("✅ Template tables migration completed successfully")

if __name__ == "__main__":
    asyncio.run(migrate_template_tables())
