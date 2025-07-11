"""
Test Pipeline composition functionality.

This module contains tests for Pipeline composition including
pipeline chaining, from_pipeline method, and complex compositions.
"""

from efemel.pipeline import Pipeline


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
