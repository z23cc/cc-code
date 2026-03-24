#!/bin/bash
# PreToolUse hook: quality gate before git commit.
# Behavior depends on CC_HOOK_PROFILE:
#   minimal  → allow (no check)
#   standard → allow + warn message (default)
#   strict   → block if verify hasn't passed recently
#
# Reads tool input JSON from stdin.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

PROFILE="${CC_HOOK_PROFILE:-standard}"

# Match git commit (handles: git commit, git -c x commit, git  commit)
case "$COMMAND" in
  *git*commit*)
    # Exclude git log/show/rev-parse (contain "commit" but aren't commits)
    case "$COMMAND" in
      *"git log"*|*"git show"*|*"git rev-parse"*) ;;
      *)
        case "$PROFILE" in
          minimal)
            # No enforcement
            ;;
          strict)
            # Check if cc-flow verify passed recently (within last 5 minutes)
            VERIFY_LOG=".tasks/last_verify.json"
            if [ -f "$VERIFY_LOG" ]; then
              AGE=$(python3 -c "
import json, time
from datetime import datetime, timezone
try:
    d = json.load(open('$VERIFY_LOG'))
    ts = d.get('timestamp','')
    dt = datetime.fromisoformat(ts.replace('Z','+00:00'))
    print(int(time.time() - dt.timestamp()))
except: print(9999)
" 2>/dev/null)
              if [ "${AGE:-9999}" -le 300 ]; then
                echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","decision":"allow","message":"[STRICT] Verification passed recently. Commit allowed."}}'
              else
                echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","decision":"block","reason":"[STRICT] Verification is stale (>5min). Run cc-flow verify before committing."}}'
              fi
            else
              echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","decision":"block","reason":"[STRICT] No verification record found. Run cc-flow verify before committing."}}'
            fi
            ;;
          *)
            # standard: warn but allow
            echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","decision":"allow","message":"Quality gate: Ensure lint + type check + tests pass before committing. Run cc-flow verify first if not already done."}}'
            ;;
        esac
        ;;
    esac
    ;;
esac

exit 0
