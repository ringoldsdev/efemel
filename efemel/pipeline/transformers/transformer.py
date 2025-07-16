from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
import copy
from functools import reduce
import itertools
from typing import Any
from typing import Self
from typing import Union
from typing import overload

from efemel.pipeline.helpers import PipelineContext
from efemel.pipeline.helpers import is_context_aware
from efemel.pipeline.helpers import is_context_aware_reduce

DEFAULT_CHUNK_SIZE = 1000


type PipelineFunction[Out, T] = Callable[[Out], T] | Callable[[Out, PipelineContext], T]
type PipelineReduceFunction[U, Out] = Callable[[U, Out], U] | Callable[[U, Out, PipelineContext], U]

# The internal transformer function signature is changed to explicitly accept a context.
type InternalTransformer[In, Out] = Callable[[list[In], PipelineContext], list[Out]]
type ChunkErrorHandler[In, U] = Callable[[list[In], Exception, PipelineContext], list[U]]


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

  def on_error(self, handler: ChunkErrorHandler[In, Out]) -> "Transformer[In, Out]":
    """Registers an error handler for the transformer."""
    # This method is a placeholder for future error handling logic.
    # Currently, it does not modify the transformer behavior.
    self.error_handler = handler
    return self

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

  def map[U](self, function: PipelineFunction[Out, U]) -> "Transformer[In, U]":
    """Transforms elements, passing context explicitly to the mapping function."""
    if is_context_aware(function):
      return self._pipe(lambda chunk, ctx: [function(x, ctx) for x in chunk])

    return self._pipe(lambda chunk, _ctx: [function(x) for x in chunk])  # type: ignore

  def filter(self, predicate: PipelineFunction[Out, bool]) -> "Transformer[In, Out]":
    """Filters elements, passing context explicitly to the predicate function."""
    if is_context_aware(predicate):
      return self._pipe(lambda chunk, ctx: [x for x in chunk if predicate(x, ctx)])

    return self._pipe(lambda chunk, _ctx: [x for x in chunk if predicate(x)])  # type: ignore

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

    if is_context_aware(function):
      return self._pipe(lambda chunk, ctx: [x for x in chunk if function(x, ctx) or True])

    return self._pipe(lambda chunk, _ctx: [function(x) or x for x in chunk])  # type: ignore

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

    if is_context_aware_reduce(function):

      def _reduce_with_context(data: Iterable[In], context: PipelineContext | None = None) -> Iterator[U]:
        # The context for the run is determined here.
        run_context = context or self.context

        data_iterator = self(data, run_context)

        def function_wrapper(acc: U, value: Out) -> U:
          return function(acc, value, run_context)

        yield reduce(function_wrapper, data_iterator, initial)

      return _reduce_with_context

    # Not context-aware, so we adapt the function to ignore the context.
    def _reduce(data: Iterable[In], context: PipelineContext | None = None) -> Iterator[U]:
      # The context for the run is determined here.
      run_context = context or self.context

      data_iterator = self(data, run_context)

      yield reduce(function, data_iterator, initial)  # type: ignore

    return _reduce

  def catch[U](
    self,
    sub_pipeline_builder: Callable[["Transformer[Out, Out]"], "Transformer[Out, U]"],
    on_error: ChunkErrorHandler[Out, U] | None = None,
  ) -> "Transformer[In, U]":
    """
    Isolates a sub-pipeline in a chunk-based try-catch block.
    If the sub-pipeline fails for a chunk, the on_error handler is invoked.
    """

    # Check if we have any error handlers available
    error_handler = self.error_handler if hasattr(self, "error_handler") else None or on_error

    assert error_handler, "No error handler provided for Transformer.catch"

    # Create a blank transformer for the sub-pipeline
    temp_transformer = Transformer.init(_type_hint=..., chunk_size=self.chunk_size)  # type: ignore

    # Build the sub-pipeline and get its internal transformer function
    sub_pipeline = sub_pipeline_builder(temp_transformer)
    sub_transformer_func = sub_pipeline.transformer

    def operation(chunk: list[Out], ctx: PipelineContext) -> list[U]:
      try:
        # Attempt to process the whole chunk with the sub-pipeline
        return sub_transformer_func(chunk, ctx)
      except Exception as e:
        # On failure, delegate to the chunk-based error handler
        return error_handler(chunk, e, ctx) or []  # type: ignore

    return self._pipe(operation)  # type: ignore
