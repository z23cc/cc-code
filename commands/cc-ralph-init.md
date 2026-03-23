---
description: >
  Initialize Ralph autonomous harness in the current project.
  TRIGGER: 'ralph init', 'setup ralph', 'autonomous setup', '初始化 ralph'.
---

Activate the cc-ralph skill. Create the Ralph harness scaffold:

## Steps

1. Create directory structure:

```bash
mkdir -p scripts/ralph/runs scripts/ralph/hooks
```

2. Write `scripts/ralph/config.env` with defaults
3. Write `scripts/ralph/ralph.sh` (main loop)
4. Write `scripts/ralph/ralph_once.sh` (single iteration test)
5. Write `scripts/ralph/hooks/ralph-guard.py` (safety hooks)
6. Write prompt templates: `prompt_plan.md`, `prompt_work.md`, `prompt_completion.md`
7. Make scripts executable: `chmod +x scripts/ralph/*.sh`
8. Add to `.gitignore`: `scripts/ralph/runs/`

## Prompt Templates

### prompt_work.md

```markdown
You are executing a task autonomously. Use cc-code skills.

TASK_ID: {{TASK_ID}}
EPIC_ID: {{EPIC_ID}}
REVIEW_MODE: {{WORK_REVIEW}}
RECEIPT_PATH: {{RECEIPT_PATH}}

Steps:
1. Read task spec: cc-flow show {{TASK_ID}}
2. Implement using /cc-tdd workflow
3. Verify: cc-flow verify
4. If REVIEW_MODE != none: run /cc-review with {{WORK_REVIEW}} backend
5. Mark done: cc-flow done {{TASK_ID}} --summary "..."
6. Write receipt to {{RECEIPT_PATH}}
```

### prompt_plan.md

```markdown
Review the epic plan before implementation begins.

EPIC_ID: {{EPIC_ID}}
REVIEW_MODE: {{PLAN_REVIEW}}
RECEIPT_PATH: {{RECEIPT_PATH}}

Steps:
1. Read epic spec: cc-flow show {{EPIC_ID}}
2. Review using /cc-review with {{PLAN_REVIEW}} backend
3. If NEEDS_WORK: fix spec, re-review
4. Write receipt to {{RECEIPT_PATH}}
```

### prompt_completion.md

```markdown
Verify all tasks fully implement the epic spec.

EPIC_ID: {{EPIC_ID}}
REVIEW_MODE: {{COMPLETION_REVIEW}}
RECEIPT_PATH: {{RECEIPT_PATH}}

Steps:
1. Run /cc-epic-review {{EPIC_ID}}
2. If NEEDS_WORK: implement missing requirements, re-review
3. Write receipt to {{RECEIPT_PATH}}
```

## After Setup

```bash
# Test single iteration
bash scripts/ralph/ralph_once.sh

# Full autonomous run
bash scripts/ralph/ralph.sh

# Watch mode
bash scripts/ralph/ralph.sh --watch
```
