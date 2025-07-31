"""
Tests for RepositoryManager
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from perfx.core.repository_manager import RepositoryManager


class TestRepositoryManager:
    """Test RepositoryManager functionality"""

    def test_init(self):
        """Test repository manager initialization"""
        manager = RepositoryManager()
        
        assert manager.base_dir == Path(".")
        assert manager.repositories_dir == Path(".") / "repositories"

    def test_init_with_custom_base_dir(self):
        """Test initialization with custom base directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            assert manager.base_dir == Path(temp_dir)
            assert manager.repositories_dir == Path(temp_dir) / "repositories"

    def test_setup_repositories_empty(self):
        """Test setting up empty repositories list"""
        manager = RepositoryManager()
        
        result = manager.setup_repositories([])
        
        assert result == {}

    def test_setup_repositories_creates_directory(self):
        """Test that setup creates repositories directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            repositories = [
                {
                    "name": "test-repo",
                    "url": "https://github.com/test/test-repo.git",
                    "branch": "main",
                    "path": "test-repo",
                    "submodules": False
                }
            ]
            
            with patch.object(manager, '_setup_single_repository') as mock_setup:
                mock_setup.return_value = Path(temp_dir) / "repositories" / "test-repo"
                
                result = manager.setup_repositories(repositories)
            
            assert "test-repo" in result
            assert (Path(temp_dir) / "repositories").exists()

    def test_setup_single_repository_new(self):
        """Test setting up a new repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            repo_config = {
                "name": "test-repo",
                "url": "https://github.com/test/test-repo.git",
                "branch": "main",
                "path": "test-repo",
                "submodules": False
            }
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = manager._setup_single_repository(repo_config)
            
            expected_path = Path(temp_dir) / "repositories" / "test-repo"
            assert result == expected_path

    def test_setup_single_repository_existing(self):
        """Test setting up an existing repository"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            # Create existing repository
            repo_path = Path(temp_dir) / "repositories" / "test-repo"
            repo_path.mkdir(parents=True)
            (repo_path / ".git").mkdir()  # Simulate git repository
            
            repo_config = {
                "name": "test-repo",
                "url": "https://github.com/test/test-repo.git",
                "branch": "main",
                "path": "test-repo",
                "submodules": False
            }
            
            with patch.object(manager, '_update_repository') as mock_update:
                mock_update.return_value = repo_path
                
                result = manager._setup_single_repository(repo_config)
            
            assert result == repo_path
            mock_update.assert_called_once_with(repo_path, "main", False)

    def test_clone_repository_success(self):
        """Test successful repository cloning"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            url = "https://github.com/test/test-repo.git"
            repo_path = Path(temp_dir) / "repositories" / "test-repo"
            branch = "main"
            submodules = False
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = manager._clone_repository(url, repo_path, branch, submodules)
            
            assert result == repo_path
            mock_run.assert_called_once()

    def test_clone_repository_with_submodules(self):
        """Test repository cloning with submodules"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            url = "https://github.com/test/test-repo.git"
            repo_path = Path(temp_dir) / "repositories" / "test-repo"
            branch = "main"
            submodules = True
            
            with patch('subprocess.run') as mock_run:
                with patch.object(manager, '_init_submodules') as mock_submodules:
                    mock_run.return_value = Mock(returncode=0)
                    
                    result = manager._clone_repository(url, repo_path, branch, submodules)
                
                assert result == repo_path
                mock_submodules.assert_called_once_with(repo_path)

    def test_clone_repository_failure(self):
        """Test repository cloning failure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            url = "https://github.com/test/test-repo.git"
            repo_path = Path(temp_dir) / "repositories" / "test-repo"
            branch = "main"
            submodules = False
            
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Clone failed")
                
                with pytest.raises(Exception) as exc_info:
                    manager._clone_repository(url, repo_path, branch, submodules)
                
                assert "Clone failed" in str(exc_info.value)

    def test_update_repository_success(self):
        """Test successful repository update"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            repo_path = Path(temp_dir) / "test-repo"
            repo_path.mkdir()
            branch = "main"
            submodules = False
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = manager._update_repository(repo_path, branch, submodules)
            
            assert result == repo_path
            assert mock_run.call_count == 3  # fetch, checkout, pull

    def test_update_repository_with_submodules(self):
        """Test repository update with submodules"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            repo_path = Path(temp_dir) / "test-repo"
            repo_path.mkdir()
            branch = "main"
            submodules = True
            
            with patch('subprocess.run') as mock_run:
                with patch.object(manager, '_init_submodules') as mock_submodules:
                    mock_run.return_value = Mock(returncode=0)
                    
                    result = manager._update_repository(repo_path, branch, submodules)
                
                assert result == repo_path
                mock_submodules.assert_called_once_with(repo_path)

    def test_init_submodules_success(self):
        """Test successful submodule initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            repo_path = Path(temp_dir) / "test-repo"
            repo_path.mkdir()
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                manager._init_submodules(repo_path)
            
            mock_run.assert_called_once()

    def test_init_submodules_failure(self):
        """Test submodule initialization failure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            repo_path = Path(temp_dir) / "test-repo"
            repo_path.mkdir()
            
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "git submodule", "Submodule init failed")
                
                # Should not raise exception, just log warning
                manager._init_submodules(repo_path)

    def test_get_repository_path_exists(self):
        """Test getting existing repository path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            # Create repository
            repo_path = Path(temp_dir) / "repositories" / "test-repo"
            repo_path.mkdir(parents=True)
            
            result = manager.get_repository_path("test-repo")
            
            assert result == repo_path

    def test_get_repository_path_not_exists(self):
        """Test getting non-existent repository path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            # Create repositories directory but no repo inside
            repo_dir = Path(temp_dir) / "repositories"
            repo_dir.mkdir()
            
            result = manager.get_repository_path("non-existent")
            
            assert result is None

    def test_clean_repositories(self):
        """Test cleaning repositories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            # Create repositories directory with some content
            repo_dir = Path(temp_dir) / "repositories"
            repo_dir.mkdir()
            (repo_dir / "test-repo").mkdir()
            
            manager.clean_repositories()
            
            assert not repo_dir.exists()

    def test_clean_repositories_not_exists(self):
        """Test cleaning repositories when directory doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            # Should not raise exception
            manager.clean_repositories()

    def test_list_repositories_empty(self):
        """Test listing repositories when none exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            repos = manager.list_repositories()
            
            assert repos == []

    def test_list_repositories_with_repos(self):
        """Test listing repositories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = RepositoryManager(temp_dir)
            
            # Create repositories
            repo_dir = Path(temp_dir) / "repositories"
            repo_dir.mkdir()
            
            (repo_dir / "repo1").mkdir()
            (repo_dir / "repo1" / ".git").mkdir()
            
            (repo_dir / "repo2").mkdir()
            (repo_dir / "repo2" / ".git").mkdir()
            
            (repo_dir / "not-a-repo").mkdir()  # Directory without .git
            
            repos = manager.list_repositories()
            
            assert len(repos) == 2
            assert "repo1" in repos
            assert "repo2" in repos
            assert "not-a-repo" not in repos 