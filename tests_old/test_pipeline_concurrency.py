"""
Test Pipeline concurrency functionality.

This module contains tests for Pipeline concurrent operations
including basic concurrency and context isolation.
"""

from efemel.pipeline import Pipeline


class TestPipelineConcurrency:
  """Test Pipeline concurrency functionality."""

  def test_concurrent(self):
    # Create a simple pipeline

    def _double_pipeline(p):
      return p.map(lambda x: x * 2)

    pipeline = Pipeline(chunk_size=1)
    result = list(pipeline.concurrent(range(0, 5), pipeline=_double_pipeline, max_workers=5))

    # Check if all numbers are doubled
    assert result == [0, 2, 4, 6, 8]

  def test_concurrent_consumer(self):
    # Create a simple pipeline

    items = []

    def dummy_consumer(p):
      return p.tap(lambda x: items.append(x))

    pipeline = Pipeline(chunk_size=1)
    list(pipeline.concurrent(range(0, 5), pipeline=dummy_consumer, max_workers=5))

    # Check if all numbers are consumed
    assert items == [0, 1, 2, 3, 4]

  def test_concurrent_vs_sequential(self):
    """Test that concurrent and sequential processing produce the same results."""
    data = list(range(20))

    def transform_pipeline(p):
      return p.map(lambda x: x * 3).filter(lambda x: x % 2 == 0)

    # Sequential
    sequential_pipeline = Pipeline().apply(transform_pipeline)
    sequential_result = sequential_pipeline.to_list(data)

    # Concurrent
    concurrent_pipeline = Pipeline(chunk_size=5)
    concurrent_result = list(concurrent_pipeline.concurrent(data, pipeline=transform_pipeline, max_workers=3))

    assert sequential_result == concurrent_result

  def test_concurrent_unordered(self):
    """Test unordered concurrent processing."""
    data = list(range(20))

    def simple_transform(p):
      return p.map(lambda x: x * 2)

    # Unordered processing
    pipeline = Pipeline(chunk_size=4)
    result = list(pipeline.concurrent(data, pipeline=simple_transform, max_workers=3, ordered=False))

    # Results should be correct but may be out of order
    expected = [x * 2 for x in data]
    assert sorted(result) == sorted(expected)

  def test_concurrent_context_thread_safety(self):
    """Test that context updates are thread-safe during concurrent processing."""
    data = list(range(100))

    def context_aware_pipeline(p):
      """Pipeline that interacts with context."""
      return p.map(lambda x, ctx: x * 2 if not ctx.get("has_errors", False) else x)

    pipeline = Pipeline(chunk_size=10)
    pipeline.context["has_errors"] = False
    result = list(pipeline.concurrent(data, pipeline=context_aware_pipeline, max_workers=4))

    # Should get consistent results despite concurrent access to context
    expected = [x * 2 for x in data]
    assert result == expected
    assert not pipeline.context.get("has_errors", False)
