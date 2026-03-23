#!/usr/bin/env bash
# cc-code Ralph — Single iteration test
# Usage: bash scripts/ralph/ralph_once.sh
set -euo pipefail

export MAX_ITERATIONS=1
exec bash "$(dirname "${BASH_SOURCE[0]}")/ralph.sh" "$@"
