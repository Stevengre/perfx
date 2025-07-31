"""
KEVM Builder for EVM semantics.

This module provides functionality to build KEVM semantics with proper
compiler setup and dependency management.
"""

import os
import subprocess
import sys
import platform
import time
from pathlib import Path

from . import EVM_SEMANTICS_DIR, KEVM_PYK_DIR, PROJECT_ROOT
from .utils import setup_compiler_for_macos, run_command, run_command_with_timeout, check_directories_and_files, print_project_info
from .evaluation_recorder import recorder


def init_git_submodules() -> bool:
    """
    初始化git子模块：git submodule update --init --recursive
    """
    return run_command(
        ["git", "submodule", "update", "--init", "--recursive"],
        "初始化git子模块",
        cwd=EVM_SEMANTICS_DIR
    )


def setup_poetry_environment() -> bool:
    """
    设置Poetry环境：make poetry
    """
    return run_command(
        ["make", "poetry"],
        "设置Poetry环境",
        cwd=EVM_SEMANTICS_DIR
    )


def clean_build() -> bool:
    """
    清理构建产物：poetry -C evm-semantics/kevm-pyk run kdist clean
    """
    return run_command(
        ["poetry", "run", "kdist", "clean"],
        "清理构建产物",
        cwd=KEVM_PYK_DIR
    )


def build_plugin_and_semantics_with_timeout(plugin_timeout_minutes: int = 30, semantics_timeout_minutes: int = 60) -> bool:
    """
    构建plugin和semantics，带超时限制
    
    Args:
        plugin_timeout_minutes: plugin构建超时时间（分钟），默认30分钟
        semantics_timeout_minutes: semantics构建超时时间（分钟），默认60分钟
    """
    # 1. 构建plugin（带超时）
    plugin_success = build_plugin_with_timeout(plugin_timeout_minutes)
    
    # 2. 构建所有semantics（带超时）
    semantics_success = build_all_semantics_with_timeout(semantics_timeout_minutes)
    
    # 3. 如果任一构建超时，清理后一起重新构建
    if not plugin_success or not semantics_success:
        print(f"\n=== 构建超时，清理后重新构建plugin和semantics ===")
        if not clean_build():
            return False
        
        # 一起重新构建plugin和semantics（无超时限制）
        if not build_plugin():
            return False
        if not build_all_semantics():
            return False
    
    return True


def build_plugin_with_timeout(timeout_minutes: int = 30) -> bool:
    """
    构建evm-semantics.plugin，带超时限制
    
    Args:
        timeout_minutes: 超时时间（分钟），默认30分钟
    """
    plugin_cmd = ["poetry", "-C", "kevm-pyk", "run", "kdist", "--verbose", "build", "evm-semantics.plugin"]
    
    # 如果是Apple Silicon，添加特殊标志
    if platform.machine() == "arm64" and platform.system() == "Darwin":
        env = os.environ.copy()
        env["APPLE_SILICON"] = "true"
        print(f"\n=== 构建evm-semantics.plugin (Apple Silicon, 超时: {timeout_minutes}分钟) ===")
        print(f"执行命令: {' '.join(plugin_cmd)} (APPLE_SILICON=true)")
        print(f"工作目录: {EVM_SEMANTICS_DIR}")
        try:
            result = subprocess.run(plugin_cmd, check=True, cwd=EVM_SEMANTICS_DIR, env=env, timeout=timeout_minutes * 60)
            print("✓ 构建evm-semantics.plugin 完成")
            return True
        except subprocess.TimeoutExpired:
            print(f"✗ 构建evm-semantics.plugin 超时 ({timeout_minutes}分钟)")
            return False
        except subprocess.CalledProcessError as e:
            print(f"✗ 构建evm-semantics.plugin 失败: {e}")
            
            # 显示可以复制的命令
            print("\n" + "="*60)
            print("构建失败！请尝试手动执行以下命令：")
            print("="*60)
            print(f"cd {EVM_SEMANTICS_DIR}")
            print("export APPLE_SILICON=true")
            print(f"{' '.join(plugin_cmd)}")
            print("="*60)
            
            return False
    else:
        return run_command_with_timeout(plugin_cmd, "构建evm-semantics.plugin", timeout_minutes * 60, cwd=KEVM_PYK_DIR)


def build_all_semantics_with_timeout(timeout_minutes: int = 60) -> bool:
    """
    构建所有semantics，带超时限制
    
    Args:
        timeout_minutes: 超时时间（分钟），默认60分钟
    """
    return run_command_with_timeout(
        ["poetry", "run", "kdist", "--verbose", "build", "-j6"],
        "构建所有semantics",
        timeout_minutes * 60,
        cwd=KEVM_PYK_DIR
    )


