# Perfx 性能分析完整指南

## 概述

Perfx 现在支持完整的性能分析功能，可以生成四种不同类型的图表来分析summary相对于pure的性能提升状况。这些图表提供了从宏观到微观的全面性能分析视角。

## 四种性能分析图表

### 1. 总体性能对比图 (`performance_comparison`)
- **文件名**: `concrete_performance_comparison.pdf/png`
- **内容**: 左图显示总执行时间对比，右图显示加速因子
- **用途**: 提供整体性能提升的宏观视图

### 2. 性能分布图 (`performance_distribution`)
- **文件名**: `concrete_performance_distribution.pdf/png`
- **内容**: 左图显示加速因子分布，右图显示性能提升百分比分布
- **用途**: 分析性能提升的分布特征和统计信息

### 3. 性能散点图 (`performance_scatter`)
- **文件名**: `concrete_performance_scatter.pdf/png`
- **内容**: 散点图显示每个测试用例的原始时间vs摘要化时间
- **用途**: 直观显示性能改进的模式和趋势

### 4. 测试用例改进图 (`test_case_improvement`)
- **文件名**: `concrete_test_case_improvement.pdf/png`
- **内容**: 水平条形图显示前N个性能改进最大的测试用例
- **用途**: 识别性能改进最显著的特定测试用例

## 数据类型支持

### Concrete Execution 性能数据
- **数据文件**: `pure_concrete_performance.json` 和 `summary_concrete_performance.json`
- **图表类型**: 支持所有四种图表类型
- **特点**: 包含大量测试用例，适合全面的性能分析

### Symbolic Execution 性能数据
- **数据文件**: 多组symbolic性能数据文件
- **图表类型**: 支持散点图和测试用例改进图
- **特点**: 包含不同测试套件的symbolic执行性能数据

#### Symbolic数据文件列表：
1. **Booster Dev**: `pure_symbolic_prove_rules_booster_dev.json` 和 `summary_symbolic_prove_rules_booster_dev.json`
2. **Booster**: `pure_symbolic_prove_rules_booster.json` 和 `summary_symbolic_prove_rules_booster.json`
3. **Summaries**: `pure_symbolic_prove_summaries.json` 和 `summary_symbolic_prove_summaries.json`
4. **DSS**: `pure_symbolic_prove_dss.json` 和 `summary_symbolic_prove_dss.json`

#### 生成的图表文件：
- **Booster Dev**: `symbolic_performance_scatter.pdf/png`, `symbolic_test_case_improvement.pdf/png`
- **Booster**: `symbolic_booster_performance_scatter.pdf/png`, `symbolic_booster_test_case_improvement.pdf/png`
- **Summaries**: `symbolic_summaries_performance_scatter.pdf/png`, `symbolic_summaries_test_case_improvement.pdf/png`
- **DSS**: `symbolic_dss_performance_scatter.pdf/png`, `symbolic_dss_test_case_improvement.pdf/png`

## 配置方案

### 完整的YAML配置

```yaml
visualization_config:
  data_directory: "results/processed"
  output_directory: "results/analysis"
  
  charts:
    # 1. 总体性能对比图
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
    
    # 2. 性能分布图
    - name: "concrete_performance_distribution"
      title: "Concrete Execution Performance Distribution"
      type: "performance_distribution"
      input_files:
        - "../data/pure_concrete_performance.json"
        - "../data/summary_concrete_performance.json"
      output_file: "charts/concrete_performance_distribution.pdf"
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
    
    # 3. 性能散点图
    - name: "concrete_performance_scatter"
      title: "Performance Comparison: Original vs Summarized Semantics"
      type: "performance_scatter"
      input_files:
        - "../data/pure_concrete_performance.json"
        - "../data/summary_concrete_performance.json"
      output_file: "charts/concrete_performance_scatter.pdf"
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
        dataset1_label: "Original"
        dataset2_label: "Summarized"
    
    # 4. 测试用例改进图
    - name: "concrete_test_case_improvement"
      title: "Top 20 Test Cases by Performance Improvement"
      type: "test_case_improvement"
      input_files:
        - "../data/pure_concrete_performance.json"
        - "../data/summary_concrete_performance.json"
      output_file: "charts/concrete_test_case_improvement.pdf"
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
        top_n: 20
```

