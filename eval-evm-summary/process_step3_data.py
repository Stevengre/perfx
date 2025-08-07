#!/usr/bin/env python3
"""
第三步数据处理器 - 专门处理Step 3摘要化评估数据
输入：results/data/summarize_evaluation_results.json
输出：results/processed/step3_processed.json (perfx可直接使用的格式)
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# 添加opcode别名映射
opcode_aliases = {
    # 这里可以添加opcode别名映射，目前为空
}

OPCODE_CATEGORIES = {
    'Arith. & Bit.': {
        'count': 20,  # 更新计数
        'opcodes': [
            'ADD', 'MUL', 'SUB', 'DIV', 'SDIV', 'MOD', 'SMOD', 'ADDMOD', 'MULMOD', 
            'EXP', 'SIGNEXTEND', 'AND', 'OR', 'XOR', 'NOT', 'BYTE', 'SHL', 
            'SHR', 'SAR', 'EVMOR'
        ],
    },
    'Comparison': {
        'count': 6,
        'opcodes': ['LT', 'GT', 'SLT', 'SGT', 'EQ', 'ISZERO'],
    },
    'Flow Control': {
        'count': 9,  # 更新计数
        'opcodes': ['STOP', 'JUMP', 'JUMPI', 'PC', 'JUMPDEST', 'RETURN', 'REVERT', 'INVALID', 'UNDEFINED'],
    },
    'Stack': {
        'count': 66,
        'opcodes': ['POP', 'PUSHZERO', 'PUSH', 'DUP', 'SWAP'],
    },
    'Memory': {
        'count': 5,
        'opcodes': ['MLOAD', 'MSTORE', 'MSTORE8', 'MSIZE', 'MCOPY'],
    },
    'Storage': {
        'count': 2,
        'opcodes': ['SLOAD', 'SSTORE']
    },
    'Trans. Storage': {
        'count': 2,
        'opcodes': ['TLOAD', 'TSTORE'],
    },
    'Environment': {
        'count': 11,
        'opcodes': [
            'BLOCKHASH', 'COINBASE', 'TIMESTAMP', 'NUMBER', 'DIFFICULTY', 
            'PREVRANDAO', 'GASLIMIT', 'CHAINID', 'BASEFEE', 'BLOBHASH', 'BLOBBASEFEE'
        ],
    },
    'Context': {
        'count': 18,
        'opcodes': [
            'ADDRESS', 'BALANCE', 'ORIGIN', 'CALLER', 'CALLVALUE', 'CALLDATALOAD', 
            'CALLDATASIZE', 'CALLDATACOPY', 'CODESIZE', 'CODECOPY', 'GASPRICE', 
            'EXTCODESIZE', 'EXTCODECOPY', 'RETURNDATASIZE', 'RETURNDATACOPY', 
            'EXTCODEHASH', 'SELFBALANCE', 'GAS'
        ],
    },
    'System': {
        'count': 6,
        'opcodes': ['SHA3', 'LOG'],
    },
    'Contract': {
        'count': 7,
        'opcodes': ['CREATE', 'CREATE2', 'CALL', 'CALLCODE', 'DELEGATECALL', 'STATICCALL', 'SELFDESTRUCT'],
    }
}

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """安全加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error: Failed to load {file_path}: {e}")
        return None

def _calculate_reduction(rewriting_steps: List[int]) -> float:
    """计算reduction值"""
    if not rewriting_steps or len(rewriting_steps) < 2:
        return 0.0
    
    # 简单的reduction计算：(初始步数 - 最终步数) / 初始步数
    initial_steps = rewriting_steps[0]
    final_steps = rewriting_steps[-1]
    
    if initial_steps <= 0:
        return 0.0
    
    reduction = (initial_steps - final_steps) / initial_steps
    return max(0.0, min(1.0, reduction))  # 限制在0-1之间

def _expand_opcode_name(opcode_name: str) -> List[str]:
    """展开opcode名称，如DUP -> DUP1-16, SWAP -> SWAP1-16, PUSH -> PUSH1-32, LOG -> LOG0-4"""
    if opcode_name == "DUP":
        return ["DUP1-16"]  # 简化为范围表示
    elif opcode_name == "SWAP":
        return ["SWAP1-16"]  # 简化为范围表示
    elif opcode_name == "PUSH":
        return ["PUSH1-32"]  # 简化为范围表示
    elif opcode_name == "LOG":
        return ["LOG0-4"]  # 简化为范围表示
    else:
        return [opcode_name]  # 其他opcode不展开

