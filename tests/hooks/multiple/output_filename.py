def _output_filename(context, value):
  """
  Hook that adds a dummy timestamp to the filename before the suffix.
  """
  output_path = context["output_file_path"]

  # Split the filename into stem and suffix
  stem = output_path.stem
  suffix = output_path.suffix

  # Create new filename with timestamp
  new_filename = f"{stem}_{value}{suffix}"
  new_output_path = output_path.with_name(new_filename)

  context["output_file_path"] = new_output_path

  print(f"Added timestamp: {output_path.name} -> {new_filename}")


def output_filename_1(context):
  return _output_filename(context, "1")


def output_filename_2(context):
  return _output_filename(context, "2")


def output_filename_3(context):
  return _output_filename(context, "3")
