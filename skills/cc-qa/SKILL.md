---
name: cc-qa
description: >
  Systematic QA testing with health scoring, diff-aware page detection, and auto-fix loop.
  Tests affected pages, scores health 0-100, captures evidence, then fixes bugs iteratively.
  TRIGGER: 'qa', 'test the site', 'find bugs', 'test and fix', 'QA测试', '测试网站', '找bug'.
  NOT FOR: report-only mode — use cc-qa-report. NOT FOR: unit tests — use cc-tdd.
  DEPENDS ON: cc-browser (automation engine).
  FLOWS INTO: cc-commit (after fixes verified).
---

# QA Test & Fix Workflow

Systematic browser-based QA that detects affected pages, scores site health, and fixes bugs in a loop.

## Phase 1: Orient

1. **Detect framework** from page source:
   - Next.js: `_next/data`, `__NEXT_DATA__`
   - Rails: `csrf-token`, `data-turbo`
   - WordPress: `wp-content`, `wp-json`
   - SPA: no full-page reloads, hash/pushState routing
   - Static: plain HTML, no framework markers
2. **Diff-aware page detection** — find pages affected by recent changes:
   ```bash
   git diff main...HEAD --name-only
   ```
   Map changed files to routes: `pages/about.tsx` → `/about`, `app/api/auth/` → auth flows, `components/Header` → all pages. If no diff context (e.g., on main), test all discoverable routes.
3. **Build test plan**: list pages to test, ordered by change impact.

## Phase 2: Explore & Score

Test each page using `agent-browser`. For every page:

1. `agent-browser open <url> && agent-browser wait --load networkidle`
2. `agent-browser snapshot -i` — check interactive elements
3. `agent-browser console` — capture errors/warnings
4. `agent-browser screenshot evidence/<page>-initial.png`
5. Test forms, links, buttons via click/fill commands
6. Record issues by category

### Issue Taxonomy

| Category | Examples |
|----------|---------|
| **functional** | Broken form, 404 link, failed API call |
| **console** | JS error, unhandled rejection, deprecation warning |
| **visual** | Overflow, z-index overlap, missing image, broken layout |
| **ux** | No loading state, confusing flow, missing feedback |
| **performance** | Slow load (>3s), large bundle, layout shift |
| **accessibility** | Missing alt text, no focus indicator, low contrast |
| **links** | Dead link, wrong destination, missing href |
| **content** | Typo, placeholder text, lorem ipsum in production |

### Health Scoring Rubric

Each category starts at 100. Deduct per issue found:
- **Critical**: -25 (app crash, data loss, security hole)
- **High**: -15 (broken feature, major UX failure)
- **Medium**: -8 (cosmetic bug, minor UX issue)
- **Low**: -3 (typo, warning, minor polish)

Minimum per category: 0. Final health score = weighted average:

| Category | Weight |
|----------|--------|
| Functional | 20% |
| UX | 15% |
| Console | 15% |
| Accessibility | 15% |
| Visual | 10% |
| Performance | 10% |
| Links | 10% |
| Content | 5% |

## Phase 3: Fix Loop

For each issue (critical first, then high, medium, low):

1. **Fix** the source code
2. **Re-test** the affected page with `agent-browser`
3. **Screenshot** `evidence/<page>-after-fix-<n>.png` for before/after
4. **Re-score** — update health score
5. **Repeat** until health >= 90 or no more fixable issues

Stop the loop after 5 fix iterations max to avoid infinite cycles.

## Output Format

```markdown
# QA Report — <project> (<date>)

## Health Score: <score>/100 <emoji>

| Category | Score | Issues |
|----------|-------|--------|
| Functional | 85 | 1 high |
| ... | ... | ... |

## Issues Found: <N> (Fixed: <M>)

### 1. [critical/functional] <title>
- **Page**: /path
- **Evidence**: evidence/path-initial.png
- **Fix**: <description> → evidence/path-after-fix-1.png
- **Status**: Fixed ✓ / Remaining

## Pages Tested: <N>
<list>
```

## Rules

- Use `agent-browser` for ALL browser interactions (never Puppeteer/Playwright directly)
- Screenshot every issue as evidence before attempting fixes
- Never skip Phase 1 framework detection — it informs test strategy
- If the dev server is not running, start it first and wait for ready
- After all fixes, run the full test suite if one exists (`cc-flow verify`)

## On Completion

When QA testing and fixes are done:
```bash
cc-flow skill ctx save cc-qa --data '{"health_score": 92, "bugs_found": 5, "bugs_fixed": 4, "remaining": ["..."]}'
cc-flow skill next
```
