---
name: cc-product-lens
description: >
  Product thinking before building — founder review, PMF signals, user journey
  audit, feature prioritization. Validates the product value before investing
  engineering time.
  TRIGGER: 'product lens', 'is this worth building', 'product review', 'PMF',
  'user journey', 'feature priority', '产品视角', '值不值得做', '用户旅程'.
  NOT FOR: technical design — use cc-brainstorming. NOT FOR: idea validation — use cc-office-hours.
  DEPENDS ON: cc-office-hours (idea validated).
  FLOWS INTO: cc-brainstorming (product-validated idea ready for design).
---

# Product Lens — Think Like a Founder Before Building

## Purpose

Stop building features nobody wants. Apply product thinking to validate value before writing code.

## 4 Modes

### Mode 1: Founder Review
Ask the hard questions a founder/PM would ask:
1. **Who specifically uses this?** (not "users" — name the persona)
2. **What's their current workaround?** (if no workaround, maybe no real pain)
3. **How will we know this succeeded?** (specific metric, not "more engagement")
4. **What's the smallest version that proves the hypothesis?**
5. **What do we stop doing to make time for this?** (opportunity cost)

### Mode 2: PMF Signal Scoring
Rate 0-10 on each dimension:

| Signal | Score | Evidence |
|--------|-------|----------|
| **Demand** | ? | Are users asking for this? (tickets, feedback, churned because missing) |
| **Frequency** | ? | How often would they use it? (daily > monthly > once) |
| **Retention** | ? | Would this make users stay longer? |
| **Willingness to pay** | ? | Would someone pay for this specifically? |
| **Word of mouth** | ? | Would users tell others about this feature? |

**Interpretation:**
- 40+: Strong PMF signal → proceed
- 25-39: Promising → validate with 3 users first
- <25: Weak → reconsider or scope down

### Mode 3: User Journey Audit
Map the complete user journey for this feature:
```
Discover → Sign up → First use → [THIS FEATURE] → Success moment → Return
```

For the feature step, identify:
- **Time to value**: How long from clicking to getting value?
- **Friction points**: Where will users get stuck?
- **Drop-off risks**: Where might they abandon?
- **Delight moments**: Where can we exceed expectations?

### Mode 4: Feature Prioritization (RICE)
Score against existing backlog:

| Feature | Reach | Impact | Confidence | Effort | RICE Score |
|---------|-------|--------|------------|--------|------------|
| This feature | ? | ? | ? | ? | ? |
| Alternative A | ? | ? | ? | ? | ? |
| Alternative B | ? | ? | ? | ? | ? |

**RICE = (Reach × Impact × Confidence) / Effort**

## Output: Product Brief

```markdown
## Product Brief: [Feature Name]

### Value Proposition
[One sentence: who gets what benefit]

### PMF Score: [N]/50
[Signal breakdown table]

### User Journey
[Mapped journey with friction points]

### MVP Scope
[Smallest version that proves the hypothesis]

### Success Metrics
- Primary: [metric + target]
- Secondary: [metric + target]

### Decision
- **BUILD** — strong signals, clear value
- **VALIDATE** — promising but needs user feedback first
- **DEFER** — weak signals, better alternatives exist
```

## On Completion

```bash
cc-flow skill ctx save cc-product-lens --data '{"decision": "BUILD", "pmf_score": 42, "mvp_scope": "...", "success_metric": "..."}'
cc-flow skill next
```

## Related Skills

- **cc-office-hours** — idea validation (lighter, 5 questions)
- **cc-brainstorming** — technical design (after product validation)
- **cc-elicit** — deeper reasoning on product decisions
