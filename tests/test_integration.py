"""Integration tests for Pipeline and Transformer working together."""

from efemel.pipeline.pipeline import Pipeline
from efemel.pipeline.transformers.transformer import PipelineContext
from efemel.pipeline.transformers.transformer import Transformer


class TestPipelineTransformerIntegration:
  """Test Pipeline and Transformer integration."""

  def test_basic_integration(self):
    """Test basic pipeline and transformer integration."""
    # Create a transformer that doubles and filters
    transformer = Transformer.init(int).map(lambda x: x * 2).filter(lambda x: x > 5)

    # Apply to pipeline
    result = Pipeline([1, 2, 3, 4, 5]).apply(transformer).to_list()
    assert result == [6, 8, 10]

  def test_context_sharing(self):
    """Test that context is properly shared in transformations."""
    context = PipelineContext({"multiplier": 3, "threshold": 5})

    transformer = (
      Transformer(context=context).map(lambda x, ctx: x * ctx["multiplier"]).filter(lambda x, ctx: x > ctx["threshold"])
    )

    result = Pipeline([1, 2, 3]).apply(transformer).to_list()
    assert result == [6, 9]  # [3, 6, 9] filtered to [6, 9]

  def test_reduce_integration(self):
    """Test reduce operation with pipeline."""
    transformer = Transformer.init(int).map(lambda x: x * 2)
    reducer = transformer.reduce(lambda acc, x: acc + x, initial=0)

    result = list(reducer([1, 2, 3, 4]))
    assert result == [20]  # [2, 4, 6, 8] summed = 20

  def test_complex_chain_integration(self):
    """Test complex chain of operations."""
    # Transform: double -> flatten -> filter -> tap
    side_effects = []

    transformer = (
      Transformer.init(int)
      .map(lambda x: [x, x * 2])  # Create pairs
      .flatten()  # Flatten to single list
      .filter(lambda x: x % 3 == 0)  # Keep multiples of 3
      .tap(lambda x: side_effects.append(f"processed: {x}"))
    )

    result = Pipeline([1, 2, 3, 6]).apply(transformer).to_list()

    # Expected: [1,2,2,4,3,6,6,12] -> [3,6,6,12] (multiples of 3)
    assert result == [3, 6, 6, 12]
    assert side_effects == ["processed: 3", "processed: 6", "processed: 6", "processed: 12"]

  def test_multiple_transformer_applications(self):
    """Test applying multiple transformers in sequence."""
    t1 = Transformer.init(int).map(lambda x: x * 2)
    t2 = Transformer.init(int).filter(lambda x: x > 5)
    t3 = Transformer.init(int).map(lambda x: x + 1)

    result = (
      Pipeline([1, 2, 3, 4, 5])
      .apply(t1)  # [2, 4, 6, 8, 10]
      .apply(t2)  # [6, 8, 10]
      .apply(t3)  # [7, 9, 11]
      .to_list()
    )

    assert result == [7, 9, 11]

  def test_transform_shorthand_integration(self):
    """Test transform shorthand method integration."""
    result = (
      Pipeline([1, 2, 3, 4, 5])
      .transform(lambda t: t.map(lambda x: x * 3))
      .transform(lambda t: t.filter(lambda x: x > 6))
      .to_list()
    )

    assert result == [9, 12, 15]  # [3, 6, 9, 12, 15] -> [9, 12, 15]

  def test_mixed_operations(self):
    """Test mixing transform shorthand and apply methods."""
    transformer = Transformer.init(int).filter(lambda x: x < 10)

    result = (
      Pipeline([1, 2, 3, 4, 5])
      .transform(lambda t: t.map(lambda x: x * 2))  # [2, 4, 6, 8, 10]
      .apply(transformer)  # [2, 4, 6, 8]
      .transform(lambda t: t.map(lambda x: x + 1))  # [3, 5, 7, 9]
      .to_list()
    )

    assert result == [3, 5, 7, 9]


