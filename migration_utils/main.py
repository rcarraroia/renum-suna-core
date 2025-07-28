#!/usr/bin/env python3
"""
Main migration script for Suna-Core and Renum system fixes.

This script orchestrates the complete migration process including:
- Backup creation
- Dependency migration
- Configuration updates
- Validation and rollback capabilities
"""

import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, List

from .backup_manager import BackupManager
from .migration_validator import MigrationValidator
from .rollback_manager import RollbackManager
from .dependency_migrator import DependencyMigrator
from .config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class SystemMigrationOrchestrator:
    """Orchestrates the complete system migration process."""
    
    def __init__(self):
        self.backup_manager = BackupManager()
        self.validator = MigrationValidator()
        self.rollback_manager = RollbackManager()
        self.dependency_migrator = DependencyMigrator()
        self.config_manager = ConfigManager()
        
        self.migration_session = None
        self.rollback_plan_id = None
    
    def pre_migration_checks(self) -> bool:
        """Run comprehensive pre-migration validation."""
        logger.info("=== Starting Pre-Migration Validation ===")
        
        # Run comprehensive validation
        results = self.validator.run_comprehensive_validation()
        
        # Generate and display report
        report = self.validator.generate_validation_report()
        print(report)
        
        # Check if any critical issues exist
        critical_failures = []
        for check_name, (passed, issues) in results.items():
            if not passed and 'dependencies' in check_name:
                critical_failures.extend(issues)
        
        if critical_failures:
            logger.warning("Critical issues found, but proceeding with migration to fix them")
        
        return True
    
    def create_comprehensive_backup(self) -> str:
        """Create comprehensive backup of all critical components."""
        logger.info("=== Creating Comprehensive Backup ===")
        
        # Create backup session
        session_dir = self.backup_manager.create_backup_session("comprehensive_migration")
        self.migration_session = session_dir
        
        # Backup critical configuration files
        critical_files = [
            "docker-compose.yaml",
            "backend/pyproject.toml",
            "renum-backend/requirements.txt", 
            "backend/services/docker/redis.conf",
            "backend/.env",
            "frontend/.env.local"
        ]
        
        backup_count = 0
        for file_path in critical_files:
            if self.backup_manager.backup_file(file_path, session_dir, "Pre-migration backup"):
                backup_count += 1
        
        logger.info(f"Backed up {backup_count}/{len(critical_files)} critical files")
        return session_dir
    
    def migrate_dependencies(self) -> bool:
        """Migrate deprecated dependencies."""
        logger.info("=== Migrating Dependencies ===")
        
        # Create migration plan
        requirements_files = [
            "backend/pyproject.toml",
            "renum-backend/requirements.txt"
        ]
        
        project_dirs = [
            "backend",
            "renum-backend"
        ]
        
        plan = self.dependency_migrator.create_migration_plan(requirements_files, project_dirs)
        
        if not plan["deprecated_packages"]:
            logger.info("No deprecated packages found")
            return True
        
        logger.info(f"Found {len(plan['deprecated_packages'])} deprecated packages to migrate")
        logger.info(f"Estimated {plan['estimated_changes']} code changes needed")
        
        # Update requirements files
        for req_file in requirements_files:
            if Path(req_file).exists():
                updates = {}
                for old_pkg, new_spec in plan["requirements_updates"].items():
                    updates[old_pkg] = new_spec
                
                if updates:
                    self.dependency_migrator.update_requirements_file(req_file, updates)
        
        # Migrate code
        success = True
        for package in plan["deprecated_packages"]:
            if not self.dependency_migrator.migrate_package(package, project_dirs):
                success = False
        
        # Validate migration
        valid, issues = self.dependency_migrator.validate_migration(project_dirs)
        if not valid:
            logger.warning(f"Migration validation issues: {issues}")
        
        return success
    
    def update_configurations(self) -> bool:
        """Update system configurations for production."""
        logger.info("=== Updating System Configurations ===")
        
        success = True
        
        # Update Redis configuration
        redis_config_file = "backend/services/docker/redis.conf"
        if not self.config_manager.create_production_redis_config(redis_config_file):
            success = False
        
        # Update Docker Compose with resource limits
        if not self.config_manager.add_docker_resource_limits("docker-compose.yaml"):
            success = False
        
        # Update environment variables if needed
        env_updates = {
            "REDIS_HOST": "redis",
            "REDIS_PORT": "6379"
        }
        
        for env_file in ["backend/.env"]:
            if Path(env_file).exists():
                self.config_manager.update_env_file(env_file, env_updates)
        
        return success
    
    def create_rollback_plan(self) -> str:
        """Create rollback plan for all changes made."""
        logger.info("=== Creating Rollback Plan ===")
        
        if not self.migration_session:
            logger.error("No migration session found for rollback plan")
            return None
        
        # Create rollback changes list
        changes = []
        session_path = Path(self.migration_session)
        
        for metadata_file in session_path.glob("*.metadata.json"):
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            changes.append({
                "type": "file",
                "original_path": metadata["original_path"],
                "backup_path": metadata["backup_path"]
            })
        
        self.rollback_plan_id = self.rollback_manager.create_rollback_plan(changes)
        return self.rollback_plan_id
    
    async def post_migration_validation(self) -> bool:
        """Run post-migration validation."""
        logger.info("=== Running Post-Migration Validation ===")
        
        # Run comprehensive validation again
        results = self.validator.run_comprehensive_validation()
        
        # Test service connectivity
        connectivity_valid, connectivity_issues = await self.validator.validate_service_connectivity()
        results['connectivity'] = (connectivity_valid, connectivity_issues)
        
        # Generate report
        report = self.validator.generate_validation_report()
        print(report)
        
        # Check overall success
        total_checks = len(results)
        passed_checks = sum(1 for result in results.values() if result[0])
        
        success_rate = passed_checks / total_checks
        logger.info(f"Post-migration validation: {passed_checks}/{total_checks} checks passed ({success_rate:.1%})")
        
        return success_rate >= 0.8  # 80% success rate required
    
    async def run_complete_migration(self) -> bool:
        """Run the complete migration process."""
        logger.info("=== Starting Complete System Migration ===")
        
        try:
            # Step 1: Pre-migration validation
            if not self.pre_migration_checks():
                logger.error("Pre-migration checks failed")
                return False
            
            # Step 2: Create comprehensive backup
            backup_session = self.create_comprehensive_backup()
            if not backup_session:
                logger.error("Failed to create backup")
                return False
            
            # Step 3: Migrate dependencies
            if not self.migrate_dependencies():
                logger.error("Dependency migration failed")
                return False
            
            # Step 4: Update configurations
            if not self.update_configurations():
                logger.error("Configuration update failed")
                return False
            
            # Step 5: Create rollback plan
            rollback_plan = self.create_rollback_plan()
            if not rollback_plan:
                logger.warning("Failed to create rollback plan")
            
            # Step 6: Post-migration validation
            if not await self.post_migration_validation():
                logger.error("Post-migration validation failed")
                return False
            
            logger.info("=== Migration Completed Successfully ===")
            logger.info(f"Backup session: {backup_session}")
            logger.info(f"Rollback plan: {rollback_plan}")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed with exception: {e}")
            return False
    
    def emergency_rollback(self) -> bool:
        """Perform emergency rollback of all changes."""
        logger.info("=== Performing Emergency Rollback ===")
        
        if self.rollback_plan_id:
            return self.rollback_manager.execute_rollback_plan(self.rollback_plan_id)
        elif self.migration_session:
            session_name = Path(self.migration_session).name.split('_')[0]
            return self.rollback_manager.create_emergency_rollback(session_name)
        else:
            logger.error("No rollback plan or session available")
            return False


async def main():
    """Main entry point for migration script."""
    orchestrator = SystemMigrationOrchestrator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        # Emergency rollback mode
        success = orchestrator.emergency_rollback()
        sys.exit(0 if success else 1)
    else:
        # Normal migration mode
        success = await orchestrator.run_complete_migration()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())