from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


# Special symbols for reduce operations
class SymbolEnd:
  """
  Special symbol used to signal the end of a stream in reduce operations.
  When this symbol is passed to a reduce transformation, it triggers the
  final result to be emitted.
  """

  def __repr__(self):
    return "SymbolEnd"


class SymbolReset:
  """
  Special symbol used to reset the accumulator in reduce operations.
  When this symbol is passed to a reduce transformation, it resets the
  accumulator back to its initial value.
  """

  def __repr__(self):
    return "SymbolReset"


SYMBOL_END = SymbolEnd()
SYMBOL_RESET = SymbolReset()


class Pipeline:
  """
  A functional pipeline that chains transformations together in a composable way.

  This class implements a callback-based transformation pipeline similar to TypeScript's
  transformers.ts. Each transformation is built up through method chaining, creating
  a single composed transformation function that can be executed with `.run()`.

  Key Concepts:
  - **Chaining**: Methods return self, allowing for fluent API usage
  - **Callback-based**: Each transformation uses success/failure callbacks
  - **Composable**: Transformations are built up by wrapping previous transformations
  - **Failure handling**: Any step can fail, causing the entire pipeline to fail

  Basic Usage:
  ```python
  # Simple transformation pipeline
  pipeline = Pipeline()
  result = pipeline.map(lambda x: x * 2).filter(lambda x: x > 10).run(6)
  # result = 12 (6 * 2 = 12, 12 > 10 is True)

  # Pipeline that fails
  result = pipeline.map(lambda x: x * 2).filter(lambda x: x > 20).run(6)
  # result = None (6 * 2 = 12, 12 > 20 is False, so filter fails)
  ```

  Advanced Usage:
  ```python
  # Working with lists
  pipeline = Pipeline()
  result = pipeline.multi(lambda p: p.map(lambda x: x.upper())).run(["hello", "world"])
  # result = ["HELLO", "WORLD"]

  # Reduce operations
  pipeline = Pipeline()
  pipeline.reduce(lambda acc, x: acc + x, 0)
  pipeline.run(5)  # Accumulates: 0 + 5 = 5
  pipeline.run(3)  # Accumulates: 5 + 3 = 8
  result = pipeline.run(SYMBOL_END)  # result = 8
  ```
  """

  def __init__(self):
    # Internal transformation function that gets built up through chaining
    self._transformation = self._create_identity_transformation()

  def _create_identity_transformation(self):
    """
    Create the base identity transformation that simply passes input to output.

    This is the foundation that all other transformations build upon.
    It takes an input value and immediately calls the success callback with it.

    Returns:
        A transformation function that accepts (input_value, success_callback, failure_callback)
    """

    def transform(input_value, success_callback, failure_callback):
      try:
        success_callback(input_value)
      except Exception:
        failure_callback()

    return transform

  def identity(self):
    """
    Reset the pipeline to identity transformation.

    This method resets the pipeline back to its initial state, effectively
    clearing all previously chained transformations.

    Returns:
        self: For method chaining

    Example:
    ```python
    pipeline = Pipeline()
    pipeline.map(lambda x: x * 2).filter(lambda x: x > 10)

    # Reset the pipeline
    pipeline.identity()

    # Now the pipeline just passes values through unchanged
    result = pipeline.run(5)  # result = 5
    ```
    """
    self._transformation = self._create_identity_transformation()
    return self

  def map(self, modifier: Callable[[Any], Any]):
    """
    Apply a transformation function to the input value.

    This is equivalent to the functional programming `map` operation.
    It takes the current value in the pipeline and transforms it using
    the provided modifier function.

    Args:
        modifier: A function that takes one argument and returns a transformed value

    Returns:
        self: For method chaining

    Example:
    ```python
    # Double all numbers
    pipeline = Pipeline()
    result = pipeline.map(lambda x: x * 2).run(5)
    # result = 10

    # Chain multiple maps
    result = pipeline.map(lambda x: x * 2).map(lambda x: x + 1).run(5)
    # result = 11 (5 * 2 = 10, 10 + 1 = 11)

    # Transform strings
    result = pipeline.map(str.upper).run("hello")
    # result = "HELLO"
    ```

    Failure handling:
    ```python
    # If the modifier function raises an exception, the pipeline fails
    pipeline = Pipeline()
    result = pipeline.map(lambda x: x / 0).run(5)  # Division by zero
    # result = None (pipeline failed)
    ```
    """
    current_transformation = self._transformation

    def new_transformation(input_value, success_callback, failure_callback):
      def on_success(transformed_value):
        try:
          result = modifier(transformed_value)
          success_callback(result)
        except Exception:
          failure_callback()

      current_transformation(input_value, on_success, failure_callback)

    self._transformation = new_transformation
    return self

  def filter(self, predicate: Callable[[Any], bool]):
    """
    Filter values based on a predicate function.

    This is equivalent to the functional programming `filter` operation.
    If the predicate returns True, the value passes through. If it returns
    False, the pipeline fails (calls failure_callback).

    Args:
        predicate: A function that takes one argument and returns True/False

    Returns:
        self: For method chaining

    Example:
    ```python
    # Only allow even numbers
    pipeline = Pipeline()
    result = pipeline.filter(lambda x: x % 2 == 0).run(4)
    # result = 4 (4 is even, so it passes)

    result = pipeline.filter(lambda x: x % 2 == 0).run(5)
    # result = None (5 is odd, so filter fails)

    # Chain with map
    result = pipeline.map(lambda x: x * 2).filter(lambda x: x > 10).run(6)
    # result = 12 (6 * 2 = 12, 12 > 10 is True)

    result = pipeline.map(lambda x: x * 2).filter(lambda x: x > 20).run(6)
    # result = None (6 * 2 = 12, 12 > 20 is False)
    ```

    String filtering:
    ```python
    # Only allow non-empty strings
    pipeline = Pipeline()
    result = pipeline.filter(lambda s: len(s) > 0).run("hello")
    # result = "hello"

    result = pipeline.filter(lambda s: len(s) > 0).run("")
    # result = None (empty string fails the filter)
    ```
    """
    current_transformation = self._transformation

    def new_transformation(input_value, success_callback, failure_callback):
      def on_success(transformed_value):
        try:
          if predicate(transformed_value):
            success_callback(transformed_value)
          else:
            failure_callback()
        except Exception:
          failure_callback()

      current_transformation(input_value, on_success, failure_callback)

    self._transformation = new_transformation
    return self

  def reduce(self, accumulator: Callable[[Any, Any], Any], initial_value: Any):
    """
    Apply a reduce operation with stateful accumulation.

    This is equivalent to the functional programming `reduce` operation, but implemented
    in a stateful way. The accumulator maintains state between calls, and special
    symbols (SYMBOL_END, SYMBOL_RESET) control the reduction process.

    Args:
        accumulator: A function that takes (accumulated_value, current_value) and returns new accumulated value
        initial_value: The starting value for the accumulation

    Returns:
        self: For method chaining

    Special Symbols:
        - SYMBOL_END: Triggers the final result to be emitted
        - SYMBOL_RESET: Resets the accumulator back to initial_value

    Example - Sum accumulation:
    ```python
    pipeline = Pipeline()
    pipeline.reduce(lambda acc, x: acc + x, 0)

    # Add numbers to the accumulator
    pipeline.run(5)   # Internal state: 0 + 5 = 5
    pipeline.run(3)   # Internal state: 5 + 3 = 8
    pipeline.run(2)   # Internal state: 8 + 2 = 10

    # Get the final result
    result = pipeline.run(SYMBOL_END)  # result = 10

    # Reset and start over
    pipeline.run(SYMBOL_RESET)  # Internal state reset to 0
    pipeline.run(7)   # Internal state: 0 + 7 = 7
    result = pipeline.run(SYMBOL_END)  # result = 7
    ```

    Example - List accumulation:
    ```python
    pipeline = Pipeline()
    pipeline.reduce(lambda acc, x: acc + [x], [])

    pipeline.run("a")  # Internal state: [] + ["a"] = ["a"]
    pipeline.run("b")  # Internal state: ["a"] + ["b"] = ["a", "b"]
    result = pipeline.run(SYMBOL_END)  # result = ["a", "b"]
    ```

    Example - Object accumulation:
    ```python
    pipeline = Pipeline()
    pipeline.reduce(lambda acc, item: {**acc, **item}, {})

    pipeline.run({"name": "John"})    # Internal state: {"name": "John"}
    pipeline.run({"age": 30})         # Internal state: {"name": "John", "age": 30}
    result = pipeline.run(SYMBOL_END) # result = {"name": "John", "age": 30}
    ```
    """
    current_transformation = self._transformation
    acc = initial_value

    def new_transformation(input_value, success_callback, failure_callback):
      nonlocal acc

      if input_value is SYMBOL_END:
        success_callback(acc)
        return

      if input_value is SYMBOL_RESET:
        acc = initial_value
        return

      def on_success(transformed_value):
        nonlocal acc
        try:
          acc = accumulator(acc, transformed_value)
        except Exception:
          failure_callback()

      current_transformation(input_value, on_success, failure_callback)

    self._transformation = new_transformation
    return self

  def multi(self, create_transformation: Callable[["Pipeline"], "Pipeline"]):
    """
    Apply a transformation to each item in a list/array.
    
    This method takes a factory function that creates a transformation pipeline
    for individual items. It then applies this transformation to each item in
    an input list, collecting the results.
    
    Args:
        create_transformation: A function that takes a Pipeline and returns a configured Pipeline
                              for transforming individual items
                              
    Returns:
        self: For method chaining
        
    Example - Transform each string in a list:
    ```python
    pipeline = Pipeline()
    result = pipeline.multi(lambda p: p.map(str.upper)).run(["hello", "world"])
    # result = ["HELLO", "WORLD"]
    ```
    
    Example - Filter and transform:
    ```python
    pipeline = Pipeline()
    result = pipeline.multi(
        lambda p: p.filter(lambda x: x > 0).map(lambda x: x * 2)
    ).run([1, -2, 3, -4, 5])
    # result = [2, 6, 10] (negative numbers filtered out, positive ones doubled)
    ```
    
    Example - Complex object transformation:
    ```python
    users = [
        {"name": "john", "age": 25},
        {"name": "jane", "age": 17},
        {"name": "bob", "age": 30}
    ]
    
    pipeline = Pipeline()
    result = pipeline.multi(
        lambda p: p
            .filter(lambda user: user["age"] >= 18)  # Only adults
            .map(lambda user: user["name"].title())   # Extract and capitalize name
    ).run(users)
    # result = ["John", "Bob"]
    ```
    
    Failure handling:
    ```python
    # If any item transformation fails, the entire multi operation fails
    pipeline = Pipeline()
    result = pipeline.multi(
        lambda p: p.map(lambda x: 1 / x)  # Division by zero will fail
    ).run([1, 2, 0, 3])
    # result = None (pipeline fails when processing 0)
    ```
    
    Chaining with other operations:
    ```python
    pipeline = Pipeline()
    result = pipeline\
        .multi(lambda p: p.map(lambda x: x * 2))\
        .map(lambda results: sum(results))\
        .run([1, 2, 3])
    # Step 1: [1, 2, 3] -> [2, 4, 6] (multi doubles each)
    # Step 2: [2, 4, 6] -> 12 (map sums the results)
    # result = 12
    ```
    """
    current_transformation = self._transformation

    # Create the item transformer by calling the factory function with a new identity pipeline
    item_pipeline = Pipeline().identity()
    item_transformer = create_transformation(item_pipeline)._transformation

    def new_transformation(input_value, success_callback, failure_callback):
      def on_success(transformed_values: list[Any]):
        try:
          results = []
          for value in transformed_values:
            result = None

            def item_success(data):
              nonlocal result
              result = data

            def item_failure():
              nonlocal result
              result = None

            item_transformer(value, item_success, item_failure)

            if result is not None:
              results.append(result)
            else:
              failure_callback()
              return

          success_callback(results)
        except Exception:
          failure_callback()

      current_transformation(input_value, on_success, failure_callback)

    self._transformation = new_transformation
    return self

  def run(self, input_value: Any) -> Any | None:
    """
    Execute the pipeline with the given input value.
    
    This method runs the entire transformation pipeline synchronously and returns
    the final result. If any step in the pipeline fails, it returns None.
    
    Args:
        input_value: The value to process through the pipeline
        
    Returns:
        The final transformed value, or None if the pipeline failed
        
    Example - Basic usage:
    ```python
    pipeline = Pipeline()
    result = pipeline.map(lambda x: x * 2).run(5)
    # result = 10
    ```
    
    Example - Pipeline failure:
    ```python
    pipeline = Pipeline()
    result = pipeline.filter(lambda x: x > 10).run(5)
    # result = None (5 is not > 10, so filter fails)
    ```
    
    Example - Complex pipeline:
    ```python
    pipeline = Pipeline()
    result = pipeline\
        .map(lambda x: x.split(','))\
        .multi(lambda p: p.map(str.strip).filter(lambda s: len(s) > 0))\
        .map(lambda items: len(items))\
        .run("apple, banana, , cherry")
    # Step 1: "apple, banana, , cherry" -> ["apple", " banana", " ", " cherry"]
    # Step 2: ["apple", " banana", " ", " cherry"] -> ["apple", "banana", "cherry"] (multi strips and filters)
    # Step 3: ["apple", "banana", "cherry"] -> 3
    # result = 3
    ```
    
    Thread safety:
    This method is NOT thread-safe. Each Pipeline instance should be used by only
    one thread at a time, or proper synchronization should be implemented.
    """
    result = None

    def success(data):
      nonlocal result
      result = data

    def failure():
      nonlocal result
      result = None

    self._transformation(input_value, success, failure)
    return result
