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
    pipeline1 = Pipeline([1, 2, 3, 4, 5])
    doubled = pipeline1.map(lambda x: x * 2)
    assert doubled.to_list() == [2, 4, 6, 8, 10]

    # Square each number - use fresh pipeline
    pipeline2 = Pipeline([1, 2, 3, 4, 5])
    squared = pipeline2.map(lambda x: x**2)
    assert squared.to_list() == [1, 4, 9, 16, 25]

  def test_map_type_transformation(self):
    """Test mapping with type transformation."""
    # Convert numbers to strings
    pipeline1 = Pipeline([1, 2, 3, 4, 5])
    str_pipeline = pipeline1.map(str)
    assert str_pipeline.to_list() == ["1", "2", "3", "4", "5"]

    # Convert to boolean (non-zero is True) - use fresh pipeline
    pipeline2 = Pipeline([1, 2, 3, 4, 5])
    bool_pipeline = pipeline2.map(bool)
    assert bool_pipeline.to_list() == [True, True, True, True, True]

  def test_map_with_strings(self):
    """Test mapping with string data."""
    # Convert to uppercase
    pipeline1 = Pipeline(["hello", "world", "python"])
    upper_pipeline = pipeline1.map(str.upper)
    assert upper_pipeline.to_list() == ["HELLO", "WORLD", "PYTHON"]

    # Get string lengths - use fresh pipeline
    pipeline2 = Pipeline(["hello", "world", "python"])
    len_pipeline = pipeline2.map(len)
    assert len_pipeline.to_list() == [5, 5, 6]

  def test_map_chaining(self):
    """Test chaining multiple map operations."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Chain maps: double, then add 1
    result = pipeline.map(lambda x: x * 2).map(lambda x: x + 1)
    assert result.to_list() == [3, 5, 7, 9, 11]

  def test_map_empty_pipeline(self):
    """Test mapping on empty pipeline."""
    empty_pipeline = Pipeline([])

    # Map should return empty result
    result = empty_pipeline.map(lambda x: x * 2)
    assert result.to_list() == []
