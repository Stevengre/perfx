#!/usr/bin/env python3
"""
Tests for the dependency manager
"""

import pytest
import tempfile
import os
import time
from pathlib import Path
from perfx.core.dependency_manager import DependencyManager, DependencyInfo


class TestDependencyManager:
    """Test cases for DependencyManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def dep_manager(self, temp_dir):
        """Create a dependency manager with temporary cache file"""
        cache_file = temp_dir / "test_cache.json"
        return DependencyManager(str(cache_file))
    
    def test_init(self, temp_dir):
        """Test dependency manager initialization"""
        cache_file = temp_dir / "cache.json"
        manager = DependencyManager(str(cache_file))
        
        assert manager.cache_file == cache_file
        assert manager.dependency_cache == {}
        assert cache_file.parent.exists()
    
    def test_file_dependency_detection(self, dep_manager, temp_dir):
        """Test file dependency detection"""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("initial content")
        
        # Check dependencies
        dependencies = [
            {"path": str(test_file), "type": "file"}
        ]
        
        # First run - should detect changes (new dependency)
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
        
        # Second run - should not detect changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is False
        
        # Modify file
        test_file.write_text("modified content")
        time.sleep(0.1)  # Ensure timestamp changes
        
        # Should detect changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
    
    def test_directory_dependency_detection(self, dep_manager, temp_dir):
        """Test directory dependency detection"""
        # Create a test directory with files
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        
        file1 = test_dir / "file1.txt"
        file2 = test_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        dependencies = [
            {"path": str(test_dir), "type": "directory"}
        ]
        
        # First run
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
        
        # Second run - no changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is False
        
        # Add new file
        file3 = test_dir / "file3.txt"
        file3.write_text("content3")
        
        # Should detect changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
    
    def test_directory_pattern_dependency(self, dep_manager, temp_dir):
        """Test directory dependency with file pattern"""
        # Create a test directory with different file types
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        
        py_file = test_dir / "script.py"
        txt_file = test_dir / "data.txt"
        py_file.write_text("print('hello')")
        txt_file.write_text("some data")
        
        dependencies = [
            {"path": str(test_dir), "type": "directory", "pattern": "*.py"}
        ]
        
        # First run
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
        
        # Second run - no changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is False
        
        # Modify Python file
        py_file.write_text("print('world')")
        time.sleep(0.1)
        
        # Should detect changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
        
        # Modify text file (should not affect dependency)
        txt_file.write_text("other data")
        time.sleep(0.1)
        
        # Should not detect changes (text file doesn't match pattern)
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is False
    
    def test_multiple_dependencies(self, dep_manager, temp_dir):
        """Test multiple dependencies"""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        dependencies = [
            {"path": str(file1), "type": "file"},
            {"path": str(file2), "type": "file"}
        ]
        
        # First run
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
        
        # Second run - no changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is False
        
        # Modify one file
        file1.write_text("modified content")
        time.sleep(0.1)
        
        # Should detect changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
    
    def test_missing_dependencies(self, dep_manager, temp_dir):
        """Test handling of missing dependencies"""
        missing_file = temp_dir / "missing.txt"
        
        dependencies = [
            {"path": str(missing_file), "type": "file"}
        ]
        
        # Should handle missing file gracefully
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True  # Missing dependency is considered changed
    
    def test_mark_step_completed(self, dep_manager, temp_dir):
        """Test marking step as completed"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        dependencies = [
            {"path": str(test_file), "type": "file"}
        ]
        
        # Run step
        dep_manager.check_dependencies_changed("test_step", dependencies)
        
        # Mark as completed
        dep_manager.mark_step_completed("test_step")
        
        # Check that timestamps were updated
        cache_info = dep_manager.dependency_cache.get("test_step", {})
        assert str(test_file) in cache_info
        
        # Modify file
        test_file.write_text("modified")
        time.sleep(0.1)
        
        # Should detect changes (file was actually modified)
        # mark_step_completed doesn't prevent detection of real changes
        changed = dep_manager.check_dependencies_changed("test_step", dependencies)
        assert changed is True
    
    def test_clear_cache(self, dep_manager, temp_dir):
        """Test clearing cache"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        dependencies = [
            {"path": str(test_file), "type": "file"}
        ]
        
        # Run step
        dep_manager.check_dependencies_changed("test_step", dependencies)
        assert "test_step" in dep_manager.dependency_cache
        
        # Clear specific step
        dep_manager.clear_cache("test_step")
        assert "test_step" not in dep_manager.dependency_cache
        
        # Clear all cache
        dep_manager.check_dependencies_changed("test_step", dependencies)
        dep_manager.clear_cache()
        assert dep_manager.dependency_cache == {}
    
    def test_get_cache_info(self, dep_manager, temp_dir):
        """Test getting cache information"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        dependencies = [
            {"path": str(test_file), "type": "file"}
        ]
        
        # Initial cache info
        info = dep_manager.get_cache_info()
        assert info["cached_steps"] == []
        assert info["total_dependencies"] == 0
        
        # After running step
        dep_manager.check_dependencies_changed("test_step", dependencies)
        info = dep_manager.get_cache_info()
        assert "test_step" in info["cached_steps"]
        assert info["total_dependencies"] == 1 