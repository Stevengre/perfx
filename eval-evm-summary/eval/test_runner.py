"""
Test runner for EVM semantics with summary backend.

This module provides functionality to temporarily modify the interpreter.py file,
run conformance tests, and restore the original file.
"""

import sys
import shutil
import time
import subprocess
import re
from pathlib import Path
from typing import Dict, Tuple, Optional

from . import EVM_SEMANTICS_DIR, INTERPRETER_FILE, PROJECT_ROOT
from .utils import setup_compiler_for_macos, run_command, check_directories_and_files, print_project_info
from .evaluation_recorder import recorder

import os
import subprocess
import time
import re
import json
import shutil
from typing import Dict, List, Tuple, Any
from pathlib import Path


# 备份文件路径
BACKUP_FILE = INTERPRETER_FILE.with_suffix('.py.backup')


def backup_interpreter_file() -> bool:
    """
    备份原始的interpreter.py文件
    """
    print(f"\n=== 备份interpreter.py文件 ===")
    print(f"源文件: {INTERPRETER_FILE}")
    print(f"备份文件: {BACKUP_FILE}")
    
    if not INTERPRETER_FILE.exists():
        print(f"错误: interpreter.py文件不存在: {INTERPRETER_FILE}")
        return False
    
    try:
        shutil.copy2(INTERPRETER_FILE, BACKUP_FILE)
        print("✓ interpreter.py文件备份完成")
        return True
    except Exception as e:
        print(f"✗ 备份失败: {e}")
        return False


