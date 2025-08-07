#!/usr/bin/env python3
"""
第四步数据处理器 - 处理证明摘要化语义正确性数据
输入：results/data/prove_summaries_results.json
输出：results/processed/step4_processed.json
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
        print(f"Error: Failed to load {file_path}: {e}")
        return None

def process_step4_data(input_file: str, output_file: str):
    """处理第4步证明结果数据"""
    print(f"📊 Processing Step 4 data: {input_file}")
    
    data = load_json_file(input_file)
    if not data:
        return False
    
    # 创建perfx兼容的数据结构
    processed_data = {
        "metadata": {
            "source": input_file,
            "type": "step4_proof_verification",
            "description": "Summary Semantic Correctness Verification Results",
            "processed_by": "process_step4_data.py"
        },
        "test_results": [],
        "summary": {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "success_rate": 0.0,
            "avg_duration": 0.0
        }
    }
    
    # 处理测试结果
    test_results = data.get('test_results', [])
    if not test_results and isinstance(data, list):
        test_results = data
    
    print(f"📋 Found {len(test_results)} test results")
    
    total_duration = 0
    duration_count = 0
    
    for test in test_results:
        if isinstance(test, dict):
            # 转换为perfx格式
            processed_test = {
                "test_id": test.get('test_id', 'unknown'),
                "status": test.get('status', 'UNKNOWN'),
                "duration": test.get('duration'),
                "category": "proof_verification"
            }
            
            processed_data["test_results"].append(processed_test)
            processed_data["summary"]["total_tests"] += 1
            
            # 统计状态
            status = test.get('status', 'UNKNOWN')
            if status == 'PASSED':
                processed_data["summary"]["passed_tests"] += 1
            elif status == 'FAILED':
                processed_data["summary"]["failed_tests"] += 1
            elif status == 'SKIPPED':
                processed_data["summary"]["skipped_tests"] += 1
            
            # 累计持续时间
            duration = test.get('duration')
            if duration is not None and isinstance(duration, (int, float)):
                total_duration += duration
                duration_count += 1
    
    # 计算统计数据
    if processed_data["summary"]["total_tests"] > 0:
        processed_data["summary"]["success_rate"] = (
            processed_data["summary"]["passed_tests"] / 
            processed_data["summary"]["total_tests"]
        )
    
    if duration_count > 0:
        processed_data["summary"]["avg_duration"] = total_duration / duration_count
    
    # 保存处理后的数据
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Step 4 data processed successfully!")
    print(f"   📄 Output: {output_file}")
    print(f"   🔢 Total tests: {processed_data['summary']['total_tests']}")
    print(f"   ✅ Success rate: {processed_data['summary']['success_rate']:.1%}")
    print(f"   ⏱️ Avg duration: {processed_data['summary']['avg_duration']:.2f}s")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="第四步数据处理器")
    parser.add_argument("--input", default="results/data/prove_summaries_results.json", 
                       help="输入文件路径")
    parser.add_argument("--output", default="results/processed/step4_processed.json", 
                       help="输出文件路径")
    
    args = parser.parse_args()
    
    print("🔄 开始处理第四步数据...")
    
    if not Path(args.input).exists():
        print(f"❌ 输入文件不存在: {args.input}")
        sys.exit(1)
    
    success = process_step4_data(args.input, args.output)
    
    if success:
        print("🎉 第四步数据处理完成！")
    else:
        print("❌ 第四步数据处理失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()