def parse_prove_summaries_data(prove_file: str) -> Dict[str, Dict[str, Any]]:
    """解析prove_summaries_results.json文件，提取opcode验证信息"""
    prove_data = load_json_file(prove_file)
    if not prove_data:
        return {}
    
    prove_results = {}
    
    for test in prove_data.get('test_results', []):
        # 从test_id中提取opcode名称
        # 格式: "src/tests/integration/test_prove.py::test_prove_summaries[SAR-SUMMARY]"
        test_id = test.get('test_id', '')
        if '-SUMMARY]' in test_id:
            opcode = test_id.split('[')[1].split('-')[0]
            status = test.get('status', 'UNKNOWN')
            duration = test.get('duration', 0.0)
            
            prove_results[opcode] = {
                'status': status,
                'duration': duration,
                'success': status == 'PASSED'
            }
    
    return prove_results

def process_step3_data(input_file: str, output_file: str, prove_file: str = None):
    """处理第三步数据，生成perfx兼容的JSON格式"""
    
    # 加载原始数据
    data = load_json_file(input_file)
    if data is None:
        return False
    
    # 加载prove_summaries数据
    prove_results = {}
    if prove_file and Path(prove_file).exists():
        prove_results = parse_prove_summaries_data(prove_file)
        print(f"📋 Loaded prove_summaries data for {len(prove_results)} opcodes")
    else:
        print(f"⚠️  Prove_summaries file not found or not specified: {prove_file}")
    
    # 创建opcode到分类的映射
    opcode_to_category = {}
    for category_name, category_data in OPCODE_CATEGORIES.items():
        for opcode in category_data['opcodes']:
            opcode_to_category[opcode] = category_name
    
    # 创建perfx兼容的数据结构
    processed_data = {
        "metadata": {
            "source": input_file,
            "prove_source": prove_file,
            "type": "step3_opcode_summarization",
            "description": "EVM Opcode Summarization Evaluation Results",
            "processed_by": "process_step3_data.py"
        },
        "categories": {}  # 分类统计
    }
    
    # 初始化所有分类的统计信息
    for category_name in OPCODE_CATEGORIES.keys():
        processed_data["categories"][category_name] = {
            "category": category_name,
            "total_count": 0,
            "successful_count": 0,
            "failed_count": 0,
            "success_rate": 0.0,
            "avg_time": 0.0,
            "avg_gas_steps": 0.0,
            "avg_nogas_steps": 0.0,
            "avg_gas_reduction": 0.0,
            "avg_nogas_reduction": 0.0,
            "avg_steps": 0.0,
            "avg_reduction": 0.0,
            "success_opcodes": "",
            "failed_opcodes": "",
            # 新增验证相关字段
            "verification_total": 0,
            "verification_passed": 0,
            "verification_failed": 0,
            "verification_success_rate": 0.0,
            "avg_verification_time": 0.0
        }
    
    # 添加Total分类用于存储总计信息
    processed_data["categories"]["Total"] = {
        "category": "Total",
        "total_count": 0,
        "successful_count": 0,
        "failed_count": 0,
        "success_rate": 0.0,
        "avg_time": 0.0,
        "avg_gas_steps": 0.0,
        "avg_nogas_steps": 0.0,
        "avg_gas_reduction": 0.0,
        "avg_nogas_reduction": 0.0,
        "avg_steps": 0.0,
        "avg_reduction": 0.0,
        "success_opcodes": "",
        "failed_opcodes": "",
        # 新增验证相关字段
        "verification_total": 0,
        "verification_passed": 0,
        "verification_failed": 0,
        "verification_success_rate": 0.0,
        "avg_verification_time": 0.0
    }
    
    # 处理原始数据
    results_list = data.get('results', [])
    if not results_list:
        results_list = data if isinstance(data, list) else []
    
    print(f"📋 Found {len(results_list)} opcode results")
    
    # 从原始数据中循环处理每个opcode
    for item in results_list:
        if not isinstance(item, dict) or 'opcode' not in item:
            continue
            
        opcode = item['opcode']
        
        # 处理opcode别名
        if opcode in opcode_aliases:
            opcode = opcode_aliases[opcode]
        
        # 检查opcode是否在分类中
        if opcode not in opcode_to_category:
            print(f"❌ Error: Opcode '{item['opcode']}' (mapped to '{opcode}') not found in any category!")
            return False
        
        category_name = opcode_to_category[opcode]
        rewriting_steps = item.get('rewriting_steps') or []
        
        # 处理单个opcode结果
        status = 'success' if item.get('success', False) else 'failed'
        time = item.get('time')
        
        # 解析rewriting_steps：第一个是gas路径，第二个是nogas路径
        gas_steps = None
        nogas_steps = None
        
        if len(rewriting_steps) >= 2:
            gas_steps = rewriting_steps[0]
            nogas_steps = rewriting_steps[1]
        elif len(rewriting_steps) == 1:
            gas_steps = rewriting_steps[0]
            nogas_steps = rewriting_steps[0]  # 如果只有一个值，gas和nogas都使用这个值
        
        # 展开opcode名称（如DUP -> DUP1-16）
        expanded_opcodes = _expand_opcode_name(opcode)
        actual_count = len(expanded_opcodes)
        
        # 更新分类统计
        category_stats = processed_data["categories"][category_name]
        category_stats["total_count"] += actual_count
        
        if status == 'success':
            category_stats["successful_count"] += actual_count
        else:
            category_stats["failed_count"] += actual_count
        
        # 累计性能数据
        if time is not None:
            category_stats["avg_time"] += float(time)
        
        # 累计gas和nogas步数（只有成功的opcode才计算）
        if status == 'success':
            if gas_steps is not None:
                category_stats["avg_gas_steps"] += float(gas_steps)
            if nogas_steps is not None:
                category_stats["avg_nogas_steps"] += float(nogas_steps)
            
            # 累计总的步数（gas和nogas的平均值）
            if gas_steps is not None and nogas_steps is not None:
                total_steps = (gas_steps + nogas_steps) / 2
                category_stats["avg_steps"] += float(total_steps)
            elif gas_steps is not None:
                category_stats["avg_steps"] += float(gas_steps)
            elif nogas_steps is not None:
                category_stats["avg_steps"] += float(nogas_steps)
            
            # 添加成功的opcode到字符串
            if category_stats["success_opcodes"]:
                category_stats["success_opcodes"] += ", " + ", ".join(expanded_opcodes)
            else:
                category_stats["success_opcodes"] = ", ".join(expanded_opcodes)
        else:
            # 添加失败的opcode到字符串
            if category_stats["failed_opcodes"]:
                category_stats["failed_opcodes"] += ", " + ", ".join(expanded_opcodes)
            else:
                category_stats["failed_opcodes"] = ", ".join(expanded_opcodes)
    
    # 计算每个分类的平均值和成功率
    for category_name, category_stats in processed_data["categories"].items():
        if category_name == "Total":  # 跳过Total分类，稍后计算
            continue
            
        total_count = category_stats["total_count"]
        if total_count > 0:
            category_stats["success_rate"] = (category_stats["successful_count"] / total_count) * 100
            
            # 计算平均值（基于实际处理的opcode数量）
            processed_opcodes = 0
            for item in results_list:
                if not isinstance(item, dict) or 'opcode' not in item:
                    continue
                opcode = item['opcode']
                if opcode in opcode_aliases:
                    opcode = opcode_aliases[opcode]
                if opcode in opcode_to_category and opcode_to_category[opcode] == category_name:
                    processed_opcodes += 1
            
            if processed_opcodes > 0:
                category_stats["avg_time"] = category_stats["avg_time"] / processed_opcodes
                
                # 计算gas和nogas的平均步数（基于实际处理的opcode数量，不是展开后的数量）
                if processed_opcodes > 0:
                    category_stats["avg_gas_steps"] = category_stats["avg_gas_steps"] / processed_opcodes
                    category_stats["avg_nogas_steps"] = category_stats["avg_nogas_steps"] / processed_opcodes
                    category_stats["avg_steps"] = category_stats["avg_steps"] / processed_opcodes
                    
                    # 计算reduction
                    if category_stats["avg_gas_steps"] > 0:
                        category_stats["avg_gas_reduction"] = ((category_stats["avg_gas_steps"] - 1) / category_stats["avg_gas_steps"]) * 100
                    if category_stats["avg_nogas_steps"] > 0:
                        category_stats["avg_nogas_reduction"] = ((category_stats["avg_nogas_steps"] - 1) / category_stats["avg_nogas_steps"]) * 100
                    if category_stats["avg_steps"] > 0:
                        category_stats["avg_reduction"] = ((category_stats["avg_steps"] - 1) / category_stats["avg_steps"]) * 100
    
    # 处理验证数据
    for opcode, prove_info in prove_results.items():
        if opcode in opcode_to_category:
            category_name = opcode_to_category[opcode]
            category_stats = processed_data["categories"][category_name]
            
            # 更新验证统计
            category_stats["verification_total"] += 1
            if prove_info['success']:
                category_stats["verification_passed"] += 1
            else:
                category_stats["verification_failed"] += 1
            
            # 累计验证时间
            category_stats["avg_verification_time"] += prove_info['duration']
    
    # 计算验证统计
    for category_name, category_stats in processed_data["categories"].items():
        if category_name == "Total":  # 跳过Total分类，稍后计算
            continue
            
        verification_total = category_stats["verification_total"]
        if verification_total > 0:
            category_stats["verification_success_rate"] = (category_stats["verification_passed"] / verification_total) * 100
            category_stats["avg_verification_time"] = category_stats["avg_verification_time"] / verification_total
    
    # 计算Total分类的统计信息 - 完全按opcode计算
    total_category = processed_data["categories"]["Total"]
    total_opcodes = 0
    total_successful = 0
    total_failed = 0
    total_time = 0.0
    total_gas_steps = 0.0
    total_nogas_steps = 0.0
    total_steps = 0.0
    successful_opcodes_count = 0  # 成功处理的opcode数量（用于计算平均值）
    all_success_opcodes = []
    all_failed_opcodes = []
    
    # 验证统计
    total_verification = 0
    total_verification_passed = 0
    total_verification_failed = 0
    total_verification_time = 0.0
    
    # 完全按opcode计算Total统计信息
    for item in results_list:
        if not isinstance(item, dict) or 'opcode' not in item:
            continue
            
        opcode = item['opcode']
        if opcode in opcode_aliases:
            opcode = opcode_aliases[opcode]
        
        # 检查opcode是否在分类中
        if opcode not in opcode_to_category:
            continue
        
        status = 'success' if item.get('success', False) else 'failed'
        time = item.get('time')
        rewriting_steps = item.get('rewriting_steps') or []
        
        # 展开opcode名称（如DUP -> DUP1-16）
        expanded_opcodes = _expand_opcode_name(opcode)
        actual_count = len(expanded_opcodes)
        
        # 累计计数（按opcode的展开数量）
        total_opcodes += actual_count
        if status == 'success':
            total_successful += actual_count
        else:
            total_failed += actual_count
        
        # 累计时间（按展开数量计算）
        if time is not None:
            total_time += float(time) * actual_count  # 修改：时间乘以展开数量
        
        # 累计步数（只有成功的opcode，按展开数量计算）
        if status == 'success':
            successful_opcodes_count += actual_count  # 修改：成功数量也按展开数量计算
            
            if len(rewriting_steps) >= 2:
                gas_steps = rewriting_steps[0]
                nogas_steps = rewriting_steps[1]
            elif len(rewriting_steps) == 1:
                gas_steps = rewriting_steps[0]
                nogas_steps = rewriting_steps[0]
            else:
                continue
            
            # 修改：步数也乘以展开数量
            total_gas_steps += float(gas_steps) * actual_count
            total_nogas_steps += float(nogas_steps) * actual_count
            
            if gas_steps is not None and nogas_steps is not None:
                total_steps += (gas_steps + nogas_steps) / 2 * actual_count
            elif gas_steps is not None:
                total_steps += gas_steps * actual_count
            elif nogas_steps is not None:
                total_steps += nogas_steps * actual_count
        
        # 收集opcode列表
        if status == 'success':
            if all_success_opcodes:
                all_success_opcodes.append(", ".join(expanded_opcodes))
            else:
                all_success_opcodes = [", ".join(expanded_opcodes)]
        else:
            if all_failed_opcodes:
                all_failed_opcodes.append(", ".join(expanded_opcodes))
            else:
                all_failed_opcodes = [", ".join(expanded_opcodes)]
    
    # 填充Total分类的统计信息
    total_category["total_count"] = total_opcodes
    total_category["successful_count"] = total_successful
    total_category["failed_count"] = total_failed
    
    if total_opcodes > 0:
        total_category["success_rate"] = (total_successful / total_opcodes) * 100
    
    if successful_opcodes_count > 0:
        # 修改：平均值计算基于展开后的数量
        total_category["avg_time"] = total_time / successful_opcodes_count
        total_category["avg_gas_steps"] = total_gas_steps / successful_opcodes_count
        total_category["avg_nogas_steps"] = total_nogas_steps / successful_opcodes_count
        total_category["avg_steps"] = total_steps / successful_opcodes_count
        
        # 计算reduction（逻辑保持不变）
        if total_category["avg_gas_steps"] > 0:
            total_category["avg_gas_reduction"] = ((total_category["avg_gas_steps"] - 1) / total_category["avg_gas_steps"]) * 100
        if total_category["avg_nogas_steps"] > 0:
            total_category["avg_nogas_reduction"] = ((total_category["avg_nogas_steps"] - 1) / total_category["avg_nogas_steps"]) * 100
        if total_category["avg_steps"] > 0:
            total_category["avg_reduction"] = ((total_category["avg_steps"] - 1) / total_category["avg_steps"]) * 100
    
    # 合并所有opcodes
    if all_success_opcodes:
        total_category["success_opcodes"] = ", ".join(all_success_opcodes)
    if all_failed_opcodes:
        total_category["failed_opcodes"] = ", ".join(all_failed_opcodes)
    
    # 处理验证数据
    for opcode, prove_info in prove_results.items():
        total_verification += 1
        if prove_info['success']:
            total_verification_passed += 1
        else:
            total_verification_failed += 1
        total_verification_time += prove_info['duration']
    
    # 填充验证统计
    total_category["verification_total"] = total_verification
    total_category["verification_passed"] = total_verification_passed
    total_category["verification_failed"] = total_verification_failed
    
    if total_verification > 0:
        total_category["verification_success_rate"] = (total_verification_passed / total_verification) * 100
        total_category["avg_verification_time"] = total_verification_time / total_verification
    
    # 保存处理后的数据
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Step 3 data processed successfully!")
    print(f"   📄 Output: {output_file}")
    print(f"   📊 Categories: {len(OPCODE_CATEGORIES)}")
    print(f"   🔢 Total opcodes: {total_category['total_count']}")
    print(f"   ✅ Success rate: {total_category['success_rate']:.1f}%")
    print(f"   📈 Overall statistics:")
    print(f"      ⏱️  Avg time: {total_category['avg_time']:.2f}s")
    print(f"      🔢 Avg gas steps: {total_category['avg_gas_steps']:.2f}")
    print(f"      🔢 Avg nogas steps: {total_category['avg_nogas_steps']:.2f}")
    print(f"      🔢 Avg steps: {total_category['avg_steps']:.2f}")
    print(f"      📉 Avg gas reduction: {total_category['avg_gas_reduction']:.1f}%")
    print(f"      📉 Avg nogas reduction: {total_category['avg_nogas_reduction']:.1f}%")
    print(f"      📉 Avg reduction: {total_category['avg_reduction']:.1f}%")
    print(f"   🔍 Verification statistics:")
    print(f"      📊 Total verified: {total_category['verification_total']}")
    print(f"      ✅ Verification success rate: {total_category['verification_success_rate']:.1f}%")
    print(f"      ⏱️  Avg verification time: {total_category['avg_verification_time']:.2f}s")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="第三步数据处理器")
    parser.add_argument("--input", default="results/data/summarize_evaluation_results.json", 
                       help="输入文件路径")
    parser.add_argument("--output", default="results/processed/step3_processed.json", 
                       help="输出文件路径")
    parser.add_argument("--prove", default="results/data/prove_summaries_results.json",
                       help="prove_summaries_results.json文件路径")
    
    args = parser.parse_args()
    
    print("🔄 开始处理第三步数据...")
    
    if not Path(args.input).exists():
        print(f"❌ 输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 处理主要数据
    success = process_step3_data(args.input, args.output, args.prove)
    
    if success:
        print("🎉 第三步数据处理完成！")
    else:
        print("❌ 第三步数据处理失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()