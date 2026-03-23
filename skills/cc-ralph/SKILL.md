---
name: cc-ralph
description: >
  Autonomous execution loop with multi-model review gates and receipt-based
  proof-of-work. Spawns fresh Claude sessions per iteration. Fully unattended.
  TRIGGER: 'ralph', 'autonomous mode', 'unattended run', 'run all tasks autonomously',
  '自治模式', '无人值守', '自动跑任务', '自动执行'.
  NOT FOR: interactive development — use cc-work instead.
---

# Ralph — Autonomous Execution Loop

## Architecture

Ralph is an **external shell loop** that spawns fresh Claude sessions per iteration.
Each iteration picks the next work item, executes it with review gates, and validates
completion via receipts.

```
ralph.sh (outer loop)
  ├─ Iteration 1: claude -p "plan-review fn-1"   → receipt ✓
  ├─ Iteration 2: claude -p "work fn-1.1"        → receipt ✓
  ├─ Iteration 3: claude -p "work fn-1.2"        → receipt ✓
  ├─ Iteration 4: claude -p "epic-review fn-1"   → receipt ✓
  └─ done (NO_WORK)
```

**Key design**: Fresh context per iteration prevents context pollution, stale
assumptions, and accumulated errors. Each Claude session re-anchors from `.tasks/`.

## Setup

```bash
/cc-ralph-init
```

This creates:

```
scripts/ralph/
├── ralph.sh              # Main loop
├── ralph_once.sh         # Single iteration (for testing)
├── config.env            # All settings
├── prompt_plan.md        # Plan review prompt template
├── prompt_work.md        # Work prompt template
├── prompt_completion.md  # Completion review prompt template
├── runs/                 # Run artifacts
└── hooks/
    └── ralph-guard.py    # Safety hooks (FLOW_RALPH=1)
```

## Running

```bash
# Test single iteration
bash scripts/ralph/ralph_once.sh

# Full autonomous loop
bash scripts/ralph/ralph.sh

# Watch mode (see tool calls in real-time)
bash scripts/ralph/ralph.sh --watch

# Verbose watch (full output)
bash scripts/ralph/ralph.sh --watch verbose

# Scope to specific epics
EPICS=epic-1,epic-2 bash scripts/ralph/ralph.sh
```

## Configuration (config.env)

```bash
# Review backends (agent | rp | codex | none)
PLAN_REVIEW=agent              # How to review epic plans
WORK_REVIEW=agent              # How to review implementations
COMPLETION_REVIEW=agent        # How to review epic completeness
REQUIRE_PLAN_REVIEW=0          # 1 = block work until plans reviewed

# Loop controls
MAX_ITERATIONS=25              # Total iterations before exit
MAX_ATTEMPTS_PER_TASK=5        # Retries before auto-blocking task
MAX_REVIEW_ITERATIONS=3        # Fix+re-review cycles per review
WORKER_TIMEOUT=3600            # Seconds before killing stuck worker

# Branch strategy
BRANCH_MODE=new                # new | current | worktree

# Execution
YOLO=1                         # Skip permission prompts (required for unattended)
EPICS=                         # Comma-separated epic IDs (empty = all)
```

## Loop Logic

```bash
while (( iter <= MAX_ITERATIONS )); do
  # 1. Check pause/stop sentinels
  [[ -f $RUN_DIR/STOP ]] && exit 0
  while [[ -f $RUN_DIR/PAUSE ]]; do sleep 5; done

  # 2. Close finished epics
  for epic in $(epics_with_all_tasks_done); do
    cc-flow epic close $epic
  done

  # 3. Select next work item
  NEXT=$(cc-flow next --json)
  STATUS=$(echo $NEXT | jq -r .status)  # plan | work | completion_review | none

  [[ "$STATUS" == "none" ]] && break  # All done

  # 4. Set receipt path
  RECEIPT="$RUN_DIR/receipts/${STATUS}-${ID}.json"

  # 5. Render prompt template
  PROMPT=$(render_template prompt_${STATUS}.md)

  # 6. Spawn fresh Claude session
  timeout $WORKER_TIMEOUT claude -p \
    --output-format stream-json \
    --append-system-prompt "AUTONOMOUS MODE ACTIVE (CC_RALPH=1)..." \
    "$PROMPT" | tee "$RUN_DIR/iter-$(printf '%03d' $iter).log"

  # 7. Validate receipt
  verify_receipt "$RECEIPT" "$STATUS" "$ID"

  # 8. Handle result
  if task_not_done; then
    bump_attempts $TASK_ID
    if attempts >= MAX_ATTEMPTS_PER_TASK; then
      cc-flow block $TASK_ID --reason "Auto-blocked after $MAX_ATTEMPTS_PER_TASK attempts"
    fi
  fi

  iter=$((iter + 1))
done
```

