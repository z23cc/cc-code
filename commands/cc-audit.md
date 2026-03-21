---
description: "8-pillar project readiness audit. TRIGGER: 'audit', 'project health', 'is this ready', '体检', '项目审计'. Fixes agent-readiness issues, reports production issues."
---

Activate the cc-readiness-audit skill.

1. Run all 8 pillar checks (style, build, test, docs, env, observability, security, CI/CD)
2. Score agent readiness (Pillars 1-5) and production readiness (Pillars 6-8)
3. Offer to auto-fix agent readiness issues (Pillars 1-5 only)
4. Report production readiness findings without changing anything (Pillars 6-8)
5. Print the structured audit report
