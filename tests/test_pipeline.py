"""Tests for the Pipeline class."""

from efemel.pipeline.pipeline import Pipeline
from efemel.pipeline.transformers.transformer import Transformer


class TestPipelineBasics:
  """Test basic pipeline functionality."""

  def test_pipeline_creation_from_single_iterable(self):
    """Test creating pipeline from single iterable."""
    pipeline = Pipeline([1, 2, 3])
    result = pipeline.to_list()
    assert result == [1, 2, 3]

  def test_pipeline_creation_from_multiple_iterables(self):
    """Test creating pipeline from multiple iterables."""
    pipeline = Pipeline([1, 2], [3, 4], [5])
    result = pipeline.to_list()
    assert result == [1, 2, 3, 4, 5]

  def test_pipeline_iteration(self):
    """Test that pipeline can be iterated over."""
    pipeline = Pipeline([1, 2, 3])
    result = list(pipeline)
    assert result == [1, 2, 3]

  def test_pipeline_to_list_multiple_calls(self):
    """Test that to_list can be called multiple times (iterator consumption)."""
    pipeline = Pipeline([1, 2, 3])
    first_result = pipeline.to_list()
    second_result = pipeline.to_list()
    # Note: This tests current behavior - iterator is consumed after first call
    assert first_result == [1, 2, 3]
    assert second_result == []  # Iterator is consumed


class TestPipelineApply:
  """Test apply method with transformers."""

  def test_apply_transformer(self):
    """Test apply with chained transformer operations."""
    transformer = Transformer.init(int).map(lambda x: x * 2).filter(lambda x: x > 4)
    pipeline = Pipeline([1, 2, 3, 4]).apply(transformer)
    result = pipeline.to_list()
    assert result == [6, 8]

  def test_apply_callable_function(self):
    """Test apply with a callable function."""

    def double_generator(data):
      for item in data:
        yield item * 2

    pipeline = Pipeline([1, 2, 3]).apply(double_generator)
    result = pipeline.to_list()
    assert result == [2, 4, 6]


class TestPipelineTransform:
  """Test transform shorthand method."""

  def test_transform_chain_operations(self):
    """Test transform with chained operations."""
    pipeline = Pipeline([1, 2, 3, 4]).transform(lambda t: t.map(lambda x: x * 2).filter(lambda x: x > 4))
    result = pipeline.to_list()
    assert result == [6, 8]

  def test_transform_with_custom_transformer(self):
    """Test transform with custom transformer class."""

    def custom_transform(transformer: Transformer[int, int]) -> Transformer[int, int]:
      return transformer.map(lambda x: x + 10).filter(lambda x: x > 12)

    pipeline = Pipeline([1, 2, 3]).transform(custom_transform)
    result = pipeline.to_list()
    assert result == [13]  # [11, 12, 13] filtered to [13]


class TestPipelineTerminalOperations:
  """Test terminal operations that consume the pipeline."""

  def test_each_applies_function_to_all_elements(self):
    """Test each applies function to all elements."""
    results = []
    pipeline = Pipeline([1, 2, 3])
    pipeline.each(lambda x: results.append(x * 2))
    assert results == [2, 4, 6]

  def test_first_gets_first_n_elements(self):
    """Test first gets first n elements."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    result = pipeline.first(3)
    assert result == [1, 2, 3]

  def test_first_default_gets_one_element(self):
    """Test first with default argument gets one element."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    result = pipeline.first()
    assert result == [1]

  def test_first_with_small_dataset(self):
    """Test first when requesting more elements than available."""
    pipeline = Pipeline([1, 2])
    result = pipeline.first(5)
    assert result == [1, 2]

  def test_consume_processes_without_return(self):
    """Test consume processes all elements without returning anything."""
    side_effects = []
    transformer = Transformer.init(int).tap(lambda x: side_effects.append(x))
    pipeline = Pipeline([1, 2, 3]).apply(transformer)

    result = pipeline.consume()
    assert result is None
    assert side_effects == [1, 2, 3]

  def test_to_list_returns_all_elements(self):
    """Test to_list returns all processed elements."""
    pipeline = Pipeline([1, 2, 3, 4, 5])
    result = pipeline.to_list()
    assert result == [1, 2, 3, 4, 5]


