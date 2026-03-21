#!/bin/bash
# PreCompact hook: save session state before context compaction.
# This ensures we can recover context after auto-compaction.

CCFLOW="${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"

# Only run if .tasks/ exists (project uses cc-flow)
if [ -d ".tasks" ]; then
  python3 "$CCFLOW" session save --name "pre-compact-$(date +%Y%m%d-%H%M%S)" \
    --notes "auto-saved before context compaction" 2>/dev/null
fi

exit 0
