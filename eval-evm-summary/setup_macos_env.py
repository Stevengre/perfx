#!/usr/bin/env python3
"""
MacBook Environment Setup Script
Used to set up compiler environment for Apple Silicon and Intel Mac
"""

import os
import platform
import subprocess
from pathlib import Path


def setup_compiler_for_macos():
    """Set appropriate compiler environment variables for macOS system"""
    if platform.system() != "Darwin":
        print("Non-macOS system, skipping compiler setup")
        return
    
    print(f"Detected platform: {platform.system()} {platform.machine()}")
    
    # Prefer llvm@14, which is a verified version
    llvm_paths = [
        "/opt/homebrew/opt/llvm@14",  # Apple Silicon priority
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
            print(f"✓ Set compiler: CC={clang_path}, CXX={clangpp_path}")
            return
    
    print("⚠️  Warning: Homebrew-installed LLVM compiler not found, will use system default compiler")


def setup_apple_silicon_env():
    """Set Apple Silicon special environment variables"""
    if platform.machine() == "arm64" and platform.system() == "Darwin":
        os.environ["APPLE_SILICON"] = "true"
        print("✓ Set Apple Silicon environment variable: APPLE_SILICON=true")
    else:
        print("Non-Apple Silicon platform, skipping special environment variable setup")


def check_homebrew_llvm():
    """Check if Homebrew LLVM is installed"""
    try:
        result = subprocess.run(["brew", "list", "llvm@14"], 
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print("✓ Detected Homebrew LLVM@14")
            return True
        else:
            print("⚠️  Homebrew LLVM@14 not detected")
            return False
    except FileNotFoundError:
        print("⚠️  Homebrew not installed or not in PATH")
        return False


def main():
    """Main function"""
    print("🔧 Starting MacBook environment setup...")
    
    # Set Apple Silicon environment variables
    setup_apple_silicon_env()
    
    # Check Homebrew LLVM
    check_homebrew_llvm()
    
    # Set compiler
    setup_compiler_for_macos()
    
    # Display current environment variables
    print("\n📋 Current environment variables:")
    print(f"  CC: {os.environ.get('CC', 'Not set')}")
    print(f"  CXX: {os.environ.get('CXX', 'Not set')}")
    print(f"  APPLE_SILICON: {os.environ.get('APPLE_SILICON', 'Not set')}")
    
    print("\n✅ MacBook environment setup completed!")


if __name__ == "__main__":
    main() 