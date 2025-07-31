"""
Tests for EvaluationRecorder
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from perfx.core.recorder import EvaluationRecorder


class TestEvaluationRecorder:
    """Test EvaluationRecorder functionality"""

    def test_init(self, temp_dir):
        """Test recorder initialization"""
        recorder = EvaluationRecorder(str(temp_dir))
        
        assert recorder.output_dir == str(temp_dir)
        assert recorder.results == {
            "commands": [],
            "steps": {},
            "metadata": {}
        }

    def test_add_command(self, temp_dir):
        """Test adding command results"""
        recorder = EvaluationRecorder(str(temp_dir))
        
        command_result = {
            "command": "echo 'test'",
            "stdout": "test\n",
            "stderr": "",
            "exit_code": 0,
            "duration": 0.1,
            "success": True
        }
        
        recorder.add_command("test_step", command_result)
        
        assert len(recorder.results["commands"]) == 1
        assert recorder.results["commands"][0]["step_name"] == "test_step"
        assert recorder.results["commands"][0]["result"] == command_result

    def test_add_step_results(self, temp_dir):
        """Test adding step results"""
        recorder = EvaluationRecorder(str(temp_dir))
        
        step_results = {
            "success": True,
            "total_commands": 2,
            "successful_commands": 2,
            "failed_commands": 0,
            "duration": 0.5
        }
        
        recorder.add_step_results("test_step", step_results)
        
        assert "test_step" in recorder.results["steps"]
        assert recorder.results["steps"]["test_step"] == step_results

    def test_save_results(self, temp_dir):
        """Test saving results to files"""
        recorder = EvaluationRecorder(str(temp_dir))
        
        # Add some test data
        command_result = {
            "command": "echo 'test'",
            "stdout": "test\n",
            "stderr": "",
            "exit_code": 0,
            "duration": 0.1,
            "success": True
        }
        recorder.add_command("test_step", command_result)
        
        step_results = {
            "success": True,
            "total_commands": 1,
            "successful_commands": 1,
            "failed_commands": 0,
            "duration": 0.1
        }
        recorder.add_step_results("test_step", step_results)
        
        # Save results
        recorder.save_results()
        
        # Check that files were created
        json_file = Path(temp_dir) / "evaluation_results.json"
        log_file = Path(temp_dir) / "evaluation.log"
        
        assert json_file.exists()
        assert log_file.exists()
        
        # Check JSON content
        with open(json_file, 'r') as f:
            saved_data = json.load(f)
        
        assert "commands" in saved_data
        assert "steps" in saved_data
        assert len(saved_data["commands"]) == 1
        assert "test_step" in saved_data["steps"]

    def test_save_results_with_metadata(self, temp_dir):
        """Test saving results with metadata"""
        recorder = EvaluationRecorder(str(temp_dir))
        
        metadata = {
            "start_time": "2024-01-01T12:00:00Z",
            "end_time": "2024-01-01T12:01:00Z",
            "total_duration": 60.0
        }
        
        recorder.results["metadata"] = metadata
        recorder.save_results()
        
        json_file = Path(temp_dir) / "evaluation_results.json"
        with open(json_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["metadata"] == metadata

    def test_get_step_commands(self, temp_dir):
        """Test getting commands for a specific step"""
        recorder = EvaluationRecorder(str(temp_dir))
        
        # Add commands for different steps
        recorder.add_command("step1", {"command": "echo 'step1'", "success": True})
        recorder.add_command("step2", {"command": "echo 'step2'", "success": True})
        recorder.add_command("step1", {"command": "echo 'step1 again'", "success": True})
        
        step1_commands = recorder.get_step_commands("step1")
        step2_commands = recorder.get_step_commands("step2")
        
        assert len(step1_commands) == 2
        assert len(step2_commands) == 1
        assert step1_commands[0]["result"]["command"] == "echo 'step1'"
        assert step2_commands[0]["result"]["command"] == "echo 'step2'"

    def test_get_step_commands_empty(self, temp_dir):
        """Test getting commands for non-existent step"""
        recorder = EvaluationRecorder(str(temp_dir))
        
        commands = recorder.get_step_commands("non_existent")
        assert commands == []

    def test_save_results_creates_directory(self):
        """Test that save_results creates output directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "results"
            recorder = EvaluationRecorder(str(output_dir))
            
            # Add some data
            recorder.add_command("test_step", {"command": "echo 'test'", "success": True})
            
            # Save results (should create the directory)
            recorder.save_results()
            
            assert output_dir.exists()
            assert (output_dir / "evaluation_results.json").exists()
            assert (output_dir / "evaluation.log").exists()

    def test_log_file_content(self, temp_dir):
        """Test that log file contains readable content"""
        recorder = EvaluationRecorder(str(temp_dir))
        
        # Add some test data
        recorder.add_command("test_step", {
            "command": "echo 'test'",
            "stdout": "test output\n",
            "stderr": "test error\n",
            "exit_code": 0,
            "duration": 0.1,
            "success": True
        })
        
        recorder.save_results()
        
        log_file = Path(temp_dir) / "evaluation.log"
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        assert "test_step" in log_content
        assert "echo 'test'" in log_content
        assert "test output" in log_content
        assert "test error" in log_content
        assert "0.1" in log_content  # duration 