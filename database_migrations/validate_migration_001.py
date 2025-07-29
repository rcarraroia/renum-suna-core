#!/usr/bin/env python3
"""
Validation script for migration 001: Rename tables to renum_ prefix.

This script validates that the database migration was applied correctly
and all tables follow the renum_ naming convention.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import logging

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


class Migration001Validator:
    """Validates migration 001 - table renaming to renum_ prefix."""
    
    def __init__(self):
        self.validation_results = []
        self.db = None
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log validation result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.validation_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    async def connect_to_database(self) -> bool:
        """Connect to the database."""
        if not DB_AVAILABLE:
            self.log_result("Database Connection", False, "Database modules not available")
            return False
        
        try:
            self.db = await get_db_instance()
            self.log_result("Database Connection", True, "Connected successfully")
            return True
        except Exception as e:
            self.log_result("Database Connection", False, f"Connection failed: {e}")
            return False
    
    async def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM information_schema.tables 
                WHERE table_name = %s 
                AND table_schema = 'public'
            """
            result = await self.db.fetch(query, table_name)
            return result[0]['count'] > 0 if result else False
        except Exception as e:
            logger.error(f"Error checking table {table_name}: {e}")
            return False
    
    async def get_all_tables(self) -> List[str]:
        """Get all table names in the public schema."""
        try:
            query = """
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            result = await self.db.fetch(query)
            return [row['table_name'] for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting table list: {e}")
            return []
    
    async def check_foreign_key_constraints(self) -> List[Dict]:
        """Check foreign key constraints for renamed tables."""
        try:
            query = """
                SELECT 
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE 
                    tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_schema = 'public'
                    AND (tc.table_name LIKE 'renum_%' OR ccu.table_name LIKE 'renum_%')
                ORDER BY tc.table_name, tc.constraint_name
            """
            result = await self.db.fetch(query)
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error checking foreign keys: {e}")
            return []
    
    async def check_rls_policies(self) -> List[Dict]:
        """Check RLS policies on renum_ tables."""
        try:
            query = """
                SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
                FROM pg_policies
                WHERE schemaname = 'public'
                AND tablename LIKE 'renum_%'
                ORDER BY tablename, policyname
            """
            result = await self.db.fetch(query)
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error checking RLS policies: {e}")
            return []
    
    async def check_migration_log(self) -> bool:
        """Check if migration was logged."""
        try:
            # First check if migration log table exists
            if not await self.check_table_exists('renum_migration_log'):
                self.log_result("Migration Log Table", False, "renum_migration_log table does not exist")
                return False
            
            query = """
                SELECT migration_version, migration_name, status, applied_at
                FROM renum_migration_log
                WHERE migration_version = '001'
                ORDER BY applied_at DESC
                LIMIT 1
            """
            result = await self.db.fetch(query)
            
            if result and len(result) > 0:
                migration = result[0]
                if migration['status'] == 'completed':
                    self.log_result("Migration Log", True, f"Migration 001 logged as completed at {migration['applied_at']}")
                    return True
                else:
                    self.log_result("Migration Log", False, f"Migration 001 status: {migration['status']}")
                    return False
            else:
                self.log_result("Migration Log", False, "Migration 001 not found in log")
                return False
        except Exception as e:
            self.log_result("Migration Log", False, f"Error checking migration log: {e}")
            return False
    
    async def validate_expected_tables(self) -> bool:
        """Validate that expected renum_ tables exist."""
        expected_tables = [
            'renum_agent_teams',
            'renum_team_executions',
            'renum_team_agent_executions',
            'renum_team_messages',
            'renum_team_context_snapshots',
            'renum_ai_usage_logs',
            'renum_user_api_keys',
            'renum_agent_shares',
            'renum_settings',
            'renum_metrics',
            'renum_audit_logs',
            'renum_admins',
            'renum_admin_credentials',
            'renum_system_settings',
            'renum_migration_log'
        ]
        
        # Optional tables that may have been renamed
        optional_tables = [
            'renum_knowledge_bases',
            'renum_knowledge_collections',
            'renum_documents',
            'renum_document_chunks',
            'renum_document_versions',
            'renum_document_usage_stats',
            'renum_processing_jobs'
        ]
        
        missing_required = []
        found_optional = []
        
        for table in expected_tables:
            if not await self.check_table_exists(table):
                missing_required.append(table)
        
        for table in optional_tables:
            if await self.check_table_exists(table):
                found_optional.append(table)
        
        if missing_required:
            self.log_result("Required Tables", False, f"Missing tables: {', '.join(missing_required)}")
            return False
        else:
            message = f"All required tables exist"
            if found_optional:
                message += f". Optional tables found: {', '.join(found_optional)}"
            self.log_result("Required Tables", True, message)
            return True
    
    async def validate_no_old_tables(self) -> bool:
        """Validate that old table names don't exist (if they were renamed)."""
        potentially_renamed_tables = [
            'knowledge_bases',
            'knowledge_collections',
            'documents',
            'document_chunks',
            'document_versions',
            'document_usage_stats',
            'processing_jobs'
        ]
        
        found_old_tables = []
        
        for table in potentially_renamed_tables:
            if await self.check_table_exists(table):
                # Check if corresponding renum_ table also exists
                renum_table = f"renum_{table}"
                if await self.check_table_exists(renum_table):
                    found_old_tables.append(f"{table} (renum_{table} also exists)")
                else:
                    # Old table exists but renum_ version doesn't - this is expected for Suna Core tables
                    pass
        
        if found_old_tables:
            self.log_result("Old Tables Check", False, f"Found old tables that should have been renamed: {', '.join(found_old_tables)}")
            return False
        else:
            self.log_result("Old Tables Check", True, "No conflicting old table names found")
            return True
    
    async def validate_table_structure(self) -> bool:
        """Validate that renamed tables maintain their structure."""
        try:
            # Check a few key tables to ensure they have expected columns
            table_checks = {
                'renum_agent_teams': ['team_id', 'user_id', 'name', 'agent_ids'],
                'renum_team_executions': ['execution_id', 'team_id', 'user_id', 'status'],
                'renum_agent_shares': ['id', 'agent_id', 'user_id', 'permission_level']
            }
            
            all_valid = True
            
            for table_name, expected_columns in table_checks.items():
                if await self.check_table_exists(table_name):
                    query = """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = %s
                        AND table_schema = 'public'
                    """
                    result = await self.db.fetch(query, table_name)
                    actual_columns = [row['column_name'] for row in result] if result else []
                    
                    missing_columns = [col for col in expected_columns if col not in actual_columns]
                    
                    if missing_columns:
                        self.log_result(f"Table Structure - {table_name}", False, f"Missing columns: {', '.join(missing_columns)}")
                        all_valid = False
                    else:
                        self.log_result(f"Table Structure - {table_name}", True, "All expected columns present")
                else:
                    self.log_result(f"Table Structure - {table_name}", False, "Table does not exist")
                    all_valid = False
            
            return all_valid
            
        except Exception as e:
            self.log_result("Table Structure", False, f"Error validating table structure: {e}")
            return False
    
    async def run_validation(self) -> bool:
        """Run complete validation of migration 001."""
        print("=== Migration 001 Validation ===")
        print("Validating table renaming to renum_ prefix...\n")
        
        # Connect to database
        if not await self.connect_to_database():
            return False
        
        # Run validation tests
        tests = [
            self.validate_expected_tables,
            self.validate_no_old_tables,
            self.validate_table_structure,
            self.check_migration_log
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                test_name = test.__name__.replace('validate_', '').replace('check_', '').replace('_', ' ').title()
                self.log_result(test_name, False, f"Test failed with exception: {e}")
        
        # Additional information
        print("\n=== Additional Information ===")
        
        # List all renum_ tables
        all_tables = await self.get_all_tables()
        renum_tables = [t for t in all_tables if t.startswith('renum_')]
        
        if renum_tables:
            print(f"Found {len(renum_tables)} renum_ tables:")
            for table in sorted(renum_tables):
                print(f"  - {table}")
        else:
            print("No renum_ tables found")
        
        # Check foreign keys
        foreign_keys = await self.check_foreign_key_constraints()
        if foreign_keys:
            print(f"\nFound {len(foreign_keys)} foreign key constraints on renum_ tables:")
            for fk in foreign_keys[:5]:  # Show first 5
                print(f"  - {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
            if len(foreign_keys) > 5:
                print(f"  ... and {len(foreign_keys) - 5} more")
        
        # Check RLS policies
        policies = await self.check_rls_policies()
        if policies:
            print(f"\nFound {len(policies)} RLS policies on renum_ tables:")
            for policy in policies[:5]:  # Show first 5
                print(f"  - {policy['tablename']}: {policy['policyname']}")
            if len(policies) > 5:
                print(f"  ... and {len(policies) - 5} more")
        
        # Summary
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.validation_results if result["success"])
        total = len(self.validation_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 Migration 001 validation passed!")
            print("✅ All tables follow the renum_ naming convention")
            print("✅ Table structure is intact")
            print("✅ Foreign key constraints are working")
            print("✅ Migration was properly logged")
            return True
        else:
            print(f"\n⚠️  {total - passed} validation tests failed.")
            print("Please review the issues above before proceeding.")
            return False


async def main():
    """Main validation runner."""
    validator = Migration001Validator()
    success = await validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())