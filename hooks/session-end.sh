#!/bin/bash
# Stop hook: auto-save session and consolidate learnings when session ends.

CCFLOW="${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

# Only run if .tasks/ exists
if [ -d ".tasks" ]; then
  # Auto-save session
  python3 "$CCFLOW" session save --name "auto-$(date +%Y%m%d-%H%M%S)" \
    --notes "auto-saved at session end" 2>/dev/null

  # Auto-consolidate if enough learnings
  LEARN_COUNT=$(find .tasks/learnings -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$LEARN_COUNT" -ge 10 ]; then
    python3 "$CCFLOW" consolidate 2>/dev/null
  fi
fi

exit 0
