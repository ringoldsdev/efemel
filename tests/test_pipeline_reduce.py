"""
Test Pipeline reduce functionality.

This module contains tests for Pipeline reduce operations
including basic reduction, string operations, and edge cases.
"""

from efemel.pipeline import Pipeline


class TestPipelineReduce:
  """Test Pipeline reduce functionality."""

  def test_reduce_basic(self):
    """Test basic reduce operations."""
    # Sum all numbers
    pipeline1 = Pipeline([1, 2, 3, 4, 5])
    sum_result = pipeline1.reduce(lambda acc, x: acc + x, 0)
    assert sum_result.first() == 15

    # Multiply all numbers - use fresh pipeline
    pipeline2 = Pipeline([1, 2, 3, 4, 5])
    product_result = pipeline2.reduce(lambda acc, x: acc * x, 1)
    assert product_result.first() == 120

  def test_reduce_with_strings(self):
    """Test reduce with string data."""
    # Concatenate strings
    pipeline1 = Pipeline(["hello", "world", "python"])
    concat_result = pipeline1.reduce(lambda acc, x: acc + " " + x, "")
    assert concat_result.first() == " hello world python"

    # Join with commas - use fresh pipeline
    pipeline2 = Pipeline(["hello", "world", "python"])
    join_result = pipeline2.reduce(lambda acc, x: acc + "," + x if acc else x, "")
    assert join_result.first() == "hello,world,python"

  def test_reduce_empty_pipeline(self):
    """Test reduce on empty pipeline."""
    empty_pipeline = Pipeline([])

    # Reduce should return initial value
    result = empty_pipeline.reduce(lambda acc, x: acc + x, 10)
    assert result.first() == 10

  def test_reduce_single_item(self):
    """Test reduce with single item."""
    single_pipeline = Pipeline([42])

    # Should combine initial value with single item
    result = single_pipeline.reduce(lambda acc, x: acc + x, 10)
    assert result.first() == 52
