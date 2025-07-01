import json


class JSONTransformer:
  """
  Transformer to convert Python files to JSON format.
  """

  suffix = ".json"

  def transform(self, data: dict | None) -> str:
    """
    Convert a dictionary to a JSON string.

    :param data: Dictionary to convert.
    :return: JSON string representation of the dictionary.
    """
    return json.dumps(data if data else {}, indent=2)
