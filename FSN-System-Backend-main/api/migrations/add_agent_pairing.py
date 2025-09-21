"""
Database migration to add agent pairing support
"""
import asyncio
from sqlalchemy import text
from database.connection import get_engine

async def migrate_agent_pairing():
    """Add agent pairing tables and update existing agent table"""
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Create pair_tokens table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pair_tokens (
                id SERIAL PRIMARY KEY,
                pair_token VARCHAR(100) UNIQUE NOT NULL,
                license_id VARCHAR(100) NOT NULL,
                qr_payload VARCHAR(500) NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        # Create index on pair_token
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pair_tokens_token ON pair_tokens(pair_token);
        """))
        
        # Create index on license_id
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pair_tokens_license ON pair_tokens(license_id);
        """))
        
        # Add new columns to agents table if they don't exist
        await conn.execute(text("""
            ALTER TABLE agents 
            ADD COLUMN IF NOT EXISTS license_id VARCHAR(100),
            ADD COLUMN IF NOT EXISTS agent_name VARCHAR(100),
            ADD COLUMN IF NOT EXISTS app_version VARCHAR(20),
            ADD COLUMN IF NOT EXISTS agent_token TEXT,
            ADD COLUMN IF NOT EXISTS appium_base_path VARCHAR(50) DEFAULT '/wd/hub';
        """))
        
        # Create index on license_id in agents table
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_license_id ON agents(license_id);
        """))
        
        # Update existing agents with default values if needed
        await conn.execute(text("""
            UPDATE agents 
            SET license_id = 'default_license' 
            WHERE license_id IS NULL;
        """))
        
        await conn.execute(text("""
            UPDATE agents 
            SET agent_name = 'Legacy Agent' 
            WHERE agent_name IS NULL;
        """))
        
        await conn.execute(text("""
            UPDATE agents 
            SET platform = 'unknown' 
            WHERE platform IS NULL;
        """))
        
        await conn.execute(text("""
            UPDATE agents 
            SET app_version = '1.0.0' 
            WHERE app_version IS NULL;
        """))
        
        print("✅ Agent pairing migration completed successfully")

if __name__ == "__main__":
    asyncio.run(migrate_agent_pairing())
