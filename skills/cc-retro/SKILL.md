---
name: cc-retro
description: >
  Weekly engineering retrospective from git history. Analyzes commits,
  code quality trends, and produces action items.
  TRIGGER: 'retro', 'retrospective', 'weekly review', 'what did we ship',
  '回顾', '周报', '复盘'.
  FLOWS INTO: cc-plan (action items become next tasks).
---

# Weekly Engineering Retrospective

Analyze the past week's work and produce an actionable summary.

## Phase 1: Gather Data

```bash
git log --since="1 week ago" --oneline --no-merges          # What shipped
git log --since="1 week ago" --stat --no-merges              # Detailed stats
git log --since="1 week ago" --name-only --no-merges \
  | sort | uniq -c | sort -rn | head -20                    # Hotspot files
git shortlog --since="1 week ago" -sn --no-merges           # Authors
```

## Phase 2: Classify Commits

Group every commit into one category:

| Category | Pattern | Example prefix |
|----------|---------|----------------|
| Feature  | New capability | `feat:`, `add:` |
| Fix      | Bug repair | `fix:`, `bugfix:` |
| Improve  | Enhancement to existing | `improve:`, `refactor:` |
| Chore    | Config, deps, CI | `chore:`, `ci:`, `build:` |
| Docs     | Documentation | `docs:` |
| Test     | Test additions | `test:` |

Present as a grouped list with commit count per category.

## Phase 3: Code Quality Trends

Evaluate directionally (better / same / worse):

- **Churn hotspots** -- files changed 3+ times this week (risk indicator)
- **Test coverage direction** -- check if test files were added/modified alongside features
- **Code volume** -- net lines added vs removed (growing? shrinking?)
- **PR/commit hygiene** -- average commit message quality, atomic commits vs mega-commits

## Phase 4: Retrospective

### What went well
- Identify patterns: fast fixes, good test coverage, clean commits

### What could improve
- Identify anti-patterns: hotspot churn, missing tests, large commits

### Action items for next week
- 3-5 concrete, assignable items derived from the analysis
- Each item should reference the evidence (e.g., "file X changed 7 times -- consider refactoring")

## Output Format

Structure the output as: **Shipped** (commits grouped by category with counts),
**Quality Trends** (table: metric / direction / evidence), **What Went Well**,
**What Could Improve**, **Action Items** (3-5 checkboxes).

Save output to `docs/retros/YYYY-MM-DD-retro.md` if `docs/` exists.
