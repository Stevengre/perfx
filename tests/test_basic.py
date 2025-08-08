"""
Basic tests for core functionality
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from perfx.config.manager import ConfigManager
from perfx.parsers.base import (JsonParser, ParserFactory, SimpleParser)
from perfx.parsers.pytest import PytestParser

from .mock_data import real_pytest_output


class TestBasicFunctionality:
    """Basic functionality tests"""

    def test_config_manager_basic(self):
        """Test basic config manager functionality"""
        manager = ConfigManager()
        template = manager.create_basic_template()

        assert template["name"] == "Basic Evaluation"
        assert template["version"] == "1.0.0"
        assert "steps" in template
        assert "parsers" in template

    def test_simple_parser(self):
        """Test simple parser"""
        config = {
            "type": "simple",
            "success_patterns": ["Hello, World!"],
            "error_patterns": ["ERROR"],
        }

        parser = SimpleParser(config)
        result = parser.parse("Hello, World!\nTest completed", "", 0)

        assert result["success"] is True
        assert result["success_patterns_found"] is True
        assert result["error_patterns_found"] is False

    def test_pytest_parser(self):
        """Test pytest parser with real output"""
        config = {"type": "pytest"}
        parser = PytestParser(config)

        # Use real pytest output
        result = parser.parse(real_pytest_output["stdout"], "", 1)  # exit_code=1 because there are failed tests

        assert result["success"] is False  # There are failed tests
        assert result["total_tests"] == 8  # Actual number of parsed tests
        assert result["passed_tests"] == 7  # Actual number of passed tests
        assert result["failed_tests"] == 1  # Actual number of failed tests
        assert result["skipped_tests"] == 0
        assert "total_duration" in result

        # Verify duration information
        assert len(result["test_results"]) == 8
        for test_result in result["test_results"]:
            assert "duration" in test_result
            assert test_result["duration"] is not None

        # Verify specific test durations
        test_durations = {r["test_id"]: r["duration"] for r in result["test_results"]}
        assert test_durations["test_slow"] >= 0.1  # Slow test (may have slight variations)
        assert test_durations["test_medium"] >= 0.05  # Medium speed test (may have slight variations)
        assert test_durations["test_simple"] >= 0.0  # Fast test (may have slight variations)

    def test_json_parser(self):
        """Test JSON parser"""
        config = {"type": "json"}
        parser = JsonParser(config)

        json_data = '{"test": "data", "value": 42}'
        result = parser.parse(json_data, "", 0)

        assert result["success"] is True
        assert result["data"]["test"] == "data"
        assert result["data"]["value"] == 42

    def test_parser_factory(self):
        """Test parser factory"""
        factory = ParserFactory()

        # Test simple parser
        simple_config = {"type": "simple"}
        simple_parser = factory.create_parser(simple_config)
        assert isinstance(simple_parser, SimpleParser)

        # Test pytest parser
        pytest_config = {"type": "pytest"}
        pytest_parser = factory.create_parser(pytest_config)
        assert isinstance(pytest_parser, PytestParser)

        # Test JSON parser
        json_config = {"type": "json"}
        json_parser = factory.create_parser(json_config)
        assert isinstance(json_parser, JsonParser)

        # Test unknown parser
        with pytest.raises(ValueError):
            factory.create_parser({"type": "unknown"})

    def test_config_validation(self):
        """Test config validation"""
        manager = ConfigManager()

        # Valid config
        valid_config = {
            "name": "Test",
            "version": "1.0.0",
            "description": "Test config",
            "global": {},
            "steps": [],
            "parsers": {},
            "visualizations": [],
            "reporting": {},
        }

        errors = manager.validate_config(valid_config)
        assert len(errors) == 0

        # Invalid config
        invalid_config = {
            "name": "Test"
            # Missing required fields
        }

        errors = manager.validate_config(invalid_config)
        assert len(errors) > 0

    def test_config_save_load(self, temp_dir):
        """Test config save and load"""
        manager = ConfigManager()
        config = manager.create_basic_template()

        # Save config
        config_file = temp_dir / "test_config.yaml"
        manager.save_config(config, str(config_file))

        assert config_file.exists()

        # Load config
        loaded_config = manager.load_config(str(config_file))

        assert loaded_config["name"] == config["name"]
        assert loaded_config["version"] == config["version"]

    def test_environment_substitution(self):
        """Test environment variable substitution"""
        import os

        manager = ConfigManager()

        # Set test environment variable
        os.environ["TEST_VAR"] = "test_value"

        data = {"command": "echo ${TEST_VAR}", "nested": {"value": "${TEST_VAR}"}}

        result = manager._substitute_env_vars(data)

        assert result["command"] == "echo test_value"
        assert result["nested"]["value"] == "test_value"
