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
    pipeline1 = Pipeline()
    sum_result = pipeline1.reduce([1, 2, 3, 4, 5], function=lambda acc, x: acc + x, initial=0)
    assert sum_result == 15

    # Multiply all numbers - use fresh pipeline
    pipeline2 = Pipeline()
    product_result = pipeline2.reduce([1, 2, 3, 4, 5], function=lambda acc, x: acc * x, initial=1)
    assert product_result == 120

  def test_reduce_with_strings(self):
    """Test reduce with string data."""
    # Concatenate strings
    pipeline1 = Pipeline()
    concat_result = pipeline1.reduce(["hello", "world", "python"], function=lambda acc, x: acc + " " + x, initial="")
    assert concat_result == " hello world python"

    # Join with commas - use fresh pipeline
    pipeline2 = Pipeline()
    join_result = pipeline2.reduce(
      ["hello", "world", "python"], function=lambda acc, x: acc + "," + x if acc else x, initial=""
    )
    assert join_result == "hello,world,python"

  def test_reduce_empty_pipeline(self):
    """Test reduce on empty pipeline."""
    pipeline = Pipeline()

    # Reduce should return initial value
    result = pipeline.reduce([], function=lambda acc, x: acc + x, initial=10)
    assert result == 10

  def test_reduce_single_item(self):
    """Test reduce with single item."""
    pipeline = Pipeline()

    # Should combine initial value with single item
    result = pipeline.reduce([42], function=lambda acc, x: acc + x, initial=10)
    assert result == 52
