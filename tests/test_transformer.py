"""Tests for the Transformer class."""

import time
from unittest.mock import patch

from efemel.pipeline.transformers.transformer import ConcurrentTransformer
from efemel.pipeline.transformers.transformer import PipelineContext
from efemel.pipeline.transformers.transformer import Transformer


class TestTransformerBasics:
  """Test basic transformer functionality."""

  def test_init_creates_identity_transformer(self):
    """Test that init creates an identity transformer."""
    transformer = Transformer.init(int)
    result = list(transformer([1, 2, 3]))
    assert result == [1, 2, 3]

  def test_init_with_chunk_size(self):
    """Test init with custom chunk size."""
    transformer = Transformer.init(int, chunk_size=2)
    assert transformer.chunk_size == 2
    result = list(transformer([1, 2, 3, 4]))
    assert result == [1, 2, 3, 4]

  def test_init_with_context(self):
    """Test init with custom context."""
    context = PipelineContext({"key": "value"})
    transformer = Transformer(context=context)
    assert transformer.context == context

  def test_call_executes_transformer(self):
    """Test that calling transformer executes it on data."""
    transformer = Transformer.init(int)
    result = list(transformer([1, 2, 3]))
    assert result == [1, 2, 3]


class TestTransformerOperations:
  """Test transformer operations like map, filter, etc."""

  def test_map_transforms_elements(self):
    """Test map transforms each element."""
    transformer = Transformer.init(int).map(lambda x: x * 2)
    result = list(transformer([1, 2, 3]))
    assert result == [2, 4, 6]

  def test_map_with_context_aware_function(self):
    """Test map with context-aware function."""
    context = PipelineContext({"multiplier": 3})
    transformer = Transformer(context=context).map(lambda x, ctx: x * ctx["multiplier"])
    result = list(transformer([1, 2, 3]))
    assert result == [3, 6, 9]

  def test_filter_keeps_matching_elements(self):
    """Test filter keeps only matching elements."""
    transformer = Transformer.init(int).filter(lambda x: x % 2 == 0)
    result = list(transformer([1, 2, 3, 4, 5, 6]))
    assert result == [2, 4, 6]

  def test_filter_with_context_aware_function(self):
    """Test filter with context-aware function."""
    context = PipelineContext({"threshold": 3})
    transformer = Transformer(context=context).filter(lambda x, ctx: x > ctx["threshold"])
    result = list(transformer([1, 2, 3, 4, 5]))
    assert result == [4, 5]

  def test_flatten_list_of_lists(self):
    """Test flatten with list of lists."""
    transformer = Transformer.init(list).flatten()
    result = list(transformer([[1, 2], [3, 4], [5]]))
    assert result == [1, 2, 3, 4, 5]

  def test_flatten_list_of_tuples(self):
    """Test flatten with list of tuples."""
    transformer = Transformer.init(tuple).flatten()
    result = list(transformer([(1, 2), (3, 4), (5,)]))
    assert result == [1, 2, 3, 4, 5]

  def test_flatten_list_of_sets(self):
    """Test flatten with list of sets."""
    transformer = Transformer.init(set).flatten()
    result = list(transformer([{1, 2}, {3, 4}, {5}]))
    # Sets are unordered, so we sort for comparison
    assert sorted(result) == [1, 2, 3, 4, 5]

  def test_tap_applies_side_effect_without_modification(self):
    """Test tap applies side effect without modifying data."""
    side_effects = []
    transformer = Transformer.init(int).tap(lambda x: side_effects.append(x))
    result = list(transformer([1, 2, 3]))

    assert result == [1, 2, 3]  # Data unchanged
    assert side_effects == [1, 2, 3]  # Side effect applied

  def test_tap_with_context_aware_function(self):
    """Test tap with context-aware function."""
    side_effects = []
    context = PipelineContext({"prefix": "item:"})
    transformer = Transformer(context=context).tap(lambda x, ctx: side_effects.append(f"{ctx['prefix']}{x}"))
    result = list(transformer([1, 2, 3]))

    assert result == [1, 2, 3]
    assert side_effects == ["item:1", "item:2", "item:3"]

  def test_apply_composes_transformers(self):
    """Test apply composes transformers."""
    transformer1 = Transformer.init(int).map(lambda x: x * 2)
    transformer2 = transformer1.apply(lambda t: t.filter(lambda x: x > 4))
    result = list(transformer2([1, 2, 3, 4]))
    assert result == [6, 8]  # [2, 4, 6, 8] filtered to [6, 8]