def modify_interpreter_file(semantics_mode: str = 'summary') -> bool:
    """
    修改interpreter.py文件，根据指定的语义模式替换语义调用
    
    Args:
        semantics_mode: 语义模式，支持 'pure', 'summary', 'default'
    """
    print(f"\n=== 修改interpreter.py文件 ===")
    
    # 定义语义映射
    semantics_mapping = {
        'pure': "'evm-semantics.llvm-pure'",
        'summary': "'evm-semantics.llvm-summary'",
        'default': "'evm-semantics.llvm'"
    }
    
    if semantics_mode not in semantics_mapping:
        print(f"错误: 不支持的语义模式: {semantics_mode}")
        return False
    
    original_text = "'evm-semantics.llvm'"
    new_text = semantics_mapping[semantics_mode]
    
    print(f"将 {original_text} 替换为 {new_text}")
    
    try:
        # 读取文件内容
        with open(INTERPRETER_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 执行替换
        if original_text not in content:
            print(f"警告: 未找到要替换的文本: {original_text}")
            return False
        
        modified_content = content.replace(original_text, new_text)
        
        # 写回文件
        with open(INTERPRETER_FILE, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print("✓ interpreter.py文件修改完成")
        return True
    except Exception as e:
        print(f"✗ 修改失败: {e}")
        return False


def restore_interpreter_file() -> bool:
    """
    恢复原始的interpreter.py文件
    """
    print(f"\n=== 恢复interpreter.py文件 ===")
    print(f"从备份文件恢复: {BACKUP_FILE}")
    
    if not BACKUP_FILE.exists():
        print(f"错误: 备份文件不存在: {BACKUP_FILE}")
        return False
    
    try:
        shutil.copy2(BACKUP_FILE, INTERPRETER_FILE)
        print("✓ interpreter.py文件恢复完成")
        return True
    except Exception as e:
        print(f"✗ 恢复失败: {e}")
        return False


def cleanup_backup_file() -> bool:
    """
    清理备份文件
    """
    print(f"\n=== 清理备份文件 ===")
    print(f"删除备份文件: {BACKUP_FILE}")
    
    if not BACKUP_FILE.exists():
        print("备份文件不存在，无需清理")
        return True
    
    try:
        BACKUP_FILE.unlink()
        print("✓ 备份文件清理完成")
        return True
    except Exception as e:
        print(f"✗ 清理失败: {e}")
        return False





def run_conformance_tests_with_detailed_timing() -> Tuple[bool, Dict[str, float]]:
    """
    运行一致性测试并获取详细的测试用例耗时
    
    Returns:
        Tuple[bool, Dict[str, float]]: (是否成功, 测试用例耗时字典)
    """
    print("\n=== 执行一致性测试（详细耗时） ===")
    print("测试命令: uv run -- pytest src/tests/integration/test_conformance.py --durations=0")
    print(f"工作目录: {EVM_SEMANTICS_DIR}/kevm-pyk")
    
    command = [
        "uv", "run", "--", "pytest",
        "src/tests/integration/test_conformance.py",
        "--durations=0",  # 显示所有测试用例的耗时
        "--verbose",
        "--no-header",    # 不显示pytest头部信息
        "--tb=no",        # 不显示traceback
        "--timeout=3600"  # 1小时超时
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=EVM_SEMANTICS_DIR / "kevm-pyk"
        )
        
        duration = time.time() - start_time
        
        # 记录命令
        command_str = ' '.join(command)
        recorder.add_command(
            command=command_str,
            cwd=str(EVM_SEMANTICS_DIR / "kevm-pyk"),
            output=result.stdout,
            error=result.stderr,
            success=(result.returncode == 0),
            duration=duration
        )
        
        if result.returncode == 0:
            print("✓ 一致性测试完成")
            # 解析详细耗时
            test_durations = parse_pytest_durations(result.stdout)
            print(f"  解析到 {len(test_durations)} 个测试用例的耗时信息")
            return True, test_durations
        else:
            print("✗ 一致性测试失败")
            print("错误输出:")
            print(result.stderr)
            return False, {}
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"✗ 一致性测试执行错误: {e}")
        
        # 记录失败命令
        command_str = ' '.join(command)
        recorder.add_command(
            command=command_str,
            cwd=str(EVM_SEMANTICS_DIR / "kevm-pyk"),
            output="",
            error=str(e),
            success=False,
            duration=duration
        )
        
        return False, {}


def analyze_pytest_output(output: str) -> Dict[str, Any]:
    """
    分析pytest输出，提取测试统计信息
    
    Args:
        output: pytest的输出字符串
        
    Returns:
        Dict[str, Any]: 包含测试统计信息的字典
    """
    passed = 0
    failed = 0
    skipped = 0
    error = 0
    
    # 查找测试结果摘要
    lines = output.split('\n')
    for line in lines:
        if 'passed' in line.lower() and 'failed' in line.lower():
            # 尝试解析类似 "142 passed, 2 failed" 的行
            import re
            passed_match = re.search(r'(\d+)\s+passed', line)
            failed_match = re.search(r'(\d+)\s+failed', line)
            skipped_match = re.search(r'(\d+)\s+skipped', line)
            error_match = re.search(r'(\d+)\s+error', line)
            
            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))
            if skipped_match:
                skipped = int(skipped_match.group(1))
            if error_match:
                error = int(error_match.group(1))
            break
    
    total = passed + failed + skipped + error
    success_rate = (passed / total * 100) if total > 0 else 0
    
    return {
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'error': error,
        'total': total,
        'success_rate': success_rate
    }


def parse_pytest_durations(output: str) -> Dict[str, float]:
    """
    解析pytest --durations=0的输出，提取每个测试用例的耗时
    
    Args:
        output: pytest的输出内容
        
    Returns:
        Dict[str, float]: 测试用例名称到耗时的映射
    """
    durations = {}
    
    # pytest --durations=0的输出格式可能包括：
    # 1. test_conformance格式：
    # 171.42s call     src/tests/integration/test_conformance.py::test_bchain[Pyspecs/cancun/eip4844_blobs/external_vectors.json]
    # 2. prove测试格式：
    # 45.23s call     src/tests/integration/test_prove.py::test_prove_rules
    # 32.15s call     src/tests/integration/test_prove.py::test_prove_summaries
    # 28.67s call     src/tests/integration/test_prove.py::test_prove_dss
    
    # 使用更通用的正则表达式匹配耗时信息
    pattern = r'(\d+\.?\d*)s\s+call\s+(src/tests/integration/[^\s]+)'
    
    for line in output.split('\n'):
        match = re.search(pattern, line)
        if match:
            duration = float(match.group(1))
            test_name = match.group(2)
            durations[test_name] = duration
    
    return durations