class TestPipelineChaining:
  """Test chaining pipeline operations."""

  def test_apply_then_terminal_operation(self):
    """Test applying transformer then using terminal operation."""
    transformer = Transformer.init(int).map(lambda x: x * 2)
    pipeline = Pipeline([1, 2, 3]).apply(transformer)
    result = pipeline.first(2)
    assert result == [2, 4]

  def test_multiple_transforms(self):
    """Test applying multiple transforms."""
    pipeline = (
      Pipeline([1, 2, 3, 4]).transform(lambda t: t.map(lambda x: x * 2)).transform(lambda t: t.filter(lambda x: x > 4))
    )
    result = pipeline.to_list()
    assert result == [6, 8]

  def test_transform_then_apply(self):
    """Test transform followed by apply."""
    transformer = Transformer.init(int).filter(lambda x: x > 4)
    pipeline = Pipeline([1, 2, 3, 4, 5]).transform(lambda t: t.map(lambda x: x * 2)).apply(transformer)
    result = pipeline.to_list()
    assert result == [6, 8, 10]


class TestPipelineDataTypes:
  """Test pipeline with different data types."""

  def test_pipeline_with_strings(self):
    """Test pipeline with string data."""
    pipeline = Pipeline(["hello", "world"]).transform(lambda t: t.map(lambda x: x.upper()))
    result = pipeline.to_list()
    assert result == ["HELLO", "WORLD"]

  def test_pipeline_with_mixed_data(self):
    """Test pipeline with mixed data types."""
    pipeline = Pipeline([1, "hello", 3.14]).transform(lambda t: t.map(lambda x: str(x)))
    result = pipeline.to_list()
    assert result == ["1", "hello", "3.14"]

  def test_pipeline_with_complex_objects(self):
    """Test pipeline with complex objects."""
    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    pipeline = Pipeline(data).transform(lambda t: t.map(lambda x: x["name"]))
    result = pipeline.to_list()
    assert result == ["Alice", "Bob"]


class TestPipelineEdgeCases:
  """Test edge cases for pipeline."""

  def test_empty_pipeline(self):
    """Test pipeline with empty data."""
    pipeline = Pipeline([])
    result = pipeline.to_list()
    assert result == []

  def test_empty_pipeline_terminal_operations(self):
    """Test terminal operations on empty pipeline."""
    # Test each
    results = []
    pipeline_each = Pipeline([])
    pipeline_each.each(lambda x: results.append(x))
    assert results == []

    # Test first
    pipeline_first = Pipeline([])
    result = pipeline_first.first(5)
    assert result == []

    # Test consume
    pipeline_consume = Pipeline([])
    result = pipeline_consume.consume()
    assert result is None

  def test_single_element_pipeline(self):
    """Test pipeline with single element."""
    pipeline = Pipeline([42])
    result = pipeline.to_list()
    assert result == [42]

  def test_pipeline_type_preservation(self):
    """Test that pipeline preserves and transforms types correctly."""
    # Start with integers
    pipeline = Pipeline([1, 2, 3])
    int_result = pipeline.to_list()
    assert all(isinstance(x, int) for x in int_result)

    # Transform to strings
    pipeline = Pipeline([1, 2, 3]).transform(lambda t: t.map(lambda x: str(x)))
    str_result = pipeline.to_list()
    assert all(isinstance(x, str) for x in str_result)
    assert str_result == ["1", "2", "3"]


class TestPipelinePerformance:
  """Test pipeline performance characteristics."""

  def test_large_dataset_processing(self):
    """Test pipeline can handle large datasets."""
    large_data = list(range(10000))
    pipeline = Pipeline(large_data).transform(lambda t: t.map(lambda x: x * 2).filter(lambda x: x % 100 == 0))
    result = pipeline.to_list()

    # Should have every 50th element doubled (0, 100, 200, ..., 19800)
    expected = [x * 2 for x in range(0, 10000, 50)]
    assert result == expected

  def test_chunked_processing(self):
    """Test that chunked processing works correctly."""
    # Use small chunk size to test chunking behavior
    transformer = Transformer.init(int, chunk_size=10).map(lambda x: x + 1)
    pipeline = Pipeline(list(range(100))).apply(transformer)
    result = pipeline.to_list()

    expected = list(range(1, 101))  # [1, 2, 3, ..., 100]
    assert result == expected
