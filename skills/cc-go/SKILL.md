---
name: cc-go
description: >
  One command full automation — describe your goal, system routes to the right
  strategy and executes everything. Uses chain (lightweight), ralph (complex),
  or auto (improvement) mode automatically.
  TRIGGER: 'go', 'just do it', 'automate', 'do everything', 'run everything',
  '全自动', '一键执行', '帮我做', '自动完成'.
  NOT FOR: specific skill invocation — use the skill directly.
---

# cc-flow go — One Command, Full Automation

## Usage

```bash
cc-flow go "describe what you want"
```

## How It Works

```
Your goal → Route → Decide mode → Execute
```

### Mode Decision

| Mode | When | What happens |
|------|------|-------------|
| **chain** | Matches a skill chain ≤ 4 required steps | Executes skills in sequence with context passing |
| **ralph** | Complex goal, needs task generation | Launches Ralph: creates epic + tasks, executes autonomously |
| **auto** | Improvement/scan keywords | Runs OODA loop: scan → fix → test |

### Examples

```bash
# Bug fix → chain mode (bugfix chain: debug → tdd → review → commit)
cc-flow go "fix the login bug"

# New feature → ralph mode (creates tasks, executes autonomously)
cc-flow go "implement user authentication with JWT"

# Code quality → auto mode (scan → fix → test loop)
cc-flow go "improve code quality"

# Preview without executing
cc-flow go "refactor the auth module" --dry-run

# Force a specific mode
cc-flow go "anything" --mode=ralph
cc-flow go "anything" --mode=chain
```

### Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Show plan without executing |
| `--mode {chain,ralph,auto}` | Force execution mode |
| `--max N` | Max iterations for ralph mode (default: 25) |

## Chain Mode (Lightweight)

When `go` picks chain mode, it:
1. Sets up chain state and current skill
2. Outputs step-by-step instructions with loaded context
3. You execute each skill, then `cc-flow chain advance`

## Ralph Mode (Heavy/Autonomous)

When `go` picks ralph mode, it:
1. Sets GOAL env var
2. Launches `ralph.sh` with self-healing enabled
3. Ralph creates epic + tasks from goal
4. Executes autonomously with receipt-based proof-of-work
5. Monitor: `tail -f scripts/ralph/runs/latest/progress.log`
6. Pause: `touch scripts/ralph/PAUSE`
7. Stop: `touch scripts/ralph/STOP`

## Auto Mode (Improvement Loop)

When `go` picks auto mode, it:
1. OBSERVE: scans for lint, type, test issues
2. DECIDE: picks next task, recommends team
3. ACT: auto-fixes lint, runs tests
