#!/usr/bin/env bash
# cc-code Ralph — Autonomous Execution Loop
# Usage: bash scripts/ralph/ralph.sh [--watch [verbose]]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Load config
source "$SCRIPT_DIR/config.env"

# CLI args
WATCH_MODE=""
[[ "${1:-}" == "--watch" ]] && WATCH_MODE="tool" && shift
[[ "${1:-}" == "verbose" ]] && WATCH_MODE="verbose" && shift

# cc-flow CLI
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT:-$SCRIPT_DIR/../../}/scripts/cc-flow.py"

# Run setup
RUN_ID="$(date -u +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | xxd -p)"
RUN_DIR="$SCRIPT_DIR/runs/$RUN_ID"
mkdir -p "$RUN_DIR/receipts"
ATTEMPTS_FILE="$RUN_DIR/attempts.json"
echo '{}' > "$ATTEMPTS_FILE"
PROGRESS="$RUN_DIR/progress.txt"

echo "# Ralph Run: $RUN_ID" > "$PROGRESS"
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$PROGRESS"
echo "---" >> "$PROGRESS"

# Timeout command detection
TIMEOUT_CMD=""
if command -v timeout &>/dev/null; then
  TIMEOUT_CMD="timeout --foreground"
elif command -v gtimeout &>/dev/null; then
  TIMEOUT_CMD="gtimeout --foreground"
else
  echo "warn: no timeout command found; worker timeout disabled" >&2
fi

# Signal handling
cleanup() {
  trap - SIGINT SIGTERM
  pkill -P $$ 2>/dev/null || true
  echo "Ralph stopped at iteration $iter" >> "$PROGRESS"
  exit 130
}
trap cleanup SIGINT SIGTERM

# --- Helpers ---

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$PROGRESS"; }

