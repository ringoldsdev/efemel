"""
Test suite for the Pipeline class.

This module contains comprehensive tests for the Pipeline class functionality
including all methods, edge cases, and error conditions.
"""

import pytest

from efemel.pipeline import CompoundError
from efemel.pipeline import Pipeline


class TestPipelineBasics:
  """Test basic Pipeline functionality."""

  def test_pipeline_initialization(self):
    """Test Pipeline initialization with various iterables."""
    # Test with list
    pipeline = Pipeline([1, 2, 3, 4, 5])
    assert isinstance(pipeline, Pipeline)
    # Generator should be a generator object, not the original list
    from types import GeneratorType

    assert isinstance(pipeline.generator, GeneratorType)

    # Test with tuple
    pipeline = Pipeline((1, 2, 3))
    assert list(pipeline) == [1, 2, 3]

    # Test with generator
    def gen():
      yield from range(1, 4)

    pipeline = Pipeline(gen())
    assert list(pipeline) == [1, 2, 3]

    # Test with empty list
    pipeline = Pipeline([])
    assert list(pipeline) == []

  def test_pipeline_iteration(self):
    """Test Pipeline iteration behavior."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Test iteration
    result = []
    for item in pipeline:
      result.append(item)

    assert result == [1, 2, 3, 4, 5]

  def test_to_list(self):
    """Test Pipeline.to_list() method."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    result = pipeline.to_list()

    assert result == [1, 2, 3, 4, 5]
    assert isinstance(result, list)

    # Test with empty pipeline
    empty_pipeline = Pipeline([])
    assert empty_pipeline.to_list() == []

  def test_first(self):
    """Test Pipeline.first() method."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    assert pipeline.first() == 1

    # Test with string
    str_pipeline = Pipeline(["hello", "world"])
    assert str_pipeline.first() == "hello"

  def test_first_empty_pipeline(self):
    """Test Pipeline.first() with empty pipeline."""
    empty_pipeline = Pipeline([])
    with pytest.raises(StopIteration):
      empty_pipeline.first()


class TestPipelineFiltering:
  """Test Pipeline filtering functionality."""

  def test_filter_basic(self):
    """Test basic filtering operations."""
    # Filter even numbers
    pipeline1 = Pipeline([1, 2, 3, 4, 5])
    even_pipeline = pipeline1.filter(lambda x: x % 2 == 0)
    assert even_pipeline.to_list() == [2, 4]

    # Filter numbers greater than 3 - use fresh pipeline
    pipeline2 = Pipeline([1, 2, 3, 4, 5])
    gt3_pipeline = pipeline2.filter(lambda x: x > 3)
    assert gt3_pipeline.to_list() == [4, 5]

  def test_filter_with_strings(self):
    """Test filtering with string data."""
    # Filter strings longer than 4 characters
    pipeline1 = Pipeline(["hello", "world", "python", "test"])
    long_strings = pipeline1.filter(lambda s: len(s) > 4)
    assert long_strings.to_list() == ["hello", "world", "python"]

    # Filter strings starting with 'p' - use fresh pipeline
    pipeline2 = Pipeline(["hello", "world", "python", "test"])
    p_strings = pipeline2.filter(lambda s: s.startswith("p"))
    assert p_strings.to_list() == ["python"]

  def test_filter_empty_result(self):
    """Test filter that results in empty pipeline."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Filter that matches nothing
    empty_result = pipeline.filter(lambda x: x > 10)
    assert empty_result.to_list() == []

  def test_filter_all_pass(self):
    """Test filter where all items pass."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Filter that passes everything
    all_pass = pipeline.filter(lambda x: True)
    assert all_pass.to_list() == [1, 2, 3, 4, 5]

  def test_filter_chaining(self):
    """Test chaining multiple filters."""
    pipeline = Pipeline([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    # Chain filters: even numbers and greater than 5
    result = pipeline.filter(lambda x: x % 2 == 0).filter(lambda x: x > 5)
    assert result.to_list() == [6, 8, 10]


class TestPipelineMapping:
  """Test Pipeline mapping functionality."""

  def test_map_basic(self):
    """Test basic mapping operations."""
    # Double each number
    pipeline1 = Pipeline([1, 2, 3, 4, 5])
    doubled = pipeline1.map(lambda x: x * 2)
    assert doubled.to_list() == [2, 4, 6, 8, 10]

    # Square each number - use fresh pipeline
    pipeline2 = Pipeline([1, 2, 3, 4, 5])
    squared = pipeline2.map(lambda x: x**2)
    assert squared.to_list() == [1, 4, 9, 16, 25]

  def test_map_type_transformation(self):
    """Test mapping with type transformation."""
    # Convert numbers to strings
    pipeline1 = Pipeline([1, 2, 3, 4, 5])
    str_pipeline = pipeline1.map(str)
    assert str_pipeline.to_list() == ["1", "2", "3", "4", "5"]

    # Convert to boolean (non-zero is True) - use fresh pipeline
    pipeline2 = Pipeline([1, 2, 3, 4, 5])
    bool_pipeline = pipeline2.map(bool)
    assert bool_pipeline.to_list() == [True, True, True, True, True]

  def test_map_with_strings(self):
    """Test mapping with string data."""
    # Convert to uppercase
    pipeline1 = Pipeline(["hello", "world", "python"])
    upper_pipeline = pipeline1.map(str.upper)
    assert upper_pipeline.to_list() == ["HELLO", "WORLD", "PYTHON"]

    # Get string lengths - use fresh pipeline
    pipeline2 = Pipeline(["hello", "world", "python"])
    len_pipeline = pipeline2.map(len)
    assert len_pipeline.to_list() == [5, 5, 6]

  def test_map_chaining(self):
    """Test chaining multiple map operations."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Chain maps: double, then add 1
    result = pipeline.map(lambda x: x * 2).map(lambda x: x + 1)
    assert result.to_list() == [3, 5, 7, 9, 11]

  def test_map_empty_pipeline(self):
    """Test mapping on empty pipeline."""
    empty_pipeline = Pipeline([])

    # Map should return empty result
    result = empty_pipeline.map(lambda x: x * 2)
    assert result.to_list() == []


