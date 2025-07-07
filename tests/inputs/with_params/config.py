"""Test file for custom parameters functionality."""

# This will reference parameters passed from CLI
app_config = {
  "name": globals().get("app_name", "default-app"),  # This should come from CLI --param app_name=myapp
  "version": globals().get("version", "1.0.0"),  # This should come from CLI --param version=1.0.0
  "debug": globals().get("debug_mode", False),  # This should come from CLI --param debug_mode=true
  "port": globals().get("port", 3000),  # This should come from CLI --param port=8080
}

# Test complex parameter (JSON object)
if "database_config" in globals():
  database = database_config  # noqa: F821
else:
  database = {"host": "localhost", "port": 5432}

# Test parameter with fallback
max_connections = globals().get("max_connections", 100)

# Simple calculation using parameters
total_memory = globals().get("memory_mb", 0) * 1024 * 1024
