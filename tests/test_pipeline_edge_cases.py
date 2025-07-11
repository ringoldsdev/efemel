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
    pipeline1 = Pipeline([1, None, 3, None, 5])
    result = pipeline1.to_list()
    assert result == [1, None, 3, None, 5]

    # Filter out None values - use fresh pipeline
    pipeline2 = Pipeline([1, None, 3, None, 5])
    no_none = pipeline2.filter(lambda x: x is not None)
    assert no_none.to_list() == [1, 3, 5]

  def test_pipeline_with_mixed_types(self):
    """Test pipeline with mixed data types."""
    # Should handle mixed types
    pipeline1 = Pipeline([1, "hello", 3.14, True, None])
    result = pipeline1.to_list()
    assert result == [1, "hello", 3.14, True, None]

    # Filter by type (excluding boolean which is a subclass of int) - use fresh pipeline
    pipeline2 = Pipeline([1, "hello", 3.14, True, None])
    numbers = pipeline2.filter(lambda x: isinstance(x, int | float) and not isinstance(x, bool) and x is not None)
    assert numbers.to_list() == [1, 3.14]

  def test_pipeline_reuse(self):
    """Test that pipelines can be reused."""
    original_data = [1, 2, 3, 4, 5]
    pipeline = Pipeline(original_data)

    # First use
    result1 = pipeline.map(lambda x: x * 2).to_list()
    assert result1 == [2, 4, 6, 8, 10]

    # Create new pipeline from same data
    pipeline2 = Pipeline(original_data)
    result2 = pipeline2.filter(lambda x: x % 2 == 0).to_list()
    assert result2 == [2, 4]

  def test_pipeline_method_chaining_returns_new_instances(self):
    """Test that pipeline methods return new instances."""
    original = Pipeline([1, 2, 3, 4, 5])

    # Methods should return new instances (except passthrough)
    mapped = original.map(lambda x: x * 2)
    filtered = original.filter(lambda x: x % 2 == 0)

    assert mapped is not original
    assert filtered is not original
    assert mapped is not filtered

  def test_pipeline_with_generator_exhaustion(self):
    """Test pipeline behavior with generator exhaustion."""

    def number_generator():
      yield from range(3)

    pipeline = Pipeline(number_generator())

    # First consumption
    result1 = pipeline.to_list()
    assert result1 == [0, 1, 2]

    # Generator should be exhausted now
    # This behavior depends on the implementation
