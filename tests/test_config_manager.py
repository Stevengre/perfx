"""
Tests for config manager functionality
"""

from pathlib import Path

import pytest
import yaml

from perfx.config.manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager"""

    def test_create_basic_template(self):
        """Test creating a basic template"""
        manager = ConfigManager()
        template = manager.create_basic_template()

        assert template["name"] == "Basic Evaluation"
        assert template["version"] == "1.0.0"
        assert "steps" in template
        assert "parsers" in template
        assert "visualizations" in template
        assert "reporting" in template

    def test_load_config(self, sample_config_file):
        """Test loading a configuration file"""
        manager = ConfigManager()
        config = manager.load_config(str(sample_config_file))

        assert config["name"] == "Test Evaluation"
        assert config["version"] == "1.0.0"
        assert len(config["steps"]) == 1
        assert config["steps"][0]["name"] == "test_step"

    def test_save_config(self, temp_dir):
        """Test saving a configuration file"""
        manager = ConfigManager()
        config = manager.create_basic_template()
        output_file = temp_dir / "saved_config.yaml"

        manager.save_config(config, str(output_file))

        assert output_file.exists()

        # Verify the saved config can be loaded
        loaded_config = manager.load_config(str(output_file))
        assert loaded_config["name"] == config["name"]

    def test_validate_config_valid(self, sample_config):
        """Test validation of a valid configuration"""
        manager = ConfigManager()
        errors = manager.validate_config(sample_config)

        assert len(errors) == 0

    def test_validate_config_invalid(self):
        """Test validation of an invalid configuration"""
        manager = ConfigManager()
        invalid_config = {
            "name": "Test",
            # Missing required fields
        }

        errors = manager.validate_config(invalid_config)

        assert len(errors) > 0
        assert any("steps" in error for error in errors)  # steps is required

    def test_substitute_env_vars(self):
        """Test environment variable substitution"""
        manager = ConfigManager()

        # Set test environment variable
        import os

        os.environ["TEST_VAR"] = "test_value"

        data = {"command": "echo ${TEST_VAR}", "nested": {"value": "${TEST_VAR}"}}

        result = manager._substitute_env_vars(data)

        assert result["command"] == "echo test_value"
        assert result["nested"]["value"] == "test_value"

    def test_load_nonexistent_file(self):
        """Test loading a non-existent configuration file"""
        manager = ConfigManager()

        with pytest.raises(FileNotFoundError):
            manager.load_config("nonexistent.yaml")

    def test_load_invalid_yaml(self, temp_dir):
        """Test loading an invalid YAML file"""
        manager = ConfigManager()
        invalid_file = temp_dir / "invalid.yaml"

        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(Exception):
            manager.load_config(str(invalid_file))
