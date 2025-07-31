#!/usr/bin/env python3
"""
Evaluation executor for running configured commands
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..parsers.base import ParserFactory
from .recorder import EvaluationRecorder
from .repository_manager import RepositoryManager

console = Console()


class EvaluationExecutor:
    """Executor for running evaluation steps"""

    def __init__(
        self,
        config: Dict[str, Any],
        output_dir: Optional[str] = None,
        verbose: bool = False,
    ):
        self.config = config
        self.verbose = verbose
        self.recorder = EvaluationRecorder()

        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(
                config.get("global", {}).get("output_directory", "results")
            )

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set working directory
        self.working_dir = Path(config.get("global", {}).get("working_directory", "."))

        # Initialize parser factory
        self.parser_factory = ParserFactory()

        # Load parsers from config
        self.parsers = {}
        if "parsers" in config:
            for parser_name, parser_config in config["parsers"].items():
                self.parsers[parser_name] = self.parser_factory.create_parser(
                    parser_config
                )

        # Initialize repository manager
        self.repo_manager = RepositoryManager(str(self.working_dir))
        self.repo_paths = {}

    def run(self, steps_to_run: Optional[List[str]] = None) -> bool:
        """Run evaluation steps"""
        steps = self.config.get("steps", [])

        if not steps:
            console.print("[yellow]No steps configured[/yellow]")
            return True

        # Filter steps if specified
        if steps_to_run:
            steps = [step for step in steps if step.get("name") in steps_to_run]

        # Filter enabled steps
        steps = [step for step in steps if step.get("enabled", True)]

        if not steps:
            console.print("[yellow]No enabled steps to run[/yellow]")
            return True

        console.print(f"[blue]Running {len(steps)} steps...[/blue]")

        # Set up repositories if configured
        if "repositories" in self.config:
            try:
                self.repo_paths = self.repo_manager.setup_repositories(
                    self.config["repositories"]
                )
            except Exception as e:
                console.print(f"[red]Failed to set up repositories: {e}[/red]")
                return False

        # Track dependencies
        completed_steps = set()
        failed_steps = set()

        for step in steps:
            step_name = step.get("name", "unknown")

            # Check dependencies
            dependencies = step.get("depends_on", [])
            if dependencies:
                missing_deps = [
                    dep for dep in dependencies if dep not in completed_steps
                ]
                if missing_deps:
                    console.print(
                        f"[red]Step '{step_name}' has unmet dependencies: {missing_deps}[/red]"
                    )
                    failed_steps.add(step_name)
                    continue

            # Run step
            success = self._run_step(step)

            if success:
                completed_steps.add(step_name)
                console.print(f"[green]✓ Step '{step_name}' completed[/green]")
            else:
                failed_steps.add(step_name)
                console.print(f"[red]✗ Step '{step_name}' failed[/red]")

                # Check if we should continue on failure
                if not step.get("continue_on_failure", False):
                    console.print("[red]Stopping execution due to step failure[/red]")
                    break

        # Save results
        self.recorder.save_results(self.output_dir)

        return len(failed_steps) == 0

    def _run_step(self, step: Dict[str, Any]) -> bool:
        """Run a single step"""
        step_name = step.get("name", "unknown")
        description = step.get("description", step_name)
        commands = step.get("commands", [])

        console.print(f"\n[bold blue]Running step: {step_name}[/bold blue]")
        if description != step_name:
            console.print(f"[dim]{description}[/dim]")

        if not commands:
            console.print("[yellow]No commands configured for this step[/yellow]")
            return True

        step_success = True
        step_results = []

        for i, command_config in enumerate(commands):
            command_success = self._run_command(command_config, step_name, i)
            step_results.append(command_success)

            if not command_success:
                step_success = False
                # Check if we should continue on command failure
                if not command_config.get("continue_on_failure", False):
                    break

        # Parse step results if parser is configured
        parser_name = step.get("parser")
        if parser_name and parser_name in self.parsers:
            try:
                parsed_results = self.parsers[parser_name].parse_step_results(
                    step_results
                )
                self.recorder.add_step_results(step_name, parsed_results)
            except Exception as e:
                console.print(f"[red]Error parsing step results: {e}[/red]")

        return step_success

    def _run_command(
        self, command_config: Dict[str, Any], step_name: str, command_index: int
    ) -> bool:
        """Run a single command"""
        command = command_config.get("command", "")
        cwd = command_config.get("cwd", self.working_dir)
        timeout = command_config.get(
            "timeout", self.config.get("global", {}).get("timeout", 3600)
        )
        expected_exit_code = command_config.get("expected_exit_code", 0)

        # Handle repository-specific working directory
        repo_name = command_config.get("repository")
        if repo_name:
            if repo_name in self.repo_paths:
                cwd = self.repo_paths[repo_name]
                console.print(f"[blue]Using repository: {repo_name} at {cwd}[/blue]")
            else:
                console.print(f"[red]Repository '{repo_name}' not found[/red]")
                return False

        if not command:
            console.print("[yellow]Empty command, skipping[/yellow]")
            return True

        # Prepare environment
        env = os.environ.copy()
        global_env = self.config.get("global", {}).get("environment", {})
        env.update(global_env)

        # Add command-specific environment variables
        command_env = command_config.get("environment", {})
        env.update(command_env)

        console.print(f"[dim]Executing: {command}[/dim]")
        if cwd != self.working_dir:
            console.print(f"[dim]Working directory: {cwd}[/dim]")

        start_time = time.time()

        try:
            # Run command with progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Running command {command_index + 1}...", total=None
                )

                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                progress.update(task, description="Command completed")

        except subprocess.TimeoutExpired:
            console.print(f"[red]Command timed out after {timeout} seconds[/red]")
            self.recorder.add_command(
                command=command,
                cwd=str(cwd),
                env_vars=env,
                success=False,
                duration=timeout,
                error="Command timed out",
            )
            return False

        except Exception as e:
            console.print(f"[red]Error running command: {e}[/red]")
            self.recorder.add_command(
                command=command,
                cwd=str(cwd),
                env_vars=env,
                success=False,
                duration=time.time() - start_time,
                error=str(e),
            )
            return False

        duration = time.time() - start_time
        success = result.returncode == expected_exit_code

        # Record command execution
        self.recorder.add_command(
            command=command,
            cwd=str(cwd),
            env_vars=env,
            output=result.stdout,
            error=result.stderr,
            success=success,
            duration=duration,
        )

        # Display results
        if success:
            console.print(
                f"[green]✓ Command completed successfully ({duration:.2f}s)[/green]"
            )
        else:
            console.print(
                f"[red]✗ Command failed with exit code {result.returncode} ({duration:.2f}s)[/red]"
            )
            if result.stderr:
                console.print(f"[red]Error output:[/red]\n{result.stderr}")

        if self.verbose and result.stdout:
            console.print(f"[dim]Output:[/dim]\n{result.stdout}")

        return success
