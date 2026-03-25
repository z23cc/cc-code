# cc-code

AI-routed development toolkit — one command does everything. 3-engine system (Claude × Codex × Gemini), autopilot execution, PUA mutual challenge, failure recovery.

## Architecture

- `scripts/cc_flow/` — 75 modules, 20K LOC (lazy-loaded, atomic writes, cross-platform)
  - **Facades**: `engines.py` (review dispatch), `intelligence.py` (routing/learning), `routing.py` (Q-learning)
  - **Execution**: `go.py` (entry), `team_executor.py` (native Agent dispatch), `skill_executor.py` (claude -p subprocess), `auto_ops.py` (worktree/verify/commit), `autopilot.py` (3-engine guided)
  - **3-Engine**: `adversarial_review.py` (debate), `multi_review.py` (consensus), `pua_engine.py` (mutual challenge), `multi_plan.py` (collaborative plan)
  - **Intelligence**: `ai_router.py` (LLM routing), `failure_engine.py` (methodology switch), `auto_learn.py` (feedback loops), `plan_verify.py` (plan→diff check)
  - **Quality**: `design_review.py` (10-dim scoring), `review_dashboard.py` (history+gate), `browser_qa.py` (visual testing)
- `agents/` — 11 general + 12 scout agents (with effort/maxTurns/skills/isolation/disallowedTools)
- `skills/` — 78 skills, `commands/` — 85 slash commands
- `chains.json` — 46 predefined workflows (+ 5 light variants)
- `rules/` — 11 always-on rules (incl. ask-user format)
- `hooks/` — 15 hooks across 7 events
- `tests/` — 449 tests
- `dashboard/` — Real-time web visualization (Express + React + WebSocket + SQLite)

## One Command

```bash
cc-flow go "your goal"      # AI routes → Team Agents execute → 3-engine review → commit
```

## How It Works

```
cc-flow go "goal"
  → AI Router (gemini/claude, 24h cache)
  → Simple: light chain (2-3 steps)
  → Medium: Team Agent execution (6 research agents ∥ → planner → 3-engine PUA → tdd → review)
  → Complex: autopilot (3-engine plan → execute → checkpoint → review)
  → After: plan-verify → review (3-engine debate, PUA if disputed) → commit
  → Auto-learn: wisdom + metrics + Q-learning + supermemory + dashboard
```

## Quick Reference

| Goal | Command |
|------|---------|
| **Anything** | `cc-flow go "goal"` (AI auto-routes) |
| Complex task | `cc-flow autopilot "goal"` (3-engine guided) |
| Code review | `cc-flow review` (auto 3-engine debate + PUA) |
| Design review | `cc-flow design-review` (10-dim scoring 0-10) |
| Review history | `cc-flow review-dashboard` / `gate` |
| Plan verification | `cc-flow plan-verify` |
| Project health | `/cc-prime` (12 scouts parallel) |
| Verify code | `cc-flow verify` (lint + test) |
| Dashboard | http://localhost:3777 (auto-starts) |

## 3-Engine System

| Engine | Role | Used In |
|--------|------|---------|
| Claude | Security & Correctness | review, plan, PUA, autopilot, failure diagnosis |
| Codex (GPT) | Bug Hunter & Patterns | review, plan, PUA, autopilot, failure diagnosis |
| Gemini | Architecture & Research | review, plan, PUA, autopilot, failure diagnosis |
| RP Builder | Deep Context Provider | review phase 0, autopilot phase 0 |

### Review (auto-escalates)
```
cc-flow review → 3-engine debate → if disputed → PUA (multi-round challenge)
```

### PUA (models challenge each other)
```
Round N: one engine proposes → other 2 challenge → must respond → improve
Pass: 2 consecutive clean rounds | Stuck: 3rd engine mediates
```

### Failure Recovery
```
2+ failures → 3 engines diagnose WHY stuck → vote on methodology switch
Methodologies: RCA, Simplify, Invert, First Principles, Divide & Conquer
```

## Team Agent Execution

Default execution uses Claude Code native Agent tool (not claude -p subprocess):
```
Message 1: 6 agents parallel (3 scouts + morph-github + research + RP)
Message 2: planner agent (synthesize research)
Message 3: 3-engine PUA on plan (codex + gemini)
Message 4: tdd agent (isolation: worktree, full tool access)
Message 5: 3-engine review + plan-verify
Message 6: auto-commit + auto-learn
```

## Agent Permissions

| Role | Can Write? | disallowedTools |
|------|-----------|----------------|
| Reviewers (code/python/db) | ❌ | Write, Edit |
| Scouts (12) | ❌ | Write, Edit, Bash |
| Architect, Planner, Researcher | ❌ | Write, Edit |
| Security-reviewer, Refactor, Build-fixer | ✅ | — |

## Hooks (15 across 7 events)

| Event | Hooks | Key |
|-------|-------|-----|
| SessionStart | 1 | Dashboard auto-start + context |
| UserPromptSubmit | 1 | Task context injection |
| PreToolUse | 6 | worktree-guard, config-protect (blocks!), mode-guard, commit-gate, push-review, semantic-verify |
| PostToolUse | 4 | task-hint, edit-verify, failure-counter, learn-observer (async) |
| SubagentStop | 1 | Dashboard event |
| PreCompact | 1 | State preservation |
| Stop | 1 | Session save + learnings |

## Execution Pipeline

| Phase | Method | Auto? |
|-------|--------|-------|
| Routing | AI Router (gemini/claude LLM) | ✅ |
| Research | 6 Team Agents parallel (native) | ✅ |
| Planning | Planner agent + 3-engine PUA | ✅ |
| Worktree | isolation: worktree (native) | ✅ |
| Implementation | TDD agent (full tool access) | ✅ |
| Plan verification | plan_verify (3-engine) | ✅ |
| Review | unified_review (debate + PUA) | ✅ |
| Commit | auto_ops.auto_commit() | ✅ |
| Learning | auto_learn + dashboard events | ✅ |

## Bridge (Morph × RP × Supermemory)

```bash
cc-flow deep-search "auth flow"      # Morph → RP analysis
cc-flow smart-chat "architecture"    # Supermemory → RP chat
cc-flow bridge-status                # check all 3 systems
```

## cc-flow Commands

```bash
cc-flow go "goal"                    # one command, full auto
cc-flow review                       # 3-engine debate + PUA
cc-flow design-review                # 10-dim design scoring
cc-flow review-dashboard             # review history + gate
cc-flow autopilot "goal"             # 3-engine guided execution
cc-flow multi-plan "goal"            # 3-engine collaborative plan
cc-flow plan-verify                  # 3-engine plan→diff check
cc-flow pua                          # 3-model mutual challenge
cc-flow failure status               # failure tracking
cc-flow verify                       # lint + test
cc-flow dashboard                    # project overview
cc-flow doctor                       # health check
cc-flow health                       # score 0-100
```
