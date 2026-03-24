#!/usr/bin/env bash
# cc-code worktree manager — create, list, switch, remove, cleanup, copy-env, status
set -euo pipefail

cmd="${1:-}"
name="${2:-}"
base="${3:-}"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$repo_root" ]] || { echo "not a git repo" >&2; exit 1; }

worktrees_dir="$repo_root/.claude/worktrees"

fail() { echo "error: $*" >&2; exit 1; }

# --- Safety checks ---

assert_worktrees_dir() {
  if [[ -e "$worktrees_dir" && ! -d "$worktrees_dir" ]]; then
    fail ".claude/worktrees exists but is not a directory: $worktrees_dir"
  fi
  [[ ! -L "$worktrees_dir" ]] || fail ".claude/worktrees is a symlink; refusing: $worktrees_dir"
}

assert_safe_path() {
  local rel="$1" path="$worktrees_dir"
  local IFS='/'
  read -r -a parts <<< "$rel"
  for part in "${parts[@]}"; do
    [[ -n "$part" ]] || continue
    path="$path/$part"
    [[ ! -L "$path" ]] || fail "refusing symlink path: $path"
    [[ ! -e "$path" || -d "$path" ]] || fail "path exists but is not a directory: $path"
  done
}

validate_name() {
  local n="$1"
  [[ -n "$n" ]] || fail "missing name"
  [[ "$n" != -* ]] || fail "invalid name (cannot start with '-')"
  [[ "$n" != *".."* ]] || fail "invalid name (cannot contain '..')"
  git check-ref-format --branch "$n" >/dev/null 2>&1 || fail "invalid branch name: $n"
}

validate_base() {
  local b="$1"
  [[ -n "$b" ]] || fail "missing base"
  [[ "$b" != -* ]] || fail "invalid base (cannot start with '-')"
  [[ "$b" != *:* ]] || fail "invalid base (refspec ':' not allowed)"
  if git check-ref-format --branch "$b" >/dev/null 2>&1; then return 0; fi
  git rev-parse --verify -q "$b^{commit}" >/dev/null || fail "invalid base: $b"
}

# --- Helpers ---

has_origin() { git remote get-url origin >/dev/null 2>&1; }

default_base() {
  local b
  b="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || true)"
  [[ -z "$b" ]] || { echo "$b"; return; }
  b="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  [[ -z "$b" ]] || { echo "$b"; return; }
  git rev-parse --verify -q "main^{commit}" >/dev/null && { echo "main"; return; }
  git rev-parse --verify -q "master^{commit}" >/dev/null && { echo "master"; return; }
  echo "main"
}

ensure_dir() {
  assert_worktrees_dir
  mkdir -p "$worktrees_dir"
}

copy_env() {
  local target="$1"
  [[ -d "$target" ]] || fail "target does not exist: $target"
  [[ ! -L "$target" ]] || fail "target is a symlink: $target"
  shopt -s nullglob
  for f in "$repo_root"/.env*; do
    [[ -f "$f" && ! -L "$f" ]] || continue
    cp -n "$f" "$target/" || true
  done
  shopt -u nullglob
}

worktree_exists() {
  git worktree list --porcelain | sed -n 's/^worktree //p' | grep -Fqx -- "$1"
}

managed_worktrees() {
  git worktree list --porcelain | sed -n 's/^worktree //p' | grep "^${worktrees_dir}/" || true
}

# --- Nesting guard ---

assert_not_in_worktree() {
  local git_dir git_common
  git_dir="$(git rev-parse --git-dir 2>/dev/null || true)"
  git_common="$(git rev-parse --git-common-dir 2>/dev/null || true)"
  [[ -n "$git_dir" && -n "$git_common" ]] || return 0
  local git_dir_real git_common_real
  git_dir_real="$(cd "$git_dir" 2>/dev/null && pwd -P)"
  git_common_real="$(cd "$git_common" 2>/dev/null && pwd -P)"
  if [[ "$git_dir_real" != "$git_common_real" ]]; then
    fail "already inside a worktree ($(pwd)). Cannot create nested worktrees. Run from the main checkout instead."
  fi
}

# --- Commands ---

