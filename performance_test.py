#!/usr/bin/env python3
"""
Performance test for Pipeline class comparing different data processing approaches.

This test compares:
1. Pipeline class operations
2. Chained generator expressions with for/yield
3. Itertools map/filter chaining

Tests are run on 1 million items, 100 times each to get statistical data.
"""

import itertools
import statistics
import time
from itertools import islice

def generate_test_data(size: int = 1_000_000) -> list[int]:
  """Generate test data of specified size."""
  return range(size)


def generator_approach(data: list[int]) -> list[int]:
  """Process data using chained generator expressions."""

  def step1(items):
    """Filter even numbers."""
    for item in items:
      if item % 2 == 0:
        yield item

  def step2(items):
    """Double the numbers."""
    for item in items:
      yield item * 2

  def step3(items):
    """Filter > 100."""
    for item in items:
      if item > 100:
        yield item

  def step4(items):
    """Add 1."""
    for item in items:
      yield item + 1

  return list(step4(step3(step2(step1(data)))))


def builtin_map_filter_approach(data: list[int]) -> list[int]:
  """Process data using built-in map/filter chaining."""
  result = filter(lambda x: x % 2 == 0, data)  # Keep even numbers
  result = map(lambda x: x * 2, result)  # Double them
  result = filter(lambda x: x > 100, result)  # Keep only > 100
  result = map(lambda x: x + 1, result)  # Add 1
  return list(result)


def generator_expression_approach(data: list[int]) -> list[int]:
  """Process data using generator expressions."""
  result = (x for x in data if x % 2 == 0)  # Keep even numbers
  result = (x * 2 for x in result)  # Double them
  result = (x for x in result if x > 100)  # Keep only > 100
  result = (x + 1 for x in result)  # Add 1
  return list(result)


def list_comprehension_approach(data: list[int]) -> list[int]:
  """Process data using separate list comprehensions with intermediate lists."""
  # Create intermediate lists at each step to match other approaches
  step1 = [x for x in data if x % 2 == 0]  # Filter even numbers
  step2 = [x * 2 for x in step1]  # Double them
  step3 = [x for x in step2 if x > 100]  # Filter > 100
  step4 = [x + 1 for x in step3]  # Add 1
  return step4


def chunked_generator_listcomp_approach(data: list[int]) -> list[int]:
  """Process data using chunked generators with intermediate lists per chunk."""

  def chunk_generator(data, chunk_size=1000):
    """Generate chunks using a generator."""
    for i in range(0, len(data), chunk_size):
      yield data[i : i + chunk_size]

  # Process each chunk with intermediate lists and combine
  results = []
  for chunk in chunk_generator(data):
    # Create intermediate lists for each chunk
    step1 = [x for x in chunk if x % 2 == 0]  # Filter even numbers
    step2 = [x * 2 for x in step1]  # Double them
    step3 = [x for x in step2 if x > 100]  # Filter > 100
    step4 = [x + 1 for x in step3]  # Add 1
    results.extend(step4)
  return results


def mutated_chunked_generator_listcomp_approach(data: list[int]) -> list[int]:
  """Process data using chunked generators with intermediate lists per chunk."""

  def chunk_generator(data, chunk_size=1000):
    """Generate chunks using a generator."""
    while True:
        chunk = list(islice(data, chunk_size))
        if not chunk:
            return
        yield chunk

  # Process each chunk with intermediate lists and combine
  results = []
  for chunk in chunk_generator(data):
    # Create intermediate lists for each chunk
    step = [x for x in chunk if x % 2 == 0]  # Filter even numbers
    step = [x * 2 for x in step]  # Double them
    step = [x for x in step if x > 100]  # Filter > 100
    step = [x + 1 for x in step]  # Add 1
    results.extend(step)
  return results


