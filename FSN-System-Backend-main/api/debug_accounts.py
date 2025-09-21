#!/usr/bin/env python3
"""
Debug accounts table in PostgreSQL database
This script checks the accounts table structure and data.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, text
from models.account import Account
from core.config import settings

DATABASE_URL = settings.database_url

async def debug_accounts():
    print("🔍 Debugging accounts table in PostgreSQL database...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        try:
            # Check if accounts table exists and its structure
            print("📋 Checking accounts table structure...")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'accounts'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            if columns:
                print("✅ Accounts table structure:")
                for col in columns:
                    print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            else:
                print("❌ Accounts table not found!")
                return
            
            # Check if there are any accounts
            print("\n📊 Checking accounts data...")
            result = await session.execute(text("SELECT COUNT(*) FROM accounts"))
            total_accounts = result.scalar()
            print(f"Total accounts in database: {total_accounts}")
            
            if total_accounts > 0:
                # Get all accounts
                result = await session.execute(text("""
                    SELECT id, username, email, license_key, created_at 
                    FROM accounts 
                    ORDER BY created_at DESC
                """))
                accounts = result.fetchall()
                
                print(f"\n📋 Found {len(accounts)} accounts:")
                for acc in accounts:
                    print(f"  ID: {acc[0]}, Username: {acc[1]}, Email: {acc[2]}, License: {acc[3]}, Created: {acc[4]}")
            
            # Check for accounts with specific license key
            print("\n🔍 Checking accounts by license key...")
            test_license_key = "651A6308E6BD453C8E8C10EEF4F334A2"  # Replace with actual license key
            result = await session.execute(text("""
                SELECT COUNT(*) FROM accounts WHERE license_key = :license_key
            """), {"license_key": test_license_key})
            license_accounts = result.scalar()
            print(f"Accounts for license '{test_license_key}': {license_accounts}")
            
            # Try to query using SQLAlchemy ORM
            print("\n🔧 Testing SQLAlchemy ORM query...")
            try:
                result = await session.execute(select(Account))
                orm_accounts = result.scalars().all()
                print(f"✅ ORM query successful - found {len(orm_accounts)} accounts")
                
                for account in orm_accounts:
                    print(f"  ORM Account: {account.username} (ID: {account.id}, License: {account.license_key})")
                    
            except Exception as orm_error:
                print(f"❌ ORM query failed: {orm_error}")

        except Exception as e:
            print(f"❌ Error debugging accounts: {e}")
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_accounts())
