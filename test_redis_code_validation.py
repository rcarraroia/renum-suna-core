#!/usr/bin/env python3
"""
Redis code validation test.

This script validates that the Redis migration code is correct
without requiring an actual Redis connection.
"""

import sys
import ast
import importlib.util
from pathlib import Path


class RedisCodeValidator:
    """Validates Redis migration code structure."""
    
    def __init__(self):
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_redis_service_imports(self):
        """Test that Redis service uses correct imports."""
        try:
            redis_service_path = Path("backend/services/redis.py")
            if not redis_service_path.exists():
                self.log_test("Redis Service File", False, "File not found")
                return False
            
            with open(redis_service_path, 'r') as f:
                content = f.read()
            
            # Check for correct import
            if "import redis.asyncio as redis" in content:
                self.log_test("Redis Service Import", True, "Uses redis.asyncio correctly")
            else:
                self.log_test("Redis Service Import", False, "Does not use redis.asyncio")
                return False
            
            # Check for deprecated import
            if "import aioredis" in content or "from aioredis" in content:
                self.log_test("No Deprecated Imports", False, "Still contains aioredis imports")
                return False
            else:
                self.log_test("No Deprecated Imports", True, "No aioredis imports found")
            
            return True
            
        except Exception as e:
            self.log_test("Redis Service Imports", False, f"Error: {e}")
            return False
    
    def test_dependencies_file(self):
        """Test that dependencies.py uses correct Redis import."""
        try:
            deps_path = Path("renum-backend/app/core/dependencies.py")
            if not deps_path.exists():
                self.log_test("Dependencies File", False, "File not found")
                return False
            
            with open(deps_path, 'r') as f:
                content = f.read()
            
            # Check for correct import
            if "import redis.asyncio as redis" in content:
                self.log_test("Dependencies Import", True, "Uses redis.asyncio correctly")
            else:
                self.log_test("Dependencies Import", False, "Does not use redis.asyncio")
                return False
            
            # Check for deprecated import
            if "import aioredis" in content:
                self.log_test("Dependencies No Deprecated", False, "Still contains aioredis import")
                return False
            else:
                self.log_test("Dependencies No Deprecated", True, "No aioredis imports found")
            
            # Check for correct connection method
            if "redis.from_url" in content:
                self.log_test("Dependencies Connection", True, "Uses redis.from_url correctly")
            else:
                self.log_test("Dependencies Connection", False, "Does not use redis.from_url")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Dependencies File", False, f"Error: {e}")
            return False
    
    def test_requirements_files(self):
        """Test that requirements files are updated."""
        try:
            # Check backend pyproject.toml
            backend_req = Path("backend/pyproject.toml")
            if backend_req.exists():
                with open(backend_req, 'r') as f:
                    content = f.read()
                
                if "redis>=5" in content or "redis==5" in content:
                    self.log_test("Backend Requirements", True, "Redis version updated")
                else:
                    self.log_test("Backend Requirements", False, "Redis version not updated")
                    return False
            
            # Check renum-backend requirements.txt
            renum_req = Path("renum-backend/requirements.txt")
            if renum_req.exists():
                with open(renum_req, 'r') as f:
                    content = f.read()
                
                if "aioredis" in content:
                    self.log_test("Renum Requirements", False, "Still contains aioredis")
                    return False
                else:
                    self.log_test("Renum Requirements", True, "No aioredis in requirements")
            
            return True
            
        except Exception as e:
            self.log_test("Requirements Files", False, f"Error: {e}")
            return False
    
    def test_redis_config_file(self):
        """Test that Redis configuration is updated."""
        try:
            config_path = Path("backend/services/docker/redis.conf")
            if not config_path.exists():
                self.log_test("Redis Config File", False, "File not found")
                return False
            
            with open(config_path, 'r') as f:
                content = f.read()
            
            required_settings = [
                "maxmemory",
                "maxmemory-policy",
                "appendonly",
                "timeout",
                "requirepass"
            ]
            
            missing_settings = []
            for setting in required_settings:
                if setting not in content:
                    missing_settings.append(setting)
            
            if missing_settings:
                self.log_test("Redis Config", False, f"Missing settings: {missing_settings}")
                return False
            else:
                self.log_test("Redis Config", True, "All required settings present")
            
            return True
            
        except Exception as e:
            self.log_test("Redis Config File", False, f"Error: {e}")
            return False
    
    def test_env_files(self):
        """Test that environment files have Redis password."""
        try:
            # Check backend .env
            backend_env = Path("backend/.env")
            if backend_env.exists():
                with open(backend_env, 'r') as f:
                    content = f.read()
                
                if "REDIS_PASSWORD=secure_redis_password" in content:
                    self.log_test("Backend Env", True, "Redis password configured")
                else:
                    self.log_test("Backend Env", False, "Redis password not configured")
                    return False
            
            # Check renum-backend .env
            renum_env = Path("renum-backend/.env")
            if renum_env.exists():
                with open(renum_env, 'r') as f:
                    content = f.read()
                
                if "REDIS_URL=redis://:secure_redis_password@redis:6379/0" in content:
                    self.log_test("Renum Env", True, "Redis URL with password configured")
                else:
                    self.log_test("Renum Env", False, "Redis URL not properly configured")
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Env Files", False, f"Error: {e}")
            return False
    
    def test_code_syntax(self):
        """Test that Python files have valid syntax."""
        try:
            files_to_check = [
                "backend/services/redis.py",
                "renum-backend/app/core/dependencies.py"
            ]
            
            for file_path in files_to_check:
                path = Path(file_path)
                if path.exists():
                    with open(path, 'r') as f:
                        content = f.read()
                    
                    try:
                        ast.parse(content)
                        self.log_test(f"Syntax {path.name}", True, "Valid Python syntax")
                    except SyntaxError as e:
                        self.log_test(f"Syntax {path.name}", False, f"Syntax error: {e}")
                        return False
            
            return True
            
        except Exception as e:
            self.log_test("Code Syntax", False, f"Error: {e}")
            return False
    
    def test_import_compatibility(self):
        """Test that imports work correctly."""
        try:
            # Test redis.asyncio import
            try:
                import redis.asyncio as redis
                self.log_test("Redis Asyncio Import", True, "redis.asyncio available")
            except ImportError:
                self.log_test("Redis Asyncio Import", False, "redis.asyncio not available")
                return False
            
            # Test that aioredis is not used
            try:
                import aioredis
                self.log_test("Aioredis Not Used", False, "aioredis still available (should be removed)")
            except ImportError:
                self.log_test("Aioredis Not Used", True, "aioredis not available (good)")
            
            return True
            
        except Exception as e:
            self.log_test("Import Compatibility", False, f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("=== Redis Code Validation Suite ===\n")
        
        tests = [
            self.test_redis_service_imports,
            self.test_dependencies_file,
            self.test_requirements_files,
            self.test_redis_config_file,
            self.test_env_files,
            self.test_code_syntax,
            self.test_import_compatibility
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                test_name = test.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, f"Test crashed: {e}")
        
        # Summary
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All Redis code validation tests passed!")
            print("✅ Migration from aioredis to redis.asyncio is complete")
            print("✅ Configuration files are properly updated")
            print("✅ Code syntax is valid")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check the issues above.")
            return False


def main():
    """Main test runner."""
    validator = RedisCodeValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()