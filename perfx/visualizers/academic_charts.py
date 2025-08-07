#!/usr/bin/env python3
"""
Academic-grade chart generator for performance evaluation
用于生成适合学术论文的高质量图表
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

console = Console()

# 设置学术风格
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except OSError:
    plt.style.use('default')

if HAS_SEABORN:
    sns.set_palette("husl")
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16,
    'figure.figsize': (10, 6),
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1
})


class AcademicChartGenerator:
    """学术级图表生成器"""
    
    def __init__(self, output_dir: str = "results/charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()
    
    def generate_performance_comparison_chart(self, 
                                            pure_data: Dict[str, float], 
                                            summary_data: Dict[str, float],
                                            title: str = "Performance Comparison",
                                            output_name: str = "performance_comparison") -> str:
        """
        生成性能对比图表
        
        Args:
            pure_data: Pure模式的测试结果 {test_name: duration}
            summary_data: Summary模式的测试结果 {test_name: duration}
            title: 图表标题
            output_name: 输出文件名
            
        Returns:
            生成的图表文件路径
        """
        # 找到共同的测试用例
        common_tests = set(pure_data.keys()) & set(summary_data.keys())
        if not common_tests:
            self.console.print("[yellow]Warning: No common test cases found[/yellow]")
            return ""
        
        # 准备数据
        test_names = list(common_tests)
        pure_times = [pure_data[test] for test in test_names]
        summary_times = [summary_data[test] for test in test_names]
        
        # 计算加速比
        speedups = [pure_times[i] / summary_times[i] if summary_times[i] > 0 else 0 
                   for i in range(len(test_names))]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 左图：执行时间对比
        x = np.arange(len(test_names))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, pure_times, width, label='Pure', alpha=0.8)
        bars2 = ax1.bar(x + width/2, summary_times, width, label='Summary', alpha=0.8)
        
        ax1.set_xlabel('Test Cases')
        ax1.set_ylabel('Execution Time (s)')
        ax1.set_title(f'{title} - Execution Time')
        ax1.set_xticks(x)
        ax1.set_xticklabels([name[:15] + '...' if len(name) > 15 else name 
                           for name in test_names], rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 右图：加速比分布
        ax2.hist(speedups, bins=20, alpha=0.7, edgecolor='black')
        ax2.axvline(np.mean(speedups), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(speedups):.2f}x')
        ax2.set_xlabel('Speedup Ratio')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Speedup Distribution')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png')
        plt.close()
        
        self.console.print(f"[green]✓ Performance comparison chart saved: {output_path}[/green]")
        return str(output_path)
    
    def generate_scatter_plot(self, 
                            x_data: List[float], 
                            y_data: List[float],
                            labels: List[str] = None,
                            x_label: str = "X Axis",
                            y_label: str = "Y Axis", 
                            title: str = "Scatter Plot",
                            output_name: str = "scatter_plot") -> str:
        """
        生成散点图
        """
        plt.figure(figsize=(10, 8))
        
        # 创建散点图
        scatter = plt.scatter(x_data, y_data, alpha=0.6, s=60)
        
        # 添加趋势线
        if len(x_data) > 1:
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)
            plt.plot(x_data, p(x_data), "r--", alpha=0.8, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
        
        # 计算相关系数
        if len(x_data) > 1 and HAS_SCIPY:
            correlation, p_value = stats.pearsonr(x_data, y_data)
            plt.text(0.05, 0.95, f'Correlation: {correlation:.3f}\np-value: {p_value:.3f}',
                    transform=plt.gca().transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.grid(True, alpha=0.3)
        if len(x_data) > 1:
            plt.legend()
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png')
        plt.close()
        
        self.console.print(f"[green]✓ Scatter plot saved: {output_path}[/green]")
        return str(output_path)
    
    def generate_box_plot(self, 
                         data_dict: Dict[str, List[float]],
                         title: str = "Box Plot",
                         y_label: str = "Values",
                         output_name: str = "box_plot") -> str:
        """
        生成箱线图
        """
        plt.figure(figsize=(12, 6))
        
        # 准备数据
        labels = list(data_dict.keys())
        data_values = [data_dict[label] for label in labels]
        
        # 创建箱线图
        box_plot = plt.boxplot(data_values, labels=labels, patch_artist=True)
        
        # 设置颜色
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        plt.ylabel(y_label)
        plt.title(title)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png')
        plt.close()
        
        self.console.print(f"[green]✓ Box plot saved: {output_path}[/green]")
        return str(output_path)
    
    def generate_heatmap(self, 
                        data_matrix: np.ndarray,
                        row_labels: List[str],
                        col_labels: List[str],
                        title: str = "Heatmap",
                        output_name: str = "heatmap") -> str:
        """
        生成热力图
        """
        plt.figure(figsize=(12, 8))
        
        # 创建热力图
        if HAS_SEABORN:
            sns.heatmap(data_matrix, 
                       xticklabels=col_labels,
                       yticklabels=row_labels,
                       annot=True, 
                       fmt='.2f',
                       cmap='YlOrRd',
                       cbar_kws={'label': 'Value'})
        else:
            # 使用matplotlib的替代方案
            im = plt.imshow(data_matrix, cmap='YlOrRd', aspect='auto')
            plt.colorbar(im, label='Value')
            plt.xticks(range(len(col_labels)), col_labels)
            plt.yticks(range(len(row_labels)), row_labels)
            
            # 添加数值标注
            for i in range(len(row_labels)):
                for j in range(len(col_labels)):
                    plt.text(j, i, f'{data_matrix[i, j]:.2f}', 
                            ha='center', va='center', color='black')
        
        plt.title(title)
        plt.tight_layout()
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png')
        plt.close()
        
        self.console.print(f"[green]✓ Heatmap saved: {output_path}[/green]")
        return str(output_path)
    
    def generate_success_rate_chart(self, 
                                  test_results: Dict[str, Dict[str, Any]],
                                  title: str = "Test Success Rate",
                                  output_name: str = "success_rate") -> str:
        """
        生成测试成功率图表
        """
        # 统计成功率
        categories = []
        success_rates = []
        total_counts = []
        
        for category, results in test_results.items():
            if isinstance(results, dict) and 'test_results' in results:
                tests = results['test_results']
                total = len(tests)
                passed = sum(1 for test in tests if test.get('status') == 'passed')
                success_rate = (passed / total * 100) if total > 0 else 0
                
                categories.append(category)
                success_rates.append(success_rate)
                total_counts.append(total)
        
        if not categories:
            self.console.print("[yellow]Warning: No test results found[/yellow]")
            return ""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 左图：成功率柱状图
        bars = ax1.bar(categories, success_rates, alpha=0.7)
        ax1.set_ylabel('Success Rate (%)')
        ax1.set_title('Test Success Rate by Category')
        ax1.set_ylim(0, 100)
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, rate, count in zip(bars, success_rates, total_counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%\n({count} tests)',
                    ha='center', va='bottom', fontsize=9)
        
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 右图：测试数量饼图
        ax2.pie(total_counts, labels=categories, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Test Distribution')
        
        plt.tight_layout()
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png')
        plt.close()
        
        self.console.print(f"[green]✓ Success rate chart saved: {output_path}[/green]")
        return str(output_path)
    
    def generate_timeline_chart(self, 
                              timeline_data: List[Dict[str, Any]],
                              title: str = "Execution Timeline",
                              output_name: str = "timeline") -> str:
        """
        生成执行时间线图表
        """
        if not timeline_data:
            self.console.print("[yellow]Warning: No timeline data provided[/yellow]")
            return ""
        
        # 准备数据
        steps = [item['step'] for item in timeline_data]
        durations = [item['duration'] for item in timeline_data]
        
        plt.figure(figsize=(14, 8))
        
        # 创建甘特图风格的时间线
        y_pos = np.arange(len(steps))
        bars = plt.barh(y_pos, durations, alpha=0.7)
        
        # 添加时间标签
        for i, (bar, duration) in enumerate(zip(bars, durations)):
            plt.text(bar.get_width() + max(durations) * 0.01, bar.get_y() + bar.get_height()/2,
                    f'{duration:.1f}s', va='center', fontsize=10)
        
        plt.yticks(y_pos, steps)
        plt.xlabel('Duration (seconds)')
        plt.title(title)
        plt.grid(True, alpha=0.3, axis='x')
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png')
        plt.close()
        
        self.console.print(f"[green]✓ Timeline chart saved: {output_path}[/green]")
        return str(output_path)

    def generate_performance_distribution_chart(self, 
                                              pure_data: Dict[str, float], 
                                              summary_data: Dict[str, float],
                                              title: str = "Performance Distribution",
                                              output_name: str = "performance_distribution") -> str:
        """
        生成性能分布图表（加速因子和性能提升分布）
        
        Args:
            pure_data: Pure模式的测试结果 {test_name: duration}
            summary_data: Summary模式的测试结果 {test_name: duration}
            title: 图表标题
            output_name: 输出文件名
            
        Returns:
            生成的图表文件路径
        """
        # 找到共同的测试用例
        common_tests = set(pure_data.keys()) & set(summary_data.keys())
        if not common_tests:
            self.console.print("[yellow]Warning: No common test cases found[/yellow]")
            return ""
        
        # 计算加速因子和性能提升
        speedup_factors = []
        performance_improvements = []
        
        for test_name in common_tests:
            pure_duration = pure_data[test_name]
            summary_duration = summary_data[test_name]
            
            if summary_duration > 0:
                speedup_factor = pure_duration / summary_duration
                speedup_factors.append(speedup_factor)
                
                # 性能提升百分比 = (pure_duration - summary_duration) / pure_duration * 100
                if pure_duration > 0:
                    improvement = ((pure_duration - summary_duration) / pure_duration) * 100
                    performance_improvements.append(improvement)
        
        if not speedup_factors:
            self.console.print("[yellow]Warning: No valid speedup factors calculated[/yellow]")
            return ""
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 左图：加速因子分布
        ax1.hist(speedup_factors, bins=20, alpha=0.7, color='green', edgecolor='black')
        ax1.axvline(np.mean(speedup_factors), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(speedup_factors):.2f}x')
        ax1.set_xlabel('Speedup Factor')
        ax1.set_ylabel('Number of Test Cases')
        ax1.set_title('Distribution of Speedup Factors')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 右图：性能提升分布
        if performance_improvements:
            ax2.hist(performance_improvements, bins=20, alpha=0.7, color='red', edgecolor='black')
            ax2.axvline(np.mean(performance_improvements), color='blue', linestyle='--', 
                       label=f'Mean: {np.mean(performance_improvements):.1f}%')
            ax2.set_xlabel('Performance Improvement (%)')
            ax2.set_ylabel('Number of Test Cases')
            ax2.set_title('Distribution of Performance Improvements')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png')
        plt.close()
        
        self.console.print(f"[green]✓ Performance distribution chart saved: {output_path}[/green]")
        return str(output_path)
    
    def generate_performance_scatter_chart(self, 
                                         pure_data: Dict[str, float], 
                                         summary_data: Dict[str, float],
                                         title: str = "Performance Scatter Plot",
                                         output_name: str = "performance_scatter") -> str:
        """
        生成性能散点图（Pure vs Summary执行时间）
        
        Args:
            pure_data: Pure模式的测试结果 {test_name: duration}
            summary_data: Summary模式的测试结果 {test_name: duration}
            title: 图表标题
            output_name: 输出文件名
            
        Returns:
            生成的图表文件路径
        """
        # 找到共同的测试用例
        common_tests = set(pure_data.keys()) & set(summary_data.keys())
        if not common_tests:
            self.console.print("[yellow]Warning: No common test cases found[/yellow]")
            return ""
        
        # 准备数据
        pure_times = [pure_data[test] for test in common_tests]
        summary_times = [summary_data[test] for test in common_tests]
        
        # 创建散点图
        plt.figure(figsize=(12, 8))
        
        # 绘制散点图
        plt.scatter(pure_times, summary_times, alpha=0.6, s=30, color='blue')
        
        # 添加y=x线（无改进线）
        max_time = max(max(pure_times), max(summary_times))
        plt.plot([0, max_time], [0, max_time], 'r--', alpha=0.8, label='No improvement')
        
        # 设置轴标签和标题
        plt.xlabel('Original Semantics Time (seconds)')
        plt.ylabel('Summarized Semantics Time (seconds)')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 设置轴范围
        plt.xlim(0, max_time * 1.05)
        plt.ylim(0, max_time * 1.05)
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png')
        plt.close()
        
        self.console.print(f"[green]✓ Performance scatter chart saved: {output_path}[/green]")
        return str(output_path)
    
    def generate_test_case_improvement_chart(self, 
                                           pure_data: Dict[str, float], 
                                           summary_data: Dict[str, float],
                                           title: str = "Top Test Cases by Performance Improvement",
                                           output_name: str = "test_case_improvement",
                                           top_n: int = 20) -> str:
        """
        生成测试用例性能改进图表（前N个改进最大的测试用例）
        
        Args:
            pure_data: Pure模式的测试结果 {test_name: duration}
            summary_data: Summary模式的测试结果 {test_name: duration}
            title: 图表标题
            output_name: 输出文件名
            top_n: 显示前N个测试用例
            
        Returns:
            生成的图表文件路径
        """
        # 找到共同的测试用例
        common_tests = set(pure_data.keys()) & set(summary_data.keys())
        if not common_tests:
            self.console.print("[yellow]Warning: No common test cases found[/yellow]")
            return ""
        
        # 计算加速因子
        test_improvements = []
        for test_name in common_tests:
            pure_duration = pure_data[test_name]
            summary_duration = summary_data[test_name]
            
            if summary_duration > 0:
                speedup_factor = pure_duration / summary_duration
                test_improvements.append((test_name, speedup_factor))
        
        if not test_improvements:
            self.console.print("[yellow]Warning: No valid speedup factors calculated[/yellow]")
            return ""
        
        # 按加速因子排序，取前N个
        test_improvements.sort(key=lambda x: x[1], reverse=True)
        top_improvements = test_improvements[:top_n]
        
        # 准备数据
        test_names = [item[0] for item in top_improvements]
        speedup_factors = [item[1] for item in top_improvements]
        
        # 简化测试名称（只保留最后一部分）
        simplified_names = []
        for name in test_names:
            # 提取测试名称的最后部分
            if '::' in name:
                simplified_name = name.split('::')[-1]
            else:
                simplified_name = name.split('/')[-1] if '/' in name else name
            simplified_names.append(simplified_name[:50] + '...' if len(simplified_name) > 50 else simplified_name)
        
        # 创建水平条形图
        plt.figure(figsize=(14, 10))
        
        y_pos = np.arange(len(simplified_names))
        bars = plt.barh(y_pos, speedup_factors, color='green', alpha=0.7)
        
        # 添加数值标签
        for i, (bar, speedup) in enumerate(zip(bars, speedup_factors)):
            plt.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                    f'{speedup:.2f}x', va='center', fontsize=10)
        
        # 设置轴标签和标题
        plt.yticks(y_pos, simplified_names)
        plt.xlabel('Speedup Factor')
        plt.title(title)
        plt.grid(True, alpha=0.3, axis='x')
        
        # 添加y=x线作为参考
        plt.axvline(x=1.0, color='red', linestyle='--', alpha=0.5, label='No improvement')
        plt.legend()
        
        # 保存图表
        output_path = self.output_dir / f"{output_name}.pdf"
        plt.savefig(output_path, format='pdf', bbox_inches='tight')
        plt.savefig(self.output_dir / f"{output_name}.png", format='png', bbox_inches='tight')
        plt.close()
        
        self.console.print(f"[green]✓ Test case improvement chart saved: {output_path}[/green]")
        return str(output_path)


def load_json_data(file_path: str) -> Dict[str, Any]:
    """加载JSON数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading {file_path}: {e}[/red]")
        return {}


def extract_test_durations(json_data: Dict[str, Any]) -> Dict[str, float]:
    """从JSON数据中提取测试执行时间"""
    durations = {}
    
    if 'test_results' in json_data:
        for test in json_data['test_results']:
            test_id = test.get('test_id', '')
            duration = test.get('duration')
            if test_id and duration is not None:
                durations[test_id] = float(duration)
    
    return durations


def extract_test_results(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """从JSON数据中提取测试结果"""
    return {
        'test_results': json_data.get('test_results', []),
        'summary': json_data.get('summary', {}),
        'metadata': json_data.get('metadata', {})
    }