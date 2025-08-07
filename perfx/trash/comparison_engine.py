#!/usr/bin/env python3
"""
Configuration-driven comparison engine
配置驱动的比较引擎
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from rich.console import Console

from .comparison_config import ComparisonConfig, ComparisonPair, ChartConfig
from .academic_charts import AcademicChartGenerator
from .latex_tables import LatexTableGenerator


class ComparisonEngine:
    """配置驱动的比较引擎"""
    
    def __init__(self, data_dir: str = "results/data", output_dir: str = "results/analysis"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.console = Console()
        
        # 初始化生成器
        self.chart_generator = AcademicChartGenerator(str(self.output_dir / "charts"))
        self.table_generator = LatexTableGenerator()
        
        # 确保输出目录存在
        (self.output_dir / "charts").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "tables").mkdir(parents=True, exist_ok=True)
    
    def run_comparison(self, config: ComparisonConfig) -> Dict[str, List[str]]:
        """运行比较分析"""
        self.console.print(f"[bold blue]Running comparison: {config.name}[/bold blue]")
        
        generated_files = {
            'charts': [],
            'tables': []
        }
        
        # 处理每个比较对
        for pair in config.pairs:
            pair_results = self._process_comparison_pair(pair, config)
            generated_files['charts'].extend(pair_results['charts'])
            generated_files['tables'].extend(pair_results['tables'])
        
        return generated_files
    
    def _process_comparison_pair(self, pair: ComparisonPair, config: ComparisonConfig) -> Dict[str, List[str]]:
        """处理单个比较对"""
        self.console.print(f"[green]Processing comparison pair: {pair.name}[/green]")
        
        # 加载数据
        baseline_data = self._load_data_file(pair.baseline_file)
        comparison_data = self._load_data_file(pair.comparison_file)
        
        if not baseline_data or not comparison_data:
            self.console.print(f"[red]Failed to load data for {pair.name}[/red]")
            return {'charts': [], 'tables': []}
        
        # 提取比较数据
        baseline_metrics = self._extract_metrics(baseline_data, pair.metric_field)
        comparison_metrics = self._extract_metrics(comparison_data, pair.metric_field)
        
        generated_files = {'charts': [], 'tables': []}
        
        # 生成图表
        for chart_config in config.charts:
            chart_file = self._generate_chart(
                baseline_metrics, comparison_metrics, 
                pair, chart_config, config.output_dir
            )
            if chart_file:
                generated_files['charts'].append(chart_file)
        
        # 生成表格
        table_file = self._generate_comparison_table(
            baseline_metrics, comparison_metrics, 
            pair, config.output_dir
        )
        if table_file:
            generated_files['tables'].append(table_file)
        
        return generated_files
    
    def _load_data_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """加载数据文件"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            self.console.print(f"[yellow]Warning: {file_path} not found[/yellow]")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.console.print(f"[red]Error loading {file_path}: {e}[/red]")
            return None
    
    def _extract_metrics(self, data: Dict[str, Any], metric_field: str) -> Dict[str, float]:
        """从数据中提取指标"""
        metrics = {}
        
        # 处理不同的数据格式
        if 'test_results' in data:
            # pytest格式
            for test in data['test_results']:
                test_id = test.get('test_id', test.get('name', 'Unknown'))
                metric_value = test.get(metric_field)
                if metric_value is not None:
                    metrics[test_id] = float(metric_value)
        
        elif 'results' in data:
            # 其他结果格式
            results = data['results']
            if isinstance(results, list):
                for result in results:
                    test_id = result.get('test_id', result.get('name', 'Unknown'))
                    metric_value = result.get(metric_field)
                    if metric_value is not None:
                        metrics[test_id] = float(metric_value)
            elif isinstance(results, dict):
                for test_id, result in results.items():
                    if isinstance(result, dict):
                        metric_value = result.get(metric_field)
                    else:
                        metric_value = result
                    if metric_value is not None:
                        metrics[test_id] = float(metric_value)
        
        return metrics
    
    def _generate_chart(self, baseline_metrics: Dict[str, float], 
                       comparison_metrics: Dict[str, float],
                       pair: ComparisonPair, chart_config: ChartConfig,
                       output_dir: str) -> Optional[str]:
        """生成图表"""
        if not baseline_metrics or not comparison_metrics:
            return None
        
        output_file = Path(output_dir) / "charts" / f"{pair.name}_{chart_config.output_name}.pdf"
        
        try:
            if chart_config.chart_type == "bar":
                return self.chart_generator.generate_performance_comparison_chart(
                    baseline_metrics, comparison_metrics,
                    title=chart_config.title,
                    output_name=f"{pair.name}_{chart_config.output_name}"
                )
            
            elif chart_config.chart_type == "box":
                return self._generate_box_plot(
                    baseline_metrics, comparison_metrics,
                    pair, chart_config, str(output_file)
                )
            
            elif chart_config.chart_type == "scatter":
                return self._generate_scatter_plot(
                    baseline_metrics, comparison_metrics,
                    pair, chart_config, str(output_file)
                )
            
        except Exception as e:
            self.console.print(f"[red]Error generating chart {chart_config.output_name}: {e}[/red]")
            return None
        
        return None
    
    def _generate_box_plot(self, baseline_metrics: Dict[str, float],
                          comparison_metrics: Dict[str, float],
                          pair: ComparisonPair, chart_config: ChartConfig,
                          output_file: str) -> str:
        """生成箱线图"""
        import matplotlib.pyplot as plt
        
        # 找到共同的测试用例
        common_tests = set(baseline_metrics.keys()) & set(comparison_metrics.keys())
        if not common_tests:
            return ""
        
        baseline_values = [baseline_metrics[test] for test in common_tests]
        comparison_values = [comparison_metrics[test] for test in common_tests]
        
        plt.figure(figsize=(chart_config.width, chart_config.height))
        plt.boxplot([baseline_values, comparison_values], 
                   labels=[pair.baseline_label, pair.comparison_label])
        plt.title(chart_config.title)
        plt.ylabel(chart_config.y_label)
        plt.grid(True, alpha=0.3)
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.savefig(output_file.replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        self.console.print(f"[green]✓ Box plot saved: {output_file}[/green]")
        return output_file
    
    def _generate_scatter_plot(self, baseline_metrics: Dict[str, float],
                              comparison_metrics: Dict[str, float],
                              pair: ComparisonPair, chart_config: ChartConfig,
                              output_file: str) -> str:
        """生成散点图"""
        import matplotlib.pyplot as plt
        
        # 找到共同的测试用例
        common_tests = set(baseline_metrics.keys()) & set(comparison_metrics.keys())
        if not common_tests:
            return ""
        
        x_values = [baseline_metrics[test] for test in common_tests]
        y_values = [comparison_metrics[test] for test in common_tests]
        
        plt.figure(figsize=(chart_config.width, chart_config.height))
        plt.scatter(x_values, y_values, alpha=0.6)
        
        # 添加对角线（相等线）
        max_val = max(max(x_values), max(y_values))
        plt.plot([0, max_val], [0, max_val], 'r--', alpha=0.8, label='Equal Performance')
        
        plt.xlabel(chart_config.x_label)
        plt.ylabel(chart_config.y_label)
        plt.title(chart_config.title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.savefig(output_file.replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        self.console.print(f"[green]✓ Scatter plot saved: {output_file}[/green]")
        return output_file
    
    def _generate_comparison_table(self, baseline_metrics: Dict[str, float],
                                  comparison_metrics: Dict[str, float],
                                  pair: ComparisonPair, output_dir: str) -> Optional[str]:
        """生成比较表格"""
        if not baseline_metrics or not comparison_metrics:
            return None
        
        output_file = Path(output_dir) / "tables" / f"{pair.name}_comparison.tex"
        
        try:
            # 使用现有的LaTeX表格生成器
            success = self.table_generator.generate_performance_comparison_table(
                baseline_metrics, comparison_metrics,
                str(output_file),
                baseline_label=pair.baseline_label,
                comparison_label=pair.comparison_label
            )
            
            if success:
                self.console.print(f"[green]✓ Comparison table saved: {output_file}[/green]")
                return str(output_file)
        
        except Exception as e:
            self.console.print(f"[red]Error generating comparison table: {e}[/red]")
        
        return None