class TestPipelineMapFilter:
  """Test Pipeline map and filter combinations."""

  def test_map_then_filter(self):
    """Test mapping then filtering."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Double numbers, then filter even results
    result = pipeline.map(lambda x: x * 2).filter(lambda x: x % 2 == 0)
    assert result.to_list() == [2, 4, 6, 8, 10]

  def test_filter_then_map(self):
    """Test filtering then mapping."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    # Filter even numbers, then double them
    result = pipeline.filter(lambda x: x % 2 == 0).map(lambda x: x * 2)
    assert result.to_list() == [4, 8]

  def test_complex_map_filter_chain(self):
    """Test complex chaining of map and filter operations."""
    pipeline = Pipeline([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    # Complex chain: filter odd, multiply by 3, filter > 10
    result = (
      pipeline.filter(lambda x: x % 2 == 1)  # [1, 3, 5, 7, 9]
      .map(lambda x: x * 3)  # [3, 9, 15, 21, 27]
      .filter(lambda x: x > 10)
    )  # [15, 21, 27]

    assert result.to_list() == [15, 21, 27]


class TestPipelineReduce:
  """Test Pipeline reduce functionality."""

  def test_reduce_basic(self):
    """Test basic reduce operations."""
    # Sum all numbers
    pipeline1 = Pipeline([1, 2, 3, 4, 5])
    sum_result = pipeline1.reduce(lambda acc, x: acc + x, 0)
    assert sum_result.first() == 15

    # Multiply all numbers - use fresh pipeline
    pipeline2 = Pipeline([1, 2, 3, 4, 5])
    product_result = pipeline2.reduce(lambda acc, x: acc * x, 1)
    assert product_result.first() == 120

  def test_reduce_with_strings(self):
    """Test reduce with string data."""
    # Concatenate strings
    pipeline1 = Pipeline(["hello", "world", "python"])
    concat_result = pipeline1.reduce(lambda acc, x: acc + " " + x, "")
    assert concat_result.first() == " hello world python"

    # Join with commas - use fresh pipeline
    pipeline2 = Pipeline(["hello", "world", "python"])
    join_result = pipeline2.reduce(lambda acc, x: acc + "," + x if acc else x, "")
    assert join_result.first() == "hello,world,python"

  def test_reduce_empty_pipeline(self):
    """Test reduce on empty pipeline."""
    empty_pipeline = Pipeline([])

    # Reduce should return initial value
    result = empty_pipeline.reduce(lambda acc, x: acc + x, 10)
    assert result.first() == 10

  def test_reduce_single_item(self):
    """Test reduce with single item."""
    single_pipeline = Pipeline([42])

    # Should combine initial value with single item
    result = single_pipeline.reduce(lambda acc, x: acc + x, 10)
    assert result.first() == 52


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


class TestPipelineEach:
  """Test Pipeline each functionality."""

  def test_each_basic(self):
    """Test basic each operations."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    side_effects = []

    # Each should execute function for each item
    pipeline.each(side_effects.append)

    assert side_effects == [1, 2, 3, 4, 5]

  def test_each_returns_none(self):
    """Test that each returns None."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    result = pipeline.each(lambda x: None)
    assert result is None

  def test_each_with_empty_pipeline(self):
    """Test each with empty pipeline."""
    empty_pipeline = Pipeline([])
    side_effects = []

    # Should not execute function
    empty_pipeline.each(side_effects.append)

    assert side_effects == []

  def test_each_terminal_operation(self):
    """Test that each is a terminal operation."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    side_effects = []

    # After each, pipeline should be consumed
    pipeline.each(side_effects.append)

    assert side_effects == [1, 2, 3, 4, 5]


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
      (1, None),
      (2, None),
      (3, None),
      (4, None),
      (5, None),
      (6, None),
      (7, None),
      (8, None),
      (9, None),
      (10, None),
    ]


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


class TestPipelineIntegration:
  """Integration tests for Pipeline class."""

  def test_data_processing_pipeline(self):
    """Test a realistic data processing pipeline."""
    # Simulate processing a list of user data
    users = [
      {"name": "Alice", "age": 30, "active": True},
      {"name": "Bob", "age": 25, "active": False},
      {"name": "Charlie", "age": 35, "active": True},
      {"name": "Diana", "age": 28, "active": True},
      {"name": "Eve", "age": 22, "active": False},
    ]

    pipeline = Pipeline(users)

    # Process: filter active users, extract names, convert to uppercase
    result = pipeline.filter(lambda user: user["active"]).map(lambda user: user["name"]).map(str.upper)

    assert result.to_list() == ["ALICE", "CHARLIE", "DIANA"]

  def test_number_processing_pipeline(self):
    """Test a number processing pipeline."""
    numbers = range(1, 21)  # 1 to 20

    pipeline = Pipeline(numbers)

    # Process: filter even numbers, square them, filter > 50, sum
    result = (
      pipeline.filter(lambda x: x % 2 == 0)  # [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
      .map(lambda x: x**2)  # [4, 16, 36, 64, 100, 144, 196, 256, 324, 400]
      .filter(lambda x: x > 50)  # [64, 100, 144, 196, 256, 324, 400]
      .reduce(lambda acc, x: acc + x, 0)
    )  # 1484

    assert result.first() == 1484

  def test_text_processing_pipeline(self):
    """Test a text processing pipeline."""
    text = "Hello world! This is a test. Python is amazing."
    words = text.split()

    pipeline = Pipeline(words)

    # Process: filter words > 3 chars, remove punctuation, lowercase, get unique
    result = (
      pipeline.filter(lambda word: len(word) > 3)
      .map(lambda word: word.strip(".,!"))
      .map(str.lower)
      .filter(lambda word: word not in ["this"])
    )  # Simple "unique" filter

    expected = ["hello", "world", "test", "python", "amazing"]
    assert result.to_list() == expected

  def test_nested_data_processing(self):
    """Test processing nested data structures."""
    data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    pipeline = Pipeline(data)

    # Flatten, filter odd numbers, square them
    result = (
      pipeline.flatten()  # [1, 2, 3, 4, 5, 6, 7, 8, 9]
      .filter(lambda x: x % 2 == 1)  # [1, 3, 5, 7, 9]
      .map(lambda x: x**2)
    )  # [1, 9, 25, 49, 81]

    assert result.to_list() == [1, 9, 25, 49, 81]


class TestPipelineComposition:
  """Test Pipeline composition functionality."""

  def test_pipeline_from_pipeline_init(self):
    """Test creating a Pipeline from another Pipeline using __init__."""
    # Create source pipeline
    source_pipeline = Pipeline([1, 2, 3, 4, 5])

    # Create new pipeline from the source
    new_pipeline = Pipeline(source_pipeline)

    # Test that new pipeline works (source gets exhausted, so test new one)
    result = new_pipeline.to_list()
    assert result == [1, 2, 3, 4, 5]

  def test_from_pipeline_class_method(self):
    """Test creating a Pipeline using from_pipeline class method."""
    # Create source pipeline
    source_pipeline = Pipeline([1, 2, 3, 4, 5])

    # Create new pipeline using class method
    new_pipeline = Pipeline.from_pipeline(source_pipeline)

    # Test that they produce the same results
    assert new_pipeline.to_list() == [1, 2, 3, 4, 5]

  def test_chain_method(self):
    """Test chaining multiple pipelines."""
    pipeline1 = Pipeline([1, 2, 3])
    pipeline2 = Pipeline([4, 5, 6])
    pipeline3 = Pipeline([7, 8, 9])

    # Chain them together
    chained = Pipeline.chain(pipeline1, pipeline2, pipeline3)

    # Should contain all elements in sequence
    assert chained.to_list() == [1, 2, 3, 4, 5, 6, 7, 8, 9]

  def test_chain_empty_pipelines(self):
    """Test chaining with empty pipelines."""
    pipeline1 = Pipeline([1, 2])
    empty_pipeline = Pipeline([])
    pipeline2 = Pipeline([3, 4])

    chained = Pipeline.chain(pipeline1, empty_pipeline, pipeline2)
    assert chained.to_list() == [1, 2, 3, 4]

  def test_chain_single_pipeline(self):
    """Test chaining with a single pipeline."""
    pipeline = Pipeline([1, 2, 3])
    chained = Pipeline.chain(pipeline)

    assert chained.to_list() == [1, 2, 3]

  def test_pipeline_composition_with_operations(self):
    """Test that pipeline composition works with transformations."""
    # Create source pipeline with transformations
    source = Pipeline([1, 2, 3, 4, 5]).map(lambda x: x * 2)

    # Create new pipeline from transformed source
    new_pipeline = Pipeline.from_pipeline(source)
    filtered = new_pipeline.filter(lambda x: x > 5)

    assert filtered.to_list() == [6, 8, 10]

  def test_chain_with_different_types(self):
    """Test chaining pipelines with different but compatible types."""
    numbers = Pipeline([1, 2, 3])
    strings = Pipeline(["4", "5", "6"])

    # Chain and then transform to make types consistent
    chained = Pipeline.chain(numbers, strings)
    all_strings = chained.map(str)

    assert all_strings.to_list() == ["1", "2", "3", "4", "5", "6"]

  def test_complex_pipeline_composition(self):
    """Test complex pipeline composition scenario."""
    # Create multiple source pipelines
    evens = Pipeline([2, 4, 6, 8])
    odds = Pipeline([1, 3, 5, 7])

    # Chain them
    all_numbers = Pipeline.chain(evens, odds)

    # Apply transformations
    result = all_numbers.filter(lambda x: x > 3).map(lambda x: x**2).reduce(lambda acc, x: acc + x, 0)

    # Expected: [4, 6, 8, 5, 7] -> [16, 36, 64, 25, 49] -> 190
    assert result.first() == 190


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


class TestPipelineCatch:
  """Test Pipeline catch functionality and CompoundError handling."""

  def test_catch_basic_error_handling(self):
    """Test basic catch functionality with error callback."""
    captured_errors = []

    def error_prone_pipeline(p):
      return p.map(lambda x: 10 / x if x != 0 else 1 / 0)

    def error_handler(error):
      captured_errors.append(error)

    pipeline = Pipeline([2, 0, 4, 0, 6])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(error_prone_pipeline, error_handler).to_list()

    # Should have captured 2 ZeroDivisionErrors
    assert len(captured_errors) == 2
    assert all(isinstance(e, ZeroDivisionError) for e in captured_errors)

    # CompoundError should also contain the same errors
    assert len(exc_info.value.errors) == 2
    assert all(isinstance(e, ZeroDivisionError) for e in exc_info.value.errors)

  def test_catch_with_successful_items(self):
    """Test catch with mix of successful and failed items."""
    error_logs = []

    def selective_error_pipeline(p):
      return p.map(lambda x: x * 2 if x != 3 else 1 / 0)

    def log_error(error):
      error_logs.append(f"Caught: {type(error).__name__}")

    pipeline = Pipeline([1, 2, 3, 4, 5])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(selective_error_pipeline, log_error).to_list()

    # Should have logged one error
    assert len(error_logs) == 1
    assert "ZeroDivisionError" in error_logs[0]

    # CompoundError should contain one error
    assert len(exc_info.value.errors) == 1

  def test_catch_with_reduce_operation(self):
    """Test catch with reduce operation that has errors."""
    errors_seen = []

    def error_prone_reduce_pipeline(p: Pipeline[int]):
      # First map some values to cause errors, then reduce
      return p.map(lambda x: x if x != 2 else 1 / 0).reduce(lambda acc, x: acc + x, 0)

    def collect_errors(error):
      errors_seen.append(error)

    pipeline = Pipeline([1, 2, 3, 4, 5])

    with pytest.raises(CompoundError) as exc_info:
      result = pipeline.catch(error_prone_reduce_pipeline, collect_errors).first()

    # Should have seen the error during catch
    assert len(errors_seen) == 1
    assert isinstance(errors_seen[0], ZeroDivisionError)

    # CompoundError should also have the error
    assert len(exc_info.value.errors) == 1

  def test_catch_multiple_operation_errors(self):
    """Test catch with multiple operations that can error."""
    all_errors = []

    def multi_error_pipeline(p: Pipeline[int]):
      return (
        p.map(lambda x: x / 2 if x != 4 else 1 / 0)  # Error on 4
        .filter(
          lambda x: x > 0 if x != 1 else 1 / 0
        )  # Error on 1 (after division = 0.5, but let's say error on result 1)
        .map(lambda x: x * 3 if x != 3 else 1 / 0)
      )  # Error on 3 (after division = 1.5, won't hit)

    def track_all_errors(error):
      all_errors.append(type(error).__name__)

    pipeline = Pipeline([2, 4, 6, 8])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(multi_error_pipeline, track_all_errors).to_list()

    # Should have tracked at least one error
    assert len(all_errors) >= 1
    assert len(exc_info.value.errors) >= 1

  def test_catch_with_no_errors(self):
    """Test catch when no errors occur."""
    error_handler_called = []

    def safe_pipeline(p):
      return p.map(lambda x: x * 2).filter(lambda x: x > 5)

    def should_not_be_called(error):
      error_handler_called.append(error)

    pipeline = Pipeline([1, 2, 3, 4, 5])
    result = pipeline.catch(safe_pipeline, should_not_be_called).to_list()

    # No errors, so handler should not be called
    assert len(error_handler_called) == 0
    # Should get successful results
    assert result == [6, 8, 10]

  def test_compound_error_formatting(self):
    """Test CompoundError message formatting."""

    def always_error(x):
      if x == 1:
        raise ValueError("First error")
      elif x == 2:
        raise TypeError("Second error")
      else:
        raise RuntimeError("Third error")

    pipeline = Pipeline([1, 2, 3])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.map(always_error).to_list()

    error_message = str(exc_info.value)

    # Check message contains error count
    assert "3 error(s) occurred in the pipeline" in error_message

    # Check individual error messages are included
    assert "ValueError: First error" in error_message
    assert "TypeError: Second error" in error_message
    assert "RuntimeError: Third error" in error_message

  def test_compound_error_with_single_error(self):
    """Test CompoundError with just one error."""

    def single_error(x):
      if x == 3:
        raise ValueError("Only error")
      return x * 2

    pipeline = Pipeline([1, 2, 3, 4])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.map(single_error).to_list()

    # Should have exactly one error
    assert len(exc_info.value.errors) == 1
    assert isinstance(exc_info.value.errors[0], ValueError)

    # Message should reflect single error
    error_message = str(exc_info.value)
    assert "1 error(s) occurred in the pipeline" in error_message
    assert "ValueError: Only error" in error_message

  def test_catch_with_chained_operations(self):
    """Test catch with complex chained operations."""
    logged_errors = []

    def complex_pipeline(p):
      return (
        p.filter(lambda x: x > 0 if x != 2 else 1 / 0)  # Error on 2
        .map(lambda x: x * 2 if x != 4 else 1 / 0)  # Error on 4
        .reduce(lambda acc, x: acc + x, 0)
      )

    def error_logger(error):
      logged_errors.append(f"Error: {error}")

    pipeline = Pipeline([1, 2, 3, 4, 5])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(complex_pipeline, error_logger).first()

    # Should have logged errors from the operations
    assert len(logged_errors) >= 1
    # CompoundError should also contain the errors
    assert len(exc_info.value.errors) >= 1

  def test_catch_error_handler_exception(self):
    """Test catch when error handler itself raises exception."""

    def error_pipeline(p):
      return p.map(lambda x: 1 / 0 if x == 2 else x)

    def failing_handler(error):
      raise RuntimeError("Handler failed!")

    pipeline = Pipeline([1, 2, 3])

    # Should still work despite handler failure
    with pytest.raises(CompoundError):
      # The failing handler should not stop the pipeline
      pipeline.catch(error_pipeline, failing_handler).to_list()
