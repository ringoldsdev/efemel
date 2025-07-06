import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from efemel.cli import cli


def get_files(expected_outputs_dir: Path, glob_pattern: str = "**/*.json"):
  return [str(json_file.relative_to(expected_outputs_dir)) for json_file in expected_outputs_dir.glob(glob_pattern)]


def get_test_scenarios():
  """Get all available test scenarios based on input/output folder pairs."""
  test_dir = Path(__file__).parent

  return [
    {
      "name": "basic",
      "inputs_dir": test_dir / "inputs/basic",
      "outputs_dir": test_dir / "outputs/basic",
      "process_args": ["process", "**/*.py", "--out", "output"],
    },
    {
      "name": "basic flattened",
      "inputs_dir": test_dir / "inputs/basic",
      "outputs_dir": test_dir / "outputs/flattened",
      "process_args": ["process", "**/*.py", "--out", "output", "--flatten"],
    },
    {
      "name": "env",
      "inputs_dir": test_dir / "inputs/with_imports",
      "outputs_dir": test_dir / "outputs/with_imports",
      "process_args": ["process", "**/*.py", "--out", "output", "--env", "prod"],
    },
    {
      "name": "basic with hooks",
      "inputs_dir": test_dir / "inputs/basic",
      "outputs_dir": test_dir / "outputs/with_hooks",
      "process_args": ["process", "**/*.py", "--out", "output", "--hooks-file", "hooks/output_filename.py"],
    },
  ]


@pytest.mark.parametrize("scenario", get_test_scenarios())
def test_process_command_comprehensive(scenario):
  """
  Test the process command with all input files and compare to expected outputs.
  This test runs for each input/output folder pair found in the tests directory.
  Make sure that you've run `make generate-test-outputs` to create the expected outputs.
  """
  runner = CliRunner()

  # Extract values from scenario dictionary
  scenario_name = scenario["name"]
  inputs_dir = scenario["inputs_dir"]
  outputs_dir = scenario["outputs_dir"]
  process_args = scenario["process_args"]

  with runner.isolated_filesystem():
    # Copy all .py files recursively using glob
    for py_file in inputs_dir.glob("**/*.py"):
      # Calculate relative path from inputs directory
      rel_path = py_file.relative_to(inputs_dir)
      target_path = Path(rel_path)  # Copy directly to isolated filesystem root

      # Create parent directories if they don't exist
      target_path.parent.mkdir(parents=True, exist_ok=True)

      # Copy the file
      shutil.copy(py_file, target_path)

    # Copy all hooks files if they exist
    hooks_dir = Path(__file__).parent / "hooks"
    if hooks_dir.exists():
      for hook_file in hooks_dir.glob("*.py"):
        # Calculate relative path from hooks directory
        rel_path = hook_file.relative_to(hooks_dir)
        target_path = Path("hooks") / rel_path

        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        shutil.copy(hook_file, target_path)

    # Run the process command on all Python files recursively
    result = runner.invoke(cli, process_args)
    assert result.exit_code == 0, f"Command failed for scenario '{scenario_name}' with output: {result.output}"

    print(f"Generated files for {scenario_name}: {get_files(Path('output'))}")

    # Special handling for hooks scenario since it creates different structure
    if scenario_name == "basic with hooks":
      # For hooks scenario, just verify that files were created with expected transformations
      generated_files = list(Path("output").glob("**/*.json"))

      # Verify at least some files were generated
      assert len(generated_files) > 0, f"No files generated for scenario '{scenario_name}'"

      # Verify the hooks worked by checking for "test" subdirectory and timestamp in filenames
      test_subdir_files = list(Path("output/test").glob("**/*.json"))
      assert len(test_subdir_files) > 0, "No files found in 'test' subdirectory created by hooks"

      # Verify timestamp was added to filenames
      for generated_file in test_subdir_files:
        assert "_20250705" in generated_file.stem, f"Timestamp not found in filename: {generated_file.name}"

      print(f"Hooks test passed: {len(test_subdir_files)} files generated with correct transformations")

    else:
      # For other scenarios, compare content of each file with expected outputs
      for file_path in get_files(outputs_dir):
        generated_file = Path("output") / file_path
        expected_file = outputs_dir / file_path

        assert generated_file.exists(), f"Generated file {generated_file} not found for scenario '{scenario_name}'"

        # Load both JSON files
        with open(generated_file) as f:
          generated_data = json.load(f)

        with open(expected_file) as f:
          expected_data = json.load(f)

        # Compare the JSON content
        assert generated_data == expected_data, (
          f"Content mismatch in {file_path} for scenario '{scenario_name}':\n"
          f"Generated: {generated_data}\n"
          f"Expected: {expected_data}"
        )
