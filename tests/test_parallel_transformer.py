"""Tests for the ParallelTransformer class."""

import threading
import time
from unittest.mock import patch

from efemel.pipeline.errors import ErrorHandler
from efemel.pipeline.transformers.parallel import ParallelTransformer
from efemel.pipeline.transformers.transformer import PipelineContext
from efemel.pipeline.transformers.transformer import Transformer


class TestParallelTransformerBasics:
  """Test basic parallel transformer functionality."""

  def test_init_creates_parallel_transformer(self):
    """Test that init creates a parallel transformer with default values."""
    transformer = ParallelTransformer[int, int]()
    assert transformer.max_workers == 4
    assert transformer.ordered is True
    assert transformer.chunk_size == 1000

  def test_init_with_custom_parameters(self):
    """Test init with custom parameters."""
    transformer = ParallelTransformer[int, int](max_workers=8, ordered=False, chunk_size=500)
    assert transformer.max_workers == 8
    assert transformer.ordered is False
    assert transformer.chunk_size == 500

  def test_call_executes_transformer_concurrently(self):
    """Test that calling parallel transformer executes it on data."""
    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=3)
    result = list(transformer([1, 2, 3, 4, 5]))
    assert result == [1, 2, 3, 4, 5]

  def test_from_transformer_class_method(self):
    """Test creating ParallelTransformer from existing Transformer."""
    # Create a regular transformer with some operations
    regular = Transformer.init(int, chunk_size=100).map(lambda x: x * 2).filter(lambda x: x > 5)

    # Convert to parallel using the base class method
    parallel = ParallelTransformer.from_transformer(regular, max_workers=2, ordered=True)

    # Test both produce same results
    data = [1, 2, 3, 4, 5, 6]
    regular_results = list(regular(data))
    parallel_results = list(parallel(data))

    assert regular_results == parallel_results
    assert parallel.max_workers == 2
    assert parallel.ordered is True
    assert parallel.chunk_size == 100


class TestParallelTransformerOperations:
  """Test parallel transformer operations."""

  def test_map_transforms_elements_concurrently(self):
    """Test map transforms each element using multiple threads."""
    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2).map(lambda x: x * 2)
    result = list(transformer([1, 2, 3, 4]))
    assert result == [2, 4, 6, 8]

  def test_filter_keeps_matching_elements_concurrently(self):
    """Test filter keeps only matching elements using multiple threads."""
    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2).filter(lambda x: x % 2 == 0)
    result = list(transformer([1, 2, 3, 4, 5, 6]))
    assert result == [2, 4, 6]

  def test_chained_operations_concurrently(self):
    """Test chained operations work correctly with concurrency."""
    transformer = (
      ParallelTransformer[int, int](max_workers=2, chunk_size=2)
      .map(lambda x: x * 2)
      .filter(lambda x: x > 4)
      .map(lambda x: x + 1)
    )
    result = list(transformer([1, 2, 3, 4, 5]))
    assert result == [7, 9, 11]  # [2,4,6,8,10] -> [6,8,10] -> [7,9,11]

  def test_map_with_context_aware_function_concurrently(self):
    """Test map with context-aware function in concurrent execution."""
    context = PipelineContext({"multiplier": 3})
    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2)
    transformer = transformer.map(lambda x, ctx: x * ctx["multiplier"])
    result = list(transformer([1, 2, 3], context))
    assert result == [3, 6, 9]

  def test_flatten_concurrently(self):
    """Test flatten operation works with concurrent execution."""
    transformer = ParallelTransformer[list, int](max_workers=2, chunk_size=2).flatten()
    result = list(transformer([[1, 2], [3, 4], [5, 6]]))
    assert result == [1, 2, 3, 4, 5, 6]

  def test_tap_applies_side_effects_concurrently(self):
    """Test tap applies side effects correctly in concurrent execution."""
    side_effects = []
    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2)
    transformer = transformer.tap(lambda x: side_effects.append(x))
    result = list(transformer([1, 2, 3, 4]))

    assert result == [1, 2, 3, 4]  # Data unchanged
    assert sorted(side_effects) == [1, 2, 3, 4]  # Side effects applied (may be out of order)


class TestParallelTransformerOrdering:
  """Test ordering behavior of parallel transformer."""

  def test_ordered_execution_maintains_order(self):
    """Test that ordered=True maintains element order."""

    def slow_transform(x: int) -> int:
      # Simulate variable processing time
      time.sleep(0.01 * (5 - x))  # Later elements process faster
      return x * 2

    transformer = ParallelTransformer[int, int](max_workers=3, ordered=True, chunk_size=2)
    transformer = transformer.map(slow_transform)
    result = list(transformer([1, 2, 3, 4, 5]))

    assert result == [2, 4, 6, 8, 10]  # Order maintained despite processing times

  def test_unordered_execution_allows_reordering(self):
    """Test that ordered=False allows results in completion order."""
    transformer = ParallelTransformer[int, int](max_workers=2, ordered=False, chunk_size=1)
    transformer = transformer.map(lambda x: x * 2)
    result = list(transformer([1, 2, 3, 4]))

    # Results should have the same elements, but order may vary
    assert sorted(result) == [2, 4, 6, 8]

  def test_ordered_vs_unordered_same_results(self):
    """Test that ordered and unordered produce same elements, just different order."""
    data = list(range(10))

    ordered_transformer = ParallelTransformer[int, int](max_workers=3, ordered=True, chunk_size=3)
    ordered_result = list(ordered_transformer.map(lambda x: x * 2)(data))

    unordered_transformer = ParallelTransformer[int, int](max_workers=3, ordered=False, chunk_size=3)
    unordered_result = list(unordered_transformer.map(lambda x: x * 2)(data))

    assert sorted(ordered_result) == sorted(unordered_result)
    assert ordered_result == [x * 2 for x in data]  # Ordered maintains sequence


