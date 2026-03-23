#!/bin/bash
# PostToolUse hook: after editing Python/JS/TS files, remind about verification.
# Lightweight — only triggers for source code edits, not docs.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0

# Only for source code files
case "$FILE_PATH" in
  *.py|*.ts|*.tsx|*.js|*.jsx|*.go|*.rs)
    # Check if cc-flow verify is available
    if command -v cc-flow >/dev/null 2>&1; then
      echo "Edited source file. Run 'cc-flow verify' before committing."
    fi
    ;;
esac

exit 0
