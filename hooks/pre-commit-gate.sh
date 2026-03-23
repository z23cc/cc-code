#!/bin/bash
# PreToolUse hook: when Bash runs a git commit, remind about verification.
# Reads tool input JSON from stdin.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Match git commit (handles: git commit, git -c x commit, git  commit)
case "$COMMAND" in
  *git*commit*)
    # Exclude git log --oneline (contains "commit" in output context) and git show commit
    case "$COMMAND" in
      *"git log"*|*"git show"*|*"git rev-parse"*) ;;
      *)
        echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","decision":"allow","message":"Quality gate: Ensure lint + type check + tests pass before committing. Run cc-flow verify first if not already done."}}'
        ;;
    esac
    ;;
esac

exit 0
