#!/bin/bash
# PreCompact hook: Infinite Context Autopilot — save critical state before compaction.
# Preserves: active chain, skill context, wisdom, current task, git state.
# Restored by session-start.sh on next session.

CCFLOW="${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
CONTEXT_FILE=".tasks/compaction_context.json"

if [ -d ".tasks" ] && command -v python3 >/dev/null 2>&1; then

  # 1. Save session (existing behavior)
  if [ -f "$CCFLOW" ]; then
    HAS_ACTIVE=$(python3 "$CCFLOW" status 2>/dev/null | python3 -c "
import sys,json
try:
    d = json.load(sys.stdin)
    print('yes' if d.get('in_progress', 0) > 0 or d.get('todo', 0) > 0 else 'no')
except: print('no')
" 2>/dev/null)

    if [ "$HAS_ACTIVE" = "yes" ]; then
      python3 "$CCFLOW" session save --name "pre-compact-$(date +%Y%m%d-%H%M%S)" \
        --notes "auto-saved before context compaction" 2>/dev/null || true
    fi
  fi

  # 2. Infinite Context Autopilot — capture critical state to single JSON
  python3 -c "
import json, os, subprocess
from pathlib import Path
from datetime import datetime, timezone

ctx = {'saved_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'sections': {}}

# Active chain state
chain_file = Path('.tasks/skill_ctx/_chain_state.json')
if chain_file.exists():
    try:
        ctx['sections']['chain'] = json.loads(chain_file.read_text())
    except: pass

# Current skill
current_file = Path('.tasks/skill_ctx/_current.json')
if current_file.exists():
    try:
        ctx['sections']['current_skill'] = json.loads(current_file.read_text())
    except: pass

# Recent skill contexts (last 3)
ctx_dir = Path('.tasks/skill_ctx')
if ctx_dir.exists():
    skill_ctxs = {}
    for f in sorted(ctx_dir.glob('cc-*.json'), key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
        try:
            skill_ctxs[f.stem] = json.loads(f.read_text())
        except: pass
    if skill_ctxs:
        ctx['sections']['skill_contexts'] = skill_ctxs

# Recent wisdom (last 5 per category)
wisdom_dir = Path('.tasks/wisdom')
if wisdom_dir.exists():
    wisdom = {}
    for cat in ('learnings', 'decisions', 'conventions'):
        p = wisdom_dir / f'{cat}.jsonl'
        if p.exists():
            entries = []
            for line in p.read_text().strip().split('\n')[-5:]:
                try: entries.append(json.loads(line))
                except: pass
            if entries:
                wisdom[cat] = entries
    if wisdom:
        ctx['sections']['wisdom'] = wisdom

# Git state
try:
    branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=3).stdout.strip()
    last_commit = subprocess.run(['git', 'log', '--oneline', '-1'], capture_output=True, text=True, timeout=3).stdout.strip()
    diff_stat = subprocess.run(['git', 'diff', '--shortstat'], capture_output=True, text=True, timeout=3).stdout.strip()
    ctx['sections']['git'] = {'branch': branch, 'last_commit': last_commit, 'uncommitted': diff_stat}
except: pass

# In-progress tasks
tasks_dir = Path('.tasks/tasks')
if tasks_dir.exists():
    active = []
    for f in tasks_dir.glob('*.json'):
        try:
            t = json.loads(f.read_text())
            if t.get('status') == 'in_progress':
                active.append({'id': t.get('id',''), 'title': t.get('title',''), 'epic': t.get('epic','')})
        except: pass
    if active:
        ctx['sections']['active_tasks'] = active

# Chain metrics summary
metrics_file = Path('.tasks/chain_metrics.json')
if metrics_file.exists():
    try:
        m = json.loads(metrics_file.read_text())
        ctx['sections']['chain_metrics_summary'] = {
            'total_runs': m.get('total_runs', 0),
            'top_chains': {k: v.get('success_rate', 0) for k, v in list(m.get('chains', {}).items())[:5]}
        }
    except: pass

# Write context file
Path('.tasks').mkdir(parents=True, exist_ok=True)
Path('$CONTEXT_FILE').parent.mkdir(parents=True, exist_ok=True)
with open('$CONTEXT_FILE', 'w') as f:
    json.dump(ctx, f, indent=2, ensure_ascii=False)
" 2>/dev/null || true

fi

exit 0
