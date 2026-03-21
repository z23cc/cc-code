#!/bin/bash
# Stop hook: auto-save session and consolidate learnings when session ends.

CCFLOW="${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

# Only run if prerequisites met
if [ -d ".tasks" ] && command -v python3 >/dev/null 2>&1 && [ -f "$CCFLOW" ]; then
  # Auto-save session (ignore failures)
  python3 "$CCFLOW" session save --name "auto-$(date +%Y%m%d-%H%M%S)" \
    --notes "auto-saved at session end" 2>/dev/null || true

  # Auto-consolidate if enough learnings (ignore failures)
  if [ -d ".tasks/learnings" ]; then
    LEARN_COUNT=$(find .tasks/learnings -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$LEARN_COUNT" -ge 10 ]; then
      python3 "$CCFLOW" consolidate 2>/dev/null || true
    fi
  fi
fi

exit 0
