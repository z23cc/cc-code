#!/bin/bash
# PreToolUse hook: when Bash runs a git commit, remind about verification.
# Reads tool input JSON from stdin.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only intercept git commit commands
case "$COMMAND" in
  *"git commit"*)
    # Check if it's just a git log/status command that happens to contain "commit"
    case "$COMMAND" in
      *"git commit"*) true ;;
      *) exit 0 ;;
    esac
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","decision":"allow","message":"Quality gate: Ensure lint + type check + tests pass before committing. Run verification first if not already done."}}'
    ;;
esac

exit 0
