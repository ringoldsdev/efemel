"""
Pipeline module for functional data processing with chunked processing.

This module provides a Pipeline class that enables functional programming patterns
for data transformation and processing, using internal chunking and optional
concurrent execution for performance.
"""

from collections import deque
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterable
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from itertools import chain
from typing import Any
from typing import Self
from typing import TypeVar
from typing import overload

T = TypeVar("T")  # Type variable for the elements in the pipeline
U = TypeVar("U")  # Type variable for transformed elements


class Pipeline[T]:
  """
  A functional pipeline for data processing with internal chunked processing.

  The Pipeline class wraps an iterable and provides a fluent interface for
  applying transformations, filters, and reductions. Internally, it processes
  data in chunks for improved performance and supports concurrent execution.

  Type Parameters:
      T: The type of elements in the pipeline

  Attributes:
      generator: Generator yielding chunks (lists) of elements
  """

  generator: Generator[list[T], None, None]

  def __init__(self, source: Iterable[T], chunk_size: int = 1000) -> None:
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

    self.chunk_size = chunk_size

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
  def _from_chunks(cls, chunks: Iterable[list[T]], chunk_size: int = 1000) -> "Pipeline[T]":
    """Create a pipeline directly from an iterable of chunks."""
    p = cls([])
    p.generator = (chunk for chunk in chunks)
    p.chunk_size = chunk_size
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

    return Pipeline._from_chunks((filter_chunk(chunk) for chunk in self.generator), self.chunk_size)

  def map(self, function: Callable[[T], U]) -> "Pipeline[U]":
    """Transform elements using a function, applied per chunk."""

    def map_chunk(chunk: list[T]) -> list[U]:
      return [function(x) for x in chunk]

    return Pipeline._from_chunks((map_chunk(chunk) for chunk in self.generator), self.chunk_size)

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

    return Pipeline._from_chunks((tap_chunk(chunk) for chunk in self.generator), self.chunk_size)

  def each(self, function: Callable[[T], Any]) -> None:
    """Apply function to each element (terminal operation)."""
    for chunk in self.generator:
      for item in chunk:
        function(item)

  def noop(self) -> None:
    """Consume the pipeline without any operation."""
    # Consume all elements in the pipeline without any operation
    for _ in chain.from_iterable(self.generator):
      continue

  def passthrough(self) -> Self:
    """Return the pipeline unchanged (identity operation)."""
    return self

  def apply(self, *functions: Callable[[Self], "Pipeline[U]"]) -> "Pipeline[U]":
    """Apply sequence of transformation functions."""
    result: Pipeline[Any] = self
    for function in functions:
      result = function(result)
    return result

  @overload
  def flatten(self: "Pipeline[list[U]]") -> "Pipeline[U]": ...

  @overload
  def flatten(self: "Pipeline[tuple[U, ...]]") -> "Pipeline[U]": ...

  @overload
  def flatten(self: "Pipeline[set[U]]") -> "Pipeline[U]": ...

  def flatten(
    self: "Pipeline[list[U]] | Pipeline[tuple[U, ...]] | Pipeline[set[U]]",
  ) -> "Pipeline[Any]":
    """Flatten iterable chunks into a single pipeline of elements.

    This method flattens each chunk of iterables and maintains the chunked
    structure to avoid memory issues with large datasets. After flattening,
    the data is re-chunked to maintain the original chunk_size.

    Example:
        [[1, 2], [3, 4]] -> [1, 2, 3, 4]
        [(1, 2), (3, 4)] -> [1, 2, 3, 4]

    Note:
        We need to overload this method to handle different iterable types because
        using Iterable[U] does not preserve the type information for the flattened elements.
        It returns Pipeline[Any] instead of Pipeline[U], which is incorrect.
    """

    def flatten_generator() -> Generator[Any, None, None]:
      """Generator that yields individual flattened items."""
      for chunk in self.generator:
        for iterable in chunk:
          yield from iterable

    # Re-chunk the flattened stream to maintain consistent chunk size
    return Pipeline._from_chunks(self._chunked(flatten_generator(), self.chunk_size), self.chunk_size)

  def concurrent(
    self,
    pipeline_func: Callable[["Pipeline[T]"], "Pipeline[U]"],
    max_workers: int,
    ordered: bool = True,
  ) -> "Pipeline[U]":
    """
    Applies a pipeline function to each chunk in parallel.

    This method processes chunks concurrently using a thread pool, which can
    significantly speed up I/O-bound or GIL-releasing tasks. The provided
    function is applied to a new mini-pipeline created from each chunk.

    Args:
        pipeline_func: A function that takes a `Pipeline` and returns a
                       transformed `Pipeline`.
        max_workers: The maximum number of threads to use.
        ordered: If True (default), the output chunks will be in the same
                 order as the input. Setting to False can improve performance
                 by yielding results as they complete.

    Returns:
        A new Pipeline containing the elements from the concurrently
        processed chunks.
    """

    def apply_to_chunk(chunk: list[T]) -> list[U]:
      # Create a mini-pipeline for the chunk that treats it as a single unit
      chunk_pipeline = Pipeline(chunk, chunk_size=len(chunk))
      # Apply the user's pipeline function and collect the results
      processed_pipeline = pipeline_func(chunk_pipeline)
      return processed_pipeline.to_list()

    def ordered_generator() -> Generator[list[U], None, None]:
      """Yields results in the order they were submitted."""
      with ThreadPoolExecutor(max_workers=max_workers) as executor:
        source_iterator = iter(self.generator)
        futures = deque()

        # Prime the executor with the initial set of tasks
        for _ in range(max_workers):
          try:
            chunk = next(source_iterator)
            futures.append(executor.submit(apply_to_chunk, chunk))
          except StopIteration:
            break  # No more chunks in the source

        # As tasks complete, yield results and submit new tasks
        while futures:
          completed_future = futures.popleft()
          yield completed_future.result()

          try:
            chunk = next(source_iterator)
            futures.append(executor.submit(apply_to_chunk, chunk))
          except StopIteration:
            continue  # All chunks have been submitted

    def unordered_generator() -> Generator[list[U], None, None]:
      """Yields results as soon as they complete."""
      with ThreadPoolExecutor(max_workers=max_workers) as executor:
        source_iterator = iter(self.generator)
        futures = set()

        # Prime the executor with the initial set of tasks
        for _ in range(max_workers):
          try:
            chunk = next(source_iterator)
            futures.add(executor.submit(apply_to_chunk, chunk))
          except StopIteration:
            break

        while futures:
          # Wait for the first available result
          done, futures = wait(futures, return_when=FIRST_COMPLETED)

          for completed_future in done:
            yield completed_future.result()
            # Refill the pool with a new task
            try:
              chunk = next(source_iterator)
              futures.add(executor.submit(apply_to_chunk, chunk))
            except StopIteration:
              continue

    gen = ordered_generator() if ordered else unordered_generator()
    return Pipeline._from_chunks(gen, self.chunk_size)

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

    # Use chunk_size from the first pipeline, or default if no pipelines
    chunk_size = pipelines[0].chunk_size if pipelines else 1000
    return cls._from_chunks(chain_generator(), chunk_size)
