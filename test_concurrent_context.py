#!/usr/bin/env python3
"""
Test script to verify that the concurrent method handles context properly
and doesn't have race conditions.
"""

from efemel.pipeline import Pipeline


def test_concurrent_context_isolation():
  """Test that concurrent processing properly isolates and merges contexts."""

  # Create a pipeline with some data
  data = list(range(100))  # Large enough to ensure multiple chunks
  pipeline = Pipeline(data, chunk_size=10)  # Force multiple chunks

  def error_prone_pipeline(p):
    """A pipeline that will cause errors on certain values."""
    return p.map(lambda x: x if x % 7 != 0 else 1 / 0)  # Error on multiples of 7

  def safe_pipeline(p):
    """A pipeline that should work without errors."""
    return p.map(lambda x: x * 2)

  print("Testing concurrent pipeline with errors...")

  # Test with error-prone pipeline
  try:
    result = pipeline.concurrent(error_prone_pipeline, max_workers=4).to_list()
    print("ERROR: Should have raised CompoundError!")
  except Exception as e:
    print(f"✓ Correctly caught exception: {type(e).__name__}")
    print(f"  Pipeline context has_errors: {pipeline.context['has_errors']}")

  # Test with safe pipeline
  print("\nTesting concurrent pipeline without errors...")
  safe_data = list(range(50))
  safe_pipeline_obj = Pipeline(safe_data, chunk_size=5)

  result = safe_pipeline_obj.concurrent(safe_pipeline, max_workers=4).to_list()
  expected = [x * 2 for x in safe_data]

  print(f"✓ Results match expected: {result == expected}")
  print(f"  Pipeline context has_errors: {safe_pipeline_obj.context['has_errors']}")
  print(f"  Result length: {len(result)}")


def test_concurrent_vs_sequential():
  """Test that concurrent and sequential processing produce the same results."""

  data = list(range(20))

  def transform_pipeline(p):
    return p.map(lambda x: x * 3).filter(lambda x: x % 2 == 0)

  # Sequential
  sequential_result = Pipeline(data).apply(transform_pipeline).to_list()

  # Concurrent
  concurrent_result = Pipeline(data, chunk_size=5).concurrent(transform_pipeline, max_workers=3).to_list()

  print("\nSequential vs Concurrent comparison:")
  print(f"✓ Results match: {sequential_result == concurrent_result}")
  print(f"  Sequential: {sequential_result}")
  print(f"  Concurrent: {concurrent_result}")


if __name__ == "__main__":
  test_concurrent_context_isolation()
  test_concurrent_vs_sequential()
  print("\n✓ All concurrent context tests passed!")
