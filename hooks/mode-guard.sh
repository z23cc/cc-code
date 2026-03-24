#!/usr/bin/env bash
# cc-code mode guard — session-scoped safety modes (careful / freeze / guard).
#
# Reads ~/.cc-code/modes.json and enforces:
#   careful: warn on destructive operations (rm -rf, DROP TABLE, git push -f, git reset --hard)
#   freeze:  block Edit/Write outside the frozen directory
#   guard:   both careful + freeze
#
# Hook output: JSON decision (approve, approve+warn, or block)

set -euo pipefail

MODES_FILE="$HOME/.cc-code/modes.json"
PROFILE="${CC_HOOK_PROFILE:-standard}"

# In minimal profile, skip all mode checks
[[ "$PROFILE" == "minimal" ]] && { echo '{"decision":"approve"}'; exit 0; }

# Fast exit if no modes file
[[ -f "$MODES_FILE" ]] || { echo '{"decision":"approve"}'; exit 0; }

# Read modes
MODES="$(cat "$MODES_FILE")"
CAREFUL="$(echo "$MODES" | python3 -c "import sys,json; print(json.load(sys.stdin).get('careful',False))" 2>/dev/null || echo "False")"
FREEZE="$(echo "$MODES" | python3 -c "import sys,json; print(json.load(sys.stdin).get('freeze',False))" 2>/dev/null || echo "False")"
FREEZE_DIR="$(echo "$MODES" | python3 -c "import sys,json; print(json.load(sys.stdin).get('freeze_dir',''))" 2>/dev/null || echo "")"

# Nothing enabled → approve
[[ "$CAREFUL" == "True" || "$FREEZE" == "True" ]] || { echo '{"decision":"approve"}'; exit 0; }

# Read hook input from stdin
INPUT="$(cat)"

TOOL="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")"
EVENT="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('event',''))" 2>/dev/null || echo "")"

[[ "$EVENT" == "PreToolUse" ]] || { echo '{"decision":"approve"}'; exit 0; }

approve() {
  echo '{"decision":"approve"}'
  exit 0
}

warn() {
  local msg="$1"
  # Escape for JSON
  msg="$(echo "$msg" | sed 's/"/\\"/g')"
  echo "{\"decision\":\"approve\",\"message\":\"[MODE-GUARD] $msg\"}"
  exit 0
}

block() {
  local msg="$1"
  msg="$(echo "$msg" | sed 's/"/\\"/g')"
  echo "{\"decision\":\"block\",\"reason\":\"[MODE-GUARD] $msg\"}"
  exit 0
}

# ── Careful mode: check Bash commands for destructive patterns ──
if [[ "$CAREFUL" == "True" && "$TOOL" == "Bash" ]]; then
  COMMAND="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")"

  # Check for destructive patterns
  # In strict profile, destructive ops are blocked. In standard, they warn.
  ENFORCE="warn"
  [[ "$PROFILE" == "strict" ]] && ENFORCE="block"

  if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--force\s+--recursive|-rf)'; then
    $ENFORCE "Careful mode: detected 'rm -rf' — destructive file deletion."
  fi

  if echo "$COMMAND" | grep -qiE 'DROP\s+TABLE'; then
    $ENFORCE "Careful mode: detected 'DROP TABLE' — destructive database operation."
  fi

  if echo "$COMMAND" | grep -qE 'git\s+push\s+(-[a-zA-Z]*f|--force)'; then
    $ENFORCE "Careful mode: detected 'git push -f' — force push can overwrite remote history."
  fi

  if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
    $ENFORCE "Careful mode: detected 'git reset --hard' — will discard all uncommitted changes."
  fi
fi

# ── Freeze mode: check Edit/Write target paths ──
if [[ "$FREEZE" == "True" && -n "$FREEZE_DIR" ]]; then
  case "$TOOL" in
    Edit|Write)
      FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")"

      if [[ -n "$FILE_PATH" ]]; then
        # Resolve to absolute path
        if [[ "$FILE_PATH" != /* ]]; then
          FILE_PATH="$(pwd)/$FILE_PATH"
        fi
        FILE_PATH="$(python3 -c "import os.path; print(os.path.normpath('$FILE_PATH'))" 2>/dev/null || echo "$FILE_PATH")"

        # Normalize freeze dir
        FREEZE_REAL="$(python3 -c "import os.path; print(os.path.normpath('$FREEZE_DIR'))" 2>/dev/null || echo "$FREEZE_DIR")"

        # Check if within frozen directory
        case "$FILE_PATH" in
          "$FREEZE_REAL"/*|"$FREEZE_REAL") approve ;;
          *)
            block "Freeze mode: edits are restricted to '$FREEZE_DIR'. File '$FILE_PATH' is outside the frozen directory."
            ;;
        esac
      fi
      ;;
    Bash)
      # In freeze mode, also warn on Bash commands that might write outside the dir
      # (Can't fully block bash, just warn for awareness)
      ;;
  esac
fi

approve