class TestPipelineDataProcessingPatterns:
  """Test common data processing patterns."""

  def test_etl_pattern(self):
    """Test Extract-Transform-Load pattern."""
    # Simulate raw data extraction
    raw_data = [
      {"name": "Alice", "age": 25, "salary": 50000},
      {"name": "Bob", "age": 30, "salary": 60000},
      {"name": "Charlie", "age": 35, "salary": 70000},
      {"name": "David", "age": 28, "salary": 55000},
    ]

    # Transform: extract names of people over 28 with salary > 55000
    result = (
      Pipeline(raw_data)
      .transform(lambda t: t.filter(lambda x: x["age"] > 28 and x["salary"] > 55000))
      .transform(lambda t: t.map(lambda x: x["name"]))
      .to_list()
    )

    assert result == ["Bob", "Charlie"]

  def test_data_aggregation_pattern(self):
    """Test data aggregation pattern."""
    # Group and count pattern
    data = ["apple", "banana", "apple", "cherry", "banana", "apple"]

    # Count occurrences
    counts = {}
    (Pipeline(data).transform(lambda t: t.tap(lambda x: counts.update({x: counts.get(x, 0) + 1}))).consume())

    assert counts == {"apple": 3, "banana": 2, "cherry": 1}

  def test_map_reduce_pattern(self):
    """Test map-reduce pattern."""
    # Map: square numbers, Reduce: sum them
    transformer = Transformer.init(int).map(lambda x: x * x)  # Square

    reducer = transformer.reduce(lambda acc, x: acc + x, initial=0)  # Sum

    result = list(reducer([1, 2, 3, 4, 5]))
    assert result == [55]  # 1 + 4 + 9 + 16 + 25 = 55

  def test_filtering_and_transformation_pattern(self):
    """Test filtering and transformation pattern."""
    # Process only even numbers, double them, then sum
    even_numbers = []
    transformer = (
      Transformer.init(int).filter(lambda x: x % 2 == 0).tap(lambda x: even_numbers.append(x)).map(lambda x: x * 2)
    )

    result = Pipeline(range(1, 11)).apply(transformer).to_list()

    assert even_numbers == [2, 4, 6, 8, 10]
    assert result == [4, 8, 12, 16, 20]

  def test_data_validation_pattern(self):
    """Test data validation pattern."""
    # Validate and clean data
    raw_data = [1, "2", 3.0, "invalid", 5, None, 7]

    valid_numbers = []

    def validate_and_convert(x):
      try:
        num = float(x) if x is not None else None
        if num is not None and not str(x).lower() == "invalid":
          valid_numbers.append(num)
          return int(num)
        return None
      except (ValueError, TypeError):
        return None

    result = (
      Pipeline(raw_data)
      .transform(lambda t: t.map(validate_and_convert))
      .transform(lambda t: t.filter(lambda x: x is not None))
      .to_list()
    )

    assert result == [1, 2, 3, 5, 7]
    assert valid_numbers == [1.0, 2.0, 3.0, 5.0, 7.0]


class TestPipelinePerformanceIntegration:
  """Test performance aspects of pipeline and transformer integration."""

  def test_large_dataset_chunked_processing(self):
    """Test chunked processing with large datasets."""
    # Process 10,000 numbers with small chunk size
    transformer = Transformer.init(int, chunk_size=100).map(lambda x: x * 2).filter(lambda x: x % 1000 == 0)

    large_data = range(10000)
    result = Pipeline(large_data).apply(transformer).to_list()

    # Should get multiples of 500 doubled (0, 1000, 2000, ..., 18000)
    expected = [x * 2 for x in range(0, 10000, 500)]
    assert result == expected

  def test_memory_efficient_processing(self):
    """Test memory-efficient lazy processing."""
    # Process large dataset but only take first few results
    transformer = Transformer.init(int).map(lambda x: x**2).filter(lambda x: x > 100)

    large_data = range(1000)
    result = Pipeline(large_data).apply(transformer).first(5)

    # First 5 squares > 100: 121, 144, 169, 196, 225
    assert result == [121, 144, 169, 196, 225]

  def test_streaming_processing(self):
    """Test streaming-like processing pattern."""
    # Simulate processing data as it arrives
    batches = [[1, 2], [3, 4], [5, 6]]
    results = []

    for batch in batches:
      batch_result = Pipeline(batch).transform(lambda t: t.map(lambda x: x * 3)).to_list()
      results.extend(batch_result)

    assert results == [3, 6, 9, 12, 15, 18]
