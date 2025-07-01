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
@click.option("--name", "-n", default="World", help="Name to greet")
@click.option("--count", "-c", default=1, help="Number of greetings")
@click.option("--loud", is_flag=True, help="Shout the greeting")
def greet(name, count, loud):
    """Greet someone with customizable options."""
    for _ in range(count):
        greeting = f"Hello, {name}!"
        if loud:
            greeting = greeting.upper()
        click.echo(greeting)


@cli.command()
@click.argument("text")
@click.option("--reverse", is_flag=True, help="Reverse the text")
@click.option("--upper", is_flag=True, help="Convert to uppercase")
@click.option("--lower", is_flag=True, help="Convert to lowercase")
def echo(text, reverse, upper, lower):
    """Echo text with optional transformations."""
    result = text

    if reverse:
        result = result[::-1]
    if upper:
        result = result.upper()
    elif lower:  # Only apply lower if upper is not set
        result = result.lower()

    click.echo(result)


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.option("--key", required=True, help="Configuration key")
@click.option("--value", required=True, help="Configuration value")
def set(key, value):
    """Set a configuration value."""
    click.echo(f"Setting {key} = {value}")
    # In a real app, this would save to a config file


@config.command()
@click.option("--key", help="Specific configuration key to show")
def show(key):
    """Show configuration values."""
    if key:
        click.echo(f"Configuration for '{key}': <not implemented>")
    else:
        click.echo("All configuration values: <not implemented>")


def main():
    """Main CLI function."""
    cli()


if __name__ == "__main__":
    main()
