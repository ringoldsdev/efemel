"""Tests for the Transformer class."""

import pytest

from efemel.pipeline.errors import ErrorHandler
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
    transformer = Transformer().map(lambda x, ctx: x * ctx["multiplier"])
    result = list(transformer([1, 2, 3], context))
    assert result == [3, 6, 9]

  def test_filter_keeps_matching_elements(self):
    """Test filter keeps only matching elements."""
    transformer = Transformer.init(int).filter(lambda x: x % 2 == 0)
    result = list(transformer([1, 2, 3, 4, 5, 6]))
    assert result == [2, 4, 6]

  def test_filter_with_context_aware_function(self):
    """Test filter with context-aware function."""
    context = PipelineContext({"threshold": 3})
    transformer = Transformer().filter(lambda x, ctx: x > ctx["threshold"])
    result = list(transformer([1, 2, 3, 4, 5], context))
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
    transformer = Transformer().tap(lambda x, ctx: side_effects.append(f"{ctx['prefix']}{x}"))
    result = list(transformer([1, 2, 3], context))

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
    transformer = Transformer()
    reducer = transformer.reduce(lambda acc, x, ctx: acc + (x * ctx["multiplier"]), initial=0)
    result = list(reducer([1, 2, 3], context))
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


class TestTransformerFromTransformer:
  """Test the from_transformer class method."""

  def test_from_transformer_copies_logic(self):
    """Test that from_transformer copies transformation logic."""
    # Create a transformer with some operations
    source = Transformer.init(int, chunk_size=50).map(lambda x: x * 3).filter(lambda x: x > 6)

    # Create new transformer from the source
    target = Transformer.from_transformer(source)

    # Test both produce same results
    data = [1, 2, 3, 4, 5]
    source_result = list(source(data))
    target_result = list(target(data))

    assert source_result == target_result
    assert target.chunk_size == 50  # Chunk size should be copied

  def test_from_transformer_with_custom_parameters(self):
    """Test from_transformer with custom parameters."""
    source = Transformer.init(int).map(lambda x: x * 2)

    target = Transformer.from_transformer(source, chunk_size=200)

    assert target.chunk_size == 200  # Custom chunk size

    # Should still have same transformation logic
    data = [1, 2, 3]
    assert list(source(data)) == list(target(data))


class TestSafeTransformer:
  def test_safe_with_no_errors(self):
    """Test safe run with successful transformation."""
    transformer = Transformer.init(int).catch(lambda t: t.map(lambda x: x * 2))
    data = [1, 2, 3]
    result = list(transformer(data))
    assert result == [2, 4, 6]

  def test_safe_with_error_handling(self):
    """Test safe run with error handling."""
    errored_chunks = []
    transformer = Transformer.init(int, chunk_size=1).catch(
      lambda t: t.map(lambda x: x / 0),  # This will raise an error
      on_error=lambda chunk, error, context: errored_chunks.append(chunk),  # Return 0 on error
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

    transformer = Transformer.init(int, chunk_size=1).on_error(error_handler).catch(lambda t: t.map(lambda x: x / 0))
    data = [1, 2, 3]
    result = list(transformer(data))

    assert result == []
    # Note that we get 3 values back because we've specified chunk_size=1
    assert errored_chunks == [[1], [2], [3]]

  def test_safe_with_short_circuit(self):
    """Test safe run with error handling."""

    def set_error_context(_chunk, _error, context):
      context["error_occurred"] = True

    transformer = (
      Transformer.init(int, chunk_size=1)
      .catch(
        lambda t: t.map(lambda x: x / 0),  # This will raise an error
        on_error=set_error_context,
      )
      .short_circuit(lambda ctx: ctx["error_occurred"])
    )

    data = [1, 2, 3]
    with pytest.raises(RuntimeError):
      list(transformer(data))

  def test_safe_with_short_circuit_that_raises(self):
    """Test safe run with error handling."""

    def set_error_context(_chunk, _error, context):
      context["error_occurred"] = True

    def raise_on_context_error(ctx):
      if ctx.get("error_occurred"):
        raise RuntimeError("Short-circuit condition met, stopping execution.")

    transformer = (
      Transformer.init(int, chunk_size=1)
      .catch(
        lambda t: t.map(lambda x: x / 0),  # This will raise an error
        on_error=set_error_context,
      )
      .short_circuit(raise_on_context_error)
    )

    data = [1, 2, 3]
    with pytest.raises(RuntimeError):
      list(transformer(data))
