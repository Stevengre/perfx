#!/usr/bin/env python3
"""
Repository manager for handling dependent repositories
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class RepositoryManager:
    """Manages dependent repositories for evaluation"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.repositories_dir = self.base_dir / "repositories"

    def setup_repositories(self, repositories: List[Dict[str, Any]]) -> Dict[str, Path]:
        """
        Set up all required repositories

        Args:
            repositories: List of repository configurations

        Returns:
            Dict mapping repository names to their local paths
        """
        if not repositories:
            return {}

        console.print("[bold blue]Setting up repositories...[/bold blue]")

        # Create repositories directory
        self.repositories_dir.mkdir(exist_ok=True)

        repo_paths = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            for repo_config in repositories:
                task = progress.add_task(
                    f"Setting up {repo_config['name']}...", total=None
                )

                try:
                    repo_path = self._setup_single_repository(repo_config)
                    repo_paths[repo_config["name"]] = repo_path
                    progress.update(task, description=f"✅ {repo_config['name']} ready")

                except Exception as e:
                    progress.update(
                        task, description=f"❌ {repo_config['name']} failed"
                    )
                    console.print(
                        f"[red]Error setting up {repo_config['name']}: {e}[/red]"
                    )
                    raise

        console.print(f"[green]✅ All repositories set up successfully![/green]")
        return repo_paths

    def _setup_single_repository(self, repo_config: Dict[str, Any]) -> Path:
        """
        Set up a single repository

        Args:
            repo_config: Repository configuration

        Returns:
            Path to the repository
        """
        name = repo_config["name"]
        url = repo_config["url"]
        branch = repo_config.get("branch", "main")
        path = repo_config.get("path", name)
        submodules = repo_config.get("submodules", True)

        repo_path = self.repositories_dir / path

        # Check if repository already exists
        if repo_path.exists() and (repo_path / ".git").exists():
            console.print(
                f"[yellow]Repository {name} already exists, updating...[/yellow]"
            )
            return self._update_repository(repo_path, branch, submodules)
        else:
            console.print(f"[blue]Cloning {name} from {url}...[/blue]")
            return self._clone_repository(url, repo_path, branch, submodules)

    def _clone_repository(
        self, url: str, repo_path: Path, branch: str, submodules: bool
    ) -> Path:
        """Clone a repository"""
        try:
            # Clone the repository
            cmd = ["git", "clone", "--branch", branch, url, str(repo_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Initialize submodules if requested
            if submodules:
                self._init_submodules(repo_path)

            return repo_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")

    def _update_repository(
        self, repo_path: Path, branch: str, submodules: bool
    ) -> Path:
        """Update an existing repository"""
        try:
            # Fetch latest changes
            subprocess.run(["git", "fetch"], cwd=repo_path, check=True)

            # Checkout the specified branch
            subprocess.run(["git", "checkout", branch], cwd=repo_path, check=True)

            # Pull latest changes
            subprocess.run(["git", "pull"], cwd=repo_path, check=True)

            # Update submodules if requested
            if submodules:
                self._init_submodules(repo_path)

            return repo_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to update repository: {e}")

    def _init_submodules(self, repo_path: Path) -> None:
        """Initialize and update submodules"""
        try:
            console.print(
                f"[blue]Initializing submodules in {repo_path.name}...[/blue]"
            )

            # Initialize submodules
            subprocess.run(
                ["git", "submodule", "update", "--init", "--recursive"],
                cwd=repo_path,
                check=True,
            )

        except subprocess.CalledProcessError as e:
            console.print(
                f"[yellow]Warning: Failed to initialize submodules: {e}[/yellow]"
            )

    def get_repository_path(self, name: str) -> Optional[Path]:
        """Get the path of a repository by name"""
        # First check in repositories directory
        repo_path = self.repositories_dir / name
        if repo_path.exists():
            return repo_path

        # Check if it's a subdirectory
        for subdir in self.repositories_dir.iterdir():
            if subdir.is_dir() and subdir.name == name:
                return subdir

        return None

    def clean_repositories(self) -> None:
        """Remove all downloaded repositories"""
        if self.repositories_dir.exists():
            shutil.rmtree(self.repositories_dir)
            console.print("[green]✅ All repositories cleaned[/green]")

    def list_repositories(self) -> List[str]:
        """List all available repositories"""
        if not self.repositories_dir.exists():
            return []

        repos = []
        for item in self.repositories_dir.iterdir():
            if item.is_dir() and (item / ".git").exists():
                repos.append(item.name)

        return repos
