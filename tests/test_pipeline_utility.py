"""
Test Pipeline utility methods.

This module contains tests for Pipeline utility operations
including passthrough, apply, flatten, and chunked processing.
"""

from efemel.pipeline import Pipeline
from efemel.pipeline import PipelineItem


class TestPipelineUtility:
  """Test Pipeline utility methods."""

  def test_passthrough(self):
    """Test passthrough method."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Passthrough should return the same pipeline
    result = pipeline.passthrough()
    assert result is pipeline

    # Data should be unchanged
    assert result.to_list() == [1, 2, 3, 4, 5]

  def test_apply_function(self):
    """Test apply with single function."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    def double_pipeline(p):
      return p.map(lambda x: x * 2)

    result = pipeline.apply(double_pipeline)
    assert result.to_list() == [2, 4, 6, 8, 10]

  def test_flatten_basic(self):
    """Test basic flatten operation."""
    pipeline = Pipeline([[1, 2], [3, 4], [5]])

    result = pipeline.flatten()
    assert result.to_list() == [1, 2, 3, 4, 5]

  def test_flatten_empty_lists(self):
    """Test flatten with empty lists."""
    pipeline = Pipeline([[], [1, 2], [], [3]])

    result = pipeline.flatten()
    assert result.to_list() == [1, 2, 3]

  def test_flatten_nested_tuples(self):
    """Test flatten with nested tuples."""
    pipeline = Pipeline([(1, 2), (3, 4, 5), (6,)])

    result = pipeline.flatten()
    assert result.to_list() == [1, 2, 3, 4, 5, 6]

  def test_flatten_chunked_processing(self):
    """Test that flatten maintains chunked processing and doesn't consume entire pipeline."""

    # Create a large dataset that would cause OOM if consumed all at once
    def generate_nested_data():
      for i in range(1000):
        yield [i * 2, i * 2 + 1]

    # Use small chunk size to verify chunked processing
    pipeline = Pipeline(generate_nested_data(), chunk_size=10)
    result = pipeline.flatten()

    # Verify first few elements without consuming the entire pipeline
    first_10 = []
    count = 0
    for item in result:
      first_10.append(item)
      count += 1
      if count >= 10:
        break

    assert first_10 == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

  def test_flatten_preserves_chunk_structure(self):
    """Test that flatten preserves chunked structure."""
    # Create pipeline with known chunk structure
    data = [[1, 2], [3, 4], [5, 6], [7, 8]]
    pipeline = Pipeline(data, chunk_size=2)  # 2 sublists per chunk

    result = pipeline.flatten()

    # Verify the result is correct
    assert result.to_list() == [1, 2, 3, 4, 5, 6, 7, 8]

  def test_flatten_maintains_chunk_size(self):
    """Test that flatten maintains the original chunk_size setting."""
    # Create test data with varying sizes of sublists
    data = [[1, 2], [3, 4, 5], [6], [7, 8, 9, 10]]
    chunk_size = 3
    pipeline = Pipeline(data, chunk_size=chunk_size)

    # Flatten the pipeline
    flattened = pipeline.flatten()

    # Verify chunk_size is preserved
    assert flattened.chunk_size == chunk_size

    # Collect chunks to verify structure
    chunks = []
    for chunk in flattened.generator:
      chunks.append(chunk)

    # Verify all chunks except the last have the expected size
    for i, chunk in enumerate(chunks[:-1]):
      assert len(chunk) == chunk_size, f"Chunk {i} has size {len(chunk)}, expected {chunk_size}"

    # Last chunk can be smaller than chunk_size
    if chunks:
      assert len(chunks[-1]) <= chunk_size, f"Last chunk has size {len(chunks[-1])}, should be <= {chunk_size}"

    # Verify the final result is correct
    result = []
    for chunk in chunks:
      result.extend(chunk)

    # This is showing the internal representation of the data wheresecond value of the Tuple is the exception
    assert result == [
      PipelineItem(1, None, {"has_errors": False, "errors": []}),
      PipelineItem(2, None, {"has_errors": False, "errors": []}),
      PipelineItem(3, None, {"has_errors": False, "errors": []}),
      PipelineItem(4, None, {"has_errors": False, "errors": []}),
      PipelineItem(5, None, {"has_errors": False, "errors": []}),
      PipelineItem(6, None, {"has_errors": False, "errors": []}),
      PipelineItem(7, None, {"has_errors": False, "errors": []}),
      PipelineItem(8, None, {"has_errors": False, "errors": []}),
      PipelineItem(9, None, {"has_errors": False, "errors": []}),
      PipelineItem(10, None, {"has_errors": False, "errors": []}),
    ]
