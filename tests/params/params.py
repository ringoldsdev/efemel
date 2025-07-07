"""Parameters file for testing --params-file functionality."""

# Basic configuration parameters
app_name = "params-file-app"
version = "2.1.0"
debug_mode = False
port = 9090
memory_mb = 1024

# Complex configuration
database_config = {"host": "params-file-db", "port": 5432, "ssl": True, "pool_size": 10}

# Environment-specific settings
api_endpoints = ["https://api.example.com", "https://api-backup.example.com"]

# Computed values
timeout_seconds = 30
max_retries = 3
cache_ttl = timeout_seconds * 60
