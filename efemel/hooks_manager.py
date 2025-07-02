# hooks_manager.py
import importlib.util
import os
import sys
from collections.abc import Callable
from typing import Any

# Global dictionary to store registered hook functions
# Keys are hook names (strings), values are lists of functions
# This will now be populated directly from the user's 'hooks' dictionary
HOOKS: dict[str, list[Callable]] = {}


def load_user_hooks_file(file_path: str):
  """
  Dynamically imports a Python module from a given file path
  and registers hooks defined in a 'hooks' dictionary within that module.
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
    sys.modules[module_name] = module  # Add to sys.modules for standard import compatibility
    print(f"Successfully loaded hooks module: {module_name} from {file_path}")

    # Look for a 'hooks' dictionary in the loaded module
    if hasattr(module, "hooks") and isinstance(module.hooks, dict):
      for hook_name, hook_funcs in module.hooks.items():
        if isinstance(hook_funcs, list):
          # Ensure all items in the list are callable
          valid_funcs = [f for f in hook_funcs if callable(f)]
          if len(valid_funcs) != len(hook_funcs):
            print(f"Warning: Some items in hook '{hook_name}' are not callable and will be ignored.")
          if hook_name not in HOOKS:
            HOOKS[hook_name] = []
          HOOKS[hook_name].extend(valid_funcs)
          print(f"Registered {len(valid_funcs)} functions for hook '{hook_name}' from user file.")
        else:
          print(f"Warning: Value for hook '{hook_name}' in user_hooks.py is not a list of functions. Ignoring.")
    else:
      print(f"Warning: No 'hooks' dictionary found in '{file_path}'. No hooks registered.")

  except Exception as e:
    print(f"Error loading hooks from {file_path}: {e}")


def call_hook(hook_name: str, *args, **kwargs) -> Any:
  """
  Invokes a chain of registered hook functions for a given hook.
  Each hook function receives a 'next_hook' callable as its last argument.
  The *args and **kwargs are the initial arguments for the first hook in the chain.
  """
  hook_funcs = HOOKS.get(
    hook_name,
  )

  # If no hooks are registered, return the first argument (or None if no args)
  # This ensures the original value is passed through if no hooks are active.
  if not hook_funcs:
    return args[0] if args else None

  # Create an iterator for the hook functions to manage the chain
  hook_iterator = iter(hook_funcs)

  def _next_callable(*next_args, **next_kwargs) -> Any:
    """
    This function represents the 'next' step in the middleware chain.
    It calls the next hook in the sequence or returns the first argument
    from next_args if there are no more hooks.
    """
    try:
      next_func = next(hook_iterator)
      # Pass the arguments received by _next_callable to the next hook,
      # along with _next_callable itself as the 'next_hook' argument.
      return next_func(*next_args, **next_kwargs, next_hook=_next_callable)
    except StopIteration:
      # No more hooks in the chain, return the first argument passed to next_callable
      return next_args[0] if next_args else None
    except Exception as e:
      # Log errors in hooks to prevent a single plugin from crashing the application
      print(f"Error in hook chain for '{hook_name}' (hook: {getattr(next_func, '__name__', 'unknown')}): {e}")
      # If an error occurs, stop the chain and return the last valid value
      return next_args[0] if next_args else None  # Return the value before the error

  # Start the chain by calling the first hook
  # The first hook receives the initial *args and **kwargs,
  # and _next_callable as its 'next_hook' argument.
  try:
    first_hook = next(hook_iterator)
    return first_hook(*args, **kwargs, next_hook=_next_callable)
  except StopIteration:
    # This case should ideally not happen if hook_funcs is not empty,
    # but handles the edge case where the list is empty after all.
    return args[0] if args else None
  except Exception as e:
    print(f"Error starting hook chain for '{hook_name}' (hook: {getattr(first_hook, '__name__', 'unknown')}): {e}")
    return args[0] if args else None
