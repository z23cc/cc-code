---
name: cc-ralph
description: "Start Ralph autonomous execution. One command, unattended."
---

Start autonomous execution via `cc-flow ralph`.

## Usage

```bash

# Parse arguments
GOAL="${1:-}"
MAX="${2:-25}"

if [[ -n "$GOAL" ]]; then
  # Goal-driven: run until objective achieved
  cc-flow ralph --goal "$GOAL" --max "$MAX"
else
  # Task-driven: work through existing tasks
  cc-flow ralph --max "$MAX"
fi
```

## Examples

- `/cc-ralph` — work through all pending tasks, unattended
- `/cc-ralph "all tests pass"` — goal-driven, self-heal until tests green
- `/cc-ralph "health >= 90" 50` — target health score, max 50 iterations
