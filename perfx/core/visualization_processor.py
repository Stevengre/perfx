#!/usr/bin/env python3
"""
可视化配置处理器 - 处理YAML中的visualization_config配置
将声明式的可视化配置转换为实际的图表和表格生成
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console

console = Console()

def process_visualization_step(step: Dict[str, Any], base_dir: str) -> Dict[str, Any]:
    """
    处理可视化步骤
    
    Args:
        step: 步骤配置
        base_dir: 基础目录
        
    Returns:
        处理结果
    """
    try:
        # 检查是否有可视化配置
        if 'visualization_config' not in step:
            console.print("[yellow]No visualization configuration found in step[/yellow]")
            return {"success": False, "message": "No visualization configuration"}
        
        config = step['visualization_config']
        processor = VisualizationConfigProcessor(config, base_dir)
        
        # 处理表格
        table_results = processor.process_tables()
        
        # 处理图表
        chart_results = processor.process_charts()
        
        # 生成LaTeX文档
        if config.get('generate_latex_document', False):
            doc_results = processor.generate_latex_document()
        else:
            doc_results = {"success": True, "message": "LaTeX document generation skipped"}
        
        # 汇总结果
        total_tables = len(table_results.get('generated', []))
        total_charts = len(chart_results.get('generated', []))
        
        console.print(f"✓ Visualization processing completed")
        console.print(f"Tables: {total_tables}, Charts: {total_charts}")
        
        return {
            "success": True,
            "tables": table_results,
            "charts": chart_results,
            "latex_document": doc_results,
            "total_files": total_tables + total_charts
        }
        
    except Exception as e:
        console.print(f"[red]Error processing visualization step: {e}[/red]")
        return {"success": False, "error": str(e)}


class VisualizationConfigProcessor:
    """通用的可视化配置处理器"""
    
    def __init__(self, config: Dict[str, Any], base_dir: str):
        self.config = config
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / config.get('data_directory', 'results/processed')
        self.output_dir = self.base_dir / config.get('output_directory', 'results/analysis')
        self.console = Console()
    
    def process_tables(self) -> Dict[str, Any]:
        """处理表格配置"""
        tables = self.config.get('tables', [])
        if not tables:
            return {"generated": [], "errors": []}
        
        self.console.print(f"Processing {len(tables)} table configurations...")
        
        generated = []
        errors = []
        
        for table_config in tables:
            try:
                success = self._generate_table(table_config)
                if success:
                    generated.append(table_config['name'])
                    self.console.print(f"✓ Table generated: {table_config['name']}")
                else:
                    errors.append(f"Failed to generate table: {table_config['name']}")
            except Exception as e:
                errors.append(f"Error generating table {table_config['name']}: {e}")
        
        return {"generated": generated, "errors": errors}
    
    def process_charts(self) -> Dict[str, Any]:
        """处理图表配置"""
        charts = self.config.get('charts', [])
        if not charts:
            return {"generated": [], "errors": []}
        
        self.console.print(f"Processing {len(charts)} chart configurations...")
        
        generated = []
        errors = []
        
        for chart_config in charts:
            try:
                success = self._generate_chart(chart_config)
                if success:
                    generated.append(chart_config['name'])
                    self.console.print(f"✓ Chart generated: {chart_config['name']}")
                else:
                    errors.append(f"Failed to generate chart: {chart_config['name']}")
            except Exception as e:
                errors.append(f"Error generating chart {chart_config['name']}: {e}")
        
        return {"generated": generated, "errors": errors}
    
    def _generate_table(self, table_config: Dict[str, Any]) -> bool:
        """生成表格"""
        try:
            input_file = self.data_dir / table_config['input_file']
            output_file = self.output_dir / table_config['output_file']
            
            if not input_file.exists():
                self.console.print(f"[yellow]Input file not found: {input_file}[/yellow]")
                return False
            
            # 根据生成器类型选择方法
            generator = table_config.get('generator', 'simple')
            
            if generator == 'perfx.latex_tables':
                return self._generate_perfx_table(input_file, output_file, table_config)
            else:
                return self._generate_simple_table(table_config, input_file, output_file)
                
        except Exception as e:
            self.console.print(f"[red]Error generating table: {e}[/red]")
            return False
    
    def _generate_chart(self, chart_config: Dict[str, Any]) -> bool:
        """生成图表"""
        try:
            # 检查是否有多个输入文件
            if 'input_files' in chart_config:
                # 多个输入文件的情况（用于对比图表）
                input_files = [self.data_dir / f for f in chart_config['input_files']]
                output_file = self.output_dir / chart_config['output_file']
                
                # 检查所有输入文件是否存在
                for input_file in input_files:
                    if not input_file.exists():
                        self.console.print(f"[yellow]Input file not found: {input_file}[/yellow]")
                        return False
                
                return self._generate_comparison_chart(chart_config, input_files, output_file)
            else:
                # 单个输入文件的情况（原有逻辑）
                input_file = self.data_dir / chart_config['input_file']
                output_file = self.output_dir / chart_config['output_file']
                
                if not input_file.exists():
                    self.console.print(f"[yellow]Input file not found: {input_file}[/yellow]")
                    return False
                
                return self._generate_simple_chart(chart_config, input_file, output_file)
            
        except Exception as e:
            self.console.print(f"[red]Error generating chart: {e}[/red]")
            return False
    
    def _generate_perfx_table(self, input_file: Path, output_file: Path, table_config: Dict[str, Any]) -> bool:
        """使用perfx.latex_tables生成表格"""
        try:
            from perfx.visualizers.latex_tables import generate_latex_table
            
            success = generate_latex_table(
                str(input_file), 
                str(output_file), 
                table_config
            )
            
            return success
            
        except ImportError:
            self.console.print("[yellow]perfx.latex_tables not available, using simple generator[/yellow]")
            return self._generate_simple_table(table_config, input_file, output_file)
    
    def _generate_simple_table(self, table_config: Dict[str, Any], input_file: Path, output_file: Path) -> bool:
        """使用简单方法生成表格"""
        try:
            # 加载数据
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取表格数据
            data_path = table_config.get('data_path', '')
            table_data = self._extract_data_by_path(data, data_path)
            
            if not table_data:
                return False
            
            # 生成LaTeX表格
            latex_content = self._generate_latex_table_content(table_config, table_data)
            
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存表格
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            return True
        except Exception as e:
            self.console.print(f"[red]Error generating simple table: {e}[/red]")
            return False
    
    def _generate_simple_chart(self, chart_config: Dict[str, Any], input_file: Path, output_file: Path) -> bool:
        """使用简单方法生成图表"""
        try:
            # 尝试导入matplotlib
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            # 检查输入文件是否存在
            if not input_file.exists():
                self.console.print(f"[yellow]Input file not found: {input_file}[/yellow]")
                return False
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取图表数据
            data_path = chart_config.get("data_path", "")
            chart_data = self._extract_data_by_path(data, data_path)
            
            if not chart_data:
                return False
            
            # 根据图表类型生成
            chart_type = chart_config.get('type', 'bar')
            
            if chart_type == 'bar':
                success = self._generate_bar_chart(chart_config, chart_data, output_file)
            elif chart_type == 'pie':
                success = self._generate_pie_chart(chart_config, chart_data, output_file)
            elif chart_type == 'performance_comparison':
                success = self._generate_performance_comparison_chart(chart_config, chart_data, output_file)
            elif chart_type == 'performance_distribution':
                success = self._generate_performance_distribution_chart(chart_config, chart_data, output_file)
            elif chart_type == 'performance_scatter':
                success = self._generate_performance_scatter_chart(chart_config, chart_data, output_file)
            elif chart_type == 'test_case_improvement':
                success = self._generate_test_case_improvement_chart(chart_config, chart_data, output_file)
            else:
                self.console.print(f"[yellow]Unsupported chart type: {chart_type}[/yellow]")
                return False
            
            return success
            
        except ImportError:
            self.console.print("[yellow]matplotlib not available, skipping chart generation[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error generating chart: {e}[/red]")
            return False
    
    def _generate_comparison_chart(self, chart_config: Dict[str, Any], input_files: List[Path], output_file: Path) -> bool:
        """生成对比图表（处理多个输入文件）"""
        try:
            from perfx.visualizers.academic_charts import AcademicChartGenerator
            
            # 加载所有输入文件的数据
            datasets = []
            for input_file in input_files:
                with open(input_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                datasets.append(data)
            
            # 获取配置
            data_config = chart_config.get('data_config', {})
            filters = chart_config.get('filters', {})
            chart_config_options = chart_config.get('chart_config', {})
            
            # 数据提取配置
            test_results_path = data_config.get('test_results_path', 'test_results')
            test_id_field = data_config.get('test_id_field', 'test_id')
            duration_field = data_config.get('duration_field', 'duration')
            status_field = data_config.get('status_field', 'status')
            error_field = data_config.get('error_field', 'error_message')
            
            # 过滤配置
            include_statuses = filters.get('include_statuses', ['PASSED', 'FAILED'])
            exclude_statuses = filters.get('exclude_statuses', ['SKIPPED'])
            only_successful = filters.get('only_successful', False)
            ignore_errors = filters.get('ignore_errors', False)
            
            # 从每个数据集中提取测试结果
            test_data_sets = []
            for i, data in enumerate(datasets):
                test_results = self._extract_data_by_path(data, test_results_path)
                if not test_results:
                    self.console.print(f"[yellow]Warning: No data found at path '{test_results_path}' in file {input_files[i]}[/yellow]")
                    return False
                
                # 提取并过滤测试数据
                test_data = {}
                for test in test_results:
                    if not isinstance(test, dict):
                        continue
                    
                    test_id = test.get(test_id_field)
                    duration = test.get(duration_field)
                    status = test.get(status_field)
                    error_msg = test.get(error_field)
                    
                    # 基本验证
                    if not test_id or duration is None:
                        continue
                    
                    # 状态过滤
                    if include_statuses and status not in include_statuses:
                        continue
                    if exclude_statuses and status in exclude_statuses:
                        continue
                    
                    # 成功状态过滤
                    if only_successful and status != 'PASSED':
                        continue
                    
                    # 错误过滤
                    if ignore_errors and error_msg:
                        continue
                    
                    test_data[test_id] = float(duration)
                
                test_data_sets.append(test_data)
            
            if len(test_data_sets) != 2:
                self.console.print("[yellow]Warning: Comparison chart requires exactly 2 input files[/yellow]")
                return False
            
            pure_data, summary_data = test_data_sets[0], test_data_sets[1]
            
            if not pure_data or not summary_data:
                self.console.print("[yellow]Warning: No valid performance data found after filtering[/yellow]")
                return False
            
            # 生成对比图表
            chart_generator = AcademicChartGenerator(str(output_file.parent))
            title = chart_config.get('title', 'Performance Comparison')
            output_name = chart_config.get('name', 'performance_comparison')
            
            # 使用自定义标签
            dataset1_label = chart_config_options.get('dataset1_label', 'Dataset 1')
            dataset2_label = chart_config_options.get('dataset2_label', 'Dataset 2')
            
            # 根据图表类型生成不同的图表
            chart_type = chart_config.get('type', 'performance_comparison')
            
            if chart_type == 'performance_comparison':
                chart_file = chart_generator.generate_performance_comparison_chart(
                    pure_data, summary_data, title, output_name
                )
            elif chart_type == 'performance_distribution':
                chart_file = chart_generator.generate_performance_distribution_chart(
                    pure_data, summary_data, title, output_name
                )
            elif chart_type == 'performance_scatter':
                chart_file = chart_generator.generate_performance_scatter_chart(
                    pure_data, summary_data, title, output_name
                )
            elif chart_type == 'test_case_improvement':
                top_n = chart_config_options.get('top_n', 20)
                chart_file = chart_generator.generate_test_case_improvement_chart(
                    pure_data, summary_data, title, output_name, top_n
                )
            else:
                self.console.print(f"[yellow]Warning: Unknown chart type: {chart_type}[/yellow]")
                return False
            
            if chart_file:
                self.console.print(f"[green]✓ {chart_type} chart generated: {chart_file}[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to generate {chart_type} chart[/red]")
                return False
                
        except ImportError:
            self.console.print("[yellow]academic_charts not available, skipping comparison chart[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error generating comparison chart: {e}[/red]")
            return False
    
    def _extract_data_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """根据路径提取数据"""
        if not path:
            return data
        
        current = data
        for key in path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _generate_latex_table_content(self, table_config: Dict[str, Any], table_data: Any) -> str:
        """生成LaTeX表格内容"""
        title = table_config.get('title', 'Generated Table')
        columns = table_config.get('columns', [])
        
        if not columns:
            return f"% Error: No columns defined for table {table_config.get('name', 'unknown')}"
        
        # LaTeX表格开始
        latex_lines = [
            "\\begin{table}[htbp]",
            "\\centering",
            f"\\caption{{{title}}}",
            f"\\label{{tab:{table_config.get('name', 'table')}}}",
        ]
        
        # 检查是否使用tabularx环境
        use_tabularx = table_config.get('use_tabularx', False)
        
        # 表格格式 - 根据数据类型选择合适的列格式（三线表格式）
        col_formats = []
        for col in columns:
            format_type = col.get("format", "text")
            if format_type in ["integer", "float_2", "percentage"]:
                col_formats.append("r")  # 数字右对齐
            else:
                # 根据配置决定是否使用X列类型
                if use_tabularx:
                    col_formats.append("X")  # 文本自动换行，使用X列类型
                else:
                    col_formats.append("l")  # 文本左对齐
        
        col_format = "".join(col_formats)  # 不使用竖线
        
        # 根据配置选择表格环境
        if use_tabularx:
            latex_lines.append(f"\\begin{{tabularx}}{{\\textwidth}}{{{col_format}}}")
        else:
            latex_lines.append(f"\\begin{{tabular}}{{{col_format}}}")
        latex_lines.append("\\toprule")
        
        # 表头
        headers = [self._escape_latex(col["header"]) for col in columns]
        latex_lines.append(" & ".join(headers) + " \\\\")
        latex_lines.append("\\midrule")
        
        # 获取忽略的分类列表
        ignore_categories = table_config.get('ignore_categories', [])
        
        # 表格数据
        if isinstance(table_data, dict):
            # 检查是否是summary类型的数据（单个对象）
            if table_config.get('type') == 'summary_table':
                # summary数据：单个对象，直接提取字段
                row_data = []
                for col in columns:
                    field = col["field"]
                    value = table_data.get(field, "")
                    formatted_value = self._format_value(value, col.get("format", "text"))
                    row_data.append(formatted_value)
                latex_lines.append(" & ".join(row_data) + " \\\\")
            else:
                # 字典数据：每行是一个键值对
                for key, item in table_data.items():
                    # 检查是否应该忽略这个分类
                    if key in ignore_categories:
                        continue
                        
                    if isinstance(item, dict):
                        row_data = []
                        for col in columns:
                            field = col["field"]
                            value = item.get(field, "")
                            formatted_value = self._format_value(value, col.get("format", "text"))
                            row_data.append(formatted_value)
                        latex_lines.append(" & ".join(row_data) + " \\\\")
                    else:
                        row_data = [str(key), self._format_value(item, columns[1].get("format", "text"))]
                        latex_lines.append(" & ".join(row_data) + " \\\\")
        
        elif isinstance(table_data, list):
            for item in table_data:
                if isinstance(item, dict):
                    # 检查是否应该忽略这个分类（基于category字段）
                    category = item.get("category", "")
                    if category in ignore_categories:
                        continue
                        
                    row_data = []
                    for col in columns:
                        field = col["field"]
                        value = item.get(field, "")
                        formatted_value = self._format_value(value, col.get("format", "text"))
                        row_data.append(formatted_value)
                    latex_lines.append(" & ".join(row_data) + " \\\\")
        
        latex_lines.append("\\bottomrule")
        # 根据配置选择表格结束标签
        if use_tabularx:
            latex_lines.append("\\end{tabularx}")
        else:
            latex_lines.append("\\end{tabular}")
        latex_lines.append("\\end{table}")
        
        return "\n".join(latex_lines)
    
    def _generate_bar_chart(self, chart_config: Dict[str, Any], chart_data: Any, output_file: Path) -> bool:
        """生成柱状图"""
        import matplotlib.pyplot as plt
        
        try:
            # 准备数据
            if isinstance(chart_data, dict):
                x_field = chart_config["x_axis"]["field"]
                y_field = chart_config["y_axis"]["field"]
                
                x_values = []
                y_values = []
                
                for key, item in chart_data.items():
                    if isinstance(item, dict):
                        x_val = item.get(x_field, key)
                        y_val = item.get(y_field, 0)
                        x_values.append(str(x_val))
                        y_values.append(float(y_val) if y_val is not None else 0)
            else:
                return False
            
            # 创建图表
            plt.figure(figsize=(10, 6))
            bars = plt.bar(x_values, y_values)
            
            # 设置标题和标签
            plt.title(chart_config["title"], fontsize=14, fontweight='bold')
            plt.xlabel(chart_config["x_axis"]["label"], fontsize=12)
            plt.ylabel(chart_config["y_axis"]["label"], fontsize=12)
            
            # 格式化Y轴
            if chart_config["y_axis"].get("format") == "percentage":
                plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x*100:.1f}%'))
            
            # 旋转X轴标签如果太长
            if max(len(str(x)) for x in x_values) > 10:
                plt.xticks(rotation=45, ha='right')
            
            # 在柱子上显示数值
            for bar, value in zip(bars, y_values):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        self._format_value(value, chart_config["y_axis"].get("format", "float_2")),
                        ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图表
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            self.console.print(f"[red]Error generating bar chart: {e}[/red]")
            return False
    
    def _generate_pie_chart(self, chart_config: Dict[str, Any], chart_data: Any, output_file: Path) -> bool:
        """生成饼图"""
        import matplotlib.pyplot as plt
        
        try:
            # 准备数据
            values = []
            labels = []
            
            if isinstance(chart_data, dict):
                value_field = chart_config["value_field"]
                label_field = chart_config["label_field"]
                
                for key, item in chart_data.items():
                    if isinstance(item, dict):
                        value = item.get(value_field, 0)
                        label = item.get(label_field, key)
                        if value > 0:
                            values.append(float(value))
                            labels.append(str(label))
            
            if not values:
                return False
            
            # 创建饼图
            plt.figure(figsize=(10, 8))
            wedges, texts, autotexts = plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            
            # 设置标题
            plt.title(chart_config["title"], fontsize=14, fontweight='bold')
            
            # 美化文本
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            plt.axis('equal')
            
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图表
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            self.console.print(f"[red]Error generating pie chart: {e}[/red]")
            return False
    
    def _generate_performance_comparison_chart(self, chart_config: Dict[str, Any], chart_data: Any, output_file: Path) -> bool:
        """生成性能对比图表"""
        try:
            from perfx.visualizers.academic_charts import AcademicChartGenerator, extract_test_durations
            
            # 检查数据格式 - chart_data已经是comparison对象了
            if not isinstance(chart_data, dict):
                self.console.print("[yellow]Warning: chart_data is not a dict[/yellow]")
                return False
            
            # chart_data应该包含'pure'和'summary'键
            if 'pure' not in chart_data or 'summary' not in chart_data:
                self.console.print("[yellow]Warning: 'pure' or 'summary' key not found in chart_data[/yellow]")
                self.console.print(f"[yellow]Available keys: {list(chart_data.keys())}[/yellow]")
                return False
            
            # 提取pure和summary数据
            pure_data = {}
            summary_data = {}
            
            if 'durations' in chart_data['pure']:
                # 如果数据已经处理过（有durations数组）
                pure_durations = chart_data['pure']['durations']
                summary_durations = chart_data['summary']['durations'] if 'durations' in chart_data['summary'] else []
                
                # 创建测试名称
                for i, duration in enumerate(pure_durations):
                    pure_data[f"test_{i+1}"] = duration
                
                for i, duration in enumerate(summary_durations):
                    summary_data[f"test_{i+1}"] = duration
            else:
                # 如果数据是原始格式（需要提取）
                pure_data = extract_test_durations(chart_data['pure'])
                summary_data = extract_test_durations(chart_data['summary'])
            
            if not pure_data and not summary_data:
                self.console.print("[yellow]Warning: No valid performance data found[/yellow]")
                return False
            
            # 确保至少有一种数据
            if not pure_data:
                self.console.print("[yellow]Warning: No pure execution data found[/yellow]")
                return False
            if not summary_data:
                self.console.print("[yellow]Warning: No summary execution data found[/yellow]")
                return False
            
            # 生成对比图表
            chart_generator = AcademicChartGenerator(str(output_file.parent))
            title = chart_config.get('title', 'Performance Comparison')
            output_name = chart_config.get('name', 'performance_comparison')
            
            chart_file = chart_generator.generate_performance_comparison_chart(
                pure_data, summary_data, title, output_name
            )
            
            if chart_file:
                self.console.print(f"[green]✓ Performance comparison chart generated: {chart_file}[/green]")
                return True
            else:
                self.console.print("[red]Failed to generate performance comparison chart[/red]")
                return False
                
        except ImportError:
            self.console.print("[yellow]academic_charts not available, skipping performance comparison chart[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error generating performance comparison chart: {e}[/red]")
            return False
    
    def _generate_performance_distribution_chart(self, chart_config: Dict[str, Any], chart_data: Any, output_file: Path) -> bool:
        """生成性能分布图表"""
        try:
            from perfx.visualizers.academic_charts import AcademicChartGenerator
            
            # 检查数据格式 - chart_data应该是包含durations的列表
            if not isinstance(chart_data, list):
                self.console.print("[yellow]Warning: chart_data is not a list[/yellow]")
                return False
            
            # 确保列表不为空
            if not chart_data:
                self.console.print("[yellow]Warning: chart_data list is empty[/yellow]")
                return False
            
            # 获取配置
            data_config = chart_config.get('data_config', {})
            filters = chart_config.get('filters', {})
            chart_config_options = chart_config.get('chart_config', {})
            
            # 数据提取配置
            test_results_path = data_config.get('test_results_path', 'test_results')
            test_id_field = data_config.get('test_id_field', 'test_id')
            duration_field = data_config.get('duration_field', 'duration')
            status_field = data_config.get('status_field', 'status')
            error_field = data_config.get('error_field', 'error_message')
            
            # 过滤配置
            include_statuses = filters.get('include_statuses', ['PASSED', 'FAILED'])
            exclude_statuses = filters.get('exclude_statuses', ['SKIPPED'])
            only_successful = filters.get('only_successful', False)
            ignore_errors = filters.get('ignore_errors', False)
            
            # 从数据中提取测试结果
            test_data = []
            for item in chart_data:
                if isinstance(item, dict):
                    test_id = item.get(test_id_field)
                    duration = item.get(duration_field)
                    status = item.get(status_field)
                    error_msg = item.get(error_field)
                    
                    # 基本验证
                    if not test_id or duration is None:
                        continue
                    
                    # 状态过滤
                    if include_statuses and status not in include_statuses:
                        continue
                    if exclude_statuses and status in exclude_statuses:
                        continue
                    
                    # 成功状态过滤
                    if only_successful and status != 'PASSED':
                        continue
                    
                    # 错误过滤
                    if ignore_errors and error_msg:
                        continue
                    
                    test_data.append(float(duration))
                else:
                    self.console.print(f"[yellow]Warning: Skipping non-dict item in performance distribution chart data: {item}[/yellow]")
            
            if not test_data:
                self.console.print("[yellow]Warning: No valid performance data found after filtering[/yellow]")
                return False
            
            # 生成性能分布图表
            chart_generator = AcademicChartGenerator(str(output_file.parent))
            title = chart_config.get('title', 'Performance Distribution')
            output_name = chart_config.get('name', 'performance_distribution')
            
            chart_file = chart_generator.generate_performance_distribution_chart(
                test_data, title, output_name
            )
            
            if chart_file:
                self.console.print(f"[green]✓ Performance distribution chart generated: {chart_file}[/green]")
                return True
            else:
                self.console.print("[red]Failed to generate performance distribution chart[/red]")
                return False
                
        except ImportError:
            self.console.print("[yellow]academic_charts not available, skipping performance distribution chart[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error generating performance distribution chart: {e}[/red]")
            return False
    
    def _generate_performance_scatter_chart(self, chart_config: Dict[str, Any], chart_data: Any, output_file: Path) -> bool:
        """生成性能散点图"""
        try:
            from perfx.visualizers.academic_charts import AcademicChartGenerator
            
            # 检查数据格式 - chart_data应该是包含durations的列表
            if not isinstance(chart_data, list):
                self.console.print("[yellow]Warning: chart_data is not a list[/yellow]")
                return False
            
            # 确保列表不为空
            if not chart_data:
                self.console.print("[yellow]Warning: chart_data list is empty[/yellow]")
                return False
            
            # 获取配置
            data_config = chart_config.get('data_config', {})
            filters = chart_config.get('filters', {})
            chart_config_options = chart_config.get('chart_config', {})
            
            # 数据提取配置
            test_results_path = data_config.get('test_results_path', 'test_results')
            test_id_field = data_config.get('test_id_field', 'test_id')
            duration_field = data_config.get('duration_field', 'duration')
            status_field = data_config.get('status_field', 'status')
            error_field = data_config.get('error_field', 'error_message')
            
            # 过滤配置
            include_statuses = filters.get('include_statuses', ['PASSED', 'FAILED'])
            exclude_statuses = filters.get('exclude_statuses', ['SKIPPED'])
            only_successful = filters.get('only_successful', False)
            ignore_errors = filters.get('ignore_errors', False)
            
            # 从数据中提取测试结果
            test_data = []
            for item in chart_data:
                if isinstance(item, dict):
                    test_id = item.get(test_id_field)
                    duration = item.get(duration_field)
                    status = item.get(status_field)
                    error_msg = item.get(error_field)
                    
                    # 基本验证
                    if not test_id or duration is None:
                        continue
                    
                    # 状态过滤
                    if include_statuses and status not in include_statuses:
                        continue
                    if exclude_statuses and status in exclude_statuses:
                        continue
                    
                    # 成功状态过滤
                    if only_successful and status != 'PASSED':
                        continue
                    
                    # 错误过滤
                    if ignore_errors and error_msg:
                        continue
                    
                    test_data.append(float(duration))
                else:
                    self.console.print(f"[yellow]Warning: Skipping non-dict item in performance scatter chart data: {item}[/yellow]")
            
            if not test_data:
                self.console.print("[yellow]Warning: No valid performance data found after filtering[/yellow]")
                return False
            
            # 生成性能散点图
            chart_generator = AcademicChartGenerator(str(output_file.parent))
            title = chart_config.get('title', 'Performance Scatter Plot')
            output_name = chart_config.get('name', 'performance_scatter')
            
            chart_file = chart_generator.generate_performance_scatter_chart(
                test_data, title, output_name
            )
            
            if chart_file:
                self.console.print(f"[green]✓ Performance scatter chart generated: {chart_file}[/green]")
                return True
            else:
                self.console.print("[red]Failed to generate performance scatter chart[/red]")
                return False
                
        except ImportError:
            self.console.print("[yellow]academic_charts not available, skipping performance scatter chart[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error generating performance scatter chart: {e}[/red]")
            return False
    
    def _generate_test_case_improvement_chart(self, chart_config: Dict[str, Any], chart_data: Any, output_file: Path) -> bool:
        """生成测试用例改进图表"""
        try:
            from perfx.visualizers.academic_charts import AcademicChartGenerator
            
            # 检查数据格式 - chart_data应该是包含durations的列表
            if not isinstance(chart_data, list):
                self.console.print("[yellow]Warning: chart_data is not a list[/yellow]")
                return False
            
            # 确保列表不为空
            if not chart_data:
                self.console.print("[yellow]Warning: chart_data list is empty[/yellow]")
                return False
            
            # 获取配置
            data_config = chart_config.get('data_config', {})
            filters = chart_config.get('filters', {})
            chart_config_options = chart_config.get('chart_config', {})
            
            # 数据提取配置
            test_results_path = data_config.get('test_results_path', 'test_results')
            test_id_field = data_config.get('test_id_field', 'test_id')
            duration_field = data_config.get('duration_field', 'duration')
            status_field = data_config.get('status_field', 'status')
            error_field = data_config.get('error_field', 'error_message')
            
            # 过滤配置
            include_statuses = filters.get('include_statuses', ['PASSED', 'FAILED'])
            exclude_statuses = filters.get('exclude_statuses', ['SKIPPED'])
            only_successful = filters.get('only_successful', False)
            ignore_errors = filters.get('ignore_errors', False)
            
            # 从数据中提取测试结果
            test_data = []
            for item in chart_data:
                if isinstance(item, dict):
                    test_id = item.get(test_id_field)
                    duration = item.get(duration_field)
                    status = item.get(status_field)
                    error_msg = item.get(error_field)
                    
                    # 基本验证
                    if not test_id or duration is None:
                        continue
                    
                    # 状态过滤
                    if include_statuses and status not in include_statuses:
                        continue
                    if exclude_statuses and status in exclude_statuses:
                        continue
                    
                    # 成功状态过滤
                    if only_successful and status != 'PASSED':
                        continue
                    
                    # 错误过滤
                    if ignore_errors and error_msg:
                        continue
                    
                    test_data.append(float(duration))
                else:
                    self.console.print(f"[yellow]Warning: Skipping non-dict item in test case improvement chart data: {item}[/yellow]")
            
            if not test_data:
                self.console.print("[yellow]Warning: No valid performance data found after filtering[/yellow]")
                return False
            
            # 生成测试用例改进图表
            chart_generator = AcademicChartGenerator(str(output_file.parent))
            title = chart_config.get('title', 'Test Case Improvement')
            output_name = chart_config.get('name', 'test_case_improvement')
            
            chart_file = chart_generator.generate_test_case_improvement_chart(
                test_data, title, output_name
            )
            
            if chart_file:
                self.console.print(f"[green]✓ Test case improvement chart generated: {chart_file}[/green]")
                return True
            else:
                self.console.print("[red]Failed to generate test case improvement chart[/red]")
                return False
                
        except ImportError:
            self.console.print("[yellow]academic_charts not available, skipping test case improvement chart[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error generating test case improvement chart: {e}[/red]")
            return False
    
    def _escape_latex(self, text: str) -> str:
        """转义LaTeX特殊字符"""
        if not isinstance(text, str):
            return str(text)
        
        # LaTeX特殊字符转义 - 按特定顺序处理，避免重复转义
        text = text.replace('\\', r'\textbackslash{}')  # 先处理反斜杠
        text = text.replace('&', r'\&')
        text = text.replace('%', r'\%')
        text = text.replace('$', r'\$')
        text = text.replace('#', r'\#')
        text = text.replace('^', r'\^{}')
        text = text.replace('_', r'\_')
        text = text.replace('{', r'\{')
        text = text.replace('}', r'\}')
        text = text.replace('~', r'\textasciitilde{}')
        
        return text

    def _format_value(self, value: Any, format_type: str) -> str:
        """格式化值"""
        if value is None:
            return "N/A"
        
        try:
            if format_type == "integer":
                return str(int(value))
            elif format_type == "float_1":
                return f"{float(value):.1f}"
            elif format_type == "float_2":
                return f"{float(value):.2f}"
            elif format_type == "percentage":
                if isinstance(value, (int, float)):
                    return f"{value:.1f}\\%"  # 修改：添加%符号
                else:
                    return str(value)
            elif format_type == "text":
                return self._escape_latex(str(value))
            else:
                return self._escape_latex(str(value))
        except (ValueError, TypeError):
            return self._escape_latex(str(value))
    
    def generate_latex_document(self) -> Dict[str, Any]:
        """生成LaTeX文档"""
        try:
            from perfx.visualizers.latex_document import generate_latex_document
            
            success = generate_latex_document(self.config, str(self.base_dir))
            
            if success:
                return {"success": True, "message": "LaTeX document generated successfully"}
            else:
                return {"success": False, "message": "Failed to generate LaTeX document"}
                
        except ImportError:
            self.console.print("[yellow]perfx.latex_document not available[/yellow]")
            return {"success": False, "message": "LaTeX document generation not available"}
        except Exception as e:
            self.console.print(f"[red]Error generating LaTeX document: {e}[/red]")
            return {"success": False, "error": str(e)}