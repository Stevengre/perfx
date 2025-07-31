#!/usr/bin/env python3
"""
LaTeX 表格生成器
用于从 JSON 数据生成学术论文级别的 LaTeX 表格
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

console = Console()


class LatexTableGenerator:
    """LaTeX 表格生成器"""
    
    def __init__(self):
        self.console = Console()
    
    def generate_opcode_summary_table(self, json_file_path: str, output_path: str) -> bool:
        """
        生成 EVM Opcode 摘要化评估结果的 LaTeX 表格
        
        Args:
            json_file_path: JSON 数据文件路径
            output_path: 输出 LaTeX 文件路径
            
        Returns:
            是否成功生成
        """
        try:
            # 读取 JSON 数据
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 生成 LaTeX 内容
            latex_content = self._generate_opcode_summary_latex(data)
            
            # 保存文件
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            self.console.print(f"[green]✓ LaTeX 表格已生成: {output_path}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]✗ 生成 LaTeX 表格失败: {e}[/red]")
            return False
    
    def _generate_opcode_summary_latex(self, data: Dict[str, Any]) -> str:
        """生成 EVM Opcode 摘要化评估的 LaTeX 内容"""
        
        # 提取统计数据
        stats = data.get("statistics", {})
        overall = stats.get("overall", {})
        by_category = stats.get("by_category", {})
        by_summary_status = stats.get("by_summary_status", {})
        performance = stats.get("performance_metrics", {})
        
        latex_content = []
        
        # 添加文档头部
        latex_content.append(r"""\documentclass{article}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{array}
\usepackage{siunitx}
\usepackage{graphicx}
\usepackage{geometry}

\geometry{margin=1in}

\begin{document}

\title{EVM Opcode Summarization Evaluation Results}
\author{Automated Evaluation Report}
\date{""" + data.get("metadata", {}).get("timestamp", "Generated") + r"""}

\maketitle

""")
        
        # 1. 总体统计表格
        latex_content.append(self._generate_overall_stats_table(overall))
        
        # 2. 按分类统计表格
        latex_content.append(self._generate_category_stats_table(by_category))
        
        # 3. 按摘要状态统计表格
        latex_content.append(self._generate_summary_status_table(by_summary_status))
        
        # 4. 性能指标表格
        latex_content.append(self._generate_performance_table(performance))
        
        # 5. 详细结果表格（前20个）
        results = data.get("results", [])
        if results:
            latex_content.append(self._generate_detailed_results_table(results[:20]))
        
        # 文档结尾
        latex_content.append(r"""
\end{document}
""")
        
        return "\n".join(latex_content)
    
    def _generate_overall_stats_table(self, overall: Dict[str, Any]) -> str:
        """生成总体统计表格"""
        return f"""
\\section{{Overall Statistics}}

\\begin{{table}}[h]
\\centering
\\begin{{tabular}}{{lr}}
\\toprule
\\textbf{{Metric}} & \\textbf{{Value}} \\\\
\\midrule
Total Opcodes & {overall.get('total_opcodes', 0)} \\\\
Successful & {overall.get('successful', 0)} \\\\
Failed & {overall.get('failed', 0)} \\\\
Skipped & {overall.get('skipped', 0)} \\\\
Success Rate & {overall.get('success_rate', 0):.2%} \\\\
Average Time & {overall.get('average_time', 0):.2f} s \\\\
Timeout Count & {overall.get('timeout_count', 0)} \\\\
Error Count & {overall.get('error_count', 0)} \\\\
\\bottomrule
\\end{{tabular}}
\\caption{{Overall evaluation statistics}}
\\label{{tab:overall-stats}}
\\end{{table}}
"""
    
    def _generate_category_stats_table(self, by_category: Dict[str, Any]) -> str:
        """生成按分类统计表格"""
        table_content = []
        table_content.append(r"""
\section{Statistics by Opcode Category}

\begin{table}[h]
\centering
\begin{tabular}{lrrrrr}
\toprule
\textbf{Category} & \textbf{Total} & \textbf{Success} & \textbf{Failed} & \textbf{Success Rate} & \textbf{Avg Time (s)} \\
\midrule
""")
        
        # 按成功率排序
        sorted_categories = sorted(
            by_category.items(),
            key=lambda x: x[1].get('success_rate', 0),
            reverse=True
        )
        
        for category, stats in sorted_categories:
            if stats.get('total', 0) > 0:
                table_content.append(
                    f"{category.replace('_', ' ').title()} & "
                    f"{stats.get('total', 0)} & "
                    f"{stats.get('successful', 0)} & "
                    f"{stats.get('failed', 0)} & "
                    f"{stats.get('success_rate', 0):.2%} & "
                    f"{stats.get('average_time', 0):.2f} \\\\"
                )
        
        table_content.append(r"""
\bottomrule
\end{tabular}
\caption{Evaluation results by opcode category}
\label{tab:category-stats}
\end{table}
""")
        
        return "\n".join(table_content)
    
    def _generate_summary_status_table(self, by_summary_status: Dict[str, Any]) -> str:
        """生成按摘要状态统计表格"""
        table_content = []
        table_content.append(r"""
\section{Statistics by Summary Status}

\begin{table}[h]
\centering
\begin{tabular}{lrrr}
\toprule
\textbf{Status} & \textbf{Total} & \textbf{Success} & \textbf{Success Rate} \\
\midrule
""")
        
        for status, stats in by_summary_status.items():
            if stats.get('total', 0) > 0:
                table_content.append(
                    f"{status.replace('_', ' ').title()} & "
                    f"{stats.get('total', 0)} & "
                    f"{stats.get('successful', 0)} & "
                    f"{stats.get('success_rate', 0):.2%} \\\\"
                )
        
        table_content.append(r"""