class TestTransformerChaining:
  """Test chaining multiple transformer operations."""

  def test_map_then_filter(self):
    """Test map followed by filter."""
    transformer = Transformer.init(int).map(lambda x: x * 2).filter(lambda x: x > 4)
    result = list(transformer([1, 2, 3, 4]))
    assert result == [6, 8]

  def test_filter_then_map(self):
    """Test filter followed by map."""
    transformer = Transformer.init(int).filter(lambda x: x % 2 == 0).map(lambda x: x * 3)
    result = list(transformer([1, 2, 3, 4, 5, 6]))
    assert result == [6, 12, 18]

  def test_map_flatten_filter(self):
    """Test map, flatten, then filter."""
    transformer = Transformer.init(int).map(lambda x: [x, x * 2]).flatten().filter(lambda x: x > 3)
    result = list(transformer([1, 2, 3]))
    assert result == [4, 6]  # [[1,2], [2,4], [3,6]] -> [1,2,2,4,3,6] -> [4,6]

  def test_complex_chain_with_tap(self):
    """Test complex chain with tap for side effects."""
    side_effects = []
    transformer = (
      Transformer.init(int)
      .map(lambda x: x * 2)
      .tap(lambda x: side_effects.append(f"doubled: {x}"))
      .filter(lambda x: x > 4)
      .tap(lambda x: side_effects.append(f"filtered: {x}"))
    )

    result = list(transformer([1, 2, 3, 4]))
    assert result == [6, 8]
    assert side_effects == ["doubled: 2", "doubled: 4", "doubled: 6", "doubled: 8", "filtered: 6", "filtered: 8"]


class TestTransformerTerminalOperations:
  """Test terminal operations like reduce."""

  def test_reduce_sums_elements(self):
    """Test reduce sums all elements."""
    transformer = Transformer.init(int)
    reducer = transformer.reduce(lambda acc, x: acc + x, initial=0)
    result = list(reducer([1, 2, 3, 4]))
    assert result == [10]

  def test_reduce_with_context_aware_function(self):
    """Test reduce with context-aware function."""
    context = PipelineContext({"multiplier": 2})
    transformer = Transformer(context=context)
    reducer = transformer.reduce(lambda acc, x, ctx: acc + (x * ctx["multiplier"]), initial=0)
    result = list(reducer([1, 2, 3]))
    assert result == [12]  # (1*2) + (2*2) + (3*2) = 2 + 4 + 6 = 12

  def test_reduce_with_map_chain(self):
    """Test reduce after map transformation."""
    transformer = Transformer.init(int).map(lambda x: x * 2)
    reducer = transformer.reduce(lambda acc, x: acc + x, initial=0)
    result = list(reducer([1, 2, 3]))
    assert result == [12]  # [2, 4, 6] summed = 12


class TestTransformerChunking:
  """Test chunking behavior."""

  def test_chunking_with_small_chunk_size(self):
    """Test transformer works correctly with small chunk sizes."""
    transformer = Transformer.init(int, chunk_size=2).map(lambda x: x * 2)
    result = list(transformer([1, 2, 3, 4, 5]))
    assert result == [2, 4, 6, 8, 10]

  def test_chunking_with_large_data(self):
    """Test transformer works correctly with large datasets."""
    transformer = Transformer.init(int, chunk_size=100).map(lambda x: x + 1)
    large_data = list(range(1000))
    result = list(transformer(large_data))
    expected = [x + 1 for x in large_data]
    assert result == expected


class TestTransformerEdgeCases:
  """Test edge cases for transformer."""

  def test_empty_data(self):
    """Test transformer with empty data."""
    transformer = Transformer.init(int).map(lambda x: x * 2)
    result = list(transformer([]))
    assert result == []

  def test_single_element(self):
    """Test transformer with single element."""
    transformer = Transformer.init(int).map(lambda x: x * 2).filter(lambda x: x > 0)
    result = list(transformer([5]))
    assert result == [10]

  def test_filter_removes_all_elements(self):
    """Test filter that removes all elements."""
    transformer = Transformer.init(int).filter(lambda x: x > 100)
    result = list(transformer([1, 2, 3]))
    assert result == []


