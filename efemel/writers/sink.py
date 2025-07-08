from pathlib import Path


class SinkWriter:
  def __init__(self, output_dir: str, cwd: Path | None = None):
    """
    Initialize the SinkWriter.
    This class mimics LocalWriter but doesn't actually write files - used for dry runs.
    """
    self.output_dir = Path(output_dir)

    # If output path is relative, make it relative to original working directory
    if not self.output_dir.is_absolute():
      self.output_dir = cwd / self.output_dir

  def write(self, data: str, file_path: Path) -> Path:
    """
    Simulate writing data to a file without actually writing it.
    Returns the path where the file would have been written.

    :param data: The data that would be written (ignored).
    :param file_path: The path to the file where the data would be written.
    :return: The path where the file would have been written.
    """
    output_file = self.output_dir / file_path.with_suffix(".json")
    return output_file
