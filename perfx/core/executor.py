#!/usr/bin/env python3
"""
Evaluation executor for running configured commands
"""

import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..parsers.base import ParserFactory
from .recorder import EvaluationRecorder
from .repository_manager import RepositoryManager
from .dependency_manager import DependencyManager

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

        # Load conditions from config
        self.conditions = config.get("conditions", {})
        
        # Initialize dependency manager
        cache_file = config.get("global", {}).get("dependency_cache", "results/.dependency_cache.json")
        self.dependency_manager = DependencyManager(cache_file)

    def _evaluate_condition(self, condition_expr: str) -> bool:
        """Evaluate a condition expression"""
        try:
            # Create a safe evaluation environment
            eval_env = {
                'platform': platform,
                'os': os,
            }
            
            # Evaluate the condition
            result = eval(condition_expr, {"__builtins__": {}}, eval_env)
            return bool(result)
        except Exception as e:
            console.print(f"[red]Error evaluating condition '{condition_expr}': {e}[/red]")
            return False

    def _should_run_command(self, command_config: Dict[str, Any]) -> bool:
        """Check if a command should be run based on its condition"""
        condition = command_config.get("condition")
        if not condition:
            return True  # No condition means always run
        
        # Check if condition is defined in config
        if condition in self.conditions:
            condition_expr = self.conditions[condition]
            return self._evaluate_condition(condition_expr)
        else:
            console.print(f"[yellow]Warning: Condition '{condition}' not found in config[/yellow]")
            return True

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

        # First, check all steps to determine which ones are already completed
        # due to unchanged dependencies
        all_steps = self.config.get("steps", [])
        all_steps = [step for step in all_steps if step.get("enabled", True)]
        
        completed_steps = set()
        for step in all_steps:
            step_name = step.get("name", "unknown")
            
            # If step exists in cache, consider it completed
            if step_name in self.dependency_manager.dependency_cache:
                completed_steps.add(step_name)
                console.print(f"[dim]Step '{step_name}' already completed (found in cache)[/dim]")

        # Track dependencies for current run
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
        dependencies = step.get("dependencies", [])

        console.print(f"\n[bold blue]Running step: {step_name}[/bold blue]")
        if description != step_name:
            console.print(f"[dim]{description}[/dim]")

        # Check file dependencies
        step_skipped = False
        if dependencies:
            console.print(f"[dim]Checking dependencies for step: {step_name}[/dim]")
            dependencies_changed = self.dependency_manager.check_dependencies_changed(step_name, dependencies)
            
            if not dependencies_changed:
                console.print(f"[green]✓ Step '{step_name}' skipped - no dependencies changed[/green]")
                step_skipped = True
                # Mark dependencies as up-to-date even when skipped
                self.dependency_manager.mark_step_completed(step_name)
                return True
            else:
                console.print(f"[yellow]Dependencies changed, running step: {step_name}[/yellow]")

        if not commands:
            console.print("[yellow]No commands configured for this step[/yellow]")
            return True

        step_success = True
        step_results = []
        cleanup_commands = []

        # Separate normal commands from cleanup commands
        normal_commands = []
        for i, command_config in enumerate(commands):
            if command_config.get("cleanup", False):
                cleanup_commands.append((i, command_config))
            else:
                normal_commands.append((i, command_config))

        # Run normal commands
        for i, command_config in normal_commands:
            # Check if the command should be run
            if not self._should_run_command(command_config):
                console.print(f"[yellow]Skipping command '{command_config.get('command', 'unknown')}' due to condition[/yellow]")
                step_results.append(True)  # Indicate skipped command as successful
                continue

            command_success = self._run_command(command_config, step_name, i)
            step_results.append(command_success)

            if not command_success:
                step_success = False
                # Check if we should continue on command failure
                if not command_config.get("continue_on_failure", False):
                    break

        # Run cleanup commands in reverse order (LIFO)
        if cleanup_commands:
            console.print(f"[yellow]Running {len(cleanup_commands)} cleanup commands...[/yellow]")
            for i, command_config in reversed(cleanup_commands):
                # Check if the command should be run
                if not self._should_run_command(command_config):
                    console.print(f"[yellow]Skipping cleanup command '{command_config.get('command', 'unknown')}' due to condition[/yellow]")
                    continue

                cleanup_success = self._run_command(command_config, step_name, i)
                step_results.append(cleanup_success)
                
                # Note: Cleanup command failures don't affect step success
                if not cleanup_success:
                    console.print(f"[red]Warning: Cleanup command failed, but continuing...[/red]")

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

        # Mark dependencies as up-to-date if step was successful
        if step_success and not step_skipped:
            if dependencies:
                self.dependency_manager.mark_step_completed(step_name)
            else:
                # For steps without file dependencies, mark them as completed in cache
                self.dependency_manager.dependency_cache[step_name] = {}
                self.dependency_manager._save_cache()

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

        # Process outputs if configured
        outputs = command_config.get("outputs", [])
        if outputs:
            for output_config in outputs:
                try:
                    input_type = output_config.get("input", "stdout")
                    output_path = output_config.get("output")
                    parser_type = output_config.get("parser")
                    
                    if not output_path:
                        continue
                    
                    # Determine input content
                    if input_type == "stdout":
                        content = result.stdout
                    elif input_type == "stderr":
                        content = result.stderr
                    elif input_type == "combined":
                        content = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
                    else:
                        console.print(f"[yellow]Warning: Unknown input type '{input_type}'[/yellow]")
                        continue
                    
                    # Create output path
                    # Remove 'results/' prefix from output_path if it exists
                    if output_path.startswith('results/'):
                        output_path = output_path[8:]  # Remove 'results/' prefix
                    
                    output_file_path = Path(self.output_dir) / output_path
                    output_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Apply parser if specified
                    if parser_type:
                        try:
                            from perfx.parsers import ParserFactory
                            factory = ParserFactory()
                            
                            parser_config = {"type": parser_type}
                            parser = factory.create_parser(parser_config)
                            
                            # Parse the content
                            if input_type == "stdout":
                                parsed_result = parser.parse(result.stdout, result.stderr, result.returncode)
                            elif input_type == "stderr":
                                parsed_result = parser.parse("", result.stderr, result.returncode)
                            else:  # combined
                                parsed_result = parser.parse(result.stdout, result.stderr, result.returncode)
                            
                            # Save parsed result as JSON
                            with open(output_file_path, 'w', encoding='utf-8') as f:
                                json.dump(parsed_result, f, indent=2, ensure_ascii=False)
                            
                            console.print(f"[dim]Parsed {input_type} saved to: {output_file_path}[/dim]")
                            
                        except Exception as e:
                            console.print(f"[yellow]Warning: Parser '{parser_type}' failed: {e}[/yellow]")
                            # Fall back to saving raw content
                            with open(output_file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            console.print(f"[dim]Raw {input_type} saved to: {output_file_path}[/dim]")
                    else:
                        # Save raw content
                        with open(output_file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        console.print(f"[dim]Raw {input_type} saved to: {output_file_path}[/dim]")
                        
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to process output: {e}[/yellow]")

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
