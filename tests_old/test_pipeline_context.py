"""
Test Pipeline global context functionality.

This module contains tests for Pipeline global context operations
including context propagation and sharing between operations.
"""

from efemel.pipeline import Pipeline


class TestPipelineContext:
  """Test Pipeline global context functionality."""

  def test_map_sets_context_value_propagated_to_all_items(self):
    """Test that when map function sets a value in context once, it gets passed to all items."""
    pipeline = Pipeline([1, 2, 3, 4, 5])

    context_access_count = 0

    def set_context_once(value, context):
      nonlocal context_access_count
      context_access_count += 1

      # Set a value in context only on the first call
      if context_access_count == 1:
        context["shared_value"] = "set_by_first_item"

      # All items should be able to access the shared value
      shared = context.get("shared_value", "not_found")
      return f"{value}_{shared}"

    result = pipeline.map(set_context_once).to_list()

    # Verify that all items got access to the shared value
    expected = [
      "1_set_by_first_item",
      "2_set_by_first_item",
      "3_set_by_first_item",
      "4_set_by_first_item",
      "5_set_by_first_item",
    ]

    assert result == expected

    # Verify the function was called for each item
    assert context_access_count == 5

  def test_concurrent_vs_sequential_context(self):
    """Test that concurrent and sequential processing produce the same results."""
    data = list(range(20))

    def transform_pipeline(p):
      return p.map(lambda x: x * 3).filter(lambda x: x % 2 == 0)

    # Sequential
    sequential_result = Pipeline().apply(transform_pipeline).to_list(data)

    # Concurrent
    concurrent_result = list(Pipeline(5).concurrent(data, pipeline=transform_pipeline, max_workers=3))

    assert sequential_result == concurrent_result

  def test_context_modifications_merged_in_concurrent_operations(self):
    """Test that context modifications in concurrent processing are properly merged back."""
    data = list(range(20))

    def context_modifying_pipeline(p):
      """Pipeline that modifies context during processing."""

      def modify_context(value, context):
        # Modify context - these changes should be merged back
        if "processed_values" not in context:
          context["processed_values"] = []
        context["processed_values"].append(value)
        return value * 2

      return p.map(modify_context)

    pipeline = Pipeline(5)
    result = list(pipeline.concurrent(data, pipeline=context_modifying_pipeline, max_workers=2))

    # Verify results are correct
    expected = [x * 2 for x in data]
    assert result == expected

    # Context modifications should be merged back from all threads
    # Each thread processes its chunk and adds values to context
    assert "processed_values" in pipeline.context
    assert len(pipeline.context["processed_values"]) > 0
    # Should have all processed values (order may vary due to concurrency)
    assert set(pipeline.context["processed_values"]) == set(data)
    assert not pipeline.context["has_errors"]
