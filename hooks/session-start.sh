#!/bin/bash
# SessionStart hook: show skills overview + recent context.

CCFLOW="${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
HOOK_DIR="${CLAUDE_PLUGIN_ROOT}/hooks"

# 1. Static skills overview
cat "${HOOK_DIR}/session-start.md" 2>/dev/null || true

# 2. Dynamic context: recent activity (if .tasks/ exists)
if [ -d ".tasks" ] && command -v python3 >/dev/null 2>&1 && [ -f "$CCFLOW" ]; then
  echo ""
  echo "# [cc-code] recent context, $(date '+%Y-%m-%d %I:%M%p %Z')"
  echo ""

  # Show in-progress tasks
  ACTIVE=$(python3 "$CCFLOW" status 2>/dev/null | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    ip = d.get('in_progress', 0)
    bl = d.get('blocked', 0)
    todo = d.get('todo', 0)
    done = d.get('done', 0)
    if ip > 0: print(f'Active: {ip} task(s) in progress')
    if bl > 0: print(f'Blocked: {bl} task(s)')
    if todo > 0: print(f'Ready: {todo} task(s) todo')
    if done > 0: print(f'Done: {done} completed')
except Exception:
    pass
" 2>/dev/null)

  if [ -n "$ACTIVE" ]; then
    echo "$ACTIVE"
  else
    echo "No previous sessions found for this project yet."
  fi
fi
