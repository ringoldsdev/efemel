# API Reference

This document provides detailed API reference for Efemel's Python modules and classes.

## Core Modules

### efemel.cli

The CLI interface module built with Click.

#### Functions

##### `cli()`
Main CLI entry point.

##### `process(file_pattern, out, flatten, cwd, env, workers, hooks)`
Process Python files and extract dictionaries.

**Parameters:**
- `file_pattern` (str): Glob pattern for input files
- `out` (str): Output directory path
- `flatten` (bool): Whether to flatten directory structure
- `cwd` (str, optional): Working directory
- `env` (str, optional): Environment name
- `workers` (int): Number of parallel workers
- `hooks` (str, optional): Path to hooks file or directory

### efemel.process

Core file processing functionality.

#### Functions

##### `process_py_file(file_path, env=None)`
Extract dictionary variables from a Python file.

**Parameters:**
- `file_path` (Path): Path to Python file
- `env` (str, optional): Environment for imports

**Returns:**
- `dict`: Extracted dictionary variables

**Example:**
```python
from pathlib import Path
from efemel.process import process_py_file

data = process_py_file(Path('config.py'), env='prod')
print(data)  # {'config': {...}, 'settings': {...}}
```

### efemel.hooks_manager

Hook system management.

#### Classes

##### `HooksManager`

Manages hook registration and execution.

**Methods:**

###### `__init__()`
Initialize empty hooks manager.

###### `load_user_file(file_path)`
Load hooks from a Python file.

**Parameters:**
- `file_path` (str): Path to hooks file

###### `load_hooks_directory(hooks_dir)`
Load all hooks from a directory.

**Parameters:**
- `hooks_dir` (str): Path to directory containing hooks

###### `call(hook_name, context, return_params)`
Execute all hooks for a given hook name.

**Parameters:**
- `hook_name` (str): Name of hook to execute
- `context` (dict): Context data for hooks
- `return_params` (list): Parameters to return

**Returns:**
- `dict` or `tuple`: Updated context or specified parameters

###### `add(hook_name, hook_func)`
Manually register a hook function.

**Parameters:**
- `hook_name` (str): Hook name
- `hook_func` (callable): Hook function

###### `add_before(hook_name, hook_func)`
Register a hook to run before others.

**Parameters:**
- `hook_name` (str): Hook name  
- `hook_func` (callable): Hook function

###### `remove(hook_name, hook_func=None)`
Remove hook(s).

**Parameters:**
- `hook_name` (str): Hook name
- `hook_func` (callable, optional): Specific function to remove

###### `clear()`
Remove all registered hooks.

###### `list()`
Get all registered hooks.

**Returns:**
- `dict`: Mapping of hook names to function names

###### `get_count(hook_name)`
Get number of functions for a hook.

**Parameters:**
- `hook_name` (str): Hook name

**Returns:**
- `int`: Number of registered functions

**Example:**
```python
from efemel.hooks_manager import HooksManager

# Create manager
hm = HooksManager()

# Load hooks from file
hm.load_user_file('my_hooks.py')

# Load hooks from directory
hm.load_hooks_directory('hooks/')

# Execute hooks
context = {'input_path': 'test.py', 'output_path': 'test.json'}
result = hm.call('output_filename', context, ['output_path'])
```

## Reader Modules

### efemel.readers.local

Local filesystem file reading.

#### Classes

##### `LocalReader`

Reads files from local filesystem.

**Methods:**

###### `__init__(cwd=None)`
Initialize reader with working directory.

**Parameters:**
- `cwd` (str, optional): Working directory

###### `read(glob_pattern)`
Find files matching pattern.

**Parameters:**
- `glob_pattern` (str): Glob pattern (must end with .py)

**Yields:**
- `Path`: File paths matching pattern

**Example:**
```python
from efemel.readers.local import LocalReader

reader = LocalReader('/path/to/project')
for file_path in reader.read('**/*.py'):
    print(file_path)
```

## Transformer Modules

### efemel.transformers.json

