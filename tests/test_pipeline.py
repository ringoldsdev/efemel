from efemel.pipeline import SYMBOL_END, SYMBOL_RESET, Pipeline


class TestPipeline:
  """Test suite for the Pipeline class."""

  def test_identity_transformation(self):
    """Test that identity transformation passes values through unchanged."""
    pipeline = Pipeline()

    # Test with different data types
    assert pipeline.run(5) == 5
    assert pipeline.run("hello") == "hello"
    assert pipeline.run([1, 2, 3]) == [1, 2, 3]
    assert pipeline.run({"key": "value"}) == {"key": "value"}
    assert pipeline.run(None) is None

  def test_identity_reset(self):
    """Test that identity() resets the pipeline to initial state."""
    pipeline = Pipeline()

    # Add some transformations
    pipeline.map(lambda x: x * 2).filter(lambda x: x > 10)

    # Reset to identity
    pipeline.identity()

    # Should now pass values through unchanged
    assert pipeline.run(5) == 5

  def test_map_basic_transformation(self):
    """Test basic map transformations."""
    pipeline = Pipeline()

    # Double numbers
    result = pipeline.map(lambda x: x * 2).run(5)
    assert result == 10

    # Transform strings
    pipeline = Pipeline()
    result = pipeline.map(str.upper).run("hello")
    assert result == "HELLO"

  def test_map_chaining(self):
    """Test chaining multiple map operations."""
    pipeline = Pipeline()

    # Chain multiple maps: 5 * 2 = 10, 10 + 1 = 11
    result = pipeline.map(lambda x: x * 2).map(lambda x: x + 1).run(5)
    assert result == 11

  def test_map_failure_handling(self):
    """Test that map failures are handled properly."""
    pipeline = Pipeline()

    # Division by zero should cause failure
    result = pipeline.map(lambda x: x / 0).run(5)
    assert result is None

    # Exception in map function should cause failure
    result = pipeline.map(lambda x: x.nonexistent_method()).run(5)
    assert result is None

  def test_filter_basic_operation(self):
    """Test basic filter operations."""
    pipeline = Pipeline()

    # Even numbers pass
    result = pipeline.filter(lambda x: x % 2 == 0).run(4)
    assert result == 4

    # Odd numbers fail
    result = pipeline.filter(lambda x: x % 2 == 0).run(5)
    assert result is None

  def test_filter_with_strings(self):
    """Test filter operations with strings."""
    pipeline = Pipeline()

    # Non-empty strings pass
    result = pipeline.filter(lambda s: len(s) > 0).run("hello")
    assert result == "hello"

    # Empty strings fail
    result = pipeline.filter(lambda s: len(s) > 0).run("")
    assert result is None

  def test_map_filter_chaining(self):
    """Test chaining map and filter operations."""
    pipeline = Pipeline()

    # 6 * 2 = 12, 12 > 10 is True
    result = pipeline.map(lambda x: x * 2).filter(lambda x: x > 10).run(6)
    assert result == 12

    # 6 * 2 = 12, 12 > 20 is False
    pipeline = Pipeline()
    result = pipeline.map(lambda x: x * 2).filter(lambda x: x > 20).run(6)
    assert result is None

  def test_reduce_sum_accumulation(self):
    """Test reduce operation with sum accumulation."""
    pipeline = Pipeline()
    pipeline.reduce(lambda acc, x: acc + x, 0)

    # Add numbers to accumulator
    pipeline.run(5)  # 0 + 5 = 5
    pipeline.run(3)  # 5 + 3 = 8
    pipeline.run(2)  # 8 + 2 = 10

    # Get final result
    result = pipeline.run(SYMBOL_END)
    assert result == 10

  def test_reduce_reset_functionality(self):
    """Test reduce reset functionality."""
    pipeline = Pipeline()
    pipeline.reduce(lambda acc, x: acc + x, 0)

    # Accumulate some values
    pipeline.run(5)
    pipeline.run(3)

    # Reset and start over
    pipeline.run(SYMBOL_RESET)
    pipeline.run(7)

    result = pipeline.run(SYMBOL_END)
    assert result == 7

  def test_reduce_list_accumulation(self):
    """Test reduce operation with list accumulation."""
    pipeline = Pipeline()
    pipeline.reduce(lambda acc, x: acc + [x], [])

    pipeline.run("a")
    pipeline.run("b")
    pipeline.run("c")

    result = pipeline.run(SYMBOL_END)
    assert result == ["a", "b", "c"]

  def test_reduce_object_accumulation(self):
    """Test reduce operation with object accumulation."""
    pipeline = Pipeline()
    pipeline.reduce(lambda acc, item: {**acc, **item}, {})

    pipeline.run({"name": "John"})
    pipeline.run({"age": 30})
    pipeline.run({"city": "NYC"})

    result = pipeline.run(SYMBOL_END)
    assert result == {"name": "John", "age": 30, "city": "NYC"}

  def test_pipeline_failure_propagation(self):
    """Test that failures propagate through the pipeline."""
    pipeline = Pipeline()

    # Filter that fails should make entire pipeline fail
    result = pipeline.map(lambda x: x * 2).filter(lambda x: x > 100).map(lambda x: x + 1).run(10)

    # 10 * 2 = 20, 20 > 100 is False, so pipeline fails
    assert result is None

  def test_pipeline_with_none_input(self):
    """Test pipeline behavior with None input."""
    pipeline = Pipeline()

    # Identity should pass None through
    assert pipeline.run(None) is None

    # Map should work with None if function handles it
    pipeline = Pipeline()
    result = pipeline.map(lambda x: x if x is None else x * 2).run(None)
    assert result is None

  def test_filter_exception_handling(self):
    """Test that exceptions in filter predicates are handled."""
    pipeline = Pipeline()

    # Exception in predicate should cause failure
    result = pipeline.filter(lambda x: x.nonexistent_method()).run(5)
    assert result is None

  def test_reduce_exception_handling(self):
    """Test that exceptions in reduce accumulator are handled."""
    pipeline = Pipeline()
    pipeline.reduce(lambda acc, x: acc / x, 1)  # Will cause division by zero

    pipeline.run(0)  # This should cause an exception in the accumulator

    # The pipeline should handle the exception gracefully
    # Note: The exact behavior depends on implementation details
    # This test ensures no unhandled exceptions occur

  def test_pipeline_reuse(self):
    """Test that pipelines can be reused with different inputs."""
    pipeline = Pipeline()
    pipeline.map(lambda x: x * 2).filter(lambda x: x > 5)

    # Test with different inputs
    assert pipeline.run(3) == 6  # 3 * 2 = 6, 6 > 5
    assert pipeline.run(2) is None  # 2 * 2 = 4, 4 > 5 is False
    assert pipeline.run(5) == 10  # 5 * 2 = 10, 10 > 5

  def test_symbol_end_and_reset_constants(self):
    """Test that SYMBOL_END and SYMBOL_RESET are proper constants."""
    # These should be singleton instances
    assert SYMBOL_END is SYMBOL_END
    assert SYMBOL_RESET is SYMBOL_RESET
    assert SYMBOL_END is not SYMBOL_RESET

    # Test string representations
    assert str(SYMBOL_END) == "SymbolEnd"
    assert str(SYMBOL_RESET) == "SymbolReset"

  def test_pipeline_method_chaining_returns_self(self):
    """Test that all pipeline methods return self for chaining."""
    pipeline = Pipeline()

    # All these should return the same pipeline instance
    assert pipeline.identity() is pipeline
    assert pipeline.map(lambda x: x) is pipeline
    assert pipeline.filter(lambda x: True) is pipeline
    assert pipeline.reduce(lambda acc, x: acc, 0) is pipeline
