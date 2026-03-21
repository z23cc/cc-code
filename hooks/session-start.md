## cc-code — Development Workflow Toolkit

**Workflows:**
- New feature → `/brainstorm` → `/plan` → `/tdd` → `/refine` → `/commit`
- Unfamiliar code → `/research` → then plan/fix
- Bug/error → `/debug` → `/fix` → `/commit`
- Code review → `/review` or `/pr-review`
- Performance → `/perf`
- Cleanup → `/simplify` → `/commit`
- New project → `/scaffold`
- Project health → `/audit` → feeds into `/autoimmune`
- Task management → `/tasks` (cc-flow CLI: list / create / start / done / progress)

**Autonomous improvement:**
- `/autoimmune scan` — auto-detect issues, generate tasks, then fix
- `/autoimmune` — pick from task list, implement, verify, commit/revert
- `/autoimmune test` — auto-fix lint + type + test errors
- `/autoimmune full` — scan → improve → fix (all three)

**Language detection:** Core skills auto-detect project language from pyproject.toml / package.json / go.mod / Cargo.toml and adapt verify/lint/test commands.

**Gates:**
- DO NOT implement without design approval (`/brainstorm` first)
- DO NOT commit without verification (`/commit` runs lint+typecheck)
- DO NOT claim success without test evidence (verification skill)