class ChunkedPipeline:
  """
  A chunked pipeline that composes operations into a single function,
  inspired by a callback-chaining pattern.
  """

  def __init__(self, chunk_size=1000):
    """Initialize the pipeline with data and chunk size."""
    self.chunk_size = chunk_size
    # The transformer starts as an identity function that does nothing.
    self.transformer = lambda chunk: chunk

  def _chunk_generator(self, data):
    """Generate chunks from the data."""
    data_iter = iter(data)
    while True:
      chunk = list(itertools.islice(data_iter, self.chunk_size))
      if not chunk:
        break
      yield chunk

  def pipe(self, operation):
    """
    Composes the current transformer with a new chunk-wise operation.
    The operation should be a function that takes a list and returns a list.
    """
    # Capture the current transformer
    prev_transformer = self.transformer
    # Create a new transformer that first calls the old one, then the new operation
    self.transformer = lambda chunk: operation(prev_transformer(chunk))
    return self

  def filter(self, predicate):
    """Adds a filter operation by wrapping the current transformer in a list comprehension."""
    return self.pipe(lambda chunk: [x for x in chunk if predicate(x)])

  def map(self, func):
    """Adds a map operation by wrapping the current transformer in a list comprehension."""
    return self.pipe(lambda chunk: [func(x) for x in chunk])

  def run(self, data):
    """
    Execute the pipeline by calling the single, composed transformer on each chunk.
    """
    for chunk in self._chunk_generator(data):
      # The transformer is a single function that contains all the nested operations.
      yield from self.transformer(chunk)


PIPELINE = (
  ChunkedPipeline()
  .filter(lambda x: x % 2 == 0)  # Filter even numbers
  .map(lambda x: x * 2)  # Double them
  .filter(lambda x: x > 100)  # Filter > 100
  .map(lambda x: x + 1)
)


class ChunkedPipelineGenerator:
  """
  A chunked pipeline that composes operations into a single generator function,
  using lazy evaluation throughout the pipeline.
  """

  def __init__(self, chunk_size=1000):
    """Initialize the pipeline with chunk size."""
    self.chunk_size = chunk_size
    # The transformer starts as an identity generator that yields items as-is
    self.transformer = lambda chunk: (x for x in chunk)

  def _chunk_generator(self, data):
    """Generate chunks from the data."""
    data_iter = iter(data)
    while True:
      chunk = list(itertools.islice(data_iter, self.chunk_size))
      if not chunk:
        break
      yield chunk

  def pipe(self, operation):
    """
    Composes the current transformer with a new chunk-wise operation.
    The operation should be a function that takes a generator and returns a generator.
    """
    # Capture the current transformer
    prev_transformer = self.transformer
    # Create a new transformer that first calls the old one, then the new operation
    self.transformer = lambda chunk: operation(prev_transformer(chunk))
    return self

  def filter(self, predicate):
    """Adds a filter operation using generator expression."""
    return self.pipe(lambda gen: (x for x in gen if predicate(x)))

  def map(self, func):
    """Adds a map operation using generator expression."""
    return self.pipe(lambda gen: (func(x) for x in gen))

  def run(self, data):
    """
    Execute the pipeline by calling the single, composed transformer on each chunk.
    Yields items lazily from the generator pipeline.
    """
    for chunk in self._chunk_generator(data):
      # The transformer is a single function that contains all the nested generator operations
      yield from self.transformer(chunk)


# Create a generator-based pipeline instance
PIPELINE_GENERATOR = (
  ChunkedPipelineGenerator()
  .filter(lambda x: x % 2 == 0)  # Filter even numbers
  .map(lambda x: x * 2)  # Double them
  .filter(lambda x: x > 100)  # Filter > 100
  .map(lambda x: x + 1)
)


def chunked_pipeline_approach(data: list[int]) -> list[int]:
  """Process data using the ChunkedPipeline class."""
  return list(PIPELINE.run(data))


def chunked_pipeline_generator_approach(data: list[int]) -> list[int]:
  """Process data using the ChunkedPipelineGenerator class."""
  return list(PIPELINE_GENERATOR.run(data))


class ChunkedPipelineSimple:
  """
  A simple chunked pipeline that stores operations in a list and applies them sequentially
  using list comprehensions when executed.
  """

  def __init__(self, chunk_size=1000):
    """Initialize the pipeline with chunk size."""
    self.chunk_size = chunk_size
    self.operations = []

  def _chunk_generator(self, data):
    """Generate chunks from the data."""
    data_iter = iter(data)
    while True:
      chunk = list(itertools.islice(data_iter, self.chunk_size))
      if not chunk:
        break
      yield chunk

  def pipe(self, operation):
    """
    Add an operation to the pipeline.
    The operation should be a function that takes a list and returns a list.
    """
    self.operations.append(operation)
    return self

  def filter(self, predicate):
    """Add a filter operation to the pipeline."""
    return self.pipe(lambda chunk: [x for x in chunk if predicate(x)])

  def map(self, func):
    """Add a map operation to the pipeline."""
    return self.pipe(lambda chunk: [func(x) for x in chunk])

  def run(self, data):
    """
    Execute the pipeline by applying all operations sequentially to each chunk.
    """
    for chunk in self._chunk_generator(data):
      # Apply all operations sequentially to the chunk
      current_chunk = chunk
      for operation in self.operations:
        current_chunk = operation(current_chunk)

      # Yield each item from the processed chunk
      yield from current_chunk


