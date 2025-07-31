#!/usr/bin/env python3
"""
Evaluation recorder for storing execution results
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class EvaluationRecorder:
    """Recorder for storing evaluation results and command history"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "commands": [],
            "metadata": {},
        }

    def add_command(
        self,
        command: str,
        cwd: str = None,
        env_vars: dict = None,
        output: str = None,
        error: str = None,
        success: bool = None,
        duration: float = None,
    ) -> None:
        """Record executed command"""
        command_record = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "cwd": cwd,
            "env_vars": env_vars,
            "output": output,
            "error": error,
            "success": success,
            "duration": duration,
        }
        self.results["commands"].append(command_record)

    def add_step_results(self, step_name: str, results: Dict[str, Any]) -> None:
        """Add parsed results for a step"""
        self.results["steps"][step_name] = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to results"""
        self.results["metadata"][key] = value

    def save_results(self, output_dir: Path) -> None:
        """Save all results to files"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON results
        results_file = output_dir / "evaluation_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # Save commands log
        commands_log = output_dir / "executed_commands.log"
        with open(commands_log, "w", encoding="utf-8") as f:
            f.write("EXECUTED COMMANDS LOG\n")
            f.write("=" * 50 + "\n\n")

            for i, cmd_info in enumerate(self.results["commands"], 1):
                f.write(f"Command #{i}\n")
                f.write("-" * 20 + "\n")
                f.write(f"Timestamp: {cmd_info['timestamp']}\n")
                f.write(f"Command: {cmd_info['command']}\n")
                if cmd_info["cwd"]:
                    f.write(f"Working Directory: {cmd_info['cwd']}\n")
                if cmd_info["duration"] is not None:
                    f.write(f"Duration: {cmd_info['duration']:.2f}s\n")
                f.write(f"Success: {cmd_info['success']}\n")
                if cmd_info["output"]:
                    f.write(f"Output:\n{cmd_info['output']}\n")
                if cmd_info["error"]:
                    f.write(f"Error:\n{cmd_info['error']}\n")
                f.write("\n" + "=" * 50 + "\n\n")

        # Save summary
        summary_file = output_dir / "summary.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("EVALUATION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Timestamp: {self.results['timestamp']}\n")
            f.write(f"Total Commands: {len(self.results['commands'])}\n")

            successful_commands = sum(
                1 for cmd in self.results["commands"] if cmd.get("success", False)
            )
            f.write(f"Successful Commands: {successful_commands}\n")
            f.write(
                f"Failed Commands: {len(self.results['commands']) - successful_commands}\n"
            )

            total_duration = sum(
                cmd.get("duration", 0) for cmd in self.results["commands"]
            )
            f.write(f"Total Duration: {total_duration:.2f}s\n")

            f.write(f"\nSteps Completed: {len(self.results['steps'])}\n")
            for step_name in self.results["steps"]:
                f.write(f"  - {step_name}\n")

    def get_command_results(self) -> List[Dict[str, Any]]:
        """Get all command results"""
        return self.results["commands"]

    def get_step_results(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific step"""
        return self.results["steps"].get(step_name)

    def get_all_step_results(self) -> Dict[str, Any]:
        """Get all step results"""
        return self.results["steps"]
