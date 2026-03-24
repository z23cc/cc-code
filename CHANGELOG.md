# Changelog

## [5.25.0] - 2026-03-25
### Added
- **Real multi-engine code review** (`cc-flow multi-review`) — parallel subprocess dispatch:
  - 4 engines: Agent (Claude lint), Gemini (`gemini -p`), Codex (`codex review`), RP (`rp builder --type review`)
  - ThreadPoolExecutor parallel execution with per-engine timeouts (Codex/RP: 1000s)
  - Consensus engine: worst-verdict-wins, severity-weighted scoring, cross-engine deduplication
  - Multi-format findings parser: text markers, markdown tables, numbered lists
  - Per-engine JSON artifacts + consensus report saved to `.tasks/reviews/`
  - 20 tests covering verdict parsing, finding extraction, consensus logic
- **Scale-adaptive planning** — blast-radius complexity scoring:
  - Zero-blast (typo, rename, config) → simple → light chain variants (2-3 steps)
  - High-blast (auth, payment, database, production) → medium/complex → full chains
  - Multi-goal detection, file path mentions, query length signals
  - 5 light chain variants: feature-light, bugfix-light, refactor-light, release-light, testing-light
- **Phase-based parallel execution** — chain steps annotated with phases:
  - observe/design steps run in PARALLEL (multiple Agent tool calls)
  - mutate steps run sequentially, verify steps can parallelize
  - Dependency-aware: respects reads/outputs, won't parallelize dependent steps
  - 185 chain steps annotated across 45 chains
- **3 new chains** (45 total): ci-cd, prd-review, architecture, multi-review, + 5 light variants
- **Gemini CLI** detected as review backend (`gemini`/`gemini-cli`)
- **`multi` virtual backend** — available when 2+ review engines detected

### Fixed
- Chinese routing: 代码审查→deep-review, 写单元测试→testing, 理解代码→research (28/29 EN+CN)
- Codex review: native `codex review` mode (auto-reads git diff), filter MCP/session noise
- RP review: `rp builder --type review` with nested JSON response extraction
- Verdict parser: handles LGTM, APPROVED, BLOCK + word-boundary matching
- Session-start.md: concise table format, `go` as #1 entry

## [5.24.0] - 2026-03-24
### Added
- **3 new chains** (39 total):
  - `ci-cd`: scaffold → deploy → verify → commit (CI/CD pipeline setup)
  - `prd-review`: prd-validate → elicit → requirement-gate → prd (spec quality pipeline)
  - `architecture`: research → clean-architecture → architecture → plan (system design)
- **Expanded help system** — `cc-flow help` now shows:
  - `go` as the #1 entry point (was missing from help)
  - 7 example chains (was 4), including hotfix, idea-to-ship, deploy, security-audit
  - New categories: Automation, Wisdom & Learning, Workflows
  - Tab completions for go, wisdom, explore, wf commands

### Fixed
- **"set up CI/CD" routing** — now correctly routes to deploy/ci-cd chain (was hitting refactor)
- **`chain list` count** — help now shows "39 chains" (was hardcoded "7")
- **Non-standard skill ref** — `deep-search` in research chain → `/cc-bridge`
- **Deploy chain triggers** — added CI/CD, pipeline keywords

## [5.23.0] - 2026-03-24
### Added
- **15 missing slash commands** — every skill now has a direct `/cc-*` command (82 total):
  - cc-bridge, cc-parallel-agents, cc-plan-sync, cc-python-patterns, cc-python-testing
  - cc-readiness-audit, cc-review-backend, cc-rp, cc-search-strategy, cc-security-review
  - cc-task-queues, cc-task-tracking, cc-teams, cc-verification, cc-worker-protocol
- **61 new tests** (354 total) — 3 new test files covering previously untested modules:
  - `test_auto.py` (20 tests): OODA-loop team recommendation, findings orientation, task filtering
  - `test_wf_executor.py` (21 tests): topo sort, node description, chain export, workflow loading
  - `test_wisdom.py` (20 tests): wisdom CRUD, search, exploration cache, checkpoint logic
- **Chains extracted to `chains.json`** — 36 chain definitions moved from inline Python dict to user-editable JSON file (zero-dependency loader via stdlib `json`)

### Fixed
- **Scanner SyntaxWarnings** — excluded `ref/`, `zcf/`, `ccg-workflow/` from architecture scan (was parsing external files with invalid escape sequences)
- **Morph API test failures** — embed/rerank tests now gracefully skip when endpoint returns 404 (API changed, not a code bug)

