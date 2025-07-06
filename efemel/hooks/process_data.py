from efemel.helpers import is_json_serializable


def drop_non_json_serializable(context):
  """
  Filter out values that are not JSON serializable from the data.

  Args:
      context: Hook context containing 'data' key with the extracted module data
  """
  data = context.get("data", {})

  def is_serializable_recursive(obj):
    """Recursively check if an object is JSON serializable."""
    match obj:
      # Fast path for JSON primitives
      case None | bool() | int() | float() | str():
        return True
      case list() | tuple():
        # Recursively check all items in the sequence
        return all(is_serializable_recursive(item) for item in obj)
      case dict():
        # Recursively check all keys and values in the dictionary
        return all(isinstance(key, str) and is_serializable_recursive(value) for key, value in obj.items())
      # Catchall for any other types - use expensive check
      case _:
        return is_json_serializable(obj)

  # Filter out non-JSON serializable values
  filtered_data = {}
  for attr_name, attr_value in data.items():
    if is_serializable_recursive(attr_value):
      filtered_data[attr_name] = attr_value

  context["data"] = filtered_data


def skip_private_properties(context):
  """
  Filter out private properties (those starting with underscore) from the data.

  Args:
      context: Hook context containing 'data' key with the extracted module data
  """
  data = context.get("data", {})

  # Filter out private properties (starting with underscore)
  filtered_data = {}
  for attr_name, attr_value in data.items():
    if not attr_name.startswith("_"):
      filtered_data[attr_name] = attr_value

  context["data"] = filtered_data


def pick_data(keys):
  """Pick specific keys from the processed python file."""

  def _pick(context):
    if not keys:
      return
    context["data"] = {key: value for key, value in context["data"].items() if key in keys}

  return _pick


def unwrap_data(keys):
  """Extracts specific values from the processed data dictionary, merges them."""

  def _unwrap(context):
    if not keys:
      return

    merged = {}

    for key in keys:
      if key not in context["data"]:
        continue

      value = context["data"][key]

      if isinstance(value, dict):
        merged.update(value)

    context["data"] = merged

  return _unwrap
