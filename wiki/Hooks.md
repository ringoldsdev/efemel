# Hooks System

Efemel's hook system provides a powerful way to customize and extend the processing pipeline. Hooks allow you to modify how files are processed, where outputs are written, and how data is transformed.

## Overview

The hook system is based on the concept of **hook points** - specific moments in the processing pipeline where custom functions can be executed. Currently, Efemel supports:

- **`output_filename`**: Modify output file paths and names

## How Hooks Work

### Hook Files

Hooks are defined in Python files. The **filename** (without `.py` extension) becomes the **hook name**. All functions in that file are executed sequentially for that hook.

Example: A file named `output_filename.py` creates hooks for the `output_filename` hook point.

### Hook Functions

Hook functions receive a `context` dictionary that they can read from and modify:

```python
def my_transform(context):
    """
    Hook function that modifies the context.
    
    Args:
        context: Dictionary containing processing data
    """
    # Read from context
    input_path = context['input_file_path']
    output_path = context['output_file_path']
    
    # Modify context
    context['output_file_path'] = transform_path(output_path)
```

### Before Hooks

Functions prefixed with `before_` are executed before regular hooks:

```python
def before_validate(context):
    """Executed before other hooks"""
    if not context['input_file_path'].exists():
        raise ValueError("Input file not found")

def transform_filename(context):
    """Executed after before hooks"""
    # Transform logic here
    pass
```

## Built-in Hooks

### output_filename Hook

The `output_filename` hook point is called for each file and allows you to modify where and how output files are written.

**Context Parameters:**
- `input_file_path`: Path to the input Python file
- `output_file_path`: Proposed output file path  
- `output_dir`: Base output directory
- `env`: Current environment (if specified)

**Example built-in hooks:**

```python
# efemel/hooks/output_filename.py

def ensure_output_path(context):
    """Ensure output path has correct suffix"""
    output_path = context['output_file_path']
    if not output_path.suffix == '.json':
        context['output_file_path'] = output_path.with_suffix('.json')

def flatten_output_path(context):
    """Flatten directory structure into filename"""
    output_path = context['output_file_path']
    if len(output_path.parts) > 1:
        # Convert path/to/file.json -> path_to_file.json
        flat_name = '_'.join(output_path.parts).replace('/', '_')
        context['output_file_path'] = Path(flat_name)
```

## Using Hooks

### Single Hook File

```bash
efemel process "**/*.py" --out output --hooks path/to/my_hooks.py
```

### Hook Directory

```bash
efemel process "**/*.py" --out output --hooks path/to/hooks/
```

This loads all `.py` files in the directory as separate hooks.

## Creating Custom Hooks

### Example: Add Timestamp to Filenames

Create `timestamp_hooks.py`:

```python
from datetime import datetime
from pathlib import Path

def add_timestamp(context):
    """Add timestamp to output filename"""
    output_path = context['output_file_path']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Insert timestamp before file extension
    stem = output_path.stem
    suffix = output_path.suffix
    new_name = f"{stem}_{timestamp}{suffix}"
    
    context['output_file_path'] = output_path.with_name(new_name)
```

Usage:
```bash
efemel process config.py --out output --hooks timestamp_hooks.py
```

Result: `config.py` → `config_20250106_143022.json`

### Example: Environment-based Subdirectories

Create `env_organizer.py`:

```python
from pathlib import Path

def organize_by_environment(context):
    """Organize outputs into environment subdirectories"""
    env = context.get('env', 'default')
    output_path = context['output_file_path']
    
    # Add environment as subdirectory
    new_path = Path(env) / output_path
    context['output_file_path'] = new_path
```

Usage:
```bash
efemel process "**/*.py" --out output --env prod --hooks env_organizer.py
```

Result: `config.py` → `prod/config.json`

### Example: File Type Validation

Create `validators.py`:

