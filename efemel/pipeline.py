"""
Pipeline module for functional data processing with chunked processing and robust error handling.

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
import inspect
from typing import Any
from typing import NamedTuple
from typing import Self
from typing import TypedDict
from typing import TypeVar
from typing import Union
from typing import overload

# Type variable for the value part of the internal tuple
T = TypeVar("T")
# Type variable for the transformed value part
U = TypeVar("U")


def _get_function_arity(func: Callable) -> int:
  """
  Determine how many parameters a function accepts.
  Returns the number of positional parameters the function expects.
  """
  try:
    sig = inspect.signature(func)
    return len([p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)])
  except (ValueError, TypeError):
    # Fall back to assuming single parameter for lambda or built-in functions
    return 1


class PipelineContext(TypedDict):
  """Global context available to all pipeline operations."""

  has_errors: bool
  errors: list[dict[str, Any]]


# Define a type for the internal data structure: a tuple of (value, error)
class PipelineItem(NamedTuple):
  """Represents an item in the pipeline."""

  value: T
  error: Exception | None
  context: PipelineContext


class CompoundError(Exception):
  """An exception that aggregates multiple underlying errors from a pipeline."""

  def __init__(self, errors: list[Exception]):
    self.errors = errors
    super().__init__(self._format_message())

  def _format_message(self) -> str:
    """Create a summary message for all the contained errors."""
    message = f"{len(self.errors)} error(s) occurred in the pipeline:\n"
    for i, error in enumerate(self.errors, 1):
      message += f"  {i}. {type(error).__name__}: {error}\n"
    return message

  def __repr__(self) -> str:
    return f"CompoundError(errors={self.errors!r})"


class Pipeline[T]:
  """
  A functional pipeline for data processing with internal chunked processing and error handling.

  The Pipeline class wraps an iterable and provides a fluent interface for
  applying transformations and filters. It processes data in chunks for performance,
  captures exceptions without halting execution, and reports all errors at the end.

  Type Parameters:
      T: The type of elements being processed in the pipeline.

  Attributes:
      generator: A generator yielding chunks of pipeline items.
      chunk_size: The number of elements to process in each chunk.
      context: A dictionary for global pipeline state.
  """

  generator: Generator[list[PipelineItem[T]], None, None]
  context: PipelineContext

  def __init__(self, source: Union[Iterable[T], "Pipeline[T]"], chunk_size: int = 1000) -> None:
    """
    Initialize a new Pipeline with the given data source.

    Args:
        source: An iterable or another Pipeline.
        chunk_size: The number of elements per chunk (default: 1000).
    """
    if isinstance(source, Pipeline):
      self.generator = source.generator
      self.chunk_size = source.chunk_size
      self.context = source.context
    else:
      self.context = PipelineContext(has_errors=False, errors=[])
      self.generator = self._chunked_and_wrap(source, chunk_size)
      self.chunk_size = chunk_size

  def _chunked_and_wrap(self, iterable: Iterable[T], size: int) -> Generator[list[PipelineItem[T]], None, None]:
    """Break an iterable into chunks of specified size and wrap items."""
    chunk: list[PipelineItem[T]] = []
    for item in iterable:
      chunk.append(PipelineItem(item, None, self.context))  # Wrap each item
      if len(chunk) == size:
        yield chunk
        chunk = []
    if chunk:
      yield chunk

  @classmethod
  def _from_chunks(
    cls, chunks: Iterable[list[PipelineItem[T]]], chunk_size: int, context: PipelineContext
  ) -> "Pipeline[T]":
    """Create a pipeline directly from an iterable of chunks."""
    p = cls([], chunk_size=chunk_size)
    p.generator = (chunk for chunk in chunks)
    p.context = context
    return p

  def __iter__(self) -> Generator[T, None, None]:
    """
    Iterate over elements, raising a CompoundError at the end if any exceptions were caught.
    """
    errors: list[Exception] = []
    for chunk in self.generator:
      for value, error, _ in chunk:
        if error:
          errors.append(error)
          self.context["has_errors"] = True
        else:
          yield value
    if errors:
      raise CompoundError(errors)

  def to_list(self) -> list[T]:
    """
    Convert the pipeline to a list, raising a CompoundError if any exceptions were caught.
    """
    results: list[T] = []
    errors: list[Exception] = []
    for chunk in self.generator:
      for value, error, _ in chunk:
        if error:
          errors.append(error)
          self.context["has_errors"] = True
        else:
          results.append(value)
    if errors:
      raise CompoundError(errors)
    return results

  def first(self) -> T:
    """
    Get the first element, raising a CompoundError if any exceptions are found anywhere in the pipeline.
    """
    # Note: This is a terminal operation and must consume the generator to find all errors.
    items = self.to_list()
    if not items:
      raise StopIteration("Pipeline is empty")
    return items[0]

  def map[U](self, function: Callable[[T], U] | Callable[[T, PipelineContext], U]) -> "Pipeline[U]":
    """Transform elements, capturing any exceptions that occur."""

    # Check function arity once upfront for efficiency
    func_arity = _get_function_arity(function)
    accepts_context = func_arity >= 2

    def map_generator() -> Generator[list[PipelineItem[U]], None, None]:
      for chunk in self.generator:
        new_chunk: list[PipelineItem[U]] = []
        for value, error, context in chunk:
          if error:
            # Pass through existing errors
            new_chunk.append(PipelineItem(value, error, context))
            self.context["has_errors"] = True
          else:
            try:
              # Apply the function with appropriate signature
              if accepts_context:
                result = function(value, self.context)
              else:
                result = function(value)
              new_chunk.append(PipelineItem(result, None, context))
            except Exception as e:
              # On failure, capture the exception
              new_chunk.append(PipelineItem(value, e, context))
              self.context["has_errors"] = True
        yield new_chunk

    return Pipeline._from_chunks(map_generator(), self.chunk_size, self.context)

  def filter(self, predicate: Callable[[T], bool] | Callable[[T, PipelineContext], bool]) -> "Pipeline[T]":
    """Filter elements, capturing any exceptions from the predicate."""

    # Check function arity once upfront for efficiency
    func_arity = _get_function_arity(predicate)
    accepts_context = func_arity >= 2

    def filter_generator() -> Generator[list[PipelineItem[T]], None, None]:
      for chunk in self.generator:
        new_chunk: list[PipelineItem[T]] = []
        for item in chunk:
          if item.error:
            # Pass through existing errors
            new_chunk.append(item)
            self.context["has_errors"] = True
            continue
          try:
            # Keep item if predicate is true
            if accepts_context:
              result = predicate(item.value, self.context)
            else:
              result = predicate(item.value)
            if result:
              new_chunk.append(item)
          except Exception as e:
            # If predicate fails, capture the error
            new_chunk.append(PipelineItem(item.value, e, item.context))
            self.context["has_errors"] = True
        yield new_chunk

    return Pipeline._from_chunks(filter_generator(), self.chunk_size, self.context)

  def reduce[U](
    self, function: Callable[[U, T], U] | Callable[[U, T, PipelineContext], U], initial: U
  ) -> "Pipeline[U]":
    """
    Reduce elements to a single value (intermediate operation).
    Errored items are skipped in the reduction and passed through.
    """

    def reduce_generator() -> Generator[list[PipelineItem[U]], None, None]:
      acc = initial
      error_items: list[PipelineItem[U]] = []

      # Check function arity once upfront for efficiency
      func_arity = _get_function_arity(function)
      accepts_context = func_arity >= 3  # For reduce: acc, value, context

      for chunk in self.generator:
        for value, error, context in chunk:
          if error:
            error_items.append(PipelineItem(value, error, context))
            self.context["has_errors"] = True
          else:
            try:
              if accepts_context:
                acc = function(acc, value, self.context)
              else:
                acc = function(acc, value)
            except Exception as e:
              # If reduce function fails, we still need to handle it
              error_items.append(PipelineItem(value, e, context))
              self.context["has_errors"] = True
      # Yield all collected errors first, then the final result.
      if error_items:
        yield error_items
      yield [PipelineItem(acc, None, self.context)]

    return Pipeline._from_chunks(reduce_generator(), self.chunk_size, self.context)

  def each(self, function: Callable[[T], Any] | Callable[[T, PipelineContext], Any]) -> None:
    """
    Apply a function to each element (terminal operation).

    Raises a CompoundError at the end if any exceptions were caught.
    """

    # Check function arity once upfront for efficiency
    func_arity = _get_function_arity(function)
    accepts_context = func_arity >= 2

    errors: list[Exception] = []
    for chunk in self.generator:
      for value, error, _ in chunk:
        if error:
          errors.append(error)
          self.context["has_errors"] = True
        else:
          try:
            if accepts_context:
              function(value, self.context)
            else:
              function(value)
          except Exception as e:
            errors.append(e)
            self.context["has_errors"] = True
    if errors:
      raise CompoundError(errors)

  def apply[U](self, function: Callable[[Self], "Pipeline[U]"]) -> "Pipeline[U]":
    """Apply a sequence of transformations to the pipeline."""
    return function(self)

  def catch[U](
    self,
    pipeline_func: Callable[["Pipeline[T]"], "Pipeline[U]"],
    on_error: Callable[[Exception], Any],
  ) -> "Pipeline[U]":
    """
    Apply a pipeline function and handle any captured errors with a callback.

    This method is for inspecting or logging errors mid-stream. It does not
    recover from them; the errors remain in the pipeline.

    Args:
        pipeline_func: A function that takes a pipeline and returns a new one.
        on_error: A function to call with any exception captured in the `pipeline_func`.

    Returns:
        A new pipeline that continues with the (potentially errored) items.
    """
    # Initialize errors list in context if not present
    if "errors" not in self.context:
      self.context["errors"] = []

    processed_pipeline = pipeline_func(self)

    def error_tapping_generator() -> Generator[list[PipelineItem[U]], None, None]:
      for chunk in processed_pipeline.generator:
        for value, error, _ in chunk:
          if error:
            self.context["has_errors"] = True
            self.context["errors"].append({"value": value, "error": error})
            try:
              on_error(error)
            except Exception as e:
              # To prevent the handler itself from stopping the pipeline,
              # we could log this as a meta-error, but for now, we'll print it.
              print(f"Error in `on_error` handler: {e}")
        yield chunk  # Pass the original chunk through

    return Pipeline._from_chunks(error_tapping_generator(), self.chunk_size, self.context)

  @overload
  def flatten(self: "Pipeline[list[U]]") -> "Pipeline[U]": ...

  @overload
  def flatten(self: "Pipeline[tuple[U, ...]]") -> "Pipeline[U]": ...

  @overload
  def flatten(self: "Pipeline[set[U]]") -> "Pipeline[U]": ...

  def flatten(self: Union["Pipeline[list[U]]", "Pipeline[tuple[U, ...]]", "Pipeline[set[U]]"]) -> "Pipeline[Any]":
    """Flatten nested iterables within the pipeline."""

    def flatten_generator() -> Generator[list[PipelineItem[Any]], None, None]:
      current_chunk: list[PipelineItem[Any]] = []
      for chunk in self.generator:
        for value, error, context in chunk:
          if error:
            # Pass through errored items directly
            current_chunk.append(PipelineItem(value, error, context))
            self.context["has_errors"] = True
          elif isinstance(value, list | tuple | set):
            # Flatten the value from a successful item
            for item in value:
              current_chunk.append(PipelineItem(item, None, context))
              if len(current_chunk) == self.chunk_size:
                yield current_chunk
                current_chunk = []
          # Non-iterable, non-errored items are passed through as-is
          else:
            current_chunk.append(PipelineItem(value, None, context))

          if len(current_chunk) == self.chunk_size:
            yield current_chunk
            current_chunk = []

      if current_chunk:
        yield current_chunk

    return Pipeline._from_chunks(flatten_generator(), self.chunk_size, self.context)

  def concurrent(
    self,
    pipeline_func: Callable[["Pipeline[T]"], "Pipeline[U]"],
    max_workers: int,
    ordered: bool = True,
  ) -> "Pipeline[U]":
    """Applies a pipeline function to each chunk in parallel."""

    def apply_to_chunk(chunk: list[PipelineItem[T]]) -> list[PipelineItem[U]]:
      # Create a mini-pipeline from the single chunk of (value, error) tuples.
      # The chunk size is len(chunk) to ensure it's processed as one unit.
      chunk_pipeline = Pipeline._from_chunks([chunk], len(chunk), self.context)
      processed_pipeline = pipeline_func(chunk_pipeline)
      # The result is already a list of chunks of tuples, so we flatten it by one level.
      return [item for processed_chunk in processed_pipeline.generator for item in processed_chunk]

    def process_in_pool(
      gen_func: Callable[[], Generator[list[PipelineItem[U]], None, None]],
    ) -> Generator[list[PipelineItem[U]], None, None]:
      with ThreadPoolExecutor(max_workers=max_workers) as executor:
        yield from gen_func(executor)

    def ordered_generator(
      executor: ThreadPoolExecutor,
    ) -> Generator[list[PipelineItem[U]], None, None]:
      futures = deque(executor.submit(apply_to_chunk, chunk) for chunk in self.generator)
      while futures:
        yield futures.popleft().result()

    def unordered_generator(
      executor: ThreadPoolExecutor,
    ) -> Generator[list[PipelineItem[U]], None, None]:
      futures = {executor.submit(apply_to_chunk, chunk) for chunk in self.generator}
      while futures:
        done, futures = wait(futures, return_when=FIRST_COMPLETED)
        for f in done:
          yield f.result()

    def gen(executor):
      if ordered:
        return ordered_generator(executor)
      else:
        return unordered_generator(executor)

    return Pipeline._from_chunks(process_in_pool(gen), self.chunk_size, self.context)

  # All other methods like tap, noop, etc. can be adapted similarly
  # to handle the (value, error) tuple structure.
  def noop(self) -> None:
    """Consume the pipeline, raising a CompoundError if any exceptions were caught."""
    errors = [error for chunk in self.generator for _, error, _ in chunk if error]
    if errors:
      self.context["has_errors"] = True
      raise CompoundError(errors)

  @classmethod
  def chain(cls, *pipelines: "Pipeline[T]") -> "Pipeline[T]":
    """Chain multiple pipelines together sequentially."""

    def chain_generator():
      for pipeline in pipelines:
        yield from pipeline.generator

    chunk_size = pipelines[0].chunk_size if pipelines else 1000
    context = pipelines[0].context if pipelines else PipelineContext(has_errors=False, errors=[])
    return cls._from_chunks(chain_generator(), chunk_size, context)

  def tap(self, function: Callable[[T], Any] | Callable[[T, PipelineContext], Any]) -> Self:
    """Apply a side-effect function to each element without modifying the data."""

    # Check function arity once upfront for efficiency
    func_arity = _get_function_arity(function)
    accepts_context = func_arity >= 2

    def tap_generator() -> Generator[list[PipelineItem[T]], None, None]:
      for chunk in self.generator:
        for value, error, _ in chunk:
          # Apply tap only to non-errored items
          if not error:
            try:
              if accepts_context:
                function(value, self.context)
              else:
                function(value)
            except Exception as e:
              # If the tap function itself fails, we should not halt the pipeline.
              # For now, we print a warning. A more advanced logger could be used here.
              print(f"Warning: Exception in tap function ignored: {e}")
        yield chunk  # Pass the original chunk through unchanged

    return Pipeline._from_chunks(tap_generator(), self.chunk_size, self.context)

  @classmethod
  def from_pipeline(cls, pipeline: "Pipeline[T]") -> "Pipeline[T]":
    """Create a new Pipeline from another Pipeline, preserving its state."""
    new_pipeline = cls([], chunk_size=pipeline.chunk_size)
    new_pipeline.generator = pipeline.generator
    new_pipeline.context = pipeline.context
    return new_pipeline

  def passthrough(self) -> Self:
    """Return the pipeline unchanged (identity operation)."""
    return self
