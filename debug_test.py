#!/usr/bin/env python3
"""
Simple test to verify folder processing works.
"""

import os

from click.testing import CliRunner

from efemel.cli import cli


def test_folder_processing():
  """Test folder processing manually."""
  runner = CliRunner()

  with runner.isolated_filesystem():
    # Create test structure
    os.makedirs("test_dir", exist_ok=True)

    # Create test file
    with open("test_dir/config.py", "w") as f:
      f.write('app_config = {"name": "test"}\n')

    # Run command
    result = runner.invoke(
      cli, ["process", "test_dir/**/*.py", "--out", "output", "--verbose"]
    )

    print("Exit code:", result.exit_code)
    print("Output:")
    print(result.output)

    print("\nFiles created:")
    for root, dirs, files in os.walk("."):
      for file in files:
        if file.endswith(".json"):
          print(f"  {os.path.join(root, file)}")

    return result.exit_code == 0


if __name__ == "__main__":
  success = test_folder_processing()
  print(f"\nTest {'PASSED' if success else 'FAILED'}")
