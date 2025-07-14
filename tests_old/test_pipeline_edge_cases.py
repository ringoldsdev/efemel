"""
Test Pipeline edge cases and error conditions.

This module contains tests for Pipeline edge cases including
None values, mixed types, reuse, and generator behavior.
"""

from efemel.pipeline import Pipeline


class TestPipelineEdgeCases:
  """Test Pipeline edge cases and error conditions."""

  def test_pipeline_with_none_values(self):
    """Test pipeline with None values."""
    # Should handle None values properly
    pipeline = Pipeline()
    result = pipeline.to_list([1, None, 3, None, 5])
    assert result == [1, None, 3, None, 5]

    # Filter out None values - use fresh pipeline
    pipeline2 = Pipeline()
    no_none = pipeline2.filter(lambda x: x is not None)
    assert no_none.to_list([1, None, 3, None, 5]) == [1, 3, 5]

  def test_pipeline_with_mixed_types(self):
    """Test pipeline with mixed data types."""
    # Should handle mixed types
    pipeline = Pipeline()
    result = pipeline.to_list([1, "hello", 3.14, True, None])
    assert result == [1, "hello", 3.14, True, None]

    # Filter by type (excluding boolean which is a subclass of int) - use fresh pipeline
    pipeline2 = Pipeline()
    numbers = pipeline2.filter(lambda x: isinstance(x, int | float) and not isinstance(x, bool) and x is not None)
    assert numbers.to_list([1, "hello", 3.14, True, None]) == [1, 3.14]

  def test_pipeline_reuse(self):
    """Test that pipelines can be reused."""
    original_data = [1, 2, 3, 4, 5]
    pipeline = Pipeline()

    # First use
    result1 = pipeline.map(lambda x: x * 2).to_list(original_data)
    assert result1 == [2, 4, 6, 8, 10]

    # Pipeline should be reusable with different data
    new_data = [10, 20, 30]
    result2 = pipeline.to_list(new_data)  # Same pipeline, different data
    assert result2 == [20, 40, 60]

  def test_pipeline_method_chaining_returns_new_instances(self):
    """Test that pipeline methods return new instances."""
    # Create separate pipelines for different operations
    mapped = Pipeline().map(lambda x: x * 2)
    filtered = Pipeline().filter(lambda x: x % 2 == 0)

    # Test that they work correctly with different transformations
    assert mapped.to_list([1, 2, 3, 4, 5]) == [2, 4, 6, 8, 10]
    assert filtered.to_list([1, 2, 3, 4, 5]) == [2, 4]
    assert mapped is not filtered

  def test_pipeline_with_generator_exhaustion(self):
    """Test pipeline behavior with generator exhaustion."""

    def number_generator():
      yield from range(3)

    pipeline = Pipeline()

    # First consumption
    result1 = pipeline.to_list(number_generator())
    assert result1 == [0, 1, 2]

    # New generator for second consumption (generators are single-use)
    result2 = pipeline.to_list(number_generator())
    assert result2 == [0, 1, 2]
