# cc-code

Development workflow toolkit for Claude Code — task management, smart routing, multi-backend review, autonomous execution (Ralph), worktree isolation, OODA autoimmune loop, embedding-powered search, and skills marketplace integration.

## Install

```bash
# As Claude Code plugin
claude plugin add z23cc/cc-code

# Or standalone CLI
pip install -e .
cc-flow dashboard
```

## Quick Start

```bash
cc-flow                                # Interactive REPL (tab completion + typo correction!)
cc-flow init                           # Initialize project
cc-flow epic create --title "Feature"  # Create an epic
cc-flow task create --epic epic-1 --title "Step 1"
cc-flow start epic-1.1                 # Start task
cc-flow verify                         # Lint + test (auto-detect language)
cc-flow done epic-1.1                  # Complete task
cc-flow dashboard                      # Visual overview
```

## First-Time Setup

### 1. Initialize Project

```bash
cc-flow init                           # Creates .tasks/ directory
```

### 2. Configure Review Backend

cc-code supports multiple review backends. Run detection first:

```bash
cc-flow review-setup                   # Detect available backends
```

Output shows which backends are available on your system:

```
agent  ✓  Built-in cc-code reviewer agents (no setup needed)
rp     ✓  RepoPrompt GUI — deep file context via Builder (macOS)
codex  ✓  OpenAI Codex CLI — multi-model terminal review
export ✓  Export context markdown for external LLM
```

Set your preferred default:

```bash
# Option A: Use built-in agents (default, no setup needed)
cc-flow review-setup --set agent

# Option B: Use RepoPrompt for deeper reviews (requires RepoPrompt app)
cc-flow review-setup --set rp

# Option C: Use Codex CLI for multi-model reviews
cc-flow review-setup --set codex
```

You can also configure **per review type**:

```bash
cc-flow review-setup --set rp --scope plan          # Plan reviews via RepoPrompt
cc-flow review-setup --set agent --scope impl        # Impl reviews via agents
cc-flow review-setup --set codex --scope completion  # Epic reviews via Codex
```

Verify your config:

```bash
cc-flow review-setup
```

### 3. (Optional) Setup Ralph Autonomous Mode

For fully unattended task execution:

```bash
/cc-ralph-init                         # Creates scripts/ralph/ harness
```

Edit `scripts/ralph/config.env` to configure review gates, iteration limits, and branch strategy. Then:

```bash
bash scripts/ralph/ralph_once.sh       # Test single iteration
bash scripts/ralph/ralph.sh            # Full autonomous run
bash scripts/ralph/ralph.sh --watch    # Watch mode (real-time output)
```

### 4. (Optional) Worktree Setup

cc-code uses Claude Code's native worktree directory (`.claude/worktrees/`):

```bash
# Nothing to configure — works out of the box
/cc-worktree create feature-auth       # Create isolated worktree
/cc-worktree list                      # List all worktrees
/cc-worktree status                    # Show clean/dirty state
/cc-worktree cleanup                   # Remove all managed worktrees
```

For cross-worktree task state sharing:

```bash
cc-flow state-path                     # Show shared state directory
cc-flow migrate-state --clean          # Move runtime state to .git/cc-flow-state/
```

## Workflow Guide

### Feature Development (Full Pipeline)

```bash
# 1. Plan
/cc-brainstorm "Add user authentication"     # Explore design
/cc-plan epic-1                              # Break into tasks

# 2. Execute (one-stop command)
/cc-work epic-1                              # Sequential: task → verify → review → done
/cc-work epic-1 --branch=worktree            # Each task in isolated worktree
/cc-work epic-1 --backend=rp                 # Use RepoPrompt for reviews

# 3. Verify completion
/cc-epic-review epic-1                       # Check all requirements met

# 4. Ship
/cc-commit
```

### Quick Bug Fix

```bash
/cc-debug "describe the bug"                 # Research → fix → review
```

### Code Review (Multi-Backend)

```bash
/cc-review                                   # Default backend (agent)
/cc-review --backend=rp                      # RepoPrompt GUI
/cc-review --backend=codex                   # Codex CLI
/cc-review --backend=export                  # Export for external LLM
```

### Autonomous Mode (Ralph)

```bash
# Setup (once per project)
/cc-ralph-init

# Configure (edit scripts/ralph/config.env)
PLAN_REVIEW=agent                   # Review backend for plans
WORK_REVIEW=agent                   # Review backend for implementations
COMPLETION_REVIEW=agent             # Review backend for epic completion
MAX_ITERATIONS=25                   # Loop limit
MAX_ATTEMPTS_PER_TASK=5             # Retries before auto-blocking

# Run
bash scripts/ralph/ralph.sh
```

Ralph spawns fresh Claude sessions per iteration, validates completion via receipts, and auto-blocks tasks after repeated failures.

### Not Sure What to Do?

```bash
/cc-route "describe your task"               # Smart routing → suggests command + team
```

## Key Features

