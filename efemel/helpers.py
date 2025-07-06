import json


def is_json_serializable(obj):
  """Check if an object is JSON serializable."""
  try:
    json.dumps(obj)
    return True
  except (TypeError, ValueError):
    return False
