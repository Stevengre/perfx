# Makefile for perfx project
# Author: Jianhong Zhao <zhaojianhong96@gmail.com>

.PHONY: help install install-dev test test-coverage format lint type-check clean clean-all check-all

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-coverage- Run tests with coverage report"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run linting checks"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  clean        - Clean Python cache files"
	@echo "  clean-all    - Clean all generated files"
	@echo "  check-all    - Run format, lint, type-check, and tests"
	@echo "  run          - Run perfx CLI"
	@echo "  build        - Build the package"
	@echo "  demo-mocks   - Demo realistic mock durations"
	@echo "  generate-mocks - Generate real mock data"

# Install dependencies
install:
	uv sync

install-dev:
	uv sync --extra dev

# Testing
test:
	uv run pytest

test-coverage:
	uv run pytest --cov=perfx --cov-report=html --cov-report=term-missing

test-verbose:
	uv run pytest -v

test-failed:
	uv run pytest --lf

# Code formatting
format:
	uv run black perfx/ tests/
	uv run isort perfx/ tests/

format-check:
	uv run black --check perfx/ tests/
	uv run isort --check-only perfx/ tests/

# Linting
lint:
	uv run flake8 perfx/ tests/ --max-line-length=88 --extend-ignore=E203,W503

# Type checking
type-check:
	uv run mypy perfx/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf results/
	rm -rf repositories/

clean-all: clean
	rm -rf .venv/
	rm -f uv.lock

# Run all checks
check-all: format-check lint type-check test

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete!"

# Run the CLI
run:
	uv run perfx --help

# Build package
build:
	uv build

# Show project info
info:
	@echo "Project: perfx"
	@echo "Python version: $(shell python --version)"
	@echo "UV version: $(shell uv --version)"
	@echo "Source directory: perfx/"
	@echo "Tests directory: tests/"

# Demo realistic mock durations (deprecated - use generate-mocks instead)
demo-mocks:
	@echo "This command is deprecated. Use 'make generate-mocks' instead."
	@echo "Running generate-mocks..."
	uv run python perfx/utils/generate_mocks.py

# Generate real mock data
generate-mocks:
	uv run python perfx/utils/generate_mocks.py

# Quick development cycle
dev: format lint type-check test

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	uv run pytest $(FILE)

# Run tests with specific pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=test_pattern"; \
		exit 1; \
	fi
	uv run pytest -k "$(PATTERN)"

# Install pre-commit hooks (if pre-commit is available)
install-hooks:
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
	else \
		echo "pre-commit not found. Install it with: pip install pre-commit"; \
	fi

# Show dependency tree
deps:
	uv tree

# Update dependencies
update:
	uv lock --upgrade

# Security check (if safety is available)
security-check:
	@if command -v safety >/dev/null 2>&1; then \
		safety check; \
	else \
		echo "safety not found. Install it with: pip install safety"; \
	fi

# Documentation
docs:
	@echo "Documentation commands:"
	@echo "  make docs-build  - Build documentation"
	@echo "  make docs-serve  - Serve documentation locally"

docs-build:
	@echo "Building documentation..."
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs build; \
	else \
		echo "mkdocs not found. Install it with: pip install mkdocs"; \
	fi

docs-serve:
	@echo "Serving documentation..."
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs serve; \
	else \
		echo "mkdocs not found. Install it with: pip install mkdocs"; \
	fi 