class TestConcurrentTransformerBasics:
  """Test basic concurrent transformer functionality."""

  def test_init_creates_concurrent_transformer(self):
    """Test that init creates a concurrent transformer with default values."""
    transformer = ConcurrentTransformer[int, int]()
    assert transformer.max_workers == 4
    assert transformer.ordered is True
    assert transformer.chunk_size == 1000

  def test_init_with_custom_parameters(self):
    """Test init with custom parameters."""
    context = PipelineContext({"key": "value"})
    transformer = ConcurrentTransformer[int, int](max_workers=8, ordered=False, chunk_size=500, context=context)
    assert transformer.max_workers == 8
    assert transformer.ordered is False
    assert transformer.chunk_size == 500
    assert transformer.context == context

  def test_call_executes_transformer_concurrently(self):
    """Test that calling concurrent transformer executes it on data."""
    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=3)
    result = list(transformer([1, 2, 3, 4, 5]))
    assert result == [1, 2, 3, 4, 5]

  def test_from_transformer_class_method(self):
    """Test creating ConcurrentTransformer from existing Transformer."""
    # Create a regular transformer with some operations
    regular = Transformer.init(int, chunk_size=100).map(lambda x: x * 2).filter(lambda x: x > 5)

    # Convert to concurrent
    concurrent = ConcurrentTransformer.from_transformer(regular, max_workers=2, ordered=True)

    # Test both produce same results
    data = [1, 2, 3, 4, 5, 6]
    regular_results = list(regular(data))
    concurrent_results = list(concurrent(data))

    assert regular_results == concurrent_results
    assert concurrent.max_workers == 2
    assert concurrent.ordered is True
    assert concurrent.chunk_size == 100


class TestConcurrentTransformerOperations:
  """Test concurrent transformer operations."""

  def test_map_transforms_elements_concurrently(self):
    """Test map transforms each element using multiple threads."""
    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=2).map(lambda x: x * 2)
    result = list(transformer([1, 2, 3, 4]))
    assert result == [2, 4, 6, 8]

  def test_filter_keeps_matching_elements_concurrently(self):
    """Test filter keeps only matching elements using multiple threads."""
    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=2).filter(lambda x: x % 2 == 0)
    result = list(transformer([1, 2, 3, 4, 5, 6]))
    assert result == [2, 4, 6]

  def test_chained_operations_concurrently(self):
    """Test chained operations work correctly with concurrency."""
    transformer = (
      ConcurrentTransformer[int, int](max_workers=2, chunk_size=2)
      .map(lambda x: x * 2)
      .filter(lambda x: x > 4)
      .map(lambda x: x + 1)
    )
    result = list(transformer([1, 2, 3, 4, 5]))
    assert result == [7, 9, 11]  # [2,4,6,8,10] -> [6,8,10] -> [7,9,11]

  def test_map_with_context_aware_function_concurrently(self):
    """Test map with context-aware function in concurrent execution."""
    context = PipelineContext({"multiplier": 3})
    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=2, context=context)
    transformer = transformer.map(lambda x, ctx: x * ctx["multiplier"])
    result = list(transformer([1, 2, 3]))
    assert result == [3, 6, 9]

  def test_flatten_concurrently(self):
    """Test flatten operation works with concurrent execution."""
    transformer = ConcurrentTransformer[list, int](max_workers=2, chunk_size=2).flatten()
    result = list(transformer([[1, 2], [3, 4], [5, 6]]))
    assert result == [1, 2, 3, 4, 5, 6]

  def test_tap_applies_side_effects_concurrently(self):
    """Test tap applies side effects correctly in concurrent execution."""
    side_effects = []
    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=2)
    transformer = transformer.tap(lambda x: side_effects.append(x))
    result = list(transformer([1, 2, 3, 4]))

    assert result == [1, 2, 3, 4]  # Data unchanged
    assert sorted(side_effects) == [1, 2, 3, 4]  # Side effects applied (may be out of order)


class TestConcurrentTransformerOrdering:
  """Test ordering behavior of concurrent transformer."""

  def test_ordered_execution_maintains_order(self):
    """Test that ordered=True maintains element order."""

    def slow_transform(x: int) -> int:
      # Simulate variable processing time
      time.sleep(0.01 * (5 - x))  # Later elements process faster
      return x * 2

    transformer = ConcurrentTransformer[int, int](max_workers=3, ordered=True, chunk_size=2)
    transformer = transformer.map(slow_transform)
    result = list(transformer([1, 2, 3, 4, 5]))

    assert result == [2, 4, 6, 8, 10]  # Order maintained despite processing times

  def test_unordered_execution_allows_reordering(self):
    """Test that ordered=False allows results in completion order."""
    transformer = ConcurrentTransformer[int, int](max_workers=2, ordered=False, chunk_size=1)
    transformer = transformer.map(lambda x: x * 2)
    result = list(transformer([1, 2, 3, 4]))

    # Results should have the same elements, but order may vary
    assert sorted(result) == [2, 4, 6, 8]

  def test_ordered_vs_unordered_same_results(self):
    """Test that ordered and unordered produce same elements, just different order."""
    data = list(range(10))

    ordered_transformer = ConcurrentTransformer[int, int](max_workers=3, ordered=True, chunk_size=3)
    ordered_result = list(ordered_transformer.map(lambda x: x * 2)(data))

    unordered_transformer = ConcurrentTransformer[int, int](max_workers=3, ordered=False, chunk_size=3)
    unordered_result = list(unordered_transformer.map(lambda x: x * 2)(data))

    assert sorted(ordered_result) == sorted(unordered_result)
    assert ordered_result == [x * 2 for x in data]  # Ordered maintains sequence