# Create a simple pipeline instance
PIPELINE_SIMPLE = (
  ChunkedPipelineSimple()
  .filter(lambda x: x % 2 == 0)  # Filter even numbers
  .map(lambda x: x * 2)  # Double them
  .filter(lambda x: x > 100)  # Filter > 100
  .map(lambda x: x + 1)
)


def chunked_pipeline_simple_approach(data: list[int]) -> list[int]:
  """Process data using the ChunkedPipelineSimple class."""
  return list(PIPELINE_SIMPLE.run(data))

# Sentinel value to indicate that an item has been filtered out.
_SKIPPED = object()

class ChunkedPipelinePerItem:
    """
    A chunked pipeline that composes operations into a single function
    operating on individual items, inspired by a callback-chaining pattern
    to reduce the creation of intermediate lists.
    """

    def __init__(self, chunk_size=1000):
        """Initialize the pipeline with a specified chunk size."""
        self.chunk_size = chunk_size
        # The transformer starts as an identity function.
        self.transformer = lambda item: item

    def _chunk_generator(self, data):
        """A generator that yields chunks of data."""
        data_iter = iter(data)
        while True:
            chunk = list(itertools.islice(data_iter, self.chunk_size))
            if not chunk:
                break
            yield chunk

    def pipe(self, operation):
        """
        Composes the current transformer with a new item-wise operation.
        This internal method is the core of the pipeline's composition logic.
        """
        prev_transformer = self.transformer

        def new_transformer(item):
            # Apply the existing chain of transformations.
            processed_item = prev_transformer(item)
            
            # If a previous operation (like a filter) already skipped this item,
            # we bypass the new operation entirely.
            if processed_item is _SKIPPED:
                return _SKIPPED
            
            # Apply the new operation to the result of the previous ones.
            return operation(processed_item)

        self.transformer = new_transformer
        return self

    def filter(self, predicate):
        """
        Adds a filter operation to the pipeline.

        If the predicate returns `False`, the item is marked as skipped,
        and no further operations in the chain will be executed on it.
        """
        def filter_operation(item):
            return item if predicate(item) else _SKIPPED

        return self.pipe(filter_operation)

    def map(self, func):
        """Adds a map operation to transform an item."""
        return self.pipe(func)

    def run(self, data):
        """
        Executes the pipeline.

        The composed transformer function is applied to each item individually.
        Results are yielded only if they haven't been marked as skipped.
        """
        for chunk in self._chunk_generator(data):
            yield from [result for item in chunk if (result := self.transformer(item)) is not _SKIPPED]

PIPELINE_PER_ITEM = (
  ChunkedPipelinePerItem()
  .filter(lambda x: x % 2 == 0)  # Filter even numbers
  .map(lambda x: x * 2)  # Double them
  .filter(lambda x: x > 100)  # Filter > 100
  .map(lambda x: x + 1)
)

def chunked_pipeline_per_item_approach(data) -> list[int]:
  """Process data using the ChunkedPipelinePerItem class."""
  return list(PIPELINE_PER_ITEM.run(data))

def time_function(func, *args, **kwargs) -> float:
  """Time a function execution and return duration in seconds."""
  start_time = time.perf_counter()
  func(*args, **kwargs)
  end_time = time.perf_counter()
  return end_time - start_time


