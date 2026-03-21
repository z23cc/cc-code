## cc-code — Development Workflow Toolkit (Team-First)

**Don't know which command to use? → `/cc-route` (smart routing with learning)**

**All commands default to team dispatch (researcher → specialist → reviewer):**
- New feature → `/cc-brainstorm` *(feature-dev team)* → `/cc-plan` → `/cc-tdd` → `/cc-refine` → `/cc-review` *(review team)* → `/cc-commit`
- Bug/error → `/cc-debug` *(bug-fix team: researcher → fixer → reviewer)*
- Code quality → `/cc-simplify` *(refactor team)* | `/cc-perf` *(profiler team)*
- Health check → `/cc-audit` *(audit team)* | `/cc-prime` *(all 12 scouts)*
- Big project → `/cc-blueprint` | `/cc-interview` → `/cc-plan`
- Unfamiliar code → `/cc-research` *(research team)*

**Team dispatch = higher quality:** researcher finds context → specialist implements → reviewer verifies.

**Scouts:** `/cc-scout [type]` — practices, repo, docs, gaps, security, testing, tooling, build, env, observability
**Autonomous:** `/cc-autoimmune` *(auto-learns + auto-session-save)*
**Tasks:** `/cc-tasks` | `cc-flow dashboard` | `cc-flow graph`

**Auto-learning:** commands auto-record learnings → `/cc-route` gets smarter over time
**Session:** `cc-flow session save/restore` — persist work across sessions

**Gates:**
- DO NOT implement without design (`/cc-brainstorm` first)
- DO NOT commit without verification (`/cc-commit` runs lint+typecheck)
- DO NOT claim success without evidence (cc-verification skill)
