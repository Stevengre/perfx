"""
Tests for visualizers functionality
"""

import os
import tempfile
from pathlib import Path

import pytest

from perfx.visualizers.charts import ChartGenerator
from perfx.visualizers.tables import TableGenerator


class TestChartGenerator:
    """Test cases for ChartGenerator"""

    def test_create_line_chart(self, temp_dir):
        """Test creating a line chart"""
        generator = ChartGenerator()

        data = {
            "test1": {"duration": 1.0, "status": "PASSED"},
            "test2": {"duration": 1.5, "status": "PASSED"},
            "test3": {"duration": 0.8, "status": "FAILED"},
        }

        output_file = temp_dir / "line_chart.png"

        result = generator.create_line_chart(
            data=data,
            x_axis="test_name",
            y_axis="duration",
            title="Test Performance",
            output_file=str(output_file),
        )

        assert result["success"] is True
        assert output_file.exists()

    def test_create_bar_chart(self, temp_dir):
        """Test creating a bar chart"""
        generator = ChartGenerator()

        data = {
            "test1": {"duration": 1.0, "status": "PASSED"},
            "test2": {"duration": 1.5, "status": "PASSED"},
            "test3": {"duration": 0.8, "status": "FAILED"},
        }

        output_file = temp_dir / "bar_chart.png"

        result = generator.create_bar_chart(
            data=data,
            x_axis="test_name",
            y_axis="duration",
            title="Test Results",
            output_file=str(output_file),
        )

        assert result["success"] is True
        assert output_file.exists()

    def test_create_scatter_plot(self, temp_dir):
        """Test creating a scatter plot"""
        generator = ChartGenerator()

        data = {
            "test1": {"duration": 1.0, "memory": 100},
            "test2": {"duration": 1.5, "memory": 150},
            "test3": {"duration": 0.8, "memory": 80},
        }

        output_file = temp_dir / "scatter_plot.png"

        result = generator.create_scatter_plot(
            data=data,
            x_axis="duration",
            y_axis="memory",
            title="Duration vs Memory",
            output_file=str(output_file),
        )

        assert result["success"] is True
        assert output_file.exists()

    def test_create_histogram(self, temp_dir):
        """Test creating a histogram"""
        generator = ChartGenerator()

        data = [1.0, 1.5, 0.8, 1.2, 1.8, 0.9, 1.1]

        output_file = temp_dir / "histogram.png"

        result = generator.create_histogram(
            data=data, title="Duration Distribution", output_file=str(output_file)
        )

        assert result["success"] is True
        assert output_file.exists()

    def test_extract_plot_data(self):
        """Test extracting plot data from various formats"""
        generator = ChartGenerator()

        # Test dict format
        data_dict = {
            "test1": {"duration": 1.0, "status": "PASSED"},
            "test2": {"duration": 1.5, "status": "PASSED"},
        }

        x_data, y_data = generator._extract_plot_data(
            data_dict, "test_name", "duration"
        )

        assert len(x_data) == 2
        assert len(y_data) == 2
        assert "test1" in x_data
        assert "test2" in x_data
        assert 1.0 in y_data
        assert 1.5 in y_data

    def test_invalid_data_format(self, temp_dir):
        """Test handling invalid data format"""
        generator = ChartGenerator()

        output_file = temp_dir / "invalid_chart.png"

        result = generator.create_line_chart(
            data="invalid_data",
            x_axis="test_name",
            y_axis="duration",
            title="Test",
            output_file=str(output_file),
        )

        assert result["success"] is False
        assert "error" in result


class TestTableGenerator:
    """Test cases for TableGenerator"""

    def test_create_markdown_table(self, temp_dir):
        """Test creating a markdown table"""
        generator = TableGenerator()

        data = {
            "test1": {"status": "PASSED", "duration": 1.0},
            "test2": {"status": "FAILED", "duration": 1.5},
        }

        output_file = temp_dir / "table.md"

        result = generator.create_table(
            data=data,
            columns=["test_name", "status", "duration"],
            output_file=str(output_file),
            format="markdown",
        )

        assert result["success"] is True
        assert output_file.exists()

        # Check content
        content = output_file.read_text()
        assert "| test_name | status | duration |" in content
        assert "| test1 | PASSED | 1.0 |" in content

    def test_create_csv_table(self, temp_dir):
        """Test creating a CSV table"""
        generator = TableGenerator()

        data = {
            "test1": {"status": "PASSED", "duration": 1.0},
            "test2": {"status": "FAILED", "duration": 1.5},
        }

        output_file = temp_dir / "table.csv"

        result = generator.create_table(
            data=data,
            columns=["test_name", "status", "duration"],
            output_file=str(output_file),
            format="csv",
        )

        assert result["success"] is True
        assert output_file.exists()

        # Check content
        content = output_file.read_text()
        assert "test_name,status,duration" in content
        assert "test1,PASSED,1.0" in content

    def test_create_html_table(self, temp_dir):
        """Test creating an HTML table"""
        generator = TableGenerator()

        data = {
            "test1": {"status": "PASSED", "duration": 1.0},
            "test2": {"status": "FAILED", "duration": 1.5},
        }

        output_file = temp_dir / "table.html"

        result = generator.create_table(
            data=data,
            columns=["test_name", "status", "duration"],
            output_file=str(output_file),
            format="html",
        )

        assert result["success"] is True
        assert output_file.exists()

        # Check content
        content = output_file.read_text()
        assert "<table>" in content
        assert "<th>test_name</th>" in content

    def test_extract_table_data_dict(self):
        """Test extracting table data from dict format"""
        generator = TableGenerator()

        data = {
            "test1": {"status": "PASSED", "duration": 1.0},
            "test2": {"status": "FAILED", "duration": 1.5},
        }

        rows = generator._extract_table_data(data, ["test_name", "status", "duration"])

        assert len(rows) == 2
        assert rows[0][0] == "test1"  # test_name
        assert rows[0][1] == "PASSED"  # status
        assert rows[0][2] == "1.0"  # duration

    def test_extract_table_data_list(self):
        """Test extracting table data from list format"""
        generator = TableGenerator()

        data = [
            {"test_name": "test1", "status": "PASSED", "duration": 1.0},
            {"test_name": "test2", "status": "FAILED", "duration": 1.5},
        ]

        rows = generator._extract_table_data(data, ["test_name", "status", "duration"])

        assert len(rows) == 2
        assert rows[0][0] == "test1"
        assert rows[0][1] == "PASSED"
        assert rows[0][2] == "1.0"

    def test_extract_table_data_pytest_results(self):
        """Test extracting table data from pytest results format"""
        generator = TableGenerator()

        data = {
            "test_results": {"total_tests": 4, "passed_tests": 3, "failed_tests": 1},
            "details": [
                {"test": "test1", "status": "PASSED", "duration": 0.5},
                {"test": "test2", "status": "FAILED", "duration": 0.8},
            ],
        }

        rows = generator._extract_table_data(data, ["test", "status", "duration"])

        assert len(rows) == 2
        assert rows[0][0] == "test1"
        assert rows[0][1] == "PASSED"
        assert rows[0][2] == "0.5"

    def test_invalid_format(self, temp_dir):
        """Test handling invalid table format"""
        generator = TableGenerator()

        output_file = temp_dir / "table.txt"

        result = generator.create_table(
            data={},
            columns=["test_name"],
            output_file=str(output_file),
            format="invalid",
        )

        assert result["success"] is False
        assert "error" in result
