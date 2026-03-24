---
name: cc-web-design
description: >
  Review UI/frontend code against Vercel Web Interface Guidelines.
  TRIGGER: 'review UI', 'check design', 'audit UX', 'accessibility check',
  'web design review', '检查UI', '审查设计', '前端审查'.
  Fetches latest guidelines, reads files, outputs findings.
  FLOWS INTO: cc-optimize, cc-review.
  DEPENDS ON: cc-ui-ux.
---

# Web Design Review

Review frontend code for compliance with [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines).

## Process

### Step 1: Fetch Latest Guidelines

Always fetch fresh guidelines before review:

```
WebFetch: https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

This ensures you're using the most current rules.

### Step 2: Identify Files to Review

If the user specifies files, use those. Otherwise, look for:
- `*.tsx`, `*.jsx` — React components
- `*.css`, `*.scss` — Stylesheets
- `*.html` — Templates
- `tailwind.config.*` — Tailwind configuration

Use Glob to find relevant files:
```
Glob: src/**/*.tsx
Glob: app/**/*.tsx
Glob: components/**/*.tsx
```

### Step 3: Review Against Guidelines

For each file, check all rules from the fetched guidelines. Key areas:

**Accessibility**
- Semantic HTML elements
- ARIA attributes
- Keyboard navigation
- Color contrast
- Screen reader compatibility

**Performance**
- Image optimization (next/image, lazy loading)
- Bundle size awareness
- Client vs server components
- Rendering strategy

**UX Patterns**
- Loading states
- Error boundaries
- Empty states
- Responsive design
- Dark mode support

**Code Quality**
- Component composition
- Props interface design
- CSS methodology consistency
- Animation performance (prefer CSS transforms)

### Step 4: Output Findings

Use terse `file:line` format as specified in the fetched guidelines:

```
src/components/Button.tsx:12 — Missing aria-label on icon-only button
src/app/page.tsx:45 — Using <img> instead of next/image
src/components/Modal.tsx:8 — No focus trap implementation
```

Group by severity:
1. **Critical** — Accessibility violations, broken UX
2. **Warning** — Performance issues, missing best practices
3. **Info** — Style suggestions, nice-to-haves

### Step 5: Suggest Fixes

For each finding, provide a one-line fix suggestion:

```
src/components/Button.tsx:12
  Issue: Missing aria-label on icon-only button
  Fix: Add aria-label="Close" to the <button> element
```

## Integration with cc-flow

After review, create tasks for findings:

```bash
cc-flow epic create --title "Web Design Review Findings"
cc-flow task create --epic epic-N --title "[Critical] Fix: missing aria-labels" --size S
cc-flow task create --epic epic-N --title "[Warning] Optimize images with next/image" --size M
```

Or use auto scan to detect issues:
```bash
cc-flow auto deep   # includes architecture scan
cc-flow verify      # runs lint (catches some UI issues)
```

## Related Skills

- **cc-code-review-loop** — general code review with verdict system
- **cc-security-review** — security-focused review (XSS, CSRF)
- **cc-performance** — performance profiling and optimization
- **cc-scout-practices** — best practices research
