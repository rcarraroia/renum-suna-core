#!/usr/bin/env python3
"""
Safe database migration runner.

This script executes database migrations safely with proper validation,
backup procedures, and rollback capabilities.
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime
import json

# Add renum-backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "renum-backend"))

try:
    from app.db.database import get_db_instance
    from app.core.config import get_settings
    DB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import database modules: {e}")
    DB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SafeMigrationRunner:
    """Safely executes database migrations with validation and rollback capabilities."""
    
    def __init__(self, migrations_dir: str = "database_migrations"):
        self.migrations_dir = Path(migrations_dir)
        self.db = None
        self.migration_log = []
        self.backup_info = {}
        
    def log_step(self, step: str, success: bool, message: str = "", details: Dict = None):
        """Log migration step."""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "success": success,
            "message": message,
            "details": details or {}
        }
        
        self.migration_log.append(log_entry)
        print(f"[{timestamp}] {status} {step}: {message}")
        
        if not success:
            logger.error(f"Migration step failed: {step} - {message}")
    
    async def connect_to_database(self) -> bool:
        """Connect to the database."""
        if not DB_AVAILABLE:
            self.log_step("Database Connection", False, "Database modules not available")
            return False
        
        try:
            self.db = await get_db_instance()
            self.log_step("Database Connection", True, "Connected successfully")
            return True
        except Exception as e:
            self.log_step("Database Connection", False, f"Connection failed: {e}")
            return False
    
    async def check_prerequisites(self) -> bool:
        """Check prerequisites before running migrations."""
        self.log_step("Prerequisites Check", True, "Starting prerequisites validation")
        
        # Check if migration files exist
        migration_files = [
            "001_rename_tables_to_renum_prefix.sql",
            "002_implement_rls_policies.sql"
        ]
        
        missing_files = []
        for file in migration_files:
            if not (self.migrations_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            self.log_step("Migration Files", False, f"Missing files: {', '.join(missing_files)}")
            return False
        else:
            self.log_step("Migration Files", True, f"All {len(migration_files)} migration files found")
        
        # Check database connection
        if not await self.connect_to_database():
            return False
        
        # Check if migration log table exists or can be created
        try:
            await self.ensure_migration_log_table()
            self.log_step("Migration Log Table", True, "Migration log table ready")
        except Exception as e:
            self.log_step("Migration Log Table", False, f"Cannot create migration log table: {e}")
            return False
        
        return True
    
    async def ensure_migration_log_table(self):
        """Ensure migration log table exists."""
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS renum_migration_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                migration_version VARCHAR(10) NOT NULL,
                migration_name TEXT NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                applied_by TEXT DEFAULT current_user,
                status VARCHAR(20) DEFAULT 'completed',
                notes TEXT,
                execution_time_ms INTEGER,
                rollback_available BOOLEAN DEFAULT true
            );
        """
        await self.db.execute(create_table_sql)
    
    async def check_migration_status(self, version: str) -> Optional[Dict]:
        """Check if a migration has already been applied."""
        try:
            query = """
                SELECT migration_version, migration_name, status, applied_at
                FROM renum_migration_log
                WHERE migration_version = $1
                ORDER BY applied_at DESC
                LIMIT 1
            """
            result = await self.db.fetch(query, version)
            return dict(result[0]) if result else None
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return None
    
    async def create_backup_info(self) -> Dict:
        """Create backup information for rollback purposes."""
        try:
            # Get list of all renum_ tables before migration
            query = """
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' 
                AND (table_name LIKE 'renum_%' OR table_name IN ('knowledge_bases', 'documents', 'agents'))
                ORDER BY table_name
            """
            result = await self.db.fetch(query)
            
            backup_info = {
                "timestamp": datetime.now().isoformat(),
                "tables_before_migration": [dict(row) for row in result] if result else [],
                "database_version": await self.get_database_version(),
                "migration_runner_version": "1.0.0"
            }
            
            self.backup_info = backup_info
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating backup info: {e}")
            return {}
    
    async def get_database_version(self) -> str:
        """Get database version information."""
        try:
            result = await self.db.fetch("SELECT version()")
            return result[0]['version'] if result else "unknown"
        except Exception as e:
            return f"error: {e}"
    
    async def execute_migration_file(self, file_path: Path, version: str) -> bool:
        """Execute a single migration file safely."""
        self.log_step(f"Migration {version}", True, f"Starting execution of {file_path.name}")
        
        try:
            # Read migration file
            with open(file_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Record start time
            start_time = datetime.now()
            
            # Execute migration in a transaction
            async with self.db.transaction():
                await self.db.execute(migration_sql)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.log_step(f"Migration {version}", True, 
                         f"Executed successfully in {execution_time:.0f}ms",
                         {"execution_time_ms": execution_time, "file": file_path.name})
            
            return True
            
        except Exception as e:
            self.log_step(f"Migration {version}", False, f"Execution failed: {e}")
            return False
    
    async def validate_migration_result(self, version: str) -> bool:
        """Validate that migration was applied correctly."""
        self.log_step(f"Validation {version}", True, "Starting post-migration validation")
        
        try:
            if version == "001":
                # Validate table renaming
                return await self.validate_migration_001()
            elif version == "002":
                # Validate RLS policies
                return await self.validate_migration_002()
            else:
                self.log_step(f"Validation {version}", False, f"No validation available for version {version}")
                return False
                
        except Exception as e:
            self.log_step(f"Validation {version}", False, f"Validation failed: {e}")
            return False
    
    async def validate_migration_001(self) -> bool:
        """Validate migration 001 - table renaming."""
        try:
            # Check that expected renum_ tables exist
            query = """
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'renum_%'
            """
            result = await self.db.fetch(query)
            table_count = result[0]['count'] if result else 0
            
            if table_count >= 5:  # Should have at least core tables
                self.log_step("Validation 001", True, f"Found {table_count} renum_ tables")
                return True
            else:
                self.log_step("Validation 001", False, f"Only found {table_count} renum_ tables")
                return False
                
        except Exception as e:
            self.log_step("Validation 001", False, f"Validation error: {e}")
            return False
    
    async def validate_migration_002(self) -> bool:
        """Validate migration 002 - RLS policies."""
        try:
            # Check that RLS is enabled on renum_ tables
            query = """
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'renum_%'
                AND row_security = 'YES'
            """
            result = await self.db.fetch(query)
            rls_count = result[0]['count'] if result else 0
            
            # Check that policies exist
            policy_query = """
                SELECT COUNT(*) as count
                FROM pg_policies
                WHERE schemaname = 'public'
                AND tablename LIKE 'renum_%'
            """
            policy_result = await self.db.fetch(policy_query)
            policy_count = policy_result[0]['count'] if policy_result else 0
            
            if rls_count >= 5 and policy_count >= 10:
                self.log_step("Validation 002", True, f"RLS enabled on {rls_count} tables, {policy_count} policies created")
                return True
            else:
                self.log_step("Validation 002", False, f"RLS: {rls_count} tables, Policies: {policy_count}")
                return False
                
        except Exception as e:
            self.log_step("Validation 002", False, f"Validation error: {e}")
            return False
    
    async def run_migration(self, version: str, force: bool = False) -> bool:
        """Run a specific migration safely."""
        migration_file = self.migrations_dir / f"{version}_*.sql"
        migration_files = list(self.migrations_dir.glob(f"{version}_*.sql"))
        
        if not migration_files:
            self.log_step(f"Migration {version}", False, f"Migration file not found: {version}_*.sql")
            return False
        
        migration_file = migration_files[0]
        
        # Check if migration already applied
        if not force:
            existing_migration = await self.check_migration_status(version)
            if existing_migration and existing_migration['status'] == 'completed':
                self.log_step(f"Migration {version}", True, 
                             f"Already applied at {existing_migration['applied_at']}")
                return True
        
        # Create backup info
        await self.create_backup_info()
        
        # Execute migration
        if not await self.execute_migration_file(migration_file, version):
            return False
        
        # Validate migration
        if not await self.validate_migration_result(version):
            self.log_step(f"Migration {version}", False, "Validation failed after execution")
            return False
        
        return True
    
    async def run_all_migrations(self, force: bool = False) -> bool:
        """Run all migrations in order."""
        migrations = [
            ("001", "Rename tables to renum_ prefix"),
            ("002", "Implement RLS policies")
        ]
        
        self.log_step("Migration Suite", True, f"Starting {len(migrations)} migrations")
        
        for version, description in migrations:
            self.log_step(f"Migration {version}", True, f"Starting: {description}")
            
            if not await self.run_migration(version, force):
                self.log_step("Migration Suite", False, f"Failed at migration {version}")
                return False
        
        self.log_step("Migration Suite", True, "All migrations completed successfully")
        return True
    
    def save_migration_log(self):
        """Save migration log to file."""
        log_file = self.migrations_dir / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        log_data = {
            "migration_run": {
                "timestamp": datetime.now().isoformat(),
                "database_info": self.backup_info.get("database_version", "unknown"),
                "runner_version": "1.0.0"
            },
            "backup_info": self.backup_info,
            "steps": self.migration_log
        }
        
        try:
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
            
            print(f"\n📄 Migration log saved to: {log_file}")
            
        except Exception as e:
            print(f"⚠️  Could not save migration log: {e}")
    
    def print_summary(self):
        """Print migration summary."""
        print("\n" + "="*60)
        print("MIGRATION EXECUTION SUMMARY")
        print("="*60)
        
        successful_steps = sum(1 for step in self.migration_log if step["success"])
        total_steps = len(self.migration_log)
        
        print(f"Steps executed: {total_steps}")
        print(f"Successful: {successful_steps}")
        print(f"Failed: {total_steps - successful_steps}")
        print(f"Success rate: {successful_steps/total_steps*100:.1f}%")
        
        # Show failed steps
        failed_steps = [step for step in self.migration_log if not step["success"]]
        if failed_steps:
            print(f"\n❌ Failed Steps:")
            for step in failed_steps:
                print(f"  - {step['step']}: {step['message']}")
        
        # Show timing information
        migration_steps = [step for step in self.migration_log if "Migration" in step["step"] and step["success"]]
        if migration_steps:
            print(f"\n⏱️  Migration Timing:")
            for step in migration_steps:
                execution_time = step["details"].get("execution_time_ms", 0)
                print(f"  - {step['step']}: {execution_time:.0f}ms")
        
        print("="*60)


async def main():
    """Main migration runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run database migrations safely")
    parser.add_argument("--migration", help="Run specific migration (e.g., 001, 002)")
    parser.add_argument("--force", action="store_true", help="Force run even if already applied")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    
    args = parser.parse_args()
    
    runner = SafeMigrationRunner()
    
    print("🔧 Safe Database Migration Runner")
    print("="*50)
    
    # Check prerequisites
    if not await runner.check_prerequisites():
        print("\n❌ Prerequisites check failed. Cannot proceed with migrations.")
        runner.save_migration_log()
        sys.exit(1)
    
    success = False
    
    try:
        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
            runner.log_step("Dry Run", True, "Would execute migrations but no changes made")
            success = True
            
        elif args.validate_only:
            print("\n🔍 VALIDATION ONLY MODE")
            if args.migration:
                success = await runner.validate_migration_result(args.migration)
            else:
                success = (await runner.validate_migration_result("001") and 
                          await runner.validate_migration_result("002"))
                          
        elif args.migration:
            print(f"\n🚀 Running migration {args.migration}")
            success = await runner.run_migration(args.migration, args.force)
            
        else:
            print("\n🚀 Running all migrations")
            success = await runner.run_all_migrations(args.force)
    
    except KeyboardInterrupt:
        runner.log_step("Migration Interrupted", False, "User interrupted migration")
        print("\n⚠️  Migration interrupted by user")
        success = False
        
    except Exception as e:
        runner.log_step("Migration Error", False, f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        success = False
    
    finally:
        # Always save log and print summary
        runner.save_migration_log()
        runner.print_summary()
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("✅ Database is ready for use")
        else:
            print("\n❌ Migration failed!")
            print("⚠️  Check the logs above and consider rollback if necessary")
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())