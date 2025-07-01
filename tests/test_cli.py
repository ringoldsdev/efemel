import json
import os
import shutil
from pathlib import Path

from click.testing import CliRunner

from efemel.cli import cli


def test_process_command():
  """Test the process command with a single file."""
  runner = CliRunner()
  test_inputs_dir = Path(__file__).parent / "inputs"

  with runner.isolated_filesystem():
    # Copy test file to isolated filesystem
    shutil.copy(test_inputs_dir / "simple_test.py", "test_file.py")

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
  test_inputs_dir = Path(__file__).parent / "inputs"

  with runner.isolated_filesystem():
    # Copy test file to isolated filesystem
    shutil.copy(test_inputs_dir / "test_data.py", "test_data.py")

    # Run the process command
    result = runner.invoke(cli, ["process", "test_data.py", "--out", "output"])
    assert result.exit_code == 0
    assert "Successfully processed: 1 files" in result.output

    # Check that output file was created
    output_file = Path("output/test_data.json")
    assert output_file.exists()

    # Check the content
    with open(output_file) as f:
      data = json.load(f)

    # Should contain the public dicts from test_data.py
    assert len(data) > 0  # Should have found some dictionaries
    assert "config" in data
    assert "settings" in data
    assert "user_data" in data


def test_process_command_entire_folder():
  """Test the process command with an entire folder."""
  runner = CliRunner()
  test_inputs_dir = Path(__file__).parent / "inputs"

  with runner.isolated_filesystem():
    # Copy the entire test_dir structure to isolated filesystem
    shutil.copytree(test_inputs_dir / "test_dir", "test_project")

    # Run the process command on the entire folder using glob pattern
    result = runner.invoke(
      cli, ["process", "test_project/**/*.py", "--out", "output", "--verbose"]
    )
    assert result.exit_code == 0, f"Command failed with output: {result.output}"
    # Should process files with dictionaries (config.py and nested.py)
    # utils.py has no dictionaries so won't be processed
    assert "Successfully processed: 2 files" in result.output

    # Check that output files were created for files with dictionaries
    # Should preserve directory structure
    expected_config = "output/test_project/config.json"
    expected_nested = "output/test_project/subdir/nested.json"
    expected_utils = "output/test_project/utils.json"

    assert os.path.exists(expected_config), f"Expected file {expected_config} not found"
    assert os.path.exists(expected_nested), f"Expected file {expected_nested} not found"
    # utils.py should not create an output file since it has no dictionaries
    assert not os.path.exists(expected_utils), f"Unexpected file {expected_utils} found"

    # Check the content of config.json
    with open(expected_config) as f:
      config_data = json.load(f)

    assert "app_config" in config_data
    assert "database_config" in config_data
    assert "_internal_config" not in config_data  # Should be filtered out
    assert config_data["app_config"]["app_name"] == "my_app"
    assert config_data["database_config"]["pool_size"] == 10

    # Check the content of nested.json
    with open(expected_nested) as f:
      nested_data = json.load(f)

    assert "nested_data" in nested_data
    assert "metadata" in nested_data
    assert nested_data["nested_data"]["level"] == "deep"
    assert nested_data["metadata"]["created_by"] == "test"