### Improved
- **All CLI via `cc-flow` command** — eliminated all `python3 scripts/cc-flow.py` and `python3 -m cc_flow` invocations:
  - 12 scout agents: `CCFLOW="cc-flow"` instead of `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py`
  - 4 Ralph templates: `cc-flow show/start/done/verify` instead of `python3 scripts/cc-flow.py`
  - 4 hooks (session-end, pre-compact, session-start, post-task-hint): `cc-flow` CLI
  - CLAUDE.md, `__init__.py` docs updated
- **CLAUDE.md accuracy** — updated all stats: 55 modules (was 53), 78 skills (was 69), 82 commands (was 58), 36 chains (was 22), 354 tests (was 286)
- **`skill_chains.py` reduced from 827 → ~380 lines** — data separated from logic

## [5.22.0] - 2026-03-24
### Added
- **AI-first skill routing** — `cc-flow go` now analyzes intent + detects domains before routing:
  - 7 intent categories: BUILD, FIX, IMPROVE, VERIFY, SHIP, UNDERSTAND, PLAN
  - 5 domain detectors: security, database, api, frontend, performance
  - Auto-recommends supporting skills per domain (e.g., "add JWT auth" → auto-add `/cc-security-review`)
  - Output includes: `intent`, `domains_detected`, `recommended_additions`, `supporting_skills`
- **Enhanced proactive-suggestions rule** — full skill catalog by domain, multi-skill combination patterns, contextual triggers with AI analysis protocol. Replaces simple keyword matching with "analyze before suggesting" framework.

## [5.21.0] - 2026-03-24
### Improved
- **100% On Completion coverage** — all 78 skills now have standardized `## On Completion` section with:
  - Skill-specific context save keys (e.g., test skills save `test_results`+`coverage`, security saves `vulnerabilities`+`verdict`)
  - `cc-flow skill ctx save` + `cc-flow skill next` commands
  - Previously only 21/78 had this (27%), now 78/78 (100%)
- Every skill now participates in the context protocol: output from any skill is available to the next skill in the chain

## [5.20.0] - 2026-03-24
### Added
- **8 new chains** (36 total): testing, logging-observability, error-handling, product-validation, visual-qa, async-backend, team-workflow, clone-and-ship
- **Fixed 6 orphan skills** with flow edges: cc-feedback-loop, cc-git-workflow, cc-go, cc-optimize, cc-plan-sync, cc-ralph
- **Skill graph 92% connected** (was 86%): 72/78 skills have flow relationships
- **58 skills now in chains** (was 48): 10 more skills reachable via `cc-flow go`
- **0 routing gaps** (was 2): "write tests" → testing chain, "async patterns" → async-backend chain
- All common queries now route: visual qa, error handling, logging, clone site, team workflow, product validation

## [5.19.0] - 2026-03-24
### Added (Ruflo inspired)
- **Infinite Context Autopilot** — survives context compaction:
  - PreCompact hook saves critical state to `.tasks/compaction_context.json`: active chain, current skill, recent skill contexts (last 3), wisdom (last 5 per category), git state, active tasks, chain metrics
  - SessionStart hook restores and displays: `# RESTORED CONTEXT (from pre-compaction save)`
  - Shows: branch, last commit, active chain + step, current skill, in-progress tasks, recent wisdom, skill context keys
  - Zero config — works automatically on every compaction event

## [5.18.0] - 2026-03-24
### Added (gmickel flow-next inspired)
- **`/cc-deps`** — dependency graph skill: blocking chains, parallel execution phases, critical path analysis, ready-to-start recommendations. Answers "what should I work on next?" (78 skills, 67 commands)

## [5.17.0] - 2026-03-24
### Added (Everything Claude Code inspired)
- **`/cc-product-lens`** — product thinking before building: founder review, PMF scoring (0-50), user journey audit, RICE prioritization. BUILD/VALIDATE/DEFER decision.
- **`/cc-browser-qa`** — automated visual QA: smoke tests, Core Web Vitals (LCP/CLS/TTFB), WCAG AA accessibility, responsive breakpoints (mobile/tablet/desktop), dark mode, visual regression baselines.
- **`/cc-team-builder`** — dynamic agent composition: analyzes task (file types, domains, complexity), checks past success from wisdom system, recommends optimal team + execution mode.
- 3 new skills + commands (77 skills, 66 commands total)

