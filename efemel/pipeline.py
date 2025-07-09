"""
Pipeline module for functional data processing with chunked processing.

This module provides a Pipeline class that enables functional programming patterns
for data transformation and processing, using internal chunking for performance.
"""

from collections.abc import Callable, Generator, Iterable
from typing import Any, Self, TypeVar

T = TypeVar("T")  # Type variable for the elements in the pipeline
U = TypeVar("U")  # Type variable for transformed elements
V = TypeVar("V")  # Type variable for additional transformations


class Pipeline[T]:
  """
  A functional pipeline for data processing with internal chunked processing.

  The Pipeline class wraps an iterable and provides a fluent interface for
  applying transformations, filters, and reductions. Internally, it processes
  data in chunks for improved performance.

  Type Parameters:
      T: The type of elements in the pipeline

  Attributes:
      generator: Generator yielding chunks (lists) of elements
  """

  generator: Generator[list[T], None, None]

  def __init__(self, source: Iterable[T], chunk_size: int = 1000) -> "Pipeline[T]":
    """
    Initialize a new Pipeline with the given data source.

    Args:
        source: An iterable that provides the data for the pipeline.
               If source is another Pipeline, it will be efficiently composed.
        chunk_size: Number of elements per chunk (default: 1000)
    """
    if isinstance(source, Pipeline):
      # If source is another Pipeline, use its generator directly to avoid double-chunking
      self.generator = source.generator
    else:
      self.generator = self._chunked(source, chunk_size)

  @staticmethod
  def _chunked(iterable: Iterable[T], size: int) -> Generator[list[T], None, None]:
    """Break an iterable into chunks of specified size."""
    chunk = []
    for item in iterable:
      chunk.append(item)
      if len(chunk) == size:
        yield chunk
        chunk = []
    if chunk:
      yield chunk

  @classmethod
  def _from_chunks(cls, chunks: Iterable[list[T]]) -> "Pipeline[T]":
    """Create a pipeline directly from an iterable of chunks."""
    p = cls([])
    p.generator = (chunk for chunk in chunks)
    return p

  @classmethod
  def from_pipeline(cls, pipeline: "Pipeline[T]") -> "Pipeline[T]":
    """
    Create a new Pipeline from another Pipeline.

    This method provides an explicit way to create a new Pipeline from an existing one,
    preserving the chunked structure for optimal performance.

    Args:
        pipeline: The source Pipeline to copy from

    Returns:
        A new Pipeline that will process the same data as the source
    """
    new_pipeline = cls([])
    new_pipeline.generator = pipeline.generator
    return new_pipeline

  def __iter__(self) -> Generator[T, None, None]:
    """Iterate over elements by flattening chunks."""
    for chunk in self.generator:
      yield from chunk

  def to_list(self) -> list[T]:
    """Convert the pipeline to a list by concatenating all chunks."""
    result = []
    for chunk in self.generator:
      result.extend(chunk)
    return result

  def first(self) -> T:
    """Get the first element from the pipeline."""
    for chunk in self.generator:
      if chunk:
        return chunk[0]
    raise StopIteration("Pipeline is empty")

  def filter(self, predicate: Callable[[T], bool]) -> "Pipeline[T]":
    """Filter elements using a predicate, applied per chunk."""

    def filter_chunk(chunk: list[T]) -> list[T]:
      return [x for x in chunk if predicate(x)]

    return Pipeline._from_chunks(filter_chunk(chunk) for chunk in self.generator)

  def map(self, function: Callable[[T], U]) -> "Pipeline[U]":
    """Transform elements using a function, applied per chunk."""

    def map_chunk(chunk: list[T]) -> list[U]:
      return [function(x) for x in chunk]

    return Pipeline._from_chunks(map_chunk(chunk) for chunk in self.generator)

  def reduce(self, function: Callable[[U, T], U], initial: U) -> "Pipeline[U]":
    """Reduce elements to a single value using the given function."""
    acc = initial
    for chunk in self.generator:
      for item in chunk:
        acc = function(acc, item)
    return Pipeline([acc])

  def tap(self, function: Callable[[T], Any]) -> Self:
    """Apply side effect to each element without modifying data."""

    def tap_chunk(chunk: list[T]) -> list[T]:
      for item in chunk:
        function(item)
      return chunk

    return Pipeline._from_chunks(tap_chunk(chunk) for chunk in self.generator)

  def each(self, function: Callable[[T], Any]) -> None:
    """Apply function to each element (terminal operation)."""
    for chunk in self.generator:
      for item in chunk:
        function(item)

  def passthrough(self) -> Self:
    """Return the pipeline unchanged (identity operation)."""
    return self

  def apply(self, *functions: Callable[[Self], "Pipeline[U]"]) -> "Pipeline[U]":
    """Apply sequence of transformation functions."""
    result: Pipeline[T] = self
    for function in functions:
      result = function(result)
    return result

  def flatten(self: "Pipeline[Iterable[U]]") -> "Pipeline[U]":
    """Flatten pipeline of iterables into single pipeline."""

    def flatten_chunk(chunk: list[Iterable[U]]) -> list[U]:
      return [item for iterable in chunk for item in iterable]

    return Pipeline._from_chunks(flatten_chunk(chunk) for chunk in self.generator)

  @classmethod
  def chain(cls, *pipelines: "Pipeline[T]") -> "Pipeline[T]":
    """
    Chain multiple pipelines together sequentially.

    Args:
        *pipelines: Variable number of Pipeline instances to chain

    Returns:
        A new Pipeline that processes all input pipelines in sequence
    """

    def chain_generator():
      for pipeline in pipelines:
        yield from pipeline.generator

    return cls._from_chunks(chain_generator())