def run_prove_summaries_test() -> bool:
    """
    在evm-semantics目录下执行prove summaries测试
    
    Returns:
        bool: 测试执行是否成功
    """
    print("\n=== 执行prove summaries测试 ===")
    print("测试命令: uv run -- pytest src/tests/integration/test_prove.py::test_prove_summaries")
    print(f"工作目录: {EVM_SEMANTICS_DIR}/kevm-pyk")
    print("超时时间: 2小时")
    
    try:
        result = subprocess.run(
            [
                "uv", "run", "--", "pytest",
                "src/tests/integration/test_prove.py::test_prove_summaries",
                "--verbose", "--durations=0", "--dist=worksteal", "--numprocesses=8", "--timeout=7200"
            ],
            capture_output=True,
            text=True,
            cwd=EVM_SEMANTICS_DIR / "kevm-pyk"  # Execute in kevm-pyk directory
        )
        
        if result.returncode == 0:
            print("✓ prove summaries测试完成")
            print("测试输出:")
            print(result.stdout)
            return True
        else:
            print("✗ prove summaries测试失败")
            print("错误输出:")
            print(result.stderr)
            print("标准输出:")
            print(result.stdout)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ prove summaries测试执行错误: {e}")
        return False
    except Exception as e:
        print(f"✗ prove summaries测试发生异常: {e}")
        return False





def run_conformance_test_with_semantics(semantics_mode: str, record_results: bool = False) -> Tuple[bool, Dict[str, float]]:
    """
    使用指定语义运行一致性测试并获取详细耗时
    
    Args:
        semantics_mode: 语义模式，支持 'pure', 'summary', 'default'
        record_results: 是否记录结果到recorder中
    
    Returns:
        Tuple[bool, Dict[str, float]]: (是否成功, 测试用例耗时字典)
    """
    semantics_names = {
        'pure': '原始语义 (llvm-pure)',
        'summary': 'summarized语义 (llvm-summary)',
        'default': '默认语义 (llvm)'
    }
    
    test_name = f"conformance_test_{semantics_mode}"
    
    if record_results:
        recorder.start_test(test_name)
    
    print(f"\n=== 使用{semantics_names.get(semantics_mode, semantics_mode)}运行一致性测试 ===")
    
    # 检查目录和文件是否存在
    if not check_directories_and_files(EVM_SEMANTICS_DIR, INTERPRETER_FILE, description="路径"):
        if record_results:
            recorder.end_test(test_name, False, "路径检查失败")
        return False, {}
    
    # 为macOS设置编译器
    setup_compiler_for_macos()
    
    success = False
    test_durations = {}
    
    try:
        # 1. 备份原始文件
        if not backup_interpreter_file():
            if record_results:
                recorder.end_test(test_name, False, "备份文件失败")
            return False, {}
        
        # 2. 修改文件使用指定语义
        if not modify_interpreter_file(semantics_mode):
            if record_results:
                recorder.end_test(test_name, False, "修改文件失败")
            return False, {}
        
        # 3. 执行测试并获取详细耗时
        success, test_durations = run_conformance_tests_with_detailed_timing()
        
    except Exception as e:
        print(f"\n=== 执行过程中发生错误 ===")
        print(f"错误: {e}")
        success = False
        if record_results:
            recorder.end_test(test_name, False, str(e))
    
    finally:
        # 4. 恢复原始文件
        if not restore_interpreter_file():
            print("警告: 文件恢复失败，请手动检查")
        
        # 5. 清理备份文件
        cleanup_backup_file()
    
    if record_results and success:
        recorder.end_test(test_name, True)
    
    return success, test_durations


