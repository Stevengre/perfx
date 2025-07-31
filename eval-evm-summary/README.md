# EVM Summarization Evaluation

EVM 语义摘要化评估工具。

## 📁 目录结构

```
eval-evm-summary/
├── configs/
│   └── evm_summarization.yaml     # 主配置文件
├── scripts/
│   └── setup_macos_env.py         # MacBook 环境设置脚本
└── results/                       # 评估结果输出目录
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入评估目录
cd eval-evm-summary

# 设置 MacBook 环境（如果需要）
python scripts/setup_macos_env.py
```

### 2. 执行评估

```bash
# 从项目根目录执行
cd ..  # 回到 perfx 根目录

# 执行完整的 EVM summarization evaluation
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml

# 只执行特定步骤
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --steps build_kevm

# 只执行前几个步骤
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --steps setup_environment,build_kevm,summarize_evaluation

# 详细输出
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --verbose

# 生成报告
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --generate-report
```

### 3. 查看结果

```bash
# 查看评估结果
ls -la eval-evm-summary/results/

# 查看日志
cat eval-evm-summary/results/logs/setup.log

# 查看摘要化结果
cat eval-evm-summary/results/data/summarization_results.json
```

## 📋 评估步骤

### 1. setup_environment
- 创建必要的目录结构
- 设置 MacBook 环境变量

### 2. build_kevm
- 克隆 evm-semantics 仓库
- 更新子模块
- 安装 poetry 依赖
- 构建 KEVM 语义

### 3. summarize_evaluation
- 获取可用的 opcode 列表
- 执行摘要化评估
- 生成摘要化结果

### 4. category_analysis
- 按类别分析 opcode
- 生成分类统计结果

### 5. prove_summaries_test
- 测试摘要化语义的正确性

### 6. performance_comparison
- 比较纯语义和摘要化语义的性能

## 📊 输出结果

### 文件结构

```
results/
├── backups/                      # 备份文件
├── logs/                         # 日志文件
│   └── setup.log                 # 环境设置日志
├── data/                         # 数据文件
│   ├── opcode_list.txt           # Opcode 列表
│   ├── summarization_results.json # 摘要化结果
│   ├── category_analysis.json    # 分类分析结果
│   ├── prove_summaries_test_results.txt # 测试结果
│   ├── concrete_execution_performance.txt # 性能测试结果
│   └── concrete_execution_summary_performance.txt # 摘要化性能测试结果
└── evaluation_report.html        # 评估报告
```

## 🔧 故障排除

### 常见问题

1. **构建失败**
   ```bash
   # 检查环境变量
   echo $CC
   echo $CXX
   echo $APPLE_SILICON
   
   # 重新设置环境
   python eval-evm-summary/scripts/setup_macos_env.py
   ```

2. **权限问题**
   ```bash
   # 确保有执行权限
   chmod +x eval-evm-summary/scripts/*.py
   ```

### 调试模式

```bash
# 启用详细输出
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --verbose

# 只执行单个步骤进行调试
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --steps setup_environment --verbose
```

## 📄 许可证

本项目遵循与主项目相同的许可证。 