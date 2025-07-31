from .mock_data import *

"""
Pytest configuration and fixtures for perfx tests
"""

import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import pytest


def get_real_command_duration(command: str, timeout: int = 5) -> float:
    """
    Execute a command and return its real duration.
    This provides more realistic test data.
    """
    start_time = time.time()
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        duration = time.time() - start_time
        return round(duration, 3)
    except subprocess.TimeoutExpired:
        return timeout
    except Exception:
        return 0.1  # fallback duration


def get_real_pytest_duration() -> float:
    """
    Run a simple pytest command to get realistic duration.
    """
    # Create a simple test file
    test_content = """
import pytest

def test_simple():
    assert True

def test_another():
    assert 1 + 1 == 2

def test_failing():
    assert False

def test_passing():
    assert "hello" == "hello"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_content)
        test_file = f.name

    try:
        # Run pytest with -q (quiet) to get just the summary
        start_time = time.time()
        result = subprocess.run(
            ["python", "-m", "pytest", test_file, "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        duration = time.time() - start_time
        return round(duration, 3)
    except Exception:
        return 0.5  # fallback duration
    finally:
        # Clean up
        try:
            import os

            os.unlink(test_file)
        except:
            pass


@pytest.fixture(scope="session")
def real_durations():
    """
    Get real command durations for more realistic testing.
    This fixture has session scope to avoid running commands multiple times.
    """
    return {
        "echo_duration": get_real_command_duration("echo 'Hello, World!'"),
        "pytest_duration": get_real_pytest_duration(),
        "sleep_duration": get_real_command_duration("sleep 0.1"),
    }


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing"""
    return {
        "name": "Test Evaluation",
        "version": "1.0.0",
        "description": "Test configuration",
        "metadata": {"author": "Test Author", "date": "2024-01-01"},
        "global": {
            "working_directory": ".",
            "output_directory": "test_output",
            "timeout": 60,
            "parallel": False,
        },
        "steps": [
            {
                "name": "test_step",
                "description": "A test step",
                "enabled": True,
                "commands": [
                    {
                        "command": "echo 'Hello, World!'",
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
                "success_patterns": ["Hello, World!"],
                "error_patterns": ["ERROR"],
            }
        },
        "visualizations": [],
        "reporting": {
            "template": "basic",
            "output_formats": ["markdown"],
            "include_charts": False,
            "include_tables": False,
        },
    }


@pytest.fixture
def sample_config_file(temp_dir, sample_config):
    """Create a sample config file for testing"""
    import yaml

    config_file = temp_dir / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config, f)

    return config_file


# Mock 数据现在从 tests/mock_data.py 导入
# 可以直接使用导入的变量，无需 fixture
