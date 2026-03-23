#!/bin/bash
# PreToolUse hook: remind to review before git push.
# Shows diff stats and asks to confirm.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

case "$COMMAND" in
  *git*push*)
    # Exclude git log/show that might contain "push" in output
    case "$COMMAND" in
      *"git log"*|*"git show"*) ;;
      *)
        # Get quick diff stats
        STATS=$(git diff --stat HEAD~1..HEAD 2>/dev/null | tail -1)
        BRANCH=$(git branch --show-current 2>/dev/null)
        echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"decision\":\"allow\",\"message\":\"Pushing ${BRANCH}: ${STATS}. Verify: tests pass, no debug code, no secrets.\"}}"
        ;;
    esac
    ;;
esac

exit 0
