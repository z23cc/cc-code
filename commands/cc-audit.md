---
team: "audit"
agent: "architect"
description: "8-pillar project readiness audit. TRIGGER: 'audit', 'project health', 'is this ready', '体检', '项目审计'. Fixes agent-readiness issues, reports production issues."
---

Activate the cc-readiness-audit skill with **Audit team** dispatch.

## Default Team: researcher → architect → security-reviewer

### Step 1: Dispatch researcher
Run all 8 pillar checks and write findings to `/tmp/cc-team-research.md`:
- Pillar 1-5 (agent readiness): style, build, test, docs, env
- Pillar 6-8 (production readiness): observability, security, CI/CD

### Step 2: Dispatch architect
- Score each pillar (pass/warn/fail)
- Propose fixes for agent readiness (Pillars 1-5)
- Report production findings (Pillars 6-8, no changes)

### Step 3: Dispatch security-reviewer
- Deep check on Pillar 7 (security)
- Flag any critical vulnerabilities

### Output
Structured audit report with pillar scores and recommendations.
Auto-fix agent readiness only. Report production issues without changing.
