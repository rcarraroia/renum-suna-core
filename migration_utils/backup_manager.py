"""
Backup Manager for critical system configurations and data.

Provides automated backup and restore functionality for:
- Configuration files
- Database schemas
- Docker configurations
- Environment variables
"""

import os
import json
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backups of critical system components."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def create_backup_session(self, session_name: str) -> str:
        """Create a new backup session directory."""
        session_dir = self.backup_dir / f"{session_name}_{self.timestamp}"
        session_dir.mkdir(exist_ok=True)
        return str(session_dir)
    
    def backup_file(self, file_path: str, session_dir: str, description: str = "") -> bool:
        """Backup a single file with metadata."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                logger.warning(f"File not found for backup: {file_path}")
                return False
                
            session_path = Path(session_dir)
            backup_path = session_path / source_path.name
            
            # Copy file
            shutil.copy2(source_path, backup_path)
            
            # Create metadata
            metadata = {
                "original_path": str(source_path),
                "backup_path": str(backup_path),
                "timestamp": self.timestamp,
                "description": description,
                "file_size": source_path.stat().st_size
            }
            
            metadata_path = session_path / f"{source_path.name}.metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Backed up: {file_path} -> {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            return False
    
    def backup_directory(self, dir_path: str, session_dir: str, description: str = "") -> bool:
        """Backup an entire directory."""
        try:
            source_path = Path(dir_path)
            if not source_path.exists():
                logger.warning(f"Directory not found for backup: {dir_path}")
                return False
                
            session_path = Path(session_dir)
            backup_path = session_path / source_path.name
            
            # Copy directory
            shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
            
            # Create metadata
            metadata = {
                "original_path": str(source_path),
                "backup_path": str(backup_path),
                "timestamp": self.timestamp,
                "description": description,
                "type": "directory"
            }
            
            metadata_path = session_path / f"{source_path.name}.metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Backed up directory: {dir_path} -> {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup directory {dir_path}: {e}")
            return False
    
    def backup_critical_configs(self) -> str:
        """Backup all critical configuration files."""
        session_dir = self.create_backup_session("critical_configs")
        
        critical_files = [
            "docker-compose.yaml",
            "backend/pyproject.toml", 
            "renum-backend/requirements.txt",
            "backend/services/docker/redis.conf",
            "backend/.env",
            "frontend/.env.local"
        ]
        
        success_count = 0
        for file_path in critical_files:
            if self.backup_file(file_path, session_dir, "Critical configuration"):
                success_count += 1
        
        logger.info(f"Backed up {success_count}/{len(critical_files)} critical files")
        return session_dir
    
    def restore_file(self, metadata_path: str) -> bool:
        """Restore a file from backup using its metadata."""
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            backup_path = Path(metadata["backup_path"])
            original_path = Path(metadata["original_path"])
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create parent directories if needed
            original_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore file
            shutil.copy2(backup_path, original_path)
            logger.info(f"Restored: {backup_path} -> {original_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from {metadata_path}: {e}")
            return False
    
    def list_backup_sessions(self) -> List[Dict]:
        """List all available backup sessions."""
        sessions = []
        for session_dir in self.backup_dir.iterdir():
            if session_dir.is_dir():
                metadata_files = list(session_dir.glob("*.metadata.json"))
                sessions.append({
                    "session_name": session_dir.name,
                    "path": str(session_dir),
                    "file_count": len(metadata_files),
                    "created": session_dir.stat().st_ctime
                })
        return sorted(sessions, key=lambda x: x["created"], reverse=True)