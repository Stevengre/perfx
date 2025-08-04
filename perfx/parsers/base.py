#!/usr/bin/env python3
"""
Base parser classes for Perfx
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseParser(ABC):
    """Base class for all parsers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def parse_step_results(self, step_results: List[bool]) -> Dict[str, Any]:
        """Parse step results and return structured data"""
        pass

    @abstractmethod
    def parse(self, stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        """Parse command output and return structured data"""
        pass


class SimpleParser(BaseParser):
    """Simple parser for basic success/failure detection"""

    def parse_step_results(self, step_results: List[bool]) -> Dict[str, Any]:
        """Parse step results"""
        return {
            "success": all(step_results),
            "total_commands": len(step_results),
            "successful_commands": sum(step_results),
            "failed_commands": len(step_results) - sum(step_results),
        }

    def parse(self, stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        """Parse output using configured patterns"""
        success_patterns = self.config.get("success_patterns", [])
        error_patterns = self.config.get("error_patterns", [])

        # Search in both stdout and stderr
        success_found = any(
            re.search(pattern, stdout, re.IGNORECASE) for pattern in success_patterns
        ) or any(
            re.search(pattern, stderr, re.IGNORECASE) for pattern in success_patterns
        )
        error_found = any(
            re.search(pattern, stdout, re.IGNORECASE) for pattern in error_patterns
        ) or any(
            re.search(pattern, stderr, re.IGNORECASE) for pattern in error_patterns
        )

        # If no patterns are configured, only check exit_code
        if not success_patterns and not error_patterns:
            return {
                "success": exit_code == 0,
                "success_patterns_found": False,
                "error_patterns_found": False,
            }

        return {
            "success": success_found and not error_found and exit_code == 0,
            "success_patterns_found": success_found,
            "error_patterns_found": error_found,
        }


class PytestParser(BaseParser):
    """Parser for pytest output"""

    def parse_step_results(self, step_results: List[bool]) -> Dict[str, Any]:
        """Parse step results"""
        return {
            "success": all(step_results),
            "total_commands": len(step_results),
            "successful_commands": sum(step_results),
            "failed_commands": len(step_results) - sum(step_results),
        }

    def parse(self, stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        """Parse pytest output with duration information"""
        import re

        lines = stdout.split("\n")

        # Extract test results
        test_results = []
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        overall_duration = None

        # Dictionary to store test durations
        test_durations = {}

        for line in lines:
            # Extract overall duration from summary
            if "passed in" in line and "s" in line:
                # Look for pattern like "1 failed, 5 passed in 0.06s"
                duration_match = re.search(r"passed in ([\d.]+)s", line)
                if duration_match:
                    overall_duration = float(duration_match.group(1))

            # Parse test result line with dots and F (e.g., "..F..")
            if re.match(
                r"^[.FEs]+.*\[.*%\]$", line.strip()
            ) and not line.strip().startswith("("):
                # Count dots (passed), F (failed), E (error), s (skipped)
                result_chars = line.split()[0]
                # Only count if this looks like a test result line (not too many characters)
                if len(result_chars) <= 10:  # Reasonable number of test results
                    for char in result_chars:
                        if char == ".":
                            passed_tests += 1
                            total_tests += 1
                        elif char == "F":
                            failed_tests += 1
                            total_tests += 1
                        elif char == "E":
                            failed_tests += 1
                            total_tests += 1
                        elif char == "s":
                            skipped_tests += 1
                            total_tests += 1

            # Parse detailed test names from verbose output
            elif "::" in line and ("PASSED" in line or "passed" in line):
                # Extract test name from format like:
                # "../../../../../var/folders/.../tmpy5q03j7l.py::test_simple PASSED [ 16%]"
                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[1].split()[0]  # Get test function name
                    passed_tests += 1
                    total_tests += 1
                    test_results.append(
                        {"name": test_name, "status": "passed", "duration": None}
                    )

            elif "::" in line and ("FAILED" in line or "failed" in line):
                # Extract test name from format like:
                # "../../../../../var/folders/.../tmpy5q03j7l.py::test_failing FAILED [ 66%]"
                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[1].split()[0]  # Get test function name
                    failed_tests += 1
                    total_tests += 1
                    test_results.append(
                        {"name": test_name, "status": "failed", "duration": None}
                    )

            elif "::" in line and ("SKIPPED" in line or "skipped" in line):
                # Extract test name from format like:
                # "../../../../../var/folders/.../tmpy5q03j7l.py::test_skipped SKIPPED [ 83%]"
                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[1].split()[0]  # Get test function name
                    skipped_tests += 1
                    total_tests += 1
                    test_results.append(
                        {"name": test_name, "status": "skipped", "duration": None}
                    )

            # Parse test durations from slowest durations section
            elif "s call" in line and "::" in line:
                # Format: "0.00s call     tmp06_ejtmi.py::test_failing"
                duration_match = re.search(r"^([\d.]+)s call\s+.*::(\w+)", line)
                if duration_match:
                    duration = float(duration_match.group(1))
                    test_name = duration_match.group(2)
                    test_durations[test_name] = duration

        # Handle multi-line test results (where PASSED/FAILED might be split across lines)
        for i, line in enumerate(lines):
            if "::" in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                if "PASSED" in next_line or "passed" in next_line:
                    parts = line.split("::")
                    if len(parts) >= 2:
                        test_name = parts[1].split()[0]  # Get test function name
                        if not any(r["name"] == test_name for r in test_results):
                            passed_tests += 1
                            total_tests += 1
                            test_results.append(
                                {
                                    "name": test_name,
                                    "status": "passed",
                                    "duration": None,
                                }
                            )
                elif "FAILED" in next_line or "failed" in next_line:
                    parts = line.split("::")
                    if len(parts) >= 2:
                        test_name = parts[1].split()[0]  # Get test function name
                        if not any(r["name"] == test_name for r in test_results):
                            failed_tests += 1
                            total_tests += 1
                            test_results.append(
                                {
                                    "name": test_name,
                                    "status": "failed",
                                    "duration": None,
                                }
                            )

        # Handle lines where PASSED/FAILED is on the same line but might be split
        for line in lines:
            if "::" in line and ("PASSED" in line or "passed" in line):
                # Check if this test was already processed
                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[1].split()[0]  # Get test function name
                    if not any(r["name"] == test_name for r in test_results):
                        passed_tests += 1
                        total_tests += 1
                        test_results.append(
                            {"name": test_name, "status": "passed", "duration": None}
                        )
            elif "::" in line and ("FAILED" in line or "failed" in line):
                # Check if this test was already processed
                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[1].split()[0]  # Get test function name
                    if not any(r["name"] == test_name for r in test_results):
                        failed_tests += 1
                        total_tests += 1
                        test_results.append(
                            {"name": test_name, "status": "failed", "duration": None}
                        )

        # Update test results with durations
        for test_result in test_results:
            test_name = test_result["name"]
            if test_name in test_durations:
                test_result["duration"] = test_durations[test_name]

        return {
            "success": failed_tests == 0 and exit_code == 0,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "error_tests": 0,  # Not separately tracked in this simple parser
            "overall_duration": overall_duration,
            "test_durations": test_durations,
        }


class JsonParser(BaseParser):
    """Parser for JSON output"""

    def parse_step_results(self, step_results: List[bool]) -> Dict[str, Any]:
        """Parse step results"""
        return {
            "success": all(step_results),
            "total_commands": len(step_results),
            "successful_commands": sum(step_results),
            "failed_commands": len(step_results) - sum(step_results),
        }

    def parse(self, stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        """Parse JSON output"""
        import json

        try:
            data = json.loads(stdout)
            return {
                "success": exit_code == 0,
                "data": data,
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON",
                "data": None,
            }


class ParserFactory:
    """Factory for creating parser instances"""

    def __init__(self):
        self.parser_types = {
            "simple": SimpleParser,
            "pytest": PytestParser,
            "json": JsonParser,
        }
        
        # Try to register the enhanced pytest parser if available
        try:
            from .pytest import PytestParser as EnhancedPytestParser
            self.parser_types["pytest"] = EnhancedPytestParser
        except ImportError:
            pass  # Fall back to basic pytest parser

    def create_parser(self, config: Dict[str, Any]) -> BaseParser:
        """Create a parser instance based on configuration"""
        parser_type = config.get("type", "simple")

        if parser_type not in self.parser_types:
            raise ValueError(f"Unknown parser type: {parser_type}")

        parser_class = self.parser_types[parser_type]
        return parser_class(config)

    def register_parser(self, name: str, parser_class: type) -> None:
        """Register a new parser type"""
        if not issubclass(parser_class, BaseParser):
            raise ValueError("Parser class must inherit from BaseParser")

        self.parser_types[name] = parser_class
