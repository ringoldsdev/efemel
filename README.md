# Efemel

A Python CLI application built with UV package manager.

## Development Setup

This project uses VS Code Development Containers for a consistent development environment and UV for fast Python package management.

### Prerequisites

- [VS Code](https://code.visualstudio.com/)
- [Docker](https://www.docker.com/get-started)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Getting Started

1. Clone this repository
2. Open the project in VS Code
3. When prompted, click "Reopen in Container" or use the Command Palette (Ctrl+Shift+P) and select "Dev Containers: Reopen in Container"
4. VS Code will build the development container, install UV, and set up the virtual environment with dependencies

### Project Structure

```
efemel/
├── .devcontainer/
│   └── devcontainer.json    # Dev container configuration
├── efemel/                  # Main package directory
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Main application logic
│   └── cli.py              # CLI entry point
├── tests/
│   └── test_main.py        # Test files
├── pyproject.toml          # Project configuration and dependencies
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

### Package Management with UV

This project uses [UV](https://github.com/astral-sh/uv) for fast Python package management.

#### Adding Dependencies

```bash
# Add a runtime dependency
uv add requests

# Add a development dependency
uv add --dev pytest-cov
```

#### Installing Dependencies

```bash
# Install all dependencies (runtime + dev)
uv sync

# Install only runtime dependencies
uv sync --no-dev
```

### Installing the CLI

```bash
# Install in development mode (editable)
uv pip install -e .

# Or install from source
uv pip install .
```

### Using the CLI

```bash
# Show help
efemel

# Print hello world message
efemel --hello

# Show version
efemel --version
```

### Running the Project

```bash
# Run directly with UV
uv run efemel --hello

# Or activate the virtual environment and run
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
efemel --hello
```

### Running Tests

```bash
# Run tests with UV
uv run pytest

# Or with activated environment
source .venv/bin/activate
pytest
```

### Code Formatting and Linting

The project uses Ruff for both code formatting and linting:

```bash
# Format code
uv run ruff format .

# Check for linting issues
uv run ruff check .

# Fix auto-fixable linting issues
uv run ruff check --fix .
```

## Contributing

### Development Workflow

1. **Make your changes**
2. **Run checks locally** (recommended before committing):
   ```bash
   make ci-local     # Run the same checks as CI
   # OR
   make pre-commit   # Fix formatting, lint, and test
   ```
3. **Commit and push** your changes
4. **Create a Pull Request**

The CI will automatically run when you create or update a PR and will check:
- ✅ Code formatting (ruff format)
- ✅ Linting (ruff check) 
- ✅ Tests (pytest)
- ✅ Package builds correctly
- ✅ CLI functionality works

### Makefile Commands

```bash
make help         # Show all available commands
make install-dev  # Install development dependencies
make lint-fix     # Fix linting issues automatically
make format       # Format code
make test         # Run tests
make check        # Run all checks (lint + format + test)
make build        # Build package for distribution
make ci-local     # Run same checks as GitHub Actions
make pre-commit   # Quick check before committing
```

### GitHub Actions

This project uses GitHub Actions for CI/CD:

- **PR Validation** (`pr-validation.yml`) - Runs on every PR with detailed feedback
- **Required Checks** (`required-checks.yml`) - Must pass before merging
- **CI** (`ci.yml`) - Comprehensive testing across Python versions

To set up required status checks in your repository:
1. Go to Settings → Branches → Add rule for your main branch  
2. Enable "Require status checks to pass before merging"
3. Select "Required Checks (Lint + Test)" as a required check

1. Make sure your code follows the project's coding standards
2. Run tests before submitting changes  
3. Update documentation as needed
