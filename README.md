---
name: "Efemel"
short_description: "Python-nati**Primary Use Cases:**
- **CI/CD Pipelines:** Generate GitHub Actions, GitLab CI, or Jenkins workflows with complex logic and conditions
- **Cloud Workflows:** AWS Step Functions, Google Cloud Workflows, Azure Logic Apps with dynamic state machines
- **Infrastructure as Code:** Terraform, CloudFormation, or ARM templates with environment-specific resources
- **Docker Compose:** Multi-service applications with environment-specific configurations and overrides
- **Application Config:** API settings, database connections, feature flags across dev/staging/prod environments
- **API Gateway Configs:** Route definitions, rate limiting, authentication rules for different environments
- **Monitoring & Alerting:** Datadog monitors, New Relic alerts, or custom monitoring rules with complex conditionsguration tool eliminating YAML templating hell and markup language complexity"
long_description: "Efemel is a developer tool that uses Python dictionaries as a configuration language, replacing difficult-to-template markup formats (YAML, JSON, TOML) with native Python syntax for complex configuration management, multi-environment deployments, and automated validation."
version: "1.0.0"
license: "MIT"
primary_language: "Python"
category: "DevOps Tool"
keywords: ["python", "configuration", "templating", "yaml-alternative", "devops", "config-management", "multi-environment"]
status: "Active Development"
target_audience: ["DevOps Engineers", "Platform Engineers", "Configuration Managers", "Infrastructure Teams"]
github_repo_url: "https://github.com/your-username/efemel"
documentation_url: "https://github.com/your-username/efemel/wiki"
contributing_guide_url: "https://github.com/your-username/efemel/wiki/Development"
issue_tracker_url: "https://github.com/your-username/efemel/issues"
---

<!-- PROJECT_TITLE -->
# Efemel

<!-- PROJECT_TAGLINE -->
**Python turned into a functional markup language. Also what I've said thousands of times while working with yaml.**

<!-- BADGES_SECTION -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Built with UV](https://img.shields.io/badge/built%20with-uv-green)](https://github.com/astral-sh/uv)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

<!-- INTRODUCTION_SECTION -->
## 🎯 Overview

**Efemel** is a configuration management tool that replaces complex markup templating with native Python syntax. Instead of wrestling with YAML templating engines, custom DSLs, or markup languages that don't scale, Efemel lets you write configurations in Python and export them to any format you need.

**Pain Points Solved:**
- **YAML at Scale:** Plain YAML becomes unmaintainable for complex configurations (1000+ line files, deep nesting)
- **Templating Hell:** Tools like Helm, Jinja2, or Jsonnet require learning custom DSLs with poor tooling
- **Zero Validation:** Markup languages provide no built-in validation, type checking, or IDE support
- **Runtime-Only Errors:** Syntax and logic errors only discovered during deployment, not development
- **Limited Logic:** Complex conditionals, loops, and transformations are impossible or unreadable in markup
- **Copy-Paste Culture:** Configuration duplication across environments leads to drift and maintenance nightmares

**Why Python for Configuration:**
- **Native Language:** Use familiar Python syntax instead of learning templating DSLs or custom languages
- **Built-in Validation:** Leverage Python's type system, IDE autocomplete, and linting for immediate feedback
- **Full Programming Power:** Complex logic, imports, functions, classes - everything Python offers
- **Excellent Tooling:** IDE support, debugging, unit testing, version control, and code review workflows
- **Instant Feedback:** Syntax errors, type issues, and logic problems caught during development, not deployment
- **Reusable Components:** Create shared libraries of configuration components with proper imports and modules

**Primary Use Cases:**
- **CI/CD Pipelines:** Generate GitHub Actions, GitLab CI, or Jenkins workflows with complex logic and conditions
- **Workflows:** AWS Step Functions, Google Cloud Workflows, Azure Logic Apps with dynamic state machines
- **Infrastructure as Code:** Terraform, CloudFormation, or ARM templates with environment-specific resources
- **Docker Compose:** Multi-service applications with environment-specific configurations and overrides
- **Application Config:** API settings, database connections, feature flags across dev/staging/prod environments

---

<!-- FEATURES_SECTION -->
## ✨ Features & Capabilities

### Core Functionality
- **Python-Native Configuration:** Write configs in Python instead of learning templating languages
- **Multi-Format Export:** Generate JSON, YAML, TOML, or any structured format
- **Structure Preservation:** Maintains source directory hierarchy in output
- **Parallel Processing:** Multi-threaded processing for large configuration projects
- **Glob Pattern Support:** Flexible file selection with Unix-style patterns
- **IDE Integration:** Full autocomplete, type checking, and error detection during development

### Advanced Features  
- **Environment-Specific Processing:** Different configs per environment without templating (`--env prod`)
- **Extensible Hook System:** Custom transformation pipeline for output formatting
- **Auto-Validation:** Leverage Python's type system and IDE validation
- **Zero Configuration:** Works out-of-the-box with sensible defaults
- **Testable Configurations:** Unit test your configs like any Python code
- **Live Reload:** Instant feedback loop - see configuration changes immediately

---

<!-- INSTALLATION_SECTION -->
## 📦 Installation & Setup

To be filled out once it gets compiled and released.

---

<!-- USAGE_SECTION -->
## 🚀 Usage Examples

### Basic Usage

#### Single File Processing
```bash
# Extract dictionaries from one file
efemel process config.py --out output/
```

#### Batch Processing
```bash
# Process all Python files recursively
efemel process "**/*.py" --out exported_configs/

# Process specific directory
efemel process "src/config/*.py" --out configs/
```

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

### Core Patterns & Examples

#### Pattern 1: Basic Dictionary Extraction

**Input (`app_config.py`):**
```python
# Basic dictionary variables are extracted
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

# Private variables (underscore prefix) are ignored
_internal_config = {"secret": "hidden"}

# Non-dictionary variables are ignored
DEBUG = True
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
  }
}
```

#### Pattern 2: Environment-Specific File Overrides

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

#### Pattern 3: Composable Configuration Parts

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

# Compose services using dict merging
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

**Output (`efemel process docker_config.py --out configs/`):**

*docker_config.json:*
```json
{
  "docker_compose": {
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
}
```

### Compare: Traditional YAML vs. Efemel Approach

#### ❌ Traditional YAML + Templating
```yaml
# app-config-prod.yaml
app_name: "{{ .AppName }}"
log_level: {{ if eq .Environment "prod" }}"INFO"{{ else }}"DEBUG"{{ end }}
workers: {{ if eq .Environment "prod" }}8{{ else if eq .Environment "dev" }}1{{ else }}2{{ end }}
{{- if eq .Environment "prod" }}
monitoring_enabled: true
{{- end }}

# app-config-dev.yaml (separate file with duplication)
app_name: "{{ .AppName }}"
log_level: "DEBUG"
workers: 1

# values-prod.yaml, values-dev.yaml (more files to maintain)
AppName: "api-server"
Environment: "prod"
```

**Problems:**
- **No validation** until runtime deployment
- **Complex templating** syntax that's hard to read and debug
- **Multiple files** for each environment with copy-paste duplication
- **Learning curve** for templating language
- **Runtime-only errors** - broken templates discovered during deployment

#### ✅ Efemel Python Approach
```python
# config.py (default)
app_config = {
    "app_name": "api-server",
    "log_level": "INFO",
    "workers": 2
}

# config.prod.py (production override)
app_config = {
    "app_name": "api-server", 
    "log_level": "INFO",
    "workers": 8,
    "monitoring_enabled": True
}

# main.py (imports based on --env flag)
from config import app_config
```

**Benefits:**
- **Immediate validation** with Python type hints and IDE support
- **Full IDE support** - autocomplete, refactoring, debugging
- **Unit testable** configuration logic
- **Standard Python** - no new syntax to learn
- **Instant feedback** during development

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

### License Summary
- **Commercial Use:** Permitted
- **Modification:** Permitted  
- **Distribution:** Permitted
- **Private Use:** Permitted
- **Liability:** Not provided
- **Warranty:** Not provided

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
