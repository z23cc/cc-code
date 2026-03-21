---
name: teams
description: >
  Agent team composition and dispatch patterns. Defines which agents work
  together, in what order, and how they hand off context.
  TRIGGER: 'assemble team', 'dispatch team', 'run team', '组团', '派团队'.
---

# Agent Teams — Composition & Dispatch

## Available Agents (8)

| Agent | Role | Mode | Best For |
|-------|------|------|----------|
| **researcher** | Investigate, map, report | Read-only | Understanding unfamiliar code |
| **architect** | Design, evaluate structure | Read-only | Architecture decisions |
| **planner** | Create implementation plan | Read-only | Breaking work into tasks |
| **code-reviewer** | Review for quality | Read-only | General code review |
| **python-reviewer** | Review Python code | Read-only | Python-specific review |
| **security-reviewer** | Review for security | Read+Write | Security audit + fixes |
| **refactor-cleaner** | Simplify, remove dead code | Read+Write | Code cleanup |
| **build-fixer** | Fix build/test errors | Read+Write | Getting build green |

## Team Templates

### Team: Feature Development

**When:** Building a new feature from scratch.

```
1. researcher (read-only)
   → "Investigate how [area] works. Map dependencies and patterns."
   → Output: research-findings.md

2. architect (read-only)
   → "Design [feature] given these findings: {research-findings}"
   → Output: architecture-proposal.md

3. planner (read-only)
   → "Create implementation plan for this design: {architecture-proposal}"
   → Output: implementation-plan.md

4. [Worker agents per task — see worker-protocol]
   → Each task: implement → test → commit

5. code-reviewer + security-reviewer (parallel)
   → Review all changes since baseline
   → Output: review-verdict (SHIP/NEEDS_WORK)
```

### Team: Bug Fix

**When:** Investigating and fixing a bug.

```
1. researcher (read-only)
   → "Investigate [bug]. Trace data flow, find root cause."
   → Output: bug-analysis.md

2. build-fixer (read+write)
   → "Fix this bug based on analysis: {bug-analysis}"
   → Implements the fix

3. code-reviewer (read-only)
   → "Review the fix for correctness and regressions"
   → Output: review-verdict
```

### Team: Code Review (Large PR)

**When:** Reviewing a PR with 500+ lines across multiple areas.

```
1. researcher (read-only)
   → "Summarize what this PR changes and why"
   → Output: pr-summary.md

2. [Parallel dispatch — split by file group]:
   a. code-reviewer → general quality (files group A)
   b. code-reviewer → general quality (files group B)
   c. security-reviewer → security-sensitive files
   d. python-reviewer → Python-specific patterns (if .py files)

3. Orchestrator consolidates all findings
   → Output: consolidated-review with verdict
```

### Team: Refactoring

**When:** Restructuring code without changing behavior.

```
1. researcher (read-only)
   → "Map all usages and dependents of [target code]"
   → Output: impact-analysis.md

2. architect (read-only)
   → "Propose refactoring approach given impact analysis"
   → Output: refactor-design.md

3. refactor-cleaner (read+write)
   → "Execute this refactoring: {refactor-design}"
   → Implements changes

4. code-reviewer (read-only)
   → "Verify refactoring preserves behavior"
   → Output: review-verdict
```

### Team: Autoimmune Improvement

**When:** Running autoimmune Mode A on complex tasks.

```
FOR each task:
  1. researcher (read-only)
     → "Research what needs to change for: {task}"

  2. build-fixer OR refactor-cleaner (read+write)
     → "Implement this improvement: {task}" (< 50 lines)

  3. [Verify: run lint+test]
     → PASS: commit
     → FAIL: revert, next task
```

### Team: Architecture Audit

**When:** Evaluating project health and structure.

```
1. researcher (read-only)
   → "Map the project architecture: layers, components, dependencies"

2. architect (read-only)
   → "Evaluate architecture: dependency direction, boundaries, coupling"

3. security-reviewer (read-only)
   → "Scan for security issues: auth, input validation, secrets"

4. Orchestrator consolidates into readiness-audit report
```

## Dispatch Rules

### Sequential vs Parallel

| Rule | When |
|------|------|
| **Sequential** | Next agent needs previous agent's output |
| **Parallel** | Agents review different file groups independently |

### Agent Handoff Protocol

1. Each agent outputs **structured markdown** (not free text)
2. Orchestrator passes relevant sections to next agent
3. Never pass full conversation history — only synthesized findings
4. Use filesystem for large handoffs: write to `/tmp/cc-team-*.md`

```bash
# Handoff pattern
Agent A → writes /tmp/cc-team-research.md
Agent B → reads /tmp/cc-team-research.md → writes /tmp/cc-team-design.md
Agent C → reads /tmp/cc-team-design.md → implements
```

### Context Isolation

Each agent gets a **fresh context** with only what it needs:
- The specific question/task
- Relevant findings from previous agents
- File paths to examine
- Constraints and acceptance criteria

This prevents context bleed and keeps agents focused.

### Error Handling

| Agent fails | Action |
|------------|--------|
| Researcher finds nothing | Ask user for more context |
| Architect disagrees with approach | Present alternatives to user |
| Build-fixer can't fix | Escalate to debugging skill |
| Reviewer rejects (NEEDS_WORK) | Route back to implementer with issues |
| Reviewer rejects (MAJOR_RETHINK) | Route back to architect |

## Quick Dispatch Reference

| Task | Team | Agents (in order) |
|------|------|-------------------|
| New feature | Feature Dev | researcher → architect → planner → workers → reviewers |
| Bug fix | Bug Fix | researcher → build-fixer → code-reviewer |
| Large PR | Review | researcher → parallel(reviewers) → consolidate |
| Refactoring | Refactor | researcher → architect → refactor-cleaner → code-reviewer |
| Improvement | Autoimmune | researcher → fixer → verify |
| Health check | Audit | researcher → architect → security-reviewer |

## E2E Example: Bug Fix Team

```
Task: "Login returns 403 for valid users"

1. Dispatch researcher:
   → Reads error logs, traces request flow
   → Finds: middleware checks role before token validation
   → Handoff: /tmp/cc-team-research.md with root cause

2. Dispatch build-fixer:
   → Reads handoff file
   → Reorders middleware: validate token → then check role
   → Diff: +3 -3 lines in middleware.py
   → Runs pytest → green

3. Dispatch code-reviewer:
   → Reads diff + handoff
   → Verdict: SHIP ✓
   → Notes: "Consider adding regression test for this ordering"

4. Record:
   $ cc-flow learn --task "403 on valid login" --outcome success \
     --approach "bug-fix team: researcher found middleware ordering issue" \
     --lesson "check middleware execution order for auth issues" \
     --score 5 --used-command /team
```

## Related Skills

- **parallel-agents** — dispatch patterns and coordination
- **worker-protocol** — per-task worker isolation
- **code-review-loop** — review verdict gates (SHIP/NEEDS_WORK/MAJOR_RETHINK)
- **autoimmune** — autonomous improvement with team support
- **feedback-loop** — record team outcomes for routing improvement