JSON transformation functionality.

#### Classes

##### `JSONTransformer`

Transforms Python data to JSON.

**Attributes:**
- `suffix` (str): File extension ('.json')

**Methods:**

###### `__init__()`
Initialize JSON transformer.

###### `transform(data)`
Convert data to JSON string.

**Parameters:**
- `data` (dict): Python data to transform

**Returns:**
- `str`: JSON string representation

**Example:**
```python
from efemel.transformers.json import JSONTransformer

transformer = JSONTransformer()
json_data = transformer.transform({'key': 'value'})
print(json_data)  # '{"key": "value"}'
```

## Writer Modules

### efemel.writers.local

Local filesystem output writing.

#### Classes

##### `LocalWriter`

Writes output files to local filesystem.

**Methods:**

###### `__init__(output_dir, base_dir)`
Initialize writer.

**Parameters:**
- `output_dir` (str): Output directory path
- `base_dir` (Path): Base directory for relative paths

###### `write(data, file_path)`
Write data to file.

**Parameters:**
- `data` (str): Data to write
- `file_path` (Path): Output file path

**Returns:**
- `Path`: Written file path

**Example:**
```python
from pathlib import Path
from efemel.writers.local import LocalWriter

writer = LocalWriter('output/', Path.cwd())
written_path = writer.write('{"test": true}', Path('test.json'))
```

## Built-in Hooks

### efemel.hooks.output_filename

Built-in output filename transformation hooks.

#### Functions

##### `ensure_output_path(context)`
Ensure output file has .json extension.

##### `flatten_output_path(context)`
Flatten directory structure into filename.

**Example:**
```python
from efemel.hooks.output_filename import flatten_output_path

context = {
    'output_file_path': Path('dir/subdir/file.json')
}
flatten_output_path(context)
print(context['output_file_path'])  # 'dir_subdir_file.json'
```

## Type Definitions

### Common Types

```python
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# Hook function signature
HookFunction = Callable[[Dict[str, Any]], None]

# Context dictionary for hooks
HookContext = Dict[str, Any]

# File processing result
ProcessingResult = Dict[str, Any]
```

## Error Handling

### Common Exceptions

#### `FileNotFoundError`
Raised when input files or directories don't exist.

#### `ValueError`
Raised for invalid parameters or configurations.

#### `ImportError` 
Raised when processing files with import issues.

### Example Error Handling

```python
from efemel.process import process_py_file
from pathlib import Path

try:
    result = process_py_file(Path('config.py'))
except FileNotFoundError:
    print("Config file not found")
except ImportError as e:
    print(f"Import error in config: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Environment Integration

### Environment Variables

Efemel respects these environment variables:

- `EFEMEL_WORKERS`: Default number of workers
- `EFEMEL_OUTPUT_DIR`: Default output directory
- `EFEMEL_HOOKS_DIR`: Default hooks directory

### Programmatic Usage

```python
from pathlib import Path
from efemel.hooks_manager import HooksManager
from efemel.readers.local import LocalReader
from efemel.transformers.json import JSONTransformer
from efemel.writers.local import LocalWriter
from efemel.process import process_py_file

# Setup components
hooks_manager = HooksManager()
reader = LocalReader('/project')
transformer = JSONTransformer()
writer = LocalWriter('output/', Path('/project'))

# Load hooks
hooks_manager.load_hooks_directory('hooks/')

# Process files
for file_path in reader.read('**/*.py'):
    # Extract data
    data = process_py_file(file_path)
    
    # Transform to JSON
    json_data = transformer.transform(data)
    
    # Apply hooks to determine output path
    context = {
        'input_file_path': file_path,
        'output_file_path': file_path.with_suffix('.json'),
        'output_dir': Path('output/'),
        'env': 'production'
    }
    
    output_path, = hooks_manager.call(
        'output_filename', context, ['output_file_path']
    )
    
    # Write output
    written_file = writer.write(json_data, output_path)
    print(f"Wrote: {written_file}")
```
