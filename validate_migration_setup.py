#!/usr/bin/env python3
"""
Quick validation script for migration utilities setup.

This script validates that all migration utilities are properly installed
and can be imported without errors.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test that all migration utilities can be imported."""
    print("Testing migration utilities imports...")
    
    try:
        from migration_utils import (
            BackupManager,
            MigrationValidator,
            RollbackManager,
            DependencyMigrator,
            ConfigManager
        )
        print("✅ All migration utilities imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality of each component."""
    print("\nTesting basic functionality...")
    
    try:
        from migration_utils import BackupManager, ConfigManager
        
        # Test BackupManager
        backup_manager = BackupManager(backup_dir="test_backups")
        session = backup_manager.create_backup_session("test")
        print("✅ BackupManager basic functionality works")
        
        # Test ConfigManager
        config_manager = ConfigManager()
        summary = config_manager.create_configuration_summary()
        print("✅ ConfigManager basic functionality works")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        traceback.print_exc()
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\nTesting file structure...")
    
    required_files = [
        "migration_utils/__init__.py",
        "migration_utils/backup_manager.py",
        "migration_utils/migration_validator.py",
        "migration_utils/rollback_manager.py",
        "migration_utils/dependency_migrator.py",
        "migration_utils/config_manager.py",
        "migration_utils/main.py",
        "migration_utils/test_migration_utils.py",
        "migration_utils/README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def test_critical_system_files():
    """Test that critical system files exist."""
    print("\nTesting critical system files...")
    
    critical_files = [
        "docker-compose.yaml",
        "backend/pyproject.toml",
        "renum-backend/requirements.txt",
        "backend/services/docker/redis.conf"
    ]
    
    existing_files = []
    missing_files = []
    
    for file_path in critical_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    print(f"✅ Found {len(existing_files)} critical files:")
    for file_path in existing_files:
        print(f"   - {file_path}")
    
    if missing_files:
        print(f"⚠️  Missing {len(missing_files)} critical files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
    
    return len(existing_files) > 0

def main():
    """Run all validation tests."""
    print("=== Migration Utilities Setup Validation ===\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Import Tests", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Critical System Files", test_critical_system_files)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed! Migration utilities are ready to use.")
        print("\nNext steps:")
        print("1. Review the migration plan in migration_utils/README.md")
        print("2. Run: python -m migration_utils.main")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)