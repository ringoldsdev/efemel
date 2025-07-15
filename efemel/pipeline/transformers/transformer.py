from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
import copy
from functools import reduce
import inspect
import itertools
from typing import Any
from typing import Self
from typing import Union
from typing import overload

from efemel.pipeline.helpers import create_context_aware_function

DEFAULT_CHUNK_SIZE = 1000


# --- Type Aliases ---
class PipelineContext(dict):
  """Generic, untyped context available to all pipeline operations."""

  pass


type PipelineFunction[Out, T] = Callable[[Out], T] | Callable[[Out, PipelineContext], T]
type PipelineReduceFunction[U, Out] = Callable[[U, Out], U] | Callable[[U, Out, PipelineContext], U]

# The internal transformer function signature is changed to explicitly accept a context.
type InternalTransformer[In, Out] = Callable[[list[In], PipelineContext], list[Out]]


class Transformer[In, Out]:
  """
  Defines and composes data transformations by passing context explicitly.
  """

  def __init__(
    self,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    transformer: InternalTransformer[In, Out] | None = None,
  ):
    self.chunk_size = chunk_size
    self.context: PipelineContext = PipelineContext()
    # The default transformer now accepts and ignores a context argument.
    self.transformer: InternalTransformer[In, Out] = transformer or (lambda chunk, ctx: chunk)  # type: ignore

  @classmethod
  def init[T](cls, _type_hint: type[T], chunk_size: int = DEFAULT_CHUNK_SIZE) -> "Transformer[T, T]":
    """Create a new identity pipeline with an explicit type hint."""
    return cls(chunk_size=chunk_size)  # type: ignore

  @classmethod
  def from_transformer[T, U](
    cls,
    transformer: "Transformer[T, U]",
    chunk_size: int | None = None,
  ) -> "Transformer[T, U]":
    """Create a new transformer from an existing one, copying its logic."""
    return cls(
      chunk_size=chunk_size or transformer.chunk_size,
      transformer=copy.deepcopy(transformer.transformer),  # type: ignore
    )

  def _chunk_generator(self, data: Iterable[In]) -> Iterator[list[In]]:
    """Breaks an iterable into chunks of a specified size."""
    data_iter = iter(data)
    while chunk := list(itertools.islice(data_iter, self.chunk_size)):
      yield chunk

  def _pipe[U](self, operation: Callable[[list[Out], PipelineContext], list[U]]) -> "Transformer[In, U]":
    """Composes the current transformer with a new context-aware operation."""
    prev_transformer = self.transformer
    # The new transformer chain ensures the context `ctx` is passed at each step.
    self.transformer = lambda chunk, ctx: operation(prev_transformer(chunk, ctx), ctx)  # type: ignore
    return self  # type: ignore

  def _create_reduce_function(self, func: PipelineReduceFunction) -> Callable[[Any, Any, PipelineContext], Any]:
    """Normalizes a user-provided reduce function to accept a context argument."""
    try:
      sig = inspect.signature(func)
      params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
      if len(params) >= 3:
        return func  # type: ignore
    except (ValueError, TypeError):
      pass
    # Adapt a simple reducer (e.g., lambda acc, val: acc + val).
    return lambda acc, value, ctx: func(acc, value)  # type: ignore

  def map[U](self, function: PipelineFunction[Out, U]) -> "Transformer[In, U]":
    """Transforms elements, passing context explicitly to the mapping function."""
    std_function = create_context_aware_function(function)
    # The operation passed to _pipe receives the chunk and context, and applies the function.
    return self._pipe(lambda chunk, ctx: [std_function(x, ctx) for x in chunk])

  def filter(self, predicate: PipelineFunction[Out, bool]) -> "Transformer[In, Out]":
    """Filters elements, passing context explicitly to the predicate function."""
    std_predicate = create_context_aware_function(predicate)
    return self._pipe(lambda chunk, ctx: [x for x in chunk if std_predicate(x, ctx)])

  @overload
  def flatten[T](self: "Transformer[In, list[T]]") -> "Transformer[In, T]": ...
  @overload
  def flatten[T](self: "Transformer[In, tuple[T, ...]]") -> "Transformer[In, T]": ...
  @overload
  def flatten[T](self: "Transformer[In, set[T]]") -> "Transformer[In, T]": ...

  def flatten[T](
    self: Union["Transformer[In, list[T]]", "Transformer[In, tuple[T, ...]]", "Transformer[In, set[T]]"],
  ) -> "Transformer[In, T]":
    """Flattens nested lists; the context is passed through the operation."""
    return self._pipe(lambda chunk, ctx: [item for sublist in chunk for item in sublist])  # type: ignore

  def tap(self, function: PipelineFunction[Out, Any]) -> "Transformer[In, Out]":
    """Applies a side-effect function without modifying the data."""
    std_function = create_context_aware_function(function)

    def tap_operation(chunk: list[Out], ctx: PipelineContext) -> list[Out]:
      for item in chunk:
        std_function(item, ctx)
      return chunk

    return self._pipe(tap_operation)

  def apply[T](self, t: Callable[[Self], "Transformer[In, T]"]) -> "Transformer[In, T]":
    """Apply another pipeline to the current one."""
    return t(self)

  def __call__(self, data: Iterable[In], context: PipelineContext | None = None) -> Iterator[Out]:
    """
    Executes the transformer on a data source.

    It uses the provided `context` by reference. If none is provided, it uses
    the transformer's internal context.
    """
    # Use the provided context by reference, or default to the instance's context.
    run_context = context or self.context

    for chunk in self._chunk_generator(data):
      # The context is now passed explicitly through the transformer chain.
      yield from self.transformer(chunk, run_context)

  def reduce[U](self, function: PipelineReduceFunction[U, Out], initial: U):
    """Reduces elements to a single value (terminal operation)."""
    std_reducer = self._create_reduce_function(function)

    def _reduce(data: Iterable[In], context: PipelineContext | None = None) -> Iterator[U]:
      # The context for the run is determined here.
      run_context = context or self.context

      # The generator now needs the context to pass to the transformer.
      data_iterator = self(data, run_context)

      # We need a new reducer that curries the context for functools.reduce.
      def reducer_with_context(acc, value):
        return std_reducer(acc, value, run_context)

      yield reduce(reducer_with_context, data_iterator, initial)

    return _reduce
