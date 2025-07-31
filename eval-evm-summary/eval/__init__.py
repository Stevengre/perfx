"""
EVM Summarization Evaluation Package

This package provides utilities for building and testing KEVM semantics.
"""

from pathlib import Path

# 全局配置
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
EVM_SEMANTICS_DIR = PROJECT_ROOT / "evm-semantics"
KEVM_PYK_DIR = EVM_SEMANTICS_DIR / "kevm-pyk"
INTERPRETER_FILE = KEVM_PYK_DIR / "src" / "kevm_pyk" / "interpreter.py"

# 导出主要配置
__all__ = [
    'PROJECT_ROOT',
    'EVM_SEMANTICS_DIR', 
    'KEVM_PYK_DIR',
    'INTERPRETER_FILE'
]
