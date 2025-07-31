"""
Tests for parser functionality
"""

import pytest

from perfx.parsers.base import (JsonParser, ParserFactory, PytestParser,
                                SimpleParser)


class TestSimpleParser:
    """Test cases for SimpleParser"""

    def test_parse_output_success(self):
        """Test parsing successful output"""
        config = {
            "type": "simple",
            "success_patterns": ["Hello, World!", "success"],
            "error_patterns": ["ERROR", "FAILED"],
        }

        parser = SimpleParser(config)
        output = "Hello, World!\nTest completed successfully"

        result = parser.parse_output(output)

        assert result["success"] is True
        assert result["success_patterns_found"] is True
        assert result["error_patterns_found"] is False

    def test_parse_output_error(self):
        """Test parsing error output"""
        config = {
            "type": "simple",
            "success_patterns": ["success"],
            "error_patterns": ["ERROR", "FAILED"],
        }

        parser = SimpleParser(config)
        output = "Something went wrong\nERROR: Build failed"

        result = parser.parse_output(output)

        assert result["success"] is False
        assert result["error_patterns_found"] is True

    def test_parse_output_no_patterns(self):
        """Test parsing output with no patterns matched"""
        config = {
            "type": "simple",
            "success_patterns": ["success"],
            "error_patterns": ["ERROR"],
        }

        parser = SimpleParser(config)
        output = "Some random output"

        result = parser.parse_output(output)

        assert result["success"] is False  # No success patterns found
        assert result["success_patterns_found"] is False
        assert result["error_patterns_found"] is False


class TestPytestParser:
    """Test cases for PytestParser"""

    def test_parse_output_success(self, mock_pytest_output):
        """Test parsing pytest output"""
        config = {"type": "pytest"}
        parser = PytestParser(config)

        result = parser.parse_output(mock_pytest_output)

        assert result["success"] is False  # One test failed
        assert result["total_tests"] == 4
        assert result["passed_tests"] == 3
        assert result["failed_tests"] == 1

    def test_parse_output_all_passed(self):
        """Test parsing pytest output with all tests passed"""
        output = """test_example.py::test_function1 passed                           [ 50%]
test_example.py::test_function2 passed                           [100%]

============================== 2 passed in 1.23s =============================="""

        config = {"type": "pytest"}
        parser = PytestParser(config)

        result = parser.parse_output(output)

        assert result["success"] is True
        assert result["total_tests"] == 2
        assert result["passed_tests"] == 2
        assert result["failed_tests"] == 0

    def test_parse_output_no_tests(self):
        """Test parsing pytest output with no tests"""
        output = "No tests found"

        config = {"type": "pytest"}
        parser = PytestParser(config)

        result = parser.parse_output(output)

        assert result["success"] is True  # No failed tests
        assert result["total_tests"] == 0
        assert result["passed_tests"] == 0
        assert result["failed_tests"] == 0


class TestJsonParser:
    """Test cases for JsonParser"""

    def test_parse_output_valid_json(self, mock_json_output):
        """Test parsing valid JSON output"""
        config = {"type": "json"}
        parser = JsonParser(config)

        result = parser.parse_output(mock_json_output)

        assert result["success"] is True
        assert result["data"]["results"]["total_tests"] == 4
        assert result["data"]["results"]["passed_tests"] == 3
        assert result["data"]["results"]["failed_tests"] == 1
        assert len(result["data"]["details"]) == 4

    def test_parse_output_invalid_json(self):
        """Test parsing invalid JSON output"""
        config = {"type": "json"}
        parser = JsonParser(config)

        invalid_json = "{ invalid json }"

        result = parser.parse_output(invalid_json)

        assert result["success"] is False
        assert "error" in result
        assert "JSON" in result["error"]


class TestParserFactory:
    """Test cases for ParserFactory"""

    def test_create_simple_parser(self):
        """Test creating a simple parser"""
        factory = ParserFactory()
        config = {"type": "simple"}

        parser = factory.create_parser(config)

        assert isinstance(parser, SimpleParser)

    def test_create_pytest_parser(self):
        """Test creating a pytest parser"""
        factory = ParserFactory()
        config = {"type": "pytest"}

        parser = factory.create_parser(config)

        assert isinstance(parser, PytestParser)

    def test_create_json_parser(self):
        """Test creating a JSON parser"""
        factory = ParserFactory()
        config = {"type": "json"}

        parser = factory.create_parser(config)

        assert isinstance(parser, JsonParser)

    def test_create_unknown_parser(self):
        """Test creating an unknown parser type"""
        factory = ParserFactory()
        config = {"type": "unknown"}

        with pytest.raises(ValueError):
            factory.create_parser(config)
