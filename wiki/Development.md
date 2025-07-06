# Development Guide

This guide covers how to contribute to and develop Efemel.

## Prerequisites

- Python 3.12+
- [UV](https://github.com/astral-sh/uv) package manager
- Git

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/efemel.git
   cd efemel
   ```

2. **Install development dependencies:**
   ```bash
   uv sync --dev
   ```

3. **Verify installation:**
   ```bash
   uv run efemel --help
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=efemel

# Run specific test file
uv run pytest tests/test_cli.py

# Run tests with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Run linting
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check formatting without changes
uv run ruff format --check .

# Run all checks (lint + format + test)
make check
```

### Makefile Commands

The project includes a comprehensive Makefile with common development tasks:

```bash
make help                    # Show available commands
make install                 # Install package in editable mode
make install-dev             # Install with development dependencies
make test                    # Run tests
make lint                    # Run linting (check only)
make lint-fix                # Run linting with auto-fix
make format                  # Format code
make check                   # Run all checks
make generate-test-outputs   # Regenerate expected test outputs
make clean                   # Clean build artifacts
make build                   # Build distribution packages
```

## Project Structure

```
efemel/
├── .github/
│   └── workflows/           # GitHub Actions workflows
├── efemel/                  # Main package source
│   ├── __init__.py         # Package initialization
│   ├── cli.py              # Click CLI interface
│   ├── hooks_manager.py    # Hook system management
│   ├── process.py          # Core file processing logic
│   ├── hooks/              # Built-in hooks
│   ├── readers/            # File reading implementations
│   ├── transformers/       # Data transformation (JSON, etc.)
│   └── writers/            # Output writing implementations
├── tests/                  # Test suite
│   ├── inputs/             # Test input files
│   ├── outputs/            # Expected test outputs
│   ├── hooks/              # Test hooks
│   └── test_*.py           # Test modules
├── wiki/                   # Wiki documentation source
├── pyproject.toml          # Project configuration
├── uv.lock                 # Dependency lock file
├── Makefile               # Development commands
└── README.md              # Project overview
```

## Adding New Features

### 1. Readers

Readers handle input file discovery and reading. To add a new reader:

1. Create a new file in `efemel/readers/`
2. Implement the reader interface
3. Register it in the CLI

Example reader structure:
```python
class MyReader:
    def __init__(self, **options):
        pass
    
    def read(self, pattern):
        """Yield Path objects for files matching pattern"""
        pass
```

### 2. Transformers

Transformers convert Python data to output formats. To add a new transformer:

1. Create a new file in `efemel/transformers/`
2. Implement the transformer interface
3. Add CLI option support

Example transformer:
```python
class MyTransformer:
    def __init__(self):
        self.suffix = ".myformat"
    
    def transform(self, data):
        """Convert data to target format"""
        pass
```

### 3. Writers

Writers handle output file creation. To add a new writer:

1. Create a new file in `efemel/writers/`
2. Implement the writer interface
3. Add CLI integration

### 4. Hooks

Hooks provide extensible processing pipeline. See [Hooks Documentation](Hooks) for details.

## Testing Strategy

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test complete CLI workflows
- **Fixture-based Testing**: Use real input/output file pairs

### Test Data

Test data is organized in `tests/` with parallel input/output structures:

```
tests/
├── inputs/
│   ├── basic/              # Basic test cases
│   └── with_imports/       # Environment-specific imports
└── outputs/
    ├── basic/              # Expected outputs for basic
    ├── flattened/          # Expected flattened outputs
    ├── with_imports/       # Expected environment outputs
    └── with_hooks/         # Expected hook-modified outputs
```

### Generating Test Outputs

When adding new test cases or modifying functionality:

```bash
# Regenerate all expected outputs
make generate-test-outputs

# Verify tests pass with new outputs
make test
```

## Debugging

### Debug Mode

Run with Python's debug mode for detailed tracebacks:

```bash
uv run python -X dev -m efemel.cli process "**/*.py" --out output
```

### Verbose Output

Most commands support verbose output:

```bash
uv run efemel process "**/*.py" --out output --verbose
```

### Hook Debugging

When developing hooks, use print statements or logging:

```python
def my_hook(context):
    print(f"Debug: context keys = {list(context.keys())}")
    # Hook logic here
```

## Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/my-feature`
3. **Make changes and add tests**
4. **Run tests:** `make check`
5. **Commit changes:** `git commit -m "Add my feature"`
6. **Push to branch:** `git push origin feature/my-feature`
7. **Create pull request**

### Pull Request Guidelines

- Include tests for new functionality
- Update documentation as needed
- Follow existing code style
- Ensure all checks pass
- Write clear commit messages

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions will build and publish automatically

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/your-username/efemel/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/efemel/discussions)
- **Documentation**: This wiki
