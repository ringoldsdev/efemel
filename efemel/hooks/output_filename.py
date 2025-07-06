from pathlib import Path


def ensure_output_path(context):
  """Internal hook to ensure output path is a Path object."""
  output_path = context["output_file_path"]
  if not isinstance(output_path, Path):
    context["output_file_path"] = Path(output_path)


def flatten_output_path(context):
  """
  Internal hook to flatten the output path by concatenating subdirectories to the filename.

  Example:
    input/subdir1/subdir2/file.py -> subdir1_subdir2_file.json
    data/config/prod/settings.py -> data_config_prod_settings.json
  """
  input_path = context["input_file_path"]
  output_path = context["output_file_path"]
  output_dir = context["output_dir"]

  # Get the relative directory structure from the input path
  if len(input_path.parts) < 2:
    print(f"No flattening needed for: {input_path}")
    return

  # Get all directory parts except the filename
  dir_parts = input_path.parts[:-1]
  # Join directory parts with underscores
  flattened_dirs = "_".join(dir_parts)

  # Create new filename with directories first, then source filename
  input_stem = input_path.stem  # Use the source file stem
  output_suffix = output_path.suffix  # Keep the output file extension (e.g., .json)
  new_filename = f"{flattened_dirs}_{input_stem}{output_suffix}"

  # Place the flattened file directly in the root output directory
  context["output_file_path"] = Path(output_dir) / new_filename

  print(f"Flattened path: {input_path} -> {new_filename}")
