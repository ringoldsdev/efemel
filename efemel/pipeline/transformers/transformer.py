from collections import deque
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import copy
from functools import reduce
import inspect
import itertools
from typing import Any
from typing import Self
from typing import Union
from typing import overload

# --- Type Aliases ---
type PipelineFunction[Out, T] = Callable[[Out], T] | Callable[[Out, PipelineContext], T]
type PipelineReduceFunction[U, Out] = Callable[[U, Out], U] | Callable[[U, Out, PipelineContext], U]


class PipelineContext(dict):
  """Global context available to all pipeline operations."""

  pass


class Transformer[In, Out]:
  """
  Defines and composes data transformations (e.g., map, filter).

  Transformers are callable and return a generator, applying the composed
  transformation logic to an iterable data source.
  """

  def __init__(
    self,
    chunk_size: int = 1000,
    context: PipelineContext | None = None,
  ):
    self.chunk_size = chunk_size
    self.context = context or PipelineContext()
    self.transformer = lambda chunk: chunk

  @classmethod
  def init[T](cls, _type_hint: type[T], chunk_size: int = 1000) -> "Transformer[T, T]":
    """Create a new identity pipeline with explicit type hint."""
    return cls(chunk_size)  # type: ignore

  def _chunk_generator(self, data: Iterable[In]) -> Iterator[list[In]]:
    """Breaks an iterable into chunks of a specified size."""
    data_iter = iter(data)
    while chunk := list(itertools.islice(data_iter, self.chunk_size)):
      yield chunk

  def _pipe[U](self, operation: Callable[[list[Out]], list[U]]) -> "Transformer[In, U]":
    """Composes the current transformer with a new chunk-wise operation."""
    prev_transformer = self.transformer
    self.transformer = lambda chunk: operation(prev_transformer(chunk))
    return self  # type: ignore

  def _create_context_aware_function(self, func: Callable) -> Callable:
    """Creates a function that correctly handles the context parameter."""
    try:
      sig = inspect.signature(func)
      params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
      if len(params) >= 2:
        return lambda value: func(value, self.context)
    except (ValueError, TypeError):
      pass
    return func

  def _create_reduce_function(self, func: Callable) -> Callable:
    """Creates a reduce function that correctly handles the context parameter."""
    try:
      sig = inspect.signature(func)
      params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
      if len(params) >= 3:
        return lambda acc, value: func(acc, value, self.context)
    except (ValueError, TypeError):
      pass
    return func

  def map[U](self, function: PipelineFunction[Out, U]) -> "Transformer[In, U]":
    """Transforms elements in the pipeline."""
    std_function = self._create_context_aware_function(function)
    return self._pipe(lambda chunk: [std_function(x) for x in chunk])

  def filter(self, predicate: PipelineFunction[Out, bool]) -> "Transformer[In, Out]":
    """Filters elements in the pipeline."""
    std_predicate = self._create_context_aware_function(predicate)
    return self._pipe(lambda chunk: [x for x in chunk if std_predicate(x)])

  @overload
  def flatten[T](self: "Transformer[In, list[T]]") -> "Transformer[In, T]": ...

  @overload
  def flatten[T](self: "Transformer[In, tuple[T, ...]]") -> "Transformer[In, T]": ...

  @overload
  def flatten[T](self: "Transformer[In, set[T]]") -> "Transformer[In, T]": ...

  def flatten[T](
    self: Union["Transformer[In, list[T]]", "Transformer[In, tuple[T, ...]]", "Transformer[In, set[T]]"],
  ) -> "Transformer[In, T]":
    """Flatten nested lists into a single list."""
    return self._pipe(lambda chunk: [item for sublist in chunk for item in sublist])  # type: ignore

  def tap(self, function: PipelineFunction[Out, Any]) -> "Transformer[In, Out]":
    """Applies a side-effect function without modifying the data."""
    std_function = self._create_context_aware_function(function)

    def tap_operation(chunk: list[Out]) -> list[Out]:
      for item in chunk:
        std_function(item)
      return chunk

    return self._pipe(tap_operation)

  def apply[T](self, t: Callable[[Self], "Transformer[In, T]"]) -> "Transformer[In, T]":
    """Apply another pipeline to the current one."""
    return t(self)

  # Terminal operations
  # These operations execute the transformer on a data source and yield results.
  # If you want to operate on the results, you need to use a Pipeline and apply
  # a different transformer to it.

  def __call__(self, data: Iterable[In]) -> Iterator[Out]:
    """
    Executes the transformer on a data source (terminal operations).
    """
    for chunk in self._chunk_generator(data):
      yield from self.transformer(chunk)

  def reduce[U](self, function: PipelineReduceFunction[Out, U], initial: U):
    """Reduces elements to a single value (terminal operation)."""
    reducer = self._create_reduce_function(function)

    def _reduce(data: Iterable[In]) -> Iterator[U]:
      yield reduce(reducer, self(data), initial)

    return _reduce


