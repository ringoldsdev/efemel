"""
Example hooks file demonstrating before hook functionality.
Functions that start with 'before_' are automatically registered as before hooks.
"""


def before_output_filename(context):
  """Before hook that runs first - validates input."""
  input_path = context["input_file_path"]
  print(f"BEFORE: Validating input file: {input_path}")

  # Example validation
  if not input_path.exists():
    raise FileNotFoundError(f"Input file does not exist: {input_path}")

  print("BEFORE: Input file validation passed")


def output_filename(context):
  """Regular hook that runs after before hooks."""
  print(f"REGULAR: Processing output filename for {context['input_file_path']}")

  # Example: add a prefix to the output filename
  output_path = context["output_file_path"]
  new_name = f"processed_{output_path.name}"
  context["output_file_path"] = output_path.with_name(new_name)

  print(f"REGULAR: Added prefix -> {context['output_file_path']}")


def before_output_filename_logging(context):
  """Another before hook - logs the start of processing."""
  print(f"BEFORE: Starting to process {context['input_file_path']}")
  print(f"BEFORE: Original output path: {context['output_file_path']}")
