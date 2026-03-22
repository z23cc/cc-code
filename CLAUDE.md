# cc-code

Development workflow toolkit with task management CLI. Language-agnostic core with Python language pack.

## Architecture

- `scripts/cc_flow/` — Task & workflow CLI package (72 subcommands, lazy-loaded, plugin-extensible)
- `scripts/morph_client.py` — Pure Python Morph API client (Apply, WarpGrep, Embed, Rerank)
- `agents/` — 11 general agents + 12 scout agents (read-only specialists), all `model: inherit`
- `skills/` — 47 skills (all prefixed `cc-`):
  - **Core (23):** brainstorming, plan, tdd, verification, refinement, code-review-loop, worker-protocol, task-tracking, debugging, research, parallel-agents, teams, autoimmune, readiness-audit, search-strategy, git-workflow, prompt-engineering, clean-architecture, context-tips, docs, incident, dependency-upgrade, feedback-loop
  - **Python pack (12):** python-patterns, python-testing, async-patterns, database, fastapi, error-handling, performance, logging, security-review, scaffold, deploy, task-queues
  - **Scouts (12):** scout-practices, scout-repo, scout-docs, scout-docs-gap, scout-security, scout-testing, scout-tooling, scout-build, scout-env, scout-observability, scout-gaps, scout-context
- `commands/` — 24 slash commands (all prefixed `/cc-`)
- `tests/` — 196 tests (125 cc-flow integration + 56 unit + 15 morph)
- `rules/` — 9 always-on rules: python-style, testing, security, git, docs-sync, agent-orchestration, workflow, performance, tool-priority
- `hooks/` — 5 hooks: SessionStart (context-aware), PreToolUse, PostToolUse, PreCompact, Stop

## Quick Decision Tree

| You want to... | Start with |
|----------------|------------|
| Build a new feature | `/cc-brainstorm` → `/cc-plan` → `/cc-tdd` |
| Fix a bug | `/cc-debug` (researcher → fixer → reviewer) |
| Fix build/lint errors | `/cc-fix` (build-fixer agent) |
| Review code quality | `/cc-review` (parallel reviewers) |
| Understand unfamiliar code | `/cc-research` (researcher agent) |
| Assess project health | `/cc-audit` or `/cc-prime` (all scouts) |
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

1. cc-flow CLI (`search`, `apply`, `embed`, `compact`) → semantic search, fast edits
2. rp-cli (`context_builder`, `structure`, `review`) → deep cross-file analysis
3. Built-in (Grep, Read, Edit) → exact patterns, targeted operations

## cc-flow Quick Reference

```bash
# After: pip install -e .  →  cc-flow <command>
# Or:    python -m cc_flow <command>  (from scripts/)

cc-flow dashboard                              # one-screen overview
cc-flow search "auth flow" --rerank            # semantic search + rerank
cc-flow route "fix login bug"                  # smart routing
cc-flow session save --notes "context"         # persist session
cc-flow session restore                        # resume
cc-flow graph --format ascii                   # dependency tree
cc-flow doctor                                 # health check
cc-flow verify                                 # lint + test (auto-detect language)
cc-flow verify --fix                           # auto-fix lint, then test
cc-flow export epic-1-xxx                      # export epic as markdown
cc-flow clean --dry-run                        # preview old data cleanup
```
