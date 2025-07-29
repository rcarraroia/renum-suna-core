#!/usr/bin/env python3
"""
Validation script for RLS policies implementation.

This script validates that Row Level Security policies are properly
implemented on all renum_ tables.
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


class RLSPolicyValidator:
    """Validates RLS policies implementation."""
    
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
    
    async def get_rls_status(self) -> List[Dict]:
        """Get RLS status for all renum_ tables."""
        try:
            query = """
                SELECT 
                    table_name,
                    CASE WHEN row_security = 'YES' THEN true ELSE false END as rls_enabled
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'renum_%'
                ORDER BY table_name
            """
            result = await self.db.fetch(query)
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting RLS status: {e}")
            return []
    
    async def get_policies_count(self) -> List[Dict]:
        """Get policy count for each renum_ table."""
        try:
            query = """
                SELECT 
                    tablename as table_name,
                    COUNT(*) as policy_count,
                    array_agg(policyname) as policy_names
                FROM pg_policies 
                WHERE schemaname = 'public'
                AND tablename LIKE 'renum_%'
                GROUP BY tablename
                ORDER BY tablename
            """
            result = await self.db.fetch(query)
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting policies count: {e}")
            return []
    
    async def get_policy_details(self) -> List[Dict]:
        """Get detailed policy information."""
        try:
            query = """
                SELECT 
                    schemaname,
                    tablename,
                    policyname,
                    permissive,
                    roles,
                    cmd,
                    qual,
                    with_check
                FROM pg_policies
                WHERE schemaname = 'public'
                AND tablename LIKE 'renum_%'
                ORDER BY tablename, policyname
            """
            result = await self.db.fetch(query)
            return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting policy details: {e}")
            return []
    
    async def check_helper_functions(self) -> bool:
        """Check if RLS helper functions exist."""
        try:
            functions_to_check = [
                'renum_is_admin',
                'renum_is_superadmin',
                'renum_get_user_client_id',
                'renum_user_can_access_team'
            ]
            
            query = """
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                AND routine_name = ANY(%s)
            """
            result = await self.db.fetch(query, functions_to_check)
            found_functions = [row['routine_name'] for row in result] if result else []
            
            missing_functions = [f for f in functions_to_check if f not in found_functions]
            
            if missing_functions:
                self.log_result("Helper Functions", False, f"Missing functions: {', '.join(missing_functions)}")
                return False
            else:
                self.log_result("Helper Functions", True, f"All {len(functions_to_check)} helper functions exist")
                return True
                
        except Exception as e:
            self.log_result("Helper Functions", False, f"Error checking functions: {e}")
            return False
    
    async def validate_rls_enabled(self) -> bool:
        """Validate that RLS is enabled on all renum_ tables."""
        rls_status = await self.get_rls_status()
        
        if not rls_status:
            self.log_result("RLS Enabled", False, "No renum_ tables found")
            return False
        
        tables_without_rls = [table['table_name'] for table in rls_status if not table['rls_enabled']]
        
        if tables_without_rls:
            self.log_result("RLS Enabled", False, f"Tables without RLS: {', '.join(tables_without_rls)}")
            return False
        else:
            self.log_result("RLS Enabled", True, f"RLS enabled on all {len(rls_status)} renum_ tables")
            return True
    
    async def validate_policies_exist(self) -> bool:
        """Validate that policies exist for all tables with RLS."""
        rls_status = await self.get_rls_status()
        policies_count = await self.get_policies_count()
        
        # Create lookup for policy counts
        policy_lookup = {p['table_name']: p['policy_count'] for p in policies_count}
        
        tables_without_policies = []
        tables_with_few_policies = []
        
        for table in rls_status:
            if table['rls_enabled']:
                table_name = table['table_name']
                policy_count = policy_lookup.get(table_name, 0)
                
                if policy_count == 0:
                    tables_without_policies.append(table_name)
                elif policy_count < 2:  # Most tables should have at least user + admin policies
                    tables_with_few_policies.append(f"{table_name} ({policy_count})")
        
        issues = []
        if tables_without_policies:
            issues.append(f"No policies: {', '.join(tables_without_policies)}")
        if tables_with_few_policies:
            issues.append(f"Few policies: {', '.join(tables_with_few_policies)}")
        
        if issues:
            self.log_result("Policies Exist", False, "; ".join(issues))
            return False
        else:
            total_policies = sum(policy_lookup.values())
            self.log_result("Policies Exist", True, f"{total_policies} policies across {len(policy_lookup)} tables")
            return True
    
    async def validate_core_table_policies(self) -> bool:
        """Validate that core tables have expected policies."""
        core_tables = [
            'renum_agent_teams',
            'renum_team_executions',
            'renum_team_agent_executions',
            'renum_ai_usage_logs',
            'renum_user_api_keys'
        ]
        
        policies_count = await self.get_policies_count()
        policy_lookup = {p['table_name']: p for p in policies_count}
        
        missing_tables = []
        insufficient_policies = []
        
        for table in core_tables:
            if table not in policy_lookup:
                missing_tables.append(table)
            else:
                policy_count = policy_lookup[table]['policy_count']
                if policy_count < 2:  # Should have at least user + admin policies
                    insufficient_policies.append(f"{table} ({policy_count})")
        
        issues = []
        if missing_tables:
            issues.append(f"Missing policies: {', '.join(missing_tables)}")
        if insufficient_policies:
            issues.append(f"Insufficient policies: {', '.join(insufficient_policies)}")
        
        if issues:
            self.log_result("Core Table Policies", False, "; ".join(issues))
            return False
        else:
            self.log_result("Core Table Policies", True, f"All {len(core_tables)} core tables have adequate policies")
            return True
    
    async def validate_admin_table_policies(self) -> bool:
        """Validate that admin tables have appropriate policies."""
        admin_tables = [
            'renum_admins',
            'renum_admin_credentials',
            'renum_system_settings',
            'renum_audit_logs'
        ]
        
        policies_count = await self.get_policies_count()
        policy_lookup = {p['table_name']: p for p in policies_count}
        
        found_admin_tables = []
        for table in admin_tables:
            if table in policy_lookup:
                found_admin_tables.append(table)
        
        if found_admin_tables:
            self.log_result("Admin Table Policies", True, f"Policies found for {len(found_admin_tables)} admin tables")
            return True
        else:
            self.log_result("Admin Table Policies", False, "No admin tables with policies found")
            return False
    
    async def validate_policy_naming(self) -> bool:
        """Validate that policies follow naming conventions."""
        policy_details = await self.get_policy_details()
        
        if not policy_details:
            self.log_result("Policy Naming", False, "No policies found")
            return False
        
        # Check for consistent naming patterns
        expected_patterns = ['_user_access', '_admin_access', '_superadmin_', '_client_access']
        
        policies_with_good_names = 0
        total_policies = len(policy_details)
        
        for policy in policy_details:
            policy_name = policy['policyname']
            if any(pattern in policy_name for pattern in expected_patterns):
                policies_with_good_names += 1
        
        if policies_with_good_names >= total_policies * 0.8:  # 80% should follow naming convention
            self.log_result("Policy Naming", True, f"{policies_with_good_names}/{total_policies} policies follow naming conventions")
            return True
        else:
            self.log_result("Policy Naming", False, f"Only {policies_with_good_names}/{total_policies} policies follow naming conventions")
            return False
    
    async def check_migration_log(self) -> bool:
        """Check if RLS migration was logged."""
        try:
            query = """
                SELECT migration_version, migration_name, status, applied_at
                FROM renum_migration_log
                WHERE migration_version = '002'
                ORDER BY applied_at DESC
                LIMIT 1
            """
            result = await self.db.fetch(query)
            
            if result and len(result) > 0:
                migration = result[0]
                if migration['status'] == 'completed':
                    self.log_result("Migration Log", True, f"RLS migration logged as completed at {migration['applied_at']}")
                    return True
                else:
                    self.log_result("Migration Log", False, f"RLS migration status: {migration['status']}")
                    return False
            else:
                self.log_result("Migration Log", False, "RLS migration not found in log")
                return False
        except Exception as e:
            self.log_result("Migration Log", False, f"Error checking migration log: {e}")
            return False
    
    async def run_validation(self) -> bool:
        """Run complete RLS validation."""
        print("=== RLS Policies Validation ===")
        print("Validating Row Level Security implementation...\n")
        
        # Connect to database
        if not await self.connect_to_database():
            return False
        
        # Run validation tests
        tests = [
            self.check_helper_functions,
            self.validate_rls_enabled,
            self.validate_policies_exist,
            self.validate_core_table_policies,
            self.validate_admin_table_policies,
            self.validate_policy_naming,
            self.check_migration_log
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                test_name = test.__name__.replace('validate_', '').replace('check_', '').replace('_', ' ').title()
                self.log_result(test_name, False, f"Test failed with exception: {e}")
        
        # Additional information
        print("\n=== Detailed RLS Information ===")
        
        # Show RLS status for all tables
        rls_status = await self.get_rls_status()
        if rls_status:
            print(f"\nRLS Status for {len(rls_status)} renum_ tables:")
            for table in rls_status:
                status = "ON" if table['rls_enabled'] else "OFF"
                print(f"  - {table['table_name']}: {status}")
        
        # Show policy summary
        policies_count = await self.get_policies_count()
        if policies_count:
            print(f"\nPolicy Summary for {len(policies_count)} tables:")
            for table in policies_count:
                print(f"  - {table['table_name']}: {table['policy_count']} policies")
        
        # Show some policy details
        policy_details = await self.get_policy_details()
        if policy_details:
            print(f"\nSample Policies (showing first 10 of {len(policy_details)}):")
            for policy in policy_details[:10]:
                print(f"  - {policy['tablename']}.{policy['policyname']} ({policy['cmd']})")
        
        # Summary
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.validation_results if result["success"])
        total = len(self.validation_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 RLS policies validation passed!")
            print("✅ Row Level Security is enabled on all renum_ tables")
            print("✅ Security policies are properly implemented")
            print("✅ Helper functions are available")
            print("✅ Migration was properly logged")
            return True
        else:
            print(f"\n⚠️  {total - passed} validation tests failed.")
            print("Please review the RLS implementation before proceeding.")
            return False


async def main():
    """Main validation runner."""
    validator = RLSPolicyValidator()
    success = await validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())