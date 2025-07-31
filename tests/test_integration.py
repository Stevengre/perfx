"""
Integration tests for the complete perfx workflow
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from perfx.config.manager import ConfigManager
from perfx.core.executor import EvaluationExecutor
from perfx.core.processor import DataProcessor
from perfx.core.recorder import EvaluationRecorder


class TestIntegration:
    """Integration tests for complete workflow"""

    def test_complete_workflow_success(self, temp_dir):
        """Test complete workflow from config to report"""
        # Create a test configuration
        config = {
            "name": "Integration Test",
            "version": "1.0.0",
            "description": "Integration test configuration",
            "global": {
                "working_directory": ".",
                "output_directory": str(temp_dir / "output"),
                "timeout": 60,
            },
            "steps": [
                {
                    "name": "build",
                    "description": "Build step",
                    "enabled": True,
                    "commands": [
                        {
                            "command": "echo 'Building...' && echo 'Build completed successfully'",
                            "cwd": ".",
                            "timeout": 30,
                            "expected_exit_code": 0,
                        }
                    ],
                    "parser": "build_parser",
                },
                {
                    "name": "test",
                    "description": "Test step",
                    "enabled": True,
                    "commands": [
                        {
                            "command": "echo 'test_example::test1 PASSED in 0.5s' && echo 'test_example::test2 PASSED in 1.2s'",
                            "cwd": ".",
                            "timeout": 30,
                            "expected_exit_code": 0,
                        }
                    ],
                    "parser": "pytest_parser",
                },
            ],
            "parsers": {
                "build_parser": {
                    "type": "simple",
                    "success_patterns": ["Build completed successfully"],
                    "error_patterns": ["ERROR", "FAILED"],
                },
                "pytest_parser": {"type": "pytest"},
            },
            "visualizations": [
                {
                    "name": "test_performance",
                    "type": "line_chart",
                    "data_source": "test",
                    "x_axis": "test_name",
                    "y_axis": "duration",
                    "title": "Test Performance",
                    "output_formats": ["png"],
                },
                {
                    "name": "summary_table",
                    "type": "table",
                    "data_source": "all",
                    "columns": ["step", "status", "details"],
                    "output_formats": ["markdown"],
                },
            ],
            "reporting": {
                "template": "basic",
                "output_formats": ["html", "markdown"],
                "include_charts": True,
                "include_tables": True,
            },
        }

        # Save config to file
        config_file = temp_dir / "integration_config.yaml"
        config_manager = ConfigManager()
        config_manager.save_config(config, str(config_file))

        # Create output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir(exist_ok=True)

        # Mock subprocess.run
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Build completed successfully\n", stderr=""
            )

            # Execute evaluation
            executor = EvaluationExecutor(config, str(output_dir))
            success = executor.run()

            assert success is True
            assert len(executor.recorder.results["commands"]) == 2
            assert len(executor.recorder.results["steps"]) == 2

            # Save results
            executor.recorder.save_results(Path(output_dir))

            # Check output files
            assert (output_dir / "evaluation_results.json").exists()
            assert (output_dir / "executed_commands.log").exists()
            assert (output_dir / "summary.txt").exists()

    def test_workflow_with_failure(self, temp_dir):
        """Test workflow with command failure"""
        config = {
            "name": "Failure Test",
            "version": "1.0.0",
            "description": "Test with failure",
            "global": {
                "working_directory": ".",
                "output_directory": str(temp_dir / "output"),
                "timeout": 60,
            },
            "steps": [
                {
                    "name": "failing_step",
                    "description": "Step that fails",
                    "enabled": True,
                    "commands": [
                        {
                            "command": "echo 'This will fail'",
                            "cwd": ".",
                            "timeout": 30,
                            "expected_exit_code": 0,
                        }
                    ],
                    "parser": "simple_parser",
                }
            ],
            "parsers": {
                "simple_parser": {
                    "type": "simple",
                    "success_patterns": ["success"],
                    "error_patterns": ["fail"],
                }
            },
            "visualizations": [],
            "reporting": {},
        }

        # Mock subprocess.run to simulate failure
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="This will fail\n", stderr="Error occurred"
            )

            output_dir = str(temp_dir / "output")
            executor = EvaluationExecutor(config, output_dir)
            success = executor.run()

            assert success is False
            assert len(executor.recorder.results["commands"]) == 1
            assert executor.recorder.results["commands"][0]["success"] is False

    def test_workflow_with_timeout(self, temp_dir):
        """Test workflow with command timeout"""
        config = {
            "name": "Timeout Test",
            "version": "1.0.0",
            "description": "Test with timeout",
            "global": {
                "working_directory": ".",
                "output_directory": str(temp_dir / "output"),
                "timeout": 60,
            },
            "steps": [
                {
                    "name": "timeout_step",
                    "description": "Step that times out",
                    "enabled": True,
                    "commands": [
                        {
                            "command": "sleep 10",
                            "cwd": ".",
                            "timeout": 1,  # Very short timeout
                            "expected_exit_code": 0,
                        }
                    ],
                    "parser": "simple_parser",
                }
            ],
            "parsers": {
                "simple_parser": {
                    "type": "simple",
                    "success_patterns": ["success"],
                    "error_patterns": ["fail"],
                }
            },
            "visualizations": [],
            "reporting": {},
        }

        # Mock subprocess.run to simulate timeout
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = TimeoutError("Command timed out")

            output_dir = str(temp_dir / "output")
            executor = EvaluationExecutor(config, output_dir)
            success = executor.run()

            assert success is False
            assert len(executor.recorder.results["commands"]) == 1
            assert executor.recorder.results["commands"][0]["success"] is False

    def test_workflow_with_environment_vars(self, temp_dir):
        """Test workflow with environment variables"""
        config = {
            "name": "Env Test",
            "version": "1.0.0",
            "description": "Test with environment variables",
            "global": {
                "working_directory": ".",
                "output_directory": str(temp_dir / "output"),
                "timeout": 60,
                "environment": {
                    "TEST_VAR": "test_value",
                    "ANOTHER_VAR": "another_value",
                },
            },
            "steps": [
                {
                    "name": "env_step",
                    "description": "Step with environment",
                    "enabled": True,
                    "commands": [
                        {
                            "command": "echo $TEST_VAR && echo $ANOTHER_VAR",
                            "cwd": ".",
                            "timeout": 30,
                            "expected_exit_code": 0,
                        }
                    ],
                    "parser": "simple_parser",
                }
            ],
            "parsers": {
                "simple_parser": {
                    "type": "simple",
                    "success_patterns": ["test_value", "another_value"],
                    "error_patterns": ["ERROR"],
                }
            },
            "visualizations": [],
            "reporting": {},
        }

        # Mock subprocess.run
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="test_value\nanother_value\n", stderr=""
            )

            output_dir = str(temp_dir / "output")
            executor = EvaluationExecutor(config, output_dir)
            success = executor.run()

            assert success is True
            assert len(executor.recorder.results["commands"]) == 1
            assert executor.recorder.results["commands"][0]["success"] is True

            # Verify environment was passed to subprocess
            mock_run.assert_called()
            call_args = mock_run.call_args
            assert "env" in call_args[1]
            assert call_args[1]["env"]["TEST_VAR"] == "test_value"
            assert call_args[1]["env"]["ANOTHER_VAR"] == "another_value"


