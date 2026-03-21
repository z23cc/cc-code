"""cc-flow — task & workflow manager for cc-code plugin.

This package provides the cc-flow CLI. The main entry point is cc-flow.py
which imports from this package.

Architecture:
  cc-flow.py          → thin shim (entry point, preserves CLI path)
  cc_flow/
    __init__.py       → VERSION, constants, core utilities
    core.py           → all_tasks, save_task, load_meta, safe_json_load
    cli.py            → argparse setup + dispatch (main function)
"""

VERSION = "3.6.0"
