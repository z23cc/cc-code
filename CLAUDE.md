# cc-code

AI-routed development toolkit — one command does everything. 3-engine system (Claude × Codex × Gemini), autopilot execution, PUA mutual challenge, failure recovery.

## Architecture

- `scripts/cc_flow/` — 73 modules, 20K LOC (lazy-loaded, atomic writes, cross-platform)
  - **Facades**: `engines.py` (review dispatch), `intelligence.py` (routing/learning), `routing.py` (Q-learning)
  - **Execution**: `go.py` (entry), `skill_executor.py` (claude -p subprocess), `auto_ops.py` (worktree/verify/commit), `autopilot.py` (3-engine guided)
  - **3-Engine**: `adversarial_review.py` (debate), `multi_review.py` (consensus), `pua_engine.py` (mutual challenge), `multi_plan.py` (collaborative plan)
  - **Intelligence**: `ai_router.py` (LLM routing), `failure_engine.py` (methodology switch), `auto_learn.py` (feedback loops), `plan_verify.py` (plan→diff check)
  - **Quality**: `design_review.py` (10-dim scoring), `review_dashboard.py` (history+gate), `browser_qa.py` (visual testing)
- `agents/` — 11 general + 12 scout agents
- `skills/` — 78 skills, `commands/` — 85 slash commands
- `chains.json` — 46 predefined workflows (+ 5 light variants)
- `rules/` — 11 always-on rules (incl. ask-user format)
- `hooks/` — 13 hooks across 6 events
- `tests/` — 449 tests

## One Command

```bash
cc-flow go "your goal"      # AI routes → auto-executes → review → commit
```

## How It Works

```
cc-flow go "goal"
  → AI Router (gemini/claude, 24h cache)
  → Simple: light chain (2-3 steps, auto-exec via claude -p)
  → Medium: standard chain (4-7 steps, team dispatch, worktree isolation)
  → Complex: autopilot (3-engine plan → execute → checkpoint → review)
  → After execution: plan-verify → review (3-engine debate, PUA if disputed) → commit
  → Auto-learn: wisdom + metrics + Q-learning + supermemory
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
| Dashboard | `cc-flow dashboard` |

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

### Design Review (10 dimensions, 0-10)
```
cc-flow design-review → 3 engines score → below 8 → "what would make it 10?" + fix
```

### PUA (models challenge each other)
```
Round N: one engine proposes → other 2 challenge → must respond → improve → repeat
Pass: 2 consecutive clean rounds | Stuck: 3rd engine mediates
```

### Failure Recovery
```
2+ failures → 3 engines diagnose WHY stuck → vote on methodology switch
Methodologies: RCA, Simplify, Invert, First Principles, Divide & Conquer
```

## Team Dispatch

Single skill steps auto-expand to specialist teams:
- **REVIEW**: code-reviewer + python-reviewer + security-reviewer (parallel)
- **DESIGN**: scout-repo + scout-practices + scout-gaps (parallel)

## Execution Pipeline

| Phase | Method | Auto? |
|-------|--------|-------|
| Routing | AI Router (gemini/claude LLM) | ✅ subprocess |
| Planning | multi-plan (3-engine collaborative) | ✅ subprocess |
| Worktree | auto_ops.auto_worktree_create() | ✅ subprocess |
| Skill execution | skill_executor (claude -p) | ✅ subprocess |
| Plan verification | plan_verify (3-engine) | ✅ subprocess |
| Review | unified_review (3-engine debate + PUA) | ✅ subprocess |
| Commit | auto_ops.auto_commit() | ✅ subprocess |
| Learning | auto_learn (wisdom + metrics + Q-learning) | ✅ auto callback |

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
cc-flow verify                       # lint + test
cc-flow dashboard                    # project overview
cc-flow doctor                       # health check
cc-flow health                       # score 0-100
```
