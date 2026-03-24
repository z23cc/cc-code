#!/bin/bash
# SessionStart hook: show skills overview + smart project state detection.
# Detects: interrupted chains, pending tasks, lint status, recent activity.

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

# 3. Smart project state detection + recommendations
if command -v python3 >/dev/null 2>&1 && [ -f "$CCFLOW" ]; then
  echo ""
  echo "# [cc-code] recent context, $(date '+%Y-%m-%d %I:%M%p %Z')"
  echo ""

  python3 -c "
import json, sys, os
from pathlib import Path

recommendations = []
context_lines = []

# --- Detect interrupted chain ---
chain_state = Path('.tasks/skill_ctx/_chain_state.json')
if chain_state.exists():
    try:
        state = json.loads(chain_state.read_text())
        chain = state.get('chain', '?')
        step = state.get('current_step', 0) + 1
        total = state.get('total_steps', 0)
        context_lines.append(f'Interrupted chain: {chain} (step {step}/{total})')
        recommendations.append(f'Resume chain: cc-flow go --resume')
    except Exception:
        pass

# --- Detect task status ---
tasks_dir = Path('.tasks/tasks')
if tasks_dir.exists():
    in_progress = 0
    blocked = 0
    todo = 0
    done = 0
    for f in tasks_dir.glob('*.json'):
        try:
            t = json.loads(f.read_text())
            s = t.get('status', '')
            if s == 'in_progress': in_progress += 1
            elif s == 'blocked': blocked += 1
            elif s == 'todo': todo += 1
            elif s == 'done': done += 1
        except Exception:
            pass
    if in_progress > 0:
        context_lines.append(f'Active: {in_progress} task(s) in progress')
        recommendations.append('Continue: cc-flow next')
    if blocked > 0:
        context_lines.append(f'Blocked: {blocked} task(s)')
    if todo > 0:
        context_lines.append(f'Ready: {todo} task(s) waiting')
        if not in_progress:
            recommendations.append(f'Start next task: cc-flow start')
    if done > 0:
        context_lines.append(f'Done: {done} completed')

# --- Detect recent git activity ---
try:
    import subprocess
    result = subprocess.run(['git', 'log', '--oneline', '-1', '--format=%ar'],
                          capture_output=True, text=True, timeout=3)
    if result.returncode == 0:
        last_commit = result.stdout.strip()
        context_lines.append(f'Last commit: {last_commit}')
except Exception:
    pass

# --- Detect uncommitted changes ---
try:
    import subprocess
    result = subprocess.run(['git', 'diff', '--stat', '--shortstat'],
                          capture_output=True, text=True, timeout=3)
    if result.returncode == 0 and result.stdout.strip():
        context_lines.append(f'Uncommitted changes: {result.stdout.strip().split(chr(10))[-1].strip()}')
        recommendations.append('Review changes: git diff')
except Exception:
    pass

# --- Detect lint issues (quick check) ---
try:
    import subprocess
    result = subprocess.run(['python3', '-m', 'ruff', 'check', '.', '--statistics', '-q'],
                          capture_output=True, text=True, timeout=10, cwd=os.getcwd())
    if result.returncode != 0 and result.stdout.strip():
        lines = result.stdout.strip().split('\n')
        total_issues = len(lines)
        if total_issues > 0:
            context_lines.append(f'Lint: {total_issues} issue type(s) found')
            recommendations.append('Fix lint: cc-flow verify --fix')
except Exception:
    pass

# --- Output ---
if context_lines:
    for line in context_lines:
        print(line)
else:
    print('No previous sessions found for this project yet.')

if recommendations:
    print('')
    print('Recommended next steps:')
    for i, rec in enumerate(recommendations, 1):
        print(f'  {i}. {rec}')
    print('')
    print('Or just: cc-flow go \"describe what you want\"')
" 2>/dev/null
fi
