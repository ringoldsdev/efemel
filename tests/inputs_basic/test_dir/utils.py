"""
Test file with no dictionaries.
"""

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
