"""cc-flow skin — unified terminal output with colors and icons.

Inspired by CLI-Anything's ReplSkin. No external dependencies.
Graceful degradation: respects NO_COLOR and non-TTY environments.
"""

import os
import sys

from cc_flow import VERSION

# ANSI color codes
_RESET = "\033[0m"
_BOLD = "\033[1m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_CYAN = "\033[36m"
_DIM = "\033[2m"
_ACCENT = "\033[38;5;99m"  # Purple accent for cc-flow


def _color_enabled():
    """Check if color output is enabled."""
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


def _c(color, text):
    """Colorize text if colors enabled."""
    if _color_enabled():
        return f"{color}{text}{_RESET}"
    return str(text)


def banner():
    """Print startup banner."""
    print(f"\n  {_c(_ACCENT + _BOLD, '◆')} {_c(_BOLD, 'cc-flow')} {_c(_DIM, f'v{VERSION}')}")
    print(f"  {_c(_DIM, 'Task & workflow manager for Claude Code')}")
    print()


def success(message):
    """Print success message."""
    print(f"  {_c(_GREEN, '✓')} {message}")


def error(message):
    """Print error message."""
    print(f"  {_c(_RED, '✗')} {message}", file=sys.stderr)


def warning(message):
    """Print warning message."""
    print(f"  {_c(_YELLOW, '⚠')} {message}")


def info(message):
    """Print info message."""
    print(f"  {_c(_BLUE, '●')} {message}")


def dim(message):
    """Print dimmed/secondary text."""
    print(f"  {_c(_DIM, message)}")


def heading(title):
    """Print section heading."""
    print(f"\n  {_c(_BOLD, title)}")


def table(headers, rows):
    """Print a formatted table."""
    if not rows:
        dim("(no data)")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    # Header
    header_line = "  " + "  ".join(
        _c(_BOLD, str(h).ljust(widths[i])) for i, h in enumerate(headers)
    )
    print(header_line)
    print("  " + "  ".join("─" * w for w in widths))

    # Rows
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            s = str(cell).ljust(widths[i]) if i < len(widths) else str(cell)
            cells.append(s)
        print("  " + "  ".join(cells))


def progress_bar(current, total, label="", width=20):
    """Print a progress bar."""
    pct = int(current / total * 100) if total > 0 else 0
    filled = int(width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    color = _GREEN if pct == 100 else _YELLOW if pct > 50 else _RED
    print(f"  {_c(color, bar)} {pct:>3}% {_c(_DIM, label)}")


def goodbye():
    """Print exit message."""
    print(f"\n  {_c(_DIM, 'bye')} {_c(_ACCENT, '◆')}\n")
