# Perfx 性能对比功能使用指南

## 概述

Perfx 现在支持直接比较两个JSON数据文件，无需预处理步骤。通过详细的YAML配置，可以精确控制数据提取、过滤和图表生成过程。

## 功能特点

1. **直接数据对比**：无需预处理，直接比较两个JSON文件
2. **详细字段配置**：可配置数据路径、字段名、状态过滤等
3. **灵活过滤选项**：支持按状态过滤、错误过滤、成功测试过滤等
4. **学术级质量**：生成适合论文发表的高质量图表
5. **声明式配置**：通过YAML配置文件定义对比需求

## 使用方法

### 1. 数据准备

确保您有两个具有相同结构的JSON文件，例如：
- `results/data/pure_concrete_performance.json`
- `results/data/summary_concrete_performance.json`

这些文件应该包含 `test_results` 数组，每个测试结果包含：
```json
{
  "test_results": [
    {
      "test_id": "src/tests/integration/test_conformance.py::test_vm[vmArithmeticTest/mulmod.json]",
      "status": "PASSED",
      "duration": 0.61,
      "error_message": null
    }
  ]
}
```

### 2. YAML配置

在 `evm_summarization.yaml` 中添加对比图表配置：

```yaml
visualization_config:
  charts:
    - name: "concrete_performance_comparison"
      title: "Concrete Execution Performance Comparison"
      type: "performance_comparison"
      input_files:
        - "../data/pure_concrete_performance.json"
        - "../data/summary_concrete_performance.json"
      output_file: "charts/concrete_performance_comparison.pdf"
      # 数据提取配置
      data_config:
        test_results_path: "test_results"
        test_id_field: "test_id"
        duration_field: "duration"
        status_field: "status"
        error_field: "error_message"
      # 过滤配置
      filters:
        include_statuses: ["PASSED", "FAILED"]
        exclude_statuses: ["SKIPPED"]
        only_successful: false
        ignore_errors: false
      # 图表配置
      chart_config:
        dataset1_label: "Pure"
        dataset2_label: "Summary"
```

### 3. 生成图表

运行perfx可视化步骤：

```bash
uv run perfx run eval-evm-summary/evm_summarization.yaml -s visualization
```

## 配置参数说明

### 必需参数

- `name`: 图表名称（用于标识）
- `title`: 图表标题
- `type`: 图表类型（`performance_comparison`）
- `input_files`: 输入文件列表（必须是2个文件）
- `output_file`: 输出文件路径

### 数据提取配置 (data_config)

- `test_results_path`: 测试结果列表的路径（默认：`"test_results"`）
- `test_id_field`: 测试ID字段名（默认：`"test_id"`）
- `duration_field`: 持续时间字段名（默认：`"duration"`）
- `status_field`: 状态字段名（默认：`"status"`）
- `error_field`: 错误信息字段名（默认：`"error_message"`）

### 过滤配置 (filters)

- `include_statuses`: 要包含的状态列表（默认：`["PASSED", "FAILED"]`）
- `exclude_statuses`: 要排除的状态列表（默认：`["SKIPPED"]`）
- `only_successful`: 是否只包含成功的测试（默认：`false`）
- `ignore_errors`: 是否忽略有错误信息的测试（默认：`false`）

### 图表配置 (chart_config)

- `dataset1_label`: 第一个数据集的标签（默认：`"Dataset 1"`）
- `dataset2_label`: 第二个数据集的标签（默认：`"Dataset 2"`）

## 过滤示例

### 1. 包含所有非跳过测试
```yaml
filters:
  include_statuses: ["PASSED", "FAILED"]
  exclude_statuses: ["SKIPPED"]
  only_successful: false
  ignore_errors: false
```

### 2. 只包含成功测试
```yaml
filters:
  include_statuses: ["PASSED"]
  exclude_statuses: ["SKIPPED", "FAILED"]
  only_successful: true
  ignore_errors: true
```

### 3. 包含失败测试但忽略错误
```yaml
filters:
  include_statuses: ["PASSED", "FAILED"]
  exclude_statuses: ["SKIPPED"]
  only_successful: false
  ignore_errors: true
```

## 生成的图表

对比图表包含两个子图：

1. **左图：执行时间对比**
   - 柱状图显示两个模式的执行时间
   - 便于直观比较性能差异

2. **右图：加速比分布**
   - 直方图显示加速比的分布情况
   - 包含平均加速比标记

## 输出文件

生成的图表文件：
- `results/analysis/charts/concrete_performance_comparison.pdf` (PDF格式)
- `results/analysis/charts/concrete_performance_comparison.png` (PNG格式)

## 完整配置示例

```yaml
visualization_config:
  data_directory: "results/processed"
  output_directory: "results/analysis"
  
  charts:
    - name: "concrete_performance_comparison"
      title: "Concrete Execution Performance Comparison"
      type: "performance_comparison"
      input_files:
        - "../data/pure_concrete_performance.json"
        - "../data/summary_concrete_performance.json"
      output_file: "charts/concrete_performance_comparison.pdf"
      data_config:
        test_results_path: "test_results"
        test_id_field: "test_id"
        duration_field: "duration"
        status_field: "status"
        error_field: "error_message"
      filters:
        include_statuses: ["PASSED", "FAILED"]
        exclude_statuses: ["SKIPPED"]
        only_successful: false
        ignore_errors: false
      chart_config:
        dataset1_label: "Pure"
        dataset2_label: "Summary"
```

## 路径配置说明

- `data_directory`: 基础数据目录（如 `"results/processed"`）
- `input_files`: 相对于基础数据目录的路径
  - 如果文件在 `results/data/` 目录，使用 `"../data/filename.json"`
  - 如果文件在 `results/processed/` 目录，使用 `"filename.json"`

## 注意事项

1. **文件格式**：确保两个输入文件具有相同的结构
2. **测试匹配**：对比的测试用例应该有相同的test_id
3. **数据质量**：建议使用相同环境下的测试结果进行对比
4. **文件路径**：确保所有文件路径正确且文件存在
5. **过滤逻辑**：过滤条件按顺序应用，确保配置符合预期

## 故障排除

### 常见问题

1. **"Input file not found"**
   - 检查文件路径是否正确
   - 确保路径相对于`data_directory`正确

2. **"No valid performance data found after filtering"**
   - 检查过滤条件是否过于严格
   - 验证JSON文件中的状态值
   - 确认字段名配置正确

3. **"No common test cases found"**
   - 检查两个JSON文件中的test_id是否匹配
   - 确保数据格式正确

### 调试方法

- 查看调试输出，了解过滤后的测试数量
- 检查生成的日志文件
- 验证JSON文件结构
- 确认YAML配置格式正确 