bump_attempts() {
  local task="$1"
  local current
  current=$(python3 -c "
import json, sys
f='$ATTEMPTS_FILE'
d=json.load(open(f))
d['$task']=d.get('$task',0)+1
json.dump(d,open(f,'w'))
print(d['$task'])
")
  echo "$current"
}

get_attempts() {
  python3 -c "
import json
d=json.load(open('$ATTEMPTS_FILE'))
print(d.get('$1',0))
"
}

verify_receipt() {
  local path="$1" expected_type="$2" expected_id="$3"
  [[ -f "$path" ]] || return 1
  python3 -c "
import json, sys
r=json.load(open('$path'))
if r.get('type')!='$expected_type' or r.get('id')!='$expected_id':
  sys.exit(1)
" 2>/dev/null
}

render_template() {
  local template="$1"
  sed \
    -e "s|{{TASK_ID}}|${TASK_ID:-}|g" \
    -e "s|{{EPIC_ID}}|${EPIC_ID:-}|g" \
    -e "s|{{WORK_REVIEW}}|${WORK_REVIEW}|g" \
    -e "s|{{PLAN_REVIEW}}|${PLAN_REVIEW}|g" \
    -e "s|{{COMPLETION_REVIEW}}|${COMPLETION_REVIEW}|g" \
    -e "s|{{RECEIPT_PATH}}|${RECEIPT_PATH:-}|g" \
    "$SCRIPT_DIR/$template"
}

maybe_close_epics() {
  local epics_json
  epics_json=$($CCFLOW epics 2>/dev/null || echo '{"epics":[]}')
  # Close epics where all tasks are done
  echo "$epics_json" | python3 -c "
import json, sys, subprocess
data = json.load(sys.stdin)
for e in data.get('epics', []):
  eid = e.get('id','')
  if not eid: continue
  tasks_out = subprocess.run(
    ['python3', '${CCFLOW#python3 }', 'tasks', '--epic', eid, '--json'],
    capture_output=True, text=True
  )
  try:
    tasks = json.loads(tasks_out.stdout).get('tasks', [])
  except: continue
  if tasks and all(t.get('status')=='done' for t in tasks):
    subprocess.run(['python3', '${CCFLOW#python3 }', 'epic', 'close', eid])
" 2>/dev/null || true
}

# --- Main Loop ---

iter=1
echo "Ralph starting: max_iterations=$MAX_ITERATIONS, review=$WORK_REVIEW"

while (( iter <= MAX_ITERATIONS )); do
  # Sentinel checks
  [[ -f "$RUN_DIR/STOP" ]] && { log "STOP sentinel detected"; break; }
  while [[ -f "$RUN_DIR/PAUSE" ]]; do
    echo "Paused (remove $RUN_DIR/PAUSE to resume)"
    sleep 5
  done

  # Close finished epics
  maybe_close_epics

  # Select next work item
  NEXT_JSON=$($CCFLOW next --json 2>/dev/null || echo '{"status":"none"}')
  STATUS=$(echo "$NEXT_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','none'))")
  EPIC_ID=$(echo "$NEXT_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('epic',''))")
  TASK_ID=$(echo "$NEXT_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('task',''))")

  log "iter $iter: status=$STATUS epic=$EPIC_ID task=$TASK_ID"

  [[ "$STATUS" != "none" ]] || { log "NO_WORK — all done"; break; }

  # Set receipt path
  case "$STATUS" in
    plan)       RECEIPT_PATH="$RUN_DIR/receipts/plan-${EPIC_ID}.json" ;;
    work)       RECEIPT_PATH="$RUN_DIR/receipts/impl-${TASK_ID}.json" ;;
    completion_review) RECEIPT_PATH="$RUN_DIR/receipts/completion-${EPIC_ID}.json" ;;
  esac

  # Select prompt template
  case "$STATUS" in
    plan)       TEMPLATE="prompt_plan.md" ;;
    work)       TEMPLATE="prompt_work.md" ;;
    completion_review) TEMPLATE="prompt_completion.md" ;;
  esac

  # Render prompt
  PROMPT=$(render_template "$TEMPLATE")

  # Export for guard hooks
  export EPIC_ID TASK_ID RECEIPT_PATH CC_RALPH=1

  # System prompt injection
  SYS_PROMPT="AUTONOMOUS MODE ACTIVE (CC_RALPH=1). CRITICAL: Execute commands exactly as shown. Verify outcomes. Never claim success without proof."

  # Spawn worker
  LOG_FILE="$RUN_DIR/iter-$(printf '%03d' $iter).log"

  CLAUDE_CMD=(claude -p --output-format stream-json --append-system-prompt "$SYS_PROMPT")
  [[ "${YOLO:-0}" == "1" ]] && CLAUDE_CMD+=(--dangerously-skip-permissions)

  if [[ -n "$TIMEOUT_CMD" ]]; then
    $TIMEOUT_CMD "$WORKER_TIMEOUT" "${CLAUDE_CMD[@]}" "$PROMPT" 2>&1 | tee "$LOG_FILE"
    WORKER_RC=${PIPESTATUS[0]}
  else
    "${CLAUDE_CMD[@]}" "$PROMPT" 2>&1 | tee "$LOG_FILE"
    WORKER_RC=${PIPESTATUS[0]}
  fi

  # Check timeout
  if [[ $WORKER_RC -eq 124 ]]; then
    log "iter $iter: TIMEOUT after ${WORKER_TIMEOUT}s"
  fi

  # Validate receipt
  RECEIPT_VALID=0
  case "$STATUS" in
    plan)
      verify_receipt "$RECEIPT_PATH" "plan_review" "$EPIC_ID" && RECEIPT_VALID=1 ;;
    work)
      verify_receipt "$RECEIPT_PATH" "impl_review" "$TASK_ID" && RECEIPT_VALID=1 ;;
    completion_review)
      verify_receipt "$RECEIPT_PATH" "completion_review" "$EPIC_ID" && RECEIPT_VALID=1 ;;
  esac

  log "iter $iter: receipt_valid=$RECEIPT_VALID worker_rc=$WORKER_RC"

  # Handle work phase: check if task actually done
  if [[ "$STATUS" == "work" && -n "$TASK_ID" ]]; then
    TASK_STATUS=$($CCFLOW show "$TASK_ID" --json 2>/dev/null \
      | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null \
      || echo "unknown")

    if [[ "$TASK_STATUS" != "done" ]]; then
      ATTEMPTS=$(bump_attempts "$TASK_ID")
      log "iter $iter: task not done (attempt $ATTEMPTS/$MAX_ATTEMPTS_PER_TASK)"

      if (( ATTEMPTS >= MAX_ATTEMPTS_PER_TASK )); then
        log "iter $iter: AUTO-BLOCK $TASK_ID after $ATTEMPTS attempts"
        $CCFLOW block "$TASK_ID" --reason "Auto-blocked after $ATTEMPTS attempts" 2>/dev/null || true
        cat > "$RUN_DIR/block-${TASK_ID}.md" << EOF
# Auto-blocked: $TASK_ID

Blocked after $ATTEMPTS failed attempts.
Last log: iter-$(printf '%03d' $iter).log
Review the log and fix manually.
EOF
      fi
    fi
  fi

  iter=$((iter + 1))
done

log "Ralph finished: $((iter - 1)) iterations"
echo ""
echo "Run complete: $RUN_DIR"
echo "Progress: $PROGRESS"
