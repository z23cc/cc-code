---
name: parallel-agents
description: "Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies."
---

# Dispatching Parallel Agents

Delegate tasks to specialized agents with isolated context. Craft precise instructions — agents should never inherit your session history.

## When to Use

**Use when:**
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood alone
- No shared state between investigations

**Don't use when:**
- Failures are related (fix one might fix others)
- Need to understand full system state
- Agents would edit same files

## The Pattern

### 1. Identify Independent Domains
Group failures by what's broken — each domain is independent.

### 2. Create Focused Agent Tasks
Each agent gets:
- **Specific scope:** One test file or subsystem
- **Clear goal:** Make these tests pass
- **Constraints:** Don't change unrelated code
- **Expected output:** Summary of findings and fixes

### 3. Dispatch in Parallel

```python
# Example: 3 independent failures
Agent("Fix tests/test_auth.py failures")
Agent("Fix tests/test_api.py failures")
Agent("Fix tests/test_models.py failures")
# All three run concurrently
```

### 4. Review and Integrate
- Read each summary
- Verify fixes don't conflict
- Run full test suite
- Integrate all changes

## Agent Prompt Structure

Good agent prompts are:
1. **Focused** — one clear problem domain
2. **Self-contained** — all context needed
3. **Specific about output** — what should the agent return?

Example:
```markdown
Fix the 3 failing tests in tests/test_auth.py:

1. "test_login_invalid_password" - expects 401, gets 500
2. "test_token_expiry" - token not expiring
3. "test_rate_limiting" - rate limit not enforced

Your task:
1. Read the test file and understand what each test verifies
2. Identify root cause
3. Fix the minimal code needed
4. Return: Summary of root cause and changes made
```

## Common Mistakes

- **Too broad:** "Fix all the tests" — agent gets lost
- **No context:** "Fix the race condition" — agent doesn't know where
- **No constraints:** Agent might refactor everything
- **Vague output:** "Fix it" — you don't know what changed

## Verification

After agents return:
1. Review each summary
2. Check for conflicts (same files edited)
3. Run full test suite
4. Spot check agent changes
