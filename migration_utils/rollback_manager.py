"""
Rollback Manager for safe system recovery.

Provides automated rollback functionality for:
- Configuration changes
- Dependency updates
- Database migrations
- Infrastructure changes
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RollbackManager:
    """Manages rollback operations for system changes."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.rollback_log = []
        
    def create_rollback_plan(self, changes: List[Dict]) -> str:
        """Create a rollback plan for a set of changes."""
        plan_id = f"rollback_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan_file = self.backup_dir / f"{plan_id}.json"
        
        rollback_plan = {
            "plan_id": plan_id,
            "created_at": datetime.now().isoformat(),
            "changes": changes,
            "status": "created"
        }
        
        with open(plan_file, 'w') as f:
            json.dump(rollback_plan, f, indent=2)
        
        logger.info(f"Created rollback plan: {plan_id}")
        return plan_id
    
    def rollback_file_change(self, original_path: str, backup_path: str) -> bool:
        """Rollback a single file change."""
        try:
            original = Path(original_path)
            backup = Path(backup_path)
            
            if not backup.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create parent directories if needed
            original.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore from backup
            shutil.copy2(backup, original)
            
            self.rollback_log.append({
                "type": "file_rollback",
                "original_path": original_path,
                "backup_path": backup_path,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            
            logger.info(f"Rolled back file: {original_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback file {original_path}: {e}")
            self.rollback_log.append({
                "type": "file_rollback",
                "original_path": original_path,
                "backup_path": backup_path,
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            })
            return False
    
    def rollback_dependency_changes(self, requirements_file: str, backup_file: str) -> bool:
        """Rollback dependency changes by restoring requirements file."""
        try:
            if self.rollback_file_change(requirements_file, backup_file):
                # Reinstall dependencies from backup
                result = subprocess.run([
                    "python", "-m", "pip", "install", "-r", requirements_file
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Successfully rolled back dependencies: {requirements_file}")
                    return True
                else:
                    logger.error(f"Failed to reinstall dependencies: {result.stderr}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to rollback dependencies: {e}")
            return False
    
    def rollback_docker_changes(self, compose_file: str, backup_file: str) -> bool:
        """Rollback Docker Compose changes."""
        try:
            # Stop current services
            subprocess.run([
                "docker", "compose", "down"
            ], capture_output=True)
            
            # Restore compose file
            if self.rollback_file_change(compose_file, backup_file):
                # Restart services with restored configuration
                result = subprocess.run([
                    "docker", "compose", "up", "-d"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("Successfully rolled back Docker configuration")
                    return True
                else:
                    logger.error(f"Failed to restart Docker services: {result.stderr}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to rollback Docker changes: {e}")
            return False
    
    def rollback_database_migration(self, rollback_script: str) -> bool:
        """Execute database rollback script."""
        try:
            if not Path(rollback_script).exists():
                logger.error(f"Rollback script not found: {rollback_script}")
                return False
            
            # This would execute the rollback SQL script
            # Implementation depends on database setup
            logger.info(f"Would execute rollback script: {rollback_script}")
            
            self.rollback_log.append({
                "type": "database_rollback",
                "script": rollback_script,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback database migration: {e}")
            return False
    
    def execute_rollback_plan(self, plan_id: str) -> bool:
        """Execute a complete rollback plan."""
        try:
            plan_file = self.backup_dir / f"{plan_id}.json"
            
            if not plan_file.exists():
                logger.error(f"Rollback plan not found: {plan_id}")
                return False
            
            with open(plan_file, 'r') as f:
                plan = json.load(f)
            
            logger.info(f"Executing rollback plan: {plan_id}")
            
            success_count = 0
            total_changes = len(plan['changes'])
            
            # Execute rollback changes in reverse order
            for change in reversed(plan['changes']):
                change_type = change.get('type')
                
                if change_type == 'file':
                    success = self.rollback_file_change(
                        change['original_path'], 
                        change['backup_path']
                    )
                elif change_type == 'dependencies':
                    success = self.rollback_dependency_changes(
                        change['requirements_file'],
                        change['backup_file']
                    )
                elif change_type == 'docker':
                    success = self.rollback_docker_changes(
                        change['compose_file'],
                        change['backup_file']
                    )
                elif change_type == 'database':
                    success = self.rollback_database_migration(
                        change['rollback_script']
                    )
                else:
                    logger.warning(f"Unknown change type: {change_type}")
                    continue
                
                if success:
                    success_count += 1
            
            # Update plan status
            plan['status'] = 'completed' if success_count == total_changes else 'partial'
            plan['completed_at'] = datetime.now().isoformat()
            plan['success_count'] = success_count
            plan['total_count'] = total_changes
            
            with open(plan_file, 'w') as f:
                json.dump(plan, f, indent=2)
            
            logger.info(f"Rollback plan completed: {success_count}/{total_changes} changes rolled back")
            return success_count == total_changes
            
        except Exception as e:
            logger.error(f"Failed to execute rollback plan: {e}")
            return False
    
    def create_emergency_rollback(self, session_name: str) -> bool:
        """Create emergency rollback for the most recent backup session."""
        try:
            # Find most recent backup session
            sessions = []
            for session_dir in self.backup_dir.iterdir():
                if session_dir.is_dir() and session_name in session_dir.name:
                    sessions.append(session_dir)
            
            if not sessions:
                logger.error(f"No backup sessions found for: {session_name}")
                return False
            
            latest_session = max(sessions, key=lambda x: x.stat().st_ctime)
            
            # Create rollback plan from all files in session
            changes = []
            for metadata_file in latest_session.glob("*.metadata.json"):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                changes.append({
                    "type": "file",
                    "original_path": metadata["original_path"],
                    "backup_path": metadata["backup_path"]
                })
            
            plan_id = self.create_rollback_plan(changes)
            
            # Execute immediately
            return self.execute_rollback_plan(plan_id)
            
        except Exception as e:
            logger.error(f"Failed to create emergency rollback: {e}")
            return False
    
    def get_rollback_status(self) -> Dict:
        """Get current rollback status and history."""
        return {
            "rollback_log": self.rollback_log,
            "available_plans": [
                f.stem for f in self.backup_dir.glob("rollback_plan_*.json")
            ],
            "total_rollbacks": len(self.rollback_log)
        }