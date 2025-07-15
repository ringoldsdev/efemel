from efemel.pipeline.pipeline import Pipeline
from efemel.pipeline.transformers.transformer import Transformer


def generate_test_data(size: int = 1_000_000) -> list[int]:
  """Generate test data of specified size."""
  return range(size)  # type: ignore


def run():
  PIPELINE_TRANSFORMER = (
    Transformer()
    .filter(lambda x: x % 2 == 0)  # Filter even numbers
    .map(lambda x: x * 2)  # Double them
    .filter(lambda x: x > 100)  # Filter > 100
    .map(lambda x: x + 1)
  )

  for i in range(20):
    Pipeline(generate_test_data(1_000_000)).apply(PIPELINE_TRANSFORMER).to_list()
    print(f"Finished run {i + 1}")


if __name__ == "__main__":
  try:
    run()
  except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    raise
