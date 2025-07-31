"""
Tests for condition execution functionality in perfx
"""

import platform
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from perfx.core.executor import EvaluationExecutor


class TestConditionExecution:
    """Test cases for condition execution functionality"""

    @pytest.fixture
    def condition_config(self):
        """Configuration with conditions for testing"""
        return {
            "name": "Condition Test",
            "version": "1.0.0",
            "description": "Test condition execution",
            "conditions": {
                "platform.macbook": "platform.system() == 'Darwin' and platform.machine() == 'arm64'",
                "platform.other": "platform.system() != 'Darwin' or platform.machine() != 'arm64'",
                "always_true": "True",
                "always_false": "False",
                "complex_condition": "platform.system() == 'Darwin' and platform.machine() in ['arm64', 'x86_64']"
            },
            "global": {
                "working_directory": ".",
                "output_directory": "results",
                "timeout": 30,
                "verbose": True
            },
            "steps": [
                {
                    "name": "test_step",
                    "description": "Test step with conditions",
                    "enabled": True,
                    "commands": [
                        {
                            "command": "echo 'MacBook command'",
                            "cwd": ".",
                            "timeout": 10,
                            "expected_exit_code": 0,
                            "condition": "platform.macbook"
                        },
                        {
                            "command": "echo 'Other platform command'",
                            "cwd": ".",
                            "timeout": 10,
                            "expected_exit_code": 0,
                            "condition": "platform.other"
                        },
                        {
                            "command": "echo 'Always true command'",
                            "cwd": ".",
                            "timeout": 10,
                            "expected_exit_code": 0,
                            "condition": "always_true"
                        },
                        {
                            "command": "echo 'Always false command'",
                            "cwd": ".",
                            "timeout": 10,
                            "expected_exit_code": 0,
                            "condition": "always_false"
                        },
                        {
                            "command": "echo 'No condition command'",
                            "cwd": ".",
                            "timeout": 10,
                            "expected_exit_code": 0
                        },
                        {
                            "command": "echo 'Complex condition command'",
                            "cwd": ".",
                            "timeout": 10,
                            "expected_exit_code": 0,
                            "condition": "complex_condition"
                        }
                    ]
                }
            ],
            "parsers": {}
        }

    def test_condition_evaluation_macbook(self, condition_config, temp_dir):
        """Test condition evaluation on MacBook platform"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test condition evaluation
        assert executor._evaluate_condition("platform.system() == 'Darwin'") == (platform.system() == 'Darwin')
        assert executor._evaluate_condition("platform.machine() == 'arm64'") == (platform.machine() == 'arm64')
        assert executor._evaluate_condition("platform.system() == 'Darwin' and platform.machine() == 'arm64'") == (
            platform.system() == 'Darwin' and platform.machine() == 'arm64'
        )

    def test_condition_evaluation_boolean(self, condition_config, temp_dir):
        """Test boolean condition evaluation"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        assert executor._evaluate_condition("True") is True
        assert executor._evaluate_condition("False") is False
        assert executor._evaluate_condition("1 == 1") is True
        assert executor._evaluate_condition("1 == 2") is False

    def test_should_run_command_with_condition(self, condition_config, temp_dir):
        """Test command execution decision based on conditions"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test always true condition
        always_true_cmd = {"condition": "always_true"}
        assert executor._should_run_command(always_true_cmd) is True

        # Test always false condition
        always_false_cmd = {"condition": "always_false"}
        assert executor._should_run_command(always_false_cmd) is False

        # Test no condition (should always run)
        no_condition_cmd = {"command": "echo 'test'"}
        assert executor._should_run_command(no_condition_cmd) is True

    def test_should_run_command_platform_specific(self, condition_config, temp_dir):
        """Test platform-specific command execution"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test MacBook condition
        macbook_cmd = {"condition": "platform.macbook"}
        expected_macbook = platform.system() == 'Darwin' and platform.machine() == 'arm64'
        assert executor._should_run_command(macbook_cmd) == expected_macbook

        # Test other platform condition
        other_cmd = {"condition": "platform.other"}
        expected_other = platform.system() != 'Darwin' or platform.machine() != 'arm64'
        assert executor._should_run_command(other_cmd) == expected_other

    def test_should_run_command_undefined_condition(self, condition_config, temp_dir):
        """Test behavior with undefined condition"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test undefined condition (should default to True and show warning)
        undefined_cmd = {"condition": "undefined_condition"}
        with patch('perfx.core.executor.console.print') as mock_print:
            result = executor._should_run_command(undefined_cmd)
            assert result is True
            mock_print.assert_called_with("[yellow]Warning: Condition 'undefined_condition' not found in config[/yellow]")

    def test_condition_evaluation_error_handling(self, condition_config, temp_dir):
        """Test error handling in condition evaluation"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test invalid condition expression
        with patch('perfx.core.executor.console.print') as mock_print:
            result = executor._evaluate_condition("invalid_syntax(")
            assert result is False
            mock_print.assert_called()

    def test_run_step_with_conditions(self, condition_config, temp_dir):
        """Test running a step with conditional commands"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Command executed\n", stderr=""
            )

            success = executor.run()

            assert success is True
            
            # Count how many commands were actually executed
            executed_commands = [cmd for cmd in executor.recorder.results["commands"] if cmd["success"]]
            
            # Should execute: always_true, no_condition, and complex_condition (if true)
            # Should skip: always_false, and platform-specific commands based on current platform
            expected_min_commands = 2  # always_true + no_condition
            expected_max_commands = 4  # + complex_condition + one platform-specific
            
            assert len(executed_commands) >= expected_min_commands
            assert len(executed_commands) <= expected_max_commands

    def test_condition_with_environment_variables(self, condition_config, temp_dir):
        """Test condition evaluation with environment variables"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test condition that uses environment variables
        env_condition = "os.environ.get('TEST_VAR', '') == 'test_value'"
        
        # Without the environment variable (or with different value)
        # The test might be running in an environment where TEST_VAR is already set
        # So we need to be more specific about the test condition
        with patch.dict('os.environ', {}, clear=True):
            assert executor._evaluate_condition(env_condition) is False
        
        # With the environment variable
        with patch.dict('os.environ', {'TEST_VAR': 'test_value'}, clear=True):
            assert executor._evaluate_condition(env_condition) is True

    def test_complex_condition_evaluation(self, condition_config, temp_dir):
        """Test complex condition expressions"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test complex condition
        complex_condition = "platform.system() == 'Darwin' and platform.machine() in ['arm64', 'x86_64']"
        expected_result = platform.system() == 'Darwin' and platform.machine() in ['arm64', 'x86_64']
        assert executor._evaluate_condition(complex_condition) == expected_result

        # Test nested conditions
        nested_condition = "(platform.system() == 'Darwin') and (platform.machine() == 'arm64' or platform.machine() == 'x86_64')"
        expected_nested = (platform.system() == 'Darwin') and (platform.machine() == 'arm64' or platform.machine() == 'x86_64')
        assert executor._evaluate_condition(nested_condition) == expected_nested

    def test_condition_with_imports(self, condition_config, temp_dir):
        """Test condition evaluation with imported modules"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test using imported modules in boolean expressions
        assert executor._evaluate_condition("platform.system() == 'Darwin'") == (platform.system() == 'Darwin')
        assert executor._evaluate_condition("platform.machine() == 'arm64'") == (platform.machine() == 'arm64')
        assert executor._evaluate_condition("platform.architecture()[0] == '64bit'") == (platform.architecture()[0] == '64bit')

    def test_condition_safety(self, condition_config, temp_dir):
        """Test that condition evaluation is safe from malicious code"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test that dangerous operations are not allowed
        dangerous_conditions = [
            "__import__('os').system('echo dangerous')",
            "open('/etc/passwd').read()",
            "exec('print(\"dangerous\")')",
            "eval('__import__(\"os\").system(\"echo dangerous\")')"
        ]

        for condition in dangerous_conditions:
            # These should either fail safely or be restricted
            result = executor._evaluate_condition(condition)
            # Should not execute dangerous code, should return False or raise exception safely
            assert result is False

    def test_condition_performance(self, condition_config, temp_dir):
        """Test that condition evaluation is reasonably fast"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        import time
        
        # Test simple condition performance
        start_time = time.time()
        for _ in range(1000):
            executor._evaluate_condition("platform.system() == 'Darwin'")
        end_time = time.time()
        
        # Should complete 1000 evaluations in less than 1 second
        assert (end_time - start_time) < 1.0

    def test_condition_logging(self, condition_config, temp_dir):
        """Test that condition evaluation logs appropriately"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        with patch('perfx.core.executor.console.print') as mock_print:
            # Test successful condition evaluation
            executor._evaluate_condition("True")
            # Should not print anything for successful evaluation
            
            # Test failed condition evaluation
            executor._evaluate_condition("invalid_syntax(")
            # Should print error message
            mock_print.assert_called()

    def test_condition_with_config_conditions(self, condition_config, temp_dir):
        """Test using conditions defined in config"""
        output_dir = str(temp_dir / "output")
        executor = EvaluationExecutor(condition_config, output_dir)

        # Test using config-defined conditions
        assert executor._should_run_command({"condition": "platform.macbook"}) == (
            platform.system() == 'Darwin' and platform.machine() == 'arm64'
        )
        assert executor._should_run_command({"condition": "platform.other"}) == (
            platform.system() != 'Darwin' or platform.machine() != 'arm64'
        )
        assert executor._should_run_command({"condition": "always_true"}) is True
        assert executor._should_run_command({"condition": "always_false"}) is False 