def build_plugin() -> bool:
    """
    构建evm-semantics.plugin（无超时限制）
    """
    plugin_cmd = ["poetry", "-C", "kevm-pyk", "run", "kdist", "--verbose", "build", "evm-semantics.plugin"]
    
    # 如果是Apple Silicon，添加特殊标志
    if platform.machine() == "arm64" and platform.system() == "Darwin":
        env = os.environ.copy()
        env["APPLE_SILICON"] = "true"
        print("\n=== 构建evm-semantics.plugin (Apple Silicon) ===")
        print(f"执行命令: {' '.join(plugin_cmd)} (APPLE_SILICON=true)")
        print(f"工作目录: {EVM_SEMANTICS_DIR}")
        
        start_time = time.time()
        command_str = ' '.join(plugin_cmd)
        
        try:
            result = subprocess.run(plugin_cmd, check=True, cwd=EVM_SEMANTICS_DIR, env=env, capture_output=True, text=True)
            duration = time.time() - start_time
            print("✓ 构建evm-semantics.plugin 完成")
            
            # 记录命令
            recorder.add_command(
                command=command_str,
                cwd=str(EVM_SEMANTICS_DIR),
                env_vars={"APPLE_SILICON": "true"},
                output=result.stdout,
                error=result.stderr,
                success=True,
                duration=duration
            )
            
            return True
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            print(f"✗ 构建evm-semantics.plugin 失败: {e}")
            
            # 显示可以复制的命令
            print("\n" + "="*60)
            print("构建失败！请尝试手动执行以下命令：")
            print("="*60)
            print(f"cd {EVM_SEMANTICS_DIR}")
            print("export APPLE_SILICON=true")
            print(f"{command_str}")
            print("="*60)
            
            # 记录命令
            recorder.add_command(
                command=command_str,
                cwd=str(EVM_SEMANTICS_DIR),
                env_vars={"APPLE_SILICON": "true"},
                output=e.stdout,
                error=e.stderr,
                success=False,
                duration=duration
            )
            
            return False
    else:
        return run_command(plugin_cmd, "构建evm-semantics.plugin", cwd=KEVM_PYK_DIR)


def build_all_semantics() -> bool:
    """
    构建所有semantics（无超时限制）
    """
    return run_command(
        ["poetry", "run", "kdist", "--verbose", "build", "-j6"],
        "构建所有semantics",
        cwd=KEVM_PYK_DIR
    )