def run_performance_test():
  """Run comprehensive performance test."""
  print("🚀 Starting Performance Test")
  print("=" * 60)

  # Test configurations
  approaches = {
    # "Generators": generator_approach,
    # "Map/Filter": builtin_map_filter_approach,
    # "GeneratorExpression": generator_expression_approach,
    "ChunkedPipeline": chunked_pipeline_approach,
    "ChunkedPipelinePerItem": chunked_pipeline_per_item_approach,
    "ChunkedPipelineGenerator": chunked_pipeline_generator_approach,
    "ChunkedPipelineSimple": chunked_pipeline_simple_approach,
    "ListComprehension": list_comprehension_approach,
    "ChunkedGeneratorListComp": chunked_generator_listcomp_approach,
    # "MutatedChunkedGeneratorListComp": mutated_chunked_generator_listcomp_approach,
  }

  num_runs = 50
  results = {}

  for name, approach_func in approaches.items():
    print(f"\n🔄 Testing {name} approach ({num_runs} runs)...")
    times = []

    # Warm up
    approach_func(generate_test_data(1_000_000))

    # Actual timing runs
    for run in range(num_runs):
      print(f"  Run {run + 1}/{num_runs}")

      duration = time_function(approach_func, generate_test_data(1_000_000))
      times.append(duration)

    # Calculate statistics
    results[name] = {
      "times": times,
      "min": min(times),
      "max": max(times),
      "avg": statistics.mean(times),
      "p95": statistics.quantiles(times, n=20)[18],  # 95th percentile
      "p99": statistics.quantiles(times, n=100)[98],  # 99th percentile
      "median": statistics.median(times),
      "stdev": statistics.stdev(times) if len(times) > 1 else 0,
    }  # Print results
    print("\n" + "=" * 60)
    print("📈 PERFORMANCE RESULTS")
    print("=" * 60)

    # Header
    header = (
      f"{'Approach':<12} {'Min (s)':<10} {'Max (s)':<10} {'Avg (s)':<10} "
      f"{'P95 (s)':<10} {'P99 (s)':<10} {'Median (s)':<12} {'StdDev':<10}"
    )
    print(header)
    print("-" * 104)

  # Sort by average time
  sorted_results = sorted(results.items(), key=lambda x: x[1]["avg"])

  for name, stats in sorted_results:
    print(
      f"{name:<12} {stats['min']:<10.4f} {stats['max']:<10.4f} {stats['avg']:<10.4f} "
      f"{stats['p95']:<10.4f} {stats['p99']:<10.4f} {stats['median']:<12.4f} {stats['stdev']:<10.4f}"
    )

  # Relative performance
  print("\n" + "=" * 60)
  print("🏆 RELATIVE PERFORMANCE")
  print("=" * 60)

  baseline = sorted_results[0][1]["avg"]  # Fastest approach as baseline

  for name, stats in sorted_results:
    ratio = stats["avg"] / baseline
    percentage = (ratio - 1) * 100
    if ratio == 1.0:
      print(f"{name:<12} 1.00x (baseline)")
    else:
      print(f"{name:<12} {ratio:.2f}x ({percentage:+.1f}% slower)")

  # Verify correctness
  print("\n" + "=" * 60)
  print("✅ CORRECTNESS VERIFICATION")
  print("=" * 60)

  # Use smaller dataset for verification
  results_correctness = {}

  for name, approach_func in approaches.items():
    result = approach_func(generate_test_data(1_000))
    results_correctness[name] = result
    print(f"{name:<12} Result length: {len(result)}")

  # Check if all approaches produce the same result
  first_result = next(iter(results_correctness.values()))
  all_same = all(result == first_result for result in results_correctness.values())

  if all_same:
    print("✅ All approaches produce identical results")
    print(f"   Sample result (first 10): {first_result[:10]}")
  else:
    print("❌ Approaches produce different results!")
    for name, result in results_correctness.items():
      print(f"   {name}: {result[:10]} (length: {len(result)})")


def run_memory_test():
  """Run a quick memory efficiency comparison."""
  print("\n" + "=" * 60)
  print("💾 MEMORY EFFICIENCY TEST")
  print("=" * 60)

  import tracemalloc

  approaches = {
    # "Generators": generator_approach,
    # "MapFilter": builtin_map_filter_approach,
    # "GeneratorExpression": generator_expression_approach,
    "ChunkedPipeline": chunked_pipeline_approach,
    "ChunkedPipelinePerItem": chunked_pipeline_per_item_approach,
    "ChunkedPipelineGenerator": chunked_pipeline_generator_approach,
    "ChunkedPipelineSimple": chunked_pipeline_simple_approach,
    "ListComprehension": list_comprehension_approach,
    "ChunkedGeneratorListComp": chunked_generator_listcomp_approach,
    # "MutatedChunkedGeneratorListComp": mutated_chunked_generator_listcomp_approach,
  }

  for name, approach_func in approaches.items():
    tracemalloc.start()

    result = approach_func(generate_test_data(100_000))

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(
      f"{name:<12} Peak memory: {peak / 1024 / 1024:.2f} MB, "
      f"Current: {current / 1024 / 1024:.2f} MB, "
      f"Result length: {len(result)}"
    )


if __name__ == "__main__":
  try:
    run_performance_test()
    run_memory_test()
    print("\n🎉 ChunkedPipeline test completed successfully!")
  except KeyboardInterrupt:
    print("\n⚠️  Test interrupted by user")
  except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    raise