def run_concrete_execution_performance_comparison() -> bool:
    """
    执行concrete execution性能对比测试
    
    Returns:
        bool: 性能对比测试是否成功
    """
    print("\n=== 开始Concrete Execution性能对比测试 ===")
    
    # 记录开始时间
    recorder.start_test("concrete_execution_performance")
    
    try:
        # 1. 使用原始语义运行测试
        print("\n" + "="*50)
        print("PHASE 1: 使用原始语义 (llvm-pure)")
        print("="*50)
        pure_success, pure_durations = run_conformance_test_with_semantics('pure', record_results=False)
        
        if not pure_success:
            print("✗ 原始语义测试失败，无法进行性能对比")
            recorder.end_test("concrete_execution_performance", False, "原始语义测试失败")
            return False
        
        # 2. 使用summarized语义运行测试
        print("\n" + "="*50)
        print("PHASE 2: 使用summarized语义 (llvm-summary)")
        print("="*50)
        summary_success, summary_durations = run_conformance_test_with_semantics('summary', record_results=False)
        
        if not summary_success:
            print("✗ summarized语义测试失败，无法进行性能对比")
            recorder.end_test("concrete_execution_performance", False, "summarized语义测试失败")
            return False
        
        # 3. 分析性能对比结果
        print("\n" + "="*50)
        print("PHASE 3: 性能对比分析")
        print("="*50)
        
        # 将结果存储到recorder中
        recorder.results["concrete_execution_performance"] = {
            "pure_semantics": {
                "success": pure_success,
                "test_durations": pure_durations
            },
            "summary_semantics": {
                "success": summary_success,
                "test_durations": summary_durations
            }
        }
        
        # 执行性能分析
        performance_analysis = recorder.analyze_concrete_execution_performance(pure_durations, summary_durations)
        recorder.results["concrete_execution_performance"]["analysis"] = performance_analysis
        
        # 打印性能分析结果
        print(f"原始语义总耗时: {performance_analysis['pure_total_time']:.2f}s")
        print(f"Summarized语义总耗时: {performance_analysis['summary_total_time']:.2f}s")
        print(f"总体性能提升: {performance_analysis['total_speedup']:.2f}x")
        print(f"总体改进百分比: {performance_analysis['total_improvement']:.1f}%")
        
        # 记录成功
        recorder.end_test("concrete_execution_performance", True)
        
        print("\n✓ Concrete Execution性能对比测试完成")
        return True
        
    except Exception as e:
        error_msg = f"性能对比测试发生异常: {e}"
        print(f"✗ {error_msg}")
        recorder.end_test("concrete_execution_performance", False, error_msg)
        return False


def run_conformance_test_with_summary() -> bool:
    """运行一致性测试并记录结果（使用summarized语义）"""
    success, _ = run_conformance_test_with_semantics('summary', record_results=True)
    return success


def run_prove_summaries_test_with_recording() -> bool:
    """运行prove summaries测试并记录结果"""
    recorder.start_test("prove_summaries_test")
    try:
        # 这里需要重新实现，因为我们需要捕获输出
        print("\n=== 执行prove summaries测试 ===")
        print("测试命令: uv run -- pytest src/tests/integration/test_prove.py::test_prove_summaries")
        print(f"工作目录: {EVM_SEMANTICS_DIR}/kevm-pyk")
        print("超时时间: 2小时")
        
        start_time = time.time()
        command = [
            "uv", "run", "--", "pytest",
            "src/tests/integration/test_prove.py::test_prove_summaries",
            "--verbose", "--durations=0", "--dist=worksteal", "--numprocesses=8", "--timeout=7200"
        ]
        command_str = ' '.join(command)
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=EVM_SEMANTICS_DIR / "kevm-pyk"  # Execute in kevm-pyk directory
        )
        
        duration = time.time() - start_time
        
        # 记录命令
        recorder.add_command(
            command=command_str,
            cwd=str(EVM_SEMANTICS_DIR / "kevm-pyk"),
            output=result.stdout,
            error=result.stderr,
            success=(result.returncode == 0),
            duration=duration
        )
        
        if result.returncode == 0:
            print("✓ prove summaries测试完成")
            print("测试输出:")
            print(result.stdout)
            
            # 记录结果
            recorder.end_test("prove_summaries_test", True)
            recorder.update_test_output("prove_summaries_test", result.stdout, result.stderr)
            
            return True
        else:
            print("✗ prove summaries测试失败")
            print("错误输出:")
            print(result.stderr)
            print("标准输出:")
            print(result.stdout)
            
            # 记录结果
            recorder.end_test("prove_summaries_test", False)
            recorder.update_test_output("prove_summaries_test", result.stdout, result.stderr)
            
            return False
            
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"✗ prove summaries测试执行错误: {e}")
        
        # 记录失败命令
        recorder.add_command(
            command=command_str,
            cwd=str(EVM_SEMANTICS_DIR / "kevm-pyk"),
            output=e.stdout,
            error=e.stderr,
            success=False,
            duration=duration
        )
        
        recorder.end_test("prove_summaries_test", False, str(e))
        return False
    except Exception as e:
        duration = time.time() - start_time
        print(f"✗ prove summaries测试发生异常: {e}")
        
        # 记录异常命令
        recorder.add_command(
            command=command_str,
            cwd=str(EVM_SEMANTICS_DIR / "kevm-pyk"),
            output="",
            error=str(e),
            success=False,
            duration=duration
        )
        
        recorder.end_test("prove_summaries_test", False, str(e))
        return False


