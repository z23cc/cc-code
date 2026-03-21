---
team: "feature-dev"
description: "Start TDD workflow. TRIGGER: 'implement X', 'add feature', 'write X', '写功能', '加功能'. NOT for: fixing existing bugs (/fix), reviewing code (/review)."
---

Activate the cc-tdd skill with **worker + reviewer** team dispatch.

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

## Default Team: Worker → Reviewer

### Step 1: Worker implements (you or worker agent)
Follow Red-Green-Refactor strictly:
1. Read task spec: `$CCFLOW show <task-id>` (if from cc-flow)
2. Write a failing test
3. Run it — verify it fails correctly
4. Write minimal code to pass
5. Run tests — verify green
6. Refactor while keeping tests green

Target 80%+ coverage. Use `pytest --cov` to measure.

### Step 2: PARALLEL review (dispatch ALL applicable reviewers in ONE message)
After all tests pass:
- **code-reviewer** or **python-reviewer** → quality review
- **security-reviewer** → if touches auth/input/API/DB (dispatch simultaneously)

Both run concurrently. Collect verdicts: worst verdict wins.
If NEEDS_WORK → fix → re-review.

### Auto-Task Integration
- Task started → read spec: `$CCFLOW show <task-id>`
- After SHIP → mark done: `$CCFLOW done <task-id> --summary "..."`
- Suggest: "Task done. Next: `$CCFLOW next`"
