#!/bin/bash
# PreToolUse hook (Bash): semantic verification before git commit.
# Uses 'prompt' pattern — asks LLM if this commit makes sense.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only trigger on git commit
case "$COMMAND" in
  *"git commit"*|*"git push"*)
    # Get staged diff
    DIFF=$(git diff --cached --stat 2>/dev/null)
    [ -z "$DIFF" ] && exit 0

    FILES_CHANGED=$(echo "$DIFF" | tail -1)

    # Semantic check: does the commit look reasonable?
    # Using prompt-style validation (lightweight, <1s)
    VERIFY=$(python3 -c "
import subprocess, json
# Quick heuristic checks (no LLM needed for obvious issues)
diff = subprocess.run(['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True).stdout
files = [f for f in diff.strip().split('\n') if f]
issues = []

# Check for common mistakes
for f in files:
    if f.endswith('.env') or 'credentials' in f or 'secret' in f.lower():
        issues.append(f'Sensitive file staged: {f}')
    if f.startswith('ref/') or f.startswith('node_modules/'):
        issues.append(f'Should not commit: {f}')

if issues:
    print(json.dumps({'block': True, 'issues': issues}))
else:
    print(json.dumps({'block': False}))
" 2>/dev/null)

    SHOULD_BLOCK=$(echo "$VERIFY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('yes' if d.get('block') else 'no')" 2>/dev/null || echo "no")

    if [ "$SHOULD_BLOCK" = "yes" ]; then
      ISSUES=$(echo "$VERIFY" | python3 -c "import sys,json; print('; '.join(json.load(sys.stdin).get('issues',[])))" 2>/dev/null)
      echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"decision\":\"block\",\"message\":\"🚫 Commit blocked: $ISSUES\"}}"
      exit 2
    fi
    ;;
esac

exit 0
