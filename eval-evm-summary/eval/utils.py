"""
Utility functions for EVM summarization evaluation.

This module contains common utilities used across different evaluation scripts.
"""

import os
import subprocess
import platform
import signal
import time
from typing import Optional
from pathlib import Path


def setup_compiler_for_macos() -> None:
    """
    为macOS系统设置合适的编译器环境变量
    优先使用Homebrew安装的LLVM编译器
    """
    if platform.system() != "Darwin":
        return
    
    # 优先使用llvm@14，这是经过验证的版本
    llvm_paths = [
        "/opt/homebrew/opt/llvm@14",  # Apple Silicon优先
        "/usr/local/opt/llvm@14",     # Intel Mac
        "/opt/homebrew/opt/llvm@15", 
        "/opt/homebrew/opt/llvm@16",
        "/opt/homebrew/opt/llvm@17",
        "/usr/local/opt/llvm@15",
        "/usr/local/opt/llvm@16",
        "/usr/local/opt/llvm@17",
    ]
    
    for llvm_path in llvm_paths:
        clang_path = os.path.join(llvm_path, "bin", "clang")
        clangpp_path = os.path.join(llvm_path, "bin", "clang++")
        
        if os.path.exists(clang_path) and os.path.exists(clangpp_path):
            os.environ["CC"] = clang_path
            os.environ["CXX"] = clangpp_path
            print(f"设置编译器: CC={clang_path}, CXX={clangpp_path}")
            return
    
    print("警告: 未找到Homebrew安装的LLVM编译器，将使用系统默认编译器")


def run_command(cmd: list, description: str, cwd: Optional[Path] = None, record: bool = True) -> bool:
    """
    运行命令并处理错误
    
    Args:
        cmd: 要执行的命令列表
        description: 命令描述
        cwd: 工作目录，如果为None则使用当前目录
        record: 是否记录命令到recorder
        
    Returns:
        bool: 命令执行是否成功
    """
    if record:
        from .evaluation_recorder import recorder
    
    start_time = time.time()
    command_str = ' '.join(cmd)
    cwd_str = str(cwd) if cwd else None
    
    print(f"\n=== {description} ===")
    print(f"执行命令: {command_str}")
    if cwd:
        print(f"工作目录: {cwd}")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=cwd, capture_output=True, text=True)
        duration = time.time() - start_time
        print(f"✓ {description} 完成")
        
        if record:
            recorder.add_command(
                command=command_str,
                cwd=cwd_str,
                output=result.stdout,
                error=result.stderr,
                success=True,
                duration=duration
            )
        
        return True
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"✗ {description} 失败: {e}")
        
        if record:
            recorder.add_command(
                command=command_str,
                cwd=cwd_str,
                output=e.stdout,
                error=e.stderr,
                success=False,
                duration=duration
            )
        
        return False


def run_command_with_timeout(cmd: list, description: str, timeout_seconds: int, cwd: Optional[Path] = None, record: bool = True) -> bool:
    """
    运行命令并设置超时时间
    
    Args:
        cmd: 要执行的命令列表
        description: 命令描述
        timeout_seconds: 超时时间（秒）
        cwd: 工作目录，如果为None则使用当前目录
        record: 是否记录命令到recorder
        
    Returns:
        bool: 命令执行是否成功
    """
    if record:
        from .evaluation_recorder import recorder
    
    start_time = time.time()
    command_str = ' '.join(cmd)
    cwd_str = str(cwd) if cwd else None
    
    print(f"\n=== {description} (超时: {timeout_seconds}秒) ===")
    print(f"执行命令: {command_str}")
    if cwd:
        print(f"工作目录: {cwd}")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=cwd, timeout=timeout_seconds, capture_output=True, text=True)
        duration = time.time() - start_time
        print(f"✓ {description} 完成")
        
        if record:
            recorder.add_command(
                command=command_str,
                cwd=cwd_str,
                output=result.stdout,
                error=result.stderr,
                success=True,
                duration=duration
            )
        
        return True
    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        print(f"✗ {description} 超时 ({timeout_seconds}秒)")
        
        if record:
            recorder.add_command(
                command=command_str,
                cwd=cwd_str,
                output="",
                error=f"Timeout after {timeout_seconds} seconds",
                success=False,
                duration=duration
            )
        
        return False
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"✗ {description} 失败: {e}")
        
        if record:
            recorder.add_command(
                command=command_str,
                cwd=cwd_str,
                output=e.stdout,
                error=e.stderr,
                success=False,
                duration=duration
            )
        
        return False


def check_directories_and_files(*paths: Path, description: str = "路径") -> bool:
    """
    检查目录和文件是否存在
    
    Args:
        *paths: 要检查的路径列表
        description: 路径描述，用于错误信息
        
    Returns:
        bool: 所有路径都存在
    """
    for path in paths:
        if not path.exists():
            print(f"错误: {description}不存在: {path}")
            return False
    return True


def print_project_info() -> None:
    """
    打印项目信息
    """
    from . import PROJECT_ROOT, EVM_SEMANTICS_DIR, KEVM_PYK_DIR
    
    print("项目信息:")
    print(f"  项目根目录: {PROJECT_ROOT}")
    print(f"  EVM语义目录: {EVM_SEMANTICS_DIR}")
    print(f"  KEVM-PYK目录: {KEVM_PYK_DIR}")
    print(f"  目录存在性检查:")
    print(f"    项目根目录: {'✓' if PROJECT_ROOT.exists() else '✗'}")
    print(f"    EVM语义目录: {'✓' if EVM_SEMANTICS_DIR.exists() else '✗'}")
    print(f"    KEVM-PYK目录: {'✓' if KEVM_PYK_DIR.exists() else '✗'}")


# 导出主要函数
__all__ = [
    'setup_compiler_for_macos',
    'run_command',
    'run_command_with_timeout', 
    'check_directories_and_files',
    'print_project_info'
]