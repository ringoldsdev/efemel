"""Integration tests for Pipeline and Transformer working together."""

import threading

from efemel.pipeline.pipeline import Pipeline
from efemel.pipeline.transformers.parallel import ParallelTransformer
from efemel.pipeline.transformers.transformer import PipelineContext
from efemel.pipeline.transformers.transformer import Transformer


class TestPipelineTransformerBasics:
  """Test basic Pipeline and Transformer integration."""

  def test_basic_pipeline_transformer_integration(self):
    """Test basic pipeline and transformer integration."""
    transformer = Transformer.init(int).map(lambda x: x * 2).filter(lambda x: x > 5)
    result = Pipeline([1, 2, 3, 4, 5]).apply(transformer).to_list()
    assert result == [6, 8, 10]

  def test_pipeline_context_sharing(self):
    """Test that context is properly shared between pipeline and transformers."""
    context = {"multiplier": 3, "threshold": 5}
    transformer = Transformer().map(lambda x, ctx: x * ctx["multiplier"]).filter(lambda x, ctx: x > ctx["threshold"])
    result = Pipeline([1, 2, 3]).context(context).apply(transformer).to_list()
    assert result == [6, 9]

  def test_pipeline_transform_shorthand(self):
    """Test pipeline transform shorthand method."""
    result = (
      Pipeline([1, 2, 3, 4, 5])
      .transform(lambda t: t.map(lambda x: x * 3))
      .transform(lambda t: t.filter(lambda x: x > 6))
      .to_list()
    )
    assert result == [9, 12, 15]


class TestPipelineDataProcessing:
  """Test common data processing patterns with pipelines."""

  def test_etl_pattern(self):
    """Test Extract-Transform-Load pattern."""
    raw_data = [
      {"name": "Alice", "age": 25, "salary": 50000},
      {"name": "Bob", "age": 30, "salary": 60000},
      {"name": "Charlie", "age": 35, "salary": 70000},
      {"name": "David", "age": 28, "salary": 55000},
    ]

    # Extract names of people over 28 with salary > 55000
    result = (
      Pipeline(raw_data)
      .transform(lambda t: t.filter(lambda x: x["age"] > 28 and x["salary"] > 55000))
      .transform(lambda t: t.map(lambda x: x["name"]))
      .to_list()
    )

    assert result == ["Bob", "Charlie"]

  def test_data_validation_pattern(self):
    """Test data validation and cleaning pattern."""
    raw_data = [1, "2", 3.0, "invalid", 5, None, 7]
    valid_numbers = []

    def validate_and_convert(x):
      try:
        if x is not None and str(x).lower() != "invalid":
          num = float(x)
          valid_numbers.append(num)
          return int(num)
        return None
      except (ValueError, TypeError):
        return None

    result = (
      Pipeline(raw_data)
      .transform(lambda t: t.map(validate_and_convert))
      .transform(lambda t: t.filter(lambda x: x is not None))
      .to_list()
    )

    assert result == [1, 2, 3, 5, 7]
    assert valid_numbers == [1.0, 2.0, 3.0, 5.0, 7.0]


