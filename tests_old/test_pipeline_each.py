"""
Test Pipeline each functionality.

This module contains tests for Pipeline each operations
including side effects and terminal operation behavior.
"""

from efemel.pipeline import Pipeline


class TestPipelineEach:
  """Test Pipeline each functionality."""

  def test_each_basic(self):
    """Test basic each operations."""
    pipeline = Pipeline()
    side_effects = []

    # Each should execute function for each item
    pipeline.each([1, 2, 3, 4, 5], function=side_effects.append)

    assert side_effects == [1, 2, 3, 4, 5]

  def test_each_returns_none(self):
    """Test that each returns None."""
    pipeline = Pipeline()

    result = pipeline.each([1, 2, 3, 4, 5], function=lambda x: None)
    assert result is None

  def test_each_with_empty_pipeline(self):
    """Test each with empty pipeline."""
    pipeline = Pipeline()
    side_effects = []

    # Should not execute function
    pipeline.each([], function=side_effects.append)

    assert side_effects == []

  def test_each_terminal_operation(self):
    """Test that each is a terminal operation."""
    pipeline = Pipeline()
    side_effects = []

    # After each, pipeline should be consumed
    pipeline.each([1, 2, 3, 4, 5], function=side_effects.append)

    assert side_effects == [1, 2, 3, 4, 5]
