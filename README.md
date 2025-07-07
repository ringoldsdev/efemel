<!-- PROJECT_TITLE -->
# Efemel

<!-- PROJECT_TAGLINE -->
**Python as a functional markup language. Solves YAML scaling issues.**

<!-- BADGES_SECTION -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Built with UV](https://img.shields.io/badge/built%20with-uv-green)](https://github.com/astral-sh/uv)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

<!-- INTRODUCTION_SECTION -->
## 🎯 Overview

**Efemel** replaces markup templating with native Python. Solves configuration scaling issues without DSLs.

**Why Python:**
- Native syntax instead of templating DSLs
- Built-in validation and IDE support
- Full programming capabilities
- Testable configurations

**Use Cases:**
- CI/CD pipelines
- Infrastructure as Code
- Workflow definitions
- Docker Compose configs
- Application settings

---

<!-- FEATURES_SECTION -->
## ✨ Features

### Core
- Python-native configuration
- Multi-format export (JSON/YAML/TOML)
- Directory structure preservation
- Parallel processing
- Glob pattern support
- IDE integration

### Advanced  
- Environment-specific processing
- Extensible hook system
- Auto-validation
- Testable configurations
- Live reload

---

<!-- INSTALLATION_SECTION -->
## 📦 Installation

To be filled out once compiled and released.

---

<!-- USAGE_SECTION -->
## 🚀 Usage

### Basic
```bash
# Single file
efemel process config.py --out output/

# Batch processing
efemel process "**/*.py" --out exported_configs/

# Pick specific keys
efemel process "**/*.py" --out output/ --pick result

# Unwrap values
efemel process "**/*.py" --out output/ --unwrap result
### Advanced Usage

#### Environment-Specific Processing
```bash
# Production environment
efemel process "config/**/*.py" --out prod_config/ --env prod

# Development environment  
efemel process "config/**/*.py" --out dev_config/ --env dev

# Staging with custom working directory
efemel process "*.py" --cwd /app/configs --out staging/ --env staging
```

### Advanced

#### Performance Tuning
```bash
# Control parallel workers
efemel process "**/*.py" --out output/ --workers 4

# Single-threaded processing
efemel process "**/*.py" --out output/ --workers 1
```

#### Hook-Based Transformations
```bash
# Use hook directory
efemel process "**/*.py" --out output/ --hooks hooks/
```

#### Parameter Injection
```bash
# Pass parameters to Python scripts during processing
efemel process "config.py" --out output/ --param app_name=myapp --param version=2.0.0 --param debug_mode=true

# Use JSON for complex parameters
efemel process "config.py" --out output/ --param 'database_config={"host":"prod-db","port":5432}'

# Multiple parameters
efemel process "**/*.py" --out output/ \
  --param app_name=myapp \
  --param version=2.0.0 \
  --param debug_mode=true \
  --param port=8080 \
  --param environment=production
```

### Core Patterns & Examples

#### Pattern 1: Parameter Injection

**Input (`config.py`):**
```python
# Parameters are injected as global variables
app_config = {
    "name": globals().get("app_name", "default-app"),
    "version": globals().get("version", "1.0.0"),
    "debug": globals().get("debug_mode", False),
    "port": globals().get("port", 3000),
}

# Direct usage (will raise NameError if not provided)
try:
    database_config = {
        "host": db_host,
        "port": db_port,
        "database": db_name,
    }
except NameError:
    database_config = {
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
    }

# Complex parameters (JSON objects)
if "redis_config" in globals():
    cache_config = globals()["redis_config"]
else:
    cache_config = {"host": "localhost", "port": 6379}
```

**Command:**
```bash
efemel process config.py --out output/ \
  --param app_name=myapp \
  --param version=2.0.0 \
  --param debug_mode=true \
  --param port=8080 \
  --param db_host=prod-db \
  --param db_port=5432 \
  --param db_name=mydb \
  --param 'redis_config={"host":"redis-server","port":6379}'
```

**Output:**
```json
{
  "app_config": {
    "name": "myapp",
    "version": "2.0.0",
    "debug": true,
    "port": 8080
  },
  "database_config": {
    "host": "prod-db",
    "port": 5432,
    "database": "mydb"
  },
  "cache_config": {
    "host": "redis-server",
    "port": 6379
  }
}
```

#### Pattern 2: Basic Data Extraction

**Input (`app_config.py`):**
```python
# All serializable variables are extracted
app_config = {
    "name": "my-app",
    "version": "1.0.0",
    "port": 8080
}

database = {
    "host": "localhost",
    "port": 5432,
    "name": "app_db"
}

# Simple values are also extracted
app_name = "my-application"
debug_mode = True
max_connections = 100

# Private variables (underscore prefix) are ignored
_internal_config = {"secret": "hidden"}
_debug_flag = False

# Non-serializable variables are filtered out
import os  # This won't be extracted
```

**Output (`efemel process app_config.py --out configs/`):**

*app_config.json:*
```json
{
  "app_config": {
    "name": "my-app", 
    "version": "1.0.0",
    "port": 8080
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "app_db"
  },
  "app_name": "my-application",
  "debug_mode": true,
  "max_connections": 100
}
```

#### Pattern 3: Environment-Specific File Overrides

**Input Files:**

*config.py (default):*
```python
server_config = {
    "app_name": "api-server",
    "log_level": "INFO",
    "workers": 2,
    "timeout": 30
}
```

*config.prod.py (production override):*
```python
server_config = {
    "app_name": "api-server",
    "log_level": "INFO",
    "workers": 8,
    "timeout": 60,
    "monitoring_enabled": True
}
```

*main.py (imports the config):*
```python
from config import server_config

application = {
    "name": "web-api",
    "config": server_config
}
```

**Default Output (`efemel process main.py --out configs/`):**
```json
{
  "application": {
    "name": "web-api",
    "config": {
      "app_name": "api-server",
      "log_level": "INFO",
      "workers": 2,
      "timeout": 30
    }
  }
}
```

**Production Output (`efemel process main.py --out configs/ --env prod`):**
```json
{
  "application": {
    "name": "web-api",
    "config": {
      "app_name": "api-server",
      "log_level": "INFO",
      "workers": 8,
      "timeout": 60,
      "monitoring_enabled": true
    }
  }
}
```

#### Pattern 4: Composable Configuration Parts

**Input (`docker_config.py`):**
```python
# Base service definition
base_service = {
    "restart": "unless-stopped",
    "networks": ["app-network"]
}

# Reusable components
logging_config = {
    "driver": "json-file",
    "options": {
        "max-size": "10m",
        "max-file": "3"
    }
}

health_check = {
    "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
    "interval": "30s",
    "timeout": "10s",
    "retries": 3
}

# Compose services using Python dict merging
web_service = {
    **base_service,
    "image": "nginx:alpine",
    "ports": ["80:80"],
    "logging": logging_config,
    "healthcheck": health_check
}

api_service = {
    **base_service,
    "image": "python:3.12",
    "ports": ["8080:8080"],
    "logging": logging_config,
    "environment": {
        "DATABASE_URL": "postgresql://localhost/app",
        "REDIS_URL": "redis://localhost:6379"
    }
}

# Final docker-compose structure
docker_compose = {
    "version": "3.8",
    "services": {
        "web": web_service,
        "api": api_service
    },
    "networks": {
        "app-network": {"driver": "bridge"}
    }
}
```

**Output (`efemel process docker_config.py --out configs/ --unwrap docker_compose`):**

*docker_config.json:*
```json
{
  "version": "3.8",
  "services": {
    "web": {
      "restart": "unless-stopped",
      "networks": ["app-network"],
      "image": "nginx:alpine",
      "ports": ["80:80"],
      "logging": {
        "driver": "json-file",
        "options": {
          "max-size": "10m", 
          "max-file": "3"
        }
      },
      "healthcheck": {
        "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
        "interval": "30s",
        "timeout": "10s",
        "retries": 3
      }
    },
    "api": {
      "restart": "unless-stopped",
      "networks": ["app-network"],
      "image": "python:3.12",
      "ports": ["8080:8080"],
      "environment": {
        "DATABASE_URL": "postgresql://localhost/app",
        "REDIS_URL": "redis://localhost:6379"
      }
    }
  },
  "networks": {
    "app-network": {"driver": "bridge"}
  }
}
```

---

<!-- CONFIGURATION_SECTION -->
## ⚙️ Configuration

### Command-Line Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `FILE_PATTERN` | - | `str` | Yes | - | Glob pattern for Python files |
| `--out` | `-o` | `str` | Yes | - | Output directory path |
| `--cwd` | `-c` | `str` | No | `"."` | Working directory for file operations |
| `--env` | `-e` | `str` | No | `None` | Environment name for imports |
| `--workers` | `-w` | `int` | No | `CPU_COUNT` | Number of parallel workers |
| `--hooks` | `-h` | `str` | No | `None` | Path to hooks file or directory |
| `--flatten` | `-f` | `flag` | No | `False` | Flatten directory structure |
| `--pick` | `-p` | `str` | No | `None` | Pick specific keys from the extracted data (can be used multiple times) |
| `--unwrap` | `-u` | `str` | No | `None` | Extract specific values from the processed data, merging them (can be used multiple times) |
| `--param` | `-P` | `str` | No | `None` | Pass custom parameters to processed scripts in key=value format (can be used multiple times) |

### Hook Configuration

Create custom transformation hooks in Python:

```python
# hooks/output_filename.py
def add_timestamp(context):
    """Add timestamp to output filenames"""
    from datetime import datetime
    output_path = context['output_file_path']
    timestamp = datetime.now().strftime('%Y%m%d')
    new_name = f"{output_path.stem}_{timestamp}{output_path.suffix}"
    context['output_file_path'] = output_path.with_name(new_name)
```

---

<!-- LICENSE_SECTION -->
## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<!-- FOOTER_SECTION -->
## 🚀 Built With

- **[Python 3.12+](https://python.org)** - Core language
- **[UV Package Manager](https://github.com/astral-sh/uv)** - Dependency management
- **[Click](https://click.palletsprojects.com/)** - CLI framework  
- **[Ruff](https://github.com/astral-sh/ruff)** - Code formatting and linting
- **[Pytest](https://pytest.org/)** - Testing framework
- **[DevContainers](https://containers.dev/)** - Consistent development environment
- **[GitHub Actions](https://github.com/features/actions)** - CI/CD automation

---

**⭐ Star this repository if Efemel helps your workflow!**
