#!/bin/bash
# SubagentStop hook: track subagent completion, emit dashboard event.

INPUT=$(cat)
AGENT_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('agent_name','unknown'))" 2>/dev/null || echo "unknown")
AGENT_TYPE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('subagent_type',''))" 2>/dev/null || echo "")

# Emit dashboard event
python3 -c "
import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
try:
    from cc_flow.dashboard_events import emit_pipeline_stage
    emit_pipeline_stage('subagent_complete', 'completed', '$AGENT_NAME ($AGENT_TYPE)')
except: pass
" 2>/dev/null || true

exit 0
