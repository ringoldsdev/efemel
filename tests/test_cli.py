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
    },
    {
      "name": "flattened",
      "inputs_dir": test_dir / "inputs/basic",
      "outputs_dir": test_dir / "outputs/flattened",
      "process_args": ["--flatten"],
    },
    {
      "name": "env",
      "inputs_dir": test_dir / "inputs/with_imports",
      "outputs_dir": test_dir / "outputs/with_imports",
      "process_args": ["--env", "prod"],
    },
    {
      "name": "hooks",
      "inputs_dir": test_dir / "inputs/basic",
      "outputs_dir": test_dir / "outputs/with_hooks",
      "process_args": ["--hooks", "hooks/before_after/output_filename.py"],
      "assets": ["hooks/before_after/output_filename.py"],
    },
    {
      "name": "hooks dir",
      "inputs_dir": test_dir / "inputs/basic",
      "outputs_dir": test_dir / "outputs/with_hooks_dir",
      "process_args": ["--hooks", "hooks/multiple"],
      "assets": ["hooks/multiple/output_filename.py"],
    },
    {
      "name": "process data - pick",
      "inputs_dir": test_dir / "inputs/process_data",
      "outputs_dir": test_dir / "outputs/process_data_pick",
      "process_args": ["--pick", "user_data"],
    },
    {
      "name": "process data - unwrap",
      "inputs_dir": test_dir / "inputs/process_data",
      "outputs_dir": test_dir / "outputs/process_data_unwrap",
      "process_args": ["--unwrap", "user_data"],
    },
    {
      "name": "with params",
      "inputs_dir": test_dir / "inputs/with_params",
      "outputs_dir": test_dir / "outputs/with_params",
      "process_args": [
        "--param",
        "app_name=myapp",
        "--param",
        "version=2.0.0",
        "--param",
        "debug_mode=true",
        "--param",
        "port=8080",
        "--param",
        'database_config={"host":"prod-db","port":5432}',
        "--param",
        "memory_mb=512",
      ],
    },
    {
      "name": "with params file",
      "inputs_dir": test_dir / "inputs/with_params_file",
      "outputs_dir": test_dir / "outputs/with_params_file",
      "process_args": [
        "--params-file",
        "params/params.py",
      ],
      "assets": ["params/params.py"],
    },
    {
      "name": "dry run",
      "inputs_dir": test_dir / "inputs/basic",
      "outputs_dir": test_dir / "outputs/dry_run",
      "process_args": ["--dry-run"],
    },
  ]


@pytest.mark.parametrize("scenario", get_test_scenarios(), ids=lambda scenario: scenario["name"])
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
  additional_args = scenario.get("process_args", [])
  assets = scenario.get("assets", [])

  # Build complete process arguments
  process_args = ["process", "**/*.py", "--out", "output"] + additional_args

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

    # Copy specified hooks files if they exist
    test_dir = Path(__file__).parent
    for hook_filename in assets:
      hook_path = test_dir / hook_filename
      if hook_path.exists():
        target_hook_path = Path(hook_filename)
        # Create parent directories if they don't exist
        target_hook_path.parent.mkdir(parents=True, exist_ok=True)
        # Copy the file
        shutil.copy(hook_path, target_hook_path)

    # Run the process command on all Python files recursively
    result = runner.invoke(cli, process_args)
    assert result.exit_code == 0, f"Command failed for scenario '{scenario_name}' with output: {result.output}"

    # For other scenarios, compare content of each file with expected outputs
    for expected_file in outputs_dir.glob("**/*.json"):
      generated_file = Path("output") / expected_file.relative_to(outputs_dir)

      assert generated_file.exists(), f"Generated file {generated_file} not found for scenario '{scenario_name}'"

      # Load both JSON files
      with open(generated_file) as f:
        generated_data = json.load(f)

      with open(expected_file) as f:
        expected_data = json.load(f)

      # Compare the JSON content
      assert generated_data == expected_data, (
        f"Content mismatch in {expected_file.relative_to(outputs_dir)} for scenario '{scenario_name}':\n"
        f"Generated: {generated_data}\n"
        f"Expected: {expected_data}"
      )
