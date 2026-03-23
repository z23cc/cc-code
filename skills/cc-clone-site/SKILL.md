---
name: cc-clone-site
description: >
  Clone/replicate a reference website or UI — screenshot, analyze, plan, implement, QA compare.
  Goal-driven: iterate until the result visually matches the reference.
  TRIGGER: 'clone site', 'replicate this site', 'copy this design', 'make it look like',
  'reference site', 'implement like this URL', '仿站', '照着这个做', '参考这个网站',
  '实现一模一样的效果', '模仿这个设计'.
  NOT FOR: original design work — use cc-brainstorm + cc-ui-ux.
  DEPENDS ON: cc-browser (screenshots), cc-qa (visual comparison).
  FLOWS INTO: cc-ship (deploy the result).
---

# Clone Site — Reference-Driven Implementation

Replicate a target website/UI by analyzing screenshots, extracting design tokens,
planning implementation, and iterating until visual match.

## Workflow

### Phase 1: Capture Reference

```bash
# Screenshot the target site at 3 breakpoints
agent-browser open "$TARGET_URL"
agent-browser screenshot --full-page -o ref-desktop.png
agent-browser viewport 768 1024
agent-browser screenshot --full-page -o ref-tablet.png
agent-browser viewport 375 812
agent-browser screenshot --full-page -o ref-mobile.png

# Snapshot the DOM structure
agent-browser snapshot -i > ref-snapshot.txt

# Extract: colors, fonts, spacing, layout patterns
agent-browser eval "JSON.stringify({
  fonts: getComputedStyle(document.body).fontFamily,
  bg: getComputedStyle(document.body).backgroundColor,
  links: document.querySelectorAll('a').length,
  images: document.querySelectorAll('img').length,
})"
```

### Phase 2: Analyze & Plan

From the screenshots and snapshot, extract:

1. **Layout structure** — grid/flex, breakpoints, section ordering
2. **Design tokens** — colors (primary, secondary, accent, bg, text), fonts, spacing scale
3. **Components** — navbar, hero, cards, footer, forms, modals
4. **Interactions** — hover states, animations, transitions, scroll behavior
5. **Content** — headings, copy structure, image placement

Create implementation plan:
```bash
cc-flow epic create --title "Clone: $TARGET_URL"
# Create tasks per component: navbar, hero, cards, footer, responsive, animations
```

### Phase 3: Implement

For each component:
1. Code the HTML/CSS/JS structure
2. Match design tokens from reference
3. Screenshot your version at same viewport
4. Visually compare with reference

### Phase 4: QA Compare Loop

```bash
# Screenshot your implementation
agent-browser open "http://localhost:3000"
agent-browser screenshot --full-page -o impl-desktop.png

# Side-by-side visual diff
# Compare: layout alignment, color accuracy, font matching, spacing consistency
```

**Iterate until visual match:**
- Layout matches? → next component
- Colors off? → adjust CSS variables
- Spacing wrong? → fix margin/padding values
- Responsive broken? → add media queries
- Animations missing? → add transitions

### Phase 5: Polish

- [ ] All 3 breakpoints match (desktop, tablet, mobile)
- [ ] Hover states replicated
- [ ] Animations/transitions match timing
- [ ] Fonts match (or closest alternative)
- [ ] Images properly sized/cropped
- [ ] Content structure matches

## Quick Start

```
/cc-clone-site https://example.com
```

This will:
1. Screenshot the reference at 3 viewports
2. Analyze design tokens and structure
3. Create epic with per-component tasks
4. Implement each component
5. QA compare after each component
6. Iterate until match

## Tips

- Start with layout structure (grid/sections), then fill in components
- Extract exact hex colors from screenshots, don't guess
- Use the reference's font stack or find closest Google Fonts match
- Compare at pixel level for spacing — use browser dev tools overlay
- For dynamic content (carousels, modals), capture multiple states
