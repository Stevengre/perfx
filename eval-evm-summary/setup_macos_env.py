#!/usr/bin/env python3
"""
MacBook 环境设置脚本
用于设置 Apple Silicon 和 Intel Mac 的编译器环境
"""

import os
import platform
import subprocess
from pathlib import Path


def setup_compiler_for_macos():
    """为 macOS 系统设置合适的编译器环境变量"""
    if platform.system() != "Darwin":
        print("非 macOS 系统，跳过编译器设置")
        return
    
    print(f"检测到平台: {platform.system()} {platform.machine()}")
    
    # 优先使用 llvm@14，这是经过验证的版本
    llvm_paths = [
        "/opt/homebrew/opt/llvm@14",  # Apple Silicon 优先
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
            print(f"✓ 设置编译器: CC={clang_path}, CXX={clangpp_path}")
            return
    
    print("⚠️  警告: 未找到 Homebrew 安装的 LLVM 编译器，将使用系统默认编译器")


def setup_apple_silicon_env():
    """设置 Apple Silicon 特殊环境变量"""
    if platform.machine() == "arm64" and platform.system() == "Darwin":
        os.environ["APPLE_SILICON"] = "true"
        print("✓ 设置 Apple Silicon 环境变量: APPLE_SILICON=true")
    else:
        print("非 Apple Silicon 平台，跳过特殊环境变量设置")


def check_homebrew_llvm():
    """检查 Homebrew LLVM 是否已安装"""
    try:
        result = subprocess.run(["brew", "list", "llvm@14"], 
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print("✓ 检测到 Homebrew LLVM@14")
            return True
        else:
            print("⚠️  未检测到 Homebrew LLVM@14")
            return False
    except FileNotFoundError:
        print("⚠️  Homebrew 未安装或不在 PATH 中")
        return False


def main():
    """主函数"""
    print("🔧 开始设置 MacBook 环境...")
    
    # 设置 Apple Silicon 环境变量
    setup_apple_silicon_env()
    
    # 检查 Homebrew LLVM
    check_homebrew_llvm()
    
    # 设置编译器
    setup_compiler_for_macos()
    
    # 显示当前环境变量
    print("\n📋 当前环境变量:")
    print(f"  CC: {os.environ.get('CC', '未设置')}")
    print(f"  CXX: {os.environ.get('CXX', '未设置')}")
    print(f"  APPLE_SILICON: {os.environ.get('APPLE_SILICON', '未设置')}")
    
    print("\n✅ MacBook 环境设置完成！")


if __name__ == "__main__":
    main() 