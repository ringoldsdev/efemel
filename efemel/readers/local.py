import os
from glob import glob
from pathlib import Path


class LocalReader:
  def __init__(self, cwd: str | None = None):
    """
    Initialize the LocalReader with an optional working directory.

    :param cwd: Optional working directory to set for file operations.
    """
    self.original_cwd, self.cwd = self.set_cwd(cwd)

  def set_cwd(self, cwd: str | None):
    original_cwd = os.getcwd()

    if not cwd:
      return original_cwd, original_cwd

    cwd_path = Path(cwd)

    if not cwd_path.is_absolute():
      cwd_path = Path(original_cwd) / cwd_path

    cwd_path = cwd_path.resolve()

    if not cwd_path.exists():
      raise FileNotFoundError(f"Working directory '{cwd}' does not exist")

    if not cwd_path.is_dir():
      raise NotADirectoryError(f"Working directory '{cwd}' is not a directory")

    os.chdir(cwd_path)

    return original_cwd, cwd_path

  def read(self, glob_pattern: str):
    # Check if file_pattern ends with .py
    if not glob_pattern.endswith(".py"):
      raise Exception("File pattern must end with .py to match Python files.")

    matching_files = glob(glob_pattern, recursive=True)

    if not matching_files:
      raise Exception(f"No files found matching pattern: {glob_pattern}")

    for file_path in matching_files:
      yield Path(file_path)
