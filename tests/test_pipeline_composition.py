"""
Test Pipeline composition functionality.

This module contains tests for Pipeline composition including
pipeline chaining, from_pipeline method, and complex compositions.
"""

from efemel.pipeline import Pipeline


class TestPipelineComposition:
  """Test Pipeline composition functionality."""

  def test_pipeline_apply_method(self):
    """Test applying one pipeline to another using apply method."""
    # Create source pipeline that doubles numbers
    doubler_pipeline = Pipeline().map(lambda x: x * 2)

    # Create main pipeline that adds 1
    main_pipeline = Pipeline().map(lambda x: x + 1)

    # Apply the doubler to the main pipeline
    composed = main_pipeline.apply(doubler_pipeline)

    # Test the composition: first add 1, then double
    result = composed.to_list([1, 2, 3, 4, 5])
    assert result == [4, 6, 8, 10, 12]  # (1+1)*2, (2+1)*2, (3+1)*2, (4+1)*2, (5+1)*2

  def test_pipeline_chaining_with_multiple_data_sources(self):
    """Test chaining operations with multiple data sources."""
    pipeline = Pipeline()

    # Chain operations: double, then filter even, then add 10
    result = pipeline.map(lambda x: x * 2).filter(lambda x: x % 2 == 0).map(lambda x: x + 10)

    # Test with multiple data sources
    data1 = [1, 2, 3]
    data2 = [4, 5, 6]
    result_list = result.to_list(data1, data2)

    # Expected: double [1,2,3,4,5,6] -> [2,4,6,8,10,12], filter even -> [2,4,6,8,10,12], add 10 -> [12,14,16,18,20,22]
    assert result_list == [12, 14, 16, 18, 20, 22]

  def test_complex_composition(self):
    """Test complex pipeline composition."""
    # Create a pipeline that processes data in multiple steps
    pipeline = Pipeline()

    # Complex chain: map to square, filter > 10, map to string, filter length > 1
    result = pipeline.map(lambda x: x**2).filter(lambda x: x > 10).map(str).filter(lambda s: len(s) > 1)

    # Test with data [1, 2, 3, 4, 5, 6]
    # Square: [1, 4, 9, 16, 25, 36]
    # Filter > 10: [16, 25, 36]
    # To string: ["16", "25", "36"]
    # Filter length > 1: ["16", "25", "36"] (all have length 2)
    result_list = result.to_list([1, 2, 3, 4, 5, 6])
    assert result_list == ["16", "25", "36"]

  def test_pipeline_apply_with_empty_data(self):
    """Test apply method with empty data."""
    doubler = Pipeline().map(lambda x: x * 2)
    main = Pipeline().map(lambda x: x + 1)

    composed = main.apply(doubler)
    result = composed.to_list([])
    assert result == []

  def test_pipeline_apply_with_filters(self):
    """Test apply method combining filters and maps."""
    # Create a pipeline that filters even numbers
    even_filter = Pipeline().filter(lambda x: x % 2 == 0)

    # Create a pipeline that doubles numbers
    doubler = Pipeline().map(lambda x: x * 2)

    # Apply even filter first, then doubler
    composed = even_filter.apply(doubler)

    result = composed.to_list([1, 2, 3, 4, 5, 6])
    assert result == [4, 8, 12]  # Even numbers [2, 4, 6] doubled

  def test_multiple_pipeline_applications(self):
    """Test applying multiple pipelines in sequence."""
    # Create individual transformation pipelines
    add_one = Pipeline().map(lambda x: x + 1)
    double = Pipeline().map(lambda x: x * 2)
    to_string = Pipeline().map(str)

    # Chain them using apply
    result_pipeline = add_one.apply(double).apply(to_string)

    # Test: (1+1)*2=4, (2+1)*2=6, (3+1)*2=8 -> ["4", "6", "8"]
    result = result_pipeline.to_list([1, 2, 3])
    assert result == ["4", "6", "8"]

  def test_complex_pipeline_composition(self):
    """Test complex pipeline composition scenario."""
    # Use a single pipeline with multiple data sources instead of chaining
    pipeline = Pipeline()

    # Apply transformations: filter > 3, square, then reduce to sum
    result = (
      pipeline.filter(lambda x: x > 3)
      .map(lambda x: x**2)
      .reduce([2, 4, 6, 8], [1, 3, 5, 7], function=lambda acc, x: acc + x, initial=0)
    )

    # Data: [2, 4, 6, 8] + [1, 3, 5, 7] = [2, 4, 6, 8, 1, 3, 5, 7]
    # Filter > 3: [4, 6, 8, 5, 7]
    # Square: [16, 36, 64, 25, 49]
    # Sum: 190
    assert result == 190
