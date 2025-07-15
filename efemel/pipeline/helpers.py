from collections.abc import Callable
import inspect


def is_context_aware(func: Callable, min_params: int = 2) -> bool:
  """
  Checks if a function is "context-aware" by inspecting its signature.

  A function is considered context-aware if it accepts a minimum number
  of positional arguments.

  - For standard maps/filters: `min_params=2` (e.g., `(value, context)`)
  - For reduce functions: `min_params=3` (e.g., `(accumulator, value, context)`)

  Args:
      func: The function or callable to inspect.
      min_params: The minimum number of arguments required for the
                  function to be considered context-aware.

  Returns:
      True if the function accepts the minimum number of arguments,
      False otherwise.
  """
  try:
    # Get the function's signature.
    sig = inspect.signature(func)

    # Filter for parameters that can be passed by position.
    params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]

    # Check if the function meets the minimum parameter count.
    return len(params) >= min_params

  except (ValueError, TypeError):
    # This handles built-ins or other non-inspectable callables,
    # which we assume are not context-aware.
    return False


def create_context_aware_function(func: Callable) -> Callable:
  """
  Normalizes a user-provided function to always accept a context argument.
  It no longer closes over `self.context`.
  """
  try:
    sig = inspect.signature(func)
    params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    # If the function already takes 2+ args, we assume it's context-aware.
    if len(params) >= 2:
      return func  # type: ignore
  except (ValueError, TypeError):
    # This handles built-ins or other non-inspectable callables.
    pass
  # If the function takes only one argument, we adapt it to accept a context that it will ignore.
  return lambda value, ctx: func(value)  # type: ignore
