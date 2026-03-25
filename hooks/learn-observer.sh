#!/bin/bash
# PostToolUse hook: continuous learning observer.
# Captures patterns from every tool call for auto-learning.
# Async — does not block execution.

INPUT=$(cat)
TOOL=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
EXIT_CODE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_result',{}).get('exit_code','0'))" 2>/dev/null || echo "0")

# Only observe significant tool calls
case "$TOOL" in
  Bash|Edit|Write)
    # Track tool usage pattern for learning
    python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
try:
    from cc_flow.auto_learn import _record_wisdom
    tool = '$TOOL'
    exit_code = '$EXIT_CODE'
    if exit_code != '0' and tool == 'Bash':
        _record_wisdom('learnings', f'Bash command failed (exit {exit_code})', source='observer')
except: pass

# Dashboard event
try:
    from cc_flow.dashboard_events import _post_event
    _post_event('tool_observed', engine='$TOOL', data={'exit_code': '$EXIT_CODE'})
except: pass
" 2>/dev/null &
    ;;
esac

exit 0
