#!/usr/bin/env python3
"""
独立的摘要化评估脚本
用于在 perfx 配置中调用，实现与 eval/evaluate_summarize.py 相同的功能
"""

import sys
import os
import json
import time
import traceback
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed

# 添加 kevm-pyk 到 Python 路径
kevm_pyk_path = os.path.join(os.path.dirname(__file__), '..', 'repositories', 'evm-semantics', 'kevm-pyk')
if os.path.exists(kevm_pyk_path):
    sys.path.insert(0, kevm_pyk_path)
    print(f"Added kevm-pyk path: {kevm_pyk_path}")
else:
    print(f"Warning: kevm-pyk path not found: {kevm_pyk_path}")

try:
    from kevm_pyk.summarizer import OPCODES, summarize
    from kevm_pyk.summarizer import get_summary_status, OPCODES_SUMMARY_STATUS
except ImportError as e:
    print(f"Error importing kevm_pyk: {e}")
    print("Make sure kevm-pyk is built and available")
    print(f"Expected path: {kevm_pyk_path}")
    sys.exit(1)

SUMMARIZE_TIME_OUT = 10 * 60  # 10 minutes

# Opcode categories for evaluation
OPCODE_CATEGORIES = {
    # 1. Arithmetic and Bitwise Operations
    'ARITHMETIC_AND_BITWISE': [
        'ADD', 'MUL', 'SUB', 'DIV', 'SDIV', 'MOD', 'SMOD', 'ADDMOD', 'MULMOD',
        'EXP', 'SIGNEXTEND', 'LT', 'GT', 'SLT', 'SGT', 'EQ', 'ISZERO', 'AND',
        'EVMOR', 'XOR', 'NOT', 'BYTE', 'SHL', 'SHR', 'SAR',
    ],
    # 2. Flow Control Operations
    'FLOW_CONTROL': ['STOP', 'JUMP', 'JUMPI', 'PC', 'JUMPDEST', 'RETURN', 'REVERT', 'INVALID', 'UNDEFINED'],
    # 3. Block and Transaction Information
    'BLOCK_AND_TRANSACTION': [
        'ADDRESS', 'BALANCE', 'ORIGIN', 'CALLER', 'CALLVALUE', 'CALLDATALOAD',
        'CALLDATASIZE', 'CALLDATACOPY', 'CODESIZE', 'CODECOPY', 'GASPRICE',
        'EXTCODESIZE', 'EXTCODECOPY', 'RETURNDATASIZE', 'RETURNDATACOPY',
        'EXTCODEHASH', 'BLOCKHASH', 'COINBASE', 'TIMESTAMP', 'NUMBER',
        'PREVRANDAO', 'DIFFICULTY', 'GASLIMIT', 'CHAINID', 'SELFBALANCE',
        'BASEFEE', 'BLOBHASH', 'BLOBBASEFEE',
    ],
    # 4. Stack Operations
    'STACK_OPERATIONS': ['POP', 'PUSHZERO', 'PUSH', 'DUP', 'SWAP'],
    # 5. Memory Operations
    'MEMORY_OPERATIONS': ['MLOAD', 'MSTORE', 'MSTORE8', 'MSIZE', 'MCOPY'],
    # 6. Storage Operations
    'STORAGE_OPERATIONS': ['SLOAD', 'SSTORE'],
    # 7. Transient Storage Operations
    'TRANSIENT_STORAGE_OPERATIONS': ['TLOAD', 'TSTORE'],
    # 8. System and Call Operations
    'SYSTEM_AND_CALLS': ['CREATE', 'CREATE2', 'CALL', 'CALLCODE', 'DELEGATECALL', 'STATICCALL', 'SELFDESTRUCT', 'GAS'],
    # 9. Logging Operations
    'LOGGING': ['LOG'],
    # 10. Hashing Operations
    'HASHING': ['SHA3'],  # Also known as KECCAK256
}

def get_opcode_category(opcode: str) -> str:
    """获取 opcode 的分类"""
    for cat, op_list in OPCODE_CATEGORIES.items():
        if opcode in op_list:
            return cat
    return "UNKNOWN"