## Work Selector

`cc-flow next --json` returns the next work item:

```json
{
  "status": "plan|work|completion_review|none",
  "epic": "epic-1",
  "task": "epic-1.3"
}
```

**Selection priority:**
1. Epic needs plan review → `status: "plan"`
2. Task is ready → `status: "work"`
3. All tasks done, epic needs completion review → `status: "completion_review"`
4. Nothing to do → `status: "none"`

## Quality Gates

| Gate | When | Backend config | Receipt required |
|------|------|---------------|-----------------|
| Plan review | Before first task | `PLAN_REVIEW` | Yes (if enabled) |
| Impl review | After each task | `WORK_REVIEW` | Yes (if enabled) |
| Completion review | After all tasks done | `COMPLETION_REVIEW` | Yes (if enabled) |

## Receipt System

Every review produces a JSON receipt (proof-of-work):

```json
{
  "type": "impl_review",
  "id": "epic-1.3",
  "mode": "agent",
  "verdict": "SHIP",
  "timestamp": "2026-03-23T10:30:00Z"
}
```

**No receipt = no progress**. Ralph retries until receipt exists.

### Receipt Storage

```
scripts/ralph/runs/<run-id>/
├── receipts/
│   ├── plan-epic-1.json
│   ├── impl-epic-1.1.json
│   ├── impl-epic-1.2.json
│   └── completion-epic-1.json
├── iter-001.log
├── iter-002.log
├── progress.txt          # Append-only run log
├── attempts.json         # {task-id: retry-count}
└── block-epic-1.3.md    # Context dump for auto-blocked tasks
```

## Autonomous Mode System Prompt

Injected into every worker session:

```
AUTONOMOUS MODE ACTIVE (CC_RALPH=1). You are running unattended. CRITICAL RULES:
1. EXECUTE COMMANDS EXACTLY as shown in prompts. Do not improvise.
2. VERIFY OUTCOMES by running verification commands (cc-flow show, git status).
3. NEVER CLAIM SUCCESS without proof. If cc-flow done was not run, the task is NOT done.
4. USE SKILLS AS SPECIFIED — invoke /cc-work, /cc-epic-review as directed.
5. Write receipt JSON EXACTLY as specified.
Violations break automation and leave incomplete work. Be precise, not creative.
```

## Safety Hooks (ralph-guard.py)

When `CC_RALPH=1`:

**PreToolUse guards:**
- Block `cc-flow done` without `--summary` and `--evidence`
- Block receipt writes before review succeeds
- Block editing of ralph-guard.py, hooks.json (self-modification prevention)

**PostToolUse tracking:**
- Track `cc-flow done` calls (which tasks completed)
- Extract verdict tags from review output
- Capture NEEDS_WORK feedback for learning system

**Stop guard:**
- Block session exit if receipt path set but file missing

## Sentinel Files (Pause/Stop)

```bash
# Pause at next iteration boundary
touch scripts/ralph/runs/<run-id>/PAUSE

# Resume
rm scripts/ralph/runs/<run-id>/PAUSE

# Stop gracefully
touch scripts/ralph/runs/<run-id>/STOP
```

## Retry & Auto-Blocking

```
Attempt 1: Worker implements task → tests fail → retry
Attempt 2: Worker re-implements → review NEEDS_WORK → fix loop → retry
Attempt 3: Worker tries again → partial completion → retry
Attempt 4: Still failing → retry
Attempt 5: MAX_ATTEMPTS reached → auto-block task
  → Write block-<task-id>.md with context
  → cc-flow block <task-id>
  → Move to next task
```

## Differences from cc-flow auto (Autoimmune)

| Aspect | cc-flow auto | Ralph |
|--------|-------------|-------|
| Session | Same session, growing context | Fresh per iteration |
| Review | Self-review (verify command) | Multi-model review gates |
| Proof | Test pass/fail | Receipt-based evidence |
| Retry | Simple revert + retry | Tracked attempts + auto-block |
| Scope | Improvement tasks | Full epic execution |
| Monitoring | Summary command | Watch mode + progress file |
| Safety | Revert on fail | Guard hooks + sentinels |

## Related Skills

- **cc-review-backend** — review backend configuration and routing
- **cc-work** — the execution pipeline Ralph invokes per task
- **cc-epic-review** — completion verification Ralph invokes per epic
- **cc-worktree** — worktree isolation for parallel workers
- **cc-autoimmune** — simpler single-session improvement loop
