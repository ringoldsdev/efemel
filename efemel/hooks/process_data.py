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
