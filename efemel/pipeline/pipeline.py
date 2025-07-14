from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
import itertools
from typing import Any
from typing import TypedDict
from typing import TypeVar

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
    self.data_source: Iterable[T] = itertools.chain.from_iterable(data)
    self.processed_data: Iterator = iter(self.data_source)

  def apply[U](self, transformer: Transformer[T, U] | Callable[[Iterable[T]], Iterator[U]]) -> "Pipeline[U]":
    """
    Applies a transformer to the current data source.
    """
    # The transformer is called with the current data, producing a new iterator
    self.processed_data = transformer(self.data_source)
    # We must cast self to the new type.
    return self  # type: ignore

  def transform[U](self, transformer: Callable[[Transformer[T, T]], Transformer[T, U]]) -> "Pipeline[U]":
    """
    Shorthand method to apply a transformation using a lambda function.
    Creates a Transformer under the hood and applies it to the pipeline.

    Args:
        function: A callable that transforms each element from type T to type U

    Returns:
        A new Pipeline with the transformed data
    """
    # Create a new transformer with identity and apply the map operation
    # We create a basic transformer and immediately map with the function

    return self.apply(Transformer[T, T]().apply(transformer))

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


t = Transformer.init(int).map(lambda x: x * 2).reduce(lambda acc, x: acc + x, initial=0)
# t = 1

# Example using the original apply method with a full transformer
Pipeline([1, 2, 3, 4]).apply(t).each(lambda x: print(x))

# Example using the new shorthand transform method
Pipeline([1, 2, 3, 4]).transform(lambda x: x.map(lambda y: y * 2)).each(lambda x: print(x))
