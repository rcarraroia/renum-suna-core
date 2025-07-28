"""
Dependency Migrator for safe package updates.

Handles migration of Python dependencies including:
- Version updates
- Package replacements (e.g., aioredis -> redis.asyncio)
- Compatibility validation
- Code pattern updates
"""

import os
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DependencyMigrator:
    """Manages safe migration of Python dependencies."""
    
    def __init__(self):
        self.migration_rules = {
            'aioredis': {
                'new_package': 'redis',
                'version': '>=5.0.0',
                'import_changes': {
                    'import aioredis': 'import redis.asyncio as redis',
                    'from aioredis import': 'from redis.asyncio import',
                    'aioredis.Redis': 'redis.Redis',
                    'aioredis.from_url': 'redis.from_url'
                },
                'code_patterns': {
                    r'aioredis\.Redis\(': 'redis.Redis(',
                    r'aioredis\.from_url\(': 'redis.from_url(',
                    r'await\s+aioredis\.create_redis_pool': 'redis.Redis'
                }
            }
        }
        
    def analyze_current_dependencies(self, requirements_file: str) -> Dict[str, str]:
        """Analyze current dependencies and their versions."""
        dependencies = {}
        
        try:
            if not Path(requirements_file).exists():
                logger.warning(f"Requirements file not found: {requirements_file}")
                return dependencies
            
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package==version or package>=version
                        if '==' in line:
                            package, version = line.split('==', 1)
                        elif '>=' in line:
                            package, version = line.split('>=', 1)
                        elif '<=' in line:
                            package, version = line.split('<=', 1)
                        else:
                            package = line
                            version = 'latest'
                        
                        dependencies[package.strip()] = version.strip()
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Failed to analyze dependencies: {e}")
            return {}
    
    def find_deprecated_packages(self, dependencies: Dict[str, str]) -> List[str]:
        """Find deprecated packages that need migration."""
        deprecated = []
        
        for package in dependencies:
            if package in self.migration_rules:
                deprecated.append(package)
        
        return deprecated
    
    def update_requirements_file(self, requirements_file: str, updates: Dict[str, str]) -> bool:
        """Update requirements file with new package versions."""
        try:
            if not Path(requirements_file).exists():
                logger.error(f"Requirements file not found: {requirements_file}")
                return False
            
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
            
            updated_lines = []
            for line in lines:
                original_line = line.strip()
                
                if original_line and not original_line.startswith('#'):
                    # Check if this line contains a package we need to update
                    package_name = original_line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                    
                    if package_name in updates:
                        # Replace with new package/version
                        new_spec = updates[package_name]
                        updated_lines.append(f"{new_spec}\n")
                        logger.info(f"Updated dependency: {original_line} -> {new_spec}")
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Write updated requirements
            with open(requirements_file, 'w') as f:
                f.writelines(updated_lines)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update requirements file: {e}")
            return False
    
    def find_import_statements(self, file_path: str, package_name: str) -> List[Tuple[int, str]]:
        """Find import statements for a specific package in a Python file."""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for various import patterns
                if (line_stripped.startswith(f'import {package_name}') or
                    line_stripped.startswith(f'from {package_name}') or
                    f'import {package_name}' in line_stripped):
                    imports.append((line_num, line_stripped))
            
            return imports
            
        except Exception as e:
            logger.error(f"Failed to analyze imports in {file_path}: {e}")
            return []
    
    def update_import_statements(self, file_path: str, package_name: str) -> bool:
        """Update import statements for a migrated package."""
        try:
            if package_name not in self.migration_rules:
                logger.warning(f"No migration rules for package: {package_name}")
                return False
            
            rules = self.migration_rules[package_name]
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply import changes
            for old_import, new_import in rules['import_changes'].items():
                content = content.replace(old_import, new_import)
            
            # Apply code pattern changes
            for pattern, replacement in rules['code_patterns'].items():
                content = re.sub(pattern, replacement, content)
            
            # Only write if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"Updated imports in: {file_path}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update imports in {file_path}: {e}")
            return False
    
    def find_python_files_with_imports(self, directory: str, package_name: str) -> List[str]:
        """Find all Python files that import a specific package."""
        files_with_imports = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip common directories that don't need updates
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'node_modules']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        imports = self.find_import_statements(file_path, package_name)
                        
                        if imports:
                            files_with_imports.append(file_path)
            
            return files_with_imports
            
        except Exception as e:
            logger.error(f"Failed to find Python files with imports: {e}")
            return []
    
    def migrate_package(self, package_name: str, project_dirs: List[str]) -> bool:
        """Migrate a package across multiple project directories."""
        try:
            if package_name not in self.migration_rules:
                logger.error(f"No migration rules for package: {package_name}")
                return False
            
            logger.info(f"Starting migration for package: {package_name}")
            
            # Find all files that need updates
            all_files = []
            for directory in project_dirs:
                if Path(directory).exists():
                    files = self.find_python_files_with_imports(directory, package_name)
                    all_files.extend(files)
            
            logger.info(f"Found {len(all_files)} files to update")
            
            # Update each file
            success_count = 0
            for file_path in all_files:
                if self.update_import_statements(file_path, package_name):
                    success_count += 1
            
            logger.info(f"Successfully updated {success_count}/{len(all_files)} files")
            return success_count == len(all_files)
            
        except Exception as e:
            logger.error(f"Failed to migrate package {package_name}: {e}")
            return False
    
    def validate_migration(self, project_dirs: List[str]) -> Tuple[bool, List[str]]:
        """Validate that migration was successful."""
        issues = []
        
        try:
            # Check for remaining deprecated imports
            for directory in project_dirs:
                if not Path(directory).exists():
                    continue
                    
                for package_name in self.migration_rules:
                    files = self.find_python_files_with_imports(directory, package_name)
                    
                    if files:
                        issues.append(f"Still found {package_name} imports in {len(files)} files")
            
            # Try to import new packages
            for package_name, rules in self.migration_rules.items():
                new_package = rules['new_package']
                try:
                    __import__(new_package)
                except ImportError:
                    issues.append(f"New package not available: {new_package}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Validation failed: {e}")
            return False, issues
    
    def create_migration_plan(self, requirements_files: List[str], project_dirs: List[str]) -> Dict:
        """Create a comprehensive migration plan."""
        plan = {
            "deprecated_packages": [],
            "files_to_update": {},
            "requirements_updates": {},
            "estimated_changes": 0
        }
        
        try:
            # Analyze all requirements files
            all_dependencies = {}
            for req_file in requirements_files:
                if Path(req_file).exists():
                    deps = self.analyze_current_dependencies(req_file)
                    all_dependencies.update(deps)
            
            # Find deprecated packages
            deprecated = self.find_deprecated_packages(all_dependencies)
            plan["deprecated_packages"] = deprecated
            
            # Find files that need updates
            for package in deprecated:
                files = []
                for directory in project_dirs:
                    if Path(directory).exists():
                        files.extend(self.find_python_files_with_imports(directory, package))
                
                plan["files_to_update"][package] = files
                plan["estimated_changes"] += len(files)
            
            # Create requirements updates
            for package in deprecated:
                if package in self.migration_rules:
                    rules = self.migration_rules[package]
                    new_spec = f"{rules['new_package']}{rules['version']}"
                    plan["requirements_updates"][package] = new_spec
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create migration plan: {e}")
            return plan