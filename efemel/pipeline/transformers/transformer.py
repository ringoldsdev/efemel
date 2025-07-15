from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
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
