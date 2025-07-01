import importlib.util
import sys
from pathlib import Path


def process_py_file(input_path: Path):
  # Determine the parent directory to simulate a package
  module_dir = input_path.parent
  module_name = input_path.stem  # The file name without .py

  # Temporarily add the module's directory to sys.path
  # This allows Python to find other modules in the same "package"
  original_sys_path = sys.path[:]
  if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))

  spec = importlib.util.spec_from_file_location(module_name, input_path)

  if spec is None or spec.loader is None:
    # Revert sys.path before raising
    sys.path = original_sys_path
    raise Exception(f"Could not create module spec for {input_path}")

  module = importlib.util.module_from_spec(spec)

  # Sets `__package__` to the module's name to enable simple relative
  # imports (e.g., `from . import sibling_module`).
  # This is necessary so that relative imports within the loaded file
  # work as if it is part of a package.
  module.__package__ = module_name

  original_module_in_sys = sys.modules.get(module_name)
  sys.modules[module_name] = module

  try:
    spec.loader.exec_module(module)
  finally:
    # Clean up sys.modules and sys.path
    if original_module_in_sys is None:
      sys.modules.pop(module_name, None)
    else:
      sys.modules[module_name] = original_module_in_sys
    sys.path = original_sys_path

  # Extract public dictionary variables
  public_dicts = {}

  for attr_name in dir(module):
    if attr_name.startswith("_"):
      continue

    attr_value = getattr(module, attr_name)

    if isinstance(attr_value, dict):  # Use isinstance for type checking
      public_dicts[attr_name] = attr_value

  return public_dicts if public_dicts else None
