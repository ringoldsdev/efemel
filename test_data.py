#!/usr/bin/env python3
"""
Test file for the process command.
"""

# Public dictionaries that should be extracted
config = {
    "name": "test_app",
    "version": "1.0.0",
    "debug": True,
    "features": ["auth", "api", "ui"],
}

settings = {
    "database": {"host": "localhost", "port": 5432, "name": "app_db"},
    "cache": {"type": "redis", "ttl": 3600},
}

user_data = {
    "admin": {"name": "Admin User", "role": "admin"},
    "guest": {"name": "Guest User", "role": "guest"},
}

# Private variables (should be ignored)
_private_dict = {"secret": "value"}
__dunder_dict = {"internal": "data"}

# Non-dictionary variables (should be ignored)
APP_NAME = "test_app"
VERSION = "1.0.0"
enabled_features = ["auth", "api"]


def some_function():
    """A function that should be ignored."""
    return "test"


class SomeClass:
    """A class that should be ignored."""

    pass
