#!/usr/bin/env python3
"""
Report generator for Perfx
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ReportGenerator:
    """Generator for creating evaluation reports"""

    def generate_report(
        self,
        data: Dict[str, Any],
        template: str,
        output_file: Path,
        format: str = "html",
    ) -> None:
        """Generate a report in the specified format"""
        try:
            if format == "html":
                self._generate_html_report(data, template, output_file)
            elif format == "markdown":
                self._generate_markdown_report(data, template, output_file)
            elif format == "text":
                self._generate_text_report(data, template, output_file)
            else:
                print(f"Unknown report format: {format}")

        except Exception as e:
            print(f"Error generating report: {e}")

    def _generate_html_report(
        self, data: Dict[str, Any], template: str, output_file: Path
    ) -> None:
        """Generate an HTML report"""
        config = data.get("config", {})
        results = data.get("results", {})

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfx Evaluation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
        .warning {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .chart {{ margin: 20px 0; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Perfx Evaluation Report</h1>
        <p><strong>Evaluation:</strong> {config.get('name', 'Unknown')}</p>
        <p><strong>Description:</strong> {config.get('description', 'No description')}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <p><strong>Total Commands:</strong> {len(results.get('commands', []))}</p>
        <p><strong>Steps Completed:</strong> {len(results.get('steps', {}))}</p>
        <p><strong>Timestamp:</strong> {results.get('timestamp', 'Unknown')}</p>
    </div>
    
    <div class="section">
        <h2>Steps</h2>
        <table>
            <tr>
                <th>Step Name</th>
                <th>Status</th>
                <th>Timestamp</th>
            </tr>
"""

        for step_name, step_data in results.get("steps", {}).items():
            status = (
                "✓ Success"
                if step_data.get("results", {}).get("success", False)
                else "✗ Failed"
            )
            status_class = (
                "success"
                if step_data.get("results", {}).get("success", False)
                else "error"
            )
            timestamp = step_data.get("timestamp", "Unknown")

            html_content += f"""
            <tr>
                <td>{step_name}</td>
                <td class="{status_class}">{status}</td>
                <td>{timestamp}</td>
            </tr>
"""

        html_content += """
        </table>
    </div>
    
    <div class="section">
        <h2>Commands</h2>
        <table>
            <tr>
                <th>Command</th>
                <th>Duration</th>
                <th>Status</th>
            </tr>
"""

        for cmd in results.get("commands", []):
            command = cmd.get("command", "Unknown")
            duration = (
                f"{cmd.get('duration', 0):.2f}s" if cmd.get("duration") else "N/A"
            )
            status = "✓ Success" if cmd.get("success", False) else "✗ Failed"
            status_class = "success" if cmd.get("success", False) else "error"

            html_content += f"""
            <tr>
                <td>{command}</td>
                <td>{duration}</td>
                <td class="{status_class}">{status}</td>
            </tr>
"""

        html_content += """
        </table>
    </div>
</body>
</html>
"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_markdown_report(
        self, data: Dict[str, Any], template: str, output_file: Path
    ) -> None:
        """Generate a Markdown report"""
        config = data.get("config", {})
        results = data.get("results", {})

        markdown_content = f"""# Perfx Evaluation Report

## Overview
- **Evaluation:** {config.get('name', 'Unknown')}
- **Description:** {config.get('description', 'No description')}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Commands:** {len(results.get('commands', []))}
- **Steps Completed:** {len(results.get('steps', {}))}
- **Timestamp:** {results.get('timestamp', 'Unknown')}

## Steps

| Step Name | Status | Timestamp |
|-----------|--------|-----------|
"""

        for step_name, step_data in results.get("steps", {}).items():
            status = (
                "✓ Success"
                if step_data.get("results", {}).get("success", False)
                else "✗ Failed"
            )
            timestamp = step_data.get("timestamp", "Unknown")
            markdown_content += f"| {step_name} | {status} | {timestamp} |\n"

        markdown_content += """
## Commands

| Command | Duration | Status |
|---------|----------|--------|
"""

        for cmd in results.get("commands", []):
            command = cmd.get("command", "Unknown")
            duration = (
                f"{cmd.get('duration', 0):.2f}s" if cmd.get("duration") else "N/A"
            )
            status = "✓ Success" if cmd.get("success", False) else "✗ Failed"
            markdown_content += f"| {command} | {duration} | {status} |\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    def _generate_text_report(
        self, data: Dict[str, Any], template: str, output_file: Path
    ) -> None:
        """Generate a plain text report"""
        config = data.get("config", {})
        results = data.get("results", {})

        text_content = f"""PERFX EVALUATION REPORT
{'=' * 50}

OVERVIEW
--------
Evaluation: {config.get('name', 'Unknown')}
Description: {config.get('description', 'No description')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
-------
Total Commands: {len(results.get('commands', []))}
Steps Completed: {len(results.get('steps', {}))}
Timestamp: {results.get('timestamp', 'Unknown')}

STEPS
-----
"""

        for step_name, step_data in results.get("steps", {}).items():
            status = (
                "SUCCESS"
                if step_data.get("results", {}).get("success", False)
                else "FAILED"
            )
            timestamp = step_data.get("timestamp", "Unknown")
            text_content += f"{step_name}: {status} ({timestamp})\n"

        text_content += """
COMMANDS
--------
"""

        for cmd in results.get("commands", []):
            command = cmd.get("command", "Unknown")
            duration = (
                f"{cmd.get('duration', 0):.2f}s" if cmd.get("duration") else "N/A"
            )
            status = "SUCCESS" if cmd.get("success", False) else "FAILED"
            text_content += f"{command}: {duration} ({status})\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text_content)
