## cc-code — Development Workflow Toolkit

**Don't know which command to use? → `/cc-route` (smart routing with learning)**

**Workflows:**
- New feature → `/cc-brainstorm` → `/cc-plan` → `/cc-tdd` → `/cc-refine` → `/cc-commit`
- Unfamiliar code → `/cc-research` → then plan/fix
- Bug/error → `/cc-debug` → `/cc-fix` → `/cc-commit`
- Code review → `/cc-review` or `/cc-pr-review`
- Agent team → `/cc-team` (feature-dev / bug-fix / review / refactor / audit)
- Performance → `/cc-perf`  |  Cleanup → `/cc-simplify`  |  New project → `/cc-scaffold`
- Task management → `/cc-tasks`  |  Documentation → `/cc-docs`  |  Health → `/cc-audit`

**Autonomous:** `/cc-autoimmune` (scan / code / test / full)

**Feedback loop:** `/cc-route` → execute → `cc-flow learn` → `cc-flow consolidate` → smarter routing

**Learning system:**
- `cc-flow route <task>` — uses past learnings + promoted patterns with confidence %
- `cc-flow learn` — record what worked (or didn't)
- `cc-flow consolidate` — promote recurring successes to patterns
- `cc-flow history` — task completion timeline + velocity trends
- `cc-flow config` — customize behavior (auto_consolidate, max_iterations, etc.)

**Gates:**
- DO NOT implement without design (`/cc-brainstorm` first)
- DO NOT commit without verification (`/cc-commit` runs lint+typecheck)
- DO NOT claim success without evidence (cc-verification skill)
