"""
Test Pipeline catch functionality and CompoundError handling.

This module contains tests for Pipeline error handling including
catch operations, CompoundError formatting, and error propagation.
"""

import pytest

from efemel.pipeline import CompoundError
from efemel.pipeline import Pipeline


class TestPipelineCatch:
  """Test Pipeline catch functionality and CompoundError handling."""

  def test_catch_basic_error_handling(self):
    """Test basic catch functionality with error callback."""
    captured_errors = []

    def error_prone_pipeline(p):
      return p.map(lambda x: 10 / x if x != 0 else 1 / 0)

    def error_handler(error):
      captured_errors.append(error)

    pipeline = Pipeline([2, 0, 4, 0, 6])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(error_prone_pipeline, error_handler).to_list()

    # Should have captured 2 ZeroDivisionErrors
    assert len(captured_errors) == 2
    assert all(isinstance(e, ZeroDivisionError) for e in captured_errors)

    # CompoundError should also contain the same errors
    assert len(exc_info.value.errors) == 2
    assert all(isinstance(e, ZeroDivisionError) for e in exc_info.value.errors)

  def test_catch_with_successful_items(self):
    """Test catch with mix of successful and failed items."""
    error_logs = []

    def selective_error_pipeline(p):
      return p.map(lambda x: x * 2 if x != 3 else 1 / 0)

    def log_error(error):
      error_logs.append(f"Caught: {type(error).__name__}")

    pipeline = Pipeline([1, 2, 3, 4, 5])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(selective_error_pipeline, log_error).to_list()

    # Should have logged one error
    assert len(error_logs) == 1
    assert "ZeroDivisionError" in error_logs[0]

    # CompoundError should contain one error
    assert len(exc_info.value.errors) == 1

  def test_catch_with_reduce_operation(self):
    """Test catch with reduce operation that has errors."""
    errors_seen = []

    def error_prone_reduce_pipeline(p: Pipeline[int]):
      # First map some values to cause errors, then reduce
      return p.map(lambda x: x if x != 2 else 1 / 0).reduce(lambda acc, x: acc + x, 0)

    def collect_errors(error):
      errors_seen.append(error)

    pipeline = Pipeline([1, 2, 3, 4, 5])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(error_prone_reduce_pipeline, collect_errors).first()

    # Should have seen the error during catch
    assert len(errors_seen) == 1
    assert isinstance(errors_seen[0], ZeroDivisionError)

    # CompoundError should also have the error
    assert len(exc_info.value.errors) == 1

  def test_catch_multiple_operation_errors(self):
    """Test catch with multiple operations that can error."""
    all_errors = []

    def multi_error_pipeline(p: Pipeline[int]):
      return (
        p.map(lambda x: x / 2 if x != 4 else 1 / 0)  # Error on 4
        .filter(
          lambda x: x > 0 if x != 1 else 1 / 0
        )  # Error on 1 (after division = 0.5, but let's say error on result 1)
        .map(lambda x: x * 3 if x != 3 else 1 / 0)
      )  # Error on 3 (after division = 1.5, won't hit)

    def track_all_errors(error):
      all_errors.append(type(error).__name__)

    pipeline = Pipeline([2, 4, 6, 8])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(multi_error_pipeline, track_all_errors).to_list()

    # Should have tracked at least one error
    assert len(all_errors) >= 1
    assert len(exc_info.value.errors) >= 1

  def test_catch_with_no_errors(self):
    """Test catch when no errors occur."""
    error_handler_called = []

    def safe_pipeline(p):
      return p.map(lambda x: x * 2).filter(lambda x: x > 5)

    def should_not_be_called(error):
      error_handler_called.append(error)

    pipeline = Pipeline([1, 2, 3, 4, 5])
    result = pipeline.catch(safe_pipeline, should_not_be_called).to_list()

    # No errors, so handler should not be called
    assert len(error_handler_called) == 0
    # Should get successful results
    assert result == [6, 8, 10]

  def test_compound_error_formatting(self):
    """Test CompoundError message formatting."""

    def always_error(x):
      if x == 1:
        raise ValueError("First error")
      elif x == 2:
        raise TypeError("Second error")
      else:
        raise RuntimeError("Third error")

    pipeline = Pipeline([1, 2, 3])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.map(always_error).to_list()

    error_message = str(exc_info.value)

    # Check message contains error count
    assert "3 error(s) occurred in the pipeline" in error_message

    # Check individual error messages are included
    assert "ValueError: First error" in error_message
    assert "TypeError: Second error" in error_message
    assert "RuntimeError: Third error" in error_message

  def test_compound_error_with_single_error(self):
    """Test CompoundError with just one error."""

    def single_error(x):
      if x == 3:
        raise ValueError("Only error")
      return x * 2

    pipeline = Pipeline([1, 2, 3, 4])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.map(single_error).to_list()

    # Should have exactly one error
    assert len(exc_info.value.errors) == 1
    assert isinstance(exc_info.value.errors[0], ValueError)

    # Message should reflect single error
    error_message = str(exc_info.value)
    assert "1 error(s) occurred in the pipeline" in error_message
    assert "ValueError: Only error" in error_message

  def test_catch_with_chained_operations(self):
    """Test catch with complex chained operations."""
    logged_errors = []

    def complex_pipeline(p):
      return (
        p.filter(lambda x: x > 0 if x != 2 else 1 / 0)  # Error on 2
        .map(lambda x: x * 2 if x != 4 else 1 / 0)  # Error on 4
        .reduce(lambda acc, x: acc + x, 0)
      )

    def error_logger(error):
      logged_errors.append(f"Error: {error}")

    pipeline = Pipeline([1, 2, 3, 4, 5])

    with pytest.raises(CompoundError) as exc_info:
      pipeline.catch(complex_pipeline, error_logger).first()

    # Should have logged errors from the operations
    assert len(logged_errors) >= 1
    # CompoundError should also contain the errors
    assert len(exc_info.value.errors) >= 1

  def test_catch_error_handler_exception(self):
    """Test catch when error handler itself raises exception."""

    def error_pipeline(p):
      return p.map(lambda x: 1 / 0 if x == 2 else x)

    def failing_handler(error):
      raise RuntimeError("Handler failed!")

    pipeline = Pipeline([1, 2, 3])

    # Should still work despite handler failure
    with pytest.raises(CompoundError):
      # The failing handler should not stop the pipeline
      pipeline.catch(error_pipeline, failing_handler).to_list()