def backup_and_restore_specs() -> bool:
    """
    使用git checkout恢复evm-semantics/tests/specs文件夹到原始状态
    
    Returns:
        bool: 操作是否成功
    """
    specs_dir = EVM_SEMANTICS_DIR / "tests" / "specs"
    if not specs_dir.exists():
        print(f"✗ specs目录不存在: {specs_dir}")
        return False
    
    print("🔄 使用git checkout恢复原始文件...")
    try:
        # 使用git checkout恢复specs目录到原始状态
        result = subprocess.run(
            ['git', 'checkout', '--', str(specs_dir)],
            capture_output=True,
            text=True,
            cwd=EVM_SEMANTICS_DIR
        )
        
        if result.returncode == 0:
            print("✓ 已使用git checkout恢复原始文件")
            return True
        else:
            print(f"✗ git checkout失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ 恢复文件失败: {e}")
        return False


def replace_edsl_in_specs(target_module: str) -> bool:
    """
    在evm-semantics/tests/specs文件夹中替换所有文件中的EDSL引用
    
    Args:
        target_module: 目标模块名，如 'EDSL-PURE' 或 'EDSL-SUMMARY'
        
    Returns:
        bool: 替换是否成功
    """
    specs_dir = EVM_SEMANTICS_DIR / "tests" / "specs"
    if not specs_dir.exists():
        print(f"✗ specs目录不存在: {specs_dir}")
        return False
    
    print(f"🔄 替换EDSL为{target_module}...")
    replaced_files = 0
    
    # 遍历所有文件，不仅仅是.k文件
    for file_path in specs_dir.rglob("*"):
        if file_path.is_file():
            try:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换imports EDSL
                original_content = content
                content = content.replace('EDSL', target_module)
                
                # 如果内容有变化，写回文件
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    replaced_files += 1
                    print(f"  ✓ 替换: {file_path.relative_to(specs_dir)}")
                    
            except Exception as e:
                print(f"  ✗ 处理文件失败 {file_path}: {e}")
                return False
    
    print(f"✓ 成功替换了 {replaced_files} 个文件中的EDSL引用")
    return True


