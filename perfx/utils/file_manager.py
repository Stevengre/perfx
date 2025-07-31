#!/usr/bin/env python3
"""
Enhanced file operations manager for EVM evaluation
"""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json


class FileOperationManager:
    """Enhanced file operations manager with backup, version control, and rollback capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backup_enabled = config.get("backup_enabled", True)
        self.backup_suffix = config.get("backup_suffix", ".backup")
        self.version_control = config.get("version_control", True)
        self.rollback_on_failure = config.get("rollback_on_failure", True)
        self.safe_mode = config.get("safe_mode", True)
        
        # Initialize backup directory
        self.backup_dir = Path("evaluation_results/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Track operations
        self.operations_log = []
        self.backup_files = {}
        self.modified_files = set()
    
    def backup_file(self, file_path: str, description: str = "") -> bool:
        """Create a backup of a file with version control"""
        if not self.backup_enabled:
            return True
        
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self._log_operation(f"Backup failed: File not found - {file_path}")
                return False
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_path.stem}_{timestamp}{self.backup_suffix}"
            backup_path = self.backup_dir / backup_name
            
            # Copy file
            shutil.copy2(source_path, backup_path)
            
            # Record backup
            self.backup_files[file_path] = {
                "backup_path": str(backup_path),
                "timestamp": timestamp,
                "description": description
            }
            
            self._log_operation(f"Backup created: {file_path} -> {backup_path}")
            return True
            
        except Exception as e:
            self._log_operation(f"Backup failed: {file_path} - {str(e)}")
            return False
    
    def modify_file(self, file_path: str, modifications: List[Dict[str, str]], 
                   backup_description: str = "") -> bool:
        """Modify a file with backup and rollback support"""
        if not self.safe_mode:
            return self._modify_file_unsafe(file_path, modifications)
        
        # Create backup first
        if not self.backup_file(file_path, backup_description):
            return False
        
        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply modifications
            modified_content = content
            for mod in modifications:
                old_text = mod.get("old", "")
                new_text = mod.get("new", "")
                if old_text in modified_content:
                    modified_content = modified_content.replace(old_text, new_text)
                else:
                    self._log_operation(f"Warning: Text not found in {file_path}: {old_text}")
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            self.modified_files.add(file_path)
            self._log_operation(f"File modified: {file_path}")
            return True
            
        except Exception as e:
            self._log_operation(f"File modification failed: {file_path} - {str(e)}")
            # Rollback on failure
            if self.rollback_on_failure:
                self.rollback_file(file_path)
            return False
    
    def _modify_file_unsafe(self, file_path: str, modifications: List[Dict[str, str]]) -> bool:
        """Modify file without safety checks"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified_content = content
            for mod in modifications:
                old_text = mod.get("old", "")
                new_text = mod.get("new", "")
                modified_content = modified_content.replace(old_text, new_text)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            self._log_operation(f"File modified (unsafe): {file_path}")
            return True
            
        except Exception as e:
            self._log_operation(f"Unsafe file modification failed: {file_path} - {str(e)}")
            return False
    
    def rollback_file(self, file_path: str) -> bool:
        """Rollback a file to its most recent backup"""
        if file_path not in self.backup_files:
            self._log_operation(f"Rollback failed: No backup found for {file_path}")
            return False
        
        try:
            backup_info = self.backup_files[file_path]
            backup_path = Path(backup_info["backup_path"])
            
            if not backup_path.exists():
                self._log_operation(f"Rollback failed: Backup file not found - {backup_path}")
                return False
            
            # Restore file
            shutil.copy2(backup_path, file_path)
            
            # Remove from modified files
            self.modified_files.discard(file_path)
            
            self._log_operation(f"File rolled back: {file_path} <- {backup_path}")
            return True
            
        except Exception as e:
            self._log_operation(f"Rollback failed: {file_path} - {str(e)}")
            return False
    
    def restore_file(self, file_path: str, backup_timestamp: Optional[str] = None) -> bool:
        """Restore a file to a specific backup version"""
        if file_path not in self.backup_files:
            self._log_operation(f"Restore failed: No backup found for {file_path}")
            return False
        
        try:
            backup_info = self.backup_files[file_path]
            
            if backup_timestamp:
                # Find specific backup
                backup_path = self.backup_dir / f"{Path(file_path).stem}_{backup_timestamp}{self.backup_suffix}"
                if not backup_path.exists():
                    self._log_operation(f"Restore failed: Specific backup not found - {backup_path}")
                    return False
            else:
                # Use most recent backup
                backup_path = Path(backup_info["backup_path"])
            
            # Restore file
            shutil.copy2(backup_path, file_path)
            
            self._log_operation(f"File restored: {file_path} <- {backup_path}")
            return True
            
        except Exception as e:
            self._log_operation(f"Restore failed: {file_path} - {str(e)}")
            return False
    
    def list_backups(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """List available backups"""
        if file_path:
            if file_path in self.backup_files:
                return {file_path: self.backup_files[file_path]}
            return {}
        
        return self.backup_files.copy()
    
    def cleanup_backups(self, keep_count: int = 5) -> int:
        """Clean up old backups, keeping only the most recent ones"""
        if not self.version_control:
            return 0
        
        cleaned_count = 0
        
        # Group backups by original file
        file_backups = {}
        for original_file, backup_info in self.backup_files.items():
            if original_file not in file_backups:
                file_backups[original_file] = []
            file_backups[original_file].append(backup_info)
        
        # Clean up each file's backups
        for original_file, backups in file_backups.items():
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Remove old backups
            for backup_info in backups[keep_count:]:
                backup_path = Path(backup_info["backup_path"])
                if backup_path.exists():
                    backup_path.unlink()
                    cleaned_count += 1
                    self._log_operation(f"Cleaned up backup: {backup_path}")
        
        return cleaned_count
    
    def get_operations_summary(self) -> Dict[str, Any]:
        """Get a summary of all file operations"""
        return {
            "total_operations": len(self.operations_log),
            "backups_created": len(self.backup_files),
            "files_modified": len(self.modified_files),
            "backup_directory": str(self.backup_dir),
            "config": {
                "backup_enabled": self.backup_enabled,
                "version_control": self.version_control,
                "rollback_on_failure": self.rollback_on_failure,
                "safe_mode": self.safe_mode
            },
            "recent_operations": self.operations_log[-10:] if self.operations_log else []
        }
    
    def _log_operation(self, message: str):
        """Log a file operation"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.operations_log.append(log_entry)
        
        # Also write to log file
        log_file = self.backup_dir / "file_operations.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")


class OpcodeController:
    """Controller for opcode-level operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.skip_opcodes = set(config.get("skip_opcodes", []))
        self.skip_categories = set(config.get("skip_categories", []))
        self.include_only = set(config.get("include_only", []))
        self.include_categories = set(config.get("include_categories", []))
        
        # Load opcode categories
        self.opcode_categories = config.get("opcode_categories", {})
        self.category_to_opcodes = self._build_category_mapping()
    
    def _build_category_mapping(self) -> Dict[str, List[str]]:
        """Build mapping from category to opcodes"""
        mapping = {}
        for category, opcodes in self.opcode_categories.items():
            # Flatten the opcode lists
            flat_opcodes = []
            for opcode_list in opcodes:
                if isinstance(opcode_list, str):
                    flat_opcodes.extend([op.strip() for op in opcode_list.split(',')])
                elif isinstance(opcode_list, list):
                    flat_opcodes.extend(opcode_list)
            mapping[category] = flat_opcodes
        return mapping
    
    def should_process_opcode(self, opcode: str) -> bool:
        """Check if an opcode should be processed based on current configuration"""
        # Check if opcode is explicitly skipped
        if opcode in self.skip_opcodes:
            return False
        
        # Check if opcode's category is skipped
        opcode_category = self._get_opcode_category(opcode)
        if opcode_category in self.skip_categories:
            return False
        
        # Check include_only filter
        if self.include_only and opcode not in self.include_only:
            return False
        
        # Check include_categories filter
        if self.include_categories and opcode_category not in self.include_categories:
            return False
        
        return True
    
    def _get_opcode_category(self, opcode: str) -> str:
        """Get the category of an opcode"""
        for category, opcodes in self.category_to_opcodes.items():
            if opcode in opcodes:
                return category
        return "UNKNOWN"
    
    def get_filtered_opcodes(self, all_opcodes: List[str]) -> List[str]:
        """Get a filtered list of opcodes based on current configuration"""
        return [opcode for opcode in all_opcodes if self.should_process_opcode(opcode)]
    
    def get_category_statistics(self, opcodes: List[str]) -> Dict[str, Dict[str, int]]:
        """Get statistics by category for a list of opcodes"""
        stats = {}
        
        for opcode in opcodes:
            category = self._get_opcode_category(opcode)
            if category not in stats:
                stats[category] = {"total": 0, "processed": 0, "skipped": 0}
            
            stats[category]["total"] += 1
            
            if self.should_process_opcode(opcode):
                stats[category]["processed"] += 1
            else:
                stats[category]["skipped"] += 1
        
        return stats 