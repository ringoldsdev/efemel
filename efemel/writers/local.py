from pathlib import Path


class LocalWriter:
  def __init__(self, output_dir: str, cwd: Path | None = None):
    """
    Initialize the LocalWriter.
    This class is responsible for writing data to local files.
    """
    self.output_dir = Path(output_dir)

    # If output path is relative, make it relative to original working directory
    if not self.output_dir.is_absolute():
      self.output_dir = cwd / self.output_dir

  def write(self, data: str, file_path: Path) -> None:
    """
    Write the given data to a local file.

    :param data: The data to write.
    :param file_path: The path to the file where the data should be written.
    """
    output_file = self.output_dir / file_path.with_suffix(".json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
      f.write(data)

    return output_file
