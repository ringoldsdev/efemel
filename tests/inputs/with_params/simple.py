"""Simple test file for custom parameters functionality."""

# Direct usage - parameters are injected as globals before execution
# When called without params, these will cause NameError
# When called with params, they will be available as globals

try:
    # This should work when parameters are passed
    result = {
        "app_name": app_name,
        "version": version,
        "debug": debug_mode,
        "port": port
    }
except NameError as e:
    # Fallback when no parameters are passed
    result = {
        "error": f"Missing parameter: {e}",
        "message": "Use --param to pass parameters"
    }

# Test complex parameter
try:
    config = database_config
except NameError:
    config = {"host": "localhost", "port": 5432}

# Test numeric parameter
try:
    memory_bytes = memory_mb * 1024 * 1024
except NameError:
    memory_bytes = 0
