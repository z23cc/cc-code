# cc-code

Development workflow toolkit with task management CLI. Language-agnostic core with Python language pack.

## Architecture

- `scripts/cc_flow/` — Task & workflow CLI package (55 modules, 15K LOC, lazy-loaded, atomic writes, cross-platform)
- `scripts/morph_client.py` — Pure Python Morph API client (Apply, WarpGrep, Embed, Rerank)
- `scripts/worktree.sh` — Git worktree manager (create/list/switch/remove/cleanup/status + nesting guard)
- `agents/` — 11 general agents + 12 scout agents (read-only specialists), all `model: inherit`
- `templates/ralph/` — Ralph autonomous harness (goal-driven + self-heal + receipt gates)
- `skills/` — 78 skills (all prefixed `cc-`):
  - **Core (54):** brainstorming, plan, tdd, verification, refinement, code-review-loop, worker-protocol, task-tracking, debugging, research, parallel-agents, teams, autoimmune, readiness-audit, search-strategy, git-workflow, prompt-engineering, clean-architecture, context-tips, docs, incident, dependency-upgrade, feedback-loop, web-design, ui-ux, browser, optimize, go, work, worktree, plan-sync, epic-review, review-backend, ralph, rp, bridge, ship, autonomous-loops, clone-site, qa, qa-report, aside, grill-me, retro, office-hours, prd, requirement-gate, architecture, prd-validate, elicit, product-lens, browser-qa, team-builder, deps
  - **Python pack (12):** python-patterns, python-testing, async-patterns, database, fastapi, error-handling, performance, logging, security-review, scaffold, deploy, task-queues
  - **Scouts (12):** scout-practices, scout-repo, scout-docs, scout-docs-gap, scout-security, scout-testing, scout-tooling, scout-build, scout-env, scout-observability, scout-gaps, scout-context
  - **Chains:** 36 predefined workflows in `chains.json` (idea-to-ship, feature, bugfix, hotfix, qa-fix, incident, security-audit, performance, deploy, testing, async-backend, db-migration, prd-to-ship, clone-and-ship, etc.)
- `commands/` — 82 slash commands (all prefixed `/cc-`, every skill has a command)
- `tests/` — 330+ tests (150 cc-flow integration + 87 unit + 22 skill-flow + 29 go + 15 morph + 15 bridge + auto + wf_executor + wisdom)
- `rules/` — 10 always-on rules: python-style, testing, security, git, docs-sync, agent-orchestration, workflow, performance, tool-priority, proactive-suggestions
- `hooks/` — 13 hooks across 6 events: UserPromptSubmit (auto-context), PreToolUse (worktree-guard + config-protect + mode-guard + commit-gate + push-review), PostToolUse (task-hint + edit-verify), SessionStart, PreCompact, Stop

## Quick Decision Tree

| You want to... | Start with |
|----------------|------------|
| **Anything (auto-routed)** | **`cc-flow go "describe your goal"`** |
| Build a new feature | `/cc-brainstorm` → `/cc-plan` → `/cc-work` (or `/cc-tdd`) |
| Execute a plan end-to-end | `/cc-work epic-1` (worktree + worker + review loop) |
| Verify epic completion | `/cc-epic-review epic-1` |
| Run autonomously (unattended) | `cc-flow ralph` or `cc-flow ralph --goal "all tests pass"` |
| Clone/replicate a website | `/cc-clone-site https://example.com` |
| QA test a site | `/cc-qa` (test + fix) or `/cc-qa-report` (report only) |
| Configure review backend | `cc-flow config set review.backend rp` |
| Fix a bug | `/cc-debug` (researcher → fixer → reviewer) |
| Fix build/lint errors | `/cc-fix` (build-fixer agent) |
| Review code quality | `/cc-review` (parallel reviewers) |
| Understand unfamiliar code | `/cc-research` or `cc-flow deep-search "query"` |
| Assess project health | `/cc-audit` or `/cc-prime` (all scouts) |
| Manage worktrees | `cc-flow worktree create/list/status/info` |
| Enable safety mode | `cc-flow careful --enable` or `cc-flow guard --enable` |
| Not sure what to do | `/cc-route "describe your task"` |

## Teams

| Team | Agents | Used by |
|------|--------|---------|
| feature-dev | scouts → architect → planner → worker | `/cc-brainstorm`, `/cc-plan`, `/cc-tdd` |
| bug-fix | researcher → build-fixer → code-reviewer | `/cc-debug`, `/cc-fix` |
| review | python-reviewer + security-reviewer (parallel) → consolidate | `/cc-review`, `/cc-pr-review` |
| refactor | researcher → refactor-cleaner → code-reviewer | `/cc-simplify` |
| audit | all 12 scouts (parallel) | `/cc-prime`, `/cc-audit` |

## Tool Priority

**RP MCP → cc-flow CLI → Built-in.** See `rules/tool-priority.md` for full decision matrix.

## Bridge (Morph × RP × Supermemory)

```bash
cc-flow bridge-status                          # check all 3 systems
cc-flow deep-search "auth flow" --type plan    # Morph find → RP analyze
cc-flow smart-chat "how to improve" --mode chat # memory-enhanced RP chat
cc-flow embed-structure src/auth/              # code structure → vectors
cc-flow recall-review "authentication"         # past review findings
cc-flow rp plan "design user auth"             # RP architecture plan
cc-flow rp review "check recent changes"       # RP code review
```

## cc-flow Quick Reference

```bash
# After: pip install -e .  →  cc-flow <command>
# Or:    python -m cc_flow <command>  (from scripts/)

cc-flow go "describe your goal"                # ONE COMMAND — auto-routes + executes
cc-flow go "fix login bug" --dry-run           # preview plan without executing
cc-flow dashboard                              # one-screen overview
cc-flow search "auth flow" --rerank            # semantic search + rerank
cc-flow route "fix login bug"                  # smart routing
cc-flow bridge-status                          # Morph × RP × SM status
cc-flow deep-search "how does auth work"       # Morph search → RP analysis
cc-flow worktree create feature-auth           # create isolated worktree
cc-flow worktree list                          # list all worktrees
cc-flow worktree info                          # current worktree context
cc-flow ralph                                  # autonomous task execution
cc-flow ralph --goal "all tests pass"          # goal-driven until achieved
cc-flow careful --enable                       # safety mode (warn on destructive ops)
cc-flow checkpoint create "before-refactor"    # save state snapshot
cc-flow context-budget                         # analyze token overhead
cc-flow session save --notes "context"         # persist session
cc-flow session restore                        # resume
cc-flow graph --format ascii                   # dependency tree
cc-flow doctor                                 # health check
cc-flow verify                                 # lint + test (auto-detect language)
cc-flow verify --fix                           # auto-fix lint, then test
cc-flow skill graph                            # skill flow graph (connections)
cc-flow skill next --skill cc-brainstorm       # what comes after brainstorm?
cc-flow skill ctx save cc-plan --data '{}'     # save context for next skill
cc-flow skill ctx load cc-brainstorming        # load predecessor's context
cc-flow chain suggest "what should I do"       # suggest best workflow chain
cc-flow chain run feature                      # run chain with context passing
cc-flow chain advance --data '{}'              # advance chain + save context
cc-flow export epic-1-xxx                      # export epic as markdown
cc-flow clean --dry-run                        # preview old data cleanup
```