def summarize_worker(opcode: str) -> Dict[str, Any]:
    """单个 opcode 的摘要化评估工作函数"""
    start = time.time()
    entry = {
        "opcode": opcode,
        "category": get_opcode_category(opcode),
        "success": False,
        "time": None,
        "rewriting_steps": None,  # list of edge.depth
        "error": None,
        "summary_status": get_summary_status(opcode) if opcode in OPCODES_SUMMARY_STATUS else None
    }
    
    try:
        from pyk.kcfg import KCFG
        _, proofs = summarize(opcode)
        proof_success = True
        steps_list = []
        for proof in proofs:
            # 1. All leaves not pending/stuck/vacuous/bounded
            for leaf in proof.kcfg.leaves:
                if proof.is_pending(leaf.id) or proof.kcfg.is_stuck(leaf.id) or proof.kcfg.is_vacuous(leaf.id) or proof.is_bounded(leaf.id):
                    proof_success = False
                    break
            if not proof_success:
                break
            # 2. Only one successor from init
            successors = proof.kcfg.successors(proof.init)
            if len(successors) != 1:
                proof_success = False
                break
            successor = successors[0]
            # 3. Edge/terminal/covered check
            if isinstance(successor, KCFG.Split):
                targets = successor.targets
                if len(proof.kcfg.edges()) != len(targets):
                    proof_success = False
                    break
                for target in targets:
                    s2 = proof.kcfg.successors(target.id)
                    if len(s2) != 1:
                        proof_success = False
                        break
                    edge = s2[0]
                    if not isinstance(edge, KCFG.Edge):
                        proof_success = False
                        break
                    if not (proof.is_terminal(edge.target.id) or proof.kcfg.is_covered(edge.target.id)):
                        proof_success = False
                        break
                    steps_list.append(edge.depth)
            else:
                if len(proof.kcfg.edges()) != 1:
                    proof_success = False
                    break
                if not isinstance(successor, KCFG.Edge):
                    proof_success = False
                    break
                if not (proof.is_terminal(successor.target.id) or proof.kcfg.is_covered(successor.target.id)):
                    proof_success = False
                    break
                steps_list.append(successor.depth)
        entry["success"] = proof_success
        entry["rewriting_steps"] = steps_list
    except Exception as e:
        entry["error"] = str(e) + "\n" + traceback.format_exc()
    finally:
        entry["time"] = time.time() - start
    
    return entry

def evaluate_summarize_effectiveness(timeout_sec: int = 600, max_workers: int = 4, skip_opcodes: List[str] = None) -> List[Dict[str, Any]]:
    """
    评估所有 opcode 的摘要化有效性
    
    Args:
        timeout_sec: 每个 opcode 评估的超时时间（秒）
        max_workers: 最大并行工作进程数
        skip_opcodes: 要跳过的 opcode 列表
    
    Returns:
        包含每个 opcode 评估结果的字典列表
    """
    if skip_opcodes is None:
        skip_opcodes = []
    
    # 过滤掉要跳过的 opcodes
    opcodes_to_evaluate = {opcode: info for opcode, info in OPCODES.items() if opcode not in skip_opcodes}
    
    if skip_opcodes:
        print(f"跳过 opcodes: {', '.join(skip_opcodes)}")
        print(f"评估 {len(opcodes_to_evaluate)} 个 opcodes，总共 {len(OPCODES)} 个")
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_opcode = {executor.submit(summarize_worker, opcode): opcode for opcode in opcodes_to_evaluate.keys()}
        for future in as_completed(future_to_opcode):
            opcode = future_to_opcode[future]
            try:
                result = future.result(timeout=timeout_sec)
            except Exception as e:
                result = {
                    "opcode": opcode,
                    "category": get_opcode_category(opcode),
                    "success": False,
                    "time": None,
                    "rewriting_steps": None,
                    "error": f"timeout or error: {str(e)}",
                    "summary_status": get_summary_status(opcode) if opcode in OPCODES_SUMMARY_STATUS else None
                }
            results.append(result)
    
    # 将跳过的 opcodes 添加到结果中
    for opcode in skip_opcodes:
        results.append({
            "opcode": opcode,
            "category": get_opcode_category(opcode),
            "success": False,
            "time": None,
            "rewriting_steps": None,
            "error": "SKIPPED",
            "summary_status": get_summary_status(opcode) if opcode in OPCODES_SUMMARY_STATUS else None
        })
    
    return results

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EVM Opcode Summarization Evaluator")
    parser.add_argument("--timeout", type=int, default=1800, help="每个 opcode 的超时时间（秒）")
    parser.add_argument("--workers", type=int, default=4, help="并行工作进程数")
    parser.add_argument("--skip-opcodes", nargs="+", default=[
        'BASEFEE', 'CALL', 'CALLCODE', 'CALLVALUE', 'CREATE', 'CREATE2',
        'DELEGATECALL', 'EXTCODECOPY', 'EXTCODEHASH', 'EXTCODESIZE',
        'JUMP', 'JUMPI', 'MUL', 'SELFDESTRUCT', 'STATICCALL', 'EXP', 'SAR', 'SHA3'
    ], help="要跳过的 opcode 列表")
    parser.add_argument("--output", default="results/data/summarize_evaluation_results.json", help="输出文件路径")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        print("开始 EVM Opcode 摘要化评估...")
        print(f"超时时间: {args.timeout} 秒")
        print(f"工作进程数: {args.workers}")
        print(f"跳过的 opcodes: {', '.join(args.skip_opcodes)}")
    
    # 执行评估
    results = evaluate_summarize_effectiveness(
        timeout_sec=args.timeout,
        max_workers=args.workers,
        skip_opcodes=args.skip_opcodes
    )
    
    # 统计结果
    successful = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"] and r["error"] != "SKIPPED")
    skipped = sum(1 for r in results if r["error"] == "SKIPPED")
    
    if args.verbose:
        print(f"\n评估完成:")
        print(f"  成功: {successful}")
        print(f"  失败: {failed}")
        print(f"  跳过: {skipped}")
        print(f"  总计: {len(results)}")
    
    # 保存结果
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "timeout_seconds": args.timeout,
                "max_workers": args.workers,
                "skipped_opcodes": args.skip_opcodes
            },
            "summary": {
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "skipped": skipped
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    if args.verbose:
        print(f"结果已保存到: {args.output}")
    
    # 返回退出码
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 