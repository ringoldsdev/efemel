"""
CLI entry point for efemel.
"""

import click

from .main import hello_world


@click.group()
@click.version_option(version=__import__("efemel").__version__, prog_name="efemel")
@click.pass_context
def cli(ctx):
  """Efemel CLI application."""
  # Ensure that ctx.obj exists and is a dict (in case `cli()` is called by scripts)
  ctx.ensure_object(dict)


@cli.command()
def hello():
  """Print hello world message."""
  click.echo(hello_world())


@cli.command()
def info():
  """Show package information."""
  version = __import__("efemel").__version__
  click.echo(f"efemel version: {version}")
  click.echo("A Python CLI application built with UV and Click")


@cli.command()
@click.argument("file_pattern")
@click.option("--out", "-o", required=True, help="Output directory for JSON files")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def process(file_pattern, out, verbose):
  """Process Python files and extract public dictionary variables to JSON.

  FILE_PATTERN: Glob pattern to match Python files (e.g., "**/*.py")
  """
  import importlib.util
  import json
  import sys
  from glob import glob
  from pathlib import Path

  output_dir = Path(out)
  output_dir.mkdir(parents=True, exist_ok=True)

  if verbose:
    click.echo(f"Searching for files matching: {file_pattern}")
    click.echo(f"Output directory: {output_dir.absolute()}")

  # Find matching files
  matching_files = glob(file_pattern, recursive=True)
  python_files = [f for f in matching_files if f.endswith(".py")]

  if not python_files:
    click.echo(f"No Python files found matching pattern: {file_pattern}")
    return

  if verbose:
    click.echo(f"Found {len(python_files)} Python files to process")

  processed_count = 0
  error_count = 0

  for file_path in python_files:
    try:
      if verbose:
        click.echo(f"\nProcessing: {file_path}")

      # Convert to Path object for easier manipulation
      py_file = Path(file_path)

      # Create output path maintaining directory structure
      # Remove .py extension and add .json
      relative_path = py_file.with_suffix(".json")
      output_file = output_dir / relative_path

      # Ensure output directory exists
      output_file.parent.mkdir(parents=True, exist_ok=True)

      # Load the module dynamically
      spec = importlib.util.spec_from_file_location("dynamic_module", py_file)
      if spec is None or spec.loader is None:
        if verbose:
          click.echo(f"  ⚠️  Could not create module spec for {file_path}")
        error_count += 1
        continue

      module = importlib.util.module_from_spec(spec)

      # Add to sys.modules temporarily to handle relative imports
      temp_module_name = f"temp_module_{processed_count}"
      sys.modules[temp_module_name] = module

      try:
        spec.loader.exec_module(module)
      except Exception as e:
        if verbose:
          click.echo(f"  ❌ Error executing module: {e}")
        error_count += 1
        continue
      finally:
        # Clean up sys.modules
        sys.modules.pop(temp_module_name, None)

      # Extract public dictionary variables
      public_dicts = {}

      for attr_name in dir(module):
        # Skip private/protected attributes (starting with _)
        if attr_name.startswith("_"):
          continue

        try:
          attr_value = getattr(module, attr_name)

          # Check if it's a dictionary
          if isinstance(attr_value, dict):
            public_dicts[attr_name] = attr_value
            if verbose:
              items_count = len(attr_value)
              click.echo(f"  📖 Found dict: {attr_name} ({items_count} items)")

        except Exception as e:
          if verbose:
            click.echo(f"  ⚠️  Could not access attribute {attr_name}: {e}")
          continue
      # Write to JSON file
      if public_dicts:
        try:
          with open(output_file, "w", encoding="utf-8") as f:
            json.dump(public_dicts, f, indent=2, ensure_ascii=False, default=str)

          if verbose:
            dict_count = len(public_dicts)
            click.echo(f"  ✅ Saved {dict_count} dict(s) to: {output_file}")

          processed_count += 1

        except Exception as e:
          click.echo(f"  ❌ Error writing JSON file {output_file}: {e}")
          error_count += 1
      else:
        if verbose:
          click.echo(f"  ℹ️  No public dictionaries found in {file_path}")

    except Exception as e:
      click.echo(f"❌ Error processing {file_path}: {e}")
      error_count += 1

  # Summary
  click.echo("\n📊 Processing complete:")
  click.echo(f"  ✅ Successfully processed: {processed_count} files")
  if error_count > 0:
    click.echo(f"  ❌ Errors encountered: {error_count} files")
  click.echo(f"  📁 Output directory: {output_dir.absolute()}")


def main():
  """Main CLI function."""
  cli()


if __name__ == "__main__":
  main()
