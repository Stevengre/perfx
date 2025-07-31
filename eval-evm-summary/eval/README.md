# EVM Summarization Evaluation Framework

这个框架用于评估EVM语义摘要化的有效性和效率。

## 快速开始

### 执行所有评估步骤
```bash
python -m eval
```

### 查看帮助信息
```bash
python -m eval --help
```

## 命令行参数

### 主要步骤选择

#### 只执行单个步骤
- `--build-only`: 只执行构建步骤（STEP 1和STEP 3）
- `--summarize-only`: 只执行summarize评估（STEP 2）
- `--prove-only`: 只执行prove summaries测试（STEP 4）
- `--concrete-only`: 只执行concrete execution性能评估（STEP 5）
- `--symbolic-only`: 只执行symbolic execution性能评估（STEP 6）

#### 组合执行多个步骤
- `--build`: 执行构建步骤
- `--summarize`: 执行summarize评估
- `--prove`: 执行prove summaries测试
- `--concrete`: 执行concrete execution性能评估
- `--symbolic`: 执行symbolic execution性能评估

#### 跳过特定步骤
- `--skip-build`: 跳过构建步骤
- `--skip-summarize`: 跳过summarize评估
- `--skip-prove`: 跳过prove summaries测试
- `--skip-concrete`: 跳过concrete execution性能评估
- `--skip-symbolic`: 跳过symbolic execution性能评估

### 其他选项

- `--skip-opcodes OPCODES`: 指定要跳过的opcode列表
  - 默认跳过: BASEFEE, CALL, CALLCODE, CALLVALUE, CREATE, CREATE2, DELEGATECALL, EXTCODECOPY, EXTCODEHASH, EXTCODESIZE, JUMP, JUMPI, MUL, SELFDESTRUCT, STATICCALL
- `--no-save`: 不保存结果到文件
- `--verbose, -v`: 显示详细输出

## 使用示例

### 1. 只进行构建
```bash
python -m eval --build-only
```

### 2. 只进行summarize评估
```bash
python -m eval --summarize-only
```

### 3. 只进行prove测试
```bash
python -m eval --prove-only
```

### 4. 只进行concrete execution性能评估
```bash
python -m eval --concrete-only
```

### 5. 只进行symbolic execution性能评估
```bash
python -m eval --symbolic-only
```

### 6. 组合执行多个步骤
```bash
# 构建 + summarize评估
python -m eval --build --summarize

# 构建 + prove测试 + concrete execution性能评估
python -m eval --build --prove --concrete

# 构建 + prove测试 + symbolic execution性能评估
python -m eval --build --prove --symbolic

# 构建 + 所有性能评估
python -m eval --build --concrete --symbolic
```

### 7. 跳过特定步骤
```bash
# 跳过构建，直接进行其他步骤
python -m eval --skip-build

# 跳过summarize评估和concrete execution性能评估
python -m eval --skip-summarize --skip-concrete

# 跳过symbolic execution性能评估
python -m eval --skip-symbolic
```

### 8. 自定义跳过的opcode
```bash
# 只跳过CALL和CREATE
python -m eval --skip-opcodes CALL CREATE

# 不跳过任何opcode
python -m eval --skip-opcodes
```

### 9. 详细输出模式
```bash
python -m eval --verbose
```

### 10. 不保存结果
```bash
python -m eval --no-save
```

## 评估步骤说明

1. **第一次构建 (STEP 1)**: 在项目根目录中构建KEVM语义
2. **Summarize评估 (STEP 2)**: 评估语义摘要化的有效性
3. **第二次构建 (STEP 3)**: 在evm-semantics目录中重新构建，确保conformance testing环境干净
4. **Prove测试 (STEP 4)**: 测试摘要化语义的正确性
5. **Concrete execution性能评估 (STEP 5)**: 比较原始语义和摘要化语义的concrete execution性能差异
6. **Symbolic execution性能评估 (STEP 6)**: 比较原始语义和摘要化语义的symbolic execution性能差异

## 注意事项

- 某些步骤之间存在依赖关系，例如prove测试和性能评估需要先完成构建
- 如果跳过构建步骤，程序会假设构建已经成功完成
- 使用`--verbose`参数可以查看将要执行的步骤和跳过的opcode
- 结果会自动保存到`evaluation_results/`目录中（除非使用`--no-save`） 