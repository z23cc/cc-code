---
description: "Start TDD workflow. TRIGGER: 'implement X', 'add feature', 'write X', '写功能', '加功能'. NOT for: fixing existing bugs (/fix), reviewing code (/review)."
---

Activate the cc-tdd skill for the current task.

```bash
CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py"
```

Follow the Red-Green-Refactor cycle strictly:
1. Write a failing test for the desired behavior
2. Run it to verify it fails correctly
3. Write minimal code to make it pass
4. Run tests to verify they pass
5. Refactor while keeping tests green
6. Repeat

Target 80%+ coverage. Use `pytest --cov` to measure.

## Auto-Task Integration (NEW)

If working from a cc-flow task:
- Task is already started → read spec: `$CCFLOW show <task-id>`
- After all tests pass → mark done: `$CCFLOW done <task-id> --summary "[what was implemented]"`
- Auto-tracks diff (lines changed) and duration

## Auto-Chain After Green

After implementation is complete (all tests green):
- Suggest: "Tests pass. Run `/cc-refine` to check coverage/complexity, or `/cc-commit` if ready."
- If part of a plan with more tasks: "Task done. Next task: `$CCFLOW next`"
