from collections.abc import Callable
import inspect
from typing import Any
from typing import TypeGuard


# --- Type Aliases ---
class PipelineContext(dict):
  """Generic, untyped context available to all pipeline operations."""

  pass


# Define the specific callables for clarity
ContextAwareCallable = Callable[[Any, PipelineContext], Any]
ContextAwareReduceCallable = Callable[[Any, Any, PipelineContext], Any]


def is_context_aware(func: Callable[..., Any]) -> TypeGuard[ContextAwareCallable]:
  """
  Checks if a function is "context-aware" by inspecting its signature.

  This function uses a TypeGuard, allowing Mypy to narrow the type of
  the checked function in conditional blocks.
  """
  return len(inspect.signature(func).parameters) > 1


def is_context_aware_reduce(func: Callable[..., Any]) -> TypeGuard[ContextAwareReduceCallable]:
  """
  Checks if a function is "context-aware" by inspecting its signature.

  This function uses a TypeGuard, allowing Mypy to narrow the type of
  the checked function in conditional blocks.
  """
  return len(inspect.signature(func).parameters) > 2