## [5.16.0] - 2026-03-24
### Added (BMAD-METHOD inspired)
- **`/cc-architecture` skill** — Solutioning phase: document ADRs (API, data model, auth, testing, deployment) before coding. Inserted into feature chain between plan and tdd as optional step. Prevents multi-agent style conflicts.
- **`/cc-prd-validate` skill** — 10-step PRD validation pipeline: format, density, clarity scoring, SMART validation, traceability, completeness, implementation leakage, measurability. PASS/REVISE verdict.
- **`/cc-elicit` skill** — 8 structured reasoning methods: pre-mortem, first principles, inversion, red team, Socratic, constraint removal, stakeholder mapping, analogical reasoning. Auto-suggests relevant methods based on content type.
- 3 new skills + commands (74 skills, 63 commands total)

## [5.15.0] - 2026-03-24
### Added (AegisFlow inspired)
- **Severity-weighted review consensus** — verdicts based on finding severity, not reviewer vote count:
  - CRITICAL/HIGH finding = NEEDS_WORK even if majority approve
  - 3+ MEDIUM = NEEDS_WORK
  - Each finding must include severity, confidence, and lens
- **`/cc-requirement-gate` skill** — validates requirements before planning:
  - Assesses 5 dimensions: clarity, completeness, complexity, feasibility, testability
  - Decision: PROCEED / CONFIRM / CLARIFY
  - Inserted into feature + idea-to-ship chains (optional step)
- **Agent lens tagging** — each reviewer agent tagged with semantic lens:
  - code-reviewer: "code quality, maintainability, correctness"
  - python-reviewer: "PEP 8, type safety, Pythonic idioms"
  - security-reviewer: "OWASP Top 10, secrets, injection vectors"
  - db-reviewer: "query performance, schema design, migration safety"
- New skill + command: cc-requirement-gate (71 skills, 60 commands total)

## [5.14.0] - 2026-03-24
### Added
- **SKILL.md template validation** (gstack pattern):
  - Enhanced `cc-flow validate-skills` with NOT FOR, flow graph, On Completion checks
  - Cross-reference validation: skill↔command sync, broken flow refs, alias-aware
  - 69 skills validated, 23 real missing commands identified (vs 58 false positives before)
- **`/cc-prd` skill** — Convert PRD/spec to phased implementation plan with architectural decisions, vertical slices, and tracer-bullet first milestone
- **`prd-to-ship` chain** (28 chains total): prd → plan → work → epic-review → ship
  - Full lifecycle from requirements document to deployed code
  - Bridges the brainstorm→plan gap with explicit architectural decisions

## [5.13.0] - 2026-03-24
### Added
- **Hook enforcement levels** (PACEflow inspired):
  - `pre-commit-gate.sh`: strict mode **blocks** commits without recent `cc-flow verify` (within 5 min)
  - `mode-guard.sh`: strict mode **blocks** destructive ops (rm -rf, DROP TABLE, git push -f), standard mode warns
  - `cc-flow verify` now records timestamp to `.tasks/last_verify.json` for strict enforcement
- **Runtime hook profiles** (`CC_HOOK_PROFILE` env var):
  - `minimal` — safety hooks only (worktree-guard, mode-guard skip)
  - `standard` — current default behavior (warn but allow)
  - `strict` — all hooks + DENY mode (blocks commits without verify, blocks destructive ops)
- **Complexity-adaptive routing** in `cc-flow go`:
  - Estimates complexity: simple (hotfix keywords, short queries), medium (standard chains), complex (architecture/system/rewrite keywords, long queries)
  - Routes: simple→hotfix chain, medium→matched chain, complex→Ralph
  - Output includes `complexity` field showing why mode was chosen

## [5.12.0] - 2026-03-24
### Added
- **Wisdom system** (inspired by CCW) — persistent cross-chain knowledge accumulation:
  - `cc-flow wisdom show/search/add/clear` — manage learnings, decisions, conventions
  - `.tasks/wisdom/{learnings,decisions,conventions}.jsonl` — append-only stores
  - Auto-records on chain completion (chain name, outcome, steps)
  - Search by keyword across all wisdom categories
- **Exploration cache** — prevent redundant research:
  - `cc-flow explore cache/lookup/clear` — manage cached explorations
  - `.tasks/explorations/` with fuzzy query matching (70% word overlap)
  - Cache index for fast lookups