do_create() {
  [[ -n "$name" ]] || fail "usage: create <name> [base]"
  assert_not_in_worktree
  validate_name "$name"
  ensure_dir

  base="${base:-$(default_base)}"
  validate_base "$base"

  if has_origin && git check-ref-format --branch "$base" >/dev/null 2>&1; then
    git fetch --quiet origin "$base" 2>/dev/null || true
  fi

  assert_safe_path "$name"
  local target="${worktrees_dir}/${name}"
  mkdir -p "$(dirname "$target")"

  if worktree_exists "$target"; then
    echo "worktree already exists: $target"
    exit 0
  fi

  local start_point="$base"
  if git rev-parse --verify -q "origin/$base^{commit}" >/dev/null; then
    start_point="origin/$base"
  fi
  git rev-parse --verify -q "$start_point^{commit}" >/dev/null || fail "base does not resolve: $start_point"

  if git show-ref --verify --quiet "refs/heads/$name"; then
    git worktree add -- "$target" "$name"
  else
    git worktree add -b "$name" -- "$target" "$start_point"
  fi

  copy_env "$target"

  # Auto-install frontend deps if package.json exists
  if [[ -f "$target/package.json" ]]; then
    echo "detected package.json — installing node_modules..."
    if command -v npm >/dev/null 2>&1; then
      (cd "$target" && npm install --no-audit --no-fund --loglevel=error 2>&1) || true
      echo "node_modules installed in worktree"
    else
      echo "warning: npm not found — run 'npm install' in worktree manually"
    fi
  fi

  # Auto-install Python deps if requirements.txt or pyproject.toml with deps
  if [[ -f "$target/requirements.txt" ]]; then
    echo "detected requirements.txt — checking Python deps..."
    if command -v pip3 >/dev/null 2>&1; then
      (cd "$target" && pip3 install -r requirements.txt --quiet 2>&1) || true
    fi
  fi

  echo "created: $target"
}

do_list() {
  echo "=== All worktrees ==="
  git worktree list
  echo ""
  local managed
  managed="$(managed_worktrees)"
  if [[ -n "$managed" ]]; then
    echo "=== Managed (.claude/worktrees/) ==="
    echo "$managed"
  else
    echo "No managed worktrees under .claude/worktrees/"
  fi
}

do_switch() {
  [[ -n "$name" ]] || fail "usage: switch <name>"
  validate_name "$name"
  assert_worktrees_dir
  assert_safe_path "$name"
  local target="${worktrees_dir}/${name}"
  [[ -d "$target" ]] || fail "no such worktree dir: $target"
  worktree_exists "$target" || fail "not a registered worktree: $target"
  echo "$target"
}

do_copy_env() {
  [[ -n "$name" ]] || fail "usage: copy-env <name>"
  validate_name "$name"
  assert_worktrees_dir
  assert_safe_path "$name"
  local target="${worktrees_dir}/${name}"
  worktree_exists "$target" || fail "not a registered worktree: $target"
  copy_env "$target"
  echo "copied .env* to $target"
}

do_remove() {
  [[ -n "$name" ]] || fail "usage: remove <name>"
  validate_name "$name"
  assert_worktrees_dir
  assert_safe_path "$name"
  local target="${worktrees_dir}/${name}"
  worktree_exists "$target" || fail "not a registered worktree: $target"
  git worktree remove -- "$target" || fail "failed to remove: $target (worktree not clean?)"
  echo "removed: $target"
}

do_cleanup() {
  assert_worktrees_dir
  local managed
  managed="$(managed_worktrees)"
  if [[ -z "$managed" ]]; then
    echo "no managed worktrees to clean up"
    git worktree prune
    exit 0
  fi

  echo "managed worktrees:"
  echo "$managed"
  echo ""

  local failed=0
  while IFS= read -r wt; do
    local wt_name="${wt#${worktrees_dir}/}"
    if git worktree remove -- "$wt" 2>/dev/null; then
      echo "removed: $wt_name"
    else
      echo "skipped (not clean): $wt_name" >&2
      failed=1
    fi
  done <<< "$managed"

  git worktree prune
  exit "$failed"
}

do_status() {
  local count=0 dirty=0
  local managed
  managed="$(managed_worktrees)"
  [[ -n "$managed" ]] || { echo "no managed worktrees"; exit 0; }

  while IFS= read -r wt; do
    count=$((count + 1))
    if [[ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]]; then
      dirty=$((dirty + 1))
      echo "dirty: ${wt#${worktrees_dir}/}"
    else
      echo "clean: ${wt#${worktrees_dir}/}"
    fi
  done <<< "$managed"

  echo ""
  echo "total: $count, dirty: $dirty"
}

# --- Dispatch ---

case "$cmd" in
  create)   do_create ;;
  list)     do_list ;;
  switch)   do_switch ;;
  remove)   do_remove ;;
  copy-env) do_copy_env ;;
  cleanup)  do_cleanup ;;
  status)   do_status ;;
  *)        fail "commands: create | list | switch | remove | cleanup | copy-env | status" ;;
esac
