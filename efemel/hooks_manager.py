# hooks_manager.py
import importlib.util
import os
import sys
from collections.abc import Callable
from typing import Any

# Global dictionary to store registered hook functions
# Keys are hook names (strings), values are single functions
HOOKS: dict[str, Callable] = {}


def load_user_hooks_file(file_path: str):
  """
  Dynamically imports a Python module from a given file path
  and registers all functions in that module as hooks.
  """
  if not os.path.exists(file_path):
    print(f"Error: Hooks file not found at '{file_path}'")
    return

  module_name = os.path.basename(file_path).replace(".py", "")

  spec = importlib.util.spec_from_file_location(module_name, file_path)
  if spec is None:
    print(f"Error: Could not find module specification for {file_path}")
    return
  if spec.loader is None:
    print(f"Error: No loader found for module specification at {file_path}")
    return

  module = importlib.util.module_from_spec(spec)
  try:
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    print(f"Successfully loaded hooks module: {module_name} from {file_path}")

    # Register all functions in the module as hooks
    for attr_name in dir(module):
      if not attr_name.startswith("_"):  # Skip private/dunder methods
        attr_value = getattr(module, attr_name)
        if callable(attr_value):
          HOOKS[attr_name] = attr_value
          print(f"Registered function '{attr_name}' as hook.")

  except Exception as e:
    print(f"Error loading hooks from {file_path}: {e}")


def call_hook(hook_name: str, context: dict[str, Any], return_params: list[str]) -> dict[str, Any] | tuple[Any, ...]:
  """
  Calls a registered hook function with the provided context.
  The hook function can mutate the context dictionary in place.

  Args:
    hook_name: Name of the hook to call
    context: Dictionary containing all data that the hook can read/modify
    return_params: List of parameter names to return. If None, returns the full context.
                  If provided, returns a tuple of the specified parameters in order.

  Returns:
    The context dictionary (if return_params is None) or a tuple of specified parameters
  """
  hook_func = HOOKS.get(hook_name)

  if not hook_func:
    # No hook registered, return unmodified context or requested parameters
    if return_params is None:
      return context
    return tuple(context.get(param) for param in return_params)

  try:
    hook_func(context)

    # Return tuple of requested parameters
    return tuple(context.get(param) for param in return_params)

  except Exception as e:
    print(f"Error in hook '{hook_name}' (function: {getattr(hook_func, '__name__', 'unknown')}): {e}")

    if return_params is None:
      return context
    return tuple(context.get(param) for param in return_params)
