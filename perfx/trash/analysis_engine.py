#!/usr/bin/env python3
"""
General analysis engine for perfx
通用的分析引擎，支持配置驱动的数据分析和可视化
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console

from .comparison_engine import ComparisonEngine
from .comparison_config import ComparisonConfigManager
from .academic_charts import AcademicChartGenerator
from .latex_tables import LatexTableGenerator

console = Console()


class AnalysisEngine:
    """通用的分析引擎"""
    
    def __init__(self, data_dir: str = "results/data", output_dir: str = "results/analysis"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.console = Console()
        
        # 初始化生成器
        self.chart_generator = AcademicChartGenerator(str(self.output_dir / "charts"))
        self.table_generator = LatexTableGenerator()
        self.comparison_engine = ComparisonEngine(str(data_dir), str(output_dir))
        
        # 确保输出目录存在
        (self.output_dir / "charts").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "tables").mkdir(parents=True, exist_ok=True)
    
    def run_analysis(self, config_file: Optional[str] = None, 
                    steps: Optional[str] = None,
                    analysis_type: str = "all") -> Dict[str, List[str]]:
        """
        运行分析
        
        Args:
            config_file: 配置文件路径
            steps: 特定步骤（逗号分隔）
            analysis_type: 分析类型 ("charts", "tables", "comparison", "all")
        
        Returns:
            生成的文件列表
        """
        self.console.print("[bold blue]Starting analysis with perfx AnalysisEngine[/bold blue]")
        
        generated_files = {
            'charts': [],
            'tables': [],
            'reports': []
        }
        
        # 解析步骤
        step_list = []
        if steps:
            step_list = [s.strip() for s in steps.split(',')]
        
        # 运行不同类型的分析
        if analysis_type in ["charts", "all"]:
            chart_files = self.generate_charts(step_list)
            generated_files['charts'].extend(chart_files)
        
        if analysis_type in ["tables", "all"]:
            table_files = self.generate_tables(step_list)
            generated_files['tables'].extend(table_files)
        
        if analysis_type in ["comparison", "all"] and config_file:
            comparison_files = self.run_comparisons(config_file)
            generated_files['charts'].extend(comparison_files.get('charts', []))
            generated_files['tables'].extend(comparison_files.get('tables', []))
        
        return generated_files
    
    def generate_charts(self, steps: List[str] = None) -> List[str]:
        """生成图表"""
        self.console.print("[blue]Generating charts...[/blue]")
        generated_files = []
        
        # 查找所有可用的数据文件
        data_files = list(self.data_dir.glob("*.json"))
        
        for data_file in data_files:
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 根据数据类型生成相应的图表
                chart_files = self._generate_charts_for_data(data, data_file.stem)
                generated_files.extend(chart_files)
                
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to process {data_file.name}: {e}[/yellow]")
        
        return generated_files
    
    def generate_tables(self, steps: List[str] = None) -> List[str]:
        """生成表格"""
        self.console.print("[blue]Generating tables...[/blue]")
        generated_files = []
        
        # 查找所有可用的数据文件
        data_files = list(self.data_dir.glob("*.json"))
        
        for data_file in data_files:
            try:
                # 生成摘要表格
                output_file = self.output_dir / "tables" / f"{data_file.stem}_summary.tex"
                success = self.table_generator.generate_test_results_table(
                    str(data_file), str(output_file), title=f"{data_file.stem} Summary"
                )
                
                if success:
                    generated_files.append(str(output_file))
                    self.console.print(f"[green]✓ Generated table: {output_file.name}[/green]")
                
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to generate table for {data_file.name}: {e}[/yellow]")
        
        return generated_files
    
    def run_comparisons(self, config_file: str) -> Dict[str, List[str]]:
        """运行配置驱动的比较"""
        self.console.print("[blue]Running comparisons...[/blue]")
        
        try:
            config_manager = ComparisonConfigManager(config_file)
            total_generated = {'charts': [], 'tables': []}
            
            for comparison in config_manager.comparisons:
                results = self.comparison_engine.run_comparison(comparison)
                total_generated['charts'].extend(results.get('charts', []))
                total_generated['tables'].extend(results.get('tables', []))
            
            return total_generated
            
        except Exception as e:
            self.console.print(f"[red]Error running comparisons: {e}[/red]")
            return {'charts': [], 'tables': []}
    
    def _generate_charts_for_data(self, data: Dict[str, Any], data_name: str) -> List[str]:
        """为特定数据生成图表"""
        generated_files = []
        
        # 检查数据结构并生成相应的图表
        if 'test_results' in data:
            # pytest格式数据
            chart_files = self._generate_test_results_charts(data, data_name)
            generated_files.extend(chart_files)
        
        elif 'results' in data and isinstance(data['results'], list):
            # 结果列表格式
            chart_files = self._generate_results_list_charts(data, data_name)
            generated_files.extend(chart_files)
        
        return generated_files
    
    def _generate_test_results_charts(self, data: Dict[str, Any], data_name: str) -> List[str]:
        """为测试结果数据生成图表"""
        generated_files = []
        
        try:
            # 提取测试结果
            test_results = data['test_results']
            
            # 1. 状态分布饼图
            status_counts = {}
            durations = []
            
            for test in test_results:
                status = test.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                duration = test.get('duration')
                if duration is not None:
                    durations.append(duration)
            
            if status_counts:
                chart_file = self._generate_status_pie_chart(status_counts, data_name)
                if chart_file:
                    generated_files.append(chart_file)
            
            # 2. 执行时间分布直方图
            if durations:
                chart_file = self._generate_duration_histogram(durations, data_name)
                if chart_file:
                    generated_files.append(chart_file)
        
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to generate test results charts for {data_name}: {e}[/yellow]")
        
        return generated_files
    
    def _generate_results_list_charts(self, data: Dict[str, Any], data_name: str) -> List[str]:
        """为结果列表数据生成图表"""
        generated_files = []
        
        try:
            results = data['results']
            
            # 分析结果数据
            success_counts = {'successful': 0, 'failed': 0, 'skipped': 0}
            times = []
            
            for result in results:
                success = result.get('success', False)
                error = result.get('error')
                time_taken = result.get('time')
                
                if error == "SKIPPED":
                    success_counts['skipped'] += 1
                elif success:
                    success_counts['successful'] += 1
                else:
                    success_counts['failed'] += 1
                
                if time_taken is not None:
                    times.append(time_taken)
            
            # 生成成功率图表
            if any(success_counts.values()):
                chart_file = self._generate_success_rate_chart(success_counts, data_name)
                if chart_file:
                    generated_files.append(chart_file)
            
            # 生成时间分布图表
            if times:
                chart_file = self._generate_time_distribution_chart(times, data_name)
                if chart_file:
                    generated_files.append(chart_file)
        
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to generate results list charts for {data_name}: {e}[/yellow]")
        
        return generated_files
    
    def _generate_status_pie_chart(self, status_counts: Dict[str, int], data_name: str) -> Optional[str]:
        """生成状态分布饼图"""
        import matplotlib.pyplot as plt
        
        output_file = self.output_dir / "charts" / f"{data_name}_status_distribution.pdf"
        
        try:
            plt.figure(figsize=(10, 8))
            plt.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%', startangle=90)
            plt.title(f'{data_name} - Test Status Distribution')
            plt.axis('equal')
            
            plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
            plt.savefig(str(output_file).replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
            plt.close()
            
            self.console.print(f"[green]✓ Status distribution chart: {output_file.name}[/green]")
            return str(output_file)
        
        except Exception as e:
            self.console.print(f"[red]Error generating status pie chart: {e}[/red]")
            return None
    
    def _generate_duration_histogram(self, durations: List[float], data_name: str) -> Optional[str]:
        """生成执行时间分布直方图"""
        import matplotlib.pyplot as plt
        import numpy as np
        
        output_file = self.output_dir / "charts" / f"{data_name}_duration_distribution.pdf"
        
        try:
            plt.figure(figsize=(12, 6))
            plt.hist(durations, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            plt.xlabel('Duration (seconds)')
            plt.ylabel('Frequency')
            plt.title(f'{data_name} - Execution Time Distribution')
            plt.grid(True, alpha=0.3)
            
            # 添加统计信息
            mean_duration = np.mean(durations)
            median_duration = np.median(durations)
            plt.axvline(mean_duration, color='red', linestyle='--', alpha=0.8, label=f'Mean: {mean_duration:.2f}s')
            plt.axvline(median_duration, color='orange', linestyle='--', alpha=0.8, label=f'Median: {median_duration:.2f}s')
            plt.legend()
            
            plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
            plt.savefig(str(output_file).replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
            plt.close()
            
            self.console.print(f"[green]✓ Duration histogram: {output_file.name}[/green]")
            return str(output_file)
        
        except Exception as e:
            self.console.print(f"[red]Error generating duration histogram: {e}[/red]")
            return None
    
    def _generate_success_rate_chart(self, success_counts: Dict[str, int], data_name: str) -> Optional[str]:
        """生成成功率图表"""
        import matplotlib.pyplot as plt
        
        output_file = self.output_dir / "charts" / f"{data_name}_success_rate.pdf"
        
        try:
            plt.figure(figsize=(10, 6))
            bars = plt.bar(success_counts.keys(), success_counts.values(), alpha=0.7, color=['green', 'red', 'orange'])
            plt.ylabel('Count')
            plt.title(f'{data_name} - Success Rate Analysis')
            plt.grid(True, alpha=0.3, axis='y')
            
            # 添加数值标签
            for bar, count in zip(bars, success_counts.values()):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{count}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
            plt.savefig(str(output_file).replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
            plt.close()
            
            self.console.print(f"[green]✓ Success rate chart: {output_file.name}[/green]")
            return str(output_file)
        
        except Exception as e:
            self.console.print(f"[red]Error generating success rate chart: {e}[/red]")
            return None
    
    def _generate_time_distribution_chart(self, times: List[float], data_name: str) -> Optional[str]:
        """生成时间分布图表"""
        import matplotlib.pyplot as plt
        import numpy as np
        
        output_file = self.output_dir / "charts" / f"{data_name}_time_distribution.pdf"
        
        try:
            plt.figure(figsize=(12, 6))
            plt.hist(times, bins=30, alpha=0.7, color='lightblue', edgecolor='black')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Frequency')
            plt.title(f'{data_name} - Time Distribution')
            plt.grid(True, alpha=0.3)
            
            # 添加统计信息
            mean_time = np.mean(times)
            median_time = np.median(times)
            plt.axvline(mean_time, color='red', linestyle='--', alpha=0.8, label=f'Mean: {mean_time:.2f}s')
            plt.axvline(median_time, color='orange', linestyle='--', alpha=0.8, label=f'Median: {median_time:.2f}s')
            plt.legend()
            
            plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
            plt.savefig(str(output_file).replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
            plt.close()
            
            self.console.print(f"[green]✓ Time distribution chart: {output_file.name}[/green]")
            return str(output_file)
        
        except Exception as e:
            self.console.print(f"[red]Error generating time distribution chart: {e}[/red]")
            return None


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="Perfx Analysis Engine")
    parser.add_argument("--data-dir", default="results/data", help="Data directory")
    parser.add_argument("--output-dir", default="results/analysis", help="Output directory")
    parser.add_argument("--config", help="Comparison configuration file")
    parser.add_argument("--steps", help="Specific steps (comma-separated)")
    parser.add_argument("--type", choices=["charts", "tables", "comparison", "all"], 
                       default="all", help="Analysis type")
    
    args = parser.parse_args()
    
    # 创建分析引擎
    engine = AnalysisEngine(args.data_dir, args.output_dir)
    
    # 运行分析
    results = engine.run_analysis(
        config_file=args.config,
        steps=args.steps,
        analysis_type=args.type
    )
    
    # 输出结果
    total_files = sum(len(files) for files in results.values())
    console.print(f"\n[bold green]Analysis completed! Generated {total_files} files[/bold green]")
    
    for file_type, files in results.items():
        if files:
            console.print(f"[blue]{file_type.capitalize()}:[/blue] {len(files)} files")


if __name__ == "__main__":
    main()