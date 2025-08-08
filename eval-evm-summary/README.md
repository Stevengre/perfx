# EVM Summarization Evaluation

EVM Semantics Summarization Evaluation Tool.

## 📁 Directory Structure

```
eval-evm-summary/
├── configs/
│   └── evm_summarization.yaml     # Main configuration file
├── scripts/
│   └── setup_macos_env.py         # MacBook environment setup script
└── results/                       # Evaluation results output directory
```

## 🚀 快速开始

### 1. Environment Preparation

```bash
# Enter evaluation directory
cd eval-evm-summary

# Set up MacBook environment (if needed)
python scripts/setup_macos_env.py
```

### 2. Execute Evaluation

```bash
# Execute from project root directory
cd ..  # Return to perfx root directory

# Execute complete EVM summarization evaluation
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml

# Execute only specific steps
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --steps build_kevm

# Execute only first few steps
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --steps setup_environment,build_kevm,summarize_evaluation

# Verbose output
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --verbose

# Generate report
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --generate-report
```

### 3. View Results

```bash
# View evaluation results
ls -la eval-evm-summary/results/

# View logs
cat eval-evm-summary/results/logs/setup.log

# View summarization results
cat eval-evm-summary/results/data/summarization_results.json
```

## 📋 Evaluation Steps

### 1. setup_environment
- Create necessary directory structure
- Set MacBook environment variables

### 2. build_kevm
- Clone evm-semantics repository
- Update submodules
- Install poetry dependencies
- Build KEVM semantics

### 3. summarize_evaluation
- Get available opcode list
- Execute summarization evaluation
- Generate summarization results

### 4. category_analysis
- Analyze opcodes by category
- Generate category statistics

### 5. prove_summaries_test
- Test correctness of summarization semantics

### 6. performance_comparison
- Compare performance of pure and summarized semantics

## 📊 Output Results

### File Structure

```
results/
├── backups/                      # Backup files
├── logs/                         # Log files
│   └── setup.log                 # Environment setup log
├── data/                         # Data files
│   ├── opcode_list.txt           # Opcode list
│   ├── summarization_results.json # Summarization results
│   ├── category_analysis.json    # Category analysis results
│   ├── prove_summaries_test_results.txt # Test results
│   ├── concrete_execution_performance.txt # Performance test results
│   └── concrete_execution_summary_performance.txt # Summarized performance test results
└── evaluation_report.html        # Evaluation report
```

## 🔧 Troubleshooting

### Common Issues

1. **Build Failure**
   ```bash
   # Check environment variables
   echo $CC
   echo $CXX
   echo $APPLE_SILICON
   
   # Reset environment
   python eval-evm-summary/scripts/setup_macos_env.py
   ```

2. **Permission Issues**
   ```bash
   # Ensure execution permissions
   chmod +x eval-evm-summary/scripts/*.py
   ```

### Debug Mode

```bash
# Enable verbose output
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --verbose

# Execute only single step for debugging
uv run perfx run -c eval-evm-summary/configs/evm_summarization.yaml --steps setup_environment --verbose
```

## 📄 License

This project follows the same license as the main project. 