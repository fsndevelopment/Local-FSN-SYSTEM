"""
Migration: Add agent support to devices table
"""
import asyncio
from sqlalchemy import text
from api.database.connection import get_async_engine

async def upgrade():
    """Add agent support columns to devices table"""
    engine = get_async_engine()
    
    async with engine.begin() as conn:
        # Add agent_id column to devices table
        await conn.execute(text("""
            ALTER TABLE devices 
            ADD COLUMN IF NOT EXISTS agent_id VARCHAR(100) NULL
        """))
        
        # Add platform column to devices table
        await conn.execute(text("""
            ALTER TABLE devices 
            ADD COLUMN IF NOT EXISTS platform VARCHAR(20) NULL
        """))
        
        # Create agents table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agents (
                id SERIAL PRIMARY KEY,
                agent_id VARCHAR(100) UNIQUE NOT NULL,
                tunnel_url VARCHAR(500) NOT NULL,
                appium_url VARCHAR(500) NOT NULL,
                status VARCHAR(20) DEFAULT 'offline',
                platform VARCHAR(50),
                capabilities JSONB,
                last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        
        # Create index on agent_id
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_devices_agent_id 
            ON devices(agent_id)
        """))
        
        # Create index on agents.agent_id
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_agent_id 
            ON agents(agent_id)
        """))
        
        print("✅ Agent support migration completed successfully")

async def downgrade():
    """Remove agent support columns"""
    engine = get_async_engine()
    
    async with engine.begin() as conn:
        # Remove agent_id column
        await conn.execute(text("""
            ALTER TABLE devices 
            DROP COLUMN IF EXISTS agent_id
        """))
        
        # Remove platform column
        await conn.execute(text("""
            ALTER TABLE devices 
            DROP COLUMN IF EXISTS platform
        """))
        
        # Drop agents table
        await conn.execute(text("""
            DROP TABLE IF EXISTS agents
        """))
        
        print("✅ Agent support migration rolled back successfully")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
