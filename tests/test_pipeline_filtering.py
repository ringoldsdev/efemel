"""
Test Pipeline filtering functionality.

This module contains tests for Pipeline filtering operations
including basic filtering, chaining, and edge cases.
"""

from efemel.pipeline import Pipeline


class TestPipelineFiltering:
  """Test Pipeline filtering functionality."""

  def test_filter_basic(self):
    """Test basic filtering operations."""
    # Filter even numbers
    pipeline1 = Pipeline([1, 2, 3, 4, 5])
    even_pipeline = pipeline1.filter(lambda x: x % 2 == 0)
    assert even_pipeline.to_list() == [2, 4]

    # Filter numbers greater than 3 - use fresh pipeline
    pipeline2 = Pipeline([1, 2, 3, 4, 5])
    gt3_pipeline = pipeline2.filter(lambda x: x > 3)
    assert gt3_pipeline.to_list() == [4, 5]

  def test_filter_with_strings(self):
    """Test filtering with string data."""
    # Filter strings longer than 4 characters
    pipeline1 = Pipeline(["hello", "world", "python", "test"])
    long_strings = pipeline1.filter(lambda s: len(s) > 4)
    assert long_strings.to_list() == ["hello", "world", "python"]

    # Filter strings starting with 'p' - use fresh pipeline
    pipeline2 = Pipeline(["hello", "world", "python", "test"])
    p_strings = pipeline2.filter(lambda s: s.startswith("p"))
    assert p_strings.to_list() == ["python"]

  def test_filter_empty_result(self):
    """Test filter that results in empty pipeline."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Filter that matches nothing
    empty_result = pipeline.filter(lambda x: x > 10)
    assert empty_result.to_list() == []

  def test_filter_all_pass(self):
    """Test filter where all items pass."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Filter that passes everything
    all_pass = pipeline.filter(lambda x: True)
    assert all_pass.to_list() == [1, 2, 3, 4, 5]

  def test_filter_chaining(self):
    """Test chaining multiple filters."""
    pipeline = Pipeline([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    # Chain filters: even numbers and greater than 5
    result = pipeline.filter(lambda x: x % 2 == 0).filter(lambda x: x > 5)
    assert result.to_list() == [6, 8, 10]
