## cc-code — Development Workflow Toolkit

**Don't know which command to use? → `/route` (smart routing with learning)**

**Workflows:**
- New feature → `/brainstorm` → `/plan` → `/tdd` → `/refine` → `/commit`
- Unfamiliar code → `/research` → then plan/fix
- Bug/error → `/debug` → `/fix` → `/commit`
- Code review → `/review` or `/pr-review`
- Agent team → `/team` (feature-dev / bug-fix / review / refactor / audit)
- Performance → `/perf`  |  Cleanup → `/simplify`  |  New project → `/scaffold`
- Task management → `/tasks`  |  Documentation → `/docs`  |  Health → `/audit`

**Autonomous:** `/autoimmune` (scan / code / test / full)

**Feedback loop:** `/route` → execute → `cc-flow learn` → `cc-flow consolidate` → smarter routing

**Learning system:**
- `cc-flow route <task>` — uses past learnings + promoted patterns with confidence %
- `cc-flow learn` — record what worked (or didn't)
- `cc-flow consolidate` — promote recurring successes to patterns
- `cc-flow history` — task completion timeline + velocity trends
- `cc-flow config` — customize behavior (auto_consolidate, max_iterations, etc.)

**Gates:**
- DO NOT implement without design (`/brainstorm` first)
- DO NOT commit without verification (`/commit` runs lint+typecheck)
- DO NOT claim success without evidence (verification skill)
