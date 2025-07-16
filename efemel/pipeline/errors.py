from collections.abc import Callable

from efemel.pipeline.helpers import PipelineContext

ChunkErrorHandler = Callable[[list, Exception, PipelineContext], None]


def raise_error(chunk: list, error: Exception, context: PipelineContext) -> None:
  """A handler that always re-raises the error, stopping execution."""
  raise error


class ErrorHandler:
  """
  Stores and executes a chain of error handlers.
  Handlers are executed in reverse order. The assumption is that the closer the handler
  is to the error, the earlier it should be executed.
  """

  def __init__(self):
    self._handlers: list[ChunkErrorHandler] = []

  def on_error(self, handler: ChunkErrorHandler) -> "ErrorHandler":
    """
    Adds a new handler to the chain.
    This method modifies the ErrorHandler instance in-place.
    """
    self._handlers.insert(0, handler)
    return self

  def handle(self, chunk: list, error: Exception, context: PipelineContext) -> None:
    """
    Executes all handlers in the chain using a list comprehension.
    Execution only stops if a handler raises an exception.
    """
    [handler(chunk, error, context) for handler in self._handlers]
