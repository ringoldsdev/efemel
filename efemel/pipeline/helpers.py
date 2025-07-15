from collections.abc import Callable
import inspect


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
