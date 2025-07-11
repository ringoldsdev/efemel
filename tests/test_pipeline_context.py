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