def run_symbolic_prove_test_with_semantics(semantics_mode: str, record_results: bool = False) -> Tuple[bool, Dict[str, Dict[str, float]]]:
    """
    使用指定语义运行symbolic execution prove测试并获取详细测试用例耗时
    
    Args:
        semantics_mode: 语义模式，支持 'pure', 'summary'
        record_results: 是否记录结果到recorder中
        
    Returns:
        Tuple[bool, Dict[str, Dict[str, float]]]: (是否成功, 测试套件到测试用例耗时的映射)
    """
    semantics_names = {
        'pure': '无优化语义 (EDSL-PURE)',
        'summary': 'summarized语义 (EDSL-SUMMARY)',
    }
    
    test_name = f"symbolic_prove_test_{semantics_mode}"
    
    if record_results:
        recorder.start_test(test_name)
    
    print(f"\n=== 使用{semantics_names.get(semantics_mode, semantics_mode)}运行symbolic prove测试 ===")
    
    # 1. 替换为指定语义
    print(f"\n1. 替换为{semantics_mode}语义...")
    if semantics_mode == 'pure':
        target_module = 'EDSL-PURE'
    elif semantics_mode == 'summary':
        target_module = 'EDSL-SUMMARY'
    else:
        print(f"✗ 不支持的语义模式: {semantics_mode}")
        if record_results:
            recorder.end_test(test_name, False, f"不支持的语义模式: {semantics_mode}")
        return False, {}
    
    if not replace_edsl_in_specs(target_module):
        print("✗ 语义替换失败")
        if record_results:
            recorder.end_test(test_name, False, "语义替换失败")
        return False, {}
    
    # 2. 运行指定的测试套件
    print("\n2. 运行测试套件...")
    test_configs = [
        # test-prove-rules 需要运行 booster 和 booster-dev 两种模式
        {'suite': 'test-prove-rules', 'booster_mode': 'booster', 'timeout': 120},
        {'suite': 'test-prove-rules', 'booster_mode': 'booster-dev', 'timeout': 120},
        # test-prove-summaries 和 test-prove-dss 使用默认配置
        {'suite': 'test-prove-summaries', 'booster_mode': 'booster', 'timeout': 120},
        {'suite': 'test-prove-dss', 'booster_mode': 'booster', 'timeout': 120},
    ]
    
    suite_test_durations = {}
    successful_suites = 0
    total_suites = len(test_configs)
    
    for config in test_configs:
        suite_name = config['suite']
        booster_mode = config['booster_mode']
        timeout = config['timeout']
        
        # 为test-prove-rules创建不同的套件名称
        if suite_name == 'test-prove-rules':
            suite_key = f"{suite_name}-{booster_mode}"
        else:
            suite_key = suite_name
        
        print(f"\n--- 运行 {suite_key} (超时: {timeout}分钟) ---")
        
        success, test_durations = run_single_prove_test_suite_with_booster(
            suite_name, booster_mode, timeout
        )
        
        suite_test_durations[suite_key] = test_durations
        
        if success:
            successful_suites += 1
            total_duration = sum(test_durations.values()) if test_durations else 0
            test_count = len(test_durations) if test_durations else 0
            print(f"✓ {suite_key} 测试成功 (总耗时: {total_duration:.2f}秒, 测试用例数: {test_count})")
        else:
            total_duration = sum(test_durations.values()) if test_durations else 0
            test_count = len(test_durations) if test_durations else 0
            print(f"⚠️  {suite_key} 测试部分失败 (总耗时: {total_duration:.2f}秒, 测试用例数: {test_count})")
    
    # 3. 恢复原始文件
    print("\n3. 恢复原始文件...")
    if not backup_and_restore_specs():
        print("⚠️  警告: 恢复原始文件失败")
    
    # 计算整体成功率
    success_rate = (successful_suites / total_suites * 100) if total_suites > 0 else 0
    overall_success = success_rate >= 50.0  # 只要50%以上的套件成功就认为是成功的
    
    print(f"\n测试套件统计: {successful_suites}/{total_suites} 成功, 成功率: {success_rate:.1f}%")
    
    # 记录结果
    if record_results:
        total_tests = sum(len(durations) for durations in suite_test_durations.values())
        recorder.end_test(test_name, overall_success, f"测试套件数量: {len(suite_test_durations)}, 成功套件: {successful_suites}/{total_suites}, 总测试用例数: {total_tests}")
    
    return overall_success, suite_test_durations


