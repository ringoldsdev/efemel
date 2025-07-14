"""
Test Pipeline mapping functionality.

This module contains tests for Pipeline mapping operations
including basic mapping, type transformations, and chaining.
"""

from efemel.pipeline import Pipeline


class TestPipelineMapping:
  """Test Pipeline mapping functionality."""

  def test_map_basic(self):
    """Test basic mapping operations."""
    # Double each number
    pipeline1 = Pipeline().map(lambda x: x * 2)
    assert pipeline1.to_list([1, 2, 3, 4, 5]) == [2, 4, 6, 8, 10]

    # Square each number - use fresh pipeline
    pipeline2 = Pipeline().map(lambda x: x**2)
    assert pipeline2.to_list([1, 2, 3, 4, 5]) == [1, 4, 9, 16, 25]

  def test_map_type_transformation(self):
    """Test mapping with type transformation."""
    # Convert numbers to strings
    pipeline1 = Pipeline().map(str)
    assert pipeline1.to_list([1, 2, 3, 4, 5]) == ["1", "2", "3", "4", "5"]

    # Convert to boolean (non-zero is True) - use fresh pipeline
    pipeline2 = Pipeline().map(bool)
    assert pipeline2.to_list([1, 2, 3, 4, 5]) == [True, True, True, True, True]

  def test_map_with_strings(self):
    """Test mapping with string data."""
    # Convert to uppercase
    pipeline1 = Pipeline().map(str.upper)
    assert pipeline1.to_list(["hello", "world", "python"]) == ["HELLO", "WORLD", "PYTHON"]

    # Get string lengths - use fresh pipeline
    pipeline2 = Pipeline().map(len)
    assert pipeline2.to_list(["hello", "world", "python"]) == [5, 5, 6]

  def test_map_chaining(self):
    """Test chaining multiple map operations."""
    pipeline = Pipeline()

    # Chain maps: double, then add 1
    result = pipeline.map(lambda x: x * 2).map(lambda x: x + 1)
    assert result.to_list([1, 2, 3, 4, 5]) == [3, 5, 7, 9, 11]

  def test_map_empty_pipeline(self):
    """Test mapping on empty pipeline."""
    pipeline = Pipeline()

    # Map should return empty result
    result = pipeline.map(lambda x: x * 2)
    assert result.to_list([]) == []