def auto_build(
    build_dir: Path,
    plugin_timeout_minutes: int = 30, 
    semantics_timeout_minutes: int = 60,
    project_name: str | None = None
) -> bool:
    """
    自动构建流程：初始化子模块 -> 构建plugin和semantics（全部用uv）
    
    Args:
        plugin_timeout_minutes: plugin构建超时时间（分钟），默认30分钟
        semantics_timeout_minutes: semantics构建超时时间（分钟），默认60分钟
        build_dir: 构建目录（必需参数）
        project_name: project名称，用于--project参数，可选，默认为None（不使用--project）
    """
    # 开始记录构建过程
    recorder.start_test("build")
    
    try:
        print("开始KEVM自动构建...")
        print_project_info()
        print(f"构建目录: {build_dir}")
        print(f"Project名称: {project_name if project_name else 'None (不使用--project)'}")
        
        # 检查目录是否存在
        if not check_directories_and_files(build_dir, description="构建目录"):
            recorder.end_test("build", False, "构建目录检查失败")
            return False
        
        # 为macOS设置编译器
        setup_compiler_for_macos()
        
        # 检查并设置CC/CXX（仅macOS）
        env = os.environ.copy()
        if platform.system() == "Darwin":
            llvm_clang = "/opt/homebrew/opt/llvm@14/bin/clang"
            llvm_clangxx = "/opt/homebrew/opt/llvm@14/bin/clang++"
            if os.path.exists(llvm_clang) and os.path.exists(llvm_clangxx):
                env["CC"] = llvm_clang
                env["CXX"] = llvm_clangxx
                print(f"设置编译器: CC={llvm_clang}, CXX={llvm_clangxx}")
            else:
                print("警告: 未找到Homebrew LLVM 14, 未设置CC/CXX环境变量")
            # Apple Silicon 特殊标志
            if platform.machine() == "arm64":
                env["APPLE_SILICON"] = "true"
                print("设置APPLE_SILICON=true (Apple Silicon)")
        
        # 0. 初始化git子模块
        if not init_git_submodules():
            recorder.end_test("build", False, "git子模块初始化失败")
            return False
        
        # 1. 构建plugin
        print("\n=== 构建evm-semantics.plugin ===")
        if project_name:
            plugin_cmd = ["uv", "--project", project_name, "run", "--", "kdist", "--verbose", "build", "evm-semantics.plugin"]
        else:
            plugin_cmd = ["uv", "run", "--", "kdist", "--verbose", "build", "evm-semantics.plugin"]
        print(f"执行命令: {' '.join(plugin_cmd)}")
        print(f"工作目录: {build_dir}")
        start_time = time.time()
        command_str = ' '.join(plugin_cmd)
        try:
            result = subprocess.run(plugin_cmd, check=True, cwd=build_dir, env=env, timeout=plugin_timeout_minutes * 60, capture_output=True, text=True)
            duration = time.time() - start_time
            print("✓ 构建evm-semantics.plugin 完成")
            recorder.add_command(
                command=command_str,
                cwd=str(build_dir),
                env_vars={"APPLE_SILICON": "true"} if "APPLE_SILICON" in env else None,
                output=result.stdout,
                error=result.stderr,
                success=True,
                duration=duration
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"✗ 构建evm-semantics.plugin 超时 ({plugin_timeout_minutes}分钟)")
            recorder.add_command(
                command=command_str,
                cwd=str(build_dir),
                env_vars={"APPLE_SILICON": "true"} if "APPLE_SILICON" in env else None,
                output="",
                error=f"Timeout after {plugin_timeout_minutes * 60} seconds",
                success=False,
                duration=duration
            )
            recorder.end_test("build", False, f"plugin构建超时 ({plugin_timeout_minutes}分钟)")
            return False
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            print(f"✗ 构建evm-semantics.plugin 失败: {e}")
            
            # 显示可以复制的命令
            print("\n" + "="*60)
            print("构建失败！请尝试手动执行以下命令：")
            print("="*60)
            print(f"cd {build_dir}")
            if "APPLE_SILICON" in env:
                print("export APPLE_SILICON=true")
            if "CC" in env:
                print(f"export CC={env['CC']}")
            if "CXX" in env:
                print(f"export CXX={env['CXX']}")
            print(f"{command_str}")
            print("="*60)
            
            recorder.add_command(
                command=command_str,
                cwd=str(build_dir),
                env_vars={"APPLE_SILICON": "true"} if "APPLE_SILICON" in env else None,
                output=e.stdout,
                error=e.stderr,
                success=False,
                duration=duration
            )
            recorder.end_test("build", False, f"plugin构建失败: {e}")
            return False
        
        # 2. 构建所有semantics
        print("\n=== 构建所有semantics ===")
        if project_name:
            semantics_cmd = ["uv", "--project", project_name, "run", "--", "kdist", "--verbose", "build", "-j6"]
        else:
            semantics_cmd = ["uv", "run", "--", "kdist", "--verbose", "build", "-j6"]
        print(f"执行命令: {' '.join(semantics_cmd)}")
        print(f"工作目录: {build_dir}")
        start_time = time.time()
        command_str = ' '.join(semantics_cmd)
        try:
            result = subprocess.run(semantics_cmd, check=True, cwd=build_dir, env=env, timeout=semantics_timeout_minutes * 60, capture_output=True, text=True)
            duration = time.time() - start_time
            print("✓ 构建所有semantics 完成")
            recorder.add_command(
                command=command_str,
                cwd=str(build_dir),
                env_vars={"APPLE_SILICON": "true"} if "APPLE_SILICON" in env else None,
                output=result.stdout,
                error=result.stderr,
                success=True,
                duration=duration
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"✗ 构建所有semantics 超时 ({semantics_timeout_minutes}分钟)")
            recorder.add_command(
                command=command_str,
                cwd=str(build_dir),
                env_vars={"APPLE_SILICON": "true"} if "APPLE_SILICON" in env else None,
                output="",
                error=f"Timeout after {semantics_timeout_minutes * 60} seconds",
                success=False,
                duration=duration
            )
            recorder.end_test("build", False, f"semantics构建超时 ({semantics_timeout_minutes}分钟)")
            return False
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            print(f"✗ 构建所有semantics 失败: {e}")
            
            # 显示可以复制的命令
            print("\n" + "="*60)
            print("构建失败！请尝试手动执行以下命令：")
            print("="*60)
            print(f"cd {build_dir}")
            if "APPLE_SILICON" in env:
                print("export APPLE_SILICON=true")
            if "CC" in env:
                print(f"export CC={env['CC']}")
            if "CXX" in env:
                print(f"export CXX={env['CXX']}")
            print(f"{command_str}")
            print("="*60)
            
            recorder.add_command(
                command=command_str,
                cwd=str(build_dir),
                env_vars={"APPLE_SILICON": "true"} if "APPLE_SILICON" in env else None,
                output=e.stdout,
                error=e.stderr,
                success=False,
                duration=duration
            )
            recorder.end_test("build", False, f"semantics构建失败: {e}")
            return False
        
        print("\n=== 构建完成 ===")
        print("所有目标构建成功！")
        
        # 记录成功
        recorder.end_test("build", True)
        return True
        
    except Exception as e:
        # 记录异常
        recorder.end_test("build", False, str(e))
        return False


