---
description: >
  Dispatch 2+ independent tasks to concurrent agents with isolated context. No shared state needed.
  TRIGGER: 'parallel', 'concurrent', 'multiple agents', 'fan-out', 'simultaneous'.
  DEPENDS ON: cc-teams.
---

Activate the cc-parallel-agents skill.

## Pattern

Use **multiple Agent tool calls in ONE message** to run them concurrently.

### When to Use
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood alone
- No shared state between investigations

### When NOT to Use
- Failures are related (fix one might fix others)
- Agents would edit same files (use worktree isolation)

## Dispatch

1. **Identify** independent domains
2. **Create** focused agent prompts (specific scope, clear goal, constraints)
3. **Dispatch** in parallel (multiple Agent calls in one message)
4. **Review** and integrate results
5. **Verify** no conflicts, run full test suite
