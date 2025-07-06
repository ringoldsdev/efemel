"""
Example usage of the new class-based hooks manager.
"""

from efemel.hooks_manager import HooksManager

# Create a new instance
manager = HooksManager()


# Example hooks
def before_test(context):
  print(f"BEFORE: {context['message']}")
  context["step"] = 1


def regular_test(context):
  print(f"REGULAR: {context['message']}, step: {context['step']}")
  context["step"] = 2


def another_test(context):
  print(f"ANOTHER: {context['message']}, step: {context['step']}")
  context["result"] = "processed"


# Register hooks using the new method names
manager.add_before("test", before_test)
manager.add("test", regular_test)
manager.add("test", another_test)

# Test the hooks
context = {"message": "Hello World"}
result_context, result_value = manager.call("test", context, ["result"])

print(f"Final context: {context}")
print(f"Returned result: {result_value}")
print(f"Hook count: {manager.get_count('test')}")
print(f"All hooks: {manager.list()}")
