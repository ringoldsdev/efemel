"""Test configuration file that uses parameters from params file."""

# Main application configuration
main_config = {
  "app_name": app_name,
  "version": version,
  "debug": debug_mode,
  "port": port,
  "memory_mb": memory_mb,
  "cache_ttl": cache_ttl,
}

# Database configuration
db_settings = database_config.copy()
db_settings["timeout"] = timeout_seconds

# API configuration
api_config = {
  "endpoints": api_endpoints,
  "timeout": timeout_seconds,
  "max_retries": max_retries,
  "default_endpoint": api_endpoints[0] if api_endpoints else None,
}

# Complete application configuration
app_configuration = {"main": main_config, "database": db_settings, "api": api_config}
