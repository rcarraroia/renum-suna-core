#!/usr/bin/env python3
"""
Simple validation script for migrations.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("renum-backend/.env")

# Add renum-backend to path
sys.path.insert(0, str(Path(__file__).parent / "renum-backend"))

try:
    from app.db.database import get_db_instance
    print("✅ Database modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database modules: {e}")
    sys.exit(1)

async def validate_migrations():
    """Validate that migrations were applied."""
    print("🔍 Validating Database Migrations")
    print("="*40)
    
    try:
        # Get database connection
        db = get_db_instance()
        client = await db.client
        print("✅ Database connection established")
        
        # Check for renum_ tables
        print("\n📋 Checking for renum_ tables...")
        
        # Try to query some expected tables
        tables_to_check = [
            'renum_agent_teams',
            'renum_team_executions',
            'renum_migration_log'
        ]
        
        found_tables = []
        for table in tables_to_check:
            try:
                result = client.table(table).select("*").limit(1).execute()
                found_tables.append(table)
                print(f"✅ Found table: {table}")
            except Exception as e:
                print(f"❌ Table not found or error: {table} - {e}")
        
        # Check migration log
        print("\n📋 Checking migration log...")
        try:
            result = client.table('renum_migration_log').select("*").execute()
            if result.data:
                print(f"✅ Migration log found with {len(result.data)} entries")
                for entry in result.data:
                    print(f"   - {entry.get('migration_version', 'N/A')}: {entry.get('migration_name', 'N/A')} ({entry.get('status', 'N/A')})")
            else:
                print("⚠️  Migration log table exists but is empty")
        except Exception as e:
            print(f"❌ Migration log check failed: {e}")
        
        print("\n" + "="*40)
        print("VALIDATION SUMMARY")
        print("="*40)
        print(f"Tables found: {len(found_tables)}/{len(tables_to_check)}")
        
        if len(found_tables) >= 2:
            print("🎉 Migrations appear to be working!")
            return True
        else:
            print("⚠️  Some tables missing - migrations may need to be run")
            return False
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(validate_migrations())
    sys.exit(0 if success else 1)