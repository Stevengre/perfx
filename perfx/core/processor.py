#!/usr/bin/env python3
"""
Data processor for handling evaluation results and generating reports
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from ..visualizers.charts import ChartGenerator
from ..visualizers.reports import ReportGenerator
from ..visualizers.tables import TableGenerator
from .recorder import EvaluationRecorder

console = Console()


class DataProcessor:
    """Processor for handling evaluation data and generating visualizations"""

    def __init__(self, config: Dict[str, Any], output_dir: Optional[str] = None):
        self.config = config
        self.recorder = EvaluationRecorder()

        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(
                config.get("global", {}).get("output_directory", "results")
            )

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize generators
        self.chart_generator = ChartGenerator()
        self.table_generator = TableGenerator()
        self.report_generator = ReportGenerator()

    def process_all_data(self) -> None:
        """Process all evaluation data and generate outputs"""
        console.print("[blue]Processing evaluation data...[/blue]")

        # Load results if they exist
        results_file = self.output_dir / "evaluation_results.json"
        if results_file.exists():
            with open(results_file, "r", encoding="utf-8") as f:
                self.recorder.results = json.load(f)

        # Process step results
        self._process_step_results()

        # Generate visualizations
        self._generate_visualizations()

        # Generate reports
        self._generate_reports()

        console.print("[green]✓ Data processing completed![/green]")

    def _process_step_results(self) -> None:
        """Process results from all steps"""
        step_results = self.recorder.get_all_step_results()

        for step_name, step_data in step_results.items():
            console.print(f"[dim]Processing step: {step_name}[/dim]")

            # Process step-specific data
            results = step_data.get("results", {})

            # Store processed data
            self.recorder.add_metadata(f"{step_name}_processed", results)

    def _generate_visualizations(self) -> None:
        """Generate visualizations based on configuration"""
        visualizations = self.config.get("visualizations", [])

        if not visualizations:
            console.print("[yellow]No visualizations configured[/yellow]")
            return

        console.print("[blue]Generating visualizations...[/blue]")

        for viz_config in visualizations:
            viz_name = viz_config.get("name", "unknown")
            viz_type = viz_config.get("type", "unknown")

            console.print(f"[dim]Generating {viz_type}: {viz_name}[/dim]")

            try:
                if viz_type == "line_chart":
                    self._generate_line_chart(viz_config)
                elif viz_type == "bar_chart":
                    self._generate_bar_chart(viz_config)
                elif viz_type == "scatter_plot":
                    self._generate_scatter_plot(viz_config)
                elif viz_type == "table":
                    self._generate_table(viz_config)
                else:
                    console.print(
                        f"[yellow]Unknown visualization type: {viz_type}[/yellow]"
                    )

            except Exception as e:
                console.print(f"[red]Error generating {viz_name}: {e}[/red]")

    def _generate_line_chart(self, config: Dict[str, Any]) -> None:
        """Generate line chart"""
        data_source = config.get("data_source")
        x_axis = config.get("x_axis")
        y_axis = config.get("y_axis")
        title = config.get("title", "Line Chart")

        # Get data from source
        data = self._get_visualization_data(data_source)

        if data:
            output_formats = config.get("output_formats", ["png"])
            for fmt in output_formats:
                output_file = self.output_dir / f"{config['name']}.{fmt}"
                self.chart_generator.create_line_chart(
                    data, x_axis, y_axis, title, output_file
                )

    def _generate_bar_chart(self, config: Dict[str, Any]) -> None:
        """Generate bar chart"""
        data_source = config.get("data_source")
        x_axis = config.get("x_axis")
        y_axis = config.get("y_axis")
        title = config.get("title", "Bar Chart")

        # Get data from source
        data = self._get_visualization_data(data_source)

        if data:
            output_formats = config.get("output_formats", ["png"])
            for fmt in output_formats:
                output_file = self.output_dir / f"{config['name']}.{fmt}"
                self.chart_generator.create_bar_chart(
                    data, x_axis, y_axis, title, output_file
                )

    def _generate_scatter_plot(self, config: Dict[str, Any]) -> None:
        """Generate scatter plot"""
        data_source = config.get("data_source")
        x_axis = config.get("x_axis")
        y_axis = config.get("y_axis")
        title = config.get("title", "Scatter Plot")

        # Get data from source
        data = self._get_visualization_data(data_source)

        if data:
            output_formats = config.get("output_formats", ["png"])
            for fmt in output_formats:
                output_file = self.output_dir / f"{config['name']}.{fmt}"
                self.chart_generator.create_scatter_plot(
                    data, x_axis, y_axis, title, output_file
                )

    def _generate_table(self, config: Dict[str, Any]) -> None:
        """Generate table"""
        data_source = config.get("data_source")
        columns = config.get("columns", [])

        # Get data from source
        data = self._get_visualization_data(data_source)

        if data:
            output_formats = config.get("output_formats", ["markdown"])
            for fmt in output_formats:
                output_file = self.output_dir / f"{config['name']}.{fmt}"
                self.table_generator.create_table(data, columns, output_file, fmt)

    def _get_visualization_data(self, data_source: str) -> Optional[Dict[str, Any]]:
        """Get data for visualization from specified source"""
        if data_source == "all":
            # Return all step results
            return self.recorder.get_all_step_results()
        elif data_source in self.recorder.get_all_step_results():
            # Return specific step results
            return self.recorder.get_step_results(data_source)
        else:
            console.print(f"[yellow]Data source '{data_source}' not found[/yellow]")
            return None

    def _generate_reports(self) -> None:
        """Generate reports based on configuration"""
        reporting_config = self.config.get("reporting", {})

        if not reporting_config:
            console.print("[yellow]No reporting configuration found[/yellow]")
            return

        console.print("[blue]Generating reports...[/blue]")

        template = reporting_config.get("template", "basic")
        output_formats = reporting_config.get("output_formats", ["html"])
        include_charts = reporting_config.get("include_charts", True)
        include_tables = reporting_config.get("include_tables", True)
        include_raw_data = reporting_config.get("include_raw_data", False)

        # Get all data for report
        report_data = {
            "config": self.config,
            "results": self.recorder.results,
            "include_charts": include_charts,
            "include_tables": include_tables,
            "include_raw_data": include_raw_data,
        }

        for fmt in output_formats:
            output_file = self.output_dir / f"report.{fmt}"
            self.report_generator.generate_report(
                report_data, template, output_file, fmt
            )

    def generate_report(self) -> None:
        """Generate report only (without processing data)"""
        self._generate_reports()
