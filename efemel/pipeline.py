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
import threading
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


def _create_context_aware_function(func: Callable, context: "PipelineContext") -> Callable[[Any], Any]:
  """
  Create a standardized function that always takes just a value parameter.

  This builder analyzes the user function once and returns a wrapper that:
  - Calls func(value) if the original function takes 1 parameter
  - Calls func(value, context) if the original function takes 2+ parameters

  Args:
    func: The user-provided function
    context: The pipeline context to pass if needed

  Returns:
    A function that takes only a value parameter
  """
  try:
    sig = inspect.signature(func)
    param_count = len([p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)])

    if param_count >= 2:
      # Function accepts context
      return lambda value: func(value, context)
    else:
      # Function takes only value
      return lambda value: func(value)
  except (ValueError, TypeError):
    # Fall back to single parameter for lambda or built-in functions
    return lambda value: func(value)


def _create_reduce_function(func: Callable, context: "PipelineContext") -> Callable[[Any, Any], Any]:
  """
  Create a standardized reduce function that always takes (accumulator, value) parameters.

  This builder analyzes the user function once and returns a wrapper that:
  - Calls func(acc, value) if the original function takes 2 parameters
  - Calls func(acc, value, context) if the original function takes 3+ parameters

  Args:
    func: The user-provided reduce function
    context: The pipeline context to pass if needed

  Returns:
    A function that takes (accumulator, value) parameters
  """
  try:
    sig = inspect.signature(func)
    param_count = len([p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)])

    if param_count >= 3:
      # Function accepts context as third parameter
      return lambda acc, value: func(acc, value, context)
    else:
      # Function takes only (acc, value)
      return lambda acc, value: func(acc, value)
  except (ValueError, TypeError):
    # Fall back to 2-parameter call for lambda or built-in functions
    return lambda acc, value: func(acc, value)


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
              # Create a standardized function using the item's specific context
              std_function = _create_context_aware_function(function, context)
              # Apply the standardized function
              result = std_function(value)
              new_chunk.append(PipelineItem(result, None, context))
            except Exception as e:
              # On failure, capture the exception
              new_chunk.append(PipelineItem(value, e, context))
              self.context["has_errors"] = True
        yield new_chunk

    return Pipeline._from_chunks(map_generator(), self.chunk_size, self.context)

  def filter(self, predicate: Callable[[T], bool] | Callable[[T, PipelineContext], bool]) -> "Pipeline[T]":
    """Filter elements, capturing any exceptions from the predicate."""

    # Create a standardized predicate that always takes just value
    std_predicate = _create_context_aware_function(predicate, self.context)

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
            result = std_predicate(item.value)
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

      # Create a standardized reduce function that always takes (acc, value)
      std_function = _create_reduce_function(function, self.context)

      for chunk in self.generator:
        for value, error, context in chunk:
          if error:
            error_items.append(PipelineItem(value, error, context))
            self.context["has_errors"] = True
          else:
            try:
              acc = std_function(acc, value)
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

    # Create a standardized function that always takes just value
    std_function = _create_context_aware_function(function, self.context)

    errors: list[Exception] = []
    for chunk in self.generator:
      for value, error, _ in chunk:
        if error:
          errors.append(error)
          self.context["has_errors"] = True
        else:
          try:
            std_function(value)
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

    # Thread-safe context merging
    context_lock = threading.Lock()
    merged_errors: list[dict[str, Any]] = []
    isolated_contexts: list[PipelineContext] = []

    def apply_to_chunk(chunk: list[PipelineItem[T]]) -> list[PipelineItem[U]]:
      # Create an isolated context for this thread, copying the main context
      isolated_context = PipelineContext(has_errors=False, errors=[])
      # Copy any existing context fields from main context
      isolated_context.update(self.context)
      isolated_context["has_errors"] = False
      isolated_context["errors"] = []

      # Create a mini-pipeline from the single chunk with isolated context
      chunk_pipeline = Pipeline._from_chunks([chunk], len(chunk), isolated_context)
      processed_pipeline = pipeline_func(chunk_pipeline)

      # Collect results and store context for later merging
      result = [item for processed_chunk in processed_pipeline.generator for item in processed_chunk]

      # Thread-safe context collection
      with context_lock:
        isolated_contexts.append(isolated_context)
        if isolated_context["has_errors"] or isolated_context["errors"]:
          self.context["has_errors"] = True
          merged_errors.extend(isolated_context["errors"])

      return result

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

    # Process all chunks and collect results
    result_pipeline = Pipeline._from_chunks(process_in_pool(gen), self.chunk_size, self.context)

    # Final context merge after all threads complete
    with context_lock:
      self.context["errors"].extend(merged_errors)

      # Merge all context fields from isolated contexts
      for isolated_context in isolated_contexts:
        for key, value in isolated_context.items():
          if key not in ["has_errors", "errors"]:  # Skip standard fields already handled
            if key in self.context:
              # If the field already exists, merge it intelligently
              if isinstance(value, list) and isinstance(self.context[key], list):
                self.context[key].extend(value)
              elif isinstance(value, dict) and isinstance(self.context[key], dict):
                self.context[key].update(value)
              else:
                # For other types, use the latest value
                self.context[key] = value
            else:
              # New field, just add it
              self.context[key] = value

    return result_pipeline

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

    # Create a standardized function that always takes just value
    std_function = _create_context_aware_function(function, self.context)

    def tap_generator() -> Generator[list[PipelineItem[T]], None, None]:
      for chunk in self.generator:
        for value, error, _ in chunk:
          # Apply tap only to non-errored items
          if not error:
            try:
              std_function(value)
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
