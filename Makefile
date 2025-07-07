.PHONY: help install install-dev lint lint-fix format check test clean build upload upload-test generate-test-outputs

# Default target
help:
	@echo "Available commands:"
	@echo "  install              - Install the package in editable mode"
	@echo "  install-dev          - Install the package with development dependencies"
	@echo "  lint                 - Run ruff linter (check only)"
	@echo "  lint-fix             - Run ruff linter and fix errors automatically"
	@echo "  format               - Format code with ruff"
	@echo "  check                - Run all checks (lint + format check + tests)"
	@echo "  test                 - Run tests with pytest"
	@echo "  generate-test-outputs - Generate expected test outputs from test inputs (includes params file demo)"
	@echo "  clean                - Clean build artifacts and cache files"
	@echo "  build                - Build the package for distribution"
	@echo "  upload-test          - Upload package to TestPyPI"
	@echo "  upload               - Upload package to PyPI"
	@echo "  info                 - Show package information"
	@echo "  run                  - Show CLI help"
	@echo "  run-hello            - Run hello command"

# Install the package in editable mode
install:
	uv pip install -e .

# Install the package with development dependencies
install-dev:
	uv pip install -e ".[dev]"

# Run ruff linter (check only)
lint:
	uv run ruff check .

# Run ruff linter and fix errors automatically
lint-fix:
	uv run ruff check --fix .

# Format code with ruff
format:
	uv run ruff format .

# Check if code is properly formatted (without making changes)
format-check:
	uv run ruff format --check .

# Run all checks (lint + format check + tests)
check: lint format-check test

# Run tests with pytest
test:
	uv run pytest

# Generate expected test outputs from test inputs
generate-test-outputs:
	@uv run efemel process "**/*.py" --cwd tests/inputs/basic --out tests/outputs/basic --clean
	@uv run efemel process "*.py" --cwd tests/inputs/with_imports --out tests/outputs/with_imports --env prod --clean
	@uv run efemel process "**/*.py" --cwd tests/inputs/basic --out tests/outputs/flattened --flatten --clean
	@uv run efemel process "**/*.py" --cwd tests/inputs/basic --out tests/outputs/with_hooks --hooks tests/hooks/before_after/output_filename.py --clean
	@uv run efemel process "**/*.py" --cwd tests/inputs/basic --out tests/outputs/with_hooks_dir --hooks tests/hooks/multiple --clean
	@uv run efemel process "**/*.py" --cwd tests/inputs/process_data --out tests/outputs/process_data_pick --pick user_data --clean
	@uv run efemel process "**/*.py" --cwd tests/inputs/process_data --out tests/outputs/process_data_unwrap --unwrap user_data --clean
	@uv run efemel process "**/*.py" --cwd tests/inputs/with_params --out tests/outputs/with_params --param app_name=myapp --param version=2.0.0 --param debug_mode=true --param port=8080 --param 'database_config={"host":"prod-db","port":5432}' --param memory_mb=512 --clean
	@uv run efemel process "config.py" --cwd tests/inputs/with_params_file --out tests/outputs/with_params_file --params-file tests/params/params.py --clean


# Clean build artifacts and cache files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Build the package for distribution
build: clean
	uv build

# Upload package to TestPyPI (requires TWINE_USERNAME and TWINE_PASSWORD env vars)
upload-test: build
	uv run twine upload --repository testpypi dist/*

# Upload package to PyPI (requires TWINE_USERNAME and TWINE_PASSWORD env vars)
upload: build
	uv run twine upload dist/*

# Install twine for package uploading (run this once before upload commands)
install-twine:
	uv add --dev twine

# Show package info
info:
	uv run efemel info

# Run the CLI application
run:
	uv run efemel --help

# Run the CLI application with hello command
run-hello:
	uv run efemel hello
