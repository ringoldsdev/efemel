def before_output_filename(context):
  """
  Hook that adds a 'test' subdirectory to the output path.
  """
  output_path = context["output_file_path"]

  # Add 'test' subdirectory to the output path
  new_output_path = "test" / output_path
  context["output_file_path"] = new_output_path

  print(f"Added test subdirectory: {output_path} -> {new_output_path}")


def output_filename(context):
  """
  Hook that adds a dummy timestamp to the filename before the suffix.
  """
  output_path = context["output_file_path"]

  # Generate a dummy timestamp
  timestamp = "20250705"

  # Split the filename into stem and suffix
  stem = output_path.stem
  suffix = output_path.suffix

  # Create new filename with timestamp
  new_filename = f"{stem}_{timestamp}{suffix}"
  new_output_path = output_path.with_name(new_filename)

  context["output_file_path"] = new_output_path

  print(f"Added timestamp: {output_path.name} -> {new_filename}")
