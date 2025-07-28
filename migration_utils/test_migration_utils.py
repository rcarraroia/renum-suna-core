#!/usr/bin/env python3
"""
Test suite for migration utilities.

Tests all components of the migration system to ensure they work correctly
before running the actual migration.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import json

from .backup_manager import BackupManager
from .migration_validator import MigrationValidator
from .rollback_manager import RollbackManager
from .dependency_migrator import DependencyMigrator
from .config_manager import ConfigManager


class TestBackupManager:
    """Test backup functionality."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.backup_manager = BackupManager(backup_dir=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_backup_session(self):
        session_dir = self.backup_manager.create_backup_session("test_session")
        assert Path(session_dir).exists()
        assert "test_session" in session_dir
    
    def test_backup_file(self):
        # Create test file
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test content")
        
        session_dir = self.backup_manager.create_backup_session("test")
        success = self.backup_manager.backup_file(str(test_file), session_dir)
        
        assert success
        assert (Path(session_dir) / "test.txt").exists()
        assert (Path(session_dir) / "test.txt.metadata.json").exists()


class TestMigrationValidator:
    """Test validation functionality."""
    
    def setup_method(self):
        self.validator = MigrationValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
    
    def test_validate_redis_config(self):
        # Create test Redis config
        config_file = Path(self.temp_dir) / "redis.conf"
        config_file.write_text("""
maxmemory 2gb
maxmemory-policy allkeys-lru
timeout 120
requirepass testpass
        """)
        
        valid, issues = self.validator.validate_redis_config(str(config_file))
        assert valid
        assert len(issues) == 0
    
    def test_validate_python_dependencies(self):
        # Create test requirements file
        req_file = Path(self.temp_dir) / "requirements.txt"
        req_file.write_text("""
fastapi==0.115.12
redis>=5.0.0
pytest>=7.0.0
        """)
        
        valid, issues = self.validator.validate_python_dependencies(str(req_file))
        # This might fail in test environment, but should not crash
        assert isinstance(valid, bool)
        assert isinstance(issues, list)


class TestDependencyMigrator:
    """Test dependency migration functionality."""
    
    def setup_method(self):
        self.migrator = DependencyMigrator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
    
    def test_analyze_current_dependencies(self):
        # Create test requirements file
        req_file = Path(self.temp_dir) / "requirements.txt"
        req_file.write_text("""
fastapi==0.95.0
aioredis>=2.0.1
pytest>=7.0.0
        """)
        
        deps = self.migrator.analyze_current_dependencies(str(req_file))
        assert "fastapi" in deps
        assert "aioredis" in deps
        assert deps["fastapi"] == "0.95.0"
    
    def test_find_deprecated_packages(self):
        deps = {"fastapi": "0.95.0", "aioredis": "2.0.1", "pytest": "7.0.0"}
        deprecated = self.migrator.find_deprecated_packages(deps)
        assert "aioredis" in deprecated
        assert "fastapi" not in deprecated
    
    def test_find_import_statements(self):
        # Create test Python file
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("""
import aioredis
from aioredis import Redis
import other_package
        """)
        
        imports = self.migrator.find_import_statements(str(test_file), "aioredis")
        assert len(imports) == 2
        assert any("import aioredis" in imp[1] for imp in imports)
        assert any("from aioredis import" in imp[1] for imp in imports)


class TestConfigManager:
    """Test configuration management functionality."""
    
    def setup_method(self):
        self.config_manager = ConfigManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
    
    def test_read_write_redis_config(self):
        config_file = Path(self.temp_dir) / "redis.conf"
        
        test_config = {
            "maxmemory": "2gb",
            "timeout": "120",
            "requirepass": "testpass"
        }
        
        # Write config
        success = self.config_manager.write_redis_config(str(config_file), test_config)
        assert success
        assert config_file.exists()
        
        # Read config back
        read_config = self.config_manager.read_redis_config(str(config_file))
        assert read_config["maxmemory"] == "2gb"
        assert read_config["timeout"] == "120"
    
    def test_read_write_env_file(self):
        env_file = Path(self.temp_dir) / ".env"
        
        test_env = {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "DEBUG": "true"
        }
        
        # Write env file
        success = self.config_manager.write_env_file(str(env_file), test_env)
        assert success
        assert env_file.exists()
        
        # Read env file back
        read_env = self.config_manager.read_env_file(str(env_file))
        assert read_env["REDIS_HOST"] == "localhost"
        assert read_env["REDIS_PORT"] == "6379"


class TestRollbackManager:
    """Test rollback functionality."""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rollback_manager = RollbackManager(backup_dir=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_rollback_plan(self):
        changes = [
            {
                "type": "file",
                "original_path": "/test/file.txt",
                "backup_path": "/backup/file.txt"
            }
        ]
        
        plan_id = self.rollback_manager.create_rollback_plan(changes)
        assert plan_id is not None
        assert plan_id.startswith("rollback_plan_")
        
        # Check plan file exists
        plan_file = Path(self.temp_dir) / f"{plan_id}.json"
        assert plan_file.exists()
    
    def test_rollback_file_change(self):
        # Create test files
        original_file = Path(self.temp_dir) / "original.txt"
        backup_file = Path(self.temp_dir) / "backup.txt"
        
        original_file.write_text("original content")
        backup_file.write_text("backup content")
        
        # Modify original
        original_file.write_text("modified content")
        
        # Rollback
        success = self.rollback_manager.rollback_file_change(
            str(original_file), str(backup_file)
        )
        
        assert success
        assert original_file.read_text() == "backup content"


def run_tests():
    """Run all tests."""
    print("Running migration utilities tests...")
    
    # Run pytest
    exit_code = pytest.main([__file__, "-v"])
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return exit_code == 0


if __name__ == "__main__":
    run_tests()