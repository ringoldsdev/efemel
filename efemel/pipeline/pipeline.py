from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
import itertools
from typing import Any
from typing import TypedDict
from typing import TypeVar
from typing import overload

from efemel.pipeline.helpers import create_context_aware_function

from .transformers.transformer import Transformer

# --- Type Aliases ---
T = TypeVar("T")
PipelineFunction = Callable[[T], Any]


class PipelineContext(TypedDict):
  """Global context available to all pipeline operations."""

  pass


class Pipeline[T]:
  """
  Manages a data source and applies transformers to it.
  Provides terminal operations to consume the resulting data.
  """

  def __init__(self, *data: Iterable[T]):
    self.data_source: Iterable[T] = itertools.chain.from_iterable(data) if len(data) > 1 else data[0]
    self.processed_data: Iterator = iter(self.data_source)
    self.ctx = PipelineContext()

  def context(self, ctx: PipelineContext) -> "Pipeline[T]":
    """
    Sets the context for the pipeline.
    """
    self.ctx = ctx
    return self

  @overload
  def apply[U](self, transformer: Transformer[T, U]) -> "Pipeline[U]": ...

  @overload
  def apply[U](self, transformer: Callable[[Iterable[T]], Iterator[U]]) -> "Pipeline[U]": ...

  @overload
  def apply[U](
    self,
    transformer: Callable[[Iterable[T], PipelineContext], Iterator[U]],
  ) -> "Pipeline[U]": ...

  def apply[U](
    self,
    transformer: Transformer[T, U]
    | Callable[[Iterable[T]], Iterator[U]]
    | Callable[[Iterable[T], PipelineContext], Iterator[U]],
  ) -> "Pipeline[U]":
    """
    Applies a transformer to the current data source.
    """

    match transformer:
      case Transformer():
        # If a Transformer instance is provided, use its __call__ method
        self.processed_data = transformer(self.processed_data, self.ctx)  # type: ignore
      case _ if callable(transformer):
        # If a callable function is provided, call it with the current data and context
        processed_transformer = create_context_aware_function(transformer)  # type: ignore
        self.processed_data = processed_transformer(self.processed_data, self.ctx)
      case _:
        raise TypeError("Transformer must be a Transformer instance or a callable function")

    return self  # type: ignore

  def transform[U](self, t: Callable[[Transformer[T, T]], Transformer[T, U]]) -> "Pipeline[U]":
    """
    Shorthand method to apply a transformation using a lambda function.
    Creates a Transformer under the hood and applies it to the pipeline.

    Args:
        t: A callable that takes a transformer and returns a transformed transformer

    Returns:
        A new Pipeline with the transformed data
    """
    # Create a new transformer and apply the transformation function
    transformer = t(Transformer[T, T]())
    return self.apply(transformer)

  def __iter__(self) -> Iterator[T]:
    """Allows the pipeline to be iterated over."""
    yield from self.processed_data

  def to_list(self) -> list[T]:
    """Executes the pipeline and returns the results as a list."""
    return list(self.processed_data)

  def each(self, function: PipelineFunction[T]) -> None:
    """Applies a function to each element (terminal operation)."""
    # Context needs to be accessed from the function if it's context-aware,
    # but the pipeline itself doesn't own a context. This is a design choice.
    # For simplicity, we assume the function is not context-aware here
    # or that context is handled within the Transformers.
    for item in self.processed_data:
      function(item)

  def first(self, n: int = 1) -> list[T]:
    """Gets the first n elements of the pipeline (terminal operation)."""
    assert n >= 1, "n must be at least 1"
    return list(itertools.islice(self.processed_data, n))

  def consume(self) -> None:
    """Consumes the pipeline without returning results."""
    for _ in self.processed_data:
      pass
