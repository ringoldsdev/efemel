import importlib.util
import sys
from datetime import datetime
from pathlib import Path


def process_py_file(input: Path):
  spec = importlib.util.spec_from_file_location("dynamic_module", input)

  if spec is None or spec.loader is None:
    raise Exception("Could not create module spec for {input}")

  module = importlib.util.module_from_spec(spec)

  # Add to sys.modules temporarily to handle relative imports
  temp_module_name = f"temp_module_{int(datetime.now().timestamp())}"
  sys.modules[temp_module_name] = module

  spec.loader.exec_module(module)

  sys.modules.pop(temp_module_name, None)

  # Extract public dictionary variables
  public_dicts = {}

  for attr_name in dir(module):
    # Skip private/protected attributes (starting with _)
    if attr_name.startswith("_"):
      continue

    attr_value = getattr(module, attr_name)

    match attr_value:
      case dict():
        public_dicts[attr_name] = attr_value

  return public_dicts if public_dicts else None
