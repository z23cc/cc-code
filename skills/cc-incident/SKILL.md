---
name: cc-incident
description: "Production incident response and postmortem — triage, investigate, mitigate, fix, write postmortem. TRIGGER: 'incident', 'production down', 'outage', 'postmortem', 'service down', 'SEV1', '事故', '生产故障', '复盘', '线上问题'. NOT FOR: dev bugs (use cc-debug), build errors (use cc-fix), code review (use cc-review)."
---

# Incident Response & Postmortem

## Triage (First 5 Minutes)

1. **What's broken?** — Which service/endpoint/page is affected?
2. **Who's affected?** — All users? Subset? Internal only?
3. **Since when?** — Check monitoring, recent deploys, error logs
4. **Severity?**

| Severity | Impact | Response |
|----------|--------|----------|
| **SEV1** | Service down, data loss risk | All hands, rollback immediately |
| **SEV2** | Major feature broken | Fix or rollback within hours |
| **SEV3** | Minor degradation | Fix in next deploy |

## Investigate

```bash
# Recent deploys
git log --oneline --since="2 hours ago"

# Error logs
# Check your logging/monitoring (Sentry, Datadog, CloudWatch, etc.)

# Recent changes to suspect area
git log --oneline -10 -- <suspect-path>
git diff <last-good-deploy>..HEAD -- <suspect-path>
```

## Mitigate (Stop the Bleeding)

| Strategy | When |
|----------|------|
| **Rollback** | Recent deploy caused it, rollback is safe |
| **Feature flag** | Can disable broken feature without full rollback |
| **Hotfix** | Root cause clear, fix is small and safe |
| **Scale** | Traffic spike, not a code bug |

**Rule:** Mitigate first, investigate fully later. Getting users working > finding root cause.

## Fix

After mitigation, follow the debugging skill's 4-phase process:
1. Root cause investigation (with production logs, not just code)
2. Pattern analysis
3. Hypothesis testing
4. Implementation with regression test

## Postmortem Template

```markdown
# Incident Postmortem: [Title]

**Date:** YYYY-MM-DD
**Duration:** X hours
**Severity:** SEV1/2/3
**Author:** [name]

## Summary
[1-2 sentences: what happened, impact, resolution]

## Timeline
| Time | Event |
|------|-------|
| HH:MM | First alert / user report |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Full fix deployed |
| HH:MM | Confirmed resolved |

## Root Cause
[What actually broke and why]

## Impact
- Users affected: N
- Duration: X hours
- Data loss: none / [description]

## What Went Well
- [Quick detection, good monitoring, etc.]

## What Went Wrong
- [Slow response, missing tests, no alerts, etc.]

## Action Items
- [ ] [Fix] Add regression test for this failure
- [ ] [Prevent] Add monitoring for [metric]
- [ ] [Process] Update runbook for [scenario]
```

## Rules

- **No blame.** Focus on systems, not people.
- **Publish internally.** Everyone learns from incidents.
- **Action items must be tracked.** Use cc-flow or issue tracker.
- **Schedule follow-up.** Review action items in 2 weeks.

## Related Skills

- **cc-debugging** — systematic root cause investigation (Phase 1-4)
- **cc-logging** — structured logs for incident investigation
- **cc-deploy** — rollback and hotfix patterns
- **cc-readiness-audit** — Pillar 6 (observability) prevents incidents
