"""
Tests for DataProcessor
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from perfx.core.processor import DataProcessor


class TestDataProcessor:
    """Test DataProcessor functionality"""

    def test_init(self, temp_dir):
        """Test processor initialization"""
        processor = DataProcessor(str(temp_dir))
        
        assert processor.output_dir == str(temp_dir)

    def test_process_all_data_empty(self, temp_dir):
        """Test processing empty data"""
        processor = DataProcessor(str(temp_dir))
        
        # Mock recorder with empty data
        mock_recorder = Mock()
        mock_recorder.results = {
            "commands": [],
            "steps": {},
            "metadata": {}
        }
        
        result = processor.process_all_data(mock_recorder)
        
        assert result["success"] is True
        assert "visualizations" in result
        assert "reports" in result

    def test_process_all_data_with_commands(self, temp_dir):
        """Test processing data with commands"""
        processor = DataProcessor(str(temp_dir))
        
        # Mock recorder with command data
        mock_recorder = Mock()
        mock_recorder.results = {
            "commands": [
                {
                    "step_name": "test_step",
                    "result": {
                        "command": "echo 'test'",
                        "stdout": "test output\n",
                        "stderr": "",
                        "exit_code": 0,
                        "duration": 0.1,
                        "success": True
                    }
                }
            ],
            "steps": {
                "test_step": {
                    "success": True,
                    "total_commands": 1,
                    "successful_commands": 1,
                    "failed_commands": 0,
                    "duration": 0.1
                }
            },
            "metadata": {}
        }
        
        with patch.object(processor, '_generate_visualizations') as mock_viz:
            with patch.object(processor, '_generate_reports') as mock_reports:
                mock_viz.return_value = {"success": True, "files": []}
                mock_reports.return_value = {"success": True, "files": []}
                
                result = processor.process_all_data(mock_recorder)
        
        assert result["success"] is True
        mock_viz.assert_called_once()
        mock_reports.assert_called_once()

    def test_extract_command_data(self, temp_dir):
        """Test extracting command data"""
        processor = DataProcessor(str(temp_dir))
        
        commands = [
            {
                "step_name": "step1",
                "result": {
                    "command": "echo 'test1'",
                    "duration": 0.1,
                    "success": True
                }
            },
            {
                "step_name": "step2",
                "result": {
                    "command": "echo 'test2'",
                    "duration": 0.2,
                    "success": False
                }
            }
        ]
        
        data = processor._extract_command_data(commands)
        
        assert len(data) == 2
        assert data[0]["step_name"] == "step1"
        assert data[0]["command"] == "echo 'test1'"
        assert data[0]["duration"] == 0.1
        assert data[0]["success"] is True
        assert data[1]["step_name"] == "step2"
        assert data[1]["success"] is False

    def test_extract_step_data(self, temp_dir):
        """Test extracting step data"""
        processor = DataProcessor(str(temp_dir))
        
        steps = {
            "step1": {
                "success": True,
                "total_commands": 2,
                "successful_commands": 2,
                "failed_commands": 0,
                "duration": 0.3
            },
            "step2": {
                "success": False,
                "total_commands": 1,
                "successful_commands": 0,
                "failed_commands": 1,
                "duration": 0.1
            }
        }
        
        data = processor._extract_step_data(steps)
        
        assert len(data) == 2
        assert data[0]["step_name"] == "step1"
        assert data[0]["success"] is True
        assert data[0]["total_commands"] == 2
        assert data[0]["duration"] == 0.3
        assert data[1]["step_name"] == "step2"
        assert data[1]["success"] is False

    def test_generate_visualizations(self, temp_dir):
        """Test generating visualizations"""
        processor = DataProcessor(str(temp_dir))
        
        # Mock data
        command_data = [
            {
                "step_name": "test_step",
                "command": "echo 'test'",
                "duration": 0.1,
                "success": True
            }
        ]
        
        step_data = [
            {
                "step_name": "test_step",
                "success": True,
                "total_commands": 1,
                "duration": 0.1
            }
        ]
        
        with patch('perfx.visualizers.charts.ChartGenerator') as mock_chart_gen:
            mock_generator = Mock()
            mock_chart_gen.return_value = mock_generator
            mock_generator.create_line_chart.return_value = {"success": True, "file": "chart.png"}
            
            result = processor._generate_visualizations(command_data, step_data)
        
        assert result["success"] is True
        assert "files" in result

    def test_generate_reports(self, temp_dir):
        """Test generating reports"""
        processor = DataProcessor(str(temp_dir))
        
        # Mock data
        command_data = [
            {
                "step_name": "test_step",
                "command": "echo 'test'",
                "duration": 0.1,
                "success": True
            }
        ]
        
        step_data = [
            {
                "step_name": "test_step",
                "success": True,
                "total_commands": 1,
                "duration": 0.1
            }
        ]
        
        with patch('perfx.visualizers.reports.ReportGenerator') as mock_report_gen:
            mock_generator = Mock()
            mock_report_gen.return_value = mock_generator
            mock_generator.generate_report.return_value = {"success": True, "file": "report.html"}
            
            result = processor._generate_reports(command_data, step_data)
        
        assert result["success"] is True
        assert "files" in result

    def test_process_all_data_with_visualization_errors(self, temp_dir):
        """Test processing data when visualizations fail"""
        processor = DataProcessor(str(temp_dir))
        
        # Mock recorder with data
        mock_recorder = Mock()
        mock_recorder.results = {
            "commands": [
                {
                    "step_name": "test_step",
                    "result": {
                        "command": "echo 'test'",
                        "duration": 0.1,
                        "success": True
                    }
                }
            ],
            "steps": {
                "test_step": {
                    "success": True,
                    "total_commands": 1,
                    "duration": 0.1
                }
            },
            "metadata": {}
        }
        
        with patch.object(processor, '_generate_visualizations') as mock_viz:
            with patch.object(processor, '_generate_reports') as mock_reports:
                mock_viz.return_value = {"success": False, "error": "Chart generation failed"}
                mock_reports.return_value = {"success": True, "files": []}
                
                result = processor.process_all_data(mock_recorder)
        
        assert result["success"] is False
        assert "visualization" in result["error"].lower()

    def test_process_all_data_with_report_errors(self, temp_dir):
        """Test processing data when reports fail"""
        processor = DataProcessor(str(temp_dir))
        
        # Mock recorder with data
        mock_recorder = Mock()
        mock_recorder.results = {
            "commands": [
                {
                    "step_name": "test_step",
                    "result": {
                        "command": "echo 'test'",
                        "duration": 0.1,
                        "success": True
                    }
                }
            ],
            "steps": {
                "test_step": {
                    "success": True,
                    "total_commands": 1,
                    "duration": 0.1
                }
            },
            "metadata": {}
        }
        
        with patch.object(processor, '_generate_visualizations') as mock_viz:
            with patch.object(processor, '_generate_reports') as mock_reports:
                mock_viz.return_value = {"success": True, "files": []}
                mock_reports.return_value = {"success": False, "error": "Report generation failed"}
                
                result = processor.process_all_data(mock_recorder)
        
        assert result["success"] is False
        assert "report" in result["error"].lower()

    def test_extract_command_data_empty(self, temp_dir):
        """Test extracting data from empty commands list"""
        processor = DataProcessor(str(temp_dir))
        
        data = processor._extract_command_data([])
        assert data == []

    def test_extract_step_data_empty(self, temp_dir):
        """Test extracting data from empty steps dict"""
        processor = DataProcessor(str(temp_dir))
        
        data = processor._extract_step_data({})
        assert data == [] 