### Symbolic Execution 性能数据配置

#### Booster Dev 数据配置
```yaml
    # Symbolic性能散点图（booster_dev）
    - name: "symbolic_performance_scatter"
      title: "Symbolic Execution Performance Comparison: Original vs Summarized Semantics"
      type: "performance_scatter"
      input_files:
        - "../data/pure_symbolic_prove_rules_booster_dev.json"
        - "../data/summary_symbolic_prove_rules_booster_dev.json"
      output_file: "charts/symbolic_performance_scatter.pdf"
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

    # Symbolic测试用例改进图（booster_dev）
    - name: "symbolic_test_case_improvement"
      title: "Top Symbolic Test Cases by Performance Improvement"
      type: "test_case_improvement"
      input_files:
        - "../data/pure_symbolic_prove_rules_booster_dev.json"
        - "../data/summary_symbolic_prove_rules_booster_dev.json"
      output_file: "charts/symbolic_test_case_improvement.pdf"
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
        top_n: 14
```

#### Booster 数据配置
```yaml
    # Symbolic性能散点图（booster）
    - name: "symbolic_booster_performance_scatter"
      title: "Symbolic Execution Performance Comparison (Booster): Original vs Summarized Semantics"
      type: "performance_scatter"
      input_files:
        - "../data/pure_symbolic_prove_rules_booster.json"
        - "../data/summary_symbolic_prove_rules_booster.json"
      output_file: "charts/symbolic_booster_performance_scatter.pdf"
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

    # Symbolic测试用例改进图（booster）
    - name: "symbolic_booster_test_case_improvement"
      title: "Top Symbolic Test Cases by Performance Improvement (Booster)"
      type: "test_case_improvement"
      input_files:
        - "../data/pure_symbolic_prove_rules_booster.json"
        - "../data/summary_symbolic_prove_rules_booster.json"
      output_file: "charts/symbolic_booster_test_case_improvement.pdf"
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
        top_n: 20
```

#### Summaries 数据配置
```yaml
    # Symbolic性能散点图（summaries）
    - name: "symbolic_summaries_performance_scatter"
      title: "Symbolic Execution Performance Comparison (Summaries): Original vs Summarized Semantics"
      type: "performance_scatter"
      input_files:
        - "../data/pure_symbolic_prove_summaries.json"
        - "../data/summary_symbolic_prove_summaries.json"
      output_file: "charts/symbolic_summaries_performance_scatter.pdf"
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

    # Symbolic测试用例改进图（summaries）
    - name: "symbolic_summaries_test_case_improvement"
      title: "Top Symbolic Test Cases by Performance Improvement (Summaries)"
      type: "test_case_improvement"
      input_files:
        - "../data/pure_symbolic_prove_summaries.json"
        - "../data/summary_symbolic_prove_summaries.json"
      output_file: "charts/symbolic_summaries_test_case_improvement.pdf"
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
        top_n: 20
```

#### DSS 数据配置
```yaml
    # Symbolic性能散点图（dss）
    - name: "symbolic_dss_performance_scatter"
      title: "Symbolic Execution Performance Comparison (DSS): Original vs Summarized Semantics"
      type: "performance_scatter"
      input_files:
        - "../data/pure_symbolic_prove_dss.json"
        - "../data/summary_symbolic_prove_dss.json"
      output_file: "charts/symbolic_dss_performance_scatter.pdf"
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

    # Symbolic测试用例改进图（dss）
    - name: "symbolic_dss_test_case_improvement"
      title: "Top Symbolic Test Cases by Performance Improvement (DSS)"
      type: "test_case_improvement"
      input_files:
        - "../data/pure_symbolic_prove_dss.json"
        - "../data/summary_symbolic_prove_dss.json"
      output_file: "charts/symbolic_dss_test_case_improvement.pdf"
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
        top_n: 20
```

## 使用方法

### 1. 准备数据
确保您有两个具有相同结构的JSON文件：
- `results/data/pure_concrete_performance.json`
- `results/data/summary_concrete_performance.json`

