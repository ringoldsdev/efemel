"""
Tests for the CLI module.
"""

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


def test_greet_command_default():
    """Test the greet command with default values."""
    runner = CliRunner()
    result = runner.invoke(cli, ["greet"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output


def test_greet_command_with_name():
    """Test the greet command with custom name."""
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output


def test_greet_command_with_count():
    """Test the greet command with multiple greetings."""
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "--count", "2"])
    assert result.exit_code == 0
    assert result.output.count("Hello, World!") == 2


def test_greet_command_loud():
    """Test the greet command with loud option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["greet", "--loud"])
    assert result.exit_code == 0
    assert "HELLO, WORLD!" in result.output


def test_echo_command():
    """Test the echo command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["echo", "test"])
    assert result.exit_code == 0
    assert "test" in result.output


def test_echo_command_reverse():
    """Test the echo command with reverse option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["echo", "hello", "--reverse"])
    assert result.exit_code == 0
    assert "olleh" in result.output


def test_echo_command_upper():
    """Test the echo command with upper option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["echo", "hello", "--upper"])
    assert result.exit_code == 0
    assert "HELLO" in result.output


def test_echo_command_lower():
    """Test the echo command with lower option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["echo", "HELLO", "--lower"])
    assert result.exit_code == 0
    assert "hello" in result.output


def test_config_show_command():
    """Test the config show command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    assert "All configuration values" in result.output


def test_config_show_command_with_key():
    """Test the config show command with specific key."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show", "--key", "test"])
    assert result.exit_code == 0
    assert "Configuration for 'test'" in result.output


def test_config_set_command():
    """Test the config set command."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["config", "set", "--key", "test", "--value", "value"])
    assert result.exit_code == 0
    assert "Setting test = value" in result.output


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
        result = runner.invoke(
            cli, ["process", "test_file.py", "--out", "output"])
        assert result.exit_code == 0
        assert "Successfully processed: 1 files" in result.output

        # Check that output file was created
        import json
        import os

        assert os.path.exists("output/test_file.json")

        # Check the content
        with open("output/test_file.json") as f:
            data = json.load(f)

        assert "test_dict" in data
        assert "config" in data
        assert "_private" not in data  # Should be filtered out
        assert data["test_dict"]["key"] == "value"
        assert data["config"]["app"] == "test"