class ConcurrentTransformer[In, Out](Transformer[In, Out]):
  """
  A transformer that executes operations concurrently using multiple threads.

  This transformer overrides the __call__ method to process data chunks
  in parallel, yielding results as they become available.
  """

  def __init__(
    self,
    max_workers: int = 4,
    ordered: bool = True,
    chunk_size: int = 1000,
    context: PipelineContext | None = None,
  ):
    """
    Initialize the concurrent transformer.

    Args:
        max_workers: Maximum number of worker threads.
        ordered: If True, results are yielded in order. If False, results
                are yielded as they complete.
        chunk_size: Size of data chunks to process.
        context: Pipeline context for operations.
    """
    super().__init__(chunk_size, context)
    self.max_workers = max_workers
    self.ordered = ordered

  @classmethod
  def from_transformer[T, U](
    cls, transformer: Transformer[T, U], max_workers: int = 4, ordered: bool = True
  ) -> "ConcurrentTransformer[T, U]":
    """
    Create a ConcurrentTransformer from an existing Transformer.

    Args:
        transformer: The base transformer to make concurrent.
        max_workers: Maximum number of worker threads.
        ordered: Whether to maintain order of results.

    Returns:
        A new ConcurrentTransformer with the same transformation logic.
    """
    concurrent = cls(max_workers, ordered, transformer.chunk_size, copy.deepcopy(transformer.context))
    concurrent.transformer = copy.deepcopy(transformer.transformer)
    return concurrent  # type: ignore

  def __call__(self, data: Iterable[In]) -> Iterator[Out]:
    """
    Executes the transformer on data concurrently, yielding results as processed.

    Args:
        data: Input data to process.

    Returns:
        Iterator yielding processed results.
    """

    def process_chunk(chunk: list[In]) -> list[Out]:
      """Process a single chunk using the transformer."""
      return self.transformer(chunk)

    def _ordered_generator(chunks_iter: Iterator[list[In]], executor: ThreadPoolExecutor) -> Iterator[list[Out]]:
      """Generate results in original order."""
      from concurrent.futures import Future

      futures: deque[Future[list[Out]]] = deque()

      # Submit initial batch of work
      for _ in range(self.max_workers + 1):
        try:
          chunk = next(chunks_iter)
          futures.append(executor.submit(process_chunk, chunk))
        except StopIteration:
          break

      # Process remaining chunks, maintaining order
      while futures:
        yield futures.popleft().result()
        try:
          chunk = next(chunks_iter)
          futures.append(executor.submit(process_chunk, chunk))
        except StopIteration:
          continue

    def _unordered_generator(chunks_iter: Iterator[list[In]], executor: ThreadPoolExecutor) -> Iterator[list[Out]]:
      """Generate results as they complete (unordered)."""
      # Submit initial batch of work
      futures = {executor.submit(process_chunk, chunk) for chunk in itertools.islice(chunks_iter, self.max_workers + 1)}

      while futures:
        done, futures = wait(futures, return_when=FIRST_COMPLETED)
        for future in done:
          yield future.result()
          try:
            chunk = next(chunks_iter)
            futures.add(executor.submit(process_chunk, chunk))
          except StopIteration:
            continue

    def result_iterator_manager() -> Iterator[Out]:
      """Manage the thread pool and flatten results."""
      with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        chunks_to_process = self._chunk_generator(data)

        gen_func = _ordered_generator if self.ordered else _unordered_generator
        processed_chunks_iterator = gen_func(chunks_to_process, executor)

        # Flatten the iterator of chunks into an iterator of items
        for result_chunk in processed_chunks_iterator:
          yield from result_chunk

    return result_iterator_manager()
