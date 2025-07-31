#!/usr/bin/env python3
"""
Dependency manager for detecting file and folder changes
"""

import os
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
import fnmatch


@dataclass
class DependencyInfo:
    """Information about a dependency"""
    path: str
    type: str  # 'file' or 'directory'
    last_modified: float
    size: Optional[int] = None
    hash: Optional[str] = None
    pattern: Optional[str] = None  # for directory patterns like "*.py"


class DependencyManager:
    """Manages file and folder dependencies for evaluation steps"""
    
    def __init__(self, cache_file: str = "results/.dependency_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.dependency_cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Dict[str, DependencyInfo]]:
        """Load dependency cache from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Convert back to DependencyInfo objects
                    result = {}
                    for step_name, deps in cache_data.items():
                        result[step_name] = {
                            dep_path: DependencyInfo(**dep_info)
                            for dep_path, dep_info in deps.items()
                        }
                    return result
            except Exception as e:
                print(f"Warning: Could not load dependency cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save dependency cache to file"""
        try:
            # Convert DependencyInfo objects to dicts
            cache_data = {}
            for step_name, deps in self.dependency_cache.items():
                cache_data[step_name] = {
                    dep_path: asdict(dep_info)
                    for dep_path, dep_info in deps.items()
                }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save dependency cache: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _get_directory_hash(self, dir_path: Path, pattern: Optional[str] = None) -> str:
        """Calculate hash of a directory (based on file contents and timestamps)"""
        try:
            files = []
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    if pattern and not fnmatch.fnmatch(file_path.name, pattern):
                        continue
                    stat = file_path.stat()
                    files.append((str(file_path), stat.st_mtime, stat.st_size))
            
            # Sort for consistent hash
            files.sort()
            content = json.dumps(files, sort_keys=True)
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""
    
    def _get_dependency_info(self, path: str, dep_type: str = "file", pattern: Optional[str] = None) -> Optional[DependencyInfo]:
        """Get current information about a dependency"""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return None
        
        if dep_type == "file":
            if path_obj.is_file():
                stat = path_obj.stat()
                return DependencyInfo(
                    path=str(path_obj),
                    type="file",
                    last_modified=stat.st_mtime,
                    size=stat.st_size,
                    hash=self._get_file_hash(path_obj)
                )
        elif dep_type == "directory":
            if path_obj.is_dir():
                return DependencyInfo(
                    path=str(path_obj),
                    type="directory",
                    last_modified=path_obj.stat().st_mtime,
                    hash=self._get_directory_hash(path_obj, pattern),
                    pattern=pattern
                )
        
        return None
    
    def check_dependencies_changed(self, step_name: str, dependencies: List[Dict[str, Any]]) -> bool:
        """
        Check if any dependencies have changed since last run
        
        Args:
            step_name: Name of the step
            dependencies: List of dependency configurations
            
        Returns:
            True if any dependency has changed, False otherwise
        """
        if not dependencies:
            return True  # No dependencies means always run
        
        current_deps = {}
        has_changes = False
        
        for dep_config in dependencies:
            dep_path = dep_config.get("path")
            dep_type = dep_config.get("type", "file")
            pattern = dep_config.get("pattern")
            
            if not dep_path:
                continue
            
            # Get current dependency info
            current_info = self._get_dependency_info(dep_path, dep_type, pattern)
            if current_info:
                current_deps[dep_path] = current_info
            
            # Check against cached info
            cached_info = self.dependency_cache.get(step_name, {}).get(dep_path)
            
            if not cached_info:
                # New dependency, consider it changed
                has_changes = True
            elif current_info:
                # Compare with cached info
                if (current_info.last_modified != cached_info.last_modified or
                    current_info.hash != cached_info.hash):
                    has_changes = True
        
        # Update cache only if there are changes
        if has_changes:
            self.dependency_cache[step_name] = current_deps
            self._save_cache()
        
        return has_changes
    
    def mark_step_completed(self, step_name: str):
        """Mark a step as completed (useful for manual cache management)"""
        if step_name in self.dependency_cache:
            # Recalculate current dependency info to mark as up-to-date
            current_time = time.time()
            for dep_path, dep_info in self.dependency_cache[step_name].items():
                # Recalculate hash and update timestamp
                path_obj = Path(dep_path)
                if path_obj.exists():
                    if dep_info.type == "file":
                        dep_info.hash = self._get_file_hash(path_obj)
                    elif dep_info.type == "directory":
                        dep_info.hash = self._get_directory_hash(path_obj, dep_info.pattern)
                dep_info.last_modified = current_time
            self._save_cache()
    
    def clear_cache(self, step_name: Optional[str] = None):
        """Clear dependency cache"""
        if step_name:
            if step_name in self.dependency_cache:
                del self.dependency_cache[step_name]
        else:
            self.dependency_cache.clear()
        self._save_cache()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache"""
        return {
            "cache_file": str(self.cache_file),
            "cached_steps": list(self.dependency_cache.keys()),
            "total_dependencies": sum(len(deps) for deps in self.dependency_cache.values())
        } 