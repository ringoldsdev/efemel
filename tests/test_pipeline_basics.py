"""
Test basic Pipeline functionality.

This module contains tests for basic Pipeline class functionality
including initialization, iteration, and core methods.
"""

from efemel.pipeline import Pipeline


class TestPipelineBasics:
  """Test basic Pipeline functionality."""

  def test_pipeline_initialization(self):
    """Test Pipeline initialization with various iterables."""
    # Test with default parameters
    pipeline = Pipeline()
    assert isinstance(pipeline, Pipeline)
    assert pipeline.chunk_size == 1000
    assert isinstance(pipeline.context, dict)

    # Test with custom chunk size
    pipeline = Pipeline(chunk_size=500)
    assert pipeline.chunk_size == 500

    # Test with custom context
    from efemel.pipeline import PipelineContext

    custom_context = PipelineContext()
    custom_context["key"] = "value"
    pipeline = Pipeline(context=custom_context)
    assert pipeline.context["key"] == "value"

  def test_pipeline_iteration(self):
    """Test Pipeline iteration behavior through callable interface."""
    pipeline = Pipeline()

    # Test iteration via __call__
    data = [1, 2, 3, 4, 5]
    result = []
    for item in pipeline(data):
      result.append(item)

    assert result == [1, 2, 3, 4, 5]

    # Test with multiple data sources
    result2 = list(pipeline([1, 2], [3, 4, 5]))
    assert result2 == [1, 2, 3, 4, 5]

  def test_to_list(self):
    """Test Pipeline.to_list() method."""
    pipeline = Pipeline()
    result = pipeline.to_list([1, 2, 3, 4, 5])

    assert result == [1, 2, 3, 4, 5]
    assert isinstance(result, list)

    # Test with empty pipeline
    assert pipeline.to_list([]) == []

    # Test with multiple data sources
    result2 = pipeline.to_list([1, 2], [3, 4, 5])
    assert result2 == [1, 2, 3, 4, 5]

  def test_first(self):
    """Test Pipeline.first() method."""
    pipeline = Pipeline()
    result = pipeline.first([1, 2, 3, 4, 5])
    assert result == [1]

    # Test with string
    result = pipeline.first(["hello", "world"])
    assert result == ["hello"]

    # Test first n elements
    result = pipeline.first([1, 2, 3, 4, 5], n=3)
    assert result == [1, 2, 3]

  def test_first_empty_pipeline(self):
    """Test Pipeline.first() with empty pipeline."""
    pipeline = Pipeline()
    result = pipeline.first([])
    assert result == []
