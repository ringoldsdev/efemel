import os
from glob import glob
from pathlib import Path


class LocalReader:
  def __init__(self, cwd: str | None = None):
    """
    Initialize the LocalReader with an optional working directory.

    :param cwd: Optional working directory to set for file operations.
    """

    self.original_cwd = Path(os.getcwd())

    if cwd is None:
      self.cwd_path = self.original_cwd
      return

    cwd_path = Path(cwd)

    if not cwd_path.is_absolute():
      cwd_path = Path(self.original_cwd) / cwd_path

    self.cwd_path = cwd_path.resolve()

    if not cwd_path.exists():
      raise FileNotFoundError(f"Working directory '{cwd}' does not exist")

    if not cwd_path.is_dir():
      raise NotADirectoryError(f"Working directory '{cwd}' is not a directory")

  def read(self, glob_pattern: str):
    # Check if file_pattern ends with .py
    if not glob_pattern.endswith(".py"):
      raise Exception("File pattern must end with .py to match Python files.")

    matching_files = glob(glob_pattern, recursive=True, root_dir=str(self.cwd_path))

    if not matching_files:
      raise Exception(f"No files found matching pattern: {glob_pattern}")

    for file_path in matching_files:
      # Ignore __init__.py files
      if "__init__.py" in file_path:
        continue
      yield Path(file_path)
