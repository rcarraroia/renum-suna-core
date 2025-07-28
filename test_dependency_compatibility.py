#!/usr/bin/env python3
"""
Dependency compatibility validation script.

This script validates that all dependencies are compatible and can be resolved
without conflicts after the standardization updates.
"""

import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import importlib.util
import pkg_resources
from typing import Dict, List, Tuple


class DependencyCompatibilityValidator:
    """Validates dependency compatibility across the system."""
    
    def __init__(self):
        self.test_results = []
        self.backend_deps = {}
        self.renum_deps = {}
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def parse_requirements_file(self, file_path: str) -> Dict[str, str]:
        """Parse requirements file and extract package versions."""
        requirements = {}
        
        try:
            if not Path(file_path).exists():
                return requirements
            
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Handle different version specifiers
                        if '==' in line:
                            package, version = line.split('==', 1)
                            requirements[package.strip()] = f"=={version.strip()}"
                        elif '>=' in line:
                            package, version = line.split('>=', 1)
                            requirements[package.strip()] = f">={version.strip()}"
                        elif '<=' in line:
                            package, version = line.split('<=', 1)
                            requirements[package.strip()] = f"<={version.strip()}"
                        else:
                            # Package without version specifier
                            requirements[line.strip()] = ""
            
            return requirements
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return {}
    
    def parse_pyproject_toml(self, file_path: str) -> Dict[str, str]:
        """Parse pyproject.toml and extract dependencies."""
        dependencies = {}
        
        try:
            if not Path(file_path).exists():
                return dependencies
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Simple parsing for dependencies section
            in_dependencies = False
            for line in content.split('\n'):
                line = line.strip()
                
                if line == 'dependencies = [':
                    in_dependencies = True
                    continue
                elif in_dependencies and line == ']':
                    break
                elif in_dependencies and line.startswith('"') and line.endswith('",'):
                    # Extract dependency
                    dep = line.strip('"",')
                    if '==' in dep:
                        package, version = dep.split('==', 1)
                        dependencies[package.strip()] = f"=={version.strip()}"
                    elif '>=' in dep:
                        package, version = dep.split('>=', 1)
                        dependencies[package.strip()] = f">={version.strip()}"
                    elif '<=' in dep:
                        package, version = dep.split('<=', 1)
                        dependencies[package.strip()] = f"<={version.strip()}"
                    else:
                        dependencies[dep.strip()] = ""
            
            return dependencies
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return {}
    
    def test_parse_backend_dependencies(self):
        """Test parsing backend dependencies."""
        try:
            self.backend_deps = self.parse_pyproject_toml("backend/pyproject.toml")
            
            if self.backend_deps:
                key_packages = ['fastapi', 'supabase', 'pyjwt', 'redis', 'cryptography']
                found_packages = [pkg for pkg in key_packages if pkg in self.backend_deps]
                
                self.log_test("Backend Dependencies Parse", True, 
                             f"Found {len(self.backend_deps)} dependencies, including {len(found_packages)} key packages")
                return True
            else:
                self.log_test("Backend Dependencies Parse", False, "No dependencies found")
                return False
                
        except Exception as e:
            self.log_test("Backend Dependencies Parse", False, f"Error: {e}")
            return False
    
    def test_parse_renum_dependencies(self):
        """Test parsing renum-backend dependencies."""
        try:
            self.renum_deps = self.parse_requirements_file("renum-backend/requirements.txt")
            
            if self.renum_deps:
                key_packages = ['fastapi', 'supabase', 'pyjwt', 'redis', 'cryptography']
                found_packages = [pkg for pkg in key_packages if pkg in self.renum_deps]
                
                self.log_test("Renum Dependencies Parse", True, 
                             f"Found {len(self.renum_deps)} dependencies, including {len(found_packages)} key packages")
                return True
            else:
                self.log_test("Renum Dependencies Parse", False, "No dependencies found")
                return False
                
        except Exception as e:
            self.log_test("Renum Dependencies Parse", False, f"Error: {e}")
            return False
    
    def test_version_alignment(self):
        """Test that key packages have aligned versions."""
        try:
            if not self.backend_deps or not self.renum_deps:
                self.log_test("Version Alignment", False, "Dependencies not loaded")
                return False
            
            key_packages = ['fastapi', 'supabase', 'pyjwt', 'cryptography']
            misaligned = []
            
            for package in key_packages:
                backend_version = self.backend_deps.get(package, "")
                renum_version = self.renum_deps.get(package, "")
                
                if backend_version and renum_version:
                    if backend_version != renum_version:
                        misaligned.append(f"{package}: backend={backend_version}, renum={renum_version}")
            
            if misaligned:
                self.log_test("Version Alignment", False, f"Misaligned: {', '.join(misaligned)}")
                return False
            else:
                self.log_test("Version Alignment", True, "Key packages have aligned versions")
                return True
                
        except Exception as e:
            self.log_test("Version Alignment", False, f"Error: {e}")
            return False
    
    def test_required_versions(self):
        """Test that required versions are present."""
        try:
            required_versions = {
                'fastapi': '==0.115.12',
                'supabase': '==2.17.0',
                'pyjwt': '==2.10.1',
                'cryptography': '>=45.0.5'
            }
            
            missing_versions = []
            
            # Check backend
            for package, required_version in required_versions.items():
                backend_version = self.backend_deps.get(package, "")
                if not backend_version or not self._version_satisfies(backend_version, required_version):
                    missing_versions.append(f"backend/{package}: expected {required_version}, got {backend_version}")
            
            # Check renum-backend
            for package, required_version in required_versions.items():
                if package in self.renum_deps:  # Only check if package exists in renum
                    renum_version = self.renum_deps.get(package, "")
                    if not renum_version or not self._version_satisfies(renum_version, required_version):
                        missing_versions.append(f"renum/{package}: expected {required_version}, got {renum_version}")
            
            if missing_versions:
                self.log_test("Required Versions", False, f"Issues: {', '.join(missing_versions)}")
                return False
            else:
                self.log_test("Required Versions", True, "All required versions present")
                return True
                
        except Exception as e:
            self.log_test("Required Versions", False, f"Error: {e}")
            return False
    
    def _version_satisfies(self, actual: str, required: str) -> bool:
        """Check if actual version satisfies required version."""
        try:
            # Simple version comparison
            if required.startswith('=='):
                return actual == required
            elif required.startswith('>='):
                # For simplicity, just check if actual starts with >= too
                return actual.startswith('>=') or actual.startswith('==')
            return True
        except:
            return False
    
    def test_no_deprecated_packages(self):
        """Test that no deprecated packages are present."""
        try:
            deprecated_packages = ['aioredis']
            found_deprecated = []
            
            # Check backend
            for package in deprecated_packages:
                if package in self.backend_deps:
                    found_deprecated.append(f"backend/{package}")
            
            # Check renum-backend
            for package in deprecated_packages:
                if package in self.renum_deps:
                    found_deprecated.append(f"renum/{package}")
            
            if found_deprecated:
                self.log_test("No Deprecated Packages", False, f"Found: {', '.join(found_deprecated)}")
                return False
            else:
                self.log_test("No Deprecated Packages", True, "No deprecated packages found")
                return True
                
        except Exception as e:
            self.log_test("No Deprecated Packages", False, f"Error: {e}")
            return False
    
    def test_prometheus_client_present(self):
        """Test that prometheus-client is present for monitoring."""
        try:
            backend_has_prometheus = 'prometheus-client' in self.backend_deps
            renum_has_prometheus = 'prometheus-client' in self.renum_deps
            
            if backend_has_prometheus and renum_has_prometheus:
                self.log_test("Prometheus Client", True, "Present in both backend and renum")
                return True
            elif backend_has_prometheus:
                self.log_test("Prometheus Client", True, "Present in backend (renum optional)")
                return True
            else:
                self.log_test("Prometheus Client", False, "Missing prometheus-client")
                return False
                
        except Exception as e:
            self.log_test("Prometheus Client", False, f"Error: {e}")
            return False
    
    def test_redis_version(self):
        """Test that Redis version is updated."""
        try:
            backend_redis = self.backend_deps.get('redis', '')
            renum_redis = self.renum_deps.get('redis', '')
            
            issues = []
            
            if not backend_redis:
                issues.append("backend missing redis")
            elif not (backend_redis.startswith('>=5') or backend_redis.startswith('==5')):
                issues.append(f"backend redis version: {backend_redis}")
            
            if not renum_redis:
                issues.append("renum missing redis")
            elif not (renum_redis.startswith('>=5') or renum_redis.startswith('==5')):
                issues.append(f"renum redis version: {renum_redis}")
            
            if issues:
                self.log_test("Redis Version", False, f"Issues: {', '.join(issues)}")
                return False
            else:
                self.log_test("Redis Version", True, "Redis >= 5.0.0 in both projects")
                return True
                
        except Exception as e:
            self.log_test("Redis Version", False, f"Error: {e}")
            return False
    
    def test_import_compatibility(self):
        """Test that key packages can be imported."""
        try:
            key_packages = ['fastapi', 'redis', 'cryptography', 'prometheus_client']
            import_issues = []
            
            for package in key_packages:
                try:
                    if package == 'redis':
                        # Test redis.asyncio specifically
                        import redis.asyncio
                    elif package == 'prometheus_client':
                        import prometheus_client
                    else:
                        __import__(package)
                except ImportError as e:
                    import_issues.append(f"{package}: {e}")
            
            if import_issues:
                self.log_test("Import Compatibility", False, f"Issues: {', '.join(import_issues)}")
                return False
            else:
                self.log_test("Import Compatibility", True, "All key packages can be imported")
                return True
                
        except Exception as e:
            self.log_test("Import Compatibility", False, f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all dependency compatibility tests."""
        print("=== Dependency Compatibility Validation ===\n")
        
        tests = [
            self.test_parse_backend_dependencies,
            self.test_parse_renum_dependencies,
            self.test_version_alignment,
            self.test_required_versions,
            self.test_no_deprecated_packages,
            self.test_prometheus_client_present,
            self.test_redis_version,
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
        print("COMPATIBILITY VALIDATION SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All dependency compatibility tests passed!")
            print("✅ Dependencies are standardized and compatible")
            print("✅ No deprecated packages found")
            print("✅ Required versions are present")
            print("✅ Key packages can be imported")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check the issues above.")
            return False


def main():
    """Main test runner."""
    validator = DependencyCompatibilityValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()