### 2. 配置YAML
将上述配置添加到 `eval-evm-summary/evm_summarization.yaml` 文件中。

### 3. 生成图表
运行perfx可视化步骤：
```bash
uv run perfx run eval-evm-summary/evm_summarization.yaml -s visualization
```

### 4. 查看结果
生成的图表文件将保存在 `results/analysis/charts/` 目录中。

## 图表解读指南

### 总体性能对比图
- **左图**: 显示Pure和Summary模式的总执行时间对比
- **右图**: 显示整体加速因子（如1.04x表示4%的性能提升）
- **解读**: 提供整体性能改进的宏观视图

### 性能分布图
- **左图**: 加速因子分布直方图
  - 峰值在1.0附近表示大部分测试性能相似
  - 右侧峰值表示有显著性能提升的测试
- **右图**: 性能提升百分比分布
  - 正值表示性能提升
  - 负值表示性能下降
- **解读**: 了解性能改进的分布特征

### 性能散点图
- **散点**: 每个点代表一个测试用例
- **对角线**: y=x线表示无性能改进
- **对角线下方**: 表示性能提升
- **对角线上方**: 表示性能下降
- **解读**: 直观显示性能改进的模式

### 测试用例改进图
- **水平条形**: 显示前N个性能改进最大的测试用例
- **条形长度**: 表示加速因子大小
- **测试名称**: 显示具体的测试用例
- **解读**: 识别性能改进最显著的特定测试

## Symbolic Execution 性能图表解读

### Symbolic性能散点图
- **散点**: 每个点代表一个symbolic测试用例
- **对角线**: y=x线表示无性能改进
- **对角线下方**: 表示性能提升
- **对角线上方**: 表示性能下降
- **解读**: 直观显示symbolic执行性能改进的模式

### Symbolic测试用例改进图
- **水平条形**: 显示前14个symbolic测试用例的性能改进
- **条形长度**: 表示加速因子大小
- **测试名称**: 显示具体的symbolic测试用例
- **解读**: 识别symbolic执行中性能改进最显著的特定测试

## 配置参数说明

### 数据提取配置 (data_config)
- `test_results_path`: 测试结果列表的路径
- `test_id_field`: 测试ID字段名
- `duration_field`: 持续时间字段名
- `status_field`: 状态字段名
- `error_field`: 错误信息字段名

### 过滤配置 (filters)
- `include_statuses`: 要包含的状态列表
- `exclude_statuses`: 要排除的状态列表
- `only_successful`: 是否只包含成功的测试
- `ignore_errors`: 是否忽略有错误信息的测试

### 图表配置 (chart_config)
- `dataset1_label`: 第一个数据集的标签
- `dataset2_label`: 第二个数据集的标签
- `top_n`: 显示前N个测试用例（仅适用于test_case_improvement）

## 性能指标计算

### 加速因子 (Speedup Factor)
```
加速因子 = Pure执行时间 / Summary执行时间
```
- 加速因子 > 1: 性能提升
- 加速因子 = 1: 无变化
- 加速因子 < 1: 性能下降

### 性能提升百分比
```
性能提升百分比 = (Pure执行时间 - Summary执行时间) / Pure执行时间 × 100%
```
- 正值: 性能提升
- 负值: 性能下降

## 故障排除

### 常见问题
1. **"No common test cases found"**
   - 检查两个JSON文件中的test_id是否匹配
   - 确保数据格式正确

2. **"No valid performance data found after filtering"**
   - 检查过滤条件是否过于严格
   - 验证JSON文件中的状态值

3. **图表生成失败**
   - 检查matplotlib是否正确安装
   - 验证输出目录权限

### 调试方法
- 查看生成的日志文件
- 验证JSON文件结构
- 确认YAML配置格式正确

## 扩展应用

### 其他数据类型
这个配置方案可以应用于任何具有相同结构的性能数据：
- Symbolic execution性能数据
- 不同优化策略的对比
- 不同硬件平台的性能对比

### 自定义分析
通过修改配置参数，可以实现：
- 只分析成功测试的性能
- 排除特定类型的测试
- 自定义图表标题和标签
- 调整显示的测试用例数量 