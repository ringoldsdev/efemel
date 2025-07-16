"""Tests for the Transformer class."""

import pytest

from efemel.pipeline.errors import ErrorHandler
from efemel.pipeline.transformers.transformer import PipelineContext
from efemel.pipeline.transformers.transformer import Transformer


class TestTransformerBasics:
  """Test core transformer functionality."""

  def test_identity_transformer(self):
    """Test that init creates an identity transformer."""
    transformer = Transformer.init(int)
    result = list(transformer([1, 2, 3]))
    assert result == [1, 2, 3]

  def test_custom_chunk_size(self):
    """Test transformer with custom chunk size."""
    transformer = Transformer.init(int, chunk_size=2)
    assert transformer.chunk_size == 2
    # Functionality should work regardless of chunk size
    result = list(transformer([1, 2, 3, 4]))
    assert result == [1, 2, 3, 4]


class TestTransformerOperations:
  """Test individual transformer operations."""

  def test_map_transformation(self):
    """Test map transforms each element."""
    transformer = Transformer.init(int).map(lambda x: x * 2)
    result = list(transformer([1, 2, 3]))
    assert result == [2, 4, 6]

  def test_filter_operation(self):
    """Test filter keeps only matching elements."""
    transformer = Transformer.init(int).filter(lambda x: x % 2 == 0)
    result = list(transformer([1, 2, 3, 4, 5, 6]))
    assert result == [2, 4, 6]

  def test_flatten_operation(self):
    """Test flatten with various iterable types."""
    # Test with lists
    transformer = Transformer.init(list).flatten()
    result = list(transformer([[1, 2], [3, 4], [5]]))
    assert result == [1, 2, 3, 4, 5]

  def test_tap_side_effects(self):
    """Test tap applies side effects without modifying data."""
    side_effects = []
    transformer = Transformer.init(int).tap(lambda x: side_effects.append(x))
    result = list(transformer([1, 2, 3]))

    assert result == [1, 2, 3]  # Data unchanged
    assert side_effects == [1, 2, 3]  # Side effect applied


class TestTransformerContextSupport:
  """Test context-aware transformer operations."""

  def test_map_with_context(self):
    """Test map with context-aware function."""
    context = PipelineContext({"multiplier": 3})
    transformer = Transformer().map(lambda x, ctx: x * ctx["multiplier"])
    result = list(transformer([1, 2, 3], context))
    assert result == [3, 6, 9]

  def test_filter_with_context(self):
    """Test filter with context-aware function."""
    context = PipelineContext({"threshold": 3})
    transformer = Transformer().filter(lambda x, ctx: x > ctx["threshold"])
    result = list(transformer([1, 2, 3, 4, 5], context))
    assert result == [4, 5]

  def test_tap_with_context(self):
    """Test tap with context-aware function."""
    side_effects = []
    context = PipelineContext({"prefix": "item:"})
    transformer = Transformer().tap(lambda x, ctx: side_effects.append(f"{ctx['prefix']}{x}"))
    result = list(transformer([1, 2, 3], context))

    assert result == [1, 2, 3]
    assert side_effects == ["item:1", "item:2", "item:3"]


class TestTransformerChaining:
  """Test chaining multiple transformer operations."""

  def test_map_filter_chain(self):
    """Test map followed by filter."""
    transformer = Transformer.init(int).map(lambda x: x * 2).filter(lambda x: x > 4)
    result = list(transformer([1, 2, 3, 4]))
    assert result == [6, 8]

  def test_complex_operation_chain(self):
    """Test complex chain with multiple operations."""
    transformer = (
      Transformer.init(int)
      .map(lambda x: [x, x * 2])  # Create pairs
      .flatten()  # Flatten to single list
      .filter(lambda x: x > 3)  # Keep values > 3
    )
    result = list(transformer([1, 2, 3]))
    assert result == [4, 6]  # [[1,2], [2,4], [3,6]] -> [1,2,2,4,3,6] -> [4,6]

  def test_transformer_composition(self):
    """Test transformer composition with apply."""
    base_transformer = Transformer.init(int).map(lambda x: x * 2)
    composed_transformer = base_transformer.apply(lambda t: t.filter(lambda x: x > 4))
    result = list(composed_transformer([1, 2, 3, 4]))
    assert result == [6, 8]


