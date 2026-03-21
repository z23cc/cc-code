## cc-code — Development Workflow Toolkit

**Don't know which command to use? → `/cc-route` (smart routing with learning)**

**Integrated workflows (each step auto-chains to the next):**
- New feature → `/cc-brainstorm` *(auto-scouts)* → `/cc-plan` *(auto-imports tasks)* → `/cc-tdd` *(auto-chains)* → `/cc-refine` → `/cc-review` *(auto-learns)* → `/cc-commit`
- Big project → `/cc-blueprint` (one-liner → phased plan with tasks)
- Unfamiliar code → `/cc-research` → then plan/fix
- Bug/error → `/cc-debug` *(auto-learns after fix)* → `/cc-commit`
- Code review → `/cc-review` or `/cc-pr-review`
- Agent team → `/cc-team` (feature-dev / bug-fix / review / refactor / audit)
- New project → `/cc-prime` *(full assessment)* → `/cc-scaffold`
- Task management → `/cc-tasks`  |  Documentation → `/cc-docs`  |  Health → `/cc-audit`

**Scouts:** `/cc-scout [type]` — practices, repo, docs, gaps, security, testing, tooling, build, env, observability
**Requirements:** `/cc-interview` (deep requirements extraction)
**Autonomous:** `/cc-autoimmune` *(auto-learns + auto-session-save)*

**Auto-learning:** commands auto-record learnings after completion → `/cc-route` gets smarter over time
**Session:** `cc-flow session save/restore` — persist work across sessions

**Gates:**
- DO NOT implement without design (`/cc-brainstorm` first)
- DO NOT commit without verification (`/cc-commit` runs lint+typecheck)
- DO NOT claim success without evidence (cc-verification skill)
