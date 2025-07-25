from importlib.abc import MetaPathFinder
import importlib.util
from pathlib import Path
import sys


class EnvironmentModuleFinder(MetaPathFinder):
  def __init__(self, environment: str = "default"):
    self.environment = environment

  def find_spec(self, fullname, path, target=None):
    # Determine the base name of the module being imported
    # e.g., "example" from "example" or "my_package.example"
    base_name = fullname.split(".")[-1]

    # Determine the directory where the import is happening (if applicable)
    # For top-level imports, 'path' is None, and we assume current working directory or sys.path
    # For sub-package imports, 'path' will be a list of directories in the package's __path__
    search_dirs = [Path(".")]  # Default to current directory for top-level imports
    if path:  # If it's an import within a package
      search_dirs = [Path(p) for p in path]

    for s_dir in search_dirs:
      # Check for environment-specific file
      env_specific_file_path = s_dir / f"{base_name}.{self.environment}.py"
      if env_specific_file_path.is_file():
        # print(f"DEBUG: Found env-specific: {env_specific_file_path} for {fullname}") # For debugging
        return importlib.util.spec_from_file_location(fullname, env_specific_file_path)

      # If environment-specific doesn't exist, check for the default file
      default_file_path = s_dir / f"{base_name}.py"
      if default_file_path.is_file():
        # print(f"DEBUG: Found default: {default_file_path} for {fullname}") # For debugging
        return importlib.util.spec_from_file_location(fullname, default_file_path)

    # If no matching file found by our logic, let other finders handle it
    return None


def set_dynamic_import_environment(environment: str):
  """
  Sets up the custom import hook to prioritize environment-specific modules for
  subsequent 'import' statements made by any code after this is called.
  This should be called early in your application's lifecycle.
  """
  # Remove any existing EnvironmentModuleFinder to avoid duplicates
  sys.meta_path[:] = [finder for finder in sys.meta_path if not isinstance(finder, EnvironmentModuleFinder)]

  # Insert our custom finder at the beginning of sys.meta_path
  # This ensures it's checked before the default finders
  sys.meta_path.insert(0, EnvironmentModuleFinder(environment))


def process_py_file(input_path: Path, environment: str = "default", custom_params: dict = None):
  """
  This function processes a Python file *exactly as specified by input_path*.
  It does NOT apply environment-specific logic to the input_path itself.
  Any 'import' statements *within* the loaded file will be subject to
  the dynamic import environment set by `set_dynamic_import_environment`.

  Args:
    input_path: Path to the Python file to process
    environment: Environment name for dynamic imports
    custom_params: Dictionary of custom parameters to inject into the module
  """

  if custom_params is None:
    custom_params = {}

  set_dynamic_import_environment(environment)

  module_dir = input_path.parent
  module_name = input_path.stem  # The file name without .py

  # The file to load is ALWAYS the input_path provided.
  file_to_load = input_path

  # Ensure the directory of the file is in sys.path for relative imports
  original_sys_path = sys.path[:]
  if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))

  spec = importlib.util.spec_from_file_location(module_name, file_to_load)

  if spec is None or spec.loader is None:
    sys.path = original_sys_path
    raise Exception(f"Could not create module spec for {file_to_load}")

  module = importlib.util.module_from_spec(spec)

  # Sets `__package__` to the module's name to enable simple relative
  # imports (e.g., `from . import sibling_module`).
  # This is necessary so that relative imports within the loaded file
  # work as if it is part of a package.
  # A more robust __package__ would be module_dir.name if it's a true package,
  # but for single file loading, module_name works for simple relative imports.
  module.__package__ = module_name

  original_module_in_sys = sys.modules.get(module_name)
  sys.modules[module_name] = module

  # Inject custom parameters into the module's namespace
  # This makes them available as global variables in the processed script
  for param_name, param_value in custom_params.items():
    setattr(module, param_name, param_value)

  try:
    spec.loader.exec_module(module)
  except NameError as e:
    # Clean up sys.modules and sys.path before raising
    if original_module_in_sys is None:
      sys.modules.pop(module_name, None)
    else:
      sys.modules[module_name] = original_module_in_sys
    sys.path = original_sys_path

    # Extract parameter name from the NameError message
    error_msg = str(e)
    if "is not defined" in error_msg:
      param_name = error_msg.split("'")[1] if "'" in error_msg else "unknown"
      raise Exception(f"Missing parameter: {param_name}. Use --param {param_name}=value to pass parameters") from e
    else:
      raise Exception(f"Missing parameter: {error_msg}. Use --param to pass parameters") from e
  finally:
    # Clean up sys.modules and sys.path
    if original_module_in_sys is None:
      sys.modules.pop(module_name, None)
    else:
      sys.modules[module_name] = original_module_in_sys
    sys.path = original_sys_path

  # Extract all variables from module
  return module.__dict__
