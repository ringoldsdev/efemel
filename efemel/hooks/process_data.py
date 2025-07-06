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
