---
description: "Python coding standards — only apply when working on Python files (.py)"
alwaysApply: true
---

# Python Style Rules (apply only to .py files)

- Use type hints on all public functions
- Use `list[X]` not `List[X]` (Python 3.9+)
- Use `pathlib.Path` over `os.path`
- Use `logging` not `print()` for output
- Use `with` for all resource management
- Catch specific exceptions, never bare `except:`
- No mutable default arguments (`def f(x=[])` is a bug)
- Import order: stdlib → third-party → local (use isort)
- Max function length: 50 lines
- Max file length: 300 lines
- Use dataclasses or Pydantic for structured data
- Use `value is None` not `value == None`
