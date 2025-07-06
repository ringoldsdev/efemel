# Efemel

**Efemel** is a Python CLI tool that extracts public dictionary variables from Python files and exports them as JSON. It's designed to help you extract configuration data, settings, and structured data from Python code.

## Quick Start

```bash
# Install
pip install efemel

# Extract dictionaries from a Python file
efemel process config.py --out output

# Process multiple files with glob patterns
efemel process "src/**/*.py" --out exports

# Use hooks for custom transformations
efemel process "**/*.py" --out output --hooks hooks/
```

## Example

Given this Python file (`config.py`):

```python
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

## Features

- ✅ **Extract public dictionaries** from Python files
- ✅ **Preserve directory structure** in outputs
- ✅ **Environment-specific processing** (`--env prod`)
- ✅ **Parallel processing** for large codebases
- ✅ **Extensible hook system** for custom transformations
- ✅ **Glob pattern support** for flexible file selection

## Documentation

📖 **[Full Documentation](../../wiki)** - Comprehensive guides and API reference

Key documentation sections:
- **[Usage Guide](../../wiki#usage)** - Basic and advanced usage examples
- **[Environment Processing](../../wiki#environment-specific-processing)** - Multi-environment configurations
- **[Hooks System](../../wiki/Hooks)** - Customize processing with hooks
- **[Development Guide](../../wiki/Development)** - Contributing and development setup
- **[API Reference](../../wiki/API-Reference)** - Complete API documentation

## Installation

```bash
# From PyPI (when published)
pip install efemel

# Development installation
git clone https://github.com/your-username/efemel.git
cd efemel
uv sync --dev
uv pip install -e .
```

## Use Cases

- **Configuration Export**: Extract configuration dictionaries for other tools
- **Data Migration**: Convert Python data structures to JSON for databases/APIs  
- **Documentation**: Generate JSON schemas from Python configuration files
- **Multi-environment Config**: Export environment-specific configurations

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

## Contributing

Contributions welcome! See the [Development Guide](../../wiki/Development) for setup instructions and contribution guidelines.

## License

MIT License - see LICENSE file for details.

---

Built with ❤️ using [UV](https://github.com/astral-sh/uv) package manager.
