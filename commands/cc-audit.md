---
team: "audit"
agent: "architect"
description: "8-pillar project readiness audit. TRIGGER: 'audit', 'project health', 'is this ready', '体检', '项目审计'. Fixes agent-readiness issues, reports production issues."
---

Activate the cc-readiness-audit skill with **parallel audit dispatch**.

## Team: researcher → PARALLEL(architect + security-reviewer) → consolidate

### Step 1: Researcher (sequential — gathers data for others)
Run all 8 pillar checks:
- Pillar 1-5 (agent readiness): style, build, test, docs, env
- Pillar 6-8 (production readiness): observability, security, CI/CD
- Write findings to `/tmp/cc-team-research.md`

### Step 2: PARALLEL dispatch (both read research findings independently)

**IMPORTANT: Dispatch both agents in one message — they analyze different pillars.**

- **architect** agent → Score pillars 1-6, propose fixes for agent readiness (1-5)
- **security-reviewer** agent → Deep check pillar 7 (security), flag vulnerabilities

### Step 3: Consolidate (after both complete)
Merge architect + security findings into audit report.
Auto-fix agent readiness only. Report production issues without changing.