- **Checkpoint supervisor gate** — auto quality checks in long chains:
  - Fires every 2 steps in chains with >3 total steps
  - Runs `cc-flow verify` (lint + tests) + syntax check on changed files
  - Verdict: pass/warn/block — included in `chain advance` output
  - Results persisted in `.tasks/checkpoints/`
- New module: `wisdom.py` (55 modules total)

## [5.11.0] - 2026-03-24
### Added
- **cc-wf-studio integration** — `cc-flow wf` command group for bidirectional workflow interop:
  - `cc-flow wf run <workflow.json>` — execute cc-wf-studio visual workflows natively
  - `cc-flow wf run <workflow.json> --dry-run` — preview execution plan
  - `cc-flow wf list` — list available .vscode/workflows/*.json files
  - `cc-flow wf show <workflow.json>` — show workflow node details
  - `cc-flow wf export <chain>` — export cc-code chain as cc-wf-studio workflow JSON
  - `cc-flow wf export all` — export all 27 chains as visual workflows
- Workflow executor supports: SubAgent, Skill, Prompt, AskUserQuestion, IfElse, Switch, MCP, SubAgentFlow nodes
- Auto-execution instruction format (same as `cc-flow go` chain mode)
- New module: `wf_executor.py` (54 modules total)

### How it works
```
cc-wf-studio (VS Code)    ←→    cc-code (CLI)
  Visual design                  Execute workflows
  .vscode/workflows/*.json       cc-flow wf run
  Export → .claude/commands/     cc-flow wf export
```

## [5.10.0] - 2026-03-24
### Added
- **5 new chains** (27 total): hotfix (3-step fast-track), pr-review, perf-regression, tech-debt, db-migration
- **8 new TEAM_PATTERNS** (14 total): performance, database, api, incident, config, frontend, dependency, devops — aligned with skill chains for better auto-routing
- **Hotfix fast-track** — `cc-flow go "hotfix: fix typo"` routes to 3-step chain (implement → review → commit), skips brainstorm/plan
- **Enforceable workflow gates** in workflow.md:
  - Before commit: verification must pass, chain steps must have context, review must be SHIP
  - Before push: tests pass, no secrets, diff reviewed
  - Before deploy: deps check pass, readiness score ≥ 70
  - After chain: must record learning, metrics auto-tracked

### Improved
- Chain threshold raised from ≤4 to ≤5 required steps (feature chain now executes inline instead of launching Ralph)
- Hotfix keywords bypass chain matching and force chain mode directly
- workflow.md restructured: sequences → gates → dependency protocol → context protocol → auto-learn

## [5.9.0] - 2026-03-24
### Added
- **Metrics-boosted chain suggest** — `cc-flow chain suggest` now factors in historical success rates. Chains with higher completion rates get a score bonus (up to +3 points). Output includes run history and success rate.
- **Smart session start** — SessionStart hook now detects and reports:
  - Interrupted chains → recommends `cc-flow go --resume`
  - Active/blocked/ready tasks → recommends next action
  - Uncommitted changes → recommends `git diff`
  - Lint issues → recommends `cc-flow verify --fix`
  - Last commit time
  - All recommendations shown as numbered list with `cc-flow go` as fallback

### Improved
- `chain suggest` output now includes `score`, `history` (runs/success_rate/last_completed), and updated `instruction` pointing to `cc-flow go`
- Session start transitions from static display to dynamic project-aware recommendations

## [5.8.0] - 2026-03-24
### Added
- **Chain auto-execution** — `cc-flow go` chain mode now outputs `# AUTO-EXECUTE` instruction with explicit "Do NOT stop between steps" directive, per-step context save/advance commands, and schema hints (outputs/reads)
- **Resume interrupted chains** — `cc-flow go --resume` detects `_chain_state.json` and generates instructions for remaining steps. No-goal invocation hints about interrupted chain.
- **Context schema validation** — `cc-flow chain advance` validates saved context against expected `outputs` keys. Next step's `reads` are checked against available context. Warnings emitted for missing keys.
- 7 new tests: auto-exec instruction format, resume, schema validation

### Improved
- `cc-flow go` chain instruction now self-contained: Claude follows it without manual intervention
- Feature + bugfix chains fully annotated with `outputs`/`reads` per step
- `--resume` flag on `go` command; `goal` arg now optional (for resume-only usage)

## [5.7.0] - 2026-03-24
### Added
- **Flow graph coverage 84%** — 38 orphan skills now have FLOWS INTO/DEPENDS ON relationships (was 33%, 21→58 connected)
- **Dependency enforcement** — `cc-flow skill check-deps --skill cc-plan` warns when predecessor context is missing
- **Chain metrics** — `cc-flow chain stats` tracks runs, completions, success rate per chain
- **Context schema hints** — feature + bugfix chains define `outputs`/`reads` keys per step
- **Auto-learn prompt** — chain completion suggests `cc-flow learn` command with outcome

### Improved
- `chain run` records start metrics; `chain advance` records completion metrics
- Scouts → readiness-audit → deploy flow connections established
- Python pack skills (fastapi, database, async, etc.) now flow into tdd/review/refinement
- UI skills chain: ui-ux → web-design → optimize → review

## [5.6.0] - 2026-03-24
### Added
- **`cc-flow go`** — one command full automation: describe your goal, system auto-routes to chain/ralph/auto mode
  - `cc-flow go "fix login bug"` → chain mode (bugfix chain)
  - `cc-flow go "implement user auth"` → ralph mode (autonomous)
  - `cc-flow go "improve code quality"` → auto mode (OODA loop)
  - `--dry-run` to preview without executing, `--mode` to force strategy
- `/cc-go` slash command + skill (69 skills, 58 commands total)
- 19 tests for go module (routing, mode decision, force mode, output format)

## [5.5.0] - 2026-03-24
### Added
- **Skill flow graph** — parses FLOWS INTO / DEPENDS ON from all 69 SKILL.md files into queryable graph
  - `cc-flow skill graph` — show full graph (21 connected / 69 total skills)
  - `cc-flow skill graph --for cc-plan` — show one skill's connections
  - `cc-flow skill next --skill cc-brainstorm` — query what comes next
- **Skill context protocol** — pass data between skills
  - `cc-flow skill ctx save <name> --data '{}'` — save output context
  - `cc-flow skill ctx load <name>` — load predecessor's context
  - `cc-flow skill ctx current` — show active skill
- **Context-aware chain execution** — `cc-flow chain run` now loads previous step's context per step
  - `cc-flow chain advance --data '{}'` — save context + advance to next step
  - Chain state persisted for resume across sessions
- **Smart post-task hints** — PostToolUse hook calls `cc-flow skill next` for context-aware suggestions
- **On Completion protocol** — 12 key SKILL.md files updated with standardized completion sections
- `skill_flow.py` module (graph extraction, context protocol, 6 CLI commands)
- 22 tests for skill flow (graph parsing, caching, context, normalization, CLI)
- Skill context protocol documented in `rules/workflow.md`

### Improved
- Post-task-hint hook: detects `cc-flow skill ctx save` and `cc-flow chain advance` for smart next-step suggestions
- Chain run output includes `on_completion` instructions per step and `prev_context` from predecessor

## [5.4.0] - 2026-03-23
### Added
- Safety modes: `cc-flow careful/freeze/guard` — session-scoped safety guards
- QA skills: `cc-qa` (test+fix with health scoring) and `cc-qa-report` (report-only)
- Clone site: `/cc-clone-site URL` — replicate reference website end-to-end
- Autonomous: `cc-flow ralph --goal "..."` — goal-driven with self-heal
- Worktree CLI: `cc-flow worktree create/list/switch/remove/status/info`
- Checkpoint: `cc-flow checkpoint create/verify/compare/list`
- Context budget: `cc-flow context-budget` — token overhead analysis
- Ship workflow: `/cc-ship` — version bump + changelog + PR
- Skills: aside, grill-me, retro, office-hours, autonomous-loops, bridge, clone-site, qa, qa-report (68 total)
- Chains: 22 predefined workflows (idea-to-ship, qa-fix, incident, security-audit, etc.)
- Agent personality: emoji + deliverables for all 23 agents
- Proactive suggestions rule: 12 contextual triggers
- Config-protect hook: warns on linter/CI config changes
- Push-review hook: diff stats before git push
- Post-edit-verify hook: reminds to verify after source edits
- Mode-guard hook: enforces careful/freeze/guard modes

### Improved
- Worktree is now default isolation mode for cc-work and Ralph
- Worktree-guard auto-detects worktree context (zero config)
- Worktree nesting prevention (blocks create inside worktree)
- All skills: TRIGGER + NOT FOR + DEPENDS ON + FLOWS INTO metadata
- All skill/command references: `cc-flow` CLI instead of `python3 cc-flow.py`
- Chain suggest: top-3 alternatives with scoring
- Ralph: goal verification (tests/health/custom) + periodic self-heal scan

### Fixed
- 12 scout agents: model: haiku → model: inherit (per agent-orchestration rule)
- pre-commit-gate: stricter pattern matching, excludes git log/show

## [5.3.0] - 2026-03-23
### Added
- Bridge module (`bridge.py`): 6 Morph×RP×Supermemory collaboration loops
  - `cc-flow deep-search`: Morph search → RP selection → Builder analysis
  - `cc-flow smart-chat`: Supermemory recall → RP chat (memory-augmented)
  - `cc-flow embed-structure`: RP code structure → Morph embed vectors
  - `cc-flow recall-review`: recall past review findings from Supermemory
  - `cc-flow bridge-status`: check all 3 system connectivity
  - Auto: review verdicts → Supermemory on `cc-flow done`
  - Auto: OODA scan findings → Supermemory on `cc-flow auto deep`
- RepoPrompt SDK (`rp.py`): unified dual-transport (CLI + MCP auto-routing)
  - 26 `cc-flow rp` subcommands including `plan`, `review`, `worktree-status`, `worktree-diff`
  - MCP detection covers plugin-level `discover-agent.json`
  - `rp_version()` for CLI version reporting
  - `worktree_git_status()` / `worktree_diff()` via `@main:<branch>` syntax
- Worktree boundary guard (`worktree-guard.sh`): PreToolUse hook blocks Edit/Write outside assigned worktree
- Ralph guard enhanced: worktree boundary enforcement in autonomous mode
- "research" skill chain: deep-search → research → scout repo
- 15 bridge unit tests (`test_bridge.py`)
- Route table: 5 new entries (deep-search, smart-chat, embed-structure, recall-review, bridge-status) with Chinese keywords
### Improved
- All 58 skill descriptions enhanced with TRIGGER keywords (English + Chinese) and NOT FOR disambiguation
- Tool priority updated to MCP-first: RP MCP > cc-flow CLI > built-in
- `chat()` mode parameter now correctly routes to `plan()` / `review()`
- `review_setup.py` reuses `rp.py` detection for consistent backend availability
- REPL tab completion: 20+ new entries (bridge, rp, memory, chain commands)
- `cc-flow rp` help reorganized by category (Explore/Context/Chat/Edit/Git/Setup)
### Fixed
- MCP detection missed plugin-level `.mcp.json` discovery — now detects `discover-agent.json`
- `review_setup.py` checked `which rp` (wrong) instead of `which rp-cli` (correct)
- `chat()` mode parameter was a no-op (`if mode: pass`) — now routes correctly

## [5.2.0] - 2026-03-23
### Added
- Skill chains: 7 predefined multi-skill workflows (`chain run feature/bugfix/ui-design/...`)
- Context-aware pipelines: `pipeline run quality-gate/full-audit/review-and-fix`
- Supermemory integration: `memory save/search/forget/sync/recall`
- learn → Supermemory auto-sync (cross-project knowledge)
- route → Supermemory recall (memory-enhanced routing)
- Performance optimization skill (cc-optimize, from pbakaus/impeccable)
- Multi-language health scoring (Python/Node/Go auto-detect)
- Progressive disclosure in REPL help (`help` vs `help all`)
- `chain run` command — one-click skill chain execution
- `pipeline create` — user-defined pipelines
### Fixed
- Supermemory search None content handling
- Eval search false negative (grep output with 'error')
- Health scoring Python-only bias (morph-plugin: 70→95)

## [5.1.0] - 2026-03-23
### Added
- Skills marketplace: `cc-flow skills find/add/list` (skills.sh integration)
- "Did you mean?" typo correction in REPL
- REPL tab completion for all 90+ commands
- Interactive REPL mode (`cc-flow` with no args)
- Terminal skin: colored output (✓ ✗ ⚠ ●), tables, progress bars
- Example plugins: notify (desktop notifications) + timer (pomodoro)
### Fixed
- Race-safe task ID allocation (`O_CREAT|O_EXCL`)
- Epic/task ID shorthand (`epic-1.3` → full ID)
- Node.js verify: auto-detect package.json scripts
- Node.js verify: skip missing tools, detect missing node_modules
- Slugify strips `#()!@` from epic IDs
- Chinese route keywords expanded (新增/添加/修复/崩溃 etc.)
- Epic validation on task create (prevents orphan tasks)
- Q-learning rate 0.1→0.25 for faster adaptation

## [5.0.0] - 2026-03-22
### Added
- Interactive REPL with prompt_toolkit
- Terminal skin module (skin.py)
- Dashboard uses skin for colored output

## [4.2.0] - 2026-03-22
### Fixed
- CRITICAL: Atomic file writes (temp + os.replace) prevent data corruption
- CRITICAL: Cross-platform file locking (fcntl on Unix, msvcrt on Windows)
- Missing docstrings on 6 public commands
- Documentation drift (__init__.py, CLAUDE.md now accurate)
- auto.py print/JSON mixing — structured output only

## [4.1.0] - 2026-03-22
### Added
- Deep Morph API integration into OODA loop
- Embedding-based semantic duplication detection in scanner
- Morph Search for pattern discovery + task context
- Morph Rerank for priority refinement in auto deep

## [4.0.0] - 2026-03-22
### Added
- Autoimmune v2: OODA loop architecture (observe/orient/decide/act/learn)
- Smart scanner module: architecture, test coverage, docstrings, duplication, dependencies
- Scan trend tracking (improving/stable/declining)
- Q-learning adaptive priority based on success history

## [3.20.0] - 2026-03-22
### Added
- Q-learning router (qrouter.py) — learns optimal commands from history
- Performance tracking (perf.py) — auto-times every command
- Config profiles — fast/strict/minimal presets

## [3.19.0] - 2026-03-22
### Added
- Plugin system — discover, load, manage user plugins (.tasks/plugins/)
- Plugin lifecycle hooks (on_task_start/done/block)
- Plugin CLI: list/enable/disable/create

## [3.18.1] - 2026-03-22
### Added
- 23 integration tests for v3.10-3.18 features
- CHANGELOG.md with full version history

## [3.18.0] - 2026-03-22
### Added
- Lazy command loading — only imports the module needed for invoked command
- Categorized `--help` output — 10 command groups
- Workflow engine — `workflow list/show/run/create` with 3 built-in workflows

## [3.17.0] - 2026-03-22
### Added
- `time` — duration analysis per task, by size and epic
- `critical-path` — longest dependency chain analysis
- `template list/show/create` — task template management

## [3.16.0] - 2026-03-22
### Added
- `bulk` — batch status changes (done/todo/blocked)
- `burndown` — epic burndown timeline data
- `report` — comprehensive markdown project report

## [3.15.0] - 2026-03-22
### Added
- `index` — pre-build embedding cache for all tasks
- `dedupe` — detect near-duplicate tasks via embeddings
- `suggest` — recommend approach from similar completed tasks

## [3.14.0] - 2026-03-22
### Added
- `find --semantic` — embedding-based task search
- `similar` — find tasks similar to a given task
- `embeddings.py` module with SHA-256 cached Morph embeddings
- 3-tier learning search: rerank -> embedding -> keyword

## [3.13.0] - 2026-03-22
### Added
- `changelog` — auto-generate from completed tasks
- `diff` — git changes since task started
- `priority` — cross-epic priority-sorted task queue

## [3.12.0] - 2026-03-22
### Added
- `standup` — daily standup report
- `dep show` — full dependency chain analysis
- `task comment` — timestamped task notes

## [3.11.0] - 2026-03-22
### Added
- `find` — full-text search across tasks and epics
- `reopen` — reopen done/blocked tasks
- `task update` — modify task attributes post-creation
### Changed
- `stats` now outputs JSON (was markdown)

## [3.10.0] - 2026-03-22
### Added
- `verify` — one-click lint+test with language auto-detection
- `clean` — garbage collect old sessions/archives
- `export` — export epic as markdown report

## [3.9.2] - 2026-03-22
### Fixed
- Replace 6 blind Exception catches with specific types
- Add docstrings to 9 public functions
- 13 new unit tests, enable BLE001 rule

## [3.9.1] - 2026-03-22
### Fixed
- Replace 15 inline error prints with `error()` helper
- 7 new unit tests (graph, config, session, consolidation)
- Enable PLR0915 + TRY300 rules

## [3.9.0] - 2026-03-22
### Changed
- Package cc-flow as installable CLI (`pip install -e .` -> `cc-flow`)
- All C901 complexity violations resolved (12 -> 0)
- 780 ruff violations -> 0, 15 rules enforced
- 114 -> 132 tests
