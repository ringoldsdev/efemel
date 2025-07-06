# hooks_manager.py
import importlib.util
import os
import sys
from collections.abc import Callable
from typing import Any


class HooksManager:
  """Manages hook registration and execution."""

  def __init__(self):
    # Dictionary to store registered hook functions
    # Keys are hook names (strings), values are lists of functions
    self.hooks: dict[str, list[Callable]] = {}

  def load_user_file(self, file_path: str):
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
      for attr_name in module.__dict__:
        if attr_name.startswith("_"):  # Skip private/dunder methods
          continue
        attr_value = getattr(module, attr_name)

        if not callable(attr_value):
          continue

        # Check if it's a before hook
        if attr_name.startswith("before_"):
          # Extract the hook name by removing the "before_" prefix
          hook_name = attr_name[7:]  # Remove "before_" prefix
          self.add_before(hook_name, attr_value)
          print(f"Registered function '{attr_name}' as before hook for '{hook_name}'.")
        else:
          self.add(attr_name, attr_value)
          print(f"Registered function '{attr_name}' as hook.")

    except Exception as e:
      print(f"Error loading hooks from {file_path}: {e}")

  def call(self, hook_name: str, context: dict[str, Any], return_params: list[str]) -> dict[str, Any] | tuple[Any, ...]:
    """
    Calls all registered hook functions for a given hook name in sequence.
    Each hook function can mutate the context dictionary in place.

    Args:
      hook_name: Name of the hook to call
      context: Dictionary containing all data that the hooks can read/modify
      return_params: List of parameter names to return. If None, returns the full context.
                    If provided, returns a tuple of the specified parameters in order.

    Returns:
      The context dictionary (if return_params is None) or a tuple of specified parameters
    """
    hook_funcs = self.hooks.get(hook_name, [])

    if not hook_funcs:
      # No hooks registered, return unmodified context or requested parameters
      if return_params is None:
        return context
      return tuple(context.get(param) for param in return_params)

    # Execute all hooks in sequence
    for hook_func in hook_funcs:
      try:
        hook_func(context)
      except Exception as e:
        print(f"Error in hook '{hook_name}' (function: {getattr(hook_func, '__name__', 'unknown')}): {e}")
        # Continue with other hooks even if one fails

    # Return requested parameters
    if return_params is None:
      return context
    return tuple(context.get(param) for param in return_params)

  def add(self, hook_name: str, hook_func: Callable) -> None:
    """
    Manually add a hook function to the registry.

    Args:
      hook_name: Name of the hook
      hook_func: Function to register for this hook
    """
    if not callable(hook_func):
      raise ValueError(f"Hook function must be callable, got {type(hook_func)}")

    if hook_name not in self.hooks:
      self.hooks[hook_name] = []

    self.hooks[hook_name].append(hook_func)

  def add_before(self, hook_name: str, hook_func: Callable) -> None:
    """
    Manually add a hook function to the beginning of the registry (before other hooks).

    Args:
      hook_name: Name of the hook
      hook_func: Function to register for this hook
    """
    if not callable(hook_func):
      raise ValueError(f"Hook function must be callable, got {type(hook_func)}")

    if hook_name not in self.hooks:
      self.hooks[hook_name] = []

    # Insert at the beginning of the list (before other hooks)
    self.hooks[hook_name].insert(0, hook_func)

  def remove(self, hook_name: str, hook_func: Callable | None = None) -> None:
    """
    Remove a hook function from the registry.

    Args:
      hook_name: Name of the hook
      hook_func: Specific function to remove. If None, removes all hooks for this name.
    """
    if hook_name not in self.hooks:
      return

    if hook_func is None:
      # Remove all hooks for this name
      del self.hooks[hook_name]
    else:
      # Remove specific function
      if hook_func in self.hooks[hook_name]:
        self.hooks[hook_name].remove(hook_func)
        # If no more hooks, remove the key
        if not self.hooks[hook_name]:
          del self.hooks[hook_name]

  def clear(self) -> None:
    """Clear all registered hooks."""
    self.hooks.clear()

  def list(self) -> dict[str, list[str]]:
    """
    List all registered hooks.

    Returns:
      Dictionary mapping hook names to lists of function names in execution order
    """
    return {
      hook_name: [getattr(func, "__name__", "unknown") for func in funcs] for hook_name, funcs in self.hooks.items()
    }

  def get_count(self, hook_name: str) -> int:
    """
    Get the number of functions registered for a specific hook.

    Args:
      hook_name: Name of the hook

    Returns:
      Number of functions registered for this hook
    """
    return len(self.hooks.get(hook_name, []))
