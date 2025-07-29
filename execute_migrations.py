#!/usr/bin/env python3
"""
Simple migration executor for Supabase database.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from renum-backend/.env
load_dotenv("renum-backend/.env")

# Add renum-backend to path
sys.path.insert(0, str(Path(__file__).parent / "renum-backend"))

try:
    from app.db.database import get_db_instance
    print("✅ Database modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database modules: {e}")
    sys.exit(1)

async def execute_migration_file(file_path: str, description: str):
    """Execute a migration file."""
    print(f"\n🚀 Executing: {description}")
    print(f"📄 File: {file_path}")
    
    try:
        # Read migration file
        with open(file_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print(f"📝 Migration SQL loaded ({len(migration_sql)} characters)")
        
        # Get database connection
        db = get_db_instance()
        client = await db.client
        print("✅ Database connection established")
        
        # Execute migration using rpc call
        # First check if exec_sql function exists, if not, try direct execution
        try:
            result = client.rpc('exec_sql', {'sql': migration_sql}).execute()
            print("✅ Migration executed via RPC")
        except Exception as rpc_error:
            print(f"⚠️  RPC failed ({rpc_error}), trying direct SQL execution...")
            # For now, we'll indicate that manual execution is needed
            print("📋 Migration SQL ready for manual execution in Supabase dashboard")
            print("🔗 Please copy the SQL from the file and execute in Supabase SQL Editor")
            return False
        
        print(f"📊 Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

async def main():
    """Execute all migrations."""
    print("🔧 Supabase Database Migration Executor")
    print("="*50)
    
    migrations = [
        ("database_migrations/001_rename_tables_to_renum_prefix.sql", "Rename tables to renum_ prefix"),
        ("database_migrations/002_implement_rls_policies.sql", "Implement RLS policies")
    ]
    
    success_count = 0
    
    for file_path, description in migrations:
        if Path(file_path).exists():
            if await execute_migration_file(file_path, description):
                success_count += 1
            else:
                print(f"⚠️  Migration failed, stopping execution")
                break
        else:
            print(f"❌ Migration file not found: {file_path}")
            break
    
    print("\n" + "="*50)
    print("MIGRATION SUMMARY")
    print("="*50)
    print(f"Migrations executed: {success_count}/{len(migrations)}")
    
    if success_count == len(migrations):
        print("🎉 All migrations completed successfully!")
        return True
    else:
        print("❌ Some migrations failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)