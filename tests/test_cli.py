"""
Tests for CLI functionality
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from perfx.cli import main


class TestCLI:
    """Test cases for CLI functionality"""

    def test_help(self):
        """Test help command"""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output

    def test_list_templates(self):
        """Test list-templates command"""
        runner = CliRunner()

        with patch("src.perfx.cli.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/tmp")

            with patch("src.perfx.cli.Path.exists") as mock_exists:
                mock_exists.return_value = False

                result = runner.invoke(main, ["list-templates"])

                assert result.exit_code == 0
                assert "Available Templates" in result.output

    def test_init_basic(self, temp_dir):
        """Test init command with basic template"""
        runner = CliRunner()

        with patch("src.perfx.cli.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_dir

            output_file = temp_dir / "test_config.yaml"

            result = runner.invoke(main, ["init", "--output", str(output_file)])

            assert result.exit_code == 0
            assert "Configuration created" in result.output
            assert output_file.exists()

    def test_init_with_template(self, temp_dir):
        """Test init command with specific template"""
        runner = CliRunner()

        with patch("src.perfx.cli.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_dir

            # Create a mock template file
            template_file = temp_dir / "configs" / "basic.yaml"
            template_file.parent.mkdir(exist_ok=True)
            template_file.write_text("name: Test Template")

            output_file = temp_dir / "test_config.yaml"

            result = runner.invoke(
                main, ["init", "--template", "basic", "--output", str(output_file)]
            )

            assert result.exit_code == 0
            assert "Configuration created" in result.output
            assert output_file.exists()

    def test_validate_valid_config(self, sample_config_file):
        """Test validate command with valid config"""
        runner = CliRunner()

        result = runner.invoke(main, ["validate", "--config", str(sample_config_file)])

        assert result.exit_code == 0
        assert "Configuration is valid" in result.output

    def test_validate_invalid_config(self, temp_dir):
        """Test validate command with invalid config"""
        runner = CliRunner()

        # Create invalid config file
        invalid_config = temp_dir / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: content: [")

        result = runner.invoke(main, ["validate", "--config", str(invalid_config)])

        assert result.exit_code != 0
        assert "Error" in result.output

    def test_info_config(self, sample_config_file):
        """Test info command"""
        runner = CliRunner()

        result = runner.invoke(main, ["info", "--config", str(sample_config_file)])

        assert result.exit_code == 0
        assert "Test Evaluation" in result.output
        assert "1.0.0" in result.output

    def test_run_success(self, sample_config_file):
        """Test run command with success"""
        runner = CliRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            result = runner.invoke(main, ["run", "--config", str(sample_config_file)])

            assert result.exit_code == 0
            assert "Evaluation completed successfully" in result.output

    def test_run_failure(self, sample_config_file):
        """Test run command with failure"""
        runner = CliRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="Command failed"
            )

            result = runner.invoke(main, ["run", "--config", str(sample_config_file)])

            assert result.exit_code != 0
            assert "Evaluation failed" in result.output

    def test_run_with_steps(self, sample_config_file):
        """Test run command with specific steps"""
        runner = CliRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            result = runner.invoke(
                main,
                ["run", "--config", str(sample_config_file), "--steps", "test_step"],
            )

            assert result.exit_code == 0
            assert "Evaluation completed successfully" in result.output

    def test_run_with_report(self, sample_config_file, temp_dir):
        """Test run command with report generation"""
        runner = CliRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            result = runner.invoke(
                main,
                [
                    "run",
                    "--config",
                    str(sample_config_file),
                    "--generate-report",
                    "--output-dir",
                    str(temp_dir),
                ],
            )

            assert result.exit_code == 0
            assert "Evaluation completed successfully" in result.output
            assert "Report generated" in result.output

    def test_run_process_only(self, sample_config_file, temp_dir):
        """Test run command with process-only flag"""
        runner = CliRunner()

        # Create some existing results
        results_file = temp_dir / "evaluation_results.json"
        results_file.write_text('{"test": "data"}')

        result = runner.invoke(
            main,
            [
                "run",
                "--config",
                str(sample_config_file),
                "--process-only",
                "--output-dir",
                str(temp_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Processing existing data" in result.output

    def test_run_verbose(self, sample_config_file):
        """Test run command with verbose flag"""
        runner = CliRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Hello, World!\n", stderr=""
            )

            result = runner.invoke(
                main, ["run", "--config", str(sample_config_file), "--verbose"]
            )

            assert result.exit_code == 0
            assert "Evaluation completed successfully" in result.output

    def test_run_nonexistent_config(self):
        """Test run command with non-existent config"""
        runner = CliRunner()

        result = runner.invoke(main, ["run", "--config", "nonexistent.yaml"])

        assert result.exit_code != 0
        assert "Error" in result.output

    def test_run_timeout(self, sample_config_file):
        """Test run command with timeout"""
        runner = CliRunner()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = TimeoutError("Command timed out")

            result = runner.invoke(main, ["run", "--config", str(sample_config_file)])

            assert result.exit_code != 0
            assert "Evaluation failed" in result.output