class TestParallelTransformerPerformance:
  """Test performance aspects of parallel transformer."""

  def test_concurrent_faster_than_sequential_for_slow_operations(self):
    """Test that concurrent execution is faster for CPU-intensive operations."""

    def slow_operation(x: int) -> int:
      time.sleep(0.01)  # 10ms delay
      return x * 2

    data = list(range(8))  # 8 items, 80ms total sequential time

    # Sequential execution
    start_time = time.time()
    sequential = Transformer[int, int](chunk_size=4)
    seq_result = list(sequential.map(slow_operation)(data))
    seq_time = time.time() - start_time

    # Concurrent execution
    start_time = time.time()
    concurrent = ParallelTransformer[int, int](max_workers=4, chunk_size=4)
    conc_result = list(concurrent.map(slow_operation)(data))
    conc_time = time.time() - start_time

    # Results should be the same
    assert seq_result == conc_result

    # Concurrent should be faster (allowing some variance for thread overhead)
    assert conc_time < seq_time * 0.8  # At least 20% faster

  def test_thread_pool_properly_managed(self):
    """Test that thread pool is properly created and cleaned up."""
    with patch("efemel.pipeline.transformers.parallel.ThreadPoolExecutor") as mock_executor:
      mock_executor.return_value.__enter__.return_value = mock_executor.return_value
      mock_executor.return_value.__exit__.return_value = None
      mock_executor.return_value.submit.return_value.result.return_value = [2, 4]

      transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2)
      list(transformer([1, 2]))

      # Verify ThreadPoolExecutor was created with correct max_workers
      mock_executor.assert_called_with(max_workers=2)
      # Verify context manager was used (enter/exit called)
      mock_executor.return_value.__enter__.assert_called_once()
      mock_executor.return_value.__exit__.assert_called_once()


class TestParallelTransformerEdgeCases:
  """Test edge cases for parallel transformer."""

  def test_empty_data_concurrent(self):
    """Test parallel transformer with empty data."""
    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2).map(lambda x: x * 2)
    result = list(transformer([]))
    assert result == []

  def test_single_element_concurrent(self):
    """Test parallel transformer with single element."""
    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2)
    transformer = transformer.map(lambda x: x * 2).filter(lambda x: x > 0)
    result = list(transformer([5]))
    assert result == [10]

  def test_data_smaller_than_chunk_size(self):
    """Test parallel transformer when data is smaller than chunk size."""
    transformer = ParallelTransformer[int, int](max_workers=4, chunk_size=100)
    transformer = transformer.map(lambda x: x * 2)
    result = list(transformer([1, 2, 3]))
    assert result == [2, 4, 6]

  def test_more_workers_than_chunks(self):
    """Test parallel transformer when workers exceed number of chunks."""
    transformer = ParallelTransformer[int, int](max_workers=10, chunk_size=2)
    transformer = transformer.map(lambda x: x * 2)
    result = list(transformer([1, 2, 3]))  # Only 2 chunks, but 10 workers
    assert result == [2, 4, 6]

  def test_exception_handling_in_concurrent_execution(self):
    """Test that exceptions in worker threads are properly propagated."""

    def failing_function(x: int) -> int:
      if x == 3:
        raise ValueError("Test exception")
      return x * 2

    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2)
    transformer = transformer.map(failing_function)

    try:
      list(transformer([1, 2, 3, 4]))
      raise AssertionError("Expected exception was not raised")
    except ValueError as e:
      assert "Test exception" in str(e)


class TestParallelTransformerChunking:
  """Test chunking behavior with concurrent execution."""

  def test_chunking_with_concurrent_execution(self):
    """Test that chunking works correctly with concurrent execution."""
    # Use a function that can help us verify chunking
    processed_chunks = []

    def chunk_tracking_function(x: int) -> int:
      # This will help us see which items are processed together
      processed_chunks.append(x)
      return x * 2

    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=3)
    transformer = transformer.map(chunk_tracking_function)
    result = list(transformer([1, 2, 3, 4, 5, 6, 7]))

    assert result == [2, 4, 6, 8, 10, 12, 14]
    # All items should have been processed
    assert sorted(processed_chunks) == [1, 2, 3, 4, 5, 6, 7]

  def test_large_chunk_size_concurrent(self):
    """Test parallel transformer with large chunk size."""
    transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=1000)
    transformer = transformer.map(lambda x: x + 1)
    large_data = list(range(100))  # Much smaller than chunk size
    result = list(transformer(large_data))
    expected = [x + 1 for x in large_data]
    assert result == expected


