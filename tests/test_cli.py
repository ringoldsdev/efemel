"""
Tests for the CLI module.
"""

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from efemel.cli import cli

# def test_cli_help():
#     """Test the CLI help command."""
#     runner = CliRunner()
#     result = runner.invoke(cli, ["--help"])
#     assert result.exit_code == 0
#     assert "Efemel CLI application" in result.output


# def test_cli_version():
#     """Test the CLI version command."""
#     runner = CliRunner()
#     result = runner.invoke(cli, ["--version"])
#     assert result.exit_code == 0
#     assert "efemel, version" in result.output


# def test_hello_command():
#     """Test the hello command."""
#     runner = CliRunner()
#     result = runner.invoke(cli, ["hello"])
#     assert result.exit_code == 0
#     assert "Hello, World from efemel!" in result.output


# def test_info_command():
#     """Test the info command."""
#     runner = CliRunner()
#     result = runner.invoke(cli, ["info"])
#     assert result.exit_code == 0
#     assert "efemel version:" in result.output
#     assert "Python CLI application" in result.output


# def test_process_command():
#     """Test the process command."""
#     runner = CliRunner()

#     # Create a temporary test file
#     with runner.isolated_filesystem():
#         # Create test Python file
#         with open("test_file.py", "w") as f:
#             f.write(
#                 """
# test_dict = {"key": "value", "number": 42}
# config = {"app": "test", "version": "1.0"}
# _private = {"secret": "hidden"}
# not_a_dict = "string value"
# """
#             )

#         # Run the process command
#         result = runner.invoke(cli, ["process", "test_file.py", "--out", "output"])
#         assert result.exit_code == 0
#         assert "Successfully processed: 1 files" in result.output

#         # Check that output file was created
#         assert os.path.exists("output/test_file.json")

#         # Check the content
#         with open("output/test_file.json") as f:
#             data = json.load(f)

#         assert "test_dict" in data
#         assert "config" in data
#         assert "_private" not in data  # Should be filtered out
#         assert data["test_dict"]["key"] == "value"
#         assert data["config"]["app"] == "test"


def test_process_command_with_test_inputs():
  """Test the process command with actual test input files."""
  runner = CliRunner()

  # Use the actual test input files
  test_inputs_dir = Path(__file__).parent / "inputs"

  with tempfile.TemporaryDirectory() as temp_dir:
    temp_output = Path(temp_dir)

    print(temp_output)

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

    # Print all files in the temp_output dir
    print("Files in temp_output:", list(temp_output.iterdir()))

    # Check that output file was created
    output_file = temp_output / "test_data.json"
    assert output_file.exists()

    # Check the content
    with open(output_file) as f:
      data = json.load(f)

    # Should contain the public dicts from test_data.py
    assert len(data) > 0  # Should have found some dictionaries
