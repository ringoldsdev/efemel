"""
CLI entry point for efemel.
"""

import click

from efemel.process import process_py_file
from efemel.readers.local import LocalReader
from efemel.transformers.json import JSONTransformer
from efemel.writers.local import LocalWriter


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
@click.option(
  "--cwd", "-c", help="Working directory to search for files (default: current)"
)
def process(file_pattern, out, cwd):
  """Process Python files and extract public dictionary variables to JSON.

  FILE_PATTERN: Glob pattern to match Python files (e.g., "**/*.py")
  """

  reader = LocalReader(cwd)
  transformer = JSONTransformer()
  writer = LocalWriter(out, reader.original_cwd)

  for file_path in reader.read(file_pattern):
    public_dicts = process_py_file(file_path)

    if not public_dicts:
      click.echo(f"ℹ️  No public dictionaries found in {file_path}")

    transformed_data = transformer.transform(public_dicts)

    output_file = writer.write(
      transformed_data, file_path.with_suffix(transformer.suffix)
    )

    click.echo(f"Processed: {reader.cwd / file_path} → {output_file}")


def main():
  """Main CLI function."""
  cli()


if __name__ == "__main__":
  main()
