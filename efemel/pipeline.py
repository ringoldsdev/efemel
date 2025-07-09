"""
Pipeline module for functional data processing.

This module provides a Pipeline class that enables functional programming patterns
for data transformation and processing. It allows chaining operations like map, filter,
reduce, and more in a fluent interface style.

Example:
    >>> pipeline = Pipeline([1, 2, 3, 4, 5])
    >>> result = pipeline.filter(lambda x: x % 2 == 0).map(lambda x: x * 2).to_list()
    >>> print(result)  # [4, 8]
"""

import functools
from collections.abc import Callable, Generator, Iterable
from typing import Any, Self, TypeVar, cast

T = TypeVar("T")  # Type variable for the elements in the pipeline
U = TypeVar("U")  # Type variable for transformed elements
V = TypeVar("V")  # Type variable for additional transformations


class Pipeline[T]:
  """
  A functional pipeline for data processing with method chaining.

  The Pipeline class wraps an iterable and provides a fluent interface for
  applying transformations, filters, and reductions in a functional programming style.

  Type Parameters:
      T: The type of elements in the pipeline

  Attributes:
      generator: The underlying iterable that provides the data source

  Example:
      >>> data = [1, 2, 3, 4, 5]
      >>> pipeline = Pipeline(data)
      >>> result = (pipeline
      ...     .filter(lambda x: x > 2)
      ...     .map(lambda x: x ** 2)
      ...     .to_list())
      >>> print(result)  # [9, 16, 25]
  """

  generator: Iterable[T]

  def __init__(self, source: Iterable[T]):
    """
    Initialize a new Pipeline with the given data source.

    Args:
        source: An iterable that provides the data for the pipeline
    """
    self.generator = source

  def __next__(self) -> T:
    """
    Get the next item from the pipeline.

    Returns:
        The next item in the pipeline

    Raises:
        StopIteration: When there are no more items
    """
    return next(iter(self.generator))

  def __iter__(self) -> Generator[T, None, None]:
    """
    Return an iterator over the pipeline elements.

    Returns:
        A generator that yields the pipeline elements
    """
    yield from self.generator

  def to_list(self) -> list[T]:
    """
    Convert the pipeline to a list.

    Returns:
        A list containing all elements from the pipeline

    Example:
        >>> Pipeline([1, 2, 3]).to_list()
        [1, 2, 3]
    """
    return list(self)

  def first(self) -> T:
    """
    Get the first element from the pipeline.

    Returns:
        The first element in the pipeline

    Raises:
        StopIteration: If the pipeline is empty

    Example:
        >>> Pipeline([1, 2, 3]).first()
        1
    """
    return next(iter(self.generator))

  def filter(
    self,
    predicate: Callable[[T], bool],
  ) -> "Pipeline[T]":
    """
    Filter pipeline elements based on a predicate function.

    Args:
        predicate: A function that takes an element and returns True to keep it

    Returns:
        A new pipeline containing only elements that satisfy the predicate

    Example:
        >>> Pipeline([1, 2, 3, 4]).filter(lambda x: x % 2 == 0).to_list()
        [2, 4]
    """
    return Pipeline(item for item in self if predicate(item))

  def map(
    self,
    function: Callable[[T], U],
  ) -> "Pipeline[U]":
    """
    Transform each element in the pipeline using the given function.

    Args:
        function: A function that transforms each element

    Returns:
        A new pipeline with transformed elements

    Example:
        >>> Pipeline([1, 2, 3]).map(lambda x: x * 2).to_list()
        [2, 4, 6]
    """
    return Pipeline(
      map(
        function,
        self.generator,
      )
    )

  def reduce(self, function: Callable[[U, T], U], initial: U) -> "Pipeline[U]":
    """
    Reduce the pipeline to a single value using the given function.

    Args:
        function: A function that takes an accumulator and current element
        initial: The initial value for the accumulator

    Returns:
        A new pipeline containing the single reduced value

    Example:
        >>> Pipeline([1, 2, 3, 4]).reduce(lambda acc, x: acc + x, 0).first()
        10
    """
    return Pipeline([functools.reduce(cast(Callable[[T, U], U], function), self, initial)])

  def tap(self, function: Callable[[T], Any]) -> Self:
    """
    Execute a side effect for each element without modifying the pipeline.

    Args:
        function: A function to execute for each element (side effect)

    Returns:
        The same pipeline (for method chaining)

    Example:
        >>> Pipeline([1, 2, 3]).tap(print).map(lambda x: x * 2).to_list()
        1
        2
        3
        [2, 4, 6]
    """

    def f(x: T) -> T:
      function(x)
      return x

    return type(self)(self.map(f))

  def each(self, function: Callable[[T], Any]) -> None:
    """
    Execute a function for each element in the pipeline (terminal operation).

    Args:
        function: A function to execute for each element

    Example:
        >>> Pipeline([1, 2, 3]).each(print)
        1
        2
        3
    """
    for item in self.generator:
      function(item)

  def passthrough(self) -> Self:
    """
    Return the pipeline unchanged (identity operation).

    Returns:
        The same pipeline instance

    Example:
        >>> pipeline = Pipeline([1, 2, 3])
        >>> same = pipeline.passthrough()
        >>> pipeline is same
        True
    """
    return self

  def apply(self, *functions: Callable[[Self], "Pipeline[U]"]) -> "Pipeline[U]":
    """
    Apply a sequence of functions to the pipeline.

    Args:
        *functions: Functions that transform the pipeline

    Returns:
        The pipeline after applying all functions

    Example:
        >>> def double(p): return p.map(lambda x: x * 2)
        >>> def filter_even(p): return p.filter(lambda x: x % 2 == 0)
        >>> Pipeline([1, 2, 3]).apply(double, filter_even).to_list()
        [2, 4, 6]
    """
    result: Pipeline[T] = self

    for function in functions:
      result = function(result)

    return result

  def flatten(self: "Pipeline[Iterable[U]]") -> "Pipeline[U]":
    """
    Flatten a pipeline of iterables into a single pipeline.

    Returns:
        A new pipeline with all nested elements flattened

    Example:
        >>> Pipeline([[1, 2], [3, 4], [5]]).flatten().to_list()
        [1, 2, 3, 4, 5]
    """
    return Pipeline(x_i for x in self for x_i in x)
