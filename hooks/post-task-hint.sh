#!/bin/bash
# PostToolUse hook: after cc-flow commands, suggest next steps.
# Reads tool input JSON from stdin.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  *cc-flow*done*|*cc_flow*done*)
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Task done! Next: (1) cc-flow learn — record what worked, (2) cc-flow next — pick next task, (3) /cc-commit — if ready."}}'
    ;;
  *cc-flow*scan*--create*|*cc_flow*scan*--create*)
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Scan complete! Next: cc-flow auto run — start fixing, or cc-flow graph — see dependency map."}}'
    ;;
  *cc-flow*start*|*cc_flow*start*)
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Task started! Read the spec, implement, then cc-flow done <id> when verified."}}'
    ;;
esac

exit 0
