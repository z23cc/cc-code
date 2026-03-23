#!/usr/bin/env bash
# cc-code worktree boundary guard — prevents editing files outside assigned worktree.
#
# Activation (any of these):
# 1. CC_WORKTREE_PATH env var (set by cc-work --branch=worktree)
# 2. Auto-detect: CWD is inside a git worktree (not the main checkout)
#
# Blocks Edit/Write operations that target paths outside the worktree.

set -euo pipefail

# Check explicit env var first
WORKTREE_PATH="${CC_WORKTREE_PATH:-}"

# Auto-detect: if CWD is a worktree, use CWD as boundary
if [[ -z "$WORKTREE_PATH" ]]; then
  GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || true)
  GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null || true)
  if [[ -n "$GIT_DIR" && -n "$GIT_COMMON" ]]; then
    GIT_DIR_REAL=$(cd "$GIT_DIR" 2>/dev/null && pwd -P || echo "$GIT_DIR")
    GIT_COMMON_REAL=$(cd "$GIT_COMMON" 2>/dev/null && pwd -P || echo "$GIT_COMMON")
    if [[ "$GIT_DIR_REAL" != "$GIT_COMMON_REAL" ]]; then
      # We're in a worktree — auto-set boundary to CWD
      WORKTREE_PATH="$(pwd)"
    fi
  fi
fi

# Not in a worktree → approve everything
[[ -n "$WORKTREE_PATH" ]] || { echo '{"decision":"approve"}'; exit 0; }

# Normalize worktree path (resolve symlinks)
WORKTREE_REAL="$(cd "$WORKTREE_PATH" 2>/dev/null && pwd -P || echo "$WORKTREE_PATH")"

# Read hook input from stdin
INPUT="$(cat)"

EVENT="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('event',''))" 2>/dev/null || echo "")"
TOOL="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")"

# Only check PreToolUse for Edit, Write, Bash
[[ "$EVENT" == "PreToolUse" ]] || { echo '{"decision":"approve"}'; exit 0; }

approve() {
  echo "{\"decision\":\"approve\"}"
  exit 0
}

block() {
  echo "{\"decision\":\"block\",\"reason\":\"$1\"}"
  exit 0
}

is_within() {
  local path="$1" base="$2"
  # Resolve the path (handle relative paths from CWD)
  local resolved
  if [[ "$path" = /* ]]; then
    resolved="$path"
  else
    resolved="$(pwd)/$path"
  fi
  # Normalize (remove .., //,  trailing /)
  resolved="$(python3 -c "import os.path; print(os.path.normpath('$resolved'))" 2>/dev/null || echo "$resolved")"

  # Check prefix
  case "$resolved" in
    "$base"/*|"$base") return 0 ;;
    *) return 1 ;;
  esac
}

# Also allow shared state dirs (.tasks/, .git/cc-flow-state/, .flow/)
is_allowed_shared() {
  local path="$1"
  case "$path" in
    */.tasks/*|*/.tasks) return 0 ;;
    */.git/cc-flow-state/*|*/.git/cc-flow-state) return 0 ;;
    */.flow/*|*/.flow) return 0 ;;
    */improvement-results.tsv) return 0 ;;
  esac
  return 1
}

case "$TOOL" in
  Edit|Write)
    FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")"
    if [[ -n "$FILE_PATH" ]]; then
      if is_within "$FILE_PATH" "$WORKTREE_REAL"; then
        approve
      elif is_allowed_shared "$FILE_PATH"; then
        approve
      else
        block "Path '$FILE_PATH' is outside assigned worktree '$WORKTREE_PATH'. Only edit files within the worktree or shared state dirs."
      fi
    fi
    ;;
  Bash)
    COMMAND="$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")"
    # Warn if cd'ing outside worktree (can't fully block bash, just warn)
    # Don't block — bash commands like git, cc-flow, etc. need to run anywhere
    ;;
esac

approve
