---
name: cc-browser-qa
description: >
  Automated visual QA testing — smoke tests, Core Web Vitals, WCAG accessibility,
  dark mode, responsive breakpoints, visual regression via baseline screenshots.
  Deeper than cc-qa: measures performance metrics and accessibility compliance.
  TRIGGER: 'browser qa', 'visual test', 'accessibility test', 'core web vitals',
  'responsive test', 'dark mode test', 'WCAG', '视觉测试', '无障碍测试', '性能测试'.
  NOT FOR: functional QA with bug fixing — use cc-qa. NOT FOR: unit tests — use cc-tdd.
  DEPENDS ON: cc-browser (automation engine).
  FLOWS INTO: cc-qa (fix issues found), cc-optimize (performance improvements).
---

# Browser QA — Automated Visual & Performance Testing

## Test Suites

### Suite 1: Smoke Tests
Quick sanity check on key pages:
1. Navigate to each key URL
2. Check: page loads (no 5xx), no console errors, key elements visible
3. Screenshot each page at desktop viewport
4. Report: pass/fail per page

### Suite 2: Core Web Vitals
Measure performance metrics on each page:

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | 2.5-4.0s | > 4.0s |
| **FID** (First Input Delay) | ≤ 100ms | 100-300ms | > 300ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | 0.1-0.25 | > 0.25 |
| **TTFB** (Time to First Byte) | ≤ 800ms | 800-1800ms | > 1800ms |

Use browser Performance API via agent-browser to measure.

### Suite 3: WCAG Accessibility (AA)
Check against WCAG 2.1 AA:
- [ ] All images have alt text
- [ ] Color contrast ≥ 4.5:1 (normal text) / 3:1 (large text)
- [ ] Interactive elements focusable via keyboard
- [ ] Form inputs have labels
- [ ] Headings in logical order (h1 → h2 → h3)
- [ ] No auto-playing media
- [ ] Skip navigation link present

### Suite 4: Responsive Breakpoints
Test at 3 viewports:

| Viewport | Width | Device |
|----------|-------|--------|
| Mobile | 375px | iPhone SE |
| Tablet | 768px | iPad |
| Desktop | 1440px | Standard |

For each: screenshot + check layout (no overflow, no overlapping elements).

### Suite 5: Dark Mode
If dark mode supported:
1. Toggle dark mode
2. Screenshot all key pages
3. Check: no white flashes, text readable, images have dark backgrounds
4. Compare with light mode screenshots

### Suite 6: Visual Regression (Optional)
Compare against baseline screenshots:
1. Load baseline from `.tasks/browser-qa/baselines/`
2. Take current screenshots
3. Pixel-diff comparison
4. Flag pages with >5% visual change
5. Save new baselines if approved

## Output

```markdown
## Browser QA Report

### Summary
- Pages tested: [N]
- Suites run: [list]
- Health score: [0-100]

### Core Web Vitals
| Page | LCP | CLS | TTFB | Grade |
|------|-----|-----|------|-------|
| / | 1.8s | 0.05 | 450ms | A |
| /dashboard | 3.2s | 0.12 | 890ms | C |

### Accessibility
- Violations: [N]
- Critical: [list]
- Warnings: [list]

### Responsive
| Page | Mobile | Tablet | Desktop |
|------|--------|--------|---------|
| / | ✅ | ✅ | ✅ |
| /dashboard | ⚠️ overflow | ✅ | ✅ |

### Issues Found
1. [HIGH] LCP > 2.5s on /dashboard — optimize hero image
2. [MEDIUM] Missing alt text on 3 images
3. [LOW] CLS 0.12 on /dashboard — add dimension attributes
```

## On Completion

```bash
cc-flow skill ctx save cc-browser-qa --data '{"health_score": 78, "vitals_grade": "B", "a11y_violations": 3, "responsive_issues": 1}'
cc-flow skill next
```

## Related Skills

- **cc-qa** — functional QA with auto-fix loop (broader, fixes bugs)
- **cc-browser** — raw browser automation commands
- **cc-optimize** — fix performance issues found by this skill
- **cc-web-design** — check against design guidelines
