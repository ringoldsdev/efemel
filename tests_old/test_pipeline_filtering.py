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
    pipeline1 = Pipeline().filter(lambda x: x % 2 == 0)
    assert pipeline1.to_list([1, 2, 3, 4, 5]) == [2, 4]

    # Filter numbers greater than 3 - use fresh pipeline
    pipeline2 = Pipeline().filter(lambda x: x > 3)
    assert pipeline2.to_list([1, 2, 3, 4, 5]) == [4, 5]

  def test_filter_with_strings(self):
    """Test filtering with string data."""
    # Filter strings longer than 4 characters
    pipeline1 = Pipeline().filter(lambda s: len(s) > 4)
    assert pipeline1.to_list(["hello", "world", "python", "test"]) == ["hello", "world", "python"]

    # Filter strings starting with 'p' - use fresh pipeline
    pipeline2 = Pipeline().filter(lambda s: s.startswith("p"))
    assert pipeline2.to_list(["hello", "world", "python", "test"]) == ["python"]

  def test_filter_empty_result(self):
    """Test filter that results in empty pipeline."""
    pipeline = Pipeline()

    # Filter that matches nothing
    empty_result = pipeline.filter(lambda x: x > 10)
    assert empty_result.to_list([1, 2, 3, 4, 5]) == []

  def test_filter_all_pass(self):
    """Test filter where all items pass."""
    pipeline = Pipeline()

    # Filter that passes everything
    all_pass = pipeline.filter(lambda x: True)
    assert all_pass.to_list([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

  def test_filter_chaining(self):
    """Test chaining multiple filters."""
    pipeline = Pipeline()

    # Chain filters: even numbers and greater than 5
    result = pipeline.filter(lambda x: x % 2 == 0).filter(lambda x: x > 5)
    assert result.to_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == [6, 8, 10]
