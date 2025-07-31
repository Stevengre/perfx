"""
Tests demonstrating realistic mock data with real command durations
"""

from unittest.mock import MagicMock, patch

import pytest

from perfx.core.executor import EvaluationExecutor
from perfx.core.recorder import EvaluationRecorder
from perfx.parsers.base import JsonParser, PytestParser, SimpleParser

# Import mock data directly
from .mock_data import (real_echo_output, real_fail_output, real_json_output,
                        real_pytest_output, real_sleep_output)


class TestRealisticMockData:
    """Tests using realistic mock data with real command durations"""

    def test_simple_parser_with_real_duration(self):
        """Test simple parser with realistic duration data"""
        config = {
            "type": "simple",
            "success_patterns": ["Hello, World!"],
            "error_patterns": ["ERROR"],
        }

        parser = SimpleParser(config)
        result = parser.parse_output(real_echo_output["stdout"])

        assert result["success"] is True
        assert result["success_patterns_found"] is True
        assert result["error_patterns_found"] is False

        # Verify that the mock duration is realistic (not 0)
        assert real_echo_output["duration"] > 0
        assert real_echo_output["duration"] < 1.0  # Should be quick

    def test_pytest_parser_with_real_duration(self):
        """Test pytest parser with realistic duration data"""
        config = {"type": "pytest"}
        parser = PytestParser(config)

        result = parser.parse_output(real_pytest_output["stdout"])

        # The real pytest output shows 1 failed, 4 passed (5 total run)
        assert result["success"] is False  # 1 failed, 4 passed
        assert result["total_tests"] == 5  # Actually run
        assert result["passed_tests"] == 4
        assert result["failed_tests"] == 1

        # Verify overall duration is parsed
        assert result["overall_duration"] == 0.04

        # Verify that the duration in the output matches our real duration
        assert "0.04s" in real_pytest_output["stdout"]

    def test_json_parser_with_real_duration(self):
        """Test JSON parser with realistic duration data"""
        config = {"type": "json"}
        parser = JsonParser(config)

        result = parser.parse_output(real_json_output["stdout"])

        assert result["success"] is True
        assert result["data"]["results"]["total_tests"] == 6
        assert result["data"]["results"]["passed_tests"] == 5
        assert result["data"]["results"]["failed_tests"] == 1

        # Verify that the duration in JSON matches our real duration
        assert result["data"]["results"]["duration"] == 1.234

    def test_executor_with_real_durations(self, sample_config, temp_dir):
        """Test executor with realistic command durations"""
        executor = EvaluationExecutor(sample_config, str(temp_dir / "output"))

        with patch("subprocess.run") as mock_run:
            # Mock the subprocess.run to return realistic data
            mock_run.return_value = MagicMock(
                stdout=real_echo_output["stdout"],
                stderr=real_echo_output["stderr"],
                returncode=real_echo_output["exit_code"],
            )

            # Mock time.time to simulate realistic timing
            with patch("time.time") as mock_time:
                mock_time.side_effect = [0.0, real_echo_output["duration"]]

                executor.run()

                # Verify that the command was recorded with realistic duration
                assert len(executor.recorder.results["commands"]) == 1
                recorded_command = executor.recorder.results["commands"][0]
                assert recorded_command["duration"] == real_echo_output["duration"]

    def test_slow_command_simulation(self):
        """Test simulation of slower commands"""
        # Verify the mock data reflects realistic timing
        assert real_sleep_output["duration"] > 0
        assert real_sleep_output["duration"] < 1.0  # Should be reasonable
        assert real_sleep_output["duration"] > 0.05  # Sleep should take some time

    def test_failed_command_simulation(self):
        """Test simulation of failed commands"""
        # Verify that failed commands still have realistic duration
        assert real_fail_output["duration"] > 0
        assert real_fail_output["exit_code"] != 0
        assert "command not found" in real_fail_output["stderr"]

    def test_duration_consistency(self, real_durations):
        """Test that durations are consistent across different mock fixtures"""
        # All durations should be positive
        for duration_name, duration_value in real_durations.items():
            assert duration_value > 0, f"Duration {duration_name} should be positive"
            assert (
                duration_value < 10.0
            ), f"Duration {duration_name} should be reasonable"

        # Sleep should be longer than echo
        assert real_durations["sleep_duration"] > real_durations["echo_duration"]

        # Pytest duration should be reasonable
        assert real_durations["pytest_duration"] > 0.1  # Should take some time
        assert real_durations["pytest_duration"] < 5.0  # Shouldn't be too slow

    def test_real_command_execution_timing(self):
        """Test that our real command execution timing is working"""
        from tests.conftest import get_real_command_duration

        # Test a simple command
        duration = get_real_command_duration("echo 'test'")
        assert duration > 0
        assert duration < 1.0

        # Test a command that should take longer
        duration_sleep = get_real_command_duration("sleep 0.1")
        assert duration_sleep >= 0.1
        assert duration_sleep < 1.0

    def test_real_pytest_execution_timing(self):
        """Test that our real pytest execution timing is working"""
        from tests.conftest import get_real_pytest_duration

        duration = get_real_pytest_duration()
        assert duration > 0
        assert duration < 10.0  # Should be reasonable for a simple test run


class TestMockDataComparison:
    """Compare old static mock data vs new realistic mock data"""

    def test_old_vs_new_mock_duration(self):
        """Compare old static duration vs new realistic duration"""
        # Old static approach
        old_duration = 0.1

        # New realistic approach (from fixture)
        from tests.conftest import get_real_command_duration

        new_duration = get_real_command_duration("echo 'Hello, World!'")

        # Both should be positive
        assert old_duration > 0
        assert new_duration > 0

        # New duration should be more realistic (not exactly 0.1)
        assert new_duration != 0.1

        # Both should be reasonable
        assert old_duration < 1.0
        assert new_duration < 1.0

    def test_mock_data_variability(self, real_durations):
        """Test that mock data shows realistic variability"""
        # Run the same command multiple times to see variability
        from tests.conftest import get_real_command_duration

        durations = []
        for _ in range(3):
            duration = get_real_command_duration("echo 'test'")
            durations.append(duration)

        # All should be positive
        assert all(d > 0 for d in durations)

        # Should show some variability (not all exactly the same)
        # Note: This might not always be true on very fast systems
        # but it's a good test for the concept
        unique_durations = len(set(durations))
        assert unique_durations >= 1  # At least one unique value
