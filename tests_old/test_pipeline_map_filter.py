"""
Test Pipeline map and filter combinations.

This module contains tests for combining mapping and filtering operations
in various orders and combinations.
"""

from efemel.pipeline import Pipeline


class TestPipelineMapFilter:
  """Test Pipeline map and filter combinations."""

  def test_map_then_filter(self):
    """Test mapping then filtering."""
    pipeline = Pipeline()

    # Double numbers, then filter even results
    result = pipeline.map(lambda x: x * 2).filter(lambda x: x % 2 == 0)
    assert result.to_list([1, 2, 3, 4, 5]) == [2, 4, 6, 8, 10]

  def test_filter_then_map(self):
    """Test filtering then mapping."""
    pipeline = Pipeline()

    # Filter even numbers, then double them
    result = pipeline.filter(lambda x: x % 2 == 0).map(lambda x: x * 2)
    assert result.to_list([1, 2, 3, 4, 5]) == [4, 8]

  def test_complex_map_filter_chain(self):
    """Test complex chaining of map and filter operations."""
    pipeline = Pipeline()

    # Complex chain: filter odd, multiply by 3, filter > 10
    result = (
      pipeline.filter(lambda x: x % 2 == 1)  # [1, 3, 5, 7, 9]
      .map(lambda x: x * 3)  # [3, 9, 15, 21, 27]
      .filter(lambda x: x > 10)
    )  # [15, 21, 27]

    assert result.to_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == [15, 21, 27]
