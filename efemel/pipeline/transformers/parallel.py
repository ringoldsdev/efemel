"""Parallel transformer implementation using multiple threads."""

from collections import deque
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import copy
import itertools

from .transformer import DEFAULT_CHUNK_SIZE
from .transformer import PipelineContext
from .transformer import Transformer


class ParallelTransformer[In, Out](Transformer[In, Out]):
  """
  A transformer that executes operations concurrently using multiple threads.

  This transformer overrides the __call__ method to process data chunks
  in parallel, yielding results as they become available.
  """

  def __init__(
    self,
    max_workers: int = 4,
    ordered: bool = True,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    context: PipelineContext | None = None,
    transformer: Callable[[list[In]], list[Out]] = lambda chunk: chunk,  # type: ignore
  ):
    """
    Initialize the parallel transformer.

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
    self.transformer = transformer

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

  @classmethod
  def from_transformer[T, U](
    cls,
    transformer: Transformer[T, U],
    max_workers: int = 4,
    ordered: bool = True,
    chunk_size: int | None = None,
    context: PipelineContext | None = None,
    **kwargs,
  ) -> "ParallelTransformer[T, U]":
    """
    Create a ParallelTransformer from an existing Transformer.

    This method uses the base class implementation but ensures the result
    is properly typed as a ParallelTransformer.

    Args:
        transformer: The base transformer to copy from.
        max_workers: Maximum number of worker threads.
        ordered: Whether to maintain order of results.
        **kwargs: Additional arguments passed to the constructor.

    Returns:
        A new ParallelTransformer with the same transformation logic.
    """
    # Pass the ParallelTransformer-specific parameters via kwargs

    return cls(
      chunk_size=chunk_size or transformer.chunk_size,
      context=context or copy.deepcopy(transformer.context),
      transformer=copy.deepcopy(transformer.transformer),  # type: ignore
      max_workers=max_workers,
      ordered=ordered,
    )  # type: ignore