class TestTransformerReduceOperations:
  """Test terminal reduce operations."""

  def test_basic_reduce(self):
    """Test reduce with sum operation."""
    transformer = Transformer.init(int)
    reducer = transformer.reduce(lambda acc, x: acc + x, initial=0)
    result = list(reducer([1, 2, 3, 4]))
    assert result == [10]

  def test_reduce_with_context(self):
    """Test reduce with context-aware function."""
    context = PipelineContext({"multiplier": 2})
    transformer = Transformer()
    reducer = transformer.reduce(lambda acc, x, ctx: acc + (x * ctx["multiplier"]), initial=0)
    result = list(reducer([1, 2, 3], context))
    assert result == [12]  # (1*2) + (2*2) + (3*2) = 12

  def test_reduce_after_transformation(self):
    """Test reduce after map transformation."""
    transformer = Transformer.init(int).map(lambda x: x * 2)
    reducer = transformer.reduce(lambda acc, x: acc + x, initial=0)
    result = list(reducer([1, 2, 3]))
    assert result == [12]  # [2, 4, 6] summed = 12


class TestTransformerEdgeCases:
  """Test edge cases and boundary conditions."""

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

  def test_chunking_behavior(self):
    """Test that chunking doesn't affect final results."""
    data = list(range(100))

    # Small chunks
    small_chunk_transformer = Transformer.init(int, chunk_size=5).map(lambda x: x * 2)
    small_result = list(small_chunk_transformer(data))

    # Large chunks
    large_chunk_transformer = Transformer.init(int, chunk_size=50).map(lambda x: x * 2)
    large_result = list(large_chunk_transformer(data))

    # Results should be identical regardless of chunk size
    assert small_result == large_result


class TestTransformerFromTransformer:
  """Test transformer copying and creation from existing transformers."""

  def test_copy_transformer_logic(self):
    """Test that from_transformer copies transformation logic."""
    source = Transformer.init(int, chunk_size=50).map(lambda x: x * 3).filter(lambda x: x > 6)
    target = Transformer.from_transformer(source)

    data = [1, 2, 3, 4, 5]
    source_result = list(source(data))
    target_result = list(target(data))

    assert source_result == target_result
    assert target.chunk_size == 50

  def test_copy_with_custom_parameters(self):
    """Test from_transformer with custom parameters."""
    source = Transformer.init(int).map(lambda x: x * 2)
    target = Transformer.from_transformer(source, chunk_size=200)

    assert target.chunk_size == 200
    # Should still have same transformation logic
    data = [1, 2, 3]
    assert list(source(data)) == list(target(data))


class TestTransformerErrorHandling:
  """Test error handling and safe operations."""

  def test_catch_with_successful_operation(self):
    """Test catch with successful transformation."""
    transformer = Transformer.init(int).catch(lambda t: t.map(lambda x: x * 2))
    result = list(transformer([1, 2, 3]))
    assert result == [2, 4, 6]

  def test_catch_with_error_isolation(self):
    """Test catch isolates errors to specific chunks."""
    errored_chunks = []
    transformer = Transformer.init(int, chunk_size=1).catch(
      lambda t: t.map(lambda x: x / 0),  # Division by zero
      on_error=lambda chunk, error, context: errored_chunks.append(chunk),
    )
    result = list(transformer([1, 2, 3]))

    assert result == []  # All operations failed
    assert errored_chunks == [[1], [2], [3]]  # Each chunk failed individually

  def test_global_error_handler(self):
    """Test global error handling through error handler."""
    errored_chunks = []
    error_handler = ErrorHandler()
    error_handler.on_error(lambda chunk, error, context: errored_chunks.append(chunk))

    transformer = Transformer.init(int, chunk_size=1).on_error(error_handler).catch(lambda t: t.map(lambda x: x / 0))

    list(transformer([1, 2, 3]))
    assert errored_chunks == [[1], [2], [3]]

  def test_short_circuit_on_error(self):
    """Test short-circuit behavior when errors occur."""

    def set_error_flag(_chunk, _error, context):
      context["error_occurred"] = True

    transformer = (
      Transformer.init(int, chunk_size=1)
      .catch(
        lambda t: t.map(lambda x: x / 0),
        on_error=set_error_flag,
      )
      .short_circuit(lambda ctx: ctx.get("error_occurred", False))
    )

    with pytest.raises(RuntimeError):
      list(transformer([1, 2, 3]))

  def test_short_circuit_with_custom_exception(self):
    """Test short-circuit with custom exception raising."""

    def set_error_flag(_chunk, _error, context):
      context["error_occurred"] = True

    def raise_on_error(ctx):
      if ctx.get("error_occurred"):
        raise RuntimeError("Short-circuit condition met, stopping execution.")

    transformer = (
      Transformer.init(int, chunk_size=1)
      .catch(
        lambda t: t.map(lambda x: x / 0),
        on_error=set_error_flag,
      )
      .short_circuit(raise_on_error)
    )

    with pytest.raises(RuntimeError, match="Short-circuit condition met"):
      list(transformer([1, 2, 3]))
