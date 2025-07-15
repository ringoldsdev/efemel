"""Parallel transformer implementation using multiple threads."""

from collections import deque
from collections.abc import Iterable
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import copy
from functools import partial
import itertools
import threading
from typing import TypedDict

from .transformer import DEFAULT_CHUNK_SIZE
from .transformer import InternalTransformer
from .transformer import PipelineContext
from .transformer import Transformer


# --- Type Definitions ---
class ParallelPipelineContextType(TypedDict):
  """A specific context type for parallel transformers that includes a lock."""

  lock: threading.Lock


# --- Class Definition ---
class ParallelTransformer[In, Out](Transformer[In, Out]):
  """
  A transformer that executes operations concurrently using multiple threads.
  """

  def __init__(
    self,
    max_workers: int = 4,
    ordered: bool = True,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    transformer: InternalTransformer[In, Out] | None = None,
  ):
    """
    Initialize the parallel transformer.

    Args:
        max_workers: Maximum number of worker threads.
        ordered: If True, results are yielded in order. If False, results
                 are yielded as they complete.
        chunk_size: Size of data chunks to process.
        transformer: The transformation logic chain.
    """
    super().__init__(chunk_size, transformer)
    self.max_workers = max_workers
    self.ordered = ordered

  @classmethod
  def from_transformer[T, U](
    cls,
    transformer: Transformer[T, U],
    chunk_size: int | None = None,
    max_workers: int = 4,
    ordered: bool = True,
  ) -> "ParallelTransformer[T, U]":
    """
    Create a ParallelTransformer from an existing Transformer's logic.

    Args:
        transformer: The base transformer to copy the transformation logic from.
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

  def __call__(self, data: Iterable[In], context: PipelineContext | None = None) -> Iterator[Out]:
    """
    Executes the transformer on data concurrently.

    A new `threading.Lock` is created and added to the context for each call
    to ensure execution runs are isolated and thread-safe.
    """
    # Determine the context for this run, passing it by reference as requested.
    run_context = context or self.context
    # Add a per-call lock for thread safety.
    run_context["lock"] = threading.Lock()

    def process_chunk(chunk: list[In], shared_context: PipelineContext) -> list[Out]:
      """
      Process a single chunk by passing the chunk and context explicitly
      to the transformer chain. This is safer and avoids mutating self.
      """
      return self.transformer(chunk, shared_context)

    # Create a partial function with the run_context "baked in".
    process_chunk_with_context = partial(process_chunk, shared_context=run_context)

    def _ordered_generator(chunks_iter: Iterator[list[In]], executor: ThreadPoolExecutor) -> Iterator[list[Out]]:
      """Generate results in their original order."""
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
      """Generate results as they complete."""
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
      """Manage the thread pool and yield flattened results."""
      with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        chunks_to_process = self._chunk_generator(data)
        gen_func = _ordered_generator if self.ordered else _unordered_generator
        processed_chunks_iterator = gen_func(chunks_to_process, executor)
        for result_chunk in processed_chunks_iterator:
          yield from result_chunk

    return result_iterator_manager()
