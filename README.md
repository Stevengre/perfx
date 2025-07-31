# Perfx - Configurable Performance Evaluation Framework

Perfx is a configurable performance evaluation framework that allows you to define evaluation workflows through YAML configuration files. It provides a flexible and extensible way to run commands, parse results, and generate visualizations and reports.

## Features

- **Configurable Workflows**: Define evaluation steps through YAML configuration
- **Command Execution**: Run shell commands with timeout, retry, and dependency management
- **Result Parsing**: Plugin-based parsing system for different output formats
- **Visualization**: Generate charts and tables in multiple formats
- **Reporting**: Create comprehensive reports in HTML, Markdown, and other formats
- **Modern CLI**: Rich command-line interface with progress indicators

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd perfx

# Install with uv
uv sync
```

## Quick Start

### 1. Create a Configuration

```bash
# Create a basic configuration
uv run perfx init --output my_evaluation.yaml

# Or use a template
uv run perfx init --template evm_evaluation --output evm_config.yaml
```

### 2. Run Evaluation

```bash
# Run with configuration
uv run perfx run --config my_evaluation.yaml

# Run specific steps
uv run perfx run --config my_evaluation.yaml --steps build,test

# Verbose output
uv run perfx run --config my_evaluation.yaml --verbose
```

### 3. Generate Reports

```bash
# Process existing data and generate reports
uv run perfx run --config my_evaluation.yaml --process-only

# Generate report after execution
uv run perfx run --config my_evaluation.yaml --generate-report
```

## Configuration Format

### Basic Structure

```yaml
name: "My Evaluation"
version: "1.0.0"
description: "Description of the evaluation"

global:
  working_directory: "."
  output_directory: "results"
  timeout: 3600
  environment:
    MY_VAR: "value"

steps:
  - name: "build"
    description: "Build the project"
    enabled: true
    commands:
      - command: "make build"
        cwd: "."
        timeout: 1800
        expected_exit_code: 0
    parser: "build_parser"

parsers:
  build_parser:
    type: "simple"
    success_patterns: ["Build completed"]
    error_patterns: ["ERROR", "FAILED"]

visualizations:
  - name: "performance_chart"
    type: "line_chart"
    data_source: "build"
    x_axis: "test_name"
    y_axis: "duration"
    title: "Performance Chart"

reporting:
  template: "basic"
  output_formats: ["html", "markdown"]
```

### Step Configuration

Each step can have:

- **name**: Unique identifier for the step
- **description**: Human-readable description
- **enabled**: Whether the step should run (default: true)
- **depends_on**: List of step names that must complete first
- **commands**: List of commands to execute
- **parser**: Parser to use for result analysis

### Command Configuration

Each command can have:

- **command**: The shell command to execute
- **cwd**: Working directory (default: global working_directory)
- **timeout**: Command timeout in seconds
- **expected_exit_code**: Expected exit code (default: 0)
- **environment**: Environment variables for this command
- **continue_on_failure**: Whether to continue if command fails

### Parser Types

- **simple**: Basic success/failure detection using patterns
- **pytest**: Parse pytest output for test results
- **json**: Parse JSON output

### Visualization Types

- **line_chart**: Line chart visualization
- **bar_chart**: Bar chart visualization
- **scatter_plot**: Scatter plot visualization
- **table**: Tabular data output

## CLI Commands

### `run`
Run evaluation based on configuration.

```bash
uv run perfx run --config config.yaml [OPTIONS]
```

Options:
- `--steps`: Comma-separated list of steps to run
- `--process-only`: Only process existing data
- `--generate-report`: Generate report after execution
- `--verbose`: Verbose output
- `--output-dir`: Output directory

### `init`
Initialize a new configuration file.

```bash
uv run perfx init [OPTIONS]
```

Options:
- `--template`: Template to use
- `--output`: Output file name

### `list-templates`
List available configuration templates.

```bash
uv run perfx list-templates
```

### `validate`
Validate configuration file.

```bash
uv run perfx validate --config config.yaml
```

### `info`
Show configuration information.

```bash
uv run perfx info --config config.yaml
```

## Examples

### Basic Example

```yaml
name: "Basic Test"
steps:
  - name: "hello"
    commands:
      - command: "echo 'Hello, World!'"
    parser: "simple_parser"

parsers:
  simple_parser:
    type: "simple"
    success_patterns: ["Hello, World!"]
```

### Pytest Example

```yaml
name: "Test Suite"
steps:
  - name: "run_tests"
    commands:
      - command: "pytest tests/ -v"
    parser: "pytest_parser"

parsers:
  pytest_parser:
    type: "pytest"

visualizations:
  - name: "test_performance"
    type: "line_chart"
    data_source: "run_tests"
    x_axis: "test_name"
    y_axis: "duration"
    title: "Test Performance"
```

## Output

Perfx generates several output files:

- `evaluation_results.json`: Structured evaluation results
- `executed_commands.log`: Detailed command execution log
- `summary.txt`: Human-readable summary
- Charts and tables as specified in configuration
- Reports in requested formats

## Extending Perfx

### Custom Parsers

Create a custom parser by inheriting from `BaseParser`:

```python
from perfx.parsers.base import BaseParser

class MyParser(BaseParser):
    def parse_step_results(self, step_results):
        # Custom parsing logic
        return {"custom_data": "value"}
```

### Custom Visualizations

Add new visualization types by extending the visualization modules.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Author

**Jianhong Zhao** - zhaojianhong96@gmail.com

## License

[Add your license information here] 