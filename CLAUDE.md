# cc-code

Development workflow toolkit with task management CLI. Language-agnostic core with Python language pack.

## Architecture

- `scripts/cc_flow/` — Task & workflow CLI package (39 modules, lazy-loaded, atomic writes, cross-platform)
- `scripts/morph_client.py` — Pure Python Morph API client (Apply, WarpGrep, Embed, Rerank)
- `scripts/worktree.sh` — Git worktree manager (create/list/switch/remove/cleanup/status)
- `agents/` — 11 general agents + 12 scout agents (read-only specialists), all `model: inherit`
- `templates/ralph/` — Ralph autonomous harness templates (ralph.sh, config.env, prompts, guard hooks)
- `skills/` — 59 skills (all prefixed `cc-`):
  - **Core (35):** brainstorming, plan, tdd, verification, refinement, code-review-loop, worker-protocol, task-tracking, debugging, research, parallel-agents, teams, autoimmune, readiness-audit, search-strategy, git-workflow, prompt-engineering, clean-architecture, context-tips, docs, incident, dependency-upgrade, feedback-loop, web-design, ui-ux, browser, optimize, **work, worktree, plan-sync, epic-review, review-backend, ralph, rp**
  - **Python pack (12):** python-patterns, python-testing, async-patterns, database, fastapi, error-handling, performance, logging, security-review, scaffold, deploy, task-queues
  - **Scouts (12):** scout-practices, scout-repo, scout-docs, scout-docs-gap, scout-security, scout-testing, scout-tooling, scout-build, scout-env, scout-observability, scout-gaps, scout-context
- `commands/` — 32 slash commands (all prefixed `/cc-`)
- `tests/` — 230 tests (128 cc-flow integration + 87 unit + 15 morph)
- `rules/` — 9 always-on rules: python-style, testing, security, git, docs-sync, agent-orchestration, workflow, performance, tool-priority
- `hooks/` — 6 hooks: SessionStart (context-aware), PreToolUse (commit-gate + worktree-guard), PostToolUse, PreCompact, Stop

## Quick Decision Tree

| You want to... | Start with |
|----------------|------------|
| Build a new feature | `/cc-brainstorm` → `/cc-plan` → `/cc-work` (or `/cc-tdd`) |
| Execute a plan end-to-end | `/cc-work epic-1` (worktree + worker + review loop) |
| Verify epic completion | `/cc-epic-review epic-1` |
| Run autonomously (unattended) | `/cc-ralph-init` → `bash scripts/ralph/ralph.sh` |
| Configure review backend | `cc-flow config set review.backend rp` |
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

1. **RP MCP** (auto-connected) → `file_search`, `context_builder`, `apply_edits`, `get_code_structure`, `git` — in-process, fast, structured JSON
2. **cc-flow CLI** → `search` (Morph semantic), `apply` (Fast Apply), `embed`, `compact` — subprocess, rich features
3. **Built-in** → Grep, Read, Edit — fallback for exact patterns and targeted operations

When MCP is unavailable (Ralph, scripts): use `cc-flow rp <cmd>` as CLI equivalent.

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

cc-flow dashboard                              # one-screen overview
cc-flow search "auth flow" --rerank            # semantic search + rerank
cc-flow route "fix login bug"                  # smart routing
cc-flow bridge-status                          # Morph × RP × SM status
cc-flow deep-search "how does auth work"       # Morph search → RP analysis
cc-flow session save --notes "context"         # persist session
cc-flow session restore                        # resume
cc-flow graph --format ascii                   # dependency tree
cc-flow doctor                                 # health check
cc-flow verify                                 # lint + test (auto-detect language)
cc-flow verify --fix                           # auto-fix lint, then test
cc-flow export epic-1-xxx                      # export epic as markdown
cc-flow clean --dry-run                        # preview old data cleanup
```
