"""
Test basic Pipeline functionality.

This module contains tests for basic Pipeline class functionality
including initialization, iteration, and core methods.
"""

import pytest

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
