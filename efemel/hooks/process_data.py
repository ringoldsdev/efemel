def pick_data(keys):
  """Pick specific keys from the processed python file."""

  def _pick(context):
    if not keys:
      return
    context["data"] = {key: value for key, value in context["data"].items() if key in keys}

  return _pick
