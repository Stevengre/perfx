#!/usr/bin/env python3
"""
Pytest output parser for perfx
Parses pytest output to extract test durations and results
"""
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from perfx.parsers.base import BaseParser


@dataclass
class TestResult:
    """Individual test result"""
    test_id: str
    status: str  # 'PASSED', 'FAILED', 'SKIPPED', 'ERROR'
    duration: Optional[float] = None
    error_message: Optional[str] = None
    progress_percent: Optional[int] = None
    worker_id: Optional[str] = None


class PytestParser(BaseParser):
    """Parser for pytest output"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.test_results: List[TestResult] = []
        self.summary_stats: Dict[str, Any] = {}
        
    def parse_step_results(self, step_results: List[bool]) -> Dict[str, Any]:
        """Parse step results and return structured data"""
        return {
            "success": all(step_results),
            "total_commands": len(step_results),
            "successful_commands": sum(step_results),
            "failed_commands": len(step_results) - sum(step_results),
        }
    
    def parse_from_json_file(self, json_file_path: str) -> Dict[str, Any]:
        """
        Parse pytest results from a JSON file containing raw_stdout
        
        Args:
            json_file_path: Path to JSON file containing raw_stdout
            
        Returns:
            Dictionary containing parsed results
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract raw_stdout from the JSON file
        raw_stdout = data.get('raw_stdout', '')
        raw_stderr = data.get('raw_stderr', '')
        exit_code = data.get('exit_code', 0)
        
        # Parse the raw_stdout
        return self.parse(raw_stdout, raw_stderr, exit_code)
        
    def parse(self, stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        """
        Parse pytest output and extract test results and durations
        
        Args:
            stdout: Standard output from pytest
            stderr: Standard error from pytest
            exit_code: Exit code from pytest
            
        Returns:
            Dictionary containing parsed results
        """
        self.test_results = []
        self.summary_stats = {}
        
        # Parse test results from stdout
        self._parse_test_results(stdout)
        
        # Parse summary statistics
        self._parse_summary_stats(stdout)
        
        # Determine overall success
        success = exit_code == 0
        
        return {
            "success": success,
            "exit_code": exit_code,
            "test_results": [self._test_result_to_dict(result) for result in self.test_results],
            "summary_stats": self.summary_stats,
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r.status == "PASSED"]),
            "failed_tests": len([r for r in self.test_results if r.status == "FAILED"]),
            "skipped_tests": len([r for r in self.test_results if r.status == "SKIPPED"]),
            "error_tests": len([r for r in self.test_results if r.status == "ERROR"]),
            "total_duration": sum(r.duration or 0 for r in self.test_results),
            "raw_stdout": stdout,
            "raw_stderr": stderr
        }
    
    def _parse_test_results(self, stdout: str):
        """Parse individual test results from pytest output"""
        lines = stdout.split('\n')
        
        # First, parse the "slowest durations" section to get actual test durations
        duration_map = self._parse_slowest_durations(stdout)
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Pattern 1: Modern pytest output with worker info and progress
            # Examples:
            # [gw6] [  1%] PASSED src/tests/integration/test_prove.py::test_prove_summaries[SAR-SUMMARY] 
            # [gw2] [ 42%] FAILED src/tests/integration/test_prove.py::test_prove_summaries[RETURN-SUMMARY] 
            test_pattern_modern = r'\[(gw\d+)\]\s+\[\s*(\d+)%\]\s+(PASSED|FAILED|SKIPPED|ERROR)\s+(.+)'
            match = re.search(test_pattern_modern, line)
            
            if match:
                worker_id = match.group(1)
                progress_percent = int(match.group(2))
                status = match.group(3)
                test_path = match.group(4).strip()
            else:
                # Pattern 2: Simple pytest output format
                # Examples:
                # test_example.py::test_function1 PASSED                           [ 25%]
                # test_example.py::test_function4 FAILED                           [100%]
                # test_example.py::test_function1 passed                           [ 50%]
                # test_example.py::test_function4 failed                           [100%]
                test_pattern_simple = r'(.+?)\s+(PASSED|FAILED|SKIPPED|ERROR|passed|failed|skipped|error)\s+\[.*?\]'
                match = re.search(test_pattern_simple, line)
                
                if match:
                    test_path = match.group(1).strip()
                    status = match.group(2).upper()  # Convert to uppercase for consistency
                    worker_id = None
                    progress_percent = None
                else:
                    continue
            
            # Extract test name and parameter from path
            # src/tests/integration/test_prove.py::test_prove_summaries[SAR-SUMMARY]
            # test_example.py::test_function1
            test_parts = test_path.split('::')
            if len(test_parts) >= 2:
                test_name = test_parts[1]  # test_prove_summaries[SAR-SUMMARY] or test_function1
                
                # Use the full test path as test_id instead of just the parameter
                # This includes the file path and function name
                test_id = test_path
            else:
                test_id = test_path
            
            # Look for duration information
            duration = None
            error_message = None
            
            # First, check if we have duration from the "slowest durations" section
            if test_id in duration_map:
                duration = duration_map[test_id]
            else:
                # Check if there's duration info in the same line
                duration_match = re.search(r'(\d+\.?\d*)s', line)
                if duration_match:
                    duration = float(duration_match.group(1))
            
            # For failed tests, look for error messages in "short test summary info" section
            if status in ["FAILED", "ERROR"]:
                error_message = self._extract_error_message(lines, i, test_id)
            
            test_result = TestResult(
                test_id=test_id,
                status=status,
                duration=duration,
                error_message=error_message,
                progress_percent=progress_percent,
                worker_id=worker_id
            )
            self.test_results.append(test_result)
    
    def _parse_slowest_durations(self, stdout: str) -> Dict[str, float]:
        """Parse the 'slowest durations' section from pytest output"""
        duration_map = {}
        
        # Look for the "slowest durations" section
        lines = stdout.split('\n')
        in_slowest_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check if we're entering the slowest durations section
            if "slowest durations" in line:
                in_slowest_section = True
                continue
            
            # Check if we're leaving the section (usually ends with ===)
            if in_slowest_section and line.startswith('==='):
                break
            
            # Parse duration lines in the slowest durations section
            if in_slowest_section and line:
                # Pattern: "1239.98s call     repositories/evm-semantics/kevm-pyk/src/tests/integration/test_prove.py::test_prove_summaries[SLOAD-SUMMARY]"
                # Updated pattern to handle multiple spaces between "call" and the test path
                duration_pattern = r'(\d+\.?\d*)s\s+call\s+(.+)'
                match = re.search(duration_pattern, line)
                
                if match:
                    duration = float(match.group(1))
                    full_test_path = match.group(2).strip()
                    
                    # Extract the relative path from the full path
                    # From: "repositories/evm-semantics/kevm-pyk/src/tests/integration/test_prove.py::test_prove_summaries[SLOAD-SUMMARY]"
                    # To: "src/tests/integration/test_prove.py::test_prove_summaries[SLOAD-SUMMARY]"
                    if 'src/tests/' in full_test_path:
                        relative_path = full_test_path.split('src/tests/')[1]
                        test_path = f"src/tests/{relative_path}"
                    else:
                        test_path = full_test_path
                    
                    duration_map[test_path] = duration
        
        return duration_map
    
    def _extract_error_message(self, lines: List[str], line_index: int, test_id: str) -> Optional[str]:
        """Extract error message from "short test summary info" section"""
        # Find "short test summary info" section
        for i in range(len(lines)):
            line = lines[i].strip()
            if "short test summary info" in line:
                # Look for corresponding failed test in this section
                for j in range(i + 1, len(lines)):
                    summary_line = lines[j].strip()
                    if summary_line.startswith('==='):
                        break
                    # Look for test_id in the FAILED line
                    if summary_line.startswith('FAILED') and test_id in summary_line:
                        # Found corresponding failed test, extract error message
                        # Format: FAILED test_path - error_message
                        error_lines = [summary_line]
                        # Continue looking for subsequent error details (may span multiple lines)
                        for k in range(j + 1, len(lines)):
                            detail_line = lines[k].strip()
                            if detail_line.startswith('===') or detail_line.startswith('FAILED'):
                                break
                            if detail_line:
                                error_lines.append(detail_line)
                        return '\n'.join(error_lines)
                break
        
        return None
    
    def _parse_summary_stats(self, stdout: str):
        """Parse summary statistics from pytest output"""
        # Look for summary lines like:
        # ================== 6 failed, 64 passed in 5681.63s (1:34:41) ==================
        summary_pattern = r'=+\s+(\d+)\s+failed[,\s]+(\d+)\s+passed[,\s]+in\s+(\d+\.?\d*)s?\s+\(([^)]+)\)\s+=+'
        
        lines = stdout.split('\n')
        for line in lines:
            match = re.search(summary_pattern, line)
            if match:
                failed_count = int(match.group(1))
                passed_count = int(match.group(2))
                total_duration = float(match.group(3))
                time_str = match.group(4)  # e.g., "1:34:41"
                
                self.summary_stats = {
                    "passed": passed_count,
                    "failed": failed_count,
                    "skipped": 0,  # Not shown in this format
                    "total_duration": total_duration,
                    "time_string": time_str
                }
                break
        
        # If no summary found, calculate from test results
        if not self.summary_stats:
            self.summary_stats = {
                "passed": len([r for r in self.test_results if r.status == "PASSED"]),
                "failed": len([r for r in self.test_results if r.status == "FAILED"]),
                "skipped": len([r for r in self.test_results if r.status == "SKIPPED"]),
                "total_duration": sum(r.duration or 0 for r in self.test_results)
            }
    
    def _test_result_to_dict(self, result: TestResult) -> Dict[str, Any]:
        """Convert TestResult to dictionary"""
        return {
            "test_id": result.test_id,
            "status": result.status,
            "duration": result.duration,
            "error_message": result.error_message
        }
    
    def get_test_durations(self) -> Dict[str, float]:
        """Get dictionary of test_id -> duration"""
        return {result.test_id: result.duration for result in self.test_results if result.duration is not None}
    
    def get_failed_tests(self) -> List[TestResult]:
        """Get list of failed tests"""
        return [result for result in self.test_results if result.status in ["FAILED", "ERROR"]] 