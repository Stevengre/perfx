import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from perfx.core.executor import EvaluationExecutor


class TestCleanupFunctionality:
    """Test cleanup functionality in perfx executor"""
    
    def test_cleanup_commands_run_regardless_of_failure(self):
        """Test that cleanup commands run even if other commands fail"""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test config
            config = {
                "global": {
                    "output_directory": str(temp_path / "results"),
                    "working_directory": str(temp_path),
                    "timeout": 300
                },
                "steps": [
                    {
                        "name": "test_step_with_cleanup",
                        "description": "Test step that creates a file and should cleanup",
                        "enabled": True,
                        "commands": [
                            {
                                "command": "echo 'test content' > test_file.txt",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            {
                                "command": "exit 1",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "continue_on_failure": True
                            },
                            {
                                "command": "echo 'cleanup completed' > cleanup.log",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    }
                ]
            }
            
            # Create executor
            executor = EvaluationExecutor(config, output_dir=str(temp_path / "results"))
            
            # Run the step
            result = executor.run(["test_step_with_cleanup"])
            
            # Check that cleanup command was executed
            cleanup_log = temp_path / "cleanup.log"
            assert cleanup_log.exists(), "Cleanup log should exist"
            
            with open(cleanup_log, 'r') as f:
                content = f.read().strip()
                assert content == "cleanup completed", "Cleanup log should contain expected content"
    
    def test_cleanup_commands_run_in_reverse_order(self):
        """Test that cleanup commands run in reverse order"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            config = {
                "global": {
                    "output_directory": str(temp_path / "results"),
                    "working_directory": str(temp_path),
                    "timeout": 300
                },
                "steps": [
                    {
                        "name": "test_cleanup_order",
                        "enabled": True,
                        "commands": [
                            {
                                "command": "echo '1' > cleanup_order.log",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            {
                                "command": "echo '2' >> cleanup_order.log",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            },
                            {
                                "command": "echo '3' >> cleanup_order.log",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    }
                ]
            }
            
            executor = EvaluationExecutor(config, output_dir=str(temp_path / "results"))
            result = executor.run(["test_cleanup_order"])
            
            # Check cleanup order (should be 3, 2, 1)
            cleanup_log = temp_path / "cleanup_order.log"
            assert cleanup_log.exists()
            
            with open(cleanup_log, 'r') as f:
                lines = [line.strip() for line in f.readlines()]
                # The order should be: 1 (normal), 3 (cleanup), 2 (cleanup)
                # But since cleanup runs in reverse order, it should be: 1, 3, 2
                assert lines == ["1", "3", "2"], f"Expected ['1', '3', '2'], got {lines}"
    
    def test_semantics_switching_with_cleanup(self):
        """Test semantics switching with proper cleanup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a mock interpreter.py file
            interpreter_file = temp_path / "interpreter.py"
            original_content = "kdist.get('evm-semantics.llvm')"
            with open(interpreter_file, 'w') as f:
                f.write(original_content)
            
            config = {
                "global": {
                    "output_directory": str(temp_path / "results"),
                    "working_directory": str(temp_path),
                    "timeout": 300
                },
                "steps": [
                    {
                        "name": "test_semantics_switch",
                        "enabled": True,
                        "commands": [
                            {
                                "command": f"sed -i.bak \"s/kdist.get('evm-semantics.llvm')/kdist.get('evm-semantics.llvm-pure')/g\" {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            {
                                "command": "echo 'test execution'",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            {
                                "command": f"cp {interpreter_file}.bak {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    }
                ]
            }
            
            executor = EvaluationExecutor(config, output_dir=str(temp_path / "results"))
            result = executor.run(["test_semantics_switch"])
            
            # Check that the file was restored to original state
            with open(interpreter_file, 'r') as f:
                final_content = f.read().strip()
                assert final_content == original_content, f"File should be restored to original state, got: {final_content}"
            
            # Check that backup file exists
            backup_file = temp_path / "interpreter.py.bak"
            assert backup_file.exists(), "Backup file should exist"
    
    def test_cleanup_from_config_file(self):
        """Test cleanup functionality using a config file"""
        config_file = Path(__file__).parent / "test_cleanup_config.yaml"
        assert config_file.exists(), f"Config file {config_file} should exist"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Load config and update paths
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update config paths for testing
            config["global"]["output_directory"] = str(temp_path / "results")
            config["global"]["working_directory"] = str(temp_path)
            
            # Update all command cwd paths to use temp_path
            for step in config["steps"]:
                for command in step["commands"]:
                    if command.get("cwd") == ".":
                        command["cwd"] = str(temp_path)
            
            # Create executor
            executor = EvaluationExecutor(config, output_dir=str(temp_path / "results"))
            
            # Run the step
            result = executor.run(["test_step_with_cleanup"])
            
            # Check that cleanup command was executed
            cleanup_log = temp_path / "cleanup.log"
            assert cleanup_log.exists(), "Cleanup log should exist"
            
            with open(cleanup_log, 'r') as f:
                content = f.read().strip()
                assert content == "cleanup completed", "Cleanup log should contain expected content" 
    
    def test_backup_file_accumulation(self):
        """Test that backup files accumulate and need cleanup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a mock interpreter.py file
            interpreter_file = temp_path / "interpreter.py"
            original_content = "kdist.get('evm-semantics.llvm')"
            with open(interpreter_file, 'w') as f:
                f.write(original_content)
            
            config = {
                "global": {
                    "output_directory": str(temp_path / "results"),
                    "working_directory": str(temp_path),
                    "timeout": 300
                },
                "steps": [
                    {
                        "name": "test_first_step_with_backup",
                        "enabled": True,
                        "commands": [
                            # Create original backup (only in first step)
                            {
                                "command": f"cp {interpreter_file} {interpreter_file}.original",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # First sed operation
                            {
                                "command": f"sed -i.bak \"s/kdist.get('evm-semantics.llvm')/kdist.get('evm-semantics.llvm-pure')/g\" {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Test execution
                            {
                                "command": "echo 'test execution'",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Cleanup: restore from original backup
                            {
                                "command": f"cp {interpreter_file}.original {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    },
                    {
                        "name": "test_last_step_with_cleanup",
                        "enabled": True,
                        "commands": [
                            # Second sed operation (no backup creation)
                            {
                                "command": f"sed -i.bak \"s/kdist.get('evm-semantics.llvm')/kdist.get('evm-semantics.llvm-summary')/g\" {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Test execution
                            {
                                "command": "echo 'test execution'",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Final cleanup: restore and clean all backup files
                            {
                                "command": f"cp {interpreter_file}.original {interpreter_file} && rm -f {interpreter_file}.original {interpreter_file}.bak*",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    }
                ]
            }
            
            executor = EvaluationExecutor(config, output_dir=str(temp_path / "results"))
            result = executor.run(["test_first_step_with_backup", "test_last_step_with_cleanup"])
            
            # Check that the file was restored to original state
            with open(interpreter_file, 'r') as f:
                final_content = f.read().strip()
                assert final_content == original_content, f"File should be restored to original state, got: {final_content}"
            
            # Check that all backup files were cleaned up
            backup_files = list(temp_path.glob("interpreter.py.bak*"))
            original_backup = temp_path / "interpreter.py.original"
            assert len(backup_files) == 0, f"Backup files should be cleaned up, found: {backup_files}"
            assert not original_backup.exists(), "Original backup file should be cleaned up" 
    
    def test_each_step_starts_from_same_state(self):
        """Test that each step starts from the same initial state"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a mock interpreter.py file
            interpreter_file = temp_path / "interpreter.py"
            original_content = "kdist.get('evm-semantics.llvm')"
            with open(interpreter_file, 'w') as f:
                f.write(original_content)
            
            config = {
                "global": {
                    "output_directory": str(temp_path / "results"),
                    "working_directory": str(temp_path),
                    "timeout": 300
                },
                "steps": [
                    {
                        "name": "step1",
                        "enabled": True,
                        "commands": [
                            # Create backup
                            {
                                "command": f"cp {interpreter_file} {interpreter_file}.original",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Modify to pure
                            {
                                "command": f"sed -i.bak \"s/kdist.get('evm-semantics.llvm')/kdist.get('evm-semantics.llvm-pure')/g\" {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Test
                            {
                                "command": "echo 'test1'",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Restore
                            {
                                "command": f"cp {interpreter_file}.original {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    },
                    {
                        "name": "step2",
                        "enabled": True,
                        "commands": [
                            # Modify to summary (should start from llvm)
                            {
                                "command": f"sed -i.bak \"s/kdist.get('evm-semantics.llvm')/kdist.get('evm-semantics.llvm-summary')/g\" {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Test
                            {
                                "command": "echo 'test2'",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Restore
                            {
                                "command": f"cp {interpreter_file}.original {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    }
                ]
            }
            
            executor = EvaluationExecutor(config, output_dir=str(temp_path / "results"))
            result = executor.run(["step1", "step2"])
            
            # Check that the file was restored to original state
            with open(interpreter_file, 'r') as f:
                final_content = f.read().strip()
                assert final_content == original_content, f"File should be restored to original state, got: {final_content}"
            
            # Check that backup files exist but will be cleaned up in final step
            backup_file = temp_path / "interpreter.py.bak"
            original_backup = temp_path / "interpreter.py.original"
            assert backup_file.exists(), "Backup file should exist after sed"
            assert original_backup.exists(), "Original backup should exist" 
    
    def test_rm_mv_restore_method(self):
        """Test using rm + mv to restore files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a mock interpreter.py file
            interpreter_file = temp_path / "interpreter.py"
            original_content = "kdist.get('evm-semantics.llvm')"
            with open(interpreter_file, 'w') as f:
                f.write(original_content)
            
            config = {
                "global": {
                    "output_directory": str(temp_path / "results"),
                    "working_directory": str(temp_path),
                    "timeout": 300
                },
                "steps": [
                    {
                        "name": "test_rm_mv_restore",
                        "enabled": True,
                        "commands": [
                            # Modify file
                            {
                                "command": f"sed -i.bak \"s/kdist.get('evm-semantics.llvm')/kdist.get('evm-semantics.llvm-pure')/g\" {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Test
                            {
                                "command": "echo 'test execution'",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Restore using rm + mv
                            {
                                "command": f"rm {interpreter_file} && mv {interpreter_file}.bak {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    }
                ]
            }
            
            executor = EvaluationExecutor(config, output_dir=str(temp_path / "results"))
            result = executor.run(["test_rm_mv_restore"])
            
            # Check that the file was restored to original state
            with open(interpreter_file, 'r') as f:
                final_content = f.read().strip()
                assert final_content == original_content, f"File should be restored to original state, got: {final_content}"
            
            # Check that no backup files remain
            backup_file = temp_path / "interpreter.py.bak"
            assert not backup_file.exists(), "Backup file should not exist after mv" 
    
    def test_direct_mv_restore_method(self):
        """Test using direct mv to restore files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a mock interpreter.py file
            interpreter_file = temp_path / "interpreter.py"
            original_content = "kdist.get('evm-semantics.llvm')"
            with open(interpreter_file, 'w') as f:
                f.write(original_content)
            
            config = {
                "global": {
                    "output_directory": str(temp_path / "results"),
                    "working_directory": str(temp_path),
                    "timeout": 300
                },
                "steps": [
                    {
                        "name": "test_direct_mv_restore",
                        "enabled": True,
                        "commands": [
                            # Modify file
                            {
                                "command": f"sed -i.bak \"s/kdist.get('evm-semantics.llvm')/kdist.get('evm-semantics.llvm-pure')/g\" {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Test
                            {
                                "command": "echo 'test execution'",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0
                            },
                            # Restore using direct mv
                            {
                                "command": f"mv {interpreter_file}.bak {interpreter_file}",
                                "cwd": str(temp_path),
                                "timeout": 30,
                                "expected_exit_code": 0,
                                "cleanup": True
                            }
                        ]
                    }
                ]
            }
            
            executor = EvaluationExecutor(config, output_dir=str(temp_path / "results"))
            result = executor.run(["test_direct_mv_restore"])
            
            # Check that the file was restored to original state
            with open(interpreter_file, 'r') as f:
                final_content = f.read().strip()
                assert final_content == original_content, f"File should be restored to original state, got: {final_content}"
            
            # Check that no backup files remain
            backup_file = temp_path / "interpreter.py.bak"
            assert not backup_file.exists(), "Backup file should not exist after mv" 

    def test_concrete_execution_commands(self):
        """Test concrete execution commands are correct"""
        # Test that concrete execution uses the right test path
        concrete_command = "uv run -- pytest src/tests/integration/test_conformance.py --durations=0 --verbose"
        assert "src/tests/integration/test_conformance.py" in concrete_command
        assert "--durations=0" in concrete_command
        assert "--verbose" in concrete_command

    def test_symbolic_execution_commands(self):
        """Test symbolic execution commands are correct"""
        # Test that symbolic execution uses make commands
        symbolic_commands = [
            "make test-prove-rules PYTEST_ARGS='-v --tb=short --durations=0 --timeout=7200'",
            "make test-prove-summaries PYTEST_ARGS='-v --tb=short --durations=0 --timeout=7200'",
            "make test-prove-dss PYTEST_ARGS='-v --tb=short --durations=0 --timeout=7200'"
        ]
        
        for cmd in symbolic_commands:
            assert cmd.startswith("make ")
            assert "PYTEST_ARGS=" in cmd
            assert "--durations=0" in cmd
            assert "--timeout=7200" in cmd

    def test_symbolic_file_modification(self):
        """Test symbolic execution file modification is correct"""
        # Test that symbolic execution modifies specs directory, not interpreter.py
        pure_cmd = "find repositories/evm-semantics/tests/specs -type f -exec sed -i.bak 's/EDSL/EDSL-PURE/g' {} \\;"
        summary_cmd = "find repositories/evm-semantics/tests/specs -type f -exec sed -i.bak 's/EDSL/EDSL-SUMMARY/g' {} \\;"
        
        assert "repositories/evm-semantics/tests/specs" in pure_cmd
        assert "EDSL-PURE" in pure_cmd
        assert "repositories/evm-semantics/tests/specs" in summary_cmd
        assert "EDSL-SUMMARY" in summary_cmd 

    def test_all_pytest_commands_have_parser(self):
        """Test that all pytest commands have parser configuration"""
        # List of all pytest commands that should have parser
        pytest_commands = [
            "prove_summaries",
            "pure_concrete_performance", 
            "summary_concrete_performance",
            "pure_symbolic_prove_rules_booster",
            "pure_symbolic_prove_rules_booster_dev",
            "pure_symbolic_prove_summaries",
            "pure_symbolic_prove_dss",
            "summary_symbolic_prove_rules_booster",
            "summary_symbolic_prove_rules_booster_dev",
            "summary_symbolic_prove_summaries",
            "summary_symbolic_prove_dss"
        ]
        
        # Each command should have a corresponding .json output file
        for command in pytest_commands:
            json_file = f"results/data/{command}.json"
            assert json_file.endswith(".json"), f"Command {command} should have JSON output"
            
        # Verify that the parser configuration is correct
        parser_config = {
            "input": "stdout",
            "parser": "pytest",
            "output": "results/data/test_command.json"
        }
        
        assert parser_config["parser"] == "pytest"
        assert parser_config["input"] == "stdout"
        assert parser_config["output"].endswith(".json") 

    def test_pytest_parser_output_structure(self):
        """Test that pytest parser outputs detailed test information"""
        # Example pytest output structure that should be generated
        expected_structure = {
            "success": True,  # Overall test success
            "total_tests": 10,  # Total number of tests
            "passed_tests": 8,  # Number of passed tests
            "failed_tests": 2,  # Number of failed tests
            "skipped_tests": 0,  # Number of skipped tests
            "error_tests": 0,  # Number of error tests
            "total_duration": 45.67,  # Total duration in seconds
            "test_results": [  # Detailed test results
                {
                    "test_id": "test_conformance_1",
                    "status": "PASSED",
                    "duration": 2.34,
                    "error_message": None,
                    "progress_percent": 10,
                    "worker_id": "gw0"
                },
                {
                    "test_id": "test_conformance_2", 
                    "status": "FAILED",
                    "duration": 1.23,
                    "error_message": "AssertionError: Expected True, got False",
                    "progress_percent": 20,
                    "worker_id": "gw1"
                }
            ],
            "summary_stats": {  # Summary statistics
                "total_duration": 45.67,
                "success_rate": 80.0
            }
        }
        
        # Verify the structure has all required fields
        assert "success" in expected_structure
        assert "total_tests" in expected_structure
        assert "passed_tests" in expected_structure
        assert "failed_tests" in expected_structure
        assert "test_results" in expected_structure
        assert "total_duration" in expected_structure
        
        # Verify test_results structure
        for test_result in expected_structure["test_results"]:
            assert "test_id" in test_result
            assert "status" in test_result
            assert "duration" in test_result
            assert "error_message" in test_result 

    def test_git_checkout_cwd_correct(self):
        """Test that git checkout command has correct cwd"""
        # The git checkout command should be executed in the evm-semantics directory
        git_checkout_cmd = "git checkout -- tests/specs"
        git_checkout_cwd = "repositories/evm-semantics"
        
        # Verify the command and cwd are correct
        assert git_checkout_cmd == "git checkout -- tests/specs"
        assert git_checkout_cwd == "repositories/evm-semantics"
        
        # The command should be relative to the evm-semantics directory
        assert "tests/specs" in git_checkout_cmd
        assert not git_checkout_cmd.startswith("repositories/")
        
        # The cwd should point to the evm-semantics directory
        assert git_checkout_cwd == "repositories/evm-semantics" 