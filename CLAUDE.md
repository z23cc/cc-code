# cc-code

Development workflow toolkit with task management CLI. Language-agnostic core with Python language pack.

## Architecture

- `scripts/cc_flow/` — Task & workflow CLI package (38 subcommands, entry: `cc_flow.entry:main`)
- `scripts/morph_client.py` — Pure Python Morph API client (Apply, WarpGrep, Embed, Rerank)
- `agents/` — 23 agents (11 core + 12 cc-scout-* scouts, all `model: inherit`)
- `skills/` — 47 skills (all prefixed `cc-`):
  - **Core (23):** brainstorming, plan, tdd, verification, refinement, code-review-loop, worker-protocol, task-tracking, debugging, research, parallel-agents, teams, autoimmune, readiness-audit, search-strategy, git-workflow, prompt-engineering, clean-architecture, context-tips, docs, incident, dependency-upgrade, feedback-loop
  - **Python pack (12):** python-patterns, python-testing, async-patterns, database, fastapi, error-handling, performance, logging, security-review, scaffold, deploy, task-queues
  - **Scouts (12):** scout-practices, scout-repo, scout-docs, scout-docs-gap, scout-security, scout-testing, scout-tooling, scout-build, scout-env, scout-observability, scout-gaps, scout-context
- `commands/` — 24 slash commands (all prefixed `/cc-`)
- `tests/` — 132 tests (99 cc-flow integration + 18 unit + 15 morph)
- `rules/` — 9 always-on rules: python-style, testing, security, git, docs-sync, agent-orchestration, workflow, performance, tool-priority
- `hooks/` — 5 hooks: SessionStart, PreToolUse, PostToolUse, PreCompact, Stop

## Key Workflow (team-first, auto-integrated)

```
/cc-route → suggests command + team + confidence % (morph rerank)
    ↓
/cc-brainstorm (auto-scouts → interview → architect)
    ↓
/cc-plan (auto-imports tasks to cc-flow with tags + templates)
    ↓
/cc-tdd (worker → code-reviewer → security-reviewer)
    ↓
/cc-review (researcher → parallel reviewers → consolidate)
    ↓
/cc-commit → cc-flow learn → cc-flow consolidate → smarter routing
```

Alternative entries: `/cc-blueprint`, `/cc-interview`, `/cc-prime`, `/cc-debug`, `/cc-autoimmune`

## Tool Priority

1. cc-flow morph commands (`search`, `apply`, `embed`, `compact`) → semantic search, fast edits, embeddings
2. rp-cli (`context_builder`, `structure`, `review`) → deep cross-file analysis
3. Built-in (Grep, Read, Edit) → fallback

## cc-flow Quick Reference

```bash
# After: pip install -e .  →  cc-flow <command>
# Or:    python -m cc_flow <command>  (from scripts/)
# Or:    CCFLOW="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cc-flow.py" (legacy shim)

cc-flow dashboard                              # one-screen overview
cc-flow search "auth flow" --rerank            # semantic search + rerank
cc-flow route "fix login bug"                  # smart routing
cc-flow session save --notes "context"         # persist session
cc-flow session restore                        # resume
cc-flow graph --format ascii                   # dependency tree
cc-flow doctor                                 # health check
```
