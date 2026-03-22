#!/bin/bash
# PreCompact hook: save session state before context compaction.
# Only saves if there are active tasks to preserve.

CCFLOW="${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

if [ -d ".tasks" ] && command -v python3 >/dev/null 2>&1 && [ -f "$CCFLOW" ]; then
  # Only save if there are in-progress tasks (avoid empty saves)
  HAS_ACTIVE=$(python3 "$CCFLOW" status 2>/dev/null | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    print('yes' if d.get('in_progress', 0) > 0 or d.get('todo', 0) > 0 else 'no')
except Exception:
    print('no')
" 2>/dev/null)

  if [ "$HAS_ACTIVE" = "yes" ]; then
    python3 "$CCFLOW" session save --name "pre-compact-$(date +%Y%m%d-%H%M%S)" \
      --notes "auto-saved before context compaction" 2>/dev/null || true
  fi
fi

exit 0
