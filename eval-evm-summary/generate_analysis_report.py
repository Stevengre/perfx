#!/usr/bin/env python3
"""
分析报告生成脚本
生成综合的评估分析报告
"""

import json
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()


def generate_comprehensive_report():
    """生成综合分析报告"""
    console.print("[blue]Generating comprehensive evaluation report...[/blue]")
    
    output_dir = Path('results/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_content = []
    
    # 报告头部
    report_content.append('# EVM Semantics Summarization Evaluation Report\n\n')
    report_content.append(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
    report_content.append('This report summarizes the comprehensive evaluation of EVM semantics summarization.\n\n')
    
    # 步骤摘要
    steps_info = [
        ('Step 3', 'Summarization Evaluation', 'EVM opcode summarization coverage and effectiveness'),
        ('Step 4', 'Prove Summaries Correctness', 'Verification of summarization semantic correctness'),
        ('Step 5', 'Pure Concrete Performance', 'Baseline concrete execution performance'),
        ('Step 6', 'Summary Concrete Performance', 'Summarized concrete execution performance'),
        ('Step 7', 'Pure Symbolic Performance', 'Baseline symbolic execution performance'),
        ('Step 8', 'Summary Symbolic Performance', 'Summarized symbolic execution performance')
    ]
    
    report_content.append('## Evaluation Steps\n\n')
    for step, name, desc in steps_info:
        report_content.append(f'- **{step}: {name}**: {desc}\n')
    
    # 生成的文件清单
    report_content.append('\n## Generated Artifacts\n\n')
    
    # 检查charts目录
    charts_dir = output_dir / 'charts'
    if charts_dir.exists():
        report_content.append('### Charts\n')
        chart_files = list(charts_dir.glob('*.pdf'))
        if chart_files:
            for chart_file in sorted(chart_files):
                report_content.append(f'- [{chart_file.name}]({chart_file.relative_to(output_dir)})\n')
        else:
            report_content.append('- No chart files found\n')
        report_content.append('\n')
    
    # 检查tables目录
    tables_dir = output_dir / 'tables'
    if tables_dir.exists():
        report_content.append('### LaTeX Tables\n')
        table_files = list(tables_dir.glob('*.tex'))
        if table_files:
            for table_file in sorted(table_files):
                report_content.append(f'- [{table_file.name}]({table_file.relative_to(output_dir)})\n')
        else:
            report_content.append('- No table files found\n')
        report_content.append('\n')
    
    # 数据统计
    report_content.append('### Data Statistics\n\n')
    
    # 尝试读取一些关键数据文件并提供统计信息
    data_files = [
        'results/data/summarize_evaluation_results.json',
        'results/data/prove_summaries_results.json',
        'results/data/pure_concrete_performance.json',
        'results/data/summary_concrete_performance.json'
    ]
    
    for data_file in data_files:
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                file_name = Path(data_file).stem
                report_content.append(f'#### {file_name}\n')
                
                # 基本统计
                if 'test_results' in data:
                    test_results = data['test_results']
                    total_tests = len(test_results)
                    passed_tests = sum(1 for test in test_results if test.get('status') == 'passed')
                    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                    
                    report_content.append(f'- Total tests: {total_tests}\n')
                    report_content.append(f'- Passed tests: {passed_tests}\n')
                    report_content.append(f'- Success rate: {success_rate:.1f}%\n')
                
                if 'statistics' in data:
                    stats = data['statistics']
                    if 'overall' in stats:
                        overall = stats['overall']
                        report_content.append(f'- Overall statistics: {overall}\n')
                
                report_content.append('\n')
                
            except Exception as e:
                report_content.append(f'- Error reading {data_file}: {e}\n\n')
    
    # 关键发现
    report_content.append('## Key Findings\n\n')
    report_content.append('### Summarization Effectiveness\n')
    report_content.append('- EVM opcode summarization coverage analysis\n')
    report_content.append('- Semantic equivalence verification results\n\n')
    
    report_content.append('### Performance Improvements\n')
    report_content.append('- Concrete execution performance gains\n')
    report_content.append('- Symbolic execution efficiency improvements\n')
    report_content.append('- Statistical significance of performance differences\n\n')
    
    report_content.append('### Correctness Verification\n')
    report_content.append('- Summarization semantic correctness validation\n')
    report_content.append('- Test case coverage and success rates\n\n')
    
    # 使用建议
    report_content.append('## Usage for Academic Papers\n\n')
    report_content.append('### Recommended Paper Structure\n')
    report_content.append('```latex\n')
    report_content.append('\\section{Evaluation}\n')
    report_content.append('\\subsection{Experimental Setup}\n')
    report_content.append('\\subsection{Summarization Effectiveness}\n')
    report_content.append('\\input{results/analysis/tables/step3_summarization_evaluation.tex}\n')
    report_content.append('\\subsection{Performance Analysis}\n')
    report_content.append('\\includegraphics{results/analysis/charts/comprehensive_performance_comparison.pdf}\n')
    report_content.append('\\input{results/analysis/tables/concrete_performance_comparison.tex}\n')
    report_content.append('```\n\n')
    
    # 保存报告
    report_file = output_dir / 'evaluation_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(''.join(report_content))
    
    console.print(f'[green]✓ Comprehensive evaluation report generated: {report_file}[/green]')


def main():
    """主函数"""
    generate_comprehensive_report()


if __name__ == "__main__":
    main()