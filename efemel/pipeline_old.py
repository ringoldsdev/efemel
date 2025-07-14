from collections import deque
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import wait
from functools import reduce
import inspect
import itertools
from typing import Any
from typing import Union
from typing import overload

# Type aliases for pipeline functions
type PipelineFunction[Out, T] = Callable[[Out], T] | Callable[[Out, PipelineContext], T]
type PipelineReduceFunction[U, Out] = Callable[[U, Out], U] | Callable[[U, Out, PipelineContext], U]


class PipelineContext(dict):
  """Global context available to all pipeline operations."""

  pass


class Pipeline[In, Out]:
  """
  A functional pipeline for data processing with internal chunked processing.

  The Pipeline class provides a fluent interface for applying transformations
  and filters. It processes data in chunks for performance and maintains a
  global context for shared state. The pipeline is callable and iterable.
  """

  def __init__(
    self,
    chunk_size: int = 1000,
    transformer: Callable[[list[In]], list[Out]] | None = None,
    context: PipelineContext | None = None,
  ) -> None:
    self.chunk_size = chunk_size
    self.context = context or PipelineContext()
    self.transformer: Callable[[list[In]], list[Out]] = transformer or (lambda chunk: chunk)

  @classmethod
  def init[T](cls, _type_hint: type[T], chunk_size: int = 1000) -> "Pipeline[T, T]":
    """Create a new identity pipeline with explicit type hint."""
    return cls(chunk_size)

  def __call__(self, *data: Iterable[In]) -> Iterator[Out]:
    """Execute the pipeline on data source (makes pipeline callable)."""
    assert data, "Data source must be provided to execute the pipeline"

    for selected_data in data:
      for chunk in self._chunk_generator(selected_data):
        yield from self.transformer(chunk)

  def pipe[U](self, operation: Callable[[list[Out]], list[U]]) -> "Pipeline[In, U]":
    """
    Composes the current transformer with a new chunk-wise operation.
    The operation should be a function that takes a list and returns a list.
    """
    prev_transformer = self.transformer
    self.transformer = lambda chunk: operation(prev_transformer(chunk))
    return self

  def _create_context_aware_function(self, func: Callable):
    """Create function that properly handles context parameter"""
    try:
      sig = inspect.signature(func)
      params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
      param_count = len(params)

      if param_count >= 2:
        return lambda value: func(value, self.context)
      return func
    except (ValueError, TypeError):
      return func

  def _create_reduce_function(self, func: Callable):
    """Create function that properly handles context parameter for reduce operations"""
    try:
      sig = inspect.signature(func)
      params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
      param_count = len(params)

      if param_count >= 3:
        return lambda acc, value: func(acc, value, self.context)
      return func
    except (ValueError, TypeError):
      return func

  def map[U](self, function: PipelineFunction[Out, U]) -> "Pipeline[In, U]":
    """Transform elements in the pipeline."""
    std_function = self._create_context_aware_function(function)
    return self.pipe(lambda chunk: [std_function(x) for x in chunk])

  def filter(self, predicate: PipelineFunction[Out, bool]) -> "Pipeline[In, Out]":
    """Filter elements in the pipeline."""
    std_predicate = self._create_context_aware_function(predicate)
    return self.pipe(lambda chunk: [x for x in chunk if std_predicate(x)])

  def _chunk_generator(self, data: Iterable[In]) -> Iterator[list[In]]:
    """Generate chunks from the data source"""
    data_iter = iter(data)
    while chunk := list(itertools.islice(data_iter, self.chunk_size)):
      yield chunk

  def to_list(self, *data: Iterable[In]) -> list[Out]:
    """Execute pipeline and return results as list."""
    return [item for d in data for chunk in self._chunk_generator(d) for item in self.transformer(chunk)]

  def each(self, *data: Iterable[In], function: PipelineFunction[Out, Any]) -> None:
    """Apply function to each element (terminal operation)."""
    std_function = self._create_context_aware_function(function)

    for chunk in self._chunk_generator(itertools.chain.from_iterable(data)):
      [std_function(item) for item in self.transformer(chunk)]

  def tap(self, function: PipelineFunction[Out, Any]) -> "Pipeline[In, Out]":
    """Apply side-effect without modifying data."""
    std_function = self._create_context_aware_function(function)

    def tap_operation(chunk: list[Out]) -> list[Out]:
      for item in chunk:
        std_function(item)
      return chunk

    return self.pipe(tap_operation)

  def consume(self, *data: Iterable[In]) -> None:
    """Consume the pipeline without returning results (terminal operation)."""
    for _ in self(*data):
      pass

  @overload
  def flatten(self: "Pipeline[list[In]]") -> "Pipeline[In]": ...

  @overload
  def flatten(self: "Pipeline[tuple[In, ...]]") -> "Pipeline[In]": ...

  @overload
  def flatten(self: "Pipeline[set[In]]") -> "Pipeline[In]": ...

  def flatten(
    self: Union["Pipeline[list[In], In]", "Pipeline[tuple[In, ...]]", "Pipeline[set[In]]"],
  ) -> "Pipeline[In, In]":
    """Flatten nested lists into a single list."""
    return self.pipe(lambda chunk: [item for sublist in chunk for item in sublist])

  def apply[T](self, pipeline: "Pipeline[Out, T]") -> "Pipeline[In, T]":
    """Apply another pipeline to the current one."""
    return self.pipe(lambda chunk: pipeline.transformer(chunk))

  def first(self, *data: Iterable[In], n: int = 1) -> list[Out]:
    """Get the first n elements of the pipeline (terminal operation)."""
    assert n >= 1, "n must be at least 1"
    data_iter = itertools.chain.from_iterable(data)
    result = []
    remaining = n

    while remaining > 0:
      selected_item_count = min(self.chunk_size, remaining)

      # Read a chunk of size min(chunk_size, remaining)
      chunk = list(itertools.islice(data_iter, selected_item_count))

      if not chunk:
        break  # No more data

      result.extend(self.transformer(chunk))

      remaining -= selected_item_count

    return result

  def reduce[U](self, *data: Iterable[In], function: PipelineReduceFunction[U, Out], initial: U) -> U:
    """
    Reduce elements to a single value (terminal operation).

    Args:
        function: Reduce function (acc, value) -> new_acc
        initial: Initial accumulator value
    """
    reducer = self._create_reduce_function(function)
    return reduce(reducer, self(*data), initial)

  def concurrent[T](
    self,
    *data: Iterable[In],
    pipeline: "Pipeline[Out,T]",
    max_workers: int,
    ordered: bool = True,
  ) -> Iterator[T]:
    """
    Applies a sub-pipeline to each chunk in parallel (Terminal Operation).

    This method consumes the pipeline and processes chunks of data concurrently,
    returning an iterator for the results. It is a terminal operation.

    To manage memory effectively, it uses a just-in-time approach, only
    pulling chunks from the source iterator when a worker thread is available.

    Args:
        *data: The input data iterable(s) to process.
        pipeline: A `Pipeline` instance to apply to each chunk. A deep
                  copy is used for each thread to ensure context isolation.
        max_workers: The maximum number of worker threads.
        ordered: If True, results are yielded in the original order.
                  If False, results are yielded as they complete.

    Returns:
        An iterator that yields the processed items.
    """

    def process_chunk(chunk: list[Out]) -> list[T]:
      return pipeline.to_list(chunk)

    def _ordered_generator(chunks_iter: Iterator[list[Out]], executor: ProcessPoolExecutor) -> Iterator[list[T]]:
      futures = deque()
      for _ in range(max_workers + 1):
        try:
          chunk = next(chunks_iter)
          futures.append(executor.submit(process_chunk, chunk))
        except StopIteration:
          break

      while futures:
        yield futures.popleft().result()
        try:
          chunk = next(chunks_iter)
          futures.append(executor.submit(process_chunk, chunk))
        except StopIteration:
          continue

    def _unordered_generator(chunks_iter: Iterator[list[Out]], executor: ProcessPoolExecutor) -> Iterator[list[T]]:
      futures = {executor.submit(process_chunk, chunk) for chunk in itertools.islice(chunks_iter, max_workers + 1)}

      while futures:
        done, futures = wait(futures, return_when=FIRST_COMPLETED)
        for future in done:
          yield future.result()
          try:
            chunk = next(chunks_iter)
            futures.add(executor.submit(process_chunk, chunk))
          except StopIteration:
            continue

    # This wrapper generator ensures the ProcessPoolExecutor is properly
    # managed and closed only after the result iterator is exhausted.
    def result_iterator_manager() -> Iterator[T]:
      with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Create the stream of chunks to be processed concurrently.
        chunks_to_process = (self.transformer(chunk) for d in data for chunk in self._chunk_generator(d))

        gen_func = _ordered_generator if ordered else _unordered_generator
        processed_chunks_iterator = gen_func(chunks_to_process, executor)

        # Flatten the iterator of chunks into an iterator of items.
        for result_chunk in processed_chunks_iterator:
          yield from result_chunk

    return result_iterator_manager()
