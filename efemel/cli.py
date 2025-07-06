import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click

from efemel.hooks.output_filename import ensure_output_path, flatten_output_path
from efemel.hooks_manager import hooks_manager
from efemel.process import process_py_file
from efemel.readers.local import LocalReader
from efemel.transformers.json import JSONTransformer
from efemel.writers.local import LocalWriter

DEFAULT_WORKERS = os.cpu_count() or 1


@click.group()
@click.version_option(version=__import__("efemel").__version__, prog_name="efemel")
@click.pass_context
def cli(ctx):
  """Efemel CLI application."""
  # Ensure that ctx.obj exists and is a dict (in case `cli()` is called by scripts)
  ctx.ensure_object(dict)


@cli.command()
def info():
  """Show package information."""
  version = __import__("efemel").__version__
  click.echo(f"efemel version: {version}")
  click.echo("A Python CLI application built with UV and Click")


@cli.command()
@click.argument("file_pattern")
@click.option("--out", "-o", required=True, help="Output directory for JSON files")
@click.option("--flatten", "-f", is_flag=True, default=False, help="Flatten the output file name")
@click.option("--env", "-e", help="Environment for processing (default: none)")
@click.option("--cwd", "-c", help="Working directory to search for files (default: current)")
@click.option(
  "--workers",
  "-w",
  default=DEFAULT_WORKERS,
  help=f"Number of parallel workers (default: {DEFAULT_WORKERS})",
)
@click.option(
  "--hooks-file",
  "-h",
  type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
  help="Path to a Python file containing user-defined hooks.",
)
def process(file_pattern, out, flatten, cwd, env, workers, hooks_file):
  """Process Python files and extract public dictionary variables to JSON.

  FILE_PATTERN: Glob pattern to match Python files (e.g., "**/*.py")
  """

  reader = LocalReader(cwd)
  transformer = JSONTransformer()
  writer = LocalWriter(out, reader.original_cwd)

  if flatten:
    # Add the flatten_output_path hook to the hooks manager
    hooks_manager.add("output_filename", flatten_output_path)

  # Load user-defined hooks if a file is specified
  if hooks_file:
    hooks_manager.load_user_file(hooks_file)
    click.echo(f"User hooks loaded from: {hooks_file}")

  hooks_manager.add("output_filename", ensure_output_path)

  # Collect all files to process
  files_to_process = list(reader.read(file_pattern))

  if not files_to_process:
    click.echo("No files found matching the pattern.")
    return

  def process_single_file(file_path: Path, cwd: Path):  # Added type hint for clarity
    """Process a single file and return results."""
    try:
      # Always create output file, even if no dictionaries found
      public_dicts = process_py_file(cwd / file_path, env) or {}
      transformed_data = transformer.transform(public_dicts)

      # Original proposed output filename (as a Path object for consistency)
      proposed_output_path = file_path.with_suffix(transformer.suffix)

      (output_file_path,) = hooks_manager.call(
        "output_filename",
        {
          "input_file_path": file_path,
          "output_file_path": proposed_output_path,
          "output_dir": writer.output_dir,
          "env": env,
        },
        return_params=["output_file_path"],
      )

      output_file = writer.write(transformed_data, output_file_path)

      return file_path, output_file, f"Processed: {cwd / file_path} → {output_file}"

    except Exception as e:
      # Ensure the exception message is clear about which file caused the error
      raise Exception(f"Error processing {file_path}: {str(e)}") from e

  # Process files in parallel
  click.echo(f"Processing {len(files_to_process)} files with {workers} workers...")

  with ThreadPoolExecutor(max_workers=workers) as executor:
    # Submit all tasks
    future_to_file = {
      executor.submit(process_single_file, file_path, reader.cwd_path): file_path for file_path in files_to_process
    }
    # Process completed tasks as they finish
    processed_count = 0
    for future in as_completed(future_to_file):
      try:
        file_path, output_file, message = future.result()
        click.echo(message)
        if output_file:
          processed_count += 1
      except Exception as e:
        click.echo(f"❌ {e}")  # Print errors from individual file processing

  click.echo(f"✅ Completed processing {processed_count}/{len(files_to_process)} files.")


def main():
  """Main CLI function."""
  cli()


if __name__ == "__main__":
  main()
