# cc-code

Development workflow toolkit for Claude Code. Language-agnostic core with Python pack.

## Install

```bash
# Add marketplace
claude plugin marketplace add z23cc/cc-code

# Install
claude plugin install cc-code@cc-code --scope user
```

## What's Inside

| Component | Count | Highlights |
|-----------|-------|-----------|
| **Skills** | 35 | brainstorming, TDD, debugging, autoimmune, feedback-loop |
| **Commands** | 19 | `/brainstorm` `/plan` `/tdd` `/review` `/autoimmune` `/route` `/tasks` |
| **Agents** | 8 | researcher, architect, planner, code-reviewer, security-reviewer, ... |
| **CLI** | cc-flow | 26 subcommands: epic/task management, scan, route, learn, checkpoint |
| **Rules** | 4 | Always-on: python-style, testing, security, git |
| **Hooks** | 2 | SessionStart context + pre-commit quality gate |

## Quick Start

```bash
# Don't know what command to use?
/route describe your task here

# New feature
/brainstorm → /plan → /tdd → /refine → /review → /commit

# Fix a bug
/debug → /fix → /commit

# Autonomous improvement
/autoimmune scan    # detect issues
/autoimmune         # fix from task list
/autoimmune full    # scan + fix + test

# Task management (cc-flow CLI)
cc-flow init
cc-flow epic create --title "My Feature"
cc-flow task create --epic epic-1-my-feature --title "Step 1" --size S
cc-flow next
cc-flow start <task-id>
cc-flow done <task-id> --summary "What I did"
cc-flow progress
```

## Architecture

```
User input
    ↓
/route → suggests command + team + past learnings
    ↓
/command → Skill → Team → Agent(s) → Result
    ↓
cc-flow learn → stored for future routing
```

### Skill Layers

- **Core (23)** — Language-agnostic workflows: brainstorming, plan, TDD, verification, refinement, review loop, teams, autoimmune, debugging, research, task tracking, feedback loop, ...
- **Python Pack (12)** — Python-specific: patterns, testing, FastAPI, async, database, Celery, ...

### cc-flow CLI

Task & workflow manager with 26 subcommands:

```
Project:    init, epic, task, dep
View:       list, epics, tasks, show, ready, next, progress, status
Work:       start, done, block
Quality:    validate, scan
Session:    checkpoint, log, summary, archive, stats
Routing:    route, learn, learnings
Meta:       version
```

## Development

Source: edit files in this repo → restart Claude Code → changes apply via symlink.

```bash
# Symlink setup (one-time)
mv ~/.claude/plugins/cache/cc-code/cc-code/X.Y.Z ~/.claude/plugins/cache/cc-code/cc-code/X.Y.Z.bak
ln -s /path/to/cc-code ~/.claude/plugins/cache/cc-code/cc-code/X.Y.Z
```

## License

MIT
