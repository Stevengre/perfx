"""
Tests for executor functionality
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from perfx.core.executor import EvaluationExecutor
from perfx.core.recorder import EvaluationRecorder


class TestEvaluationExecutor:
    """Test cases for EvaluationExecutor"""

    def test_init(self, sample_config, temp_dir):
        """Test executor initialization"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        assert executor.config == sample_config
        assert executor.recorder is not None
        assert executor.parser_factory is not None
        assert executor.output_dir == Path(output_dir)

    def test_run_single_step(self, sample_config, temp_dir):
        """Test running a single step"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            success = executor.run()

            assert success is True
            assert len(executor.recorder.results["commands"]) == 1
            assert executor.recorder.results["commands"][0]["command"] == "echo 'Hello, World!'"

    def test_run_specific_steps(self, sample_config, temp_dir):
        """Test running specific steps"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            success = executor.run(steps_to_run=["test_step"])

        assert success is True
        assert len(executor.recorder.results["commands"]) == 1

    def test_run_disabled_step(self, sample_config, temp_dir):
        """Test running with disabled step"""
        sample_config["steps"][0]["enabled"] = False
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        success = executor.run()

        assert success is True
        assert len(executor.recorder.results["commands"]) == 0  # No commands executed

    def test_run_command_timeout(self, sample_config, temp_dir):
        """Test command timeout"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = TimeoutError("Command timed out")

            success = executor.run()

            assert success is False
            assert len(executor.recorder.results["commands"]) == 1
            assert executor.recorder.results["commands"][0]["success"] is False

    def test_run_command_failure(self, sample_config, temp_dir):
        """Test command failure"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="Command failed"
            )

            success = executor.run()

            assert success is False
            assert len(executor.recorder.results["commands"]) == 1
            assert executor.recorder.results["commands"][0]["success"] is False

    def test_run_with_environment(self, sample_config, temp_dir):
        """Test running with environment variables"""
        sample_config["global"]["environment"] = {"TEST_VAR": "test_value"}
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            success = executor.run()

            assert success is True
            # Verify environment was passed to subprocess
            mock_run.assert_called()
            call_args = mock_run.call_args
            assert "env" in call_args[1]
            assert call_args[1]["env"]["TEST_VAR"] == "test_value"

    def test_run_with_working_directory(self, sample_config, temp_dir):
        """Test running with custom working directory"""
        sample_config["steps"][0]["commands"][0]["cwd"] = "/tmp"
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            success = executor.run()

            assert success is True
            # Verify working directory was passed to subprocess
            mock_run.assert_called()
            call_args = mock_run.call_args
            assert call_args[1]["cwd"] == "/tmp"

    def test_run_with_parser(self, sample_config, temp_dir):
        """Test running with parser"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Hello, World!\nTest completed successfully",
                stderr="",
            )

            success = executor.run()

            assert success is True
            assert len(executor.recorder.results["steps"]) == 1
            step_result = executor.recorder.results["steps"]["test_step"]
            assert "results" in step_result
            assert step_result["results"]["success"] is True

    def test_run_multiple_steps(self, sample_config, temp_dir):
        """Test running multiple steps"""
        # Add another step
        sample_config["steps"].append(
            {
                "name": "test_step2",
                "description": "Another test step",
                "enabled": True,
                "commands": [
                    {
                        "command": "echo 'Step 2'",
                        "cwd": ".",
                        "timeout": 30,
                        "expected_exit_code": 0,
                    }
                ],
                "parser": "simple_parser",
            }
        )

        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(sample_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            success = executor.run()

            assert success is True
            assert len(executor.recorder.results["commands"]) == 2
            assert len(executor.recorder.results["steps"]) == 2
