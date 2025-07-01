"""
Tests for the CLI module.
"""

import json
import os
import tempfile
from pathlib import Path

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


def test_process_command_with_test_inputs():
  """Test the process command with actual test input files."""
  runner = CliRunner()

  # Use the actual test input files
  test_inputs_dir = Path(__file__).parent / "inputs"

  with tempfile.TemporaryDirectory() as temp_dir:
    temp_output = Path(temp_dir)

    # Test with test_data.py
    result = runner.invoke(
      cli,
      [
        "process",
        str(test_inputs_dir / "test_data.py"),
        "--out",
        str(temp_output),
      ],
    )
    assert result.exit_code == 0
    assert "Successfully processed: 1 files" in result.output

    # Check that output file was created
    output_file = temp_output / "test_data.json"
    assert output_file.exists()

    # Check the content
    with open(output_file) as f:
      data = json.load(f)

    # Should contain the public dicts from test_data.py
    assert len(data) > 0  # Should have found some dictionaries


def test_process_command_entire_folder():
  """Test the process command with an entire folder."""
  runner = CliRunner()

  with runner.isolated_filesystem():
    # Create a test directory structure with multiple Python files
    os.makedirs("test_project/subdir", exist_ok=True)

    # Create first test file
    with open("test_project/config.py", "w") as f:
      f.write(
        """
# Configuration file
app_config = {
    "name": "test_app",
    "version": "2.0.0",
    "environment": "development"
}

database_config = {
    "host": "localhost",
    "port": 3306,
    "name": "test_db"
}

# Private config (should be ignored)
_internal_config = {"secret_key": "abc123"}
"""
      )

    # Create second test file in subdirectory
    with open("test_project/subdir/settings.py", "w") as f:
      f.write(
        """
# Settings file
user_settings = {
    "theme": "dark",
    "language": "en",
    "notifications": True
}

api_settings = {
    "timeout": 30,
    "retries": 3,
    "base_url": "https://api.example.com"
}

# Non-dict variable (should be ignored)
DEBUG_MODE = True
"""
      )

    # Create third test file with no dictionaries
    with open("test_project/utils.py", "w") as f:
      f.write(
        """
# Utility functions (no dictionaries)
def helper_function():
    return "helper"

class UtilityClass:
    pass

CONSTANT_VALUE = 42
"""
      )

    # Run the process command on the entire folder using glob pattern
    result = runner.invoke(
      cli, ["process", "test_project/**/*.py", "--out", "output", "--verbose"]
    )
    assert result.exit_code == 0, f"Command failed with output: {result.output}"
    assert "Successfully processed: 2 files" in result.output  # Only files with dicts

    # Debug: print what files were actually created
    print("\\nFiles created:")
    for root, _dirs, files in os.walk("output"):
      for file in files:
        print(f"  {os.path.join(root, file)}")

    # Check that output files were created for files with dictionaries
    # Should preserve directory structure
    expected_config = "output/test_project/config.json"
    expected_settings = "output/test_project/subdir/settings.json"
    expected_utils = "output/test_project/utils.json"

    assert os.path.exists(expected_config), f"Expected file {expected_config} not found"
    assert os.path.exists(expected_settings), (
      f"Expected file {expected_settings} not found"
    )
    # utils.py should not create an output file since it has no dictionaries
    assert not os.path.exists(expected_utils), f"Unexpected file {expected_utils} found"

    # Check the content of config.json
    with open(expected_config) as f:
      config_data = json.load(f)

    assert "app_config" in config_data
    assert "database_config" in config_data
    assert "_internal_config" not in config_data  # Should be filtered out
    assert config_data["app_config"]["name"] == "test_app"
    assert config_data["database_config"]["port"] == 3306

    # Check the content of settings.json
    with open(expected_settings) as f:
      settings_data = json.load(f)

    assert "user_settings" in settings_data
    assert "api_settings" in settings_data
    assert settings_data["user_settings"]["theme"] == "dark"
    assert settings_data["api_settings"]["timeout"] == 30
