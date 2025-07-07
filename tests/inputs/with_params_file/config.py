"""Test configuration file that uses parameters from params file."""

# Main application configuration
main_config = {
  "app_name": globals().get("app_name", "default-app"),
  "version": globals().get("version", "1.0.0"),
  "debug": globals().get("debug_mode", False),
  "port": globals().get("port", 3000),
  "memory_mb": globals().get("memory_mb", 512),
  "cache_ttl": globals().get("cache_ttl", 300),
}

# Database configuration
database_config = globals().get("database_config", {"host": "localhost", "port": 5432})
db_settings = database_config.copy()
db_settings["timeout"] = globals().get("timeout_seconds", 30)

# API configuration
api_endpoints = globals().get("api_endpoints", ["https://localhost:8000"])
api_config = {
  "endpoints": api_endpoints,
  "timeout": globals().get("timeout_seconds", 30),
  "max_retries": globals().get("max_retries", 3),
  "default_endpoint": api_endpoints[0] if api_endpoints else None,
}

# Complete application configuration
app_configuration = {"main": main_config, "database": db_settings, "api": api_config}