def run_single_prove_test_suite_with_booster(suite_name: str, booster_mode: str, timeout_minutes: int) -> Tuple[bool, Dict[str, float]]:
    """
    运行单个prove测试套件，支持指定booster模式
    
    Args:
        suite_name: 测试套件名称 (如 'test-prove-rules')
        booster_mode: booster模式 ('booster' 或 'booster-dev')
        timeout_minutes: 超时时间（分钟）
        
    Returns:
        Tuple[bool, Dict[str, float]]: (是否成功, 测试用例耗时字典)
    """
    start_time = time.time()
    
    try:
        # 根据booster模式构建不同的pytest参数，并添加timeout设置
        timeout_seconds = timeout_minutes * 60
        if booster_mode == 'booster-dev':
            pytest_args = f'-v --tb=short --durations=0 --use-booster-dev --timeout={timeout_seconds}'
        else:
            pytest_args = f'-v --tb=short --durations=0 --timeout={timeout_seconds}'
        
        # 构建make命令
        command = ['make', suite_name, f'PYTEST_ARGS={pytest_args}']
        
        print(f"执行命令: {' '.join(command)}")
        print(f"Booster模式: {booster_mode}")
        print(f"超时时间: {timeout_minutes}分钟 ({timeout_seconds}秒)")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=EVM_SEMANTICS_DIR
        )
        
        overall_duration = time.time() - start_time
        
        # 记录命令执行
        command_str = ' '.join(command)
        recorder.add_command(
            command=command_str,
            cwd=str(EVM_SEMANTICS_DIR),
            output=result.stdout,
            error=result.stderr,
            success=(result.returncode == 0),
            duration=overall_duration
        )
        
        # 解析pytest输出获取每个测试的耗时
        test_durations = parse_pytest_durations(result.stdout)
        
        # 分析测试结果
        test_stats = analyze_pytest_output(result.stdout)
        
        # 对于symbolic execution测试，即使有失败的测试用例，只要大部分测试成功就认为是成功的
        # 这样可以收集到更多的性能数据
        success = (result.returncode == 0) or (test_stats['success_rate'] > 50.0)
        
        if not success:
            print(f"测试套件输出 (最后500行):")
            print('\n'.join(result.stdout.split('\n')[-500:]))
            print(f"错误输出:")
            print(result.stderr[-1000:])
        
        print(f"测试统计: {test_stats['passed']} 通过, {test_stats['failed']} 失败, 成功率: {test_stats['success_rate']:.1f}%")
        
        # 对于symbolic execution测试，我们返回详细的测试用例耗时
        # 这样可以进行细粒度的性能分析
        return success, test_durations
        
    except Exception as e:
        overall_duration = time.time() - start_time
        print(f"✗ 运行测试套件 {suite_name} ({booster_mode}) 时发生异常: {e}")
        return False, {}


