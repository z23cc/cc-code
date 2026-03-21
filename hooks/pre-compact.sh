#!/bin/bash
# PreCompact hook: save session + compact context before compaction.

CCFLOW="${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

# Save session state
if [ -d ".tasks" ] && command -v python3 >/dev/null 2>&1 && [ -f "$CCFLOW" ]; then
  python3 "$CCFLOW" session save --name "pre-compact-$(date +%Y%m%d-%H%M%S)" \
    --notes "auto-saved before context compaction" 2>/dev/null || true
fi

exit 0
