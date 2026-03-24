#!/bin/bash
# PostToolUse hook: after cc-flow commands, suggest next steps.
# Reads tool input JSON from stdin.
# Enhanced: integrates with skill flow graph for smart next-skill suggestions.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Helper: get next skill suggestion from flow graph
_skill_next() {
  python3 -m cc_flow skill next --skill "$1" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('next_skills'):
        print(d.get('message', ''))
except: pass
" 2>/dev/null
}

case "$COMMAND" in
  *cc-flow*done*|*cc_flow*done*)
    # Check if there's a chain or flow graph suggestion
    NEXT=$(_skill_next "" 2>/dev/null)
    if [ -n "$NEXT" ]; then
      echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"decision\":\"allow\",\"message\":\"Task done! Flow: ${NEXT}. Or: (1) cc-flow chain advance — next chain step, (2) cc-flow learn — record what worked, (3) /cc-commit — if ready.\"}}"
    else
      echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Task done! Next: (1) cc-flow learn — record what worked, (2) cc-flow next — pick next task, (3) /cc-commit — if ready."}}'
    fi
    ;;
  *cc-flow*chain*advance*)
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Chain advanced! Run the suggested skill, then cc-flow chain advance when done."}}'
    ;;
  *cc-flow*skill*ctx*save*)
    # After saving skill context, suggest next
    NEXT=$(_skill_next "" 2>/dev/null)
    if [ -n "$NEXT" ]; then
      echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"decision\":\"allow\",\"message\":\"Context saved! ${NEXT}\"}}"
    fi
    ;;
  *cc-flow*scan*--create*|*cc_flow*scan*--create*)
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Scan complete! Next: cc-flow auto run — start fixing, or cc-flow graph — see dependency map."}}'
    ;;
  *cc-flow*start*|*cc_flow*start*)
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Task started! Read the spec, implement, then cc-flow done <id> when verified."}}'
    ;;
esac

exit 0
