#!/bin/bash
# Stop hook: auto-save session and consolidate learnings when session ends.

# Only run if prerequisites met
if [ -d ".tasks" ] && command -v cc-flow >/dev/null 2>&1; then
  # Auto-save session
  if cc-flow session save --name "auto-$(date +%Y%m%d-%H%M%S)" \
      --notes "auto-saved at session end" 2>/dev/null; then
    echo "cc-flow: session saved" >&2
  fi

  # Auto-consolidate if enough learnings
  if [ -d ".tasks/learnings" ]; then
    LEARN_COUNT=$(find .tasks/learnings -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$LEARN_COUNT" -ge 10 ]; then
      if cc-flow consolidate 2>/dev/null; then
        echo "cc-flow: learnings consolidated" >&2
      fi
    fi
  fi
fi

exit 0
