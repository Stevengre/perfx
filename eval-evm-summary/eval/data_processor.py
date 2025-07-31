#!/usr/bin/env python3
"""
数据处理器模块
用于分离数据解析、统计分析和图表生成功能
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import matplotlib.pyplot as plt

from .evaluation_recorder import EvaluationRecorder


class DataProcessor:
    """数据处理器，用于解析已保存的命令执行结果并生成图表"""
    
    def __init__(self, results_dir: str = "evaluation_results"):
        """
        初始化数据处理器
        
        Args:
            results_dir: 结果目录路径
        """
        self.results_dir = Path(results_dir)
        self.recorder = EvaluationRecorder()
        
    def load_executed_commands(self) -> List[Dict[str, Any]]:
        """加载已执行的命令数据"""
        commands_file = self.results_dir / "executed_commands.json"
        if not commands_file.exists():
            raise FileNotFoundError(f"找不到文件: {commands_file}")
        
        with open(commands_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_evaluation_results(self) -> Dict[str, Any]:
        """加载评估结果数据"""
        results_file = self.results_dir / "evaluation_results.json"
        if not results_file.exists():
            raise FileNotFoundError(f"找不到文件: {results_file}")
        
        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parse_concrete_execution_data(self, commands_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """解析concrete execution数据"""
        print("解析concrete execution数据...")
        
        # 查找concrete execution相关的命令
        concrete_commands = []
        for cmd in commands_data:
            command = cmd.get('command', '')
            if 'test-conformance' in command or 'concrete' in command.lower():
                concrete_commands.append(cmd)
        
        if not concrete_commands:
            print("警告: 没有找到concrete execution相关的命令")
            return {}
        
        # 解析pytest输出
        pure_durations = {}
        summary_durations = {}
        
        for cmd in concrete_commands:
            output = cmd.get('output', '')
            if not output:
                continue
            
            # 解析pytest输出中的时间信息
            lines = output.split('\n')
            for line in lines:
                if '::' in line and 'passed' in line:
                    # 提取测试名称和时间
                    parts = line.split()
                    if len(parts) >= 2:
                        test_name = parts[0]
                        # 查找时间信息
                        for part in parts:
                            if part.endswith('s') and part[:-1].replace('.', '').isdigit():
                                duration = float(part[:-1])
                                if 'pure' in cmd.get('command', '').lower():
                                    pure_durations[test_name] = duration
                                elif 'summary' in cmd.get('command', '').lower():
                                    summary_durations[test_name] = duration
                                break
        
        return {
            'pure_durations': pure_durations,
            'summary_durations': summary_durations
        }
    
    def parse_symbolic_execution_data(self, commands_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """解析symbolic execution数据"""
        print("解析symbolic execution数据...")
        
        # 查找symbolic execution相关的命令
        symbolic_commands = []
        for cmd in commands_data:
            command = cmd.get('command', '')
            if 'test-prove' in command or 'symbolic' in command.lower():
                symbolic_commands.append(cmd)
        
        if not symbolic_commands:
            print("警告: 没有找到symbolic execution相关的命令")
            return {}
        
        # 解析pytest输出
        haskell_durations = {}
        haskell_summary_durations = {}
        
        current_suite = None
        for cmd in symbolic_commands:
            output = cmd.get('output', '')
            if not output:
                continue
            
            # 解析pytest输出中的时间信息
            lines = output.split('\n')
            for line in lines:
                if '::' in line and 'passed' in line:
                    # 提取测试名称和时间
                    parts = line.split()
                    if len(parts) >= 2:
                        test_name = parts[0]
                        # 查找时间信息
                        for part in parts:
                            if part.endswith('s') and part[:-1].replace('.', '').isdigit():
                                duration = float(part[:-1])
                                suite_name = f"suite_{len(haskell_durations)}"
                                
                                if 'pure' in cmd.get('command', '').lower():
                                    if suite_name not in haskell_durations:
                                        haskell_durations[suite_name] = {}
                                    haskell_durations[suite_name][test_name] = duration
                                elif 'summary' in cmd.get('command', '').lower():
                                    if suite_name not in haskell_summary_durations:
                                        haskell_summary_durations[suite_name] = {}
                                    haskell_summary_durations[suite_name][test_name] = duration
                                break
        
        return {
            'haskell_durations': haskell_durations,
            'haskell_summary_durations': haskell_summary_durations
        }
    
    def generate_concrete_performance_analysis(self, concrete_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成concrete execution性能分析"""
        if not concrete_data:
            return {}
        
        pure_durations = concrete_data.get('pure_durations', {})
        summary_durations = concrete_data.get('summary_durations', {})
        
        # 使用recorder的分析方法
        analysis = self.recorder.analyze_concrete_execution_performance(pure_durations, summary_durations)
        
        return analysis
    
    def generate_symbolic_performance_analysis(self, symbolic_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成symbolic execution性能分析"""
        if not symbolic_data:
            return {}
        
        haskell_durations = symbolic_data.get('haskell_durations', {})
        haskell_summary_durations = symbolic_data.get('haskell_summary_durations', {})
        
        # 使用recorder的分析方法
        analysis = self.recorder.analyze_symbolic_execution_performance(haskell_durations, haskell_summary_durations)
        
        return analysis
    
    def save_analysis_results(self, concrete_analysis: Dict[str, Any], symbolic_analysis: Dict[str, Any]):
        """保存分析结果"""
        print("保存分析结果...")
        
        # 保存concrete execution分析结果
        if concrete_analysis:
            concrete_output_dir = self.results_dir / "concrete_execution"
            concrete_output_dir.mkdir(exist_ok=True)
            
            # 保存JSON数据
            performance_file = concrete_output_dir / 'concrete_execution_performance.json'
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'analysis': concrete_analysis,
                    'success': True
                }, f, indent=2, ensure_ascii=False)
            
            # 生成图表
            self.recorder.generate_performance_charts(concrete_output_dir)
            self.recorder.generate_academic_tables(concrete_output_dir)
            print("✓ Concrete execution分析结果已保存")
        
        # 保存symbolic execution分析结果
        if symbolic_analysis:
            symbolic_output_dir = self.results_dir / "symbolic_execution"
            symbolic_output_dir.mkdir(exist_ok=True)
            
            # 保存JSON数据
            performance_file = symbolic_output_dir / 'symbolic_execution_performance.json'
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'analysis': symbolic_analysis,
                    'success': True
                }, f, indent=2, ensure_ascii=False)
            
            # 生成图表
            self.recorder.generate_symbolic_performance_charts(symbolic_output_dir)
            self.recorder.generate_symbolic_academic_tables(symbolic_output_dir)
            print("✓ Symbolic execution分析结果已保存")
    
    def process_all_data(self):
        """处理所有数据：解析、分析、生成图表"""
        print("开始处理所有数据...")
        
        try:
            # 1. 加载已执行的命令数据
            commands_data = self.load_executed_commands()
            print(f"✓ 加载了 {len(commands_data)} 条命令记录")
            
            # 2. 解析concrete execution数据
            concrete_data = self.parse_concrete_execution_data(commands_data)
            
            # 3. 解析symbolic execution数据
            symbolic_data = self.parse_symbolic_execution_data(commands_data)
            
            # 4. 生成性能分析
            concrete_analysis = self.generate_concrete_performance_analysis(concrete_data)
            symbolic_analysis = self.generate_symbolic_performance_analysis(symbolic_data)
            
            # 5. 保存分析结果和生成图表
            self.save_analysis_results(concrete_analysis, symbolic_analysis)
            
            print("✓ 所有数据处理完成")
            
        except Exception as e:
            print(f"✗ 数据处理过程中出现错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数，用于独立运行数据处理"""
    import sys
    
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    else:
        results_dir = "evaluation_results"
    
    processor = DataProcessor(results_dir)
    processor.process_all_data()


if __name__ == "__main__":
    main() 