| Feature | Command | Description |
|---------|---------|-------------|
| **Work Pipeline** | `/cc-work epic-1` | End-to-end: task → worktree → worker → verify → review → done |
| **Multi-Backend Review** | `/cc-review --backend=rp` | agent, RepoPrompt, Codex CLI, export |
| **Review Setup** | `cc-flow review-setup` | Detect backends + configure defaults |
| **Ralph Autonomous** | `cc-flow ralph --goal "..."` | Goal-driven unattended execution with self-heal |
| **Epic Review** | `/cc-epic-review` | Verify all tasks satisfy epic spec |
| **Plan Sync** | Automatic in `/cc-work` | Detect implementation drift, update downstream specs |
| **Worktree** | `cc-flow worktree create` | Default isolation mode, auto-detected, nesting-safe |
| **Clone Site** | `/cc-clone-site URL` | Replicate reference site: screenshot → analyze → implement → QA |
| **QA Testing** | `/cc-qa` or `/cc-qa-report` | Diff-aware QA with health scoring (0-100) |
| **Safety Modes** | `cc-flow careful/freeze/guard` | Session-scoped safety guards for destructive ops |
| **Checkpoint** | `cc-flow checkpoint create` | Save/compare workflow state snapshots |
| **Context Budget** | `cc-flow context-budget` | Analyze token overhead from rules, skills, agents |
| **Skill Chains** | `cc-flow chain suggest "task"` | 22 predefined workflows with alternatives |
| **REPL** | `cc-flow` | Interactive shell with tab completion + "did you mean?" |
| **Dashboard** | `cc-flow dashboard` | Colored one-screen project overview |
| **Smart Router** | `cc-flow route "fix bug"` | Q-learning command suggestions |
| **Verify** | `cc-flow verify --fix` | Auto-detect language + lint + test |
| **Deep Scan** | `cc-flow auto deep` | OODA: architecture + tests + docs + deps |
| **Semantic Search** | `cc-flow find --semantic "auth"` | Morph embedding-powered task search |
| **Deep Search** | `cc-flow deep-search "auth"` | Morph find → RP select → Builder analyze |
| **Smart Chat** | `cc-flow smart-chat "question"` | Supermemory recall → RP chat (memory-augmented) |
| **Bridge Status** | `cc-flow bridge-status` | Check Morph × RP × Supermemory connectivity |
| **Health Score** | `cc-flow health` | 0-100 composite grade (A-F) |
| **Forecast** | `cc-flow forecast` | ETA from velocity |
| **GitHub Sync** | `cc-flow gh import/export` | Sync with GitHub Issues |
| **Workflows** | `cc-flow workflow run release` | Multi-step pipelines |
| **Skills Store** | `cc-flow skills find "react"` | Browse skills.sh marketplace |

## Architecture

```
cc-flow CLI (51 modules, 137 commands, 57 slash commands)
├── Core: init, epic/task CRUD, deps, templates (atomic writes, cross-platform locks)
├── Views: list, dashboard, progress, graph, export
├── Work: start, done, block, reopen, diff, bulk, /cc-work pipeline
├── Review: review-setup, multi-backend routing (agent/rp/codex/export), receipts
├── Search: find, similar, dedupe, suggest, index (Morph embed)
├── Quality: verify, scan, doctor, health, auto deep (OODA loop), validate-skills
├── Analytics: stats, standup, changelog, burndown, report, forecast, evolve
├── Routing: route (Q-learning + embedding + rerank), learn, consolidate
├── Orchestration: 22 skill chains, 6 workflows, 3 pipelines, Ralph goal-driven
├── Worktree: create, list, switch, remove, status, info (auto-detect, nesting-safe)
├── Safety: careful, freeze, guard (session-scoped modes), checkpoint create/verify
├── Bridge: deep-search, smart-chat, embed-structure, recall-review (Morph×RP×SM)
├── Integration: gh sync, context, session, Supermemory, skills.sh, context-budget
└── UX: REPL with tab completion, colored skin, "did you mean?", progressive help

Skills (58):
├── Core (34): work, worktree, plan-sync, epic-review, review-backend, ralph, ...
├── Python pack (12): patterns, testing, async, database, fastapi, ...
└── Scouts (12): practices, repo, docs, security, testing, tooling, ...

Agents (23):
├── General (11): cc-architect, planner, researcher, code-reviewer, ...
└── Scouts (12): read-only specialists for audit
```

## Review Backend Reference

| Backend | Setup | Best For |
|---------|-------|----------|
| `agent` | None (default) | Fast, always available, parallel reviewer agents |
| `rp` | Install [RepoPrompt](https://repoprompt.com) | Deep file context, GUI-based, visual review |
| `codex` | `npm i -g @openai/codex` | Multi-model, unattended, session continuity |
| `export` | None | Manual review via external LLM (ChatGPT, Claude web) |
| `none` | None | Skip review entirely |

## Claude Code Integration

```
/cc-route "describe task"    → suggests command + team
/cc-brainstorm → /cc-plan → /cc-work → /cc-epic-review → /cc-commit
/cc-review --backend=rp      → multi-backend code review
/cc-ralph-init → ralph.sh    → autonomous execution with quality gates
/cc-worktree create feature  → isolated work in .claude/worktrees/
```

## Requirements

- Python 3.9+
- Optional: `prompt_toolkit` (REPL tab completion)
- Optional: `MORPH_API_KEY` (semantic search, embeddings)
- Optional: [RepoPrompt](https://repoprompt.com) (rp review backend)
- Optional: `npm i -g @openai/codex` (codex review backend)
- Optional: `npx skills` (skills.sh marketplace)

## License

MIT
