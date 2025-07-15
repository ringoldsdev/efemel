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


def get_function_param_count(func: Callable[..., Any]) -> int:
  """
  Returns the number of parameters a function accepts, excluding `self` or `cls`.
  This is useful for determining if a function is context-aware.
  """
  try:
    sig = inspect.signature(func)
    params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    return len(params)
  except (ValueError, TypeError):
    return 0


def is_context_aware(func: Callable[..., Any]) -> TypeGuard[ContextAwareCallable]:
  """
  Checks if a function is "context-aware" by inspecting its signature.

  This function uses a TypeGuard, allowing Mypy to narrow the type of
  the checked function in conditional blocks.
  """
  return get_function_param_count(func) >= 2


def is_context_aware_reduce(func: Callable[..., Any]) -> TypeGuard[ContextAwareReduceCallable]:
  """
  Checks if a function is "context-aware" by inspecting its signature.

  This function uses a TypeGuard, allowing Mypy to narrow the type of
  the checked function in conditional blocks.
  """
  return get_function_param_count(func) >= 3
