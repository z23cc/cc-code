#!/usr/bin/env python3
"""cc-flow CLI — thin shim for backward compatibility.

Preferred: cc-flow <command>  (after pip install -e .)
"""

import sys
from pathlib import Path

# Ensure cc_flow package is importable
sys.path.insert(0, str(Path(__file__).parent))

from cc_flow.entry import main

if __name__ == "__main__":
    main()