class TestConcurrentTransformerPerformance:
  """Test performance aspects of concurrent transformer."""

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
    concurrent = ConcurrentTransformer[int, int](max_workers=4, chunk_size=4)
    conc_result = list(concurrent.map(slow_operation)(data))
    conc_time = time.time() - start_time

    # Results should be the same
    assert seq_result == conc_result

    # Concurrent should be faster (allowing some variance for thread overhead)
    assert conc_time < seq_time * 0.8  # At least 20% faster  def test_thread_pool_properly_managed(self):
    """Test that thread pool is properly created and cleaned up."""
    with patch("efemel.pipeline.transformers.transformer.ThreadPoolExecutor") as mock_executor:
      mock_executor.return_value.__enter__.return_value = mock_executor.return_value
      mock_executor.return_value.__exit__.return_value = None
      mock_executor.return_value.submit.return_value.result.return_value = [2, 4]

      transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=2)
      list(transformer([1, 2]))

      # Verify ThreadPoolExecutor was created with correct max_workers
      mock_executor.assert_called_with(max_workers=2)
      # Verify context manager was used (enter/exit called)
      mock_executor.return_value.__enter__.assert_called_once()
      mock_executor.return_value.__exit__.assert_called_once()


class TestConcurrentTransformerEdgeCases:
  """Test edge cases for concurrent transformer."""

  def test_empty_data_concurrent(self):
    """Test concurrent transformer with empty data."""
    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=2).map(lambda x: x * 2)
    result = list(transformer([]))
    assert result == []

  def test_single_element_concurrent(self):
    """Test concurrent transformer with single element."""
    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=2)
    transformer = transformer.map(lambda x: x * 2).filter(lambda x: x > 0)
    result = list(transformer([5]))
    assert result == [10]

  def test_data_smaller_than_chunk_size(self):
    """Test concurrent transformer when data is smaller than chunk size."""
    transformer = ConcurrentTransformer[int, int](max_workers=4, chunk_size=100)
    transformer = transformer.map(lambda x: x * 2)
    result = list(transformer([1, 2, 3]))
    assert result == [2, 4, 6]

  def test_more_workers_than_chunks(self):
    """Test concurrent transformer when workers exceed number of chunks."""
    transformer = ConcurrentTransformer[int, int](max_workers=10, chunk_size=2)
    transformer = transformer.map(lambda x: x * 2)
    result = list(transformer([1, 2, 3]))  # Only 2 chunks, but 10 workers
    assert result == [2, 4, 6]

  def test_exception_handling_in_concurrent_execution(self):
    """Test that exceptions in worker threads are properly propagated."""

    def failing_function(x: int) -> int:
      if x == 3:
        raise ValueError("Test exception")
      return x * 2

    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=2)
    transformer = transformer.map(failing_function)

    try:
      list(transformer([1, 2, 3, 4]))
      raise AssertionError("Expected exception was not raised")
    except ValueError as e:
      assert "Test exception" in str(e)


class TestConcurrentTransformerChunking:
  """Test chunking behavior with concurrent execution."""

  def test_chunking_with_concurrent_execution(self):
    """Test that chunking works correctly with concurrent execution."""
    # Use a function that can help us verify chunking
    processed_chunks = []

    def chunk_tracking_function(x: int) -> int:
      # This will help us see which items are processed together
      processed_chunks.append(x)
      return x * 2

    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=3)
    transformer = transformer.map(chunk_tracking_function)
    result = list(transformer([1, 2, 3, 4, 5, 6, 7]))

    assert result == [2, 4, 6, 8, 10, 12, 14]
    # All items should have been processed
    assert sorted(processed_chunks) == [1, 2, 3, 4, 5, 6, 7]

  def test_large_chunk_size_concurrent(self):
    """Test concurrent transformer with large chunk size."""
    transformer = ConcurrentTransformer[int, int](max_workers=2, chunk_size=1000)
    transformer = transformer.map(lambda x: x + 1)
    large_data = list(range(100))  # Much smaller than chunk size
    result = list(transformer(large_data))
    expected = [x + 1 for x in large_data]
    assert result == expected
