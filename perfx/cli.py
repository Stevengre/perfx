#!/usr/bin/env python3
"""
Command-line interface for perfx
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .config.manager import ConfigManager
from .core.executor import EvaluationExecutor
from .visualizers.latex_tables import generate_latex_table

console = Console()


@click.group()
@click.version_option()
def main():
    """Perfx - Performance Evaluation Framework"""
    pass


@main.command()
@click.option("--output", "-o", default="config.yaml", help="Output configuration file")
@click.option("--template", "-t", help="Template to use for initialization")
def init(output: str, template: Optional[str]):
    """Initialize a new configuration file"""
    try:
        config_manager = ConfigManager()
        
        if template:
            # Use specific template
            config_manager.create_from_template(template, output)
        else:
            # Use basic template
            config_manager.create_basic_template(output)
        
        console.print(f"[green]✓ Configuration created: {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Error creating configuration: {e}[/red]")
        sys.exit(1)


@main.command()
def list_templates():
    """List available configuration templates"""
    try:
        config_manager = ConfigManager()
        templates = config_manager.list_templates()
        
        if templates:
            table = Table(title="Available Templates")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="green")
            
            for template in templates:
                table.add_row(template["name"], template["description"])
            
            console.print(table)
        else:
            console.print("[yellow]No templates found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]✗ Error listing templates: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("config_file")
def validate(config_file: str):
    """Validate a configuration file"""
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config(config_file)
        
        # Validate configuration
        config_manager.validate_config(config)
        
        console.print("[green]✓ Configuration is valid[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Configuration validation failed: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("config_file")
def info(config_file: str):
    """Show information about a configuration file"""
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config(config_file)
        
        # Display configuration info
        table = Table(title=f"Configuration: {config_file}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Name", config.get("name", "N/A"))
        table.add_row("Version", config.get("version", "N/A"))
        table.add_row("Description", config.get("description", "N/A"))
        
        steps = config.get("steps", [])
        table.add_row("Steps", str(len(steps)))
        
        parsers = config.get("parsers", {})
        table.add_row("Parsers", str(len(parsers)))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗ Error reading configuration: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("config_file")
@click.option("--steps", "-s", help="Comma-separated list of steps to run")
@click.option("--output-dir", "-o", help="Output directory")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(config_file: str, steps: Optional[str], output_dir: Optional[str], verbose: bool):
    """Run an evaluation using a configuration file"""
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config(config_file)
        
        # Validate configuration
        config_manager.validate_config(config)
        
        # Set output directory
        if output_dir:
            config["global"]["output_directory"] = output_dir
        
        # Create executor
        executor = EvaluationExecutor(config, output_dir or config["global"].get("output_directory", "results"))
        
        # Determine steps to run
        if steps:
            step_list = [s.strip() for s in steps.split(",")]
        else:
            step_list = None
        
        # Run evaluation
        if verbose:
            console.print(f"[blue]Running evaluation with config: {config_file}[/blue]")
            if step_list:
                console.print(f"[blue]Steps: {', '.join(step_list)}[/blue]")
        
        success = executor.run(step_list)
        
        if success:
            console.print("[green]✓ Evaluation completed successfully[/green]")
        else:
            console.print("[red]✗ Evaluation failed[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]✗ Error running evaluation: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("json_file")
@click.argument("output_file")
@click.option("--type", "-t", default="opcode_summary", 
              help="Table type (opcode_summary, custom)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def latex(json_file: str, output_file: str, type: str, verbose: bool):
    """Generate LaTeX table from JSON data"""
    try:
        if verbose:
            console.print(f"[blue]Generating LaTeX table from: {json_file}[/blue]")
            console.print(f"[blue]Output: {output_file}[/blue]")
            console.print(f"[blue]Type: {type}[/blue]")
        
        success = generate_latex_table(json_file, output_file, type)
        
        if success:
            console.print("[green]✓ LaTeX table generated successfully[/green]")
        else:
            console.print("[red]✗ Failed to generate LaTeX table[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]✗ Error generating LaTeX table: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
