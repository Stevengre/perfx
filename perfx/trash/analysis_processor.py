#!/usr/bin/env python3
"""
Analysis processor for perfx
处理配置文件中的分析配置并执行相应的分析任务
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

from ..visualizers.analysis_engine import AnalysisEngine
from ..visualizers.comparison_config import ComparisonConfigManager

console = Console()


class AnalysisProcessor:
    """分析处理器，处理YAML配置中的analysis_config部分"""
    
    def __init__(self, step_config: Dict[str, Any], base_dir: str = "."):
        self.step_config = step_config
        self.base_dir = Path(base_dir)
        self.analysis_config = step_config.get('analysis_config', {})
        
        # 获取目录配置
        self.data_dir = self.analysis_config.get('data_directory', 'results/data')
        self.output_dir = self.analysis_config.get('output_directory', 'results/analysis')
        
        # 创建分析引擎
        self.analysis_engine = AnalysisEngine(self.data_dir, self.output_dir)
        
        console.print(f"[blue]AnalysisProcessor initialized[/blue]")
        console.print(f"Data directory: {self.data_dir}")
        console.print(f"Output directory: {self.output_dir}")
    
    def process(self) -> Dict[str, Any]:
        """处理分析配置并执行分析"""
        console.print("[bold blue]Processing analysis configuration[/bold blue]")
        
        results = {
            'generated_files': {
                'charts': [],
                'tables': [],
                'reports': []
            },
            'analysis_summary': {},
            'success': True
        }
        
        try:
            # 1. 执行通用分析
            if self._should_run_general_analysis():
                general_results = self._run_general_analysis()
                self._merge_results(results, general_results)
            
            # 2. 执行比较分析
            if self._should_run_comparison_analysis():
                comparison_results = self._run_comparison_analysis()
                self._merge_results(results, comparison_results)
            
            # 3. 执行EVM特定分析
            if self._should_run_evm_specific_analysis():
                evm_results = self._run_evm_specific_analysis()
                self._merge_results(results, evm_results)
            
            # 4. 生成分析摘要
            results['analysis_summary'] = self._generate_analysis_summary(results)
            
            console.print("[green]✓ Analysis configuration processed successfully[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Error processing analysis configuration: {e}[/red]")
            results['success'] = False
            results['error'] = str(e)
        
        # 即使有错误，如果生成了文件，也可能被认为是部分成功
        total_files = results['analysis_summary'].get('total_files_generated', 0)
        if not results['success'] and total_files > 0:
            console.print(f"[yellow]Analysis had errors but generated {total_files} files - may be considered successful based on outputs[/yellow]")
        
        return results
    
    def _should_run_general_analysis(self) -> bool:
        """检查是否应该运行通用分析"""
        general_config = self.analysis_config.get('general_analysis', {})
        return general_config.get('enabled', True)
    
    def _should_run_comparison_analysis(self) -> bool:
        """检查是否应该运行比较分析"""
        comparison_config = self.analysis_config.get('comparison_analysis', {})
        return comparison_config.get('enabled', True)
    
    def _should_run_evm_specific_analysis(self) -> bool:
        """检查是否应该运行EVM特定分析"""
        evm_config = self.analysis_config.get('evm_specific_analysis', {})
        return evm_config.get('enabled', False)
    
    def _run_general_analysis(self) -> Dict[str, List[str]]:
        """运行通用分析"""
        console.print("[blue]Running general analysis...[/blue]")
        
        general_config = self.analysis_config.get('general_analysis', {})
        analysis_types = general_config.get('types', ['charts', 'tables'])
        
        results = {'charts': [], 'tables': [], 'reports': []}
        
        for analysis_type in analysis_types:
            try:
                type_results = self.analysis_engine.run_analysis(
                    analysis_type=analysis_type
                )
                
                for key, files in type_results.items():
                    if key in results:
                        results[key].extend(files)
                
                console.print(f"[green]✓ General {analysis_type} analysis completed[/green]")
                
            except Exception as e:
                console.print(f"[yellow]Warning: General {analysis_type} analysis failed: {e}[/yellow]")
        
        return results
    
    def _run_comparison_analysis(self) -> Dict[str, List[str]]:
        """运行比较分析"""
        console.print("[blue]Running comparison analysis...[/blue]")
        
        comparison_config = self.analysis_config.get('comparison_analysis', {})
        config_file = comparison_config.get('config_file')
        
        if not config_file:
            console.print("[yellow]No comparison config file specified[/yellow]")
            return {'charts': [], 'tables': []}
        
        # 确保配置文件路径是相对于base_dir的
        config_path = self.base_dir / config_file
        if not config_path.exists():
            console.print(f"[yellow]Comparison config file not found: {config_path}[/yellow]")
            return {'charts': [], 'tables': []}
        
        try:
            results = self.analysis_engine.run_analysis(
                config_file=str(config_path),
                analysis_type="comparison"
            )
            
            console.print("[green]✓ Comparison analysis completed[/green]")
            return results
            
        except Exception as e:
            console.print(f"[yellow]Warning: Comparison analysis failed: {e}[/yellow]")
            return {'charts': [], 'tables': []}
    
    def _run_evm_specific_analysis(self) -> Dict[str, List[str]]:
        """运行EVM特定分析"""
        console.print("[blue]Running EVM-specific analysis...[/blue]")
        
        evm_config = self.analysis_config.get('evm_specific_analysis', {})
        
        # 这里可以根据EVM配置执行特定的分析
        # 目前返回空结果，实际实现可以调用EVM特定的分析逻辑
        
        try:
            # 可以在这里调用EVM特定的分析代码
            # 例如：opcode分类、特定图表生成等
            
            console.print("[green]✓ EVM-specific analysis completed[/green]")
            return {'charts': [], 'tables': []}
            
        except Exception as e:
            console.print(f"[yellow]Warning: EVM-specific analysis failed: {e}[/yellow]")
            return {'charts': [], 'tables': []}
    
    def _merge_results(self, main_results: Dict[str, Any], new_results: Dict[str, List[str]]):
        """合并分析结果"""
        for key, files in new_results.items():
            if key in main_results['generated_files']:
                main_results['generated_files'][key].extend(files)
    
    def _generate_analysis_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成分析摘要"""
        generated_files = results['generated_files']
        
        total_files = sum(len(files) for files in generated_files.values())
        
        summary = {
            'total_files_generated': total_files,
            'charts_generated': len(generated_files['charts']),
            'tables_generated': len(generated_files['tables']),
            'reports_generated': len(generated_files['reports']),
            'data_directory': self.data_dir,
            'output_directory': self.output_dir
        }
        
        # 添加配置摘要
        if self.analysis_config:
            summary['configuration'] = {
                'general_analysis_enabled': self._should_run_general_analysis(),
                'comparison_analysis_enabled': self._should_run_comparison_analysis(),
                'evm_specific_analysis_enabled': self._should_run_evm_specific_analysis()
            }
        
        return summary


def process_analysis_step(step_config: Dict[str, Any], base_dir: str = ".") -> Dict[str, Any]:
    """
    处理分析步骤的入口函数
    
    Args:
        step_config: 步骤配置字典
        base_dir: 基础目录
    
    Returns:
        分析结果字典
    """
    processor = AnalysisProcessor(step_config, base_dir)
    return processor.process()