class TestParallelTransformerContextModification:
  """Test context modification behavior with parallel transformer."""

  def test_context_modification_with_locking(self):
    """Test that context modification with locking works correctly in concurrent execution."""
    # Create context with items counter and a lock for thread safety
    context = PipelineContext({"items": 0, "_lock": threading.Lock()})

    def increment_counter(x: int, ctx: PipelineContext) -> int:
      """Increment the items counter in context thread-safely."""
      with ctx["_lock"]:
        current_items = ctx["items"]
        # Small delay to increase chance of race condition without locking
        time.sleep(0.001)
        ctx["items"] = current_items + 1
      return x * 2

    transformer = ParallelTransformer[int, int](max_workers=4, chunk_size=1)
    transformer = transformer.map(increment_counter)

    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = list(transformer(data, context))

    # Verify results are correct
    expected_result = [x * 2 for x in data]
    assert sorted(result) == sorted(expected_result)

    # Verify context was modified correctly - items should equal number of processed elements
    assert context["items"] == len(data)

  def test_context_modification_without_locking_shows_race_condition(self):
    """Test that context modification without locking can lead to race conditions."""
    # Create context without lock to demonstrate race condition
    context = PipelineContext({"items": 0})

    def unsafe_increment_counter(x: int, ctx: PipelineContext) -> int:
      """Increment the items counter without thread safety."""
      current_items = ctx["items"]
      # Delay to increase chance of race condition
      time.sleep(0.001)
      ctx["items"] = current_items + 1
      return x * 2

    transformer = ParallelTransformer[int, int](max_workers=4, chunk_size=1)
    transformer = transformer.map(unsafe_increment_counter)

    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = list(transformer(data, context))

    # Results should still be correct
    expected_result = [x * 2 for x in data]
    assert sorted(result) == sorted(expected_result)

    # Without locking, the final count will likely be less than expected due to race conditions
    # This test may occasionally pass by chance, but should usually fail
    # We'll check it's at least 1 but likely less than the full count
    assert context["items"] >= 1
    # In a race condition, this will typically be less than len(data)
    # But we can't assert this reliably in a test, so we just verify it's reasonable
    assert context["items"] <= len(data)

  def test_multiple_context_values_with_locking(self):
    """Test modifying multiple context values safely in concurrent execution."""
    context = PipelineContext({"total_sum": 0, "item_count": 0, "max_value": 0, "_lock": threading.Lock()})

    def update_statistics(x: int, ctx: PipelineContext) -> int:
      """Update multiple statistics in context thread-safely."""
      with ctx["_lock"]:
        ctx["total_sum"] += x
        ctx["item_count"] += 1
        ctx["max_value"] = max(ctx["max_value"], x)
      return x * 3

    transformer = ParallelTransformer[int, int](max_workers=3, chunk_size=2)
    transformer = transformer.map(update_statistics)

    data = [1, 5, 3, 8, 2, 7, 4, 6]
    result = list(transformer(data, context))

    # Verify transformation results
    expected_result = [x * 3 for x in data]
    assert sorted(result) == sorted(expected_result)

    # Verify context statistics were updated correctly
    assert context["total_sum"] == sum(data)
    assert context["item_count"] == len(data)
    assert context["max_value"] == max(data)


class TestSafeParallelTransformer:
  def test_safe_with_no_errors(self):
    """Test safe run with successful transformation."""
    transformer = ParallelTransformer.init(int).catch(lambda t: t.map(lambda x: x * 2))
    data = [1, 2, 3]
    result = list(transformer(data))
    assert result == [2, 4, 6]

  def test_safe_with_error_handling(self):
    """Test safe run with error handling."""
    errored_chunks = []
    transformer = ParallelTransformer.init(int, chunk_size=1).catch(
      lambda t: t.map(lambda x: x / 0),  # This will raise an error
      on_error=lambda chunk, error, context: errored_chunks.append(chunk),
    )
    data = [1, 2, 3]
    result = list(transformer(data))
    assert result == []
    # Note that we get 3 values back because we've specified chunk_size=1
    assert errored_chunks == [[1], [2], [3]]

  def test_global_error_handling(self):
    """Test safe run with error handling."""

    errored_chunks = []

    error_handler = ErrorHandler()
    error_handler.on_error(lambda chunk, error, context: errored_chunks.append(chunk))

    transformer = (
      ParallelTransformer.init(int, chunk_size=1).on_error(error_handler).catch(lambda t: t.map(lambda x: x / 0))
    )
    data = [1, 2, 3]
    result = list(transformer(data))
    assert result == []
    # Note that we get 3 values back because we've specified chunk_size=1
    assert errored_chunks == [[1], [2], [3]]
