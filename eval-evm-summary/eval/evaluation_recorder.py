"""
Evaluation recorder for storing and managing evaluation results.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from . import PROJECT_ROOT
import matplotlib.pyplot as plt
import numpy as np


class EvaluationRecorder:
    """评估结果记录器"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "build": {"success": False, "duration": None, "error": None},
            "conformance_test": {"success": False, "duration": None, "error": None},
            "prove_summaries_test": {"success": False, "duration": None, "error": None},
            "summarize_eval": [],  # 新增summarize评估结果
            "concrete_execution_performance": {},  # 新增concrete execution性能对比结果
            "symbolic_execution_performance": {} # 新增symbolic execution性能对比结果
        }
        # 添加命令记录
        self.commands = []
    
    def add_command(self, command: str, cwd: str = None, env_vars: dict = None, output: str = None, error: str = None, success: bool = None, duration: float = None) -> None:
        """记录执行的命令"""
        self.commands.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "cwd": cwd,
            "env_vars": env_vars,
            "output": output,
            "error": error,
            "success": success,
            "duration": duration
        })
    
    def save_commands(self, output_dir: Path) -> None:
        """保存所有执行的命令到文件"""
        commands_file = output_dir / "executed_commands.json"
        
        # 如果文件已存在，先加载现有数据
        existing_commands = []
        if commands_file.exists():
            try:
                with open(commands_file, 'r', encoding='utf-8') as f:
                    existing_commands = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_commands = []
        
        # 合并现有命令和新命令，避免重复
        all_commands = existing_commands.copy()
        for new_cmd in self.commands:
            # 检查是否已存在相同的命令
            cmd_exists = False
            for existing_cmd in existing_commands:
                if (existing_cmd.get('command') == new_cmd.get('command') and 
                    existing_cmd.get('cwd') == new_cmd.get('cwd')):
                    cmd_exists = True
                    break
            
            if not cmd_exists:
                all_commands.append(new_cmd)
        
        # 保存合并后的命令
        with open(commands_file, 'w', encoding='utf-8') as f:
            json.dump(all_commands, f, indent=2, ensure_ascii=False)
        
        # 保存人可读的命令日志
        commands_log = output_dir / "executed_commands.log"
        with open(commands_log, 'w', encoding='utf-8') as f:
            f.write("EXECUTED COMMANDS LOG\n")
            f.write("=" * 50 + "\n\n")
            
            for i, cmd_info in enumerate(all_commands, 1):
                f.write(f"Command #{i}\n")
                f.write("-" * 20 + "\n")
                f.write(f"Timestamp: {cmd_info['timestamp']}\n")
                f.write(f"Command: {cmd_info['command']}\n")
                if cmd_info['cwd']:
                    f.write(f"Working Directory: {cmd_info['cwd']}\n")
                if cmd_info['env_vars']:
                    f.write(f"Environment Variables: {cmd_info['env_vars']}\n")
                if cmd_info['duration'] is not None:
                    f.write(f"Duration: {cmd_info['duration']:.2f}s\n")
                f.write(f"Success: {cmd_info['success']}\n")
                if cmd_info['output']:
                    f.write(f"Output:\n{cmd_info['output']}\n")
                if cmd_info['error']:
                    f.write(f"Error:\n{cmd_info['error']}\n")
                f.write("\n" + "=" * 50 + "\n\n")
    
    def start_test(self, test_name: str) -> None:
        """开始测试"""
        if test_name in self.results:
            self.results[test_name]["start_time"] = time.time()
    
    def end_test(self, test_name: str, success: bool, error: Optional[str] = None) -> None:
        """结束测试"""
        if test_name in self.results:
            start_time = self.results[test_name].get("start_time")
            if start_time:
                self.results[test_name]["duration"] = time.time() - start_time
            self.results[test_name]["success"] = success
            if error:
                self.results[test_name]["error"] = error
    
    def update_test_output(self, test_name: str, stdout: str, stderr: str) -> None:
        """更新测试输出信息"""
        if test_name in self.results:
            self.results[test_name]["stdout"] = stdout
            self.results[test_name]["stderr"] = stderr
    
    def analyze_concrete_execution_performance(self, pure_durations: Dict[str, float], summary_durations: Dict[str, float]) -> Dict[str, Any]:
        """
        分析concrete execution性能对比
        
        Args:
            pure_durations: 原始语义的测试用例耗时
            summary_durations: summarized语义的测试用例耗时
            
        Returns:
            Dict[str, Any]: 性能分析结果
        """
        # 计算总体性能提升
        pure_total = sum(pure_durations.values())
        summary_total = sum(summary_durations.values())
        speedup = pure_total / summary_total if summary_total > 0 else 0
        
        # 分析各个测试用例的性能变化
        test_analysis = {}
        all_test_names = set(pure_durations.keys()) | set(summary_durations.keys())
        
        for test_name in all_test_names:
            pure_time = pure_durations.get(test_name, 0)
            summary_time = summary_durations.get(test_name, 0)
            
            if pure_time > 0 and summary_time > 0:
                test_speedup = pure_time / summary_time
                improvement = (pure_time - summary_time) / pure_time * 100
                test_analysis[test_name] = {
                    'pure_time': pure_time,
                    'summary_time': summary_time,
                    'speedup': test_speedup,
                    'improvement': improvement
                }
            elif pure_time > 0:
                # 只在原始语义中有数据
                test_analysis[test_name] = {
                    'pure_time': pure_time,
                    'summary_time': 0,
                    'speedup': 0,
                    'improvement': 0
                }
            elif summary_time > 0:
                # 只在summarized语义中有数据
                test_analysis[test_name] = {
                    'pure_time': 0,
                    'summary_time': summary_time,
                    'speedup': 0,
                    'improvement': 0
                }
        
        # 计算统计信息
        speedups = [analysis['speedup'] for analysis in test_analysis.values() if analysis['speedup'] > 0]
        improvements = [analysis['improvement'] for analysis in test_analysis.values() if analysis['improvement'] != 0]
        
        return {
            'total_speedup': speedup,
            'total_improvement': (pure_total - summary_total) / pure_total * 100 if pure_total > 0 else 0,
            'pure_total_time': pure_total,
            'summary_total_time': summary_total,
            'test_analysis': test_analysis,
            'statistics': {
                'num_tests': len(all_test_names),
                'num_comparable': len([a for a in test_analysis.values() if a['pure_time'] > 0 and a['summary_time'] > 0]),
                'avg_speedup': np.mean(speedups) if speedups else 0,
                'median_speedup': np.median(speedups) if speedups else 0,
                'max_speedup': max(speedups) if speedups else 0,
                'min_speedup': min(speedups) if speedups else 0,
                'avg_improvement': np.mean(improvements) if improvements else 0,
                'median_improvement': np.median(improvements) if improvements else 0,
                'max_improvement': max(improvements) if improvements else 0,
                'min_improvement': min(improvements) if improvements else 0
            }
        }
    
    def analyze_symbolic_execution_performance(self, haskell_durations: Dict[str, Dict[str, float]], haskell_summary_durations: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        分析symbolic execution性能对比
        
        Args:
            haskell_durations: 原始语义的测试套件到测试用例耗时映射
            haskell_summary_durations: summarized语义的测试套件到测试用例耗时映射
            
        Returns:
            Dict[str, Any]: 性能分析结果
        """
        # 计算总体性能提升
        haskell_total = sum(sum(suite_durations.values()) for suite_durations in haskell_durations.values())
        haskell_summary_total = sum(sum(suite_durations.values()) for suite_durations in haskell_summary_durations.values())
        speedup = haskell_total / haskell_summary_total if haskell_summary_total > 0 else 0
        
        # 分析各个测试套件的性能变化
        suite_analysis = {}
        all_suite_names = set(haskell_durations.keys()) | set(haskell_summary_durations.keys())
        
        for suite_name in all_suite_names:
            haskell_suite_durations = haskell_durations.get(suite_name, {})
            haskell_summary_suite_durations = haskell_summary_durations.get(suite_name, {})
            
            haskell_time = sum(haskell_suite_durations.values())
            haskell_summary_time = sum(haskell_summary_suite_durations.values())
            
            if haskell_time > 0 and haskell_summary_time > 0:
                suite_speedup = haskell_time / haskell_summary_time
                improvement = (haskell_time - haskell_summary_time) / haskell_time * 100
                suite_analysis[suite_name] = {
                    'haskell_time': haskell_time,
                    'haskell_summary_time': haskell_summary_time,
                    'speedup': suite_speedup,
                    'improvement': improvement,
                    'haskell_test_count': len(haskell_suite_durations),
                    'haskell_summary_test_count': len(haskell_summary_suite_durations)
                }
            elif haskell_time > 0:
                # 只在原始语义中有数据
                suite_analysis[suite_name] = {
                    'haskell_time': haskell_time,
                    'haskell_summary_time': 0,
                    'speedup': 0,
                    'improvement': 0,
                    'haskell_test_count': len(haskell_suite_durations),
                    'haskell_summary_test_count': 0
                }
            elif haskell_summary_time > 0:
                # 只在summarized语义中有数据
                suite_analysis[suite_name] = {
                    'haskell_time': 0,
                    'haskell_summary_time': haskell_summary_time,
                    'speedup': 0,
                    'improvement': 0,
                    'haskell_test_count': 0,
                    'haskell_summary_test_count': len(haskell_summary_suite_durations)
                }
        
        # 细粒度测试用例分析
        test_case_analysis = {}
        all_test_cases = set()
        
        # 收集所有测试用例
        for suite_durations in haskell_durations.values():
            all_test_cases.update(suite_durations.keys())
        for suite_durations in haskell_summary_durations.values():
            all_test_cases.update(suite_durations.keys())
        
        # 分析每个测试用例的性能
        for test_case in all_test_cases:
            haskell_time = 0
            haskell_summary_time = 0
            
            # 在所有套件中查找该测试用例
            for suite_durations in haskell_durations.values():
                if test_case in suite_durations:
                    haskell_time = suite_durations[test_case]
                    break
            
            for suite_durations in haskell_summary_durations.values():
                if test_case in suite_durations:
                    haskell_summary_time = suite_durations[test_case]
                    break
            
            if haskell_time > 0 and haskell_summary_time > 0:
                test_speedup = haskell_time / haskell_summary_time
                test_improvement = (haskell_time - haskell_summary_time) / haskell_time * 100
                test_case_analysis[test_case] = {
                    'haskell_time': haskell_time,
                    'haskell_summary_time': haskell_summary_time,
                    'speedup': test_speedup,
                    'improvement': test_improvement
                }
            elif haskell_time > 0:
                test_case_analysis[test_case] = {
                    'haskell_time': haskell_time,
                    'haskell_summary_time': 0,
                    'speedup': 0,
                    'improvement': 0
                }
            elif haskell_summary_time > 0:
                test_case_analysis[test_case] = {
                    'haskell_time': 0,
                    'haskell_summary_time': haskell_summary_time,
                    'speedup': 0,
                    'improvement': 0
                }
        
        # 计算统计信息
        speedups = [analysis['speedup'] for analysis in suite_analysis.values() if analysis['speedup'] > 0]
        improvements = [analysis['improvement'] for analysis in suite_analysis.values() if analysis['improvement'] != 0]
        
        test_speedups = [analysis['speedup'] for analysis in test_case_analysis.values() if analysis['speedup'] > 0]
        test_improvements = [analysis['improvement'] for analysis in test_case_analysis.values() if analysis['improvement'] != 0]
        
        return {
            'total_speedup': speedup,
            'total_improvement': (haskell_total - haskell_summary_total) / haskell_total * 100 if haskell_total > 0 else 0,
            'haskell_total_time': haskell_total,
            'haskell_summary_total_time': haskell_summary_total,
            'suite_analysis': suite_analysis,
            'test_case_analysis': test_case_analysis,
            'statistics': {
                'num_suites': len(all_suite_names),
                'num_comparable_suites': len([a for a in suite_analysis.values() if a['haskell_time'] > 0 and a['haskell_summary_time'] > 0]),
                'num_test_cases': len(all_test_cases),
                'num_comparable_test_cases': len([a for a in test_case_analysis.values() if a['haskell_time'] > 0 and a['haskell_summary_time'] > 0]),
                'avg_suite_speedup': np.mean(speedups) if speedups else 0,
                'median_suite_speedup': np.median(speedups) if speedups else 0,
                'max_suite_speedup': max(speedups) if speedups else 0,
                'min_suite_speedup': min(speedups) if speedups else 0,
                'avg_suite_improvement': np.mean(improvements) if improvements else 0,
                'median_suite_improvement': np.median(improvements) if improvements else 0,
                'max_suite_improvement': max(improvements) if improvements else 0,
                'min_suite_improvement': min(improvements) if improvements else 0,
                'avg_test_speedup': np.mean(test_speedups) if test_speedups else 0,
                'median_test_speedup': np.median(test_speedups) if test_speedups else 0,
                'max_test_speedup': max(test_speedups) if test_speedups else 0,
                'min_test_speedup': min(test_speedups) if test_speedups else 0,
                'avg_test_improvement': np.mean(test_improvements) if test_improvements else 0,
                'median_test_improvement': np.median(test_improvements) if test_improvements else 0,
                'max_test_improvement': max(test_improvements) if test_improvements else 0,
                'min_test_improvement': min(test_improvements) if test_improvements else 0
            }
        }

    def generate_performance_charts(self, output_dir: Path) -> None:
        """
        生成性能对比图表
        
        Args:
            output_dir: 输出目录
        """
        if "concrete_execution_performance" not in self.results:
            print("警告: 没有concrete execution性能数据，跳过图表生成")
            return
        
        performance_data = self.results["concrete_execution_performance"]
        if "analysis" not in performance_data:
            print("警告: 没有性能分析数据，跳过图表生成")
            return
        
        analysis = performance_data["analysis"]
        test_analysis = analysis["test_analysis"]
        
        # 设置matplotlib样式
        plt.style.use('default')
        plt.rcParams['font.size'] = 10
        plt.rcParams['figure.figsize'] = (12, 8)
        
        # 1. 总体性能对比柱状图
        self._generate_total_performance_chart(analysis, output_dir)
        
        # 2. 测试用例性能提升分布图
        self._generate_test_case_performance_chart(test_analysis, output_dir)
        
        # 3. 性能提升散点图
        self._generate_performance_scatter_plot(test_analysis, output_dir)
        
        # 4. 性能提升直方图
        self._generate_performance_histogram(test_analysis, output_dir)
    
    def generate_symbolic_performance_charts(self, output_dir: Path) -> None:
        """
        生成symbolic execution性能对比图表
        
        Args:
            output_dir: 输出目录
        """
        if "symbolic_execution_performance" not in self.results:
            print("警告: 没有symbolic execution性能数据，跳过图表生成")
            return
        
        performance_data = self.results["symbolic_execution_performance"]
        if "analysis" not in performance_data:
            print("警告: 没有性能分析数据，跳过图表生成")
            return
        
        analysis = performance_data["analysis"]
        suite_analysis = analysis["suite_analysis"]
        test_case_analysis = analysis.get("test_case_analysis", {})
        
        # 设置matplotlib样式
        plt.style.use('default')
        plt.rcParams['font.size'] = 10
        plt.rcParams['figure.figsize'] = (12, 8)
        
        # 1. 总体性能对比柱状图
        self._generate_symbolic_total_performance_chart(analysis, output_dir)
        
        # 2. 测试套件性能对比柱状图
        self._generate_symbolic_suite_performance_chart(suite_analysis, output_dir)
        
        # 3. 测试用例性能散点图
        if test_case_analysis:
            self._generate_symbolic_test_case_performance_chart(test_case_analysis, output_dir)
        
        # 4. 性能提升散点图
        self._generate_symbolic_performance_scatter_plot(suite_analysis, output_dir)
        
        # 5. 性能提升直方图
        self._generate_symbolic_performance_histogram(suite_analysis, output_dir)
        
        # 6. 测试用例性能提升直方图
        if test_case_analysis:
            self._generate_symbolic_test_case_performance_histogram(test_case_analysis, output_dir)
        
        # 7. 性能提升箱线图
        self._generate_symbolic_performance_boxplot(suite_analysis, output_dir)
        
        # 8. 测试套件大小vs性能提升散点图
        self._generate_symbolic_suite_size_vs_performance_plot(suite_analysis, output_dir)
        
        # 9. 性能提升百分比分布图
        self._generate_symbolic_improvement_distribution_plot(suite_analysis, output_dir)
        
        # 10. 时间分布对比图
        self._generate_symbolic_time_distribution_comparison(suite_analysis, output_dir)
        
        # 11. 性能提升热力图（按测试类型分组）
        self._generate_symbolic_performance_heatmap(suite_analysis, output_dir)
        
        # 12. 累积性能提升图
        self._generate_symbolic_cumulative_improvement_plot(suite_analysis, output_dir)
        
        print(f"✓ Symbolic execution性能图表已生成到: {output_dir}")
    
    def _generate_total_performance_chart(self, analysis: Dict[str, Any], output_dir: Path) -> None:
        """生成总体性能对比柱状图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 总耗时对比
        semantics = ['Original', 'Summarized']
        times = [analysis['pure_total_time'], analysis['summary_total_time']]
        colors = ['#1f77b4', '#ff7f0e']
        
        bars1 = ax1.bar(semantics, times, color=colors, alpha=0.8)
        ax1.set_ylabel('Total Execution Time (seconds)')
        ax1.set_title('Total Execution Time Comparison')
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, time in zip(bars1, times):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + max(times)*0.01,
                    f'{time:.1f}s', ha='center', va='bottom')
        
        # 性能提升
        speedup = analysis['total_speedup']
        improvement = analysis['total_improvement']
        
        ax2.bar(['Speedup'], [speedup], color='#2ca02c', alpha=0.8)
        ax2.set_ylabel('Speedup Factor')
        ax2.set_title(f'Performance Improvement\n({improvement:.1f}% faster)')
        ax2.grid(True, alpha=0.3)
        
        # 添加数值标签
        ax2.text(0, speedup + 0.1, f'{speedup:.2f}x', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'total_performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'total_performance_comparison.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_test_case_performance_chart(self, test_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成测试用例性能提升分布图"""
        # 选择前20个性能提升最大的测试用例
        sorted_tests = sorted(
            [(name, data) for name, data in test_analysis.items() if data['speedup'] > 0],
            key=lambda x: x[1]['speedup'],
            reverse=True
        )[:20]
        
        if not sorted_tests:
            return
        
        test_names = [name.split('::')[-1][:30] + '...' if len(name) > 30 else name.split('::')[-1] 
                     for name, _ in sorted_tests]
        speedups = [data['speedup'] for _, data in sorted_tests]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        bars = ax.barh(range(len(test_names)), speedups, color='#2ca02c', alpha=0.8)
        ax.set_yticks(range(len(test_names)))
        ax.set_yticklabels(test_names)
        ax.set_xlabel('Speedup Factor')
        ax.set_title('Top 20 Test Cases by Performance Improvement')
        ax.grid(True, alpha=0.3, axis='x')
        
        # 添加数值标签
        for i, (bar, speedup) in enumerate(zip(bars, speedups)):
            ax.text(speedup + 0.05, bar.get_y() + bar.get_height()/2,
                   f'{speedup:.2f}x', va='center')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'test_case_performance_improvement.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'test_case_performance_improvement.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_performance_scatter_plot(self, test_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成性能提升散点图"""
        pure_times = []
        summary_times = []
        
        for data in test_analysis.values():
            if data['pure_time'] > 0 and data['summary_time'] > 0:
                pure_times.append(data['pure_time'])
                summary_times.append(data['summary_time'])
        
        if not pure_times:
            return
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 散点图
        ax.scatter(pure_times, summary_times, alpha=0.6, s=30)
        
        # 添加对角线（y=x）
        max_time = max(max(pure_times), max(summary_times))
        ax.plot([0, max_time], [0, max_time], 'r--', alpha=0.8, label='No improvement')
        
        ax.set_xlabel('Original Semantics Time (seconds)')
        ax.set_ylabel('Summarized Semantics Time (seconds)')
        ax.set_title('Performance Comparison: Original vs Summarized Semantics')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 设置坐标轴范围
        ax.set_xlim(0, max_time * 1.1)
        ax.set_ylim(0, max_time * 1.1)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'performance_scatter_plot.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'performance_scatter_plot.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_performance_histogram(self, test_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成性能提升直方图"""
        speedups = [data['speedup'] for data in test_analysis.values() if data['speedup'] > 0]
        
        if not speedups:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 速度提升分布
        ax1.hist(speedups, bins=20, alpha=0.7, color='#2ca02c', edgecolor='black')
        ax1.set_xlabel('Speedup Factor')
        ax1.set_ylabel('Number of Test Cases')
        ax1.set_title('Distribution of Speedup Factors')
        ax1.grid(True, alpha=0.3)
        
        # 改进百分比分布
        improvements = [data['improvement'] for data in test_analysis.values() if data['improvement'] != 0]
        ax2.hist(improvements, bins=20, alpha=0.7, color='#d62728', edgecolor='black')
        ax2.set_xlabel('Performance Improvement (%)')
        ax2.set_ylabel('Number of Test Cases')
        ax2.set_title('Distribution of Performance Improvements')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'performance_distribution.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'performance_distribution.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_total_performance_chart(self, analysis: Dict[str, Any], output_dir: Path) -> None:
        """生成symbolic execution总体性能对比柱状图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 总耗时对比
        semantics = ['Original', 'Summarized']
        times = [analysis['haskell_total_time'], analysis['haskell_summary_total_time']]
        colors = ['#1f77b4', '#ff7f0e']
        
        bars1 = ax1.bar(semantics, times, color=colors, alpha=0.8)
        ax1.set_ylabel('Total Execution Time (seconds)')
        ax1.set_title('Symbolic Execution: Total Time Comparison')
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar, time in zip(bars1, times):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + max(times)*0.01,
                    f'{time:.1f}s', ha='center', va='bottom')
        
        # 性能提升
        speedup = analysis['total_speedup']
        improvement = analysis['total_improvement']
        
        ax2.bar(['Speedup'], [speedup], color='#2ca02c', alpha=0.8)
        ax2.set_ylabel('Speedup Factor')
        ax2.set_title(f'Symbolic Execution: Performance Improvement\n({improvement:.1f}% faster)')
        ax2.grid(True, alpha=0.3)
        
        # 添加数值标签
        ax2.text(0, speedup + 0.1, f'{speedup:.2f}x', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_total_performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_total_performance_comparison.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_suite_performance_chart(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成symbolic execution测试套件性能提升分布图"""
        # 选择前20个性能提升最大的测试套件
        sorted_suites = sorted(
            [(name, data) for name, data in suite_analysis.items() if data['speedup'] > 0],
            key=lambda x: x[1]['speedup'],
            reverse=True
        )[:20]
        
        if not sorted_suites:
            return
        
        suite_names = [name[:30] + '...' if len(name) > 30 else name 
                      for name, _ in sorted_suites]
        speedups = [data['speedup'] for _, data in sorted_suites]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        bars = ax.barh(range(len(suite_names)), speedups, color='#2ca02c', alpha=0.8)
        ax.set_yticks(range(len(suite_names)))
        ax.set_yticklabels(suite_names)
        ax.set_xlabel('Speedup Factor')
        ax.set_title('Symbolic Execution: Top 20 Test Suites by Performance Improvement')
        ax.grid(True, alpha=0.3, axis='x')
        
        # 添加数值标签
        for i, (bar, speedup) in enumerate(zip(bars, speedups)):
            ax.text(speedup + 0.05, bar.get_y() + bar.get_height()/2,
                   f'{speedup:.2f}x', va='center')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_suite_performance_improvement.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_suite_performance_improvement.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_performance_scatter_plot(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成symbolic execution性能提升散点图"""
        haskell_times = []
        haskell_summary_times = []
        
        for data in suite_analysis.values():
            if data['haskell_time'] > 0 and data['haskell_summary_time'] > 0:
                haskell_times.append(data['haskell_time'])
                haskell_summary_times.append(data['haskell_summary_time'])
        
        if not haskell_times:
            return
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 散点图
        ax.scatter(haskell_times, haskell_summary_times, alpha=0.6, s=30)
        
        # 添加对角线（y=x）
        max_time = max(max(haskell_times), max(haskell_summary_times))
        ax.plot([0, max_time], [0, max_time], 'r--', alpha=0.8, label='No improvement')
        
        ax.set_xlabel('Original Semantics Time (seconds)')
        ax.set_ylabel('Summarized Semantics Time (seconds)')
        ax.set_title('Symbolic Execution: Performance Comparison')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 设置坐标轴范围
        ax.set_xlim(0, max_time * 1.1)
        ax.set_ylim(0, max_time * 1.1)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_performance_scatter_plot.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_performance_scatter_plot.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_performance_histogram(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成symbolic execution性能提升直方图"""
        speedups = [data['speedup'] for data in suite_analysis.values() if data['speedup'] > 0]
        
        if not speedups:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 速度提升分布
        ax1.hist(speedups, bins=20, alpha=0.7, color='#2ca02c', edgecolor='black')
        ax1.set_xlabel('Speedup Factor')
        ax1.set_ylabel('Number of Test Suites')
        ax1.set_title('Symbolic Execution: Distribution of Speedup Factors')
        ax1.grid(True, alpha=0.3)
        
        # 改进百分比分布
        improvements = [data['improvement'] for data in suite_analysis.values() if data['improvement'] != 0]
        ax2.hist(improvements, bins=20, alpha=0.7, color='#d62728', edgecolor='black')
        ax2.set_xlabel('Performance Improvement (%)')
        ax2.set_ylabel('Number of Test Suites')
        ax2.set_title('Symbolic Execution: Distribution of Performance Improvements')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_performance_distribution.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_performance_distribution.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_test_case_performance_chart(self, test_case_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成symbolic execution测试用例性能提升分布图"""
        # 选择前20个性能提升最大的测试用例
        sorted_tests = sorted(
            [(name, data) for name, data in test_case_analysis.items() if data['speedup'] > 0],
            key=lambda x: x[1]['speedup'],
            reverse=True
        )[:20]
        
        if not sorted_tests:
            return
        
        test_names = [name.split('::')[-1][:30] + '...' if len(name) > 30 else name.split('::')[-1] 
                     for name, _ in sorted_tests]
        speedups = [data['speedup'] for _, data in sorted_tests]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        bars = ax.barh(range(len(test_names)), speedups, color='#2ca02c', alpha=0.8)
        ax.set_yticks(range(len(test_names)))
        ax.set_yticklabels(test_names)
        ax.set_xlabel('Speedup Factor')
        ax.set_title('Symbolic Execution: Top 20 Test Cases by Performance Improvement')
        ax.grid(True, alpha=0.3, axis='x')
        
        # 添加数值标签
        for i, (bar, speedup) in enumerate(zip(bars, speedups)):
            ax.text(speedup + 0.05, bar.get_y() + bar.get_height()/2,
                   f'{speedup:.2f}x', va='center')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_test_case_performance_improvement.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_test_case_performance_improvement.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_test_case_performance_histogram(self, test_case_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成symbolic execution测试用例性能提升直方图"""
        speedups = [data['speedup'] for data in test_case_analysis.values() if data['speedup'] > 0]
        
        if not speedups:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 速度提升分布
        ax1.hist(speedups, bins=20, alpha=0.7, color='#2ca02c', edgecolor='black')
        ax1.set_xlabel('Speedup Factor')
        ax1.set_ylabel('Number of Test Cases')
        ax1.set_title('Symbolic Execution: Distribution of Speedup Factors')
        ax1.grid(True, alpha=0.3)
        
        # 改进百分比分布
        improvements = [data['improvement'] for data in test_case_analysis.values() if data['improvement'] != 0]
        ax2.hist(improvements, bins=20, alpha=0.7, color='#d62728', edgecolor='black')
        ax2.set_xlabel('Performance Improvement (%)')
        ax2.set_ylabel('Number of Test Cases')
        ax2.set_title('Symbolic Execution: Distribution of Performance Improvements')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_test_case_performance_distribution.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_test_case_performance_distribution.pdf', bbox_inches='tight')
        plt.close()
    
    def generate_academic_tables(self, output_dir: Path) -> None:
        """
        生成学术论文级别的表格
        
        Args:
            output_dir: 输出目录
        """
        if "concrete_execution_performance" not in self.results:
            print("警告: 没有concrete execution性能数据，跳过表格生成")
            return
        
        performance_data = self.results["concrete_execution_performance"]
        if "analysis" not in performance_data:
            print("警告: 没有性能分析数据，跳过表格生成")
            return
        
        analysis = performance_data["analysis"]
        
        # 1. 生成LaTeX表格
        self._generate_latex_table(analysis, output_dir)
        
        # 2. 生成CSV表格
        self._generate_csv_table(analysis, output_dir)
        
        # 3. 生成Markdown表格
        self._generate_markdown_table(analysis, output_dir)
    
    def generate_symbolic_academic_tables(self, output_dir: Path) -> None:
        """
        生成symbolic execution学术论文级别的表格
        
        Args:
            output_dir: 输出目录
        """
        if "symbolic_execution_performance" not in self.results:
            print("警告: 没有symbolic execution性能数据，跳过表格生成")
            return
        
        performance_data = self.results["symbolic_execution_performance"]
        if "analysis" not in performance_data:
            print("警告: 没有symbolic execution性能分析数据，跳过表格生成")
            return
        
        analysis = performance_data["analysis"]
        
        # 1. 生成LaTeX表格
        self._generate_symbolic_latex_table(analysis, output_dir)
        
        # 2. 生成CSV表格
        self._generate_symbolic_csv_table(analysis, output_dir)
        
        # 3. 生成Markdown表格
        self._generate_symbolic_markdown_table(analysis, output_dir)
    
    def _generate_latex_table(self, analysis: Dict[str, Any], output_dir: Path) -> None:
        """生成LaTeX格式的表格"""
        latex_file = output_dir / 'performance_results.tex'
        
        # 使用字符串替换而不是格式化来避免&字符的问题
        latex_template = r"""\documentclass{article}
\usepackage{booktabs}
\usepackage{siunitx}
\usepackage{graphicx}

\begin{document}

\section{Concrete Execution Performance Results}

\subsection{Overall Performance Comparison}

\begin{table}[h]
\centering
\caption{Overall Performance Comparison between Original and Summarized Semantics}
\begin{tabular}{lcc}
\toprule
Metric & Original Semantics & Summarized Semantics \\
\midrule
Total Execution Time & \SI{PURE_TOTAL_TIME}{\second} & \SI{SUMMARY_TOTAL_TIME}{\second} \\
Speedup Factor & 1.00x & SPEEDUP_FACTORx \\
Performance Improvement & 0.0\% & IMPROVEMENT_PERCENT\% \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Statistical Summary}

\begin{table}[h]
\centering
\caption{Statistical Summary of Performance Improvements}
\begin{tabular}{lr}
\toprule
Metric & Value \\
\midrule
Number of Test Cases & NUM_TESTS \\
Comparable Test Cases & NUM_COMPARABLE \\
Average Speedup & AVG_SPEEDUPx \\
Median Speedup & MEDIAN_SPEEDUPx \\
Maximum Speedup & MAX_SPEEDUPx \\
Minimum Speedup & MIN_SPEEDUPx \\
Average Improvement & AVG_IMPROVEMENT\% \\
Median Improvement & MEDIAN_IMPROVEMENT\% \\
Maximum Improvement & MAX_IMPROVEMENT\% \\
Minimum Improvement & MIN_IMPROVEMENT\% \\
\bottomrule
\end{tabular}
\end{table}

\end{document}
"""
        
        # 替换占位符
        latex_content = latex_template.replace('PURE_TOTAL_TIME', f"{analysis['pure_total_time']:.2f}")
        latex_content = latex_content.replace('SUMMARY_TOTAL_TIME', f"{analysis['summary_total_time']:.2f}")
        latex_content = latex_content.replace('SPEEDUP_FACTOR', f"{analysis['total_speedup']:.2f}")
        latex_content = latex_content.replace('IMPROVEMENT_PERCENT', f"{analysis['total_improvement']:.1f}")
        latex_content = latex_content.replace('NUM_TESTS', str(analysis['statistics']['num_tests']))
        latex_content = latex_content.replace('NUM_COMPARABLE', str(analysis['statistics']['num_comparable']))
        latex_content = latex_content.replace('AVG_SPEEDUP', f"{analysis['statistics']['avg_speedup']:.2f}")
        latex_content = latex_content.replace('MEDIAN_SPEEDUP', f"{analysis['statistics']['median_speedup']:.2f}")
        latex_content = latex_content.replace('MAX_SPEEDUP', f"{analysis['statistics']['max_speedup']:.2f}")
        latex_content = latex_content.replace('MIN_SPEEDUP', f"{analysis['statistics']['min_speedup']:.2f}")
        latex_content = latex_content.replace('AVG_IMPROVEMENT', f"{analysis['statistics']['avg_improvement']:.1f}")
        latex_content = latex_content.replace('MEDIAN_IMPROVEMENT', f"{analysis['statistics']['median_improvement']:.1f}")
        latex_content = latex_content.replace('MAX_IMPROVEMENT', f"{analysis['statistics']['max_improvement']:.1f}")
        latex_content = latex_content.replace('MIN_IMPROVEMENT', f"{analysis['statistics']['min_improvement']:.1f}")
        
        with open(latex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
    
    def _generate_csv_table(self, analysis: Dict[str, Any], output_dir: Path) -> None:
        """生成CSV格式的表格"""
        csv_file = output_dir / 'performance_results.csv'
        
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("Test Case,Original Time (s),Summarized Time (s),Speedup,Improvement (%)\n")
            
            for test_name, data in analysis['test_analysis'].items():
                f.write(f"{test_name},{data['pure_time']:.3f},{data['summary_time']:.3f},{data['speedup']:.3f},{data['improvement']:.2f}\n")
    
    def _generate_markdown_table(self, analysis: Dict[str, Any], output_dir: Path) -> None:
        """生成Markdown格式的表格"""
        md_file = output_dir / 'performance_results.md'
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Concrete Execution Performance Results\n\n")
            
            f.write("## Overall Performance Comparison\n\n")
            f.write("| Metric | Original Semantics | Summarized Semantics |\n")
            f.write("|--------|-------------------|---------------------|\n")
            f.write(f"| Total Execution Time | {analysis['pure_total_time']:.2f}s | {analysis['summary_total_time']:.2f}s |\n")
            f.write(f"| Speedup Factor | 1.00x | {analysis['total_speedup']:.2f}x |\n")
            f.write(f"| Performance Improvement | 0.0% | {analysis['total_improvement']:.1f}% |\n\n")
            
            f.write("## Statistical Summary\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Number of Test Cases | {analysis['statistics']['num_tests']} |\n")
            f.write(f"| Comparable Test Cases | {analysis['statistics']['num_comparable']} |\n")
            f.write(f"| Average Speedup | {analysis['statistics']['avg_speedup']:.2f}x |\n")
            f.write(f"| Median Speedup | {analysis['statistics']['median_speedup']:.2f}x |\n")
            f.write(f"| Maximum Speedup | {analysis['statistics']['max_speedup']:.2f}x |\n")
            f.write(f"| Minimum Speedup | {analysis['statistics']['min_speedup']:.2f}x |\n")
            f.write(f"| Average Improvement | {analysis['statistics']['avg_improvement']:.1f}% |\n")
            f.write(f"| Median Improvement | {analysis['statistics']['median_improvement']:.1f}% |\n")
            f.write(f"| Maximum Improvement | {analysis['statistics']['max_improvement']:.1f}% |\n")
            f.write(f"| Minimum Improvement | {analysis['statistics']['min_improvement']:.1f}% |\n\n")
            
            f.write("## Detailed Test Case Results\n\n")
            f.write("| Test Case | Original Time (s) | Summarized Time (s) | Speedup | Improvement (%) |\n")
            f.write("|-----------|------------------|-------------------|---------|----------------|\n")
            
            # 按性能提升排序
            sorted_tests = sorted(
                analysis['test_analysis'].items(),
                key=lambda x: x[1]['speedup'],
                reverse=True
            )
            
            for test_name, data in sorted_tests[:50]:  # 只显示前50个
                f.write(f"| {test_name} | {data['pure_time']:.3f} | {data['summary_time']:.3f} | {data['speedup']:.3f}x | {data['improvement']:.2f}% |\n")
    
    def _generate_symbolic_latex_table(self, analysis: Dict[str, Any], output_dir: Path) -> None:
        """生成symbolic execution LaTeX格式的表格"""
        latex_file = output_dir / 'symbolic_execution_performance_results.tex'
        
        # 使用字符串替换而不是格式化来避免&字符的问题
        latex_template = r"""\documentclass{article}
\usepackage{booktabs}
\usepackage{siunitx}
\usepackage{graphicx}

\begin{document}

\section{Symbolic Execution Performance Results}

\subsection{Overall Performance Comparison}

\begin{table}[h]
\centering
\caption{Overall Performance Comparison between Original and Summarized Semantics}
\begin{tabular}{lcc}
\toprule
Metric & Original Semantics & Summarized Semantics \\
\midrule
Total Execution Time & \SI{HASKELL_TOTAL_TIME}{\second} & \SI{HASKELL_SUMMARY_TOTAL_TIME}{\second} \\
Speedup Factor & 1.00x & SPEEDUP_FACTORx \\
Performance Improvement & 0.0\% & IMPROVEMENT_PERCENT\% \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Statistical Summary}

\begin{table}[h]
\centering
\caption{Statistical Summary of Performance Improvements}
\begin{tabular}{lr}
\toprule
Metric & Value \\
\midrule
Number of Test Suites & NUM_SUITES \\
Comparable Test Suites & NUM_COMPARABLE \\
Average Speedup & AVG_SPEEDUPx \\
Median Speedup & MEDIAN_SPEEDUPx \\
Maximum Speedup & MAX_SPEEDUPx \\
Minimum Speedup & MIN_SPEEDUPx \\
Average Improvement & AVG_IMPROVEMENT\% \\
Median Improvement & MEDIAN_IMPROVEMENT\% \\
Maximum Improvement & MAX_IMPROVEMENT\% \\
Minimum Improvement & MIN_IMPROVEMENT\% \\
\bottomrule
\end{tabular}
\end{table}

\end{document}
"""
        
        # 替换占位符
        latex_content = latex_template.replace('HASKELL_TOTAL_TIME', f"{analysis['haskell_total_time']:.2f}")
        latex_content = latex_content.replace('HASKELL_SUMMARY_TOTAL_TIME', f"{analysis['haskell_summary_total_time']:.2f}")
        latex_content = latex_content.replace('SPEEDUP_FACTOR', f"{analysis['total_speedup']:.2f}")
        latex_content = latex_content.replace('IMPROVEMENT_PERCENT', f"{analysis['total_improvement']:.1f}")
        latex_content = latex_content.replace('NUM_SUITES', str(analysis['statistics']['num_suites']))
        latex_content = latex_content.replace('NUM_COMPARABLE', str(analysis['statistics']['num_comparable_suites']))
        latex_content = latex_content.replace('AVG_SPEEDUP', f"{analysis['statistics']['avg_suite_speedup']:.2f}")
        latex_content = latex_content.replace('MEDIAN_SPEEDUP', f"{analysis['statistics']['median_suite_speedup']:.2f}")
        latex_content = latex_content.replace('MAX_SPEEDUP', f"{analysis['statistics']['max_suite_speedup']:.2f}")
        latex_content = latex_content.replace('MIN_SPEEDUP', f"{analysis['statistics']['min_suite_speedup']:.2f}")
        latex_content = latex_content.replace('AVG_IMPROVEMENT', f"{analysis['statistics']['avg_suite_improvement']:.1f}")
        latex_content = latex_content.replace('MEDIAN_IMPROVEMENT', f"{analysis['statistics']['median_suite_improvement']:.1f}")
        latex_content = latex_content.replace('MAX_IMPROVEMENT', f"{analysis['statistics']['max_suite_improvement']:.1f}")
        latex_content = latex_content.replace('MIN_IMPROVEMENT', f"{analysis['statistics']['min_suite_improvement']:.1f}")
        
        with open(latex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
    
    def _generate_symbolic_csv_table(self, analysis: Dict[str, Any], output_dir: Path) -> None:
        """生成symbolic execution CSV格式的表格"""
        csv_file = output_dir / 'symbolic_execution_performance_results.csv'
        
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("Test Suite,Original Time (s),Summarized Time (s),Speedup,Improvement (%)\n")
            
            for suite_name, data in analysis['suite_analysis'].items():
                f.write(f"{suite_name},{data['haskell_time']:.3f},{data['haskell_summary_time']:.3f},{data['speedup']:.3f},{data['improvement']:.2f}\n")
    
    def _generate_symbolic_markdown_table(self, analysis: Dict[str, Any], output_dir: Path) -> None:
        """生成symbolic execution Markdown格式的表格"""
        md_file = output_dir / 'symbolic_execution_performance_results.md'
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Symbolic Execution Performance Results\n\n")
            
            f.write("## Overall Performance Comparison\n\n")
            f.write("| Metric | Original Semantics | Summarized Semantics |\n")
            f.write("|--------|-------------------|---------------------|\n")
            f.write(f"| Total Execution Time | {analysis['haskell_total_time']:.2f}s | {analysis['haskell_summary_total_time']:.2f}s |\n")
            f.write(f"| Speedup Factor | 1.00x | {analysis['total_speedup']:.2f}x |\n")
            f.write(f"| Performance Improvement | 0.0% | {analysis['total_improvement']:.1f}% |\n\n")
            
            f.write("## Statistical Summary\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Number of Test Suites | {analysis['statistics']['num_suites']} |\n")
            f.write(f"| Comparable Test Suites | {analysis['statistics']['num_comparable_suites']} |\n")
            f.write(f"| Average Speedup | {analysis['statistics']['avg_suite_speedup']:.2f}x |\n")
            f.write(f"| Median Speedup | {analysis['statistics']['median_suite_speedup']:.2f}x |\n")
            f.write(f"| Maximum Speedup | {analysis['statistics']['max_suite_speedup']:.2f}x |\n")
            f.write(f"| Minimum Speedup | {analysis['statistics']['min_suite_speedup']:.2f}x |\n")
            f.write(f"| Average Improvement | {analysis['statistics']['avg_suite_improvement']:.1f}% |\n")
            f.write(f"| Median Improvement | {analysis['statistics']['median_suite_improvement']:.1f}% |\n")
            f.write(f"| Maximum Improvement | {analysis['statistics']['max_suite_improvement']:.1f}% |\n")
            f.write(f"| Minimum Improvement | {analysis['statistics']['min_suite_improvement']:.1f}% |\n\n")
            
            f.write("## Detailed Test Suite Results\n\n")
            f.write("| Test Suite | Original Time (s) | Summarized Time (s) | Speedup | Improvement (%) |\n")
            f.write("|-----------|------------------|-------------------|---------|----------------|\n")
            
            # 按性能提升排序
            sorted_suites = sorted(
                analysis['suite_analysis'].items(),
                key=lambda x: x[1]['speedup'],
                reverse=True
            )
            
            for suite_name, data in sorted_suites[:50]:  # 只显示前50个
                f.write(f"| {suite_name} | {data['haskell_time']:.3f} | {data['haskell_summary_time']:.3f} | {data['speedup']:.3f}x | {data['improvement']:.2f}% |\n")
    
    def save_concrete_performance_result(self, output_dir: Path) -> None:
        """
        保存concrete execution性能分析结果
        
        Args:
            output_dir: 输出目录
        """
        if "concrete_execution_performance" not in self.results:
            print("警告: 没有concrete execution性能数据，跳过结果保存")
            return
        
        # 创建concrete execution专用输出目录
        concrete_output_dir = output_dir / "concrete_execution"
        concrete_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON格式的原始数据
        performance_file = concrete_output_dir / 'concrete_execution_performance.json'
        with open(performance_file, 'w', encoding='utf-8') as f:
            json.dump(self.results["concrete_execution_performance"], f, indent=2, ensure_ascii=False)
        
        # 生成图表
        self.generate_performance_charts(concrete_output_dir)
        
        # 生成表格
        self.generate_academic_tables(concrete_output_dir)
        
        print(f"✓ Concrete execution性能分析结果已保存到: {concrete_output_dir}")
    
    def save_symbolic_performance_result(self, output_dir: Path) -> None:
        """
        保存symbolic execution性能分析结果
        
        Args:
            output_dir: 输出目录
        """
        if "symbolic_execution_performance" not in self.results:
            print("警告: 没有symbolic execution性能数据，跳过结果保存")
            return
        
        # 创建symbolic execution专用输出目录
        symbolic_output_dir = output_dir / "symbolic_execution"
        symbolic_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON格式的原始数据
        performance_file = symbolic_output_dir / 'symbolic_execution_performance.json'
        with open(performance_file, 'w', encoding='utf-8') as f:
            json.dump(self.results["symbolic_execution_performance"], f, indent=2, ensure_ascii=False)
        
        # 生成图表
        self.generate_symbolic_performance_charts(symbolic_output_dir)
        
        # 生成表格
        self.generate_symbolic_academic_tables(symbolic_output_dir)
        
        print(f"✓ Symbolic execution性能分析结果已保存到: {symbolic_output_dir}")
    
    def save_all_performance_results(self, output_dir: Path) -> None:
        """
        保存所有性能分析结果（concrete和symbolic execution）
        
        Args:
            output_dir: 输出目录
        """
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存concrete execution结果
        self.save_concrete_performance_result(output_dir)
        
        # 保存symbolic execution结果
        self.save_symbolic_performance_result(output_dir)
        
        print(f"✓ 所有性能分析结果已保存到: {output_dir}")
    
    def _save_readable_file(self, output_dir: Path, test_name: str, data: dict) -> None:
        """保存单个测试结果的人可读文件"""
        file_path = output_dir / f"{test_name}.txt"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{test_name.upper()} RESULT\n")
            f.write("=" * (len(test_name) + 8) + "\n\n")
            
            # 基本信息
            f.write(f"Success: {data.get('success', 'Unknown')}\n")
            if data.get('duration'):
                f.write(f"Duration: {data['duration']:.2f} seconds\n")
            if data.get('error'):
                f.write(f"Error: {data['error']}\n")
            
            # 输出信息
            if data.get('stdout'):
                f.write(f"\nSTDOUT:\n{data['stdout']}\n")
            if data.get('stderr'):
                f.write(f"\nSTDERR:\n{data['stderr']}\n")
    
    def save_and_print_summary(self, skipped_steps: set = None) -> None:
        """保存所有结果并打印摘要"""
        if skipped_steps is None:
            skipped_steps = set()
            
        # 创建主输出目录
        output_dir = PROJECT_ROOT / "evaluation_results"
        output_dir.mkdir(exist_ok=True)
        
        # 保存JSON格式的完整结果到主目录
        results_file = output_dir / "evaluation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # 保存命令记录到主目录
        self.save_commands(output_dir)
        
        # 保存性能分析结果到各自的子目录
        self.save_all_performance_results(output_dir)
        

        
        # 保存各个测试步骤的结果到各自的子目录
        for test_name, data in self.results.items():
            if isinstance(data, dict) and test_name not in ["summarize_eval", "concrete_execution_performance", "symbolic_execution_performance"]:
                # 为每个测试步骤创建子目录
                test_output_dir = output_dir / test_name
                test_output_dir.mkdir(exist_ok=True)
                self._save_readable_file(test_output_dir, test_name, data)
        
        # 保存summarize评估结果到专门的子目录
        if self.results.get("summarize_eval"):
            summarize_output_dir = output_dir / "summarize_evaluation"
            summarize_output_dir.mkdir(exist_ok=True)
            self.save_summarize_eval_results(summarize_output_dir)
        
        # 打印摘要
        self._print_summary(skipped_steps)
        
        print(f"\n所有结果已保存到: {output_dir}")
        print("目录结构:")
        print(f"  {output_dir}/")
        print(f"    ├── evaluation_results.json (完整结果)")
        print(f"    ├── executed_commands.json (命令记录)")
        print(f"    ├── executed_commands.log (命令日志)")
        print(f"    ├── build/ (构建测试结果)")
        print(f"    ├── conformance_test/ (一致性测试结果)")
        print(f"    ├── prove_summaries_test/ (prove summaries测试结果)")
        print(f"    ├── concrete_execution/ (concrete execution性能分析)")
        print(f"    ├── symbolic_execution/ (symbolic execution性能分析)")
        print(f"    └── summarize_evaluation/ (summarize评估结果)")
    
    def save_summarize_eval_results(self, output_dir: Path) -> None:
        """保存summarize评估结果"""
        summarize_file = output_dir / "summarize_evaluation.txt"
        
        with open(summarize_file, 'w', encoding='utf-8') as f:
            f.write("SUMMARIZE EVALUATION RESULTS\n")
            f.write("=" * 30 + "\n\n")
            
            def pretty_category(cat: str) -> str:
                return cat.replace('_', ' ').title()
                
            for result in self.results["summarize_eval"]:
                f.write(f"Opcode: {result['opcode']}\n")
                f.write(f"Category: {pretty_category(result['category'])}\n")
                f.write(f"Status: {result['status']}\n")
                if result.get('error'):
                    f.write(f"Error: {result['error']}\n")
                f.write("-" * 20 + "\n\n")
    
    def _print_summary(self, skipped_steps: set = None) -> None:
        """打印评估结果摘要"""
        if skipped_steps is None:
            skipped_steps = set()
            
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        
        # 基本信息
        timestamp = self.results.get("timestamp", "Unknown")
        print(f"Evaluation Time: {timestamp}")
        
        # 构建结果
        build = self.results.get("build", {})
        if 'build' in skipped_steps:
            print(f"\nBuild: ⏭️ SKIPPED")
        else:
            print(f"\nBuild: {'✓ SUCCESS' if build.get('success') else '✗ FAILED'}")
            if build.get('duration'):
                print(f"  Duration: {build['duration']:.2f}s")
        
        # 一致性测试结果
        conformance = self.results.get("conformance_test", {})
        if 'conformance' in skipped_steps:
            print(f"\nConformance Test: ⏭️ SKIPPED")
        else:
            print(f"\nConformance Test: {'✓ SUCCESS' if conformance.get('success') else '✗ FAILED'}")
            if conformance.get('duration'):
                print(f"  Duration: {conformance['duration']:.2f}s")
        
        # Prove summaries测试结果
        prove = self.results.get("prove_summaries_test", {})
        if 'prove' in skipped_steps:
            print(f"\nProve Summaries Test: ⏭️ SKIPPED")
        else:
            print(f"\nProve Summaries Test: {'✓ SUCCESS' if prove.get('success') else '✗ FAILED'}")
            if prove.get('duration'):
                print(f"  Duration: {prove['duration']:.2f}s")
        
        # Concrete execution性能对比结果
        performance = self.results.get("concrete_execution_performance", {})
        if performance and "analysis" in performance:
            analysis = performance["analysis"]
            print(f"\nConcrete Execution Performance: {'✓ SUCCESS' if performance.get('pure_semantics', {}).get('success') and performance.get('summary_semantics', {}).get('success') else '✗ FAILED'}")
            print(f"  Original Semantics Total Time: {analysis['pure_total_time']:.2f}s")
            print(f"  Summarized Semantics Total Time: {analysis['summary_total_time']:.2f}s")
            print(f"  Overall Speedup: {analysis['total_speedup']:.2f}x")
            print(f"  Performance Improvement: {analysis['total_improvement']:.1f}%")
        
        # Symbolic execution性能对比结果
        symbolic_performance = self.results.get("symbolic_execution_performance", {})
        if symbolic_performance and "analysis" in symbolic_performance:
            analysis = symbolic_performance["analysis"]
            print(f"\nSymbolic Execution Performance: {'✓ SUCCESS' if symbolic_performance.get('haskell_semantics', {}).get('success') and symbolic_performance.get('haskell_summary_semantics', {}).get('success') else '✗ FAILED'}")
            print(f"  Original Semantics Total Time: {analysis['haskell_total_time']:.2f}s")
            print(f"  Summarized Semantics Total Time: {analysis['haskell_summary_total_time']:.2f}s")
            print(f"  Overall Speedup: {analysis['total_speedup']:.2f}x")
            print(f"  Performance Improvement: {analysis['total_improvement']:.1f}%")
        
        # Summarize评估结果
        summarize_eval = self.results.get("summarize_eval", [])
        if summarize_eval:
            print(f"\nSummarize Evaluation: {len(summarize_eval)} opcodes evaluated")
            success_count = sum(1 for r in summarize_eval if r.get('status') == 'SUCCESS')
            print(f"  Success: {success_count}/{len(summarize_eval)}")


    def _generate_symbolic_performance_boxplot(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成symbolic execution性能提升箱线图"""
        speedups = [data['speedup'] for data in suite_analysis.values() if data['speedup'] > 0]
        improvements = [data['improvement'] for data in suite_analysis.values() if data['improvement'] != 0]
        
        if not speedups:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 性能提升箱线图
        ax1.boxplot(speedups, patch_artist=True, boxprops=dict(facecolor='lightblue', alpha=0.7))
        ax1.set_ylabel('Speedup Factor')
        ax1.set_title('Symbolic Execution: Speedup Distribution')
        ax1.grid(True, alpha=0.3)
        
        # 改进百分比箱线图
        ax2.boxplot(improvements, patch_artist=True, boxprops=dict(facecolor='lightgreen', alpha=0.7))
        ax2.set_ylabel('Improvement (%)')
        ax2.set_title('Symbolic Execution: Improvement Distribution')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_performance_boxplot.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_performance_boxplot.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_suite_size_vs_performance_plot(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成测试套件大小vs性能提升散点图"""
        suite_sizes = []
        speedups = []
        improvements = []
        
        for data in suite_analysis.values():
            if data['haskell_time'] > 0 and data['haskell_summary_time'] > 0:
                suite_sizes.append(data['haskell_test_count'])
                speedups.append(data['speedup'])
                improvements.append(data['improvement'])
        
        if not suite_sizes:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 套件大小vs性能提升
        ax1.scatter(suite_sizes, speedups, alpha=0.6, s=30)
        ax1.set_xlabel('Test Suite Size (Number of Tests)')
        ax1.set_ylabel('Speedup Factor')
        ax1.set_title('Symbolic Execution: Suite Size vs Speedup')
        ax1.grid(True, alpha=0.3)
        
        # 添加趋势线
        if len(suite_sizes) > 1:
            z = np.polyfit(suite_sizes, speedups, 1)
            p = np.poly1d(z)
            ax1.plot(suite_sizes, p(suite_sizes), "r--", alpha=0.8)
        
        # 套件大小vs改进百分比
        ax2.scatter(suite_sizes, improvements, alpha=0.6, s=30, color='orange')
        ax2.set_xlabel('Test Suite Size (Number of Tests)')
        ax2.set_ylabel('Improvement (%)')
        ax2.set_title('Symbolic Execution: Suite Size vs Improvement')
        ax2.grid(True, alpha=0.3)
        
        # 添加趋势线
        if len(suite_sizes) > 1:
            z = np.polyfit(suite_sizes, improvements, 1)
            p = np.poly1d(z)
            ax2.plot(suite_sizes, p(suite_sizes), "r--", alpha=0.8)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_suite_size_vs_performance.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_suite_size_vs_performance.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_improvement_distribution_plot(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成性能提升百分比分布图"""
        improvements = [data['improvement'] for data in suite_analysis.values() if data['improvement'] != 0]
        
        if not improvements:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 改进百分比直方图
        ax1.hist(improvements, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_xlabel('Improvement (%)')
        ax1.set_ylabel('Number of Test Suites')
        ax1.set_title('Symbolic Execution: Improvement Distribution')
        ax1.grid(True, alpha=0.3)
        
        # 改进百分比区间统计
        bins = [0, 25, 50, 75, 100, float('inf')]
        labels = ['0-25%', '25-50%', '50-75%', '75-100%', '>100%']
        counts = []
        
        for i in range(len(bins)-1):
            count = sum(1 for imp in improvements if bins[i] <= imp < bins[i+1])
            counts.append(count)
        
        ax2.bar(labels, counts, color=['lightcoral', 'lightblue', 'lightgreen', 'gold', 'plum'], alpha=0.8)
        ax2.set_xlabel('Improvement Range')
        ax2.set_ylabel('Number of Test Suites')
        ax2.set_title('Symbolic Execution: Improvement Range Distribution')
        ax2.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, count in enumerate(counts):
            ax2.text(i, count + 0.1, str(count), ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_improvement_distribution.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_improvement_distribution.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_time_distribution_comparison(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成时间分布对比图"""
        original_times = []
        summarized_times = []
        
        for data in suite_analysis.values():
            if data['haskell_time'] > 0 and data['haskell_summary_time'] > 0:
                original_times.append(data['haskell_time'])
                summarized_times.append(data['haskell_summary_time'])
        
        if not original_times:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 时间分布直方图对比
        ax1.hist(original_times, bins=20, alpha=0.7, label='Original Semantics', color='red')
        ax1.hist(summarized_times, bins=20, alpha=0.7, label='Summarized Semantics', color='blue')
        ax1.set_xlabel('Execution Time (seconds)')
        ax1.set_ylabel('Number of Test Suites')
        ax1.set_title('Symbolic Execution: Time Distribution Comparison')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 时间分布箱线图对比
        ax2.boxplot([original_times, summarized_times], labels=['Original', 'Summarized'], 
                   patch_artist=True, boxprops=dict(facecolor='lightblue', alpha=0.7))
        ax2.set_ylabel('Execution Time (seconds)')
        ax2.set_title('Symbolic Execution: Time Distribution Boxplot')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_time_distribution_comparison.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_time_distribution_comparison.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_performance_heatmap(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成性能提升热力图（按测试类型分组）"""
        # 按测试类型分组
        test_categories = {}
        
        for suite_name, data in suite_analysis.items():
            if data['haskell_time'] > 0 and data['haskell_summary_time'] > 0:
                # 提取测试类型（从套件名称中）
                if 'erc20' in suite_name.lower():
                    category = 'ERC20'
                elif 'mcd' in suite_name.lower():
                    category = 'MCD'
                elif 'benchmarks' in suite_name.lower():
                    category = 'Benchmarks'
                elif 'kontrol' in suite_name.lower():
                    category = 'Kontrol'
                elif 'examples' in suite_name.lower():
                    category = 'Examples'
                else:
                    category = 'Other'
                
                if category not in test_categories:
                    test_categories[category] = []
                test_categories[category].append(data['speedup'])
        
        if not test_categories:
            return
        
        # 计算每个类别的平均性能提升
        categories = list(test_categories.keys())
        avg_speedups = [np.mean(test_categories[cat]) for cat in categories]
        
        # 创建热力图数据
        heatmap_data = np.array(avg_speedups).reshape(1, -1)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
        
        # 设置标签
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories)
        ax.set_yticks([])
        ax.set_title('Symbolic Execution: Average Speedup by Test Category')
        
        # 添加数值标签
        for i, speedup in enumerate(avg_speedups):
            ax.text(i, 0, f'{speedup:.2f}x', ha='center', va='center', fontweight='bold')
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Speedup Factor')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_performance_heatmap.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_performance_heatmap.pdf', bbox_inches='tight')
        plt.close()
    
    def _generate_symbolic_cumulative_improvement_plot(self, suite_analysis: Dict[str, Dict], output_dir: Path) -> None:
        """生成累积性能提升图"""
        # 按性能提升排序
        sorted_suites = sorted(
            [(name, data) for name, data in suite_analysis.items() if data['speedup'] > 0],
            key=lambda x: x[1]['speedup'],
            reverse=True
        )
        
        if not sorted_suites:
            return
        
        suite_names = [name for name, _ in sorted_suites]
        speedups = [data['speedup'] for _, data in sorted_suites]
        improvements = [data['improvement'] for _, data in sorted_suites]
        
        # 计算累积值
        cumulative_speedup = np.cumsum(speedups)
        cumulative_improvement = np.cumsum(improvements)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 累积性能提升
        ax1.plot(range(1, len(suite_names) + 1), cumulative_speedup, 'b-', linewidth=2, marker='o', markersize=4)
        ax1.set_xlabel('Number of Test Suites')
        ax1.set_ylabel('Cumulative Speedup Factor')
        ax1.set_title('Symbolic Execution: Cumulative Speedup')
        ax1.grid(True, alpha=0.3)
        
        # 累积改进百分比
        ax2.plot(range(1, len(suite_names) + 1), cumulative_improvement, 'g-', linewidth=2, marker='s', markersize=4)
        ax2.set_xlabel('Number of Test Suites')
        ax2.set_ylabel('Cumulative Improvement (%)')
        ax2.set_title('Symbolic Execution: Cumulative Improvement')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'symbolic_cumulative_improvement.png', dpi=300, bbox_inches='tight')
        plt.savefig(output_dir / 'symbolic_cumulative_improvement.pdf', bbox_inches='tight')
        plt.close()


# 全局recorder实例
recorder = EvaluationRecorder() 