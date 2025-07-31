#!/usr/bin/env python3
"""
Enhanced parsers for EVM evaluation
"""

import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from .base import BaseParser


class EnhancedSummarizeParser(BaseParser):
    """Enhanced parser for summarization evaluation results"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.opcode_categories = config.get("opcode_categories", {})
        self.skip_opcodes = config.get("skip_opcodes", [])
        self.include_only = config.get("include_only", [])
    
    def parse_step_results(self, results: List[bool]) -> Dict[str, Any]:
        """Parse summarization evaluation results"""
        parsed_results = {
            "total_opcodes": 0,
            "processed_opcodes": 0,
            "summarized_opcodes": 0,
            "failed_opcodes": 0,
            "skipped_opcodes": 0,
            "category_breakdown": {},
            "opcode_details": {}
        }
        
        # Parse opcode list
        opcode_list_file = Path("evaluation_results/opcode_list.txt")
        if opcode_list_file.exists():
            with open(opcode_list_file, 'r') as f:
                content = f.read()
                total_match = re.search(r'Total opcodes: (\d+)', content)
                if total_match:
                    parsed_results["total_opcodes"] = int(total_match.group(1))
                
                available_match = re.search(r'Available opcodes: (.+)', content)
                if available_match:
                    available_opcodes = available_match.group(1).split()
                    parsed_results["available_opcodes"] = available_opcodes
        
        # Parse summarization results
        summarization_file = Path("evaluation_results/summarization_results.json")
        if summarization_file.exists():
            try:
                with open(summarization_file, 'r') as f:
                    summarization_data = json.load(f)
                
                for opcode, data in summarization_data.items():
                    if opcode in self.skip_opcodes:
                        parsed_results["skipped_opcodes"] += 1
                        continue
                    
                    if self.include_only and opcode not in self.include_only:
                        parsed_results["skipped_opcodes"] += 1
                        continue
                    
                    parsed_results["processed_opcodes"] += 1
                    parsed_results["opcode_details"][opcode] = data
                    
                    if data.get("summarized", False):
                        parsed_results["summarized_opcodes"] += 1
                    else:
                        parsed_results["failed_opcodes"] += 1
                    
                    # Category breakdown
                    category = self._get_opcode_category(opcode)
                    if category not in parsed_results["category_breakdown"]:
                        parsed_results["category_breakdown"][category] = {
                            "total": 0,
                            "summarized": 0,
                            "failed": 0
                        }
                    
                    parsed_results["category_breakdown"][category]["total"] += 1
                    if data.get("summarized", False):
                        parsed_results["category_breakdown"][category]["summarized"] += 1
                    else:
                        parsed_results["category_breakdown"][category]["failed"] += 1
                        
            except Exception as e:
                parsed_results["parse_error"] = str(e)
        
        return parsed_results
    
    def _get_opcode_category(self, opcode: str) -> str:
        """Get the category of an opcode"""
        for category, opcodes in self.opcode_categories.items():
            if opcode in opcodes:
                return category
        return "UNKNOWN"


class CategoryParser(BaseParser):
    """Parser for category analysis results"""
    
    def parse_step_results(self, results: List[bool]) -> Dict[str, Any]:
        """Parse category analysis results"""
        parsed_results = {
            "categories": {},
            "summary": {
                "total_categories": 0,
                "total_opcodes": 0,
                "total_summarized": 0,
                "total_failed": 0
            }
        }
        
        category_file = Path("evaluation_results/category_analysis.json")
        if category_file.exists():
            try:
                with open(category_file, 'r') as f:
                    category_data = json.load(f)
                
                for category, opcodes in category_data.items():
                    parsed_results["categories"][category] = {
                        "total": len(opcodes),
                        "summarized": 0,
                        "failed": 0,
                        "success_rate": 0.0,
                        "opcodes": {}
                    }
                    
                    for opcode, data in opcodes.items():
                        parsed_results["categories"][category]["opcodes"][opcode] = data
                        
                        if data.get("summarized", False):
                            parsed_results["categories"][category]["summarized"] += 1
                        else:
                            parsed_results["categories"][category]["failed"] += 1
                    
                    # Calculate success rate
                    total = parsed_results["categories"][category]["total"]
                    if total > 0:
                        success_rate = parsed_results["categories"][category]["summarized"] / total
                        parsed_results["categories"][category]["success_rate"] = success_rate
                
                # Calculate summary
                parsed_results["summary"]["total_categories"] = len(parsed_results["categories"])
                for category_data in parsed_results["categories"].values():
                    parsed_results["summary"]["total_opcodes"] += category_data["total"]
                    parsed_results["summary"]["total_summarized"] += category_data["summarized"]
                    parsed_results["summary"]["total_failed"] += category_data["failed"]
                    
            except Exception as e:
                parsed_results["parse_error"] = str(e)
        
        return parsed_results


class EnhancedPerformanceParser(BaseParser):
    """Enhanced parser for performance results with timing analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.timing_patterns = config.get("timing_patterns", [])
    
    def parse_step_results(self, results: List[bool]) -> Dict[str, Any]:
        """Parse performance results with detailed timing"""
        parsed_results = {
            "performance_data": {},
            "timing_analysis": {},
            "comparison": {}
        }
        
        # Parse timing patterns
        for pattern_config in self.timing_patterns:
            pattern = pattern_config.get("pattern", "")
            capture_groups = pattern_config.get("capture_groups", [])
            
            if pattern and capture_groups:
                parsed_results["timing_analysis"][capture_groups[0]] = self._extract_timing(pattern)
        
        # Parse performance files
        performance_files = [
            "concrete_original_performance.txt",
            "concrete_summary_performance.txt",
            "symbolic_original_performance.txt",
            "symbolic_summary_performance.txt"
        ]
        
        for file_name in performance_files:
            file_path = Path(f"evaluation_results/{file_name}")
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    parsed_results["performance_data"][file_name] = self._parse_performance_file(content)
        
        # Generate comparison data
        if "concrete_original_performance.txt" in parsed_results["performance_data"] and "concrete_summary_performance.txt" in parsed_results["performance_data"]:
            parsed_results["comparison"]["concrete"] = self._compare_performance(
                parsed_results["performance_data"]["concrete_original_performance.txt"],
                parsed_results["performance_data"]["concrete_summary_performance.txt"]
            )
        
        if "symbolic_original_performance.txt" in parsed_results["performance_data"] and "symbolic_summary_performance.txt" in parsed_results["performance_data"]:
            parsed_results["comparison"]["symbolic"] = self._compare_performance(
                parsed_results["performance_data"]["symbolic_original_performance.txt"],
                parsed_results["performance_data"]["symbolic_summary_performance.txt"]
            )
        
        return parsed_results
    
    def _extract_timing(self, pattern: str) -> Optional[str]:
        """Extract timing information using regex pattern"""
        # This would be implemented based on the actual output format
        return None
    
    def _parse_performance_file(self, content: str) -> Dict[str, Any]:
        """Parse performance file content"""
        return {
            "content": content,
            "lines": len(content.split('\n')),
            "has_timing": "real" in content and "user" in content and "sys" in content
        }
    
    def _compare_performance(self, original: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Compare original vs summary performance"""
        return {
            "original": original,
            "summary": summary,
            "improvement": "TBD"  # Would calculate actual improvement
        }


class AnalysisParser(BaseParser):
    """Parser for comprehensive analysis results"""
    
    def parse_step_results(self, results: List[bool]) -> Dict[str, Any]:
        """Parse comprehensive analysis results"""
        parsed_results = {
            "comprehensive_data": {},
            "summary": {},
            "recommendations": []
        }
        
        comprehensive_file = Path("evaluation_results/comprehensive_results.json")
        if comprehensive_file.exists():
            try:
                with open(comprehensive_file, 'r') as f:
                    comprehensive_data = json.load(f)
                
                parsed_results["comprehensive_data"] = comprehensive_data
                
                # Generate summary
                if "summarization_results.json" in comprehensive_data:
                    summarization = comprehensive_data["summarization_results.json"]
                    parsed_results["summary"]["total_opcodes"] = len(summarization)
                    parsed_results["summary"]["summarized_count"] = sum(
                        1 for data in summarization.values() if data.get("summarized", False)
                    )
                    parsed_results["summary"]["success_rate"] = (
                        parsed_results["summary"]["summarized_count"] / parsed_results["summary"]["total_opcodes"]
                        if parsed_results["summary"]["total_opcodes"] > 0 else 0
                    )
                
                # Generate recommendations
                if parsed_results["summary"].get("success_rate", 0) < 0.8:
                    parsed_results["recommendations"].append(
                        "Consider improving summarization coverage for better performance"
                    )
                
                if parsed_results["summary"].get("success_rate", 0) > 0.9:
                    parsed_results["recommendations"].append(
                        "Excellent summarization coverage achieved"
                    )
                    
            except Exception as e:
                parsed_results["parse_error"] = str(e)
        
        return parsed_results


class FileOperationsParser(BaseParser):
    """Parser for file operations tracking"""
    
    def parse_step_results(self, results: List[bool]) -> Dict[str, Any]:
        """Parse file operations results"""
        parsed_results = {
            "backups_created": 0,
            "files_modified": 0,
            "files_restored": 0,
            "operations_log": [],
            "backup_files": []
        }
        
        # Check backup directory
        backup_dir = Path("evaluation_results/backups")
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.py.*"))
            parsed_results["backups_created"] = len(backup_files)
            parsed_results["backup_files"] = [str(f.name) for f in backup_files]
        
        # Parse operations log
        setup_log = Path("evaluation_results/setup.log")
        if setup_log.exists():
            with open(setup_log, 'r') as f:
                content = f.read()
                parsed_results["operations_log"].append("Environment setup completed")
        
        return parsed_results 