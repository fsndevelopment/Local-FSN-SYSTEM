#!/usr/bin/env python3
"""
Test accounts endpoint directly
This script tests the accounts endpoint to identify the 500 error.
"""

import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, text
from models.account import Account
from core.config import settings

DATABASE_URL = settings.database_url

async def test_accounts_endpoint():
    print("🔍 Testing accounts endpoint and database...")
    
    # Test database connection and table structure
    print("\n📋 Testing database connection...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        async with AsyncSession(engine) as session:
            # Check if accounts table exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'accounts'
                );
            """))
            table_exists = result.scalar()
            print(f"Accounts table exists: {table_exists}")
            
            if table_exists:
                # Check table structure
                result = await session.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'accounts'
                    ORDER BY ordinal_position;
                """))
                
                columns = result.fetchall()
                print(f"📊 Accounts table has {len(columns)} columns:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
                
                # Check for specific problematic columns
                column_names = [col[0] for col in columns]
                required_columns = ['id', 'username', 'license_key', 'created_at', 'updated_at']
                
                missing_columns = [col for col in required_columns if col not in column_names]
                if missing_columns:
                    print(f"❌ Missing required columns: {missing_columns}")
                else:
                    print("✅ All required columns present")
                
                # Try to query accounts
                try:
                    result = await session.execute(select(Account))
                    accounts = result.scalars().all()
                    print(f"✅ ORM query successful - found {len(accounts)} accounts")
                except Exception as orm_error:
                    print(f"❌ ORM query failed: {orm_error}")
                    
                    # Try raw SQL query
                    try:
                        result = await session.execute(text("SELECT COUNT(*) FROM accounts"))
                        count = result.scalar()
                        print(f"📊 Raw SQL query successful - found {count} accounts")
                    except Exception as sql_error:
                        print(f"❌ Raw SQL query also failed: {sql_error}")
                        
                        # Check for specific column issues
                        for col in required_columns:
                            try:
                                result = await session.execute(text(f"SELECT {col} FROM accounts LIMIT 1"))
                                print(f"✅ Column '{col}' is accessible")
                            except Exception as col_error:
                                print(f"❌ Column '{col}' has issues: {col_error}")
            else:
                print("❌ Accounts table does not exist!")
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    finally:
        await engine.dispose()
    
    # Test the actual endpoint
    print("\n🌐 Testing accounts endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "X-License-Key": "651A6308E6BD453C8E8C10EEF4F334A2",
                "X-Device-ID": "test-device"
            }
            
            response = await client.get(
                "https://fsn-system-backend.onrender.com/api/v1/accounts",
                headers=headers,
                timeout=10.0
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✅ Endpoint working!")
                data = response.json()
                print(f"Response: {data}")
            else:
                print(f"❌ Endpoint failed with status {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_accounts_endpoint())
