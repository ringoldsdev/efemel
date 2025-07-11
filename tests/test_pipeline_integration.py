"""
Integration tests for Pipeline class.

This module contains end-to-end integration tests for complex
Pipeline operations and realistic data processing scenarios.
"""

from efemel.pipeline import Pipeline


class TestPipelineIntegration:
  """Integration tests for Pipeline class."""

  def test_data_processing_pipeline(self):
    """Test a realistic data processing pipeline."""
    # Simulate processing a list of user data
    users = [
      {"name": "Alice", "age": 30, "active": True},
      {"name": "Bob", "age": 25, "active": False},
      {"name": "Charlie", "age": 35, "active": True},
      {"name": "Diana", "age": 28, "active": True},
      {"name": "Eve", "age": 22, "active": False},
    ]

    pipeline = Pipeline(users)

    # Process: filter active users, extract names, convert to uppercase
    result = pipeline.filter(lambda user: user["active"]).map(lambda user: user["name"]).map(str.upper)

    assert result.to_list() == ["ALICE", "CHARLIE", "DIANA"]

  def test_number_processing_pipeline(self):
    """Test a number processing pipeline."""
    numbers = range(1, 21)  # 1 to 20

    pipeline = Pipeline(numbers)

    # Process: filter even numbers, square them, filter > 50, sum
    result = (
      pipeline.filter(lambda x: x % 2 == 0)  # [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
      .map(lambda x: x**2)  # [4, 16, 36, 64, 100, 144, 196, 256, 324, 400]
      .filter(lambda x: x > 50)  # [64, 100, 144, 196, 256, 324, 400]
      .reduce(lambda acc, x: acc + x, 0)
    )  # 1484

    assert result.first() == 1484

  def test_text_processing_pipeline(self):
    """Test a text processing pipeline."""
    text = "Hello world! This is a test. Python is amazing."
    words = text.split()

    pipeline = Pipeline(words)

    # Process: filter words > 3 chars, remove punctuation, lowercase, get unique
    result = (
      pipeline.filter(lambda word: len(word) > 3)
      .map(lambda word: word.strip(".,!"))
      .map(str.lower)
      .filter(lambda word: word not in ["this"])
    )  # Simple "unique" filter

    expected = ["hello", "world", "test", "python", "amazing"]
    assert result.to_list() == expected

  def test_nested_data_processing(self):
    """Test processing nested data structures."""
    data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    pipeline = Pipeline(data)

    # Flatten, filter odd numbers, square them
    result = (
      pipeline.flatten()  # [1, 2, 3, 4, 5, 6, 7, 8, 9]
      .filter(lambda x: x % 2 == 1)  # [1, 3, 5, 7, 9]
      .map(lambda x: x**2)
    )  # [1, 9, 25, 49, 81]

    assert result.to_list() == [1, 9, 25, 49, 81]
