"""Tests for the Pipeline class."""

from efemel.pipeline.pipeline import Pipeline
from efemel.pipeline.transformers.transformer import Transformer


class TestPipelineBasics:
  """Test core pipeline functionality."""

  def test_single_iterable_creation(self):
    """Test creating pipeline from single iterable."""
    pipeline = Pipeline([1, 2, 3])
    assert pipeline.to_list() == [1, 2, 3]

  def test_multiple_iterables_creation(self):
    """Test creating pipeline from multiple iterables."""
    pipeline = Pipeline([1, 2], [3, 4], [5])
    assert pipeline.to_list() == [1, 2, 3, 4, 5]

  def test_pipeline_iteration(self):
    """Test pipeline is iterable."""
    pipeline = Pipeline([1, 2, 3])
    assert list(pipeline) == [1, 2, 3]

  def test_iterator_consumption(self):
    """Test that to_list consumes the iterator."""
    pipeline = Pipeline([1, 2, 3])
    first_result = pipeline.to_list()
    second_result = pipeline.to_list()
    assert first_result == [1, 2, 3]
    assert second_result == []  # Iterator is consumed


class TestPipelineTransformations:
  """Test pipeline transformation methods."""

  def test_apply_with_transformer(self):
    """Test apply with transformer object."""
    transformer = Transformer.init(int).map(lambda x: x * 2).filter(lambda x: x > 4)
    result = Pipeline([1, 2, 3, 4]).apply(transformer).to_list()
    assert result == [6, 8]

  def test_apply_with_generator_function(self):
    """Test apply with generator function."""

    def double_generator(data):
      for item in data:
        yield item * 2

    result = Pipeline([1, 2, 3]).apply(double_generator).to_list()
    assert result == [2, 4, 6]

  def test_transform_shorthand(self):
    """Test transform shorthand method."""
    result = Pipeline([1, 2, 3, 4]).transform(lambda t: t.map(lambda x: x * 2).filter(lambda x: x > 4)).to_list()
    assert result == [6, 8]

  def test_chained_transformations(self):
    """Test chaining multiple transformations."""
    result = (
      Pipeline([1, 2, 3, 4])
      .transform(lambda t: t.map(lambda x: x * 2))
      .transform(lambda t: t.filter(lambda x: x > 4))
      .to_list()
    )
    assert result == [6, 8]


class TestPipelineTerminalOperations:
  """Test terminal operations that consume the pipeline."""

  def test_each_applies_side_effects(self):
    """Test each applies function to all elements."""
    results = []
    Pipeline([1, 2, 3]).each(lambda x: results.append(x * 2))
    assert results == [2, 4, 6]

  def test_first_gets_n_elements(self):
    """Test first gets specified number of elements."""
    result = Pipeline([1, 2, 3, 4, 5]).first(3)
    assert result == [1, 2, 3]

  def test_first_default_one_element(self):
    """Test first with no argument gets one element."""
    result = Pipeline([1, 2, 3]).first()
    assert result == [1]

  def test_first_with_insufficient_data(self):
    """Test first when requesting more elements than available."""
    result = Pipeline([1, 2]).first(5)
    assert result == [1, 2]

  def test_consume_processes_without_return(self):
    """Test consume processes all elements without returning anything."""
    side_effects = []
    transformer = Transformer.init(int).tap(lambda x: side_effects.append(x))
    result = Pipeline([1, 2, 3]).apply(transformer).consume()

    assert result is None
    assert side_effects == [1, 2, 3]


class TestPipelineDataTypes:
  """Test pipeline with various data types."""

  def test_string_processing(self):
    """Test pipeline with string data."""
    result = Pipeline(["hello", "world"]).transform(lambda t: t.map(lambda x: x.upper())).to_list()
    assert result == ["HELLO", "WORLD"]

  def test_mixed_types_processing(self):
    """Test pipeline with mixed data types."""
    result = Pipeline([1, "hello", 3.14]).transform(lambda t: t.map(lambda x: str(x))).to_list()
    assert result == ["1", "hello", "3.14"]

  def test_complex_objects_processing(self):
    """Test pipeline with complex objects."""
    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    result = Pipeline(data).transform(lambda t: t.map(lambda x: x["name"])).to_list()
    assert result == ["Alice", "Bob"]


class TestPipelineEdgeCases:
  """Test edge cases and boundary conditions."""

  def test_empty_pipeline(self):
    """Test pipeline with empty data."""
    assert Pipeline([]).to_list() == []

    # Test terminal operations on empty pipeline
    results = []
    Pipeline([]).each(lambda x: results.append(x))
    assert results == []

    assert Pipeline([]).first(5) == []
    assert Pipeline([]).consume() is None

  def test_single_element_pipeline(self):
    """Test pipeline with single element."""
    assert Pipeline([42]).to_list() == [42]

  def test_type_preservation(self):
    """Test that pipeline preserves and transforms types correctly."""
    # Integers preserved
    int_result = Pipeline([1, 2, 3]).to_list()
    assert all(isinstance(x, int) for x in int_result)

    # Transform to strings
    str_result = Pipeline([1, 2, 3]).transform(lambda t: t.map(lambda x: str(x))).to_list()
    assert all(isinstance(x, str) for x in str_result)
    assert str_result == ["1", "2", "3"]


class TestPipelinePerformance:
  """Test pipeline performance and chunking characteristics."""

  def test_large_dataset_processing(self):
    """Test pipeline handles large datasets efficiently."""
    large_data = list(range(10000))
    result = Pipeline(large_data).transform(lambda t: t.map(lambda x: x * 2).filter(lambda x: x % 100 == 0)).to_list()

    # Every 50th element doubled (0, 100, 200, ..., 19800)
    expected = [x * 2 for x in range(0, 10000, 50)]
    assert result == expected

  def test_chunked_processing_consistency(self):
    """Test that chunked processing produces consistent results."""
    # Use small chunk size to test chunking behavior
    transformer = Transformer.init(int, chunk_size=10).map(lambda x: x + 1)
    result = Pipeline(list(range(100))).apply(transformer).to_list()

    expected = list(range(1, 101))  # [1, 2, 3, ..., 100]
    assert result == expected