\bottomrule
\end{tabular}
\caption{Evaluation results by summary status}
\label{tab:summary-status-stats}
\end{table}
""")
        
        return "\n".join(table_content)
    
    def _generate_performance_table(self, performance: Dict[str, Any]) -> str:
        """生成性能指标表格"""
        table_content = []
        table_content.append(r"""
\section{Performance Metrics}

\begin{table}[h]
\centering
\begin{tabular}{llrr}
\toprule
\textbf{Metric} & \textbf{Opcode} & \textbf{Value} & \textbf{Category} \\
\midrule
""")
        
        # 最快 opcode
        fastest = performance.get('fastest_opcode')
        if fastest:
            table_content.append(
                f"Fastest & {fastest.get('opcode', 'N/A')} & "
                f"{fastest.get('time', 0):.3f} s & "
                f"{fastest.get('category', 'N/A').replace('_', ' ').title()} \\\\"
            )
        
        # 最慢 opcode
        slowest = performance.get('slowest_opcode')
        if slowest:
            table_content.append(
                f"Slowest & {slowest.get('opcode', 'N/A')} & "
                f"{slowest.get('time', 0):.3f} s & "
                f"{slowest.get('category', 'N/A').replace('_', ' ').title()} \\\\"
            )
        
        # 最多重写步骤
        most_steps = performance.get('most_rewriting_steps')
        if most_steps:
            table_content.append(
                f"Most Steps & {most_steps.get('opcode', 'N/A')} & "
                f"{most_steps.get('steps', 0)} & "
                f"{most_steps.get('category', 'N/A').replace('_', ' ').title()} \\\\"
            )
        
        # 最少重写步骤
        least_steps = performance.get('least_rewriting_steps')
        if least_steps:
            table_content.append(
                f"Least Steps & {least_steps.get('opcode', 'N/A')} & "
                f"{least_steps.get('steps', 0)} & "
                f"{least_steps.get('category', 'N/A').replace('_', ' ').title()} \\\\"
            )
        
        table_content.append(r"""
\bottomrule
\end{tabular}
\caption{Performance metrics for opcode evaluation}
\label{tab:performance-metrics}
\end{table}
""")
        
        return "\n".join(table_content)
    
    def _generate_detailed_results_table(self, results: List[Dict[str, Any]]) -> str:
        """生成详细结果表格"""
        table_content = []
        table_content.append(r"""
\section{Detailed Results (First 20 Opcodes)}

\begin{table}[h]
\centering
\begin{tabular}{lllrrl}
\toprule
\textbf{Opcode} & \textbf{Category} & \textbf{Status} & \textbf{Time (s)} & \textbf{Steps} & \textbf{Summary Status} \\
\midrule
""")
        
        for result in results:
            opcode = result.get('opcode', 'N/A')
            category = result.get('category', 'N/A').replace('_', ' ').title()
            success = "✓" if result.get('success', False) else "✗"
            time_taken = f"{result.get('time', 0):.3f}" if result.get('time') else "N/A"
            steps = sum(result.get('rewriting_steps', [])) if result.get('rewriting_steps') else 0
            summary_status = result.get('summary_status', 'N/A')
            
            table_content.append(
                f"{opcode} & {category} & {success} & {time_taken} & {steps} & {summary_status} \\\\"
            )
        
        table_content.append(r"""
\bottomrule
\end{tabular}
\caption{Detailed evaluation results for first 20 opcodes}
\label{tab:detailed-results}
\end{table}
""")
        
        return "\n".join(table_content)
    
    def generate_custom_table(self, json_file_path: str, output_path: str, 
                             table_config: Dict[str, Any]) -> bool:
        """
        生成自定义 LaTeX 表格
        
        Args:
            json_file_path: JSON 数据文件路径
            output_path: 输出 LaTeX 文件路径
            table_config: 表格配置
            
        Returns:
            是否成功生成
        """
        try:
            # 读取 JSON 数据
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 生成自定义表格
            latex_content = self._generate_custom_latex_table(data, table_config)
            
            # 保存文件
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            self.console.print(f"[green]✓ 自定义 LaTeX 表格已生成: {output_path}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]✗ 生成自定义 LaTeX 表格失败: {e}[/red]")
            return False
    
    def _generate_custom_latex_table(self, data: Dict[str, Any], 
                                   config: Dict[str, Any]) -> str:
        """生成自定义 LaTeX 表格"""
        # 这里可以根据配置生成不同类型的表格
        # 暂时返回一个简单的表格
        return r"""
\documentclass{article}
\usepackage{booktabs}
\usepackage{array}

\begin{document}

\section{Custom Table}

\begin{table}[h]
\centering
\begin{tabular}{lr}
\toprule
\textbf{Field} & \textbf{Value} \\
\midrule
Total & """ + str(data.get("summary", {}).get("total", 0)) + r""" \\
Success & """ + str(data.get("summary", {}).get("successful", 0)) + r""" \\
\bottomrule
\end{tabular}
\caption{Custom evaluation table}
\label{tab:custom}
\end{table}

\end{document}
"""


def generate_latex_table(json_file: str, output_file: str, 
                        table_type: str = "opcode_summary") -> bool:
    """
    便捷函数：生成 LaTeX 表格
    
    Args:
        json_file: JSON 数据文件路径
        output_file: 输出 LaTeX 文件路径
        table_type: 表格类型 ("opcode_summary" 或 "custom")
        
    Returns:
        是否成功生成
    """
    generator = LatexTableGenerator()
    
    if table_type == "opcode_summary":
        return generator.generate_opcode_summary_table(json_file, output_file)
    elif table_type == "custom":
        return generator.generate_custom_table(json_file, output_file, {})
    else:
        console.print(f"[red]✗ 未知的表格类型: {table_type}[/red]")
        return False 