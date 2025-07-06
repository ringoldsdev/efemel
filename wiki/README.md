# Efemel

**Efemel** is a Python CLI tool that extracts public dictionary variables from Python files and exports them as JSON. It's designed to help you extract configuration data, settings, and structured data from Python code.

## What does Efemel do?

Efemel processes Python files and extracts all public dictionary variables (those not starting with `_`), then exports them to JSON files while preserving directory structure.

### Example

Given this Python file (`config.py`):

```python
# Public dictionaries - these will be extracted
database_config = {
    "host": "localhost",
    "port": 5432,
    "name": "myapp_db"
}

api_settings = {
    "timeout": 30,
    "retries": 3,
    "endpoints": ["auth", "users", "data"]
}

# Private variables - these will be ignored
_internal_config = {"secret": "hidden"}
__cache_settings = {"ttl": 3600}

# Non-dictionaries - these will be ignored
API_URL = "https://api.example.com"
DEBUG = True
```

Running `efemel process config.py --out output` produces `output/config.json`:

```json
{
  "database_config": {
    "host": "localhost",
    "port": 5432,
    "name": "myapp_db"
  },
  "api_settings": {
    "timeout": 30,
    "retries": 3,
    "endpoints": ["auth", "users", "data"]
  }
}
```

## Installation

```bash
# Install in development mode
uv pip install -e .

# Or install from source
pip install .
```

## Usage

### Basic Usage

```bash
# Process a single file
efemel process config.py --out output

# Process multiple files with glob patterns (uses all CPU cores by default)
efemel process "src/**/*.py" --out exports

# Process files relative to a specific directory
efemel process "**/*.py" --cwd /path/to/project --out output

# Control parallelism with --workers option
efemel process "**/*.py" --out output --workers 2
```

### Real-world Example

Consider this project structure:

```
project/
├── config/
│   ├── database.py
│   └── api.py
└── settings/
    └── app.py
```

With these files:

**config/database.py:**
```python
production = {
    "host": "prod-db.company.com",
    "port": 5432,
    "ssl": True
}

development = {
    "host": "localhost",
    "port": 5432,
    "ssl": False
}
```

**config/api.py:**
```python
endpoints = {
    "auth": "/api/v1/auth",
    "users": "/api/v1/users",
    "data": "/api/v1/data"
}

rate_limits = {
    "requests_per_minute": 60,
    "burst_limit": 100
}
```

**settings/app.py:**
```python
app_config = {
    "name": "MyApp",
    "version": "2.1.0",
    "features": ["auth", "api", "dashboard"]
}
```

Running:
```bash
efemel process "**/*.py" --out exported_config
```

Produces:
```
exported_config/
├── config/
│   ├── database.json
│   └── api.json
└── settings/
    └── app.json
```

With `exported_config/config/database.json`:
```json
{
  "production": {
    "host": "prod-db.company.com",
    "port": 5432,
    "ssl": true
  },
  "development": {
    "host": "localhost",
    "port": 5432,
    "ssl": false
  }
}
```

## CLI Commands

### `efemel process`

Extract dictionary variables from Python files.

**Options:**
- `FILE_PATTERN` - Glob pattern to match Python files (e.g., `"**/*.py"`, `config.py`)
- `--out OUTPUT_DIR` - Directory to write JSON files (required)
- `--cwd DIRECTORY` - Working directory for file operations (optional)
- `--env ENVIRONMENT` - Environment for dynamic imports (e.g., `prod`, `staging`) (optional)
- `--workers NUMBER` - Number of parallel workers (default: CPU thread count) (optional)

**Examples:**
```bash
# Single file
efemel process config.py --out output

# All Python files recursively (uses all CPU cores)
efemel process "**/*.py" --out output

# Files in specific directory with 2 workers
efemel process "src/config/*.py" --out exported --workers 2

# Process relative to different directory
efemel process "*.py" --cwd /path/to/configs --out output

# Process with production environment
efemel process "config/**/*.py" --out output --env prod

# Process with staging environment and custom working directory (single-threaded)
efemel process "**/*.py" --cwd /app/configs --out exports --env staging --workers 1
```

### `efemel info`

Show package information and version.

## Environment-Specific Processing

Efemel supports environment-specific file loading using the `--env` option. This allows you to dynamically load different configurations based on the environment (dev, prod, staging, etc.).

### How it works

When you specify `--env <environment>`, Efemel will:
1. For any `import` statements in your Python files, look for `<module>.<environment>.py` first
2. If the environment-specific file doesn't exist, fall back to the default `<module>.py`

