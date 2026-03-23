---
team: "feature-dev"
agent: "planner"
description: "Create implementation plan with TDD tasks. TRIGGER: 'plan this', 'how should we build', 'design X', '规划', '写计划'. Use AFTER brainstorming, BEFORE /tdd."
---

Create implementation plan with **Feature Dev team** support.

```bash
```

## Default Team: researcher → architect → planner

### Step 1: Dispatch researcher (if unfamiliar codebase)
- Scan related code, dependencies, test patterns
- Write findings to `/tmp/cc-team-research.md`

### Step 2: Dispatch architect (if architectural change)
- Review research findings
- Propose component structure, boundaries, interfaces
- Write architecture to `/tmp/cc-team-design.md`

### Step 3: Planner creates plan (you or planner agent)
1. Analyze spec + research + architecture findings
2. Map out file structure
3. Create bite-sized TDD tasks
4. Include exact file paths, code, and commands

## Auto-Import to cc-flow

After the plan is written:
1. Save to `docs/plans/YYYY-MM-DD-<feature>.md`
2. **Auto-import:**
   ```bash
   cc-flow epic import --file docs/plans/YYYY-MM-DD-<feature>.md --sequential
   ```
3. Auto-tag tasks based on content (api, database, auth, test)
4. Auto-select template per task (feature/bugfix/refactor/security)
5. Show dependency graph:
   ```bash
   cc-flow graph --format ascii
   ```
6. Confirm: "Plan imported as [epic-id] with [N] tasks. Start with `/cc-tdd`?"
