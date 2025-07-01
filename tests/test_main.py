"""
Tests for the main module.
"""

from efemel.main import hello_world


def test_hello_world():
  """Test the hello_world function."""
  result = hello_world()
  assert result == "Hello, World from efemel!"
  assert isinstance(result, str)
