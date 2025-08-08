#!/usr/bin/env python3
"""
LaTeX Table Generator
Used to generate academic paper-level LaTeX tables from JSON data
"""

import os
import json
from typing import Dict, Any, List
from pathlib import Path
from rich.console import Console

console = Console()

class LatexTableGenerator:
    """Generic LaTeX table generator, not dependent on specific projects"""
    
    def __init__(self):
        self.console = Console()
    
    def generate_generic_table(self, json_file_path: str, output_path: str, table_config: Dict[str, Any]) -> bool:
        """
        Generate generic LaTeX table
        
        Args:
            json_file_path: Input JSON file path
            output_path: Output LaTeX file path
            table_config: Table configuration
            
        Returns:
            Whether generation was successful
        """
        try:
            # Read JSON data
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Generate LaTeX content
            latex_content = self._generate_generic_latex(data, table_config)
            
            # Save file
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            self.console.print(f"[green]✓ LaTeX table generated: {output_path}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]✗ Failed to generate LaTeX table: {e}[/red]")
            return False
    
    def _generate_generic_latex(self, data: Dict[str, Any], table_config: Dict[str, Any]) -> str:
        """Generate generic LaTeX table content"""
        
        # Extract configuration
        title = table_config.get('title', 'Generated Table')
        data_path = table_config.get('data_path', '')
        columns = table_config.get('columns', [])
        
        # Extract data
        if data_path:
            table_data = self._extract_data_by_path(data, data_path)
        else:
            table_data = data
        
        if not table_data:
            return f"% Error: No data found at path '{data_path}'"
        
        if not columns:
            return f"% Error: No columns defined for table '{table_config.get('name', 'unknown')}'"
        
        # Generate LaTeX table
        latex_lines = [
            "\\begin{table}[htbp]",
            "\\centering",
            f"\\caption{{{title}}}",
            f"\\label{{tab:{table_config.get('name', 'table')}}}",
        ]
        
        # Table format
        col_format = "|" + "|".join(["c"] * len(columns)) + "|"
        latex_lines.append(f"\\begin{{tabular}}{{{col_format}}}")
        latex_lines.append("\\hline")
        
        # Table header
        headers = [col["header"] for col in columns]
        latex_lines.append(" & ".join(headers) + " \\\\")
        latex_lines.append("\\hline")
        
        # Table data
        if isinstance(table_data, dict):
            # Dictionary data: each row is a key-value pair
            for key, item in table_data.items():
                if isinstance(item, dict):
                    row_data = []
                    for col in columns:
                        field = col["field"]
                        value = item.get(field, "")
                        formatted_value = self._format_value(value, col.get("format", "text"))
                        row_data.append(formatted_value)
                    latex_lines.append(" & ".join(row_data) + " \\\\")
                else:
                    # Simple key-value pair
                    row_data = [str(key), self._format_value(item, columns[1].get("format", "text"))]
                    latex_lines.append(" & ".join(row_data) + " \\\\")
        
        elif isinstance(table_data, list):
            # List data: each row is an object
            for item in table_data:
                if isinstance(item, dict):
                    row_data = []
                    for col in columns:
                        field = col["field"]
                        value = item.get(field, "")
                        formatted_value = self._format_value(value, col.get("format", "text"))
                        row_data.append(formatted_value)
                    latex_lines.append(" & ".join(row_data) + " \\\\")
        
        latex_lines.append("\\hline")
        latex_lines.append("\\end{tabular}")
        latex_lines.append("\\end{table}")
        
        return "\n".join(latex_lines)
    
    def _extract_data_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """Extract data by path"""
        if not path:
            return data
        
        current = data
        for key in path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _format_value(self, value: Any, format_type: str) -> str:
        """格式化值"""
        if value is None:
            return "N/A"
        
        try:
            if format_type == "integer":
                return str(int(value))
            elif format_type == "float_2":
                return f"{float(value):.2f}"
            elif format_type == "percentage":
                if isinstance(value, (int, float)):
                    return f"{value:.1f}%"
                else:
                    return str(value)
            elif format_type == "text":
                return str(value)
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)


def generate_latex_table(json_file: str, output_file: str, table_config: Dict[str, Any]) -> bool:
    """
    生成LaTeX表格的便捷函数
    
    Args:
        json_file: 输入JSON文件路径
        output_file: 输出LaTeX文件路径
        table_config: 表格配置
        
    Returns:
        是否成功生成
    """
    generator = LatexTableGenerator()
    return generator.generate_generic_table(json_file, output_file, table_config) 