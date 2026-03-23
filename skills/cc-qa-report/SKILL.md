---
name: cc-qa-report
description: >
  Report-only QA testing — documents bugs with evidence but never fixes anything.
  Produces health score + structured issue list. Hand off to developers for fixes.
  TRIGGER: 'qa report', 'just report bugs', 'test but dont fix', 'QA报告', '只报告不修'.
  NOT FOR: fixing bugs — use cc-qa for test-and-fix. NOT FOR: unit tests.
  DEPENDS ON: cc-browser (automation engine).
---

# QA Report (No Fixes)

Browser-based QA that documents all issues with evidence but **NEVER modifies source code, config files, or any project files**. Report only — hand off to developers for fixes.

## Workflow

### 1. Orient

- **Detect framework** from page source (Next.js: `_next/data`, Rails: `csrf-token`, WordPress: `wp-content`, SPA: pushState routing)
- **Diff-aware detection**: `git diff main...HEAD --name-only` to find affected pages
- Map changed files to routes and build a test plan

### 2. Test Each Page

For every page, using `agent-browser`:

1. `agent-browser open <url> && agent-browser wait --load networkidle`
2. `agent-browser snapshot -i` — check interactive elements
3. `agent-browser console` — capture errors/warnings
4. `agent-browser screenshot evidence/<page>.png`
5. Test forms, links, buttons — document failures

### 3. Score & Categorize

**Issue categories**: functional, console, visual, ux, performance, accessibility, links, content

**Severity deductions** (from 100 per category):
- Critical: -25 | High: -15 | Medium: -8 | Low: -3

**Health score** = weighted average:
- Functional 20%, UX 15%, Console 15%, Accessibility 15%, Visual 10%, Performance 10%, Links 10%, Content 5%

### 4. Produce Report

```markdown
# QA Report — <project> (<date>)

## Health Score: <score>/100

| Category | Score | Issues |
|----------|-------|--------|
| Functional | 85 | 1 high |
| ... | ... | ... |

## Issues Found: <N>

### 1. [severity/category] <title>
- **Page**: /path
- **Evidence**: evidence/<page>.png
- **Steps to reproduce**: ...
- **Expected**: ...
- **Actual**: ...

## Pages Tested: <N>
<list>

## Recommended Fix Priority
1. Critical → 2. High functional → 3. Console → 4. A11y → 5. Visual/UX
```

## Rules

- **NEVER modify source code** — report only
- Use `agent-browser` for ALL browser interactions
- Screenshot every issue as evidence
- Include reproduction steps for each issue
- If dev server is not running, start it and wait for ready
