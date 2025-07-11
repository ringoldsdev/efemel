"""
Test Pipeline tap functionality.

This module contains tests for Pipeline tap operations
including side effects, chaining, and data integrity.
"""

from efemel.pipeline import Pipeline


class TestPipelineTap:
  """Test Pipeline tap functionality."""

  def test_tap_basic(self):
    """Test basic tap operations."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    side_effects = []

    # Tap to collect side effects
    result = pipeline.tap(side_effects.append)
    result_list = result.to_list()

    assert result_list == [1, 2, 3, 4, 5]
    assert side_effects == [1, 2, 3, 4, 5]

  def test_tap_with_print(self):
    """Test tap with print (no assertion needed, just verify it works)."""
    pipeline = Pipeline([1, 2, 3])

    # This should not raise any exceptions
    result = pipeline.tap(lambda x: None)  # Mock print
    assert result.to_list() == [1, 2, 3]

  def test_tap_chaining(self):
    """Test tap in a chain of operations."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    side_effects = []

    # Tap in middle of chain
    result = pipeline.map(lambda x: x * 2).tap(side_effects.append).filter(lambda x: x > 5)

    result_list = result.to_list()

    assert result_list == [6, 8, 10]
    assert side_effects == [2, 4, 6, 8, 10]

  def test_tap_doesnt_modify_pipeline(self):
    """Test that tap doesn't modify the pipeline data."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Tap with function that would modify if it could
    result = pipeline.tap(lambda x: x * 1000)

    # Data should be unchanged
    assert result.to_list() == [1, 2, 3, 4, 5]