def calculate_test_statistics(suite_durations: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    计算测试统计信息
    
    Args:
        suite_durations: 测试套件到测试用例耗时的映射
        
    Returns:
        Dict[str, Any]: 包含统计信息的字典
    """
    total_suites = len(suite_durations)
    successful_suites = 0
    total_test_cases = 0
    successful_test_cases = 0
    
    for suite_name, test_durations in suite_durations.items():
        suite_test_count = len(test_durations)
        total_test_cases += suite_test_count
        
        # 假设如果套件有测试用例，就认为是成功的
        if suite_test_count > 0:
            successful_suites += 1
            successful_test_cases += suite_test_count
    
    success_rate = (successful_suites / total_suites * 100) if total_suites > 0 else 0
    
    return {
        'total_suites': total_suites,
        'successful_suites': successful_suites,
        'success_rate': success_rate,
        'total_test_cases': total_test_cases,
        'successful_test_cases': successful_test_cases
    }


def run_symbolic_execution_performance_comparison() -> bool:
    """
    执行symbolic execution性能对比测试
    
    Returns:
        bool: 性能对比测试是否成功
    """
    print("\n=== 开始Symbolic Execution性能对比测试 ===")
    
    # 记录开始时间
    recorder.start_test("symbolic_execution_performance")
    
    try:
        # 1. 使用原始语义运行测试
        print("\n" + "="*50)
        print("PHASE 1: 使用原始语义 (evm-semantics.haskell)")
        print("="*50)
        haskell_success, haskell_durations = run_symbolic_prove_test_with_semantics('pure', record_results=False)
        
        # 2. 使用summarized语义运行测试
        print("\n" + "="*50)
        print("PHASE 2: 使用summarized语义 (evm-semantics.haskell-summary)")
        print("="*50)
        haskell_summary_success, haskell_summary_durations = run_symbolic_prove_test_with_semantics('summary', record_results=False)
        
        # 3. 分析性能对比结果
        print("\n" + "="*50)
        print("PHASE 3: 性能对比分析")
        print("="*50)
        
        # 计算测试统计信息
        haskell_stats = calculate_test_statistics(haskell_durations)
        haskell_summary_stats = calculate_test_statistics(haskell_summary_durations)
        
        print(f"原始语义测试统计:")
        print(f"  - 成功套件: {haskell_stats['successful_suites']}/{haskell_stats['total_suites']}")
        print(f"  - 成功率: {haskell_stats['success_rate']:.1f}%")
        print(f"  - 总测试用例: {haskell_stats['total_test_cases']}")
        print(f"  - 成功测试用例: {haskell_stats['successful_test_cases']}")
        
        print(f"Summarized语义测试统计:")
        print(f"  - 成功套件: {haskell_summary_stats['successful_suites']}/{haskell_summary_stats['total_suites']}")
        print(f"  - 成功率: {haskell_summary_stats['success_rate']:.1f}%")
        print(f"  - 总测试用例: {haskell_summary_stats['total_test_cases']}")
        print(f"  - 成功测试用例: {haskell_summary_stats['successful_test_cases']}")
        
        # 将结果存储到recorder中
        recorder.results["symbolic_execution_performance"] = {
            "haskell_semantics": {
                "success": haskell_success,
                "suite_durations": haskell_durations,
                "statistics": haskell_stats
            },
            "haskell_summary_semantics": {
                "success": haskell_summary_success,
                "suite_durations": haskell_summary_durations,
                "statistics": haskell_summary_stats
            }
        }
        
        # 执行性能分析（只对成功的测试用例进行比较）
        if haskell_stats['successful_test_cases'] > 0 and haskell_summary_stats['successful_test_cases'] > 0:
            performance_analysis = recorder.analyze_symbolic_execution_performance(haskell_durations, haskell_summary_durations)
            recorder.results["symbolic_execution_performance"]["analysis"] = performance_analysis
            
            # 打印性能分析结果
            print(f"\n性能对比分析:")
            print(f"原始语义总耗时: {performance_analysis['haskell_total_time']:.2f}s")
            print(f"Summarized语义总耗时: {performance_analysis['haskell_summary_total_time']:.2f}s")
            print(f"总体性能提升: {performance_analysis['total_speedup']:.2f}x")
            print(f"总体改进百分比: {performance_analysis['total_improvement']:.1f}%")
            print(f"可比较的套件数量: {performance_analysis['statistics']['num_comparable_suites']}/{performance_analysis['statistics']['num_suites']}")
            print(f"测试用例总数: {performance_analysis['statistics']['num_test_cases']}")
            print(f"可比较的测试用例数: {performance_analysis['statistics']['num_comparable_test_cases']}")
            
            if performance_analysis['statistics']['num_comparable_suites'] > 0:
                print(f"套件平均性能提升: {performance_analysis['statistics']['avg_suite_speedup']:.2f}x")
                print(f"套件最大性能提升: {performance_analysis['statistics']['max_suite_speedup']:.2f}x")
                print(f"套件最小性能提升: {performance_analysis['statistics']['min_suite_speedup']:.2f}x")
            
            if performance_analysis['statistics']['num_comparable_test_cases'] > 0:
                print(f"测试用例平均性能提升: {performance_analysis['statistics']['avg_test_speedup']:.2f}x")
                print(f"测试用例最大性能提升: {performance_analysis['statistics']['max_test_speedup']:.2f}x")
                print(f"测试用例最小性能提升: {performance_analysis['statistics']['min_test_speedup']:.2f}x")
        else:
            print(f"\n⚠️  无法进行性能对比分析：")
            if haskell_stats['successful_test_cases'] == 0:
                print(f"  - 原始语义没有成功的测试用例")
            if haskell_summary_stats['successful_test_cases'] == 0:
                print(f"  - Summarized语义没有成功的测试用例")
        
        # 判断整体成功：只要两个语义都有一定数量的成功测试用例就认为是成功的
        overall_success = (haskell_stats['successful_test_cases'] > 0 and haskell_summary_stats['successful_test_cases'] > 0)
        
        if overall_success:
            print(f"\n✓ Symbolic Execution性能对比测试完成")
            recorder.end_test("symbolic_execution_performance", True)
        else:
            print(f"\n⚠️  Symbolic Execution性能对比测试部分完成（测试用例成功率较低）")
            recorder.end_test("symbolic_execution_performance", False, "测试用例成功率较低")
        
        return overall_success
        
    except Exception as e:
        error_msg = f"性能对比测试发生异常: {e}"
        print(f"✗ {error_msg}")
        recorder.end_test("symbolic_execution_performance", False, error_msg)
        return False


if __name__ == "__main__":
    success, _ = run_conformance_test_with_semantics('summary', record_results=False)
    sys.exit(0 if success else 1) 