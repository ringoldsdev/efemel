import json
import shutil
from pathlib import Path

from click.testing import CliRunner

from efemel.cli import cli


def get_files(expected_outputs_dir: Path, glob_pattern: str = "**/*.json"):
  return [
    str(json_file.relative_to(expected_outputs_dir))
    for json_file in expected_outputs_dir.glob(glob_pattern)
  ]


def test_process_command_comprehensive():
  """
  Test the process command with all input files and compare to expected outputs.
  Make sure that you've run `make generate-test-outputs` to create the expected outputs.
  """
  runner = CliRunner()
  test_inputs_dir = Path(__file__).parent / "inputs_basic"
  expected_outputs_dir = Path(__file__).parent / "outputs"

  with runner.isolated_filesystem():
    # Copy all .py files recursively using glob
    for py_file in test_inputs_dir.glob("**/*.py"):
      # Calculate relative path from inputs directory
      rel_path = py_file.relative_to(test_inputs_dir)
      target_path = Path(rel_path)

      # Create parent directories if they don't exist
      target_path.parent.mkdir(parents=True, exist_ok=True)

      # Copy the file
      shutil.copy(py_file, target_path)

    # Run the process command on all Python files recursively
    result = runner.invoke(cli, ["process", "**/*.py", "--out", "output"])
    assert result.exit_code == 0, f"Command failed with output: {result.output}"

    # Compare content of each file
    for file_path in get_files(expected_outputs_dir):
      generated_file = Path("output") / file_path
      expected_file = expected_outputs_dir / file_path

      assert generated_file.exists(), f"Generated file {generated_file} not found"

      # Load both JSON files
      with open(generated_file) as f:
        generated_data = json.load(f)

      with open(expected_file) as f:
        expected_data = json.load(f)

      # Compare the JSON content
      assert generated_data == expected_data, (
        f"Content mismatch in {file_path}:\n"
        f"Generated: {generated_data}\n"
        f"Expected: {expected_data}"
      )
