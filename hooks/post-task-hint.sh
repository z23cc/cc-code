#!/bin/bash
# PostToolUse hook: after cc-flow done runs, suggest next steps.
# Reads tool input JSON from stdin.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Detect cc-flow done
case "$COMMAND" in
  *"cc-flow"*"done"*|*"cc-flow.py"*"done"*)
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Task done! Consider: (1) cc-flow learn to record what worked, (2) cc-flow next for the next task, (3) /commit if ready to commit."}}'
    ;;
  *"cc-flow"*"scan"*"--create"*|*"cc-flow.py"*"scan"*"--create"*)
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"Scan complete! Run cc-flow auto run to start fixing, or cc-flow graph to see the dependency map."}}'
    ;;
esac

exit 0