def uv_auto_build(plugin_timeout_minutes: int = 30, semantics_timeout_minutes: int = 60) -> bool:
    """
    使用uv进行自动构建流程：初始化子模块 -> 构建plugin和semantics
    
    Args:
        plugin_timeout_minutes: plugin构建超时时间（分钟），默认30分钟
        semantics_timeout_minutes: semantics构建超时时间（分钟），默认60分钟
    """
    # 开始记录构建过程
    recorder.start_test("build")
    
    try:
        print("开始KEVM自动构建 (使用uv)...")
        print_project_info()
        
        # 检查目录是否存在
        if not check_directories_and_files(EVM_SEMANTICS_DIR, description="目录"):
            recorder.end_test("build", False, "目录检查失败")
            return False
        
        # 为macOS设置编译器
        setup_compiler_for_macos()
        
        # 0. 初始化git子模块
        if not init_git_submodules():
            recorder.end_test("build", False, "git子模块初始化失败")
            return False
        
        # 1. 构建plugin（使用uv）
        print("\n=== 构建evm-semantics.plugin (使用uv) ===")
        plugin_cmd = ["uv", "run", "kdist", "--verbose", "build", "evm-semantics.plugin"]
        
        # 如果是Apple Silicon，添加特殊标志
        if platform.machine() == "arm64" and platform.system() == "Darwin":
            env = os.environ.copy()
            env["APPLE_SILICON"] = "true"
            print(f"执行命令: {' '.join(plugin_cmd)} (APPLE_SILICON=true)")
            print(f"工作目录: {PROJECT_ROOT}")
            
            start_time = time.time()
            command_str = ' '.join(plugin_cmd)
            
            try:
                result = subprocess.run(plugin_cmd, check=True, cwd=PROJECT_ROOT, env=env, timeout=plugin_timeout_minutes * 60, capture_output=True, text=True)
                duration = time.time() - start_time
                print("✓ 构建evm-semantics.plugin 完成")
                
                # 记录命令
                recorder.add_command(
                    command=command_str,
                    cwd=str(PROJECT_ROOT),
                    env_vars={"APPLE_SILICON": "true"},
                    output=result.stdout,
                    error=result.stderr,
                    success=True,
                    duration=duration
                )
                
            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                print(f"✗ 构建evm-semantics.plugin 超时 ({plugin_timeout_minutes}分钟)")
                
                # 记录命令
                recorder.add_command(
                    command=command_str,
                    cwd=str(PROJECT_ROOT),
                    env_vars={"APPLE_SILICON": "true"},
                    output="",
                    error=f"Timeout after {plugin_timeout_minutes * 60} seconds",
                    success=False,
                    duration=duration
                )
                
                recorder.end_test("build", False, f"plugin构建超时 ({plugin_timeout_minutes}分钟)")
                return False
            except subprocess.CalledProcessError as e:
                duration = time.time() - start_time
                print(f"✗ 构建evm-semantics.plugin 失败: {e}")
                
                # 记录命令
                recorder.add_command(
                    command=command_str,
                    cwd=str(PROJECT_ROOT),
                    env_vars={"APPLE_SILICON": "true"},
                    output=e.stdout,
                    error=e.stderr,
                    success=False,
                    duration=duration
                )
                
                recorder.end_test("build", False, f"plugin构建失败: {e}")
                return False
        else:
            if not run_command_with_timeout(plugin_cmd, "构建evm-semantics.plugin", plugin_timeout_minutes * 60, cwd=EVM_SEMANTICS_DIR):
                recorder.end_test("build", False, "plugin构建失败")
                return False
        
        # 2. 构建所有semantics（使用uv）
        print("\n=== 构建所有semantics (使用uv) ===")
        semantics_cmd = ["uv", "run", "kdist", "--verbose", "build", "-j6"]
        
        if not run_command_with_timeout(semantics_cmd, "构建所有semantics", semantics_timeout_minutes * 60, cwd=EVM_SEMANTICS_DIR):
            recorder.end_test("build", False, "semantics构建失败")
            return False
        
        print("\n=== 构建完成 ===")
        print("所有目标构建成功！")
        
        # 记录成功
        recorder.end_test("build", True)
        return True
        
    except Exception as e:
        # 记录异常
        recorder.end_test("build", False, str(e))
        return False


if __name__ == "__main__":
    success = auto_build()
    sys.exit(0 if success else 1) 