"""
Test Pipeline utility methods.

This module contains tests for Pipeline utility operations
including apply, flatten, and chunked processing.
"""

from efemel.pipeline import Pipeline


class TestPipelineUtility:
  """Test Pipeline utility methods."""

  def test_apply_function(self):
    """Test apply with pipeline function."""
    pipeline = Pipeline()

    # Create another pipeline to apply
    double_pipeline = Pipeline().map(lambda x: x * 2)
    
    result = pipeline.apply(double_pipeline)
    assert result.to_list([1, 2, 3, 4, 5]) == [2, 4, 6, 8, 10]

  def test_flatten_basic(self):
    """Test basic flatten operation."""
    pipeline = Pipeline()

    result = pipeline.flatten()
    assert result.to_list([[1, 2], [3, 4], [5]]) == [1, 2, 3, 4, 5]

  def test_flatten_empty_lists(self):
    """Test flatten with empty lists."""
    pipeline = Pipeline()

    result = pipeline.flatten()
    assert result.to_list([[], [1, 2], [], [3]]) == [1, 2, 3]

  def test_flatten_nested_tuples(self):
    """Test flatten with nested tuples."""
    pipeline = Pipeline()

    result = pipeline.flatten()
    assert result.to_list([(1, 2), (3, 4, 5), (6,)]) == [1, 2, 3, 4, 5, 6]

  def test_flatten_chunked_processing(self):
    """Test that flatten works with iterators and doesn't consume entire pipeline at once."""
    # Create a generator that yields nested data
    def generate_nested_data():
      for i in range(10):  # Smaller range for easier testing
        yield [i * 2, i * 2 + 1]

    pipeline = Pipeline()
    result = pipeline.flatten()

    # Test the flattened result
    actual = result.to_list(generate_nested_data())
    expected = []
    for i in range(10):
      expected.extend([i * 2, i * 2 + 1])

    assert actual == expected

  def test_flatten_with_chunk_size(self):
    """Test that flatten works correctly with different chunk sizes."""
    # Create pipeline with custom chunk size
    pipeline = Pipeline(chunk_size=3)

    # Test data with varying sizes of sublists
    data = [[1, 2], [3, 4, 5], [6], [7, 8, 9, 10]]

    result = pipeline.flatten()
    assert result.to_list(data) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

  def test_flatten_preserves_chunk_size(self):
    """Test that flatten preserves the original chunk_size setting."""
    chunk_size = 5
    pipeline = Pipeline(chunk_size=chunk_size)

    flattened = pipeline.flatten()

    # Verify chunk_size is preserved
    assert flattened.chunk_size == chunk_size

    # Test with actual data
    data = [[1, 2], [3, 4], [5, 6], [7, 8]]
    result = flattened.to_list(data)
    assert result == [1, 2, 3, 4, 5, 6, 7, 8]
