#!/usr/bin/env python3
"""
Configuration manager for Perfx
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console

console = Console()


class ConfigManager:
    """Configuration manager for loading, validating and saving evaluation configurations"""

    def __init__(self):
        self.config_schema = {
            "name": str,
            "version": str,
            "description": str,
            "global": dict,
            "repositories": list,  # 新增：仓库配置
            "steps": list,
            "parsers": dict,
            "visualizations": list,
            "reporting": dict,
            "conditions": dict,  # 新增：条件配置
        }

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Apply environment variable substitution
            config_data = self._substitute_env_vars(config_data)

            return config_data

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")

    def save_config(self, config_data: Dict[str, Any], output_path: str) -> None:
        """Save configuration to YAML file"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    config_data,
                    f,
                    default_flow_style=False,
                    indent=2,
                    allow_unicode=True,
                )
        except Exception as e:
            raise ValueError(f"Error saving configuration: {e}")

    def validate_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate configuration data and return list of errors"""
        errors = []

        # Check required fields
        required_fields = ["name", "steps"]
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Missing required field: {field}")

        # Validate steps
        if "steps" in config_data:
            steps = config_data["steps"]
            if not isinstance(steps, list):
                errors.append("Steps must be a list")
            else:
                for i, step in enumerate(steps):
                    step_errors = self._validate_step(step, i)
                    errors.extend(step_errors)

        # Validate repositories
        if "repositories" in config_data:
            repositories = config_data["repositories"]
            if not isinstance(repositories, list):
                errors.append("Repositories must be a list")
            else:
                for i, repo in enumerate(repositories):
                    repo_errors = self._validate_repository(repo, i)
                    errors.extend(repo_errors)

        # Validate parsers
        if "parsers" in config_data:
            parsers = config_data["parsers"]
            if not isinstance(parsers, dict):
                errors.append("Parsers must be a dictionary")
            else:
                for parser_name, parser_config in parsers.items():
                    parser_errors = self._validate_parser(parser_config, parser_name)
                    errors.extend(parser_errors)

        return errors

    def _validate_step(self, step: Dict[str, Any], index: int) -> List[str]:
        """Validate a single step configuration"""
        errors = []

        if not isinstance(step, dict):
            errors.append(f"Step {index} must be a dictionary")
            return errors

        # Check required step fields
        if "name" not in step:
            errors.append(f"Step {index} missing required field: name")

        if "commands" not in step:
            errors.append(f"Step {index} missing required field: commands")
        else:
            commands = step["commands"]
            if not isinstance(commands, list):
                errors.append(f"Step {index} commands must be a list")
            else:
                for j, command in enumerate(commands):
                    if not isinstance(command, dict):
                        errors.append(f"Step {index} command {j} must be a dictionary")
                    elif "command" not in command:
                        errors.append(
                            f"Step {index} command {j} missing required field: command"
                        )

        return errors

    def _validate_repository(self, repo: Dict[str, Any], index: int) -> List[str]:
        """Validate a single repository configuration"""
        errors = []

        if not isinstance(repo, dict):
            errors.append(f"Repository {index} must be a dictionary")
            return errors

        required_fields = ["name", "url"]
        for field in required_fields:
            if field not in repo:
                errors.append(f"Repository {index} missing required field: {field}")

        # Validate optional fields
        if "branch" in repo and not isinstance(repo["branch"], str):
            errors.append(f"Repository {index} branch must be a string")

        if "path" in repo and not isinstance(repo["path"], str):
            errors.append(f"Repository {index} path must be a string")

        if "submodules" in repo and not isinstance(repo["submodules"], bool):
            errors.append(f"Repository {index} submodules must be a boolean")

        return errors

    def _validate_parser(
        self, parser_config: Dict[str, Any], parser_name: str
    ) -> List[str]:
        """Validate a parser configuration"""
        errors = []

        if not isinstance(parser_config, dict):
            errors.append(f"Parser {parser_name} must be a dictionary")
            return errors

        if "type" not in parser_config:
            errors.append(f"Parser {parser_name} missing required field: type")

        return errors

    def _substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute environment variables in configuration data"""
        if isinstance(data, str):
            # Replace ${VAR} with environment variable value
            if "${" in data and "}" in data:
                import re

                pattern = r"\$\{([^}]+)\}"

                def replace_var(match):
                    var_name = match.group(1)
                    return os.getenv(var_name, match.group(0))

                return re.sub(pattern, replace_var, data)
            return data
        elif isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        else:
            return data

    def create_basic_template(self) -> Dict[str, Any]:
        """Create a basic configuration template"""
        return {
            "name": "Basic Evaluation",
            "version": "1.0.0",
            "description": "A basic evaluation configuration",
            "metadata": {
                "author": "Jianhong Zhao",
                "date": "2024-01-01",
                "tags": ["basic", "evaluation"],
            },
            "global": {
                "working_directory": ".",
                "output_directory": "results",
                "timeout": 3600,
                "parallel": False,
                "environment": {},
            },
            "steps": [
                {
                    "name": "example_step",
                    "description": "An example step",
                    "enabled": True,
                    "commands": [
                        {
                            "command": 'echo "Hello, World!"',
                            "cwd": ".",
                            "timeout": 60,
                            "expected_exit_code": 0,
                        }
                    ],
                    "parser": "simple_parser",
                }
            ],
            "parsers": {
                "simple_parser": {
                    "type": "simple",
                    "success_patterns": ["Hello, World!"],
                    "error_patterns": ["ERROR", "FAILED"],
                }
            },
            "visualizations": [
                {
                    "name": "example_chart",
                    "type": "line_chart",
                    "data_source": "example_step",
                    "x_axis": "test_name",
                    "y_axis": "duration",
                    "title": "Example Performance Chart",
                }
            ],
            "reporting": {
                "template": "basic",
                "output_formats": ["html", "markdown"],
                "include_charts": True,
                "include_tables": True,
                "include_raw_data": False,
            },
        }
