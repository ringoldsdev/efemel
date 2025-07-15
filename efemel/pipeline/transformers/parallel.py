"""Parallel transformer implementation using multiple threads."""

from collections import deque
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import copy
from functools import partial
import itertools
import threading
from typing import TypedDict

from .transformer import DEFAULT_CHUNK_SIZE
from .transformer import PipelineContext
from .transformer import Transformer


class ParallelPipelineContextType(TypedDict):
  """A specific context type for parallel transformers that includes a lock."""

  lock: threading.Lock


class ParallelTransformer[In, Out](Transformer[In, Out]):
  """
  A transformer that executes operations concurrently using multiple threads.
  """

  def __init__(
    self,
    max_workers: int = 4,
    ordered: bool = True,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    transformer: Callable[[list[In]], list[Out]] = lambda chunk: chunk,  # type: ignore
  ):
    """
    Initialize the parallel transformer.

    Args:
        max_workers: Maximum number of worker threads.
        ordered: If True, results are yielded in order. If False, results
                 are yielded as they complete.
        chunk_size: Size of data chunks to process.
    """
    super().__init__(chunk_size)
    self.max_workers = max_workers
    self.ordered = ordered
    self.transformer = transformer
    # The lock is no longer created here. It will be created per-call.

  def __call__(self, data: Iterable[In], context: PipelineContext | None = None) -> Iterator[Out]:
    """
    Executes the transformer on data concurrently, yielding results as processed.

    A new `threading.Lock` is created for each call to ensure execution runs
    are isolated from each other.

    Args:
        data: Input data to process.
        context: A PipelineContext to be shared across all worker threads.
            If provided, it will be merged with this transformer's context.
    """
    # Create a context scoped to this specific call to ensure thread safety
    # and prevent state leakage between different runs.
    if context:
      self.context = context

    self.context["lock"] = threading.Lock()

    # A new lock is created for every call, ensuring each run is isolated.

    def process_chunk(chunk: list[In], shared_context: PipelineContext) -> list[Out]:
      """Process a single chunk using the transformer."""
      self.context = shared_context
      return self.transformer(chunk)

    # Use functools.partial to pass the call-specific context to every thread.
    process_chunk_with_context = partial(process_chunk, shared_context=self.context)

    def _ordered_generator(chunks_iter: Iterator[list[In]], executor: ThreadPoolExecutor) -> Iterator[list[Out]]:
      """Generate results in original order."""
      from concurrent.futures import Future

      futures: deque[Future[list[Out]]] = deque()

      for _ in range(self.max_workers + 1):
        try:
          chunk = next(chunks_iter)
          futures.append(executor.submit(process_chunk_with_context, chunk))
        except StopIteration:
          break

      while futures:
        yield futures.popleft().result()
        try:
          chunk = next(chunks_iter)
          futures.append(executor.submit(process_chunk_with_context, chunk))
        except StopIteration:
          continue

    def _unordered_generator(chunks_iter: Iterator[list[In]], executor: ThreadPoolExecutor) -> Iterator[list[Out]]:
      """Generate results as they complete (unordered)."""
      futures = {
        executor.submit(process_chunk_with_context, chunk)
        for chunk in itertools.islice(chunks_iter, self.max_workers + 1)
      }

      while futures:
        done, futures = wait(futures, return_when=FIRST_COMPLETED)
        for future in done:
          yield future.result()
          try:
            chunk = next(chunks_iter)
            futures.add(executor.submit(process_chunk_with_context, chunk))
          except StopIteration:
            continue

    def result_iterator_manager() -> Iterator[Out]:
      """Manage the thread pool and flatten results."""
      with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        chunks_to_process = self._chunk_generator(data)

        gen_func = _ordered_generator if self.ordered else _unordered_generator
        processed_chunks_iterator = gen_func(chunks_to_process, executor)

        for result_chunk in processed_chunks_iterator:
          yield from result_chunk

    return result_iterator_manager()

  @classmethod
  def from_transformer[T, U](
    cls,
    transformer: Transformer[T, U],
    chunk_size: int | None = None,
    max_workers: int = 4,
    ordered: bool = True,
  ) -> "ParallelTransformer[T, U]":
    """
    Create a ParallelTransformer from an existing Transformer.

    Args:
        transformer: The base transformer to copy from.
        chunk_size: Optional chunk size override.
        max_workers: Maximum number of worker threads.
        ordered: If True, results are yielded in order.

    Returns:
        A new ParallelTransformer with the same transformation logic.
    """
    return cls(
      chunk_size=chunk_size or transformer.chunk_size,
      transformer=copy.deepcopy(transformer.transformer),  # type: ignore
      max_workers=max_workers,
      ordered=ordered,
    )
