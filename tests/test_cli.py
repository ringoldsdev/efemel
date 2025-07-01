"""
Tests for the CLI module.
"""

import json
import os

from click.testing import CliRunner

from efemel.cli import cli


def test_cli_help():
    """Test the CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Efemel CLI application" in result.output


def test_cli_version():
    """Test the CLI version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "efemel, version" in result.output


def test_hello_command():
    """Test the hello command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0
    assert "Hello, World from efemel!" in result.output


def test_info_command():
    """Test the info command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["info"])
    assert result.exit_code == 0
    assert "efemel version:" in result.output
    assert "Python CLI application" in result.output


def test_process_command():
    """Test the process command."""
    runner = CliRunner()

    # Create a temporary test file
    with runner.isolated_filesystem():
        # Create test Python file
        with open("test_file.py", "w") as f:
            f.write(
                """
test_dict = {"key": "value", "number": 42}
config = {"app": "test", "version": "1.0"}
_private = {"secret": "hidden"}
not_a_dict = "string value"
"""
            )

        # Run the process command
        result = runner.invoke(cli, ["process", "test_file.py", "--out", "output"])
        assert result.exit_code == 0
        assert "Successfully processed: 1 files" in result.output

        # Check that output file was created
        assert os.path.exists("output/test_file.json")

        # Check the content
        with open("output/test_file.json") as f:
            data = json.load(f)

        assert "test_dict" in data
        assert "config" in data
        assert "_private" not in data  # Should be filtered out
        assert data["test_dict"]["key"] == "value"
        assert data["config"]["app"] == "test"
