---
description: "Development workflow enforcement — required sequences, gates, and context protocol"
alwaysApply: true
---

# Workflow Rules

## Feature Development (required sequence)

```
/cc-brainstorm → /cc-plan → /cc-tdd → /cc-refine → /cc-review → /cc-commit
```

- DO NOT skip brainstorming for new features
- DO NOT write production code before a failing test
- DO NOT commit without verification (lint + type + test)
- DO NOT claim completion without evidence

## Bug Fix (required sequence)

```
/cc-debug (4 phases) → fix → test → /cc-commit
```

- DO NOT guess fixes — investigate root cause first
- DO NOT skip creating a regression test

## Hotfix (fast-track for ≤10 line changes)

```
implement → /cc-review (1 loop) → /cc-commit
```

- Skip brainstorm/plan for trivial changes (typo, config, revert)
- Still MUST run verification before commit
- Use: `cc-flow go "hotfix: description"`

## Code Review (required gates)

- **SHIP**: no critical/high issues → proceed to commit
- **NEEDS_WORK**: auto-fix → re-review (max 3 loops)
- **MAJOR_RETHINK**: STOP → discuss with user, do NOT continue

## Enforceable Gates

### Before Commit
1. Verification MUST pass: `cc-flow verify` (lint + type + test)
2. If in a chain: all prior steps MUST have saved context
3. If review was done: verdict MUST be SHIP

### Before Push
1. All tests pass locally
2. Diff stats reviewed (pre-push hook shows summary)
3. No secrets in staged files (.env, credentials, tokens)

### Before Deploy
1. `cc-flow skill check-deps --skill cc-deploy` passes
2. Readiness audit score ≥ 70
3. All chain steps completed (no partial chains)

### After Chain Completion
1. Record learning: `cc-flow learn --task "..." --outcome ...`
2. Chain metrics auto-recorded via `cc-flow chain advance`
3. Clear skill context if no longer needed: `cc-flow skill ctx clear`

## Dependency Check Protocol

Before starting a skill that DEPENDS ON another:
```bash
cc-flow skill check-deps --skill <skill-name>
```

If dependencies are missing, either:
1. Run the predecessor skill first
2. Manually provide context: `cc-flow skill ctx save <predecessor> --data '{}'`

## Skill Context Protocol

After completing any skill that FLOWS INTO another:
```bash
cc-flow skill ctx save <skill-name> --data '{"key": "value", ...}'
```

Before starting a skill that DEPENDS ON another:
```bash
cc-flow skill ctx load <predecessor-skill>
```

When working in a chain (`cc-flow chain run <name>`), after each step:
```bash
cc-flow chain advance --data '{"key": "value"}'
```

Query the flow graph:
```bash
cc-flow skill next                        # based on current active skill
cc-flow skill next --skill cc-brainstorm  # explicit skill name
cc-flow skill graph --for cc-plan         # see a skill's connections
```

## Auto-Learn

After completing any workflow, record the learning:
```bash
cc-flow learn --task "..." --outcome success --approach "..." --lesson "..."
```

Chain completion auto-suggests the learn command. Follow it.