class TestPipelineParallelTransformerIntegration:
  """Test Pipeline integration with ParallelTransformer and context modification."""

  def test_parallel_transformer_basic_integration(self):
    """Test pipeline with parallel transformer for basic operations."""
    parallel_transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2)
    parallel_transformer = parallel_transformer.map(lambda x: x * 2).filter(lambda x: x > 5)

    result = Pipeline([1, 2, 3, 4, 5]).apply(parallel_transformer).to_list()
    assert sorted(result) == [6, 8, 10]

  def test_parallel_transformer_with_context_modification(self):
    """Test parallel transformer safely modifying shared context."""
    context = PipelineContext({"processed_count": 0, "sum_total": 0, "_lock": threading.Lock()})

    def safe_increment_and_transform(x: int, ctx: PipelineContext) -> int:
      with ctx["_lock"]:
        ctx["processed_count"] += 1
        ctx["sum_total"] += x
      return x * 2

    parallel_transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2)
    parallel_transformer = parallel_transformer.map(safe_increment_and_transform)

    data = [1, 2, 3, 4, 5]
    result = Pipeline(data).context(context).apply(parallel_transformer).to_list()

    # Verify transformation results
    assert sorted(result) == [2, 4, 6, 8, 10]
    # Verify context was safely modified
    assert context["processed_count"] == len(data)
    assert context["sum_total"] == sum(data)

  def test_pipeline_accesses_modified_context(self):
    """Test that pipeline can access context data modified by parallel transformer."""
    context = PipelineContext({"items_processed": 0, "even_count": 0, "odd_count": 0, "_lock": threading.Lock()})

    def count_and_transform(x: int, ctx: PipelineContext) -> int:
      with ctx["_lock"]:
        ctx["items_processed"] += 1
        if x % 2 == 0:
          ctx["even_count"] += 1
        else:
          ctx["odd_count"] += 1
      return x * 3

    parallel_transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=3)
    parallel_transformer = parallel_transformer.map(count_and_transform)

    data = [1, 2, 3, 4, 5, 6]
    pipeline = Pipeline(data).context(context)
    result = pipeline.apply(parallel_transformer).to_list()

    # Verify results and context access
    assert sorted(result) == [3, 6, 9, 12, 15, 18]
    assert pipeline.ctx["items_processed"] == 6
    assert pipeline.ctx["even_count"] == 3  # 2, 4, 6
    assert pipeline.ctx["odd_count"] == 3  # 1, 3, 5

  def test_multiple_parallel_transformers_chaining(self):
    """Test chaining multiple parallel transformers with shared context."""
    # Shared context for statistics across transformations
    context = PipelineContext({"stage1_processed": 0, "stage2_processed": 0, "total_sum": 0})

    def stage1_processor(x: int, ctx: PipelineContext) -> int:
      """First stage processing with context update."""
      with ctx["lock"]:
        ctx["stage1_processed"] += 1
        ctx["total_sum"] += x
      return x * 2

    def stage2_processor(x: int, ctx: PipelineContext) -> int:
      """Second stage processing with context update."""
      with ctx["lock"]:
        ctx["stage2_processed"] += 1
        ctx["total_sum"] += x  # Add transformed value too
      return x + 10

    # Create two parallel transformers
    stage1 = ParallelTransformer[int, int](max_workers=2, chunk_size=2).map(stage1_processor)
    stage2 = ParallelTransformer[int, int](max_workers=2, chunk_size=2).map(stage2_processor)

    data = [1, 2, 3, 4, 5]

    # Chain parallel transformers in pipeline
    pipeline = Pipeline(data).context(context)
    result = (
      pipeline.apply(stage1)  # [2, 4, 6, 8, 10]
      .apply(stage2)  # [12, 14, 16, 18, 20]
      .to_list()
    )

    # Verify final results
    expected_stage1 = [x * 2 for x in data]  # [2, 4, 6, 8, 10]
    expected_final = [x + 10 for x in expected_stage1]  # [12, 14, 16, 18, 20]
    assert result == expected_final

    # Verify context reflects both stages
    final_context = pipeline.ctx
    assert final_context["stage1_processed"] == 5
    assert final_context["stage2_processed"] == 5

    # Total sum should include original values + transformed values
    original_sum = sum(data)  # 1+2+3+4+5 = 15
    stage1_sum = sum(expected_stage1)  # 2+4+6+8+10 = 30
    expected_total = original_sum + stage1_sum  # 15 + 30 = 45
    assert final_context["total_sum"] == expected_total

  def test_pipeline_context_isolation_with_parallel_processing(self):
    """Test that different pipeline instances have isolated contexts."""

    # Create base context structure
    def create_context():
      return PipelineContext({"count": 0})

    def increment_counter(x: int, ctx: PipelineContext) -> int:
      """Increment counter in context."""
      with ctx["lock"]:
        ctx["count"] += 1
      return x * 2

    parallel_transformer = ParallelTransformer[int, int](max_workers=2, chunk_size=2)
    parallel_transformer = parallel_transformer.map(increment_counter)

    data = [1, 2, 3]

    # Create two separate pipeline instances with their own contexts
    pipeline1 = Pipeline(data).context(create_context())
    pipeline2 = Pipeline(data).context(create_context())

    # Process with both pipelines
    result1 = pipeline1.apply(parallel_transformer).to_list()
    result2 = pipeline2.apply(parallel_transformer).to_list()

    # Both should have same transformation results
    assert result1 == [2, 4, 6]
    assert result2 == [2, 4, 6]

    # But contexts should be isolated
    assert pipeline1.ctx["count"] == 3
    assert pipeline2.ctx["count"] == 3

    # Verify they are different context objects
    assert pipeline1.ctx is not pipeline2.ctx