### Example: Dev vs Production Configuration

Consider this project structure:
```
config/
├── main.py           # Main configuration file
├── database.py       # Default database config
├── database.prod.py  # Production database config
├── cache.py          # Default cache config
└── cache.prod.py     # Production cache config
```

**config/main.py:**
```python
from database import connection_config
from cache import cache_settings

# Main application configuration
app_config = {
    "name": "MyApp",
    "version": "2.0.0",
    "database": connection_config,
    "cache": cache_settings
}

deployment = {
    "workers": 4,
    "timeout": 30
}
```

**config/database.py** (development):
```python
connection_config = {
    "host": "localhost",
    "port": 5432,
    "database": "myapp_dev",
    "ssl": False,
    "pool_size": 5
}
```

**config/database.prod.py** (production):
```python
connection_config = {
    "host": "prod-cluster.company.com",
    "port": 5432,
    "database": "myapp_production",
    "ssl": True,
    "pool_size": 20,
    "ssl_cert": "/etc/ssl/prod.pem"
}
```

**config/cache.py** (development):
```python
cache_settings = {
    "type": "memory",
    "max_size": 100,
    "ttl": 300
}
```

**config/cache.prod.py** (production):
```python
cache_settings = {
    "type": "redis",
    "host": "redis-cluster.company.com",
    "port": 6379,
    "ttl": 3600,
    "cluster_mode": True
}
```

### Processing with Different Environments

**Development environment (default):**
```bash
efemel process config/main.py --out output/dev
```

This generates `output/dev/main.json`:
```json
{
  "app_config": {
    "name": "MyApp",
    "version": "2.0.0",
    "database": {
      "host": "localhost",
      "port": 5432,
      "database": "myapp_dev",
      "ssl": false,
      "pool_size": 5
    },
    "cache": {
      "type": "memory",
      "max_size": 100,
      "ttl": 300
    }
  },
  "deployment": {
    "workers": 4,
    "timeout": 30
  }
}
```

**Production environment:**
```bash
efemel process config/main.py --out output/prod --env prod
```

This generates `output/prod/main.json`:
```json
{
  "app_config": {
    "name": "MyApp",
    "version": "2.0.0",
    "database": {
      "host": "prod-cluster.company.com",
      "port": 5432,
      "database": "myapp_production",
      "ssl": true,
      "pool_size": 20,
      "ssl_cert": "/etc/ssl/prod.pem"
    },
    "cache": {
      "type": "redis",
      "host": "redis-cluster.company.com",
      "port": 6379,
      "ttl": 3600,
      "cluster_mode": true
    }
  },
  "deployment": {
    "workers": 4,
    "timeout": 30
  }
}
```

### Environment Options Examples

```bash
# Development (default behavior)
efemel process "config/**/*.py" --out exports/dev

# Production environment
efemel process "config/**/*.py" --out exports/prod --env prod

# Staging environment  
efemel process "config/**/*.py" --out exports/staging --env staging

# Test environment
efemel process "config/**/*.py" --out exports/test --env test
```

## Development

### Quick Start

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting and formatting
uv run ruff check .
uv run ruff format .
```

### Project Structure

```
efemel/
├── efemel/              # Main package
│   ├── cli.py          # CLI interface
│   ├── main.py         # Core logic
│   └── process.py      # File processing
├── tests/              # Test files and fixtures
│   ├── inputs_basic/   # Test input files
│   ├── outputs_basic/  # Expected outputs
│   └── test_cli.py     # Test suite
└── pyproject.toml      # Project configuration
```

### Makefile Commands

```bash
make help           # Show available commands
make test           # Run tests
make check          # Run all checks (lint + format + test)
make generate-test-outputs  # Regenerate test outputs
```

## Use Cases

- **Configuration Export**: Extract configuration dictionaries from Python files to JSON for other tools
- **Data Migration**: Convert Python data structures to JSON for database seeding or API payloads
- **Documentation**: Generate JSON schemas or API documentation from Python configuration files
- **Multi-environment Config**: Export environment-specific configurations from Python modules

## What gets extracted?

✅ **Extracted:**
- Public dictionary variables (not starting with `_`)
- Nested dictionaries and complex data structures
- All standard JSON-compatible Python data types

❌ **Ignored:**
- Private variables (`_private`, `__internal`)
- Non-dictionary variables (strings, numbers, lists, etc.)
- Functions and classes
- Import statements

---

Built with ❤️ using [UV](https://github.com/astral-sh/uv) package manager.
