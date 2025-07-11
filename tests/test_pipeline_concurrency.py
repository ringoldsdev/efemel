"""
Test Pipeline concurrency functionality.

This module contains tests for Pipeline concurrent operations
including basic concurrency and context isolation.
"""

import pytest

from efemel.pipeline import CompoundError
from efemel.pipeline import Pipeline


class TestPipelineConcurrency:
  """Test Pipeline concurrency functionality."""

  def test_concurrent(self):
    # Create a simple pipeline

    def _double_pipeline(p: Pipeline[int]):
      return p.map(lambda x: x * 2)

    result = Pipeline(range(0, 5), 1).concurrent(_double_pipeline, 5).to_list()

    # Check if all numbers are doubled
    assert result == [0, 2, 4, 6, 8]

  def test_concurrent_consumer(self):
    # Create a simple pipeline

    items = []

    def dummy_consumer(p: Pipeline[int]):
      return p.tap(lambda x: items.append(x))

    Pipeline(range(0, 5), 1).concurrent(dummy_consumer, 5).noop()

    # Check if all numbers are consumed
    assert items == [0, 1, 2, 3, 4]

  def test_concurrent_context_isolation(self):
    """Test that concurrent processing properly isolates and merges contexts."""

    # Create a pipeline with some data
    data = list(range(100))  # Large enough to ensure multiple chunks
    pipeline = Pipeline(data, chunk_size=10)  # Force multiple chunks

    def error_prone_pipeline(p):
      """A pipeline that will cause errors on certain values."""
      return p.map(lambda x: x if x % 7 != 0 else 1 / 0)  # Error on multiples of 7

    def safe_pipeline(p):
      """A pipeline that should work without errors."""
      return p.map(lambda x: x * 2)

    # Test with error-prone pipeline
    with pytest.raises(CompoundError):
      pipeline.concurrent(error_prone_pipeline, max_workers=4).to_list()

    # Check that the context properly recorded errors
    assert pipeline.context["has_errors"]

    # Test with safe pipeline
    safe_data = list(range(50))
    safe_pipeline_obj = Pipeline(safe_data, chunk_size=5)

    result = safe_pipeline_obj.concurrent(safe_pipeline, max_workers=4).to_list()
    expected = [x * 2 for x in safe_data]

    assert result == expected
    assert not safe_pipeline_obj.context["has_errors"]

  def test_concurrent_vs_sequential(self):
    """Test that concurrent and sequential processing produce the same results."""
    data = list(range(20))

    def transform_pipeline(p):
      return p.map(lambda x: x * 3).filter(lambda x: x % 2 == 0)

    # Sequential
    sequential_result = Pipeline(data).apply(transform_pipeline).to_list()

    # Concurrent
    concurrent_result = Pipeline(data, chunk_size=5).concurrent(transform_pipeline, max_workers=3).to_list()

    assert sequential_result == concurrent_result

  def test_concurrent_with_errors_maintains_order(self):
    """Test that concurrent processing maintains order even with errors."""
    data = list(range(20))

    def error_prone_pipeline(p):
      """Creates errors on multiples of 5."""
      return p.map(lambda x: x if x % 5 != 0 else 1 / 0)

    # Test ordered processing
    pipeline = Pipeline(data, chunk_size=3)

    with pytest.raises(CompoundError) as exc_info:
      pipeline.concurrent(error_prone_pipeline, max_workers=2, ordered=True).to_list()

    # Should have errors for multiples of 5: 0, 5, 10, 15
    assert len(exc_info.value.errors) == 4

  def test_concurrent_unordered(self):
    """Test unordered concurrent processing."""
    data = list(range(20))

    def simple_transform(p):
      return p.map(lambda x: x * 2)

    # Unordered processing
    pipeline = Pipeline(data, chunk_size=4)
    result = pipeline.concurrent(simple_transform, max_workers=3, ordered=False).to_list()

    # Results should be correct but may be out of order
    expected = [x * 2 for x in data]
    assert sorted(result) == sorted(expected)

  def test_concurrent_context_thread_safety(self):
    """Test that context updates are thread-safe during concurrent processing."""
    data = list(range(100))

    def context_aware_pipeline(p):
      """Pipeline that interacts with context."""
      return p.map(lambda x, ctx: x * 2 if not ctx["has_errors"] else x)

    pipeline = Pipeline(data, chunk_size=10)
    result = pipeline.concurrent(context_aware_pipeline, max_workers=4).to_list()

    # Should get consistent results despite concurrent access to context
    expected = [x * 2 for x in data]
    assert result == expected
    assert not pipeline.context["has_errors"]
