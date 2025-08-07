#!/usr/bin/env python3
"""
Command-line interface for perfx analysis
Perfx分析的命令行接口
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console

from .visualizers.analysis_engine import AnalysisEngine

console = Console()


def main():
    """主命令行入口"""
    parser = argparse.ArgumentParser(
        description="Perfx Analysis - Configuration-driven data analysis and visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete analysis
  perfx-analysis --data-dir results/data --output-dir results/analysis

  # Generate only charts
  perfx-analysis --type charts --data-dir results/data

  # Run comparison analysis with config
  perfx-analysis --type comparison --config comparison_config.json

  # Generate specific steps
  perfx-analysis --steps "3,4,5" --type charts

  # Custom directories
  perfx-analysis --data-dir /path/to/data --output-dir /path/to/output
        """
    )
    
    # 基本参数
    parser.add_argument("--data-dir", 
                       default="results/data",
                       help="Directory containing JSON data files (default: results/data)")
    
    parser.add_argument("--output-dir",
                       default="results/analysis", 
                       help="Output directory for generated files (default: results/analysis)")
    
    # 分析类型
    parser.add_argument("--type",
                       choices=["charts", "tables", "comparison", "all"],
                       default="all",
                       help="Type of analysis to run (default: all)")
    
    # 配置文件
    parser.add_argument("--config",
                       help="Configuration file for comparison analysis (JSON format)")
    
    # 步骤选择
    parser.add_argument("--steps",
                       help="Specific steps to analyze (comma-separated, e.g., '3,4,5')")
    
    # 输出控制
    parser.add_argument("--verbose", "-v",
                       action="store_true",
                       help="Enable verbose output")
    
    parser.add_argument("--quiet", "-q",
                       action="store_true", 
                       help="Suppress output except errors")
    
    # 版本信息
    parser.add_argument("--version",
                       action="version",
                       version="perfx-analysis 1.0.0")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.quiet:
        console.quiet = True
    elif args.verbose:
        console.print("[blue]Verbose mode enabled[/blue]")
    
    # 验证参数
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        console.print(f"[red]Error: Data directory does not exist: {data_dir}[/red]")
        sys.exit(1)
    
    if args.type == "comparison" and not args.config:
        console.print("[red]Error: --config is required when --type is 'comparison'[/red]")
        sys.exit(1)
    
    if args.config and not Path(args.config).exists():
        console.print(f"[red]Error: Configuration file does not exist: {args.config}[/red]")
        sys.exit(1)
    
    # 显示配置信息
    if not args.quiet:
        console.print("[bold blue]Perfx Analysis Engine[/bold blue]")
        console.print(f"Data directory: {data_dir}")
        console.print(f"Output directory: {args.output_dir}")
        console.print(f"Analysis type: {args.type}")
        if args.config:
            console.print(f"Configuration: {args.config}")
        if args.steps:
            console.print(f"Steps: {args.steps}")
        console.print()
    
    try:
        # 创建分析引擎
        engine = AnalysisEngine(str(data_dir), args.output_dir)
        
        # 运行分析
        results = engine.run_analysis(
            config_file=args.config,
            steps=args.steps,
            analysis_type=args.type
        )
        
        # 输出结果统计
        total_files = sum(len(files) for files in results.values())
        
        if not args.quiet:
            console.print(f"\n[bold green]✅ Analysis completed successfully![/bold green]")
            console.print(f"Generated {total_files} files total:")
            
            for file_type, files in results.items():
                if files:
                    console.print(f"  • {file_type.capitalize()}: {len(files)} files")
            
            console.print(f"\n[blue]Output directory: {args.output_dir}[/blue]")
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user[/yellow]")
        return 130
        
    except Exception as e:
        console.print(f"\n[red]Error during analysis: {e}[/red]")
        if args.verbose:
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())