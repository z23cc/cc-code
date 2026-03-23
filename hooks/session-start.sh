#!/bin/bash
# SessionStart hook: show skills overview + recent context + worktree detection.

CCFLOW="${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
HOOK_DIR="${CLAUDE_PLUGIN_ROOT}/hooks"

# 1. Static skills overview
cat "${HOOK_DIR}/session-start.md" 2>/dev/null || true

# 2. Worktree detection — critical for multi-worktree workflows
IS_WORKTREE=0
MAIN_REPO=""
WT_BRANCH=""
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null)
CWD=$(pwd)

if [ -n "$GIT_DIR" ] && [ -n "$GIT_COMMON" ]; then
  GIT_DIR_REAL=$(cd "$GIT_DIR" 2>/dev/null && pwd -P)
  GIT_COMMON_REAL=$(cd "$GIT_COMMON" 2>/dev/null && pwd -P)

  if [ "$GIT_DIR_REAL" != "$GIT_COMMON_REAL" ]; then
    IS_WORKTREE=1
    MAIN_REPO=$(cd "$GIT_COMMON_REAL/.." 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null)
    WT_BRANCH=$(git branch --show-current 2>/dev/null)
  fi
fi

if [ "$IS_WORKTREE" = "1" ]; then
  echo ""
  echo "# WORKTREE DETECTED"
  echo ""
  echo "You are in a git worktree, not the main checkout."
  echo "- Branch: $WT_BRANCH"
  echo "- Worktree: $CWD"
  echo "- Main repo: $MAIN_REPO"
  echo "- Task state: shared via .git/cc-flow-state/"
  echo ""
  echo "Only edit files within this worktree. The worktree-guard hook enforces this."
fi

# 3. Dynamic context: recent activity
if [ -d ".tasks" ] && command -v python3 >/dev/null 2>&1 && [ -f "$CCFLOW" ]; then
  echo ""
  echo "# [cc-code] recent context, $(date '+%Y-%m-%d %I:%M%p %Z')"
  echo ""

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
