#!/bin/bash
# PostToolUse hook: track consecutive Bash failures for methodology switching.
# Counts failures → at threshold, triggers 3-engine diagnosis.

INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_result',{}).get('exit_code',0))" 2>/dev/null || echo "0")

if [ "$EXIT_CODE" != "0" ] && [ "$EXIT_CODE" != "" ]; then
  # Record failure
  cc-flow failure record --error "Bash exit code $EXIT_CODE" 2>/dev/null || true

  # Check if threshold reached
  STATE=$(cc-flow failure status 2>/dev/null || echo '{"count":0}')
  COUNT=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo "0")

  if [ "$COUNT" -ge 2 ]; then
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","decision":"allow","message":"⚠️ Multiple failures detected. Consider: cc-flow failure diagnose --goal \"your current goal\" (3-engine methodology switch)"}}'
  fi
else
  # Success → reset counter
  cc-flow failure reset 2>/dev/null || true
fi

exit 0
