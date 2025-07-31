#!/usr/bin/env python3
"""
CLI interface for Perfx
"""

from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config.manager import ConfigManager
from .core.executor import EvaluationExecutor
from .core.processor import DataProcessor
from .core.repository_manager import RepositoryManager

console = Console()


@click.group()
@click.version_option()
def main():
    """Perfx - A configurable performance evaluation framework"""
    pass


@main.command()
@click.option("--config", "-c", required=True, help="Configuration file path")
@click.option("--steps", "-s", help="Comma-separated list of steps to run")
@click.option("--process-only", is_flag=True, help="Only process existing data")
@click.option("--generate-report", is_flag=True, help="Generate report after execution")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--output-dir", "-o", help="Output directory")
def run(
    config: str,
    steps: Optional[str],
    process_only: bool,
    generate_report: bool,
    verbose: bool,
    output_dir: Optional[str],
):
    """Run evaluation based on configuration"""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config)

        if verbose:
            console.print(f"[green]Loaded configuration: {config}[/green]")
            console.print(
                f"[blue]Evaluation name: {config_data.get('name', 'Unknown')}[/blue]"
            )

        if process_only:
            # Only process existing data
            processor = DataProcessor(config_data, output_dir)
            processor.process_all_data()
            console.print("[green]✓ Data processing completed![/green]")
            return

        # Run evaluation
        executor = EvaluationExecutor(config_data, output_dir, verbose)

        # Parse steps to run
        steps_to_run = None
        if steps:
            steps_to_run = [s.strip() for s in steps.split(",")]
            if verbose:
                console.print(f"[blue]Running steps: {', '.join(steps_to_run)}[/blue]")

        # Execute evaluation
        success = executor.run(steps_to_run)

        if success:
            console.print("[green]✓ Evaluation completed successfully![/green]")

            if generate_report:
                processor = DataProcessor(config_data, output_dir)
                # Pass the executor's recorder data to the processor
                processor.recorder = executor.recorder
                processor.generate_report()
                console.print("[green]✓ Report generated![/green]")
        else:
            console.print("[red]✗ Evaluation failed![/red]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise click.Abort()


@main.command()
def list_templates():
    """List available configuration templates"""
    # Try configs directory first, then fallback to templates directory
    configs_dir = Path.cwd() / "configs"
    templates_dir = Path(__file__).parent / "config" / "templates"

    template_dirs = []
    if configs_dir.exists():
        template_dirs.append(configs_dir)
    if templates_dir.exists():
        template_dirs.append(templates_dir)

    if not template_dirs:
        console.print("[yellow]No templates directory found[/yellow]")
        return

    table = Table(title="Available Templates")
    table.add_column("Template", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("File", style="yellow")
    table.add_column("Location", style="blue")

    # Track processed templates to avoid duplicates
    processed_templates = set()

    for template_dir in template_dirs:
        for template_file in template_dir.glob("*.yaml"):
            try:
                config_manager = ConfigManager()
                config_data = config_manager.load_config(str(template_file))
                name = config_data.get("name", template_file.stem)
                description = config_data.get("description", "No description")
                location = "configs" if template_dir == configs_dir else "templates"

                # Use template name as key to avoid duplicates
                template_key = f"{name}_{template_file.stem}"
                if template_key not in processed_templates:
                    table.add_row(name, description, template_file.name, location)
                    processed_templates.add(template_key)
            except Exception as e:
                location = "configs" if template_dir == configs_dir else "templates"
                template_key = f"{template_file.stem}_{template_file.stem}"
                if template_key not in processed_templates:
                    table.add_row(
                        template_file.stem,
                        f"Error loading: {e}",
                        template_file.name,
                        location,
                    )
                    processed_templates.add(template_key)

    console.print(table)


@main.command()
@click.option("--template", "-t", help="Template to use")
@click.option("--output", "-o", default="evaluation.yaml", help="Output file name")
def init(template: Optional[str], output: str):
    """Initialize a new evaluation configuration"""
    try:
        config_manager = ConfigManager()

        if template:
            # Try configs directory first, then fallback to templates directory
            configs_dir = Path.cwd() / "configs"
            templates_dir = Path(__file__).parent / "config" / "templates"

            template_path = None
            if configs_dir.exists():
                configs_template = configs_dir / f"{template}.yaml"
                if configs_template.exists():
                    template_path = configs_template

            if not template_path and templates_dir.exists():
                templates_template = templates_dir / f"{template}.yaml"
                if templates_template.exists():
                    template_path = templates_template

            if not template_path:
                console.print(
                    f"[red]Template '{template}' not found in configs/ or templates/[/red]"
                )
                raise click.Abort()

            config_data = config_manager.load_config(str(template_path))
        else:
            # Create basic template
            config_data = config_manager.create_basic_template()

        # Save to output file
        config_manager.save_config(config_data, output)
        console.print(f"[green]✓ Configuration created: {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@main.command()
@click.option("--config", "-c", required=True, help="Configuration file path")
def validate(config: str):
    """Validate configuration file"""
    try:
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config)

        # Validate configuration
        errors = config_manager.validate_config(config_data)

        if errors:
            console.print("[red]Configuration validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")
            raise click.Abort()
        else:
            console.print("[green]✓ Configuration is valid![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@main.command()
@click.option("--config", "-c", required=True, help="Configuration file path")
def info(config: str):
    """Show configuration information"""
    try:
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config)

        # Create info panel
        info_text = Text()
        info_text.append(
            f"Name: {config_data.get('name', 'Unknown')}\n", style="bold cyan"
        )
        info_text.append(
            f"Version: {config_data.get('version', 'Unknown')}\n", style="blue"
        )
        info_text.append(
            f"Description: {config_data.get('description', 'No description')}\n",
            style="green",
        )

        # Steps info
        steps = config_data.get("steps", [])
        info_text.append(f"\nSteps ({len(steps)}):\n", style="bold")
        for step in steps:
            enabled = "✓" if step.get("enabled", True) else "✗"
            info_text.append(
                f"  {enabled} {step.get('name', 'Unknown')}\n",
                style="green" if step.get("enabled", True) else "red",
            )

        panel = Panel(info_text, title="Configuration Info", border_style="blue")
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@main.command()
@click.option("--config", "-c", required=True, help="Configuration file path")
@click.option("--clean", is_flag=True, help="Clean existing repositories before setup")
def setup_repos(config: str, clean: bool):
    """Set up repositories from configuration"""
    try:
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config)

        repositories = config_data.get("repositories", [])
        if not repositories:
            console.print("[yellow]No repositories configured[/yellow]")
            return

        repo_manager = RepositoryManager()

        if clean:
            console.print("[yellow]Cleaning existing repositories...[/yellow]")
            repo_manager.clean_repositories()

        console.print(f"[blue]Setting up {len(repositories)} repositories...[/blue]")
        repo_paths = repo_manager.setup_repositories(repositories)

        # Show results
        table = Table(title="Repository Setup Results")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Status", style="blue")

        for name, path in repo_paths.items():
            table.add_row(name, str(path), "✅ Ready")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@main.command()
@click.option("--config", "-c", required=True, help="Configuration file path")
def list_repos(config: str):
    """List repositories from configuration"""
    try:
        config_manager = ConfigManager()
        config_data = config_manager.load_config(config)

        repositories = config_data.get("repositories", [])
        if not repositories:
            console.print("[yellow]No repositories configured[/yellow]")
            return

        table = Table(title="Configured Repositories")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="green")
        table.add_column("Branch", style="blue")
        table.add_column("Path", style="yellow")
        table.add_column("Submodules", style="magenta")

        for repo in repositories:
            table.add_row(
                repo.get("name", "N/A"),
                repo.get("url", "N/A"),
                repo.get("branch", "main"),
                repo.get("path", repo.get("name", "N/A")),
                "✅" if repo.get("submodules", True) else "❌",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@main.command()
def clean_repos():
    """Clean all downloaded repositories"""
    try:
        repo_manager = RepositoryManager()
        repo_manager.clean_repositories()
        console.print("[green]✅ All repositories cleaned[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


if __name__ == "__main__":
    main()
