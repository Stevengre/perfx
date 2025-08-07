#!/usr/bin/env python3
"""
Configuration-driven comparison system for performance evaluation
配置驱动的性能评估比较系统
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class ComparisonPair:
    """定义一对比较的数据"""
    name: str
    baseline_file: str
    comparison_file: str
    baseline_label: str = "Baseline"
    comparison_label: str = "Comparison"
    metric_field: str = "duration"  # 比较的指标字段


@dataclass
class ChartConfig:
    """图表配置"""
    chart_type: str  # "bar", "line", "scatter", "box", "heatmap"
    title: str
    x_label: str
    y_label: str
    output_name: str
    width: int = 10
    height: int = 6


@dataclass
class ComparisonConfig:
    """比较配置"""
    name: str
    description: str
    pairs: List[ComparisonPair]
    charts: List[ChartConfig]
    output_dir: str = "results/analysis"


class ComparisonConfigManager:
    """比较配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.comparisons: List[ComparisonConfig] = []
        
        if config_file and Path(config_file).exists():
            self.load_config(config_file)
    
    def load_config(self, config_file: str) -> None:
        """从文件加载配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.comparisons = []
        for comp_data in data.get('comparisons', []):
            pairs = [
                ComparisonPair(**pair_data) 
                for pair_data in comp_data.get('pairs', [])
            ]
            charts = [
                ChartConfig(**chart_data)
                for chart_data in comp_data.get('charts', [])
            ]
            
            comparison = ComparisonConfig(
                name=comp_data['name'],
                description=comp_data.get('description', ''),
                pairs=pairs,
                charts=charts,
                output_dir=comp_data.get('output_dir', 'results/analysis')
            )
            self.comparisons.append(comparison)
    
    def save_config(self, config_file: str) -> None:
        """保存配置到文件"""
        data = {
            'comparisons': [
                {
                    'name': comp.name,
                    'description': comp.description,
                    'pairs': [
                        {
                            'name': pair.name,
                            'baseline_file': pair.baseline_file,
                            'comparison_file': pair.comparison_file,
                            'baseline_label': pair.baseline_label,
                            'comparison_label': pair.comparison_label,
                            'metric_field': pair.metric_field
                        }
                        for pair in comp.pairs
                    ],
                    'charts': [
                        {
                            'chart_type': chart.chart_type,
                            'title': chart.title,
                            'x_label': chart.x_label,
                            'y_label': chart.y_label,
                            'output_name': chart.output_name,
                            'width': chart.width,
                            'height': chart.height
                        }
                        for chart in comp.charts
                    ],
                    'output_dir': comp.output_dir
                }
                for comp in self.comparisons
            ]
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_comparison(self, comparison: ComparisonConfig) -> None:
        """添加比较配置"""
        self.comparisons.append(comparison)
    
    def get_comparison(self, name: str) -> Optional[ComparisonConfig]:
        """获取指定名称的比较配置"""
        for comp in self.comparisons:
            if comp.name == name:
                return comp
        return None
    
    def create_performance_comparison_config(self) -> ComparisonConfig:
        """创建性能比较的默认配置"""
        pairs = [
            ComparisonPair(
                name="concrete_performance",
                baseline_file="pure_concrete_performance.json",
                comparison_file="summary_concrete_performance.json",
                baseline_label="Pure Concrete",
                comparison_label="Summary Concrete"
            ),
            ComparisonPair(
                name="symbolic_prove_rules",
                baseline_file="pure_symbolic_prove_rules_booster.json",
                comparison_file="summary_symbolic_prove_rules_booster.json",
                baseline_label="Pure Symbolic",
                comparison_label="Summary Symbolic"
            ),
            ComparisonPair(
                name="symbolic_prove_summaries",
                baseline_file="pure_symbolic_prove_summaries.json",
                comparison_file="summary_symbolic_prove_summaries.json",
                baseline_label="Pure Symbolic",
                comparison_label="Summary Symbolic"
            ),
            ComparisonPair(
                name="symbolic_prove_dss",
                baseline_file="pure_symbolic_prove_dss.json",
                comparison_file="summary_symbolic_prove_dss.json",
                baseline_label="Pure Symbolic",
                comparison_label="Summary Symbolic"
            )
        ]
        
        charts = [
            ChartConfig(
                chart_type="bar",
                title="Performance Comparison",
                x_label="Test Cases",
                y_label="Execution Time (s)",
                output_name="performance_comparison"
            ),
            ChartConfig(
                chart_type="box",
                title="Execution Time Distribution",
                x_label="Mode",
                y_label="Execution Time (s)",
                output_name="time_distribution"
            ),
            ChartConfig(
                chart_type="scatter",
                title="Pure vs Summary Performance",
                x_label="Pure Time (s)",
                y_label="Summary Time (s)",
                output_name="pure_vs_summary_scatter"
            )
        ]
        
        return ComparisonConfig(
            name="performance_evaluation",
            description="Automated performance comparison between Pure and Summary modes",
            pairs=pairs,
            charts=charts
        )