```python
def before_validate_input(context):
    """Validate input file before processing"""
    input_path = context['input_file_path']
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if input_path.suffix != '.py':
        raise ValueError(f"Expected Python file, got: {input_path}")

def validate_output_dir(context):
    """Ensure output directory exists"""
    output_dir = context['output_dir']
    output_dir.mkdir(parents=True, exist_ok=True)
```

## Hook Directory Structure

For complex projects, organize hooks by functionality:

```
hooks/
├── output_filename.py      # Output path transformations
├── validation.py           # Input/output validation
├── metadata.py            # Add metadata to outputs
└── environments.py        # Environment-specific logic
```

Load all hooks:
```bash
efemel process "**/*.py" --out output --hooks hooks/
```

## Advanced Hook Patterns

### Conditional Logic

```python
def conditional_transform(context):
    """Apply transformation based on conditions"""
    input_path = context['input_file_path']
    
    # Only transform config files
    if 'config' in input_path.name:
        # Apply transformation
        context['output_file_path'] = transform_config_path(
            context['output_file_path']
        )
```

### Hook Configuration

Pass configuration through environment or file naming:

```python
import os

def configurable_transform(context):
    """Transform based on environment variable"""
    prefix = os.getenv('EFEMEL_PREFIX', 'output')
    output_path = context['output_file_path']
    
    new_name = f"{prefix}_{output_path.name}"
    context['output_file_path'] = output_path.with_name(new_name)
```

### Chain Transformations

Multiple functions in the same file are executed in order:

```python
def step1_normalize(context):
    """Step 1: Normalize path"""
    # Normalization logic
    pass

def step2_add_prefix(context):
    """Step 2: Add prefix (runs after step1)"""
    # Prefix logic
    pass

def step3_ensure_extension(context):
    """Step 3: Ensure correct extension (runs after step2)"""
    # Extension logic
    pass
```

## Testing Hooks

### Unit Testing

```python
def test_my_hook():
    context = {
        'input_file_path': Path('test.py'),
        'output_file_path': Path('test.json'),
        'output_dir': Path('output'),
        'env': 'test'
    }
    
    my_hook(context)
    
    assert context['output_file_path'] == expected_path
```

### Integration Testing

Test hooks with actual CLI commands:

```bash
# Create test hook
echo 'def add_suffix(ctx): ctx["output_file_path"] = ctx["output_file_path"].with_stem(ctx["output_file_path"].stem + "_test")' > test_hook.py

# Test with CLI
efemel process config.py --out output --hooks test_hook.py

# Verify output
ls output/  # Should show config_test.json
```

## Hook Best Practices

### 1. Keep Functions Small
Each hook function should have a single responsibility.

### 2. Handle Errors Gracefully
```python
def safe_transform(context):
    try:
        # Transformation logic
        pass
    except Exception as e:
        print(f"Hook warning: {e}")
        # Continue processing
```

### 3. Document Hook Functions
```python
def transform_path(context):
    """
    Transform output path for specific requirements.
    
    Modifies:
        context['output_file_path']: Updated output path
    
    Requires:
        context['input_file_path']: Source file path
    """
    pass
```

### 4. Use Descriptive Names
- `add_timestamp` instead of `transform`
- `validate_config` instead of `check`
- `organize_by_type` instead of `sort`

### 5. Test Edge Cases
- Empty paths
- Missing context keys
- File system permissions
- Invalid path characters

## Hook Reference

### Available Hook Points

| Hook Point | When Called | Context Parameters |
|------------|-------------|-------------------|
| `output_filename` | Before writing each output file | `input_file_path`, `output_file_path`, `output_dir`, `env` |

### Context Object Reference

The context dictionary contains all processing information and can be modified by hooks:

```python
context = {
    'input_file_path': Path,      # Source Python file
    'output_file_path': Path,     # Target output file (modifiable)
    'output_dir': Path,           # Base output directory
    'env': str,                   # Environment name (optional)
}
```

## Future Hook Points

Planned hook points for future versions:

- `before_read`: Called before reading input files
- `after_extract`: Called after extracting dictionaries
- `before_transform`: Called before JSON transformation
- `after_write`: Called after writing output files
