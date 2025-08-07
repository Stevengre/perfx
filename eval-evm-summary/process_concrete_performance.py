#!/usr/bin/env python3
"""
Concrete Performance数据处理器 - 处理concrete execution性能对比数据
输入：pure_concrete_performance.json + summary_concrete_performance.json
输出：concrete_performance_processed.json
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """安全加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load {file_path}: {e}")
        return None

def extract_performance_stats(data: Dict[str, Any], execution_type: str) -> Dict[str, Any]:
    """从测试数据中提取性能统计"""
    stats = {
        "execution_type": execution_type,
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "avg_duration": 0.0,
        "min_duration": float('inf'),
        "max_duration": 0.0,
        "durations": []
    }
    
    test_results = data.get('test_results', [])
    if not test_results and isinstance(data, list):
        test_results = data
    
    total_duration = 0
    duration_count = 0
    
    for test in test_results:
        if isinstance(test, dict):
            stats["total_tests"] += 1
            
            status = test.get('status', 'UNKNOWN')
            if status == 'PASSED':
                stats["passed_tests"] += 1
            else:
                stats["failed_tests"] += 1
            
            duration = test.get('duration')
            if duration is not None and isinstance(duration, (int, float)) and duration > 0:
                stats["durations"].append(duration)
                total_duration += duration
                duration_count += 1
                stats["min_duration"] = min(stats["min_duration"], duration)
                stats["max_duration"] = max(stats["max_duration"], duration)
    
    if duration_count > 0:
        stats["avg_duration"] = total_duration / duration_count
    else:
        stats["min_duration"] = 0.0
    
    return stats

def process_concrete_performance_data(pure_file: str, summary_file: str, output_file: str):
    """处理concrete execution性能对比数据"""
    print(f"📊 Processing Concrete Performance data:")
    print(f"   Pure: {pure_file}")
    print(f"   Summary: {summary_file}")
    
    pure_data = load_json_file(pure_file)
    summary_data = load_json_file(summary_file)
    
    if not pure_data and not summary_data:
        print("❌ 无法加载任何输入文件")
        return False
    
    # 创建处理后的数据结构
    processed_data = {
        "metadata": {
            "pure_source": pure_file,
            "summary_source": summary_file,
            "type": "concrete_performance_comparison",
            "description": "Pure vs Summary Concrete Execution Performance Comparison",
            "processed_by": "process_concrete_performance.py"
        },
        "comparison": {},
        "performance_gain": {
            "speedup_ratio": 0.0,
            "time_saved_percentage": 0.0,
            "efficiency_improvement": 0.0
        }
    }
    
    # 处理pure execution数据
    if pure_data:
        pure_stats = extract_performance_stats(pure_data, "pure")
        processed_data["comparison"]["pure"] = pure_stats
        print(f"📋 Pure execution: {pure_stats['total_tests']} tests, avg {pure_stats['avg_duration']:.2f}s")
    
    # 处理summary execution数据
    if summary_data:
        summary_stats = extract_performance_stats(summary_data, "summary")
        processed_data["comparison"]["summary"] = summary_stats
        print(f"📋 Summary execution: {summary_stats['total_tests']} tests, avg {summary_stats['avg_duration']:.2f}s")
    
    # 计算性能提升
    if pure_data and summary_data:
        pure_avg = processed_data["comparison"]["pure"]["avg_duration"]
        summary_avg = processed_data["comparison"]["summary"]["avg_duration"]
        
        if pure_avg > 0 and summary_avg > 0:
            processed_data["performance_gain"]["speedup_ratio"] = pure_avg / summary_avg
            processed_data["performance_gain"]["time_saved_percentage"] = (
                (pure_avg - summary_avg) / pure_avg * 100
            )
            processed_data["performance_gain"]["efficiency_improvement"] = (
                (pure_avg - summary_avg) / summary_avg * 100
            )
    
    # 保存处理后的数据
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Concrete performance data processed successfully!")
    print(f"   📄 Output: {output_file}")
    if "pure" in processed_data["comparison"] and "summary" in processed_data["comparison"]:
        speedup = processed_data["performance_gain"]["speedup_ratio"]
        time_saved = processed_data["performance_gain"]["time_saved_percentage"]
        print(f"   🚀 Speedup ratio: {speedup:.2f}x")
        print(f"   ⏱️ Time saved: {time_saved:.1f}%")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Concrete Performance数据处理器")
    parser.add_argument("--pure", default="results/data/pure_concrete_performance.json", 
                       help="Pure execution数据文件")
    parser.add_argument("--summary", default="results/data/summary_concrete_performance.json", 
                       help="Summary execution数据文件")
    parser.add_argument("--output", default="results/processed/concrete_performance_processed.json", 
                       help="输出文件路径")
    
    args = parser.parse_args()
    
    print("🔄 开始处理Concrete Performance数据...")
    
    success = process_concrete_performance_data(args.pure, args.summary, args.output)
    
    if success:
        print("🎉 Concrete Performance数据处理完成！")
    else:
        print("❌ Concrete